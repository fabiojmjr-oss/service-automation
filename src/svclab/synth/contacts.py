"""The contacts, and the two columns no real contact centre has.

Everything random is drawn **here**, once per contact, before any bot exists. A bot in
:mod:`svclab.bot` is then a deterministic function of this table: it reads the draws it is entitled
to read and decides what to do. That is a deliberate constraint with a purpose - if the bot drew its
own randomness, changing its policy would change the stream and every comparison between two
policies would be confounded by noise. Here two policies run against the identical contacts, so any
difference between them is the policy.

Which draws a bot may read matters, and the split is the whole honesty of the exercise:

- ``difficulty``, ``would_self_serve`` and ``human_seconds`` are **truth**. No bot may read them,
  and a test asserts that the bot package never names them.
- ``bot_can_resolve``, ``classifier_draw``, ``patience_turns``, ``repeats_if_unresolved`` and
  ``human_resolves`` are the contact's own behaviour. A bot's outcome depends on them the way a
  real conversation's outcome depends on facts the bot cannot see either.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._draws import bernoulli_from, beta, categorical, exponential_from, uniform
from .config import CENTRE, INTENTS, CentreProfile

#: Columns of the contact table, in order.
CONTACT_COLUMNS = (
    "contact",
    "customer",
    "intent",
    "arrival_hour",
    "holdout",
    "difficulty",
    "bot_can_resolve",
    "would_self_serve",
    "human_seconds",
    "classifier_draw",
    "patience_turns",
    "repeats_if_unresolved",
    "human_resolves",
    "u_bot",
    "u_self_serve",
    "u_seconds",
    "u_patience",
    "u_human",
)

#: The retained uniforms, and the four of them that are truth by another name.
DRAW_COLUMNS = ("u_bot", "u_self_serve", "u_seconds", "u_patience", "u_human")
TRUTH_DRAW_COLUMNS = ("u_bot", "u_self_serve", "u_seconds", "u_human")

#: Columns of the per-intent truth table.
INTENT_TRUTH_COLUMNS = (
    "intent",
    "share",
    "contacts",
    "mean_difficulty",
    "bot_can_resolve_rate",
    "would_self_serve_rate",
    "resolvable_and_needed",
    "mean_human_seconds",
    "human_resolves_rate",
)


def _rate(ceiling: float, slope: float, difficulty: np.ndarray) -> np.ndarray:
    """A probability that falls linearly with difficulty, clipped to be one.

    Linear rather than logistic on purpose: the ceiling and the slope are then readable as the two
    numbers a stakeholder would argue about - what share of the easy ones can be automated, and how
    fast that dies - instead of as coefficients.
    """
    return np.clip(ceiling - slope * difficulty, 0.0, 1.0)


def contacts(rng: np.random.Generator, centre: CentreProfile = CENTRE) -> pd.DataFrame:
    """Every contact of the period, with its declared truth.

    Args:
        rng: The shared generator. Draws are consumed in the order of the columns below, and a new
            column must be appended rather than inserted - inserting one shifts every later draw
            and moves every published figure with it.
        centre: The centre's declared shape.

    Returns:
        A frame with the columns in :data:`CONTACT_COLUMNS`, one row per contact.
    """
    count = centre.contacts
    shares = np.array([profile.share for profile in INTENTS], dtype=float)
    labels = np.array([profile.intent for profile in INTENTS])

    which = categorical(rng, count, shares)
    difficulty = beta(rng, count, centre.difficulty_alpha, centre.difficulty_beta)
    customer = np.asarray(uniform(rng, count) * centre.customers, dtype=int)
    arrival_hour = uniform(rng, count) * centre.days * 24.0

    # The holdout is drawn per customer and then joined on, so every contact of a customer lands in
    # the same arm. One uniform per customer, not per contact.
    holdout_by_customer = uniform(rng, centre.customers) < centre.holdout_share

    # Every uniform below is kept in the returned table. The draws are unchanged and in the same
    # order - each `bernoulli` and `exponential` call was already this uniform followed by this
    # transform - but keeping them separates the **noise** of a contact from the **structure** that
    # turns it into an outcome. Wave 4 replays the identical noise against a population where a
    # customer is a person rather than a label, and it can only isolate that structure because
    # nothing was redrawn.
    u_bot = uniform(rng, count)
    u_self_serve = uniform(rng, count)
    u_seconds = uniform(rng, count)
    classifier_draw = uniform(rng, count)
    u_patience = uniform(rng, count)
    repeat = np.array([profile.repeat_when_unresolved for profile in INTENTS])[which]
    repeats_if_unresolved = bernoulli_from(uniform(rng, count), repeat)
    # Appended last, and it must stay last: a human does not resolve everything, and a model in
    # which they do quietly awards the control arm a perfect score.
    u_human = uniform(rng, count)

    frame = pd.DataFrame(
        {
            "contact": np.arange(count, dtype=int),
            "customer": customer,
            "intent": labels[which],
            "arrival_hour": arrival_hour,
            "holdout": holdout_by_customer[customer],
            "difficulty": difficulty,
            "classifier_draw": classifier_draw,
            "repeats_if_unresolved": repeats_if_unresolved,
            "u_bot": u_bot,
            "u_self_serve": u_self_serve,
            "u_seconds": u_seconds,
            "u_patience": u_patience,
            "u_human": u_human,
        }
    )
    return outcomes_from_difficulty(frame, which, centre)


def intent_index(table: pd.DataFrame) -> np.ndarray:
    """Each contact's intent as an index into :data:`svclab.synth.INTENTS`.

    The contact table carries the label rather than the index, and every per-intent curve is keyed
    on the index. Recovered rather than stored, so there is one representation of the intent in the
    table and no way for the two to disagree.
    """
    order = {profile.intent: position for position, profile in enumerate(INTENTS)}
    return table["intent"].map(order).to_numpy(dtype=int)


def outcomes_from_difficulty(
    frame: pd.DataFrame, which: np.ndarray, centre: CentreProfile = CENTRE
) -> pd.DataFrame:
    """The truth columns that follow from a difficulty, given the noise already drawn.

    Separated from :func:`contacts` so that exactly one thing can change - the difficulty and the
    patience of a contact - while every uniform behind the outcome stays where it was. That is what
    makes :mod:`svclab.population`'s second world a comparison rather than another simulation.

    Args:
        frame: A contact table carrying at least ``difficulty``, ``u_patience`` and the uniforms in
            :data:`TRUTH_DRAW_COLUMNS`.
        which: Index of each contact's intent into :data:`svclab.synth.INTENTS`.
        centre: The centre's declared shape.

    Returns:
        A new frame with the columns in :data:`CONTACT_COLUMNS`, the outcome columns recomputed.
    """
    difficulty = frame["difficulty"].to_numpy(dtype=float)

    ceilings = np.array([profile.bot_ceiling for profile in INTENTS])[which]
    slopes = np.array([profile.bot_difficulty_slope for profile in INTENTS])[which]
    bot_can_resolve = bernoulli_from(
        frame["u_bot"].to_numpy(dtype=float), _rate(ceilings, slopes, difficulty)
    )

    ceilings = np.array([profile.self_serve_ceiling for profile in INTENTS])[which]
    slopes = np.array([profile.self_serve_difficulty_slope for profile in INTENTS])[which]
    would_self_serve = bernoulli_from(
        frame["u_self_serve"].to_numpy(dtype=float), _rate(ceilings, slopes, difficulty)
    )

    base = np.array([profile.human_seconds_base for profile in INTENTS])[which]
    slope = np.array([profile.human_seconds_slope for profile in INTENTS])[which]
    mean_seconds = base + slope * difficulty
    # Exponential around that mean, which is the service-time assumption the queueing formulas in
    # svclab.capacity are built on. Drawn here so that the panel and the formulas agree by
    # construction rather than by hope.
    human_seconds = exponential_from(frame["u_seconds"].to_numpy(dtype=float), 1.0) * mean_seconds

    patience_turns = np.ceil(
        exponential_from(frame["u_patience"].to_numpy(dtype=float), centre.patience_turns_mean)
    )

    ceilings = np.array([profile.human_ceiling for profile in INTENTS])[which]
    slopes = np.array([profile.human_difficulty_slope for profile in INTENTS])[which]
    human_resolves = bernoulli_from(
        frame["u_human"].to_numpy(dtype=float), _rate(ceilings, slopes, difficulty)
    )

    built = frame.assign(
        bot_can_resolve=bot_can_resolve,
        would_self_serve=would_self_serve,
        human_seconds=human_seconds,
        patience_turns=patience_turns,
        human_resolves=human_resolves,
    )
    return built[list(CONTACT_COLUMNS)]


def intent_truth(table: pd.DataFrame) -> pd.DataFrame:
    """One row per intent: what the generator declared, and what it produced.

    The column to read is ``resolvable_and_needed``: contacts a bot can resolve **and** that would
    not have resolved themselves. It is the only share of the volume where automation creates
    anything, and no real operation can compute it.

    Args:
        table: The contact table.

    Returns:
        A frame with the columns in :data:`INTENT_TRUTH_COLUMNS`.
    """
    rows = []
    for profile in INTENTS:
        subset = table[table["intent"] == profile.intent]
        needed = subset["bot_can_resolve"] & ~subset["would_self_serve"]
        rows.append(
            {
                "intent": profile.intent,
                "share": profile.share,
                "contacts": int(len(subset)),
                "mean_difficulty": float(subset["difficulty"].mean()),
                "bot_can_resolve_rate": float(subset["bot_can_resolve"].mean()),
                "would_self_serve_rate": float(subset["would_self_serve"].mean()),
                "resolvable_and_needed": float(needed.mean()),
                "mean_human_seconds": float(subset["human_seconds"].mean()),
                "human_resolves_rate": float(subset["human_resolves"].mean()),
            }
        )
    return pd.DataFrame(rows)[list(INTENT_TRUTH_COLUMNS)]

"""Running a policy against the contacts, one session at a time.

This is the environment rather than the bot: it reads the whole contact row, including the columns a
policy may not see, and works out what happens. The policy contributes two decisions - whether to
attempt the contact at all, and how long to keep trying - and the rest is the world.

Every outcome here is a deterministic function of the contact table and the policy. No draw happens
in this module, which is what makes two policies comparable: they meet the same forty thousand
contacts with the same difficulties, the same patience and the same facts.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from svclab.synth import CENTRE, INTENTS, SINGLE_RETURN, CentreProfile, ChainProfile

from .policy import BotPolicy

#: Columns of the outcome table, one row per **session**. A contact that comes back has two
#: rows: its first session and its repeat. That is not a detail - a containment rate computed
#: over sessions and one computed over contacts differ by exactly the repeat stream, and the
#: repeat stream is what an automation adds to the queue.
OUTCOME_COLUMNS = (
    "session",
    "contact",
    "customer",
    "intent",
    "predicted_intent",
    "classified_correctly",
    "route",
    "bot_turns",
    "outcome",
    "handled_by_human",
    "resolved",
    "is_repeat",
    "returns",
    "human_seconds",
    "customer_seconds",
)

#: The outcomes a session can end in.
OUTCOMES = ("resolved-by-bot", "escalated", "abandoned", "straight-to-human", "repeat-to-human")

#: What a repeat session's id is offset from its contact's id by, multiplied by the attempt. A
#: constant rather than "one past
#: the largest contact in this call", which is what the first version used: that made ids unique
#: only *within* one call, so pooling the treated and control arms - which is exactly what a quality
#: study does - produced two different sessions sharing an id. Derived from the contact id instead,
#: so a session id is unique across any set of runs over disjoint contacts and stable whatever
#: subset is passed in. Wave 6 multiplies it by the attempt number, which keeps that property for a
#: chain: the third attempt at contact 7 is session 2,000,007 in every run there will ever be.
REPEAT_SESSION_OFFSET = 1_000_000

#: Turns a bot needs to resolve a contact it can resolve, at difficulty zero and at difficulty one.
#: Not a policy parameter: it is a property of the conversation, and it is why a longer turn budget
#: buys anything at all.
TURNS_AT_EASIEST = 1
TURNS_AT_HARDEST = 5

#: An empty stand-in for the return draws, so a chain that needs none does not carry an optional
#: frame through the runtime. A two-attempt chain spends no draw, which is why it can be given none.
NO_RETURN_DRAWS = pd.DataFrame(
    {"contact": [], "attempt": [], "u_return": [], "u_human": []}, dtype=float
)


def _accuracy(difficulty: np.ndarray, which: np.ndarray) -> np.ndarray:
    """Probability the classifier labels each contact correctly, from its declared curve."""
    ceilings = np.array([profile.classifier_ceiling for profile in INTENTS])[which]
    slopes = np.array([profile.classifier_difficulty_slope for profile in INTENTS])[which]
    return np.clip(ceilings - slopes * difficulty, 0.0, 1.0)


def _turns_needed(difficulty: np.ndarray) -> np.ndarray:
    """Bot turns a resolvable contact takes, rising with difficulty."""
    span = TURNS_AT_HARDEST - TURNS_AT_EASIEST
    return np.asarray(TURNS_AT_EASIEST + np.round(difficulty * span), dtype=int)


def _human_curve(difficulty: np.ndarray, which: np.ndarray) -> np.ndarray:
    """Probability a human resolves each contact, from the declared curve.

    The same curve the contact table drew ``human_resolves`` from, recomputed here because a chain
    needs the **probability** and not only the first draw from it. The session module is the world
    and may read it; a policy may not, and a test enforces that.
    """
    ceilings = np.array([profile.human_ceiling for profile in INTENTS])[which]
    slopes = np.array([profile.human_difficulty_slope for profile in INTENTS])[which]
    return np.clip(ceilings - slopes * difficulty, 0.0, 1.0)


def _repeat_curve(which: np.ndarray) -> np.ndarray:
    """Probability an unresolved contact of each intent comes back, from the declared curve."""
    return np.array([profile.repeat_when_unresolved for profile in INTENTS])[which]


def run(
    contacts: pd.DataFrame,
    policy: BotPolicy,
    centre: CentreProfile = CENTRE,
    chain: ChainProfile = SINGLE_RETURN,
    draws: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Run one policy against every contact.

    The session, in the order it happens:

    1. The contact is classified. It lands on the right intent when its own classifier draw falls
       under the accuracy its intent and difficulty imply, and on that intent's declared confusion
       target otherwise.
    2. A contact in the holdout arm, one a router deferred, or one whose **predicted** intent the
       policy refuses, goes straight to a human.
    3. Otherwise the bot tries. It resolves the contact if the contact is resolvable *and* the
       classification was right, and only if the turns that takes fit inside both the policy's
       budget and the customer's patience.
    4. Patience running out first is an abandonment. The budget running out first is an
       escalation, and an escalation costs a human the handoff on top of the handling.
    5. A human resolves the contact unless the declared human curve says they do not, which happens
       on about seven per cent of the volume and more on the hard end.
    6. A contact that ends unresolved comes back, if the customer was going to come back and would
       not have got there alone. **The repeat is a row of its own**, routed to a human, costing the
       same handling time again plus the handoff. Collapsing it into extra seconds on the original
       row, which is what the first version of this module did, makes deflection arithmetically
       identical to containment and hides the whole finding.
    7. And a contact still unresolved after that comes back **again**, as many times as the declared
       chain allows. The default allows one return and no more, which is the world waves 1 to 5
       published - passing it changes nothing at all, by identity rather than by tolerance.

    Args:
        contacts: The contact table from :func:`svclab.synth.contacts`.
        policy: The policy to run.
        centre: The centre's declared shape, for the per-turn and handoff costs.
        chain: How many times an unresolved contact returns, and what changes when it does. The
            default is the single return of waves 1 to 5.
        draws: The uniforms a longer chain needs, from :func:`svclab.synth.return_draws`. Required
            for a chain of more than two attempts, and unused by the default.

    Returns:
        A frame with the columns in :data:`OUTCOME_COLUMNS`.

    Raises:
        KeyError: If the contact table is missing a column the session needs.
        ValueError: If a chain longer than one return is asked for without the draws it needs.
    """
    if chain.max_attempts > 2 and draws is None:
        raise ValueError(
            f"a chain of {chain.max_attempts} attempts needs the return draws; pass "
            f"`draws=data.return_draws`"
        )
    given = draws if draws is not None else NO_RETURN_DRAWS
    missing = {
        "contact",
        "customer",
        "intent",
        "holdout",
        "difficulty",
        "bot_can_resolve",
        "would_self_serve",
        "human_seconds",
        "classifier_draw",
        "patience_turns",
        "repeats_if_unresolved",
        "human_resolves",
    } - set(contacts.columns)
    if missing:
        raise KeyError(f"the contact table is missing {sorted(missing)}")

    labels = np.array([profile.intent for profile in INTENTS])
    confused = np.array([profile.confused_with for profile in INTENTS])
    index = {profile.intent: position for position, profile in enumerate(INTENTS)}
    which = np.array([index[value] for value in contacts["intent"]], dtype=int)

    difficulty = contacts["difficulty"].to_numpy(dtype=float)
    correct = contacts["classifier_draw"].to_numpy(dtype=float) < _accuracy(difficulty, which)
    predicted = np.where(correct, labels[which], confused[which])

    refused = np.array([value in policy.straight_to_human for value in predicted])
    holdout = contacts["holdout"].to_numpy(dtype=bool)
    # An optional `defer` column lets a router send a contact past the bot without the policy having
    # refused its intent. Absent, nothing is deferred - so every figure published before this column
    # existed is unaffected by it.
    deferred = (
        contacts["defer"].to_numpy(dtype=bool)
        if "defer" in contacts.columns
        else np.zeros(len(contacts), dtype=bool)
    )
    to_human = holdout | refused | deferred | (policy.turn_budget == 0)

    needed = _turns_needed(difficulty)
    patience = contacts["patience_turns"].to_numpy(dtype=float)
    can = contacts["bot_can_resolve"].to_numpy(dtype=bool)

    # A resolvable, correctly classified contact resolves when the turns it needs fit in the budget
    # and the customer stays that long. Everything else divides into abandonment - patience ran out
    # before the budget did - and escalation.
    fits_budget = needed <= policy.turn_budget
    fits_patience = needed <= patience
    resolved_by_bot = ~to_human & can & correct & fits_budget & fits_patience
    spent = np.minimum(policy.turn_budget, patience)
    abandoned = ~to_human & ~resolved_by_bot & (patience < policy.turn_budget)
    escalated = ~to_human & ~resolved_by_bot & ~abandoned

    bot_turns = np.where(
        to_human, 0, np.where(resolved_by_bot, needed, np.asarray(spent, dtype=int))
    )
    outcome = np.where(
        to_human,
        "straight-to-human",
        np.where(resolved_by_bot, "resolved-by-bot", np.where(abandoned, "abandoned", "escalated")),
    )

    seconds = contacts["human_seconds"].to_numpy(dtype=float)
    handled_by_human = to_human | escalated
    human_seconds = np.where(
        to_human, seconds, np.where(escalated, seconds + centre.handoff_seconds, 0.0)
    )

    # A human does not resolve everything either. Awarding them a perfect score is the quiet
    # assumption that makes every automation comparison unfair in the same direction.
    human_resolves = contacts["human_resolves"].to_numpy(dtype=bool)
    resolved = resolved_by_bot | (handled_by_human & human_resolves)
    returns = (
        ~resolved
        & contacts["repeats_if_unresolved"].to_numpy(dtype=bool)
        & ~contacts["would_self_serve"].to_numpy(dtype=bool)
    )

    first = pd.DataFrame(
        {
            "session": contacts["contact"].to_numpy(),
            "contact": contacts["contact"].to_numpy(),
            "customer": contacts["customer"].to_numpy(),
            "intent": contacts["intent"].to_numpy(),
            "predicted_intent": predicted,
            "classified_correctly": correct,
            "route": np.where(
                holdout,
                "holdout",
                np.where(refused, "refused", np.where(deferred, "deferred", "bot")),
            ),
            "bot_turns": bot_turns,
            "outcome": outcome,
            "handled_by_human": handled_by_human,
            "resolved": resolved,
            "is_repeat": np.zeros(len(contacts), dtype=bool),
            "returns": returns,
            "human_seconds": human_seconds,
            "customer_seconds": bot_turns * centre.bot_seconds_per_turn,
        }
    )
    if not returns.any() or chain.max_attempts < 2:
        return first[list(OUTCOME_COLUMNS)]
    if int(contacts["contact"].max()) >= REPEAT_SESSION_OFFSET:
        raise ValueError(
            f"contact ids reach {int(contacts['contact'].max())}, which collides with the repeat "
            f"session offset of {REPEAT_SESSION_OFFSET}"
        )

    # The return stream, as rows, one attempt at a time. A session id is its contact's id plus the
    # offset times the attempt, so one column identifies a session across any set of runs while
    # `contact` keeps every return joinable to what caused it.
    #
    # The second attempt uses the draws the contact table already carries - `human_resolves` and
    # `repeats_if_unresolved` - so a chain of two attempts is bit-for-bit the world waves 1 to 5
    # published. Every attempt after that needs its own coin, because a human who failed once has to
    # be allowed to succeed the next time: reusing the first draw would make a chain that starts
    # badly never end, which is a model of an operation nobody has.
    frames = [first]
    open_rows = contacts[returns]
    open_index = np.flatnonzero(returns)
    for attempt in range(2, chain.max_attempts + 1):
        if open_rows.empty:
            break
        seconds = open_rows["human_seconds"].to_numpy(dtype=float) + centre.handoff_seconds
        if attempt == 2:
            resolved_now = open_rows["human_resolves"].to_numpy(dtype=bool)
        else:
            lift = chain.human_retry_lift ** (attempt - 2)
            chance = np.clip(
                _human_curve(difficulty[open_index], which[open_index]) * lift, 0.0, 1.0
            )
            resolved_now = _attempt_draw(given, attempt, open_rows, "u_human") < chance
        # Whether each still-unresolved contact comes back once more. The declared decay applies
        # from the third attempt on: the second is the one the earlier waves already drew.
        if attempt >= chain.max_attempts:
            again = np.zeros(len(open_rows), dtype=bool)
        else:
            decay = chain.return_decay ** (attempt - 1)
            chance = np.clip(_repeat_curve(which[open_index]) * decay, 0.0, 1.0)
            again = (
                ~resolved_now
                & (_attempt_draw(given, attempt + 1, open_rows, "u_return") < chance)
                & ~open_rows["would_self_serve"].to_numpy(dtype=bool)
            )
        frames.append(
            pd.DataFrame(
                {
                    "session": open_rows["contact"].to_numpy(dtype=int)
                    + REPEAT_SESSION_OFFSET * (attempt - 1),
                    "contact": open_rows["contact"].to_numpy(),
                    "customer": open_rows["customer"].to_numpy(),
                    "intent": open_rows["intent"].to_numpy(),
                    "predicted_intent": open_rows["intent"].to_numpy(),
                    "classified_correctly": np.ones(len(open_rows), dtype=bool),
                    "route": np.repeat("repeat", len(open_rows)),
                    "bot_turns": np.zeros(len(open_rows), dtype=int),
                    "outcome": np.repeat("repeat-to-human", len(open_rows)),
                    "handled_by_human": np.ones(len(open_rows), dtype=bool),
                    "resolved": resolved_now,
                    "is_repeat": np.ones(len(open_rows), dtype=bool),
                    "returns": again,
                    "human_seconds": seconds,
                    "customer_seconds": np.zeros(len(open_rows), dtype=float),
                }
            )
        )
        open_index = open_index[again]
        open_rows = open_rows[again]
    return pd.concat(frames, ignore_index=True)[list(OUTCOME_COLUMNS)]


def _attempt_draw(draws: pd.DataFrame, attempt: int, rows: pd.DataFrame, column: str) -> np.ndarray:
    """One column of the return draws, for one attempt, aligned to the open contacts.

    Takes a frame rather than an optional one: :func:`run` refuses a long chain without draws before
    it gets here, so a second guard for the same thing was unreachable - the coverage report said so
    and it is recorded in ``docs/ROADMAP.md``. An empty frame still arrives when a two-attempt chain
    is given none, and the alignment check below is what catches anything the caller got wrong.

    Raises:
        ValueError: If the draws do not cover this attempt, which is a chain asking for a coin that
        was never flipped rather than a missing value to guess at.
    """
    slice_ = draws[draws["attempt"] == attempt].set_index("contact")[column]
    aligned = slice_.reindex(rows["contact"].to_numpy())
    if aligned.isna().any():
        raise ValueError(f"the return draws do not cover attempt {attempt} for every open contact")
    return aligned.to_numpy(dtype=float)

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

from svclab.synth import CENTRE, INTENTS, CentreProfile

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

#: Repeats one unresolved contact may generate. One, declared rather than inferred: a customer whose
#: second attempt also fails does not come back a third time here, which makes every figure in this
#: repository an underestimate of what an automation costs the queue.
MAX_REPEATS = 1

#: What a repeat session's id is offset from its contact's id by. A constant rather than "one past
#: the largest contact in this call", which is what the first version used: that made ids unique
#: only *within* one call, so pooling the treated and control arms - which is exactly what a quality
#: study does - produced two different sessions sharing an id. Derived from the contact id instead,
#: so a session id is unique across any set of runs over disjoint contacts and stable whatever
#: subset is passed in.
REPEAT_SESSION_OFFSET = 1_000_000

#: Turns a bot needs to resolve a contact it can resolve, at difficulty zero and at difficulty one.
#: Not a policy parameter: it is a property of the conversation, and it is why a longer turn budget
#: buys anything at all.
TURNS_AT_EASIEST = 1
TURNS_AT_HARDEST = 5


def _accuracy(difficulty: np.ndarray, which: np.ndarray) -> np.ndarray:
    """Probability the classifier labels each contact correctly, from its declared curve."""
    ceilings = np.array([profile.classifier_ceiling for profile in INTENTS])[which]
    slopes = np.array([profile.classifier_difficulty_slope for profile in INTENTS])[which]
    return np.clip(ceilings - slopes * difficulty, 0.0, 1.0)


def _turns_needed(difficulty: np.ndarray) -> np.ndarray:
    """Bot turns a resolvable contact takes, rising with difficulty."""
    span = TURNS_AT_HARDEST - TURNS_AT_EASIEST
    return np.asarray(TURNS_AT_EASIEST + np.round(difficulty * span), dtype=int)


def run(
    contacts: pd.DataFrame,
    policy: BotPolicy,
    centre: CentreProfile = CENTRE,
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

    Args:
        contacts: The contact table from :func:`svclab.synth.contacts`.
        policy: The policy to run.
        centre: The centre's declared shape, for the per-turn and handoff costs.

    Returns:
        A frame with the columns in :data:`OUTCOME_COLUMNS`.

    Raises:
        KeyError: If the contact table is missing a column the session needs.
    """
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
    if not returns.any():
        return first[list(OUTCOME_COLUMNS)]

    # The repeat stream, as rows. A repeat's session id is its contact's id plus a fixed offset, so
    # one column identifies a session across any set of runs while `contact` keeps the repeat
    # joinable to what caused it.
    back = contacts[returns]
    if int(contacts["contact"].max()) >= REPEAT_SESSION_OFFSET:
        raise ValueError(
            f"contact ids reach {int(contacts['contact'].max())}, which collides with the repeat "
            f"session offset of {REPEAT_SESSION_OFFSET}"
        )
    again = pd.DataFrame(
        {
            "session": back["contact"].to_numpy(dtype=int) + REPEAT_SESSION_OFFSET,
            "contact": back["contact"].to_numpy(),
            "customer": back["customer"].to_numpy(),
            "intent": back["intent"].to_numpy(),
            "predicted_intent": back["intent"].to_numpy(),
            "classified_correctly": np.ones(len(back), dtype=bool),
            "route": np.repeat("repeat", len(back)),
            "bot_turns": np.zeros(len(back), dtype=int),
            "outcome": np.repeat("repeat-to-human", len(back)),
            "handled_by_human": np.ones(len(back), dtype=bool),
            "resolved": back["human_resolves"].to_numpy(dtype=bool),
            "is_repeat": np.ones(len(back), dtype=bool),
            "returns": np.zeros(len(back), dtype=bool),
            "human_seconds": back["human_seconds"].to_numpy(dtype=float) + centre.handoff_seconds,
            "customer_seconds": np.zeros(len(back), dtype=float),
        }
    )
    return pd.concat([first, again], ignore_index=True)[list(OUTCOME_COLUMNS)]

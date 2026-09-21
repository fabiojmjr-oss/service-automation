"""A bot that actually runs, and the line between what it decides and what happens to it.

:mod:`~svclab.bot.policy` is the deployable part: how many turns the bot gets, and which predicted
intents it refuses to attempt. It sees the predicted intent and the turn number, and nothing more.

:mod:`~svclab.bot.session` is the world: it reads the whole contact, including the difficulty and
the counterfactual a policy may not see, and works out what happens. No draw happens there, so two
policies meet the same contacts and any difference between them is the policy.
"""

from .policy import GUARDED, HUMAN_ONLY, PATIENT, POLICIES, THREE_TURNS, BotPolicy
from .session import (
    OUTCOME_COLUMNS,
    OUTCOMES,
    REPEAT_SESSION_OFFSET,
    TURNS_AT_EASIEST,
    TURNS_AT_HARDEST,
    run,
)

__all__ = [
    "GUARDED",
    "HUMAN_ONLY",
    "OUTCOMES",
    "OUTCOME_COLUMNS",
    "PATIENT",
    "POLICIES",
    "REPEAT_SESSION_OFFSET",
    "THREE_TURNS",
    "TURNS_AT_EASIEST",
    "TURNS_AT_HARDEST",
    "BotPolicy",
    "run",
]

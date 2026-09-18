"""A seeded contact centre, including the columns no real one has.

The two that matter are ``difficulty`` - how hard each contact actually is - and
``would_self_serve`` - whether the customer would have got there with no help at all. Between them
they are why a containment rate can be checked against something instead of against another
containment rate.

Every draw is an inverse transform of the uniform stream, and everything random is drawn before any
bot runs, so a bot is a deterministic function of the dataset. Two policies compared here differ by
their policy and by nothing else.
"""

from .config import (
    CENTRE,
    GRADERS,
    INTENTS,
    JUDGE,
    QUALITY,
    SEED,
    CentreProfile,
    GraderProfile,
    IntentProfile,
    QualityProfile,
)
from .contacts import CONTACT_COLUMNS, INTENT_TRUTH_COLUMNS, contacts, intent_truth
from .dataset import Dataset, generate_dataset
from .quality import JUDGE_NOISE_COLUMNS, PANEL_NOISE_COLUMNS, quality_noise

__all__ = [
    "CENTRE",
    "CONTACT_COLUMNS",
    "GRADERS",
    "INTENTS",
    "INTENT_TRUTH_COLUMNS",
    "JUDGE",
    "JUDGE_NOISE_COLUMNS",
    "PANEL_NOISE_COLUMNS",
    "QUALITY",
    "SEED",
    "CentreProfile",
    "Dataset",
    "GraderProfile",
    "IntentProfile",
    "QualityProfile",
    "contacts",
    "generate_dataset",
    "intent_truth",
    "quality_noise",
]

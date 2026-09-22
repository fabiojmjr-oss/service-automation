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
    CHAIN,
    CONCENTRATION,
    EQUAL_RATES,
    GRADERS,
    INTENTS,
    JUDGE,
    POPULATION,
    QUALITY,
    ROUTING,
    SEED,
    SINGLE_RETURN,
    WORKFORCE,
    CentreProfile,
    ChainProfile,
    ConcentrationProfile,
    GraderProfile,
    IntentProfile,
    PopulationProfile,
    QualityProfile,
    RoutingProfile,
    WorkforceProfile,
)
from .contacts import (
    CONTACT_COLUMNS,
    INTENT_TRUTH_COLUMNS,
    TRUTH_DRAW_COLUMNS,
    contacts,
    intent_truth,
)
from .customers import CUSTOMER_COLUMNS, blend, correlated_contacts, customer_components
from .dataset import Dataset, concentrated_dataset, correlated_dataset, generate_dataset
from .frequency import propensity, reassign_customers
from .quality import JUDGE_NOISE_COLUMNS, PANEL_NOISE_COLUMNS, quality_noise
from .returns import RETURN_DRAW_COLUMNS, return_draws
from .routing import ROUTING_SCORE_COLUMNS, accuracy_curve, routing_scores

__all__ = [
    "CENTRE",
    "CONTACT_COLUMNS",
    "GRADERS",
    "INTENTS",
    "INTENT_TRUTH_COLUMNS",
    "CHAIN",
    "CONCENTRATION",
    "CUSTOMER_COLUMNS",
    "EQUAL_RATES",
    "JUDGE",
    "JUDGE_NOISE_COLUMNS",
    "POPULATION",
    "PANEL_NOISE_COLUMNS",
    "QUALITY",
    "RETURN_DRAW_COLUMNS",
    "ROUTING",
    "ROUTING_SCORE_COLUMNS",
    "SEED",
    "SINGLE_RETURN",
    "WORKFORCE",
    "TRUTH_DRAW_COLUMNS",
    "CentreProfile",
    "ChainProfile",
    "ConcentrationProfile",
    "Dataset",
    "GraderProfile",
    "IntentProfile",
    "PopulationProfile",
    "QualityProfile",
    "RoutingProfile",
    "WorkforceProfile",
    "accuracy_curve",
    "blend",
    "concentrated_dataset",
    "contacts",
    "correlated_contacts",
    "correlated_dataset",
    "customer_components",
    "generate_dataset",
    "intent_truth",
    "propensity",
    "quality_noise",
    "reassign_customers",
    "return_draws",
    "routing_scores",
]

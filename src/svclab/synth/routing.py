"""The confidence a routing classifier reports, drawn after everything the earlier waves draw.

One column, and where it sits in the stream is the point. The score could have been appended to
:func:`svclab.synth.contacts`, and doing that would have shifted every draw the quality panel
consumes and moved every figure wave 2 published. It is drawn here instead, after
:func:`svclab.synth.quality_noise`, and joined to the contacts by id.

The score is a **margin**, not a probability. A contact is labelled correctly when its classifier
draw falls under the accuracy its intent and difficulty imply, so the distance between those two is
how comfortably the label was reached - and the score is that distance, rescaled into the unit
interval and blurred by a declared spread. It therefore ranks correctness without being calibrated
to it, which is the situation a real threshold is chosen in.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._draws import normal_from, uniform
from .config import INTENTS, ROUTING, RoutingProfile

#: Columns of the routing score frame. ``u_score`` is the blur, kept so that a population where
#: difficulty is partly the customer can be scored by the identical classifier rather than by a
#: differently blurred one.
ROUTING_SCORE_COLUMNS = ("contact", "classifier_score", "u_score")


def accuracy_curve(difficulty: np.ndarray, which: np.ndarray) -> np.ndarray:
    """Probability the classifier labels each contact correctly, from its declared curve.

    The same curve :mod:`svclab.bot.session` applies, exposed here because the score is built from
    it. Two copies of one formula would be two places for it to drift.
    """
    ceilings = np.array([profile.classifier_ceiling for profile in INTENTS])[which]
    slopes = np.array([profile.classifier_difficulty_slope for profile in INTENTS])[which]
    return np.clip(ceilings - slopes * difficulty, 0.0, 1.0)


def routing_scores(
    rng: np.random.Generator,
    contacts: pd.DataFrame,
    routing: RoutingProfile = ROUTING,
) -> pd.DataFrame:
    """One confidence score per contact, ranking correctness without being calibrated to it.

    Args:
        rng: The shared generator, consumed after every earlier draw in the dataset.
        contacts: The contact table, for the difficulty and the classifier draw.
        routing: The declared spread.

    Returns:
        A frame with the columns in :data:`ROUTING_SCORE_COLUMNS`.

    Raises:
        KeyError: If the contact table is missing a column the score is built from.
    """
    return scores_from(contacts, uniform(rng, len(contacts)), routing)


def scores_from(
    contacts: pd.DataFrame,
    percentile: np.ndarray,
    routing: RoutingProfile = ROUTING,
) -> pd.DataFrame:
    """The same scores from a blur already drawn.

    Args:
        contacts: The contact table, for the difficulty and the classifier draw.
        percentile: One uniform per contact, the blur's percentile.
        routing: The declared spread.

    Returns:
        A frame with the columns in :data:`ROUTING_SCORE_COLUMNS`.

    Raises:
        KeyError: If the contact table is missing a column the score is built from.
    """
    missing = {"contact", "intent", "difficulty", "classifier_draw"} - set(contacts.columns)
    if missing:
        raise KeyError(f"the contact table is missing {sorted(missing)}")
    index = {profile.intent: position for position, profile in enumerate(INTENTS)}
    which = np.array([index[value] for value in contacts["intent"]], dtype=int)
    difficulty = contacts["difficulty"].to_numpy(dtype=float)
    margin = accuracy_curve(difficulty, which) - contacts["classifier_draw"].to_numpy(dtype=float)
    blurred = 0.5 + margin / 2.0 + normal_from(percentile, routing.score_noise_sd)
    return pd.DataFrame(
        {
            "contact": contacts["contact"].to_numpy(),
            "classifier_score": np.clip(blurred, 0.0, 1.0),
            "u_score": percentile,
        }
    )[list(ROUTING_SCORE_COLUMNS)]

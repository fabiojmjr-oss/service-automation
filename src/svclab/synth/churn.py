"""One uniform per contact for whether the customer stops coming back, drawn after everything else.

A leave decision cannot be drawn per **session**, because sessions are a function of the policy and
the whole discipline of this generator is that everything random is drawn before any bot exists. So
it is drawn per contact and spent against whatever that contact's experience turned out to be: the
same uniform meets a different threshold under a different policy, which is how waves 4 and 5
isolate a structural change from sampling noise.

Drawn last of all, after the chain's returns, for the same reason every table since wave 2 has been:
a draw at the end of the stream cannot move a figure that was published before it existed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._draws import uniform
from .config import CENTRE, CentreProfile

#: Columns of the churn-draw frame, one row per contact.
CHURN_DRAW_COLUMNS = ("contact", "u_leave")


def churn_draws(rng: np.random.Generator, centre: CentreProfile = CENTRE) -> pd.DataFrame:
    """One uniform per contact: how unlucky the experience has to be to end the relationship.

    Args:
        rng: The shared generator, consumed after every other table in the dataset.
        centre: The centre's declared shape, for the number of contacts.

    Returns:
        A frame with the columns in :data:`CHURN_DRAW_COLUMNS`.
    """
    return pd.DataFrame(
        {
            "contact": np.arange(centre.contacts, dtype=int),
            "u_leave": uniform(rng, centre.contacts),
        }
    )[list(CHURN_DRAW_COLUMNS)]

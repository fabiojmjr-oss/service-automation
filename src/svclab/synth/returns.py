"""The draws a chain of return visits needs, and where they sit in the stream.

Waves 1 to 5 needed one uniform per contact to decide whether an unresolved contact comes back, and
it is already in the contact table as ``repeats_if_unresolved``. A **chain** needs two more per
attempt: whether the customer comes back again, and whether the human resolves it this time.

They are drawn here, last of everything, and in long form - one row per contact and attempt. Long
form rather than a column per attempt because the number of attempts is a declared parameter, and a
table whose shape depends on a parameter is a table that cannot be joined to anything.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._draws import uniform
from .config import CENTRE, CHAIN, CentreProfile, ChainProfile

#: Columns of the return-draw frame, one row per contact and further attempt.
RETURN_DRAW_COLUMNS = ("contact", "attempt", "u_return", "u_human")


def return_draws(
    rng: np.random.Generator,
    centre: CentreProfile = CENTRE,
    chain: ChainProfile = CHAIN,
) -> pd.DataFrame:
    """Two uniforms per contact per further attempt: coming back, and being resolved.

    Drawn for the longest chain the profile allows, so shortening a chain consumes a prefix of the
    same draws rather than a different stream. That is what lets two chain lengths be compared on
    the same noise.

    Args:
        rng: The shared generator, consumed after every other table in the dataset.
        centre: The centre's declared shape, for the number of contacts.
        chain: The declared chain, for the number of attempts.

    Returns:
        A frame with the columns in :data:`RETURN_DRAW_COLUMNS`, empty when the chain allows no
        further attempt at all.

    Raises:
        ValueError: If the chain allows fewer than one attempt.
    """
    if chain.max_attempts < 1:
        raise ValueError(f"a contact has at least one attempt, not {chain.max_attempts}")
    further = chain.max_attempts - 1
    if further <= 0:
        return pd.DataFrame({name: [] for name in RETURN_DRAW_COLUMNS})
    rows = centre.contacts * further
    coming_back = uniform(rng, rows)
    resolved = uniform(rng, rows)
    return pd.DataFrame(
        {
            "contact": np.tile(np.arange(centre.contacts, dtype=int), further),
            "attempt": np.repeat(np.arange(2, chain.max_attempts + 1, dtype=int), centre.contacts),
            "u_return": coming_back,
            "u_human": resolved,
        }
    )[list(RETURN_DRAW_COLUMNS)]

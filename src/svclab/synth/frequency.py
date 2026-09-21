"""Who contacts, how often, and whether those are the same people the bot cannot help.

Waves 1 to 4 assign each contact to a customer by a uniform draw, so the number of contacts a
customer makes is Poisson with a mean below two and the busiest customer in the account is busy by
accident. Wave 4 gave a customer traits; this module gives them a **rate**.

The mechanism is the draw that was already made. Every contact's customer came from one uniform,
kept in the contact table as ``u_customer``, and reassigning it through a different set of weights
is the same inverse transform against a different distribution. Nothing is redrawn, and two
properties are preserved exactly:

- **every contact keeps its arm**, because a contact is reassigned only among customers of its own
  arm. The treated and holdout arms therefore hold the identical contacts they held before;
- **every contact keeps every trait**. Difficulty, handling time, patience and the two
  counterfactual columns are untouched.

So each per-contact aggregate the earlier waves published is not merely close in the reassigned
world - it is **identical**, bit for bit. What changes is only which contacts share a person, which
is the definition of a clustering assumption and nothing else.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._draws import to_latent
from .config import CONCENTRATION, ConcentrationProfile
from .customers import blend


def propensity(
    components: pd.DataFrame, concentration: ConcentrationProfile = CONCENTRATION
) -> np.ndarray:
    """Each customer's relative contact rate, log-normal and correlated with their difficulty.

    Args:
        components: The per-customer percentiles from :func:`customer_components`.
        concentration: The declared dispersion and correlation.

    Returns:
        One positive weight per row of ``components``, in that order. The scale is arbitrary: only
        the ratios between customers matter, because the weights are normalised when they are used.

    Raises:
        ValueError: If the dispersion is negative.
    """
    if concentration.dispersion < 0.0:
        raise ValueError(f"a dispersion is not negative, got {concentration.dispersion}")
    # blend takes the share of latent variance, and the correlation between the blended value and
    # the customer's difficulty is the square root of it - so a declared correlation is squared here
    # and comes back out of the construction as itself.
    blended = blend(
        components["propensity_percentile"].to_numpy(dtype=float),
        components["difficulty_percentile"].to_numpy(dtype=float),
        concentration.difficulty_correlation**2,
    )
    return np.exp(concentration.dispersion * to_latent(blended))


def reassign_customers(
    table: pd.DataFrame,
    components: pd.DataFrame,
    concentration: ConcentrationProfile = CONCENTRATION,
) -> pd.DataFrame:
    """The same contacts, grouped into customers who do not all contact equally often.

    Args:
        table: A contact table carrying ``customer``, ``holdout`` and ``u_customer``.
        components: The per-customer percentiles from :func:`customer_components`.
        concentration: The declared dispersion and correlation.

    Returns:
        A copy of the table with ``customer`` reassigned. Every other column, including ``holdout``,
        is unchanged.

    Raises:
        KeyError: If the table is missing a column the reassignment needs.
    """
    missing = {"customer", "holdout", "u_customer"} - set(table.columns)
    if missing:
        raise KeyError(f"the contact table is missing {sorted(missing)}")

    weights = propensity(components, concentration)
    by_customer = pd.Series(weights, index=components["customer"].to_numpy(dtype=int))
    assigned = table["customer"].to_numpy(dtype=int).copy()
    arms = table["holdout"].to_numpy(dtype=bool)
    percentile = table["u_customer"].to_numpy(dtype=float)

    # Arm by arm, so that a customer cannot straddle the line the holdout was drawn along. The pool
    # is the customers this account actually saw in that arm: a customer with no contacts at all has
    # no arm to be reassigned within, and inventing one would change the denominators every earlier
    # wave reported.
    for arm in (False, True):
        rows = np.flatnonzero(arms == arm)
        pool = np.unique(assigned[rows])
        cumulative = np.cumsum(by_customer.reindex(pool).to_numpy(dtype=float))
        cumulative = cumulative / cumulative[-1]
        picked = np.searchsorted(cumulative, percentile[rows], side="right")
        assigned[rows] = pool[np.clip(picked, 0, pool.size - 1)]

    return table.assign(customer=assigned)

"""Sizing a comparison between two bot policies, when the unit of analysis is not the contact.

Everything in waves 1 and 2 compared two policies on the whole account. A real deployment tests one
policy against another on a fraction of the volume, and the fraction has to be sized. The arithmetic
for that is in every textbook, applied to independent observations.

**Contacts are not independent, because customers come back.** One person's two contacts share
everything about that person - how patient they are, how hard their problem is, whether they are the
sort to abandon - so they carry less information than two contacts from two people. A test
randomised by customer and analysed by contact is counting each customer's contacts as if they were
strangers.

The correction is one number. With clusters averaging ``m`` contacts and an intra-cluster
correlation ``rho``, every variance is inflated by the **design effect** ``1 + (m - 1) * rho``, so
the sample needed is multiplied by it. Two consequences, and the second is the one that gets a
result published that should not have been.

**The test needs more contacts than the textbook says**, by exactly that factor.

**And a test that ignores it does not merely lose power - it runs at the wrong error rate.** A
nominal five per cent, analysed per contact on clustered data, is really running at ``2 * (1 - Phi(z
/ sqrt(deff)))`` - and that is a number this module will print for you, because it is usually the
first time anybody has seen it.
"""

from __future__ import annotations

import math

import pandas as pd
from scipy import stats

#: Columns of the sizing table, one row per scenario.
SIZING_COLUMNS = (
    "scenario",
    "mean_cluster_size",
    "icc",
    "design_effect",
    "contacts_per_arm",
    "customers_per_arm",
    "nominal_alpha",
    "actual_alpha",
)


def design_effect(mean_cluster_size: float, icc: float) -> float:
    """``1 + (m - 1) * rho``: how many times a clustered sample's variance exceeds an independent
    one.

    One when the clusters hold a single observation each, and one when the correlation inside them
    is zero. Equal to the cluster size when the correlation is total, which is the honest statement
    that a cluster of identical observations is one observation.

    Args:
        mean_cluster_size: Average observations per cluster.
        icc: Intra-cluster correlation.

    Returns:
        The design effect, never below one for a non-negative correlation.

    Raises:
        ValueError: If the cluster size is below one, or the correlation is outside ``[-1, 1]``.
    """
    if mean_cluster_size < 1.0:
        raise ValueError(f"a cluster holds at least one observation, got {mean_cluster_size}")
    if not -1.0 <= icc <= 1.0:
        raise ValueError(f"a correlation has to be between minus one and one, got {icc}")
    return 1.0 + (mean_cluster_size - 1.0) * icc


def intracluster_correlation(frame: pd.DataFrame, cluster: str, outcome: str) -> float:
    """The share of an outcome's variance that lives between clusters rather than inside them.

    Estimated by the analysis-of-variance method, which handles the unequal cluster sizes a real
    account has: clusters contribute a between-groups mean square and a within-groups one, and the
    correlation is their standardised difference. Negative estimates are possible when the clusters
    genuinely carry no signal, and are returned rather than clipped, because clipping a negative
    variance estimate to zero hides that the model does not fit.

    Args:
        frame: One row per observation.
        cluster: Column identifying the cluster - here, the customer.
        outcome: The binary or numeric outcome.

    Returns:
        The estimate.

    Raises:
        ValueError: If there are fewer than two clusters, or every cluster holds one observation -
        in which case there is nothing inside a cluster to correlate.
    """
    for column in (cluster, outcome):
        if column not in frame.columns:
            raise ValueError(f"{column!r} is not a column of this frame")
    values = frame[outcome].to_numpy(dtype=float)
    groups = frame[cluster].to_numpy()
    sizes = pd.Series(values).groupby(groups).size().to_numpy(dtype=float)
    if sizes.size < 2:
        raise ValueError("an intra-cluster correlation needs at least two clusters")
    if float(sizes.max()) <= 1.0:
        raise ValueError(
            "every cluster holds one observation, so there is nothing inside a cluster to correlate"
        )
    means = pd.Series(values).groupby(groups).mean().to_numpy(dtype=float)
    grand = float(values.mean())
    total = float(values.size)
    clusters = float(sizes.size)

    between = float((sizes * (means - grand) ** 2).sum() / (clusters - 1.0))
    # The within-cluster sum of squares, by the identity that avoids a loop over clusters:
    # sum over groups of sum over members of (y - group mean)^2 equals sum of y^2 minus the
    # size-weighted sum of squared group means.
    within_ss = float((values**2).sum()) - float((sizes * means**2).sum())
    # No guard on the degrees of freedom here: with two clusters or more and at least one holding
    # two observations - both checked above - the total exceeds the cluster count, so the divisor is
    # at least one. The first version of this function guarded it anyway and the coverage report
    # found the branch unreachable, which is the argument settled rather than debated.
    within = within_ss / (total - clusters)

    # The ANOVA estimator's effective cluster size, which is the harmonic-ish correction for unequal
    # sizes rather than the plain mean.
    effective = (total - float((sizes**2).sum()) / total) / (clusters - 1.0)
    denominator = between + (effective - 1.0) * within
    if denominator == 0.0:
        return 0.0
    return (between - within) / denominator


def actual_alpha(nominal_alpha: float, effect: float) -> float:
    """The error rate a test really runs at when it ignores its clustering.

    The statistic was divided by a standard error that is too small by ``sqrt(design effect)``, so
    the critical value it is compared against is effectively that much closer to zero.

    Args:
        nominal_alpha: The level the test believes it is running at.
        effect: The design effect it ignored.

    Returns:
        The two-sided error rate it is really running at.

    Raises:
        ValueError: If the level is not in ``(0, 1)`` or the design effect is below one.
    """
    if not 0.0 < nominal_alpha < 1.0:
        raise ValueError(f"alpha has to be between zero and one, got {nominal_alpha}")
    if effect < 1.0:
        raise ValueError(f"a design effect below one is not an inflation, got {effect}")
    critical = float(stats.norm.ppf(1.0 - nominal_alpha / 2.0))
    return float(2.0 * (1.0 - stats.norm.cdf(critical / math.sqrt(effect))))


def contacts_for_difference(
    first_rate: float,
    second_rate: float,
    effect: float = 1.0,
    power: float = 0.80,
    alpha: float = 0.05,
) -> float:
    """Contacts per arm needed to detect a difference in a rate, clustering included.

    The ordinary two-proportion sample size, multiplied by the design effect. Not rounded, so that
    the ratio between two of these is readable.

    Args:
        first_rate: Rate in one arm.
        second_rate: Rate in the other.
        effect: The design effect. One is the textbook answer, which assumes the contacts are
            strangers to each other.
        power: Power to detect the difference.
        alpha: Two-sided significance level.

    Returns:
        Contacts per arm.

    Raises:
        ValueError: If the two rates are equal, or any argument is outside its range.
    """
    for name, value in (("first rate", first_rate), ("second rate", second_rate)):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"the {name} has to be between zero and one, got {value}")
    if not 0.0 < power < 1.0:
        raise ValueError(f"power has to be between zero and one, got {power}")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha has to be between zero and one, got {alpha}")
    if effect < 1.0:
        raise ValueError(f"a design effect below one is not an inflation, got {effect}")
    if first_rate == second_rate:
        raise ValueError("there is no difference to detect between two equal rates")
    critical = float(stats.norm.ppf(1.0 - alpha / 2.0))
    detect = float(stats.norm.ppf(power))
    pooled = (first_rate + second_rate) / 2.0
    numerator = critical * math.sqrt(2.0 * pooled * (1.0 - pooled)) + detect * math.sqrt(
        first_rate * (1.0 - first_rate) + second_rate * (1.0 - second_rate)
    )
    return (numerator / (first_rate - second_rate)) ** 2 * effect


def sizing_table(
    scenarios: dict[str, tuple[float, float]],
    first_rate: float,
    second_rate: float,
    mean_cluster_size: float,
    power: float = 0.80,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Several correlation assumptions priced side by side, in contacts and in customers.

    Args:
        scenarios: Named ``(mean_cluster_size, icc)`` pairs. A scenario with a cluster size of one
        is the per-contact test that believes its observations are independent. first_rate: Rate in
        one arm. second_rate: Rate in the other. mean_cluster_size: Contacts per customer, for
        converting contacts into customers to recruit. power: Power to detect the difference. alpha:
        Two-sided significance level.

    Returns:
        A frame with the columns in :data:`SIZING_COLUMNS`.

    Raises:
        ValueError: If no scenarios are supplied.
    """
    if not scenarios:
        raise ValueError("there are no scenarios to price")
    rows = []
    for name, (size, icc) in scenarios.items():
        effect = design_effect(size, icc)
        contacts = contacts_for_difference(first_rate, second_rate, effect, power, alpha)
        rows.append(
            {
                "scenario": name,
                "mean_cluster_size": size,
                "icc": icc,
                "design_effect": effect,
                "contacts_per_arm": contacts,
                "customers_per_arm": contacts / mean_cluster_size,
                "nominal_alpha": alpha,
                "actual_alpha": actual_alpha(alpha, effect),
            }
        )
    return pd.DataFrame(rows)[list(SIZING_COLUMNS)]

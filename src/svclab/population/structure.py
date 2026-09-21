"""What the independence assumption was worth, measured against a world without it.

Wave 3 priced the design effect of clustering at *declared* correlations, because the generator drew
every trait per contact and the correlation it could measure was zero. :mod:`svclab.synth.customers`
closes that: the same account exists twice, once with a customer as a label and once with a customer
as a person, built from the identical noise and with identical marginal distributions. Everything
here is a comparison between those two worlds, where the independent one is the **control** rather
than the baseline - it absorbs whatever the estimators do on data with no structure in it, which
turns out to matter more than expected.

Four questions, in the order the answers stopped being obvious:

1. What does the correlation do to the figures the earlier waves published?
2. How much of a correlation between *people* survives into the outcome a test is run on?
3. What does the surviving part cost a comparison?
4. And what does an analyst pay for correcting it the way it is usually corrected?
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd
from scipy import stats

from svclab.containment import containment_table
from svclab.experiment import (
    actual_alpha,
    design_effect,
    effective_cluster_size,
    intracluster_correlation,
)
from svclab.synth import CENTRE, POPULATION, CentreProfile, PopulationProfile
from svclab.synth.customers import latent_traits

#: Columns of the table that says whether the correlation moved anything already published.
WORLD_COLUMNS = ("metric", "independent", "correlated", "difference")

#: Columns of the attenuation chain, one row per stage.
CORRELATION_COLUMNS = ("stage", "difficulty", "patience", "resolution")

#: Columns of the design-effect table, one row per world.
DESIGN_COLUMNS = (
    "world",
    "icc",
    "mean_cluster_size",
    "effective_cluster_size",
    "design_effect",
    "design_effect_at_mean",
    "sample_inflation",
    "nominal_alpha",
    "actual_alpha",
)

#: Columns of the repeat-failure table, one row per world.
PAIR_COLUMNS = (
    "world",
    "pairs",
    "failure_rate",
    "both_failed",
    "expected_if_independent",
    "ratio",
)

#: Columns of the standard-error table, one row per world.
ERROR_COLUMNS = (
    "world",
    "estimate",
    "naive_se",
    "cluster_mean_se",
    "corrected_se",
    "cluster_mean_ratio",
    "corrected_ratio",
)


def _first_sessions(outcomes: pd.DataFrame) -> pd.DataFrame:
    """One row per contact, the repeat rows dropped, with the failure flag the tables need."""
    first = outcomes[~outcomes["is_repeat"]].copy()
    first["resolved"] = first["resolved"].astype(float)
    first["failed"] = 1.0 - first["resolved"]
    return first


def world_table(
    contacts: Mapping[str, pd.DataFrame],
    outcomes: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """The figures the earlier waves published, in both worlds.

    This is the table to read first, and the reason the copula was chosen over the convex
    combination it replaced: the marginal distribution of every trait is unchanged, so the levels
    should not move. If they do, the comparison that follows is measuring two things at once.

    Args:
        contacts: Contact tables by world label.
        outcomes: Outcome frames by the same labels, from :func:`svclab.bot.run`.

    Returns:
        A frame with the columns in :data:`WORLD_COLUMNS`.

    Raises:
        KeyError: If the two mappings do not carry the same two labels.
    """
    labels = _two_labels(contacts, outcomes)
    left, right = labels
    rows = []
    for metric, values in _world_metrics(contacts, outcomes, labels).items():
        rows.append(
            {
                "metric": metric,
                "independent": values[left],
                "correlated": values[right],
                "difference": values[right] - values[left],
            }
        )
    return pd.DataFrame(rows)[list(WORLD_COLUMNS)]


def _two_labels(
    contacts: Mapping[str, pd.DataFrame], outcomes: Mapping[str, pd.DataFrame]
) -> tuple[str, str]:
    """The two world labels, in the order given, with the mappings checked against each other."""
    if set(contacts) != set(outcomes):
        raise KeyError(f"contacts cover {sorted(contacts)} and outcomes {sorted(outcomes)}")
    if len(contacts) != 2:
        raise KeyError(f"two worlds are compared here, not {len(contacts)}")
    first, second = list(contacts)
    return first, second


def _world_metrics(
    contacts: Mapping[str, pd.DataFrame],
    outcomes: Mapping[str, pd.DataFrame],
    labels: tuple[str, str],
) -> dict[str, dict[str, float]]:
    """Each published metric, by world."""
    named = (
        "mean difficulty",
        "difficulty sd",
        "mean patience turns",
        "session containment",
        "needed containment",
        "resolution rate",
        "repeats per contact",
        "human hours",
    )
    metrics: dict[str, dict[str, float]] = {name: {} for name in named}
    for label in labels:
        table = contacts[label]
        metrics["mean difficulty"][label] = float(table["difficulty"].mean())
        metrics["difficulty sd"][label] = float(table["difficulty"].std(ddof=1))
        metrics["mean patience turns"][label] = float(table["patience_turns"].mean())
        # Through wave 1's own table rather than recomputed here. Two definitions of containment in
        # one repository would be two places for it to drift, and this module's whole claim is that
        # the figures already published do not move.
        summary = containment_table({label: outcomes[label]}, table).iloc[0]
        metrics["session containment"][label] = float(summary["session_containment"])
        metrics["needed containment"][label] = float(summary["needed_containment"])
        metrics["resolution rate"][label] = float(summary["resolution_rate"])
        metrics["repeats per contact"][label] = float(summary["repeats_per_contact"])
        metrics["human hours"][label] = float(summary["human_hours"])
    return metrics


def correlation_table(
    contacts: Mapping[str, pd.DataFrame],
    outcomes: Mapping[str, pd.DataFrame],
    centre: CentreProfile = CENTRE,
    population: PopulationProfile = POPULATION,
) -> pd.DataFrame:
    """The declared correlation, and how much of it is left at each stage.

    Four stages, and the distance between the first and the last is the finding:

    - **declared**: the share of latent variance given to the customer.
    - **latent**: the same quantity measured on the latent scale, where the copula is exact.
    - **observed**: measured on the trait itself, attenuated by the trait's own quantile transform -
      and, for patience, by the fact that a patience is a whole number of turns.
    - **outcome**: measured on the thing a test is actually run on. A resolution is a coin whose
      bias is correlated, not a correlated coin, and the coin is most of the variance.

    Args:
        contacts: Contact tables by world label.
        outcomes: Outcome frames by the same labels.
        centre: The centre's declared shape.
        population: The declared correlations.

    Returns:
        A frame with the columns in :data:`CORRELATION_COLUMNS`, one row per stage, measured in the
        **second** world given - the correlated one. A declared correlation has nothing to say about
        the first.
    """
    _, correlated = _two_labels(contacts, outcomes)
    table = contacts[correlated]
    latent = latent_traits(table, centre)
    first = _first_sessions(outcomes[correlated])
    resolution = intracluster_correlation(first, "customer", "resolved")
    rows = [
        {
            "stage": "declared",
            "difficulty": population.difficulty_correlation,
            "patience": population.patience_correlation,
            "resolution": float("nan"),
        },
        {
            "stage": "latent",
            "difficulty": intracluster_correlation(latent, "customer", "latent_difficulty"),
            "patience": intracluster_correlation(latent, "customer", "latent_patience"),
            "resolution": float("nan"),
        },
        {
            "stage": "observed",
            "difficulty": intracluster_correlation(table, "customer", "difficulty"),
            "patience": intracluster_correlation(table, "customer", "patience_turns"),
            "resolution": float("nan"),
        },
        {
            "stage": "outcome",
            "difficulty": float("nan"),
            "patience": float("nan"),
            "resolution": resolution,
        },
    ]
    return pd.DataFrame(rows)[list(CORRELATION_COLUMNS)]


def design_table(
    outcomes: Mapping[str, pd.DataFrame],
    alpha: float = 0.05,
) -> pd.DataFrame:
    """What the surviving correlation costs a comparison, by world.

    Args:
        outcomes: Outcome frames by world label.
        alpha: The nominal significance level a per-contact test believes it is running at.

    Returns:
        A frame with the columns in :data:`DESIGN_COLUMNS`, one row per world.
    """
    rows = []
    for label, frame in outcomes.items():
        first = _first_sessions(frame)
        icc = intracluster_correlation(first, "customer", "resolved")
        sizes = first.groupby("customer").size()
        size = len(first) / float(sizes.size)
        # The size-weighted mean, not the mean. Wave 4 published this table with the mean, which
        # understates the inflation whenever the clusters are unequal - and they always are. The
        # column that keeps the old number is there so the size of that mistake stays visible.
        weighted = effective_cluster_size(sizes)
        effect = design_effect(weighted, icc)
        # A measured design effect below one is a negative correlation estimate, which is not an
        # inflation, and wave 3's function refuses it rather than clipping it to five per cent. The
        # refusal is kept here: the independent world's row reports no actual alpha because there is
        # no inflation to report, and a table that printed 0.05 there would be inventing a number.
        rows.append(
            {
                "world": label,
                "icc": icc,
                "mean_cluster_size": size,
                "effective_cluster_size": weighted,
                "design_effect": effect,
                "design_effect_at_mean": design_effect(size, icc),
                "sample_inflation": effect - 1.0,
                "nominal_alpha": alpha,
                "actual_alpha": actual_alpha(alpha, effect) if effect >= 1.0 else float("nan"),
            }
        )
    return pd.DataFrame(rows)[list(DESIGN_COLUMNS)]


def pair_failures(outcomes: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """How often a customer with two contacts was failed on both, by world.

    The quantity a complaints queue feels and a resolution rate cannot show. Under independence it
    is the square of the failure rate; the ratio to that square is what the correlation buys. The
    independent world is the control for the ratio, because what an estimator does on data with no
    structure in it is a fact about the estimator.

    Args:
        outcomes: Outcome frames by world label.

    Returns:
        A frame with the columns in :data:`PAIR_COLUMNS`, one row per world.
    """
    rows = []
    for label, frame in outcomes.items():
        first = _first_sessions(frame)
        sizes = first.groupby("customer")["failed"].size()
        pairs = first[first["customer"].isin(sizes[sizes == 2].index)]
        failures = pairs.groupby("customer")["failed"].sum()
        rate = float(pairs["failed"].mean())
        both = float((failures == 2.0).mean())
        rows.append(
            {
                "world": label,
                "pairs": int(failures.size),
                "failure_rate": rate,
                "both_failed": both,
                "expected_if_independent": rate * rate,
                "ratio": both / (rate * rate),
            }
        )
    return pd.DataFrame(rows)[list(PAIR_COLUMNS)]


def error_table(
    treated: Mapping[str, pd.DataFrame],
    control: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Three standard errors on one difference, by world.

    The three are the ones an analyst actually chooses between:

    - **naive**: contacts treated as independent observations.
    - **cluster mean**: the difference between the arms' averages **of customer averages**, which is
      the correction most often reached for because it needs no correlation estimate.
    - **corrected**: the naive error multiplied by the square root of the measured design effect.

    Read the independent world's row first. The cluster-mean error is inflated there too, on data
    with no correlation in it at all, because averaging averages over unequal cluster sizes discards
    information. That inflation is an efficiency loss wearing a correction's clothes.

    Args:
        treated: Outcome frames for the arm that met the bot, by world label.
        control: Outcome frames for the arm that did not, by the same labels.

    Returns:
        A frame with the columns in :data:`ERROR_COLUMNS`, one row per world.

    Raises:
        KeyError: If the two mappings do not carry the same labels.
    """
    if set(treated) != set(control):
        raise KeyError(f"treated covers {sorted(treated)} and control {sorted(control)}")
    rows = []
    for label in treated:
        arms = [_first_sessions(treated[label]), _first_sessions(control[label])]
        naive = 0.0
        clustered = 0.0
        estimate = []
        pooled_icc = []
        pooled_size = []
        for arm in arms:
            values = arm["resolved"].to_numpy(dtype=float)
            share = float(values.mean())
            estimate.append(share)
            naive += share * (1.0 - share) / values.size
            per_customer = arm.groupby("customer")["resolved"].mean().to_numpy(dtype=float)
            clustered += float(per_customer.var(ddof=1)) / per_customer.size
            pooled_icc.append(intracluster_correlation(arm, "customer", "resolved"))
            pooled_size.append(effective_cluster_size(arm.groupby("customer").size()))
        naive_se = math.sqrt(naive)
        effect = design_effect(float(np.mean(pooled_size)), float(np.mean(pooled_icc)))
        corrected = naive_se * math.sqrt(effect)
        rows.append(
            {
                "world": label,
                "estimate": estimate[0] - estimate[1],
                "naive_se": naive_se,
                "cluster_mean_se": math.sqrt(clustered),
                "corrected_se": corrected,
                "cluster_mean_ratio": math.sqrt(clustered) / naive_se,
                "corrected_ratio": corrected / naive_se,
            }
        )
    return pd.DataFrame(rows)[list(ERROR_COLUMNS)]


def power_at(effect: float, difference: float, share: float, contacts: int) -> float:
    """Power of a per-contact test that ignored a design effect of ``effect``.

    The other side of :func:`svclab.experiment.actual_alpha`: a test run at a nominal five per cent
    on clustered data is not only testing at the wrong level, it is also less able to find a real
    difference than its own sizing promised. Both follow from one inflated variance, which is why
    they are computed from the same number.

    Args:
        effect: The design effect.
        difference: The true difference in proportions.
        share: The proportion in the control arm.
        contacts: Contacts per arm.

    Returns:
        The probability of detecting the difference at a nominal 5% two-sided level.

    Raises:
        ValueError: If the design effect is below one or the arm is empty.
    """
    if effect < 1.0:
        raise ValueError(f"a design effect is at least one, not {effect}")
    if contacts <= 0:
        raise ValueError("power needs a non-empty arm")
    other = share + difference
    variance = (share * (1.0 - share) + other * (1.0 - other)) * effect / contacts
    critical = float(stats.norm.ppf(0.975))
    return float(stats.norm.sf(critical - abs(difference) / math.sqrt(variance)))

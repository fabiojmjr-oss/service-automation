"""Choosing where the bot stops trying, by cost rather than by accuracy.

A routing classifier reports a label and a confidence in it. Somewhere there is a number below which
the contact should go straight to a human instead, and that number is almost always chosen by
maximising accuracy - or by somebody saying "let us start at eighty per cent".

**Accuracy is the wrong objective, because the two mistakes do not cost the same.** Handing the bot
a complaint it has read as a tracking question wastes minutes of a human's day and a customer's
patience; deferring a tracking question the bot would have answered wastes twenty seconds of queue
entry. A threshold that treats those as interchangeable optimises a quantity nobody pays.

Three results, and the third is the one that corrected the draft of this paragraph.

**The cost-minimising threshold is not the accuracy-maximising one.** The gap is modest here and it
is payable in human hours, which is the currency it should be quoted in.

**One threshold for the whole queue is a compromise nobody chose.** Sweeping a threshold per intent
beats the best single number, because the cost of a misroute differs between intents by a factor of
nine and the right amount of caution differs with it.

**And the closed form for the optimum is a correct answer to a question about a probability, applied
here to a number that is not one.** On a calibrated score - one that *is* the probability the label
is right - the rule is to defer below ``1 - defer_cost / misroute_cost``, which
:func:`calibrated_threshold` returns. The score in this generator is a **margin**, informative about
correctness but not calibrated to it, and applying the closed form to it anyway is measurably worse
than sweeping. What survives is the formula's *ranking*: it orders the intents by caution exactly as
the swept optima do, and its levels are far too high. Calibration is the missing step, and the
closed form assumes it silently.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from svclab.bot import BotPolicy, run
from svclab.synth import CENTRE, ROUTING, CentreProfile, RoutingProfile

#: Columns of the cost curve, one row per threshold.
COST_COLUMNS = (
    "threshold",
    "deferred_share",
    "bot_attempts",
    "misroutes",
    "label_accuracy",
    "resolution_rate",
    "human_seconds",
    "misroute_seconds",
    "defer_seconds",
    "total_seconds",
    "seconds_per_contact",
)


def calibrated_threshold(defer_seconds: float, misroute_seconds: float) -> float:
    """Where to defer, if the score were the probability that the label is right.

    Attempting costs nothing when the label is right and ``misroute_seconds`` when it is wrong, so
    its expected cost is ``(1 - p) * misroute_seconds``. Deferring costs ``defer_seconds`` whatever
    happens. Attempt while the first is smaller, which is ``p > 1 - defer_seconds /
    misroute_seconds``.

    Args:
        defer_seconds: Cost of sending the contact past the bot.
        misroute_seconds: Cost of letting the bot try on a wrong label.

    Returns:
        The threshold, clipped into the unit interval. Zero when deferring costs at least as much as
        a misroute, which is the honest answer that the bot should always try.

    Raises:
        ValueError: If either cost is negative, or the misroute cost is zero - a mistake that costs
            nothing does not have a threshold, it has no decision.
    """
    if defer_seconds < 0 or misroute_seconds < 0:
        raise ValueError("costs cannot be negative")
    if misroute_seconds == 0:
        raise ValueError("a misroute that costs nothing does not imply a threshold")
    return float(np.clip(1.0 - defer_seconds / misroute_seconds, 0.0, 1.0))


def defer_below(
    contacts: pd.DataFrame,
    scores: pd.DataFrame,
    threshold: float | dict[str, float],
) -> pd.DataFrame:
    """The contact table with a ``defer`` column: send it past the bot below the threshold.

    Args:
        contacts: The contact table.
        scores: The routing scores, from :func:`svclab.synth.routing_scores`.
        threshold: One threshold for the whole queue, or one per **predicted** intent. Per intent is
            the interesting case and the harder one to deploy, because the rule has to be keyed on
            what the classifier thinks rather than on what the contact is.

    Returns:
        A copy of the contact table with ``classifier_score`` and ``defer`` added.

    Raises:
        KeyError: If a per-intent mapping has no threshold for an intent that appears.
    """
    joined = contacts.merge(scores, on="contact", how="left")
    score = joined["classifier_score"].to_numpy(dtype=float)
    if isinstance(threshold, dict):
        missing = set(joined["intent"]) - set(threshold)
        if missing:
            raise KeyError(f"no threshold for {sorted(missing)}")
        cut = joined["intent"].map(threshold).to_numpy(dtype=float)
    else:
        cut = np.full(len(joined), float(threshold))
    joined["defer"] = score < cut
    return joined


def cost_of(
    outcomes: pd.DataFrame,
    routed: pd.DataFrame,
    routing: RoutingProfile = ROUTING,
) -> dict[str, float]:
    """What one routing decision cost, split into the three things that are paid.

    Args:
        outcomes: Outcomes from :func:`svclab.bot.run` on the routed contacts.
        routed: The routed contact table from :func:`defer_below`, which carries the deferral and
        the true intent. routing: The declared costs.

    Returns:
        A mapping with the human seconds the queue spent, the misroute penalty, the deferral cost,
        their total, and the counts behind them.
    """
    deferred = routed["defer"].to_numpy(dtype=bool)
    attempted = ~deferred & ~routed["holdout"].to_numpy(dtype=bool)
    first = outcomes[~outcomes["is_repeat"].to_numpy(dtype=bool)]
    correct = first.set_index("contact")["classified_correctly"].reindex(routed["contact"])
    misrouted = attempted & ~correct.to_numpy(dtype=bool)
    penalty = routed["intent"].map(routing.misroute_seconds).to_numpy(dtype=float)
    return {
        "deferred": float(deferred.sum()),
        "bot_attempts": float(attempted.sum()),
        "misroutes": float(misrouted.sum()),
        "human_seconds": float(outcomes["human_seconds"].sum()),
        "misroute_seconds": float((penalty * misrouted).sum()),
        "defer_seconds": float(deferred.sum() * routing.defer_seconds),
    }


def cost_curve(
    contacts: pd.DataFrame,
    scores: pd.DataFrame,
    policy: BotPolicy,
    thresholds: tuple[float, ...],
    routing: RoutingProfile = ROUTING,
    centre: CentreProfile = CENTRE,
) -> pd.DataFrame:
    """Every threshold priced, in the two currencies it can be judged in.

    ``label_accuracy`` is the objective a classifier is usually tuned on - the share of decisions
    that were right, counting a correct deferral as right. ``seconds_per_contact`` is what the
    operation pays. They do not have their minimum in the same place, and that is the result.

    Args:
        contacts: The contact table.
        scores: The routing scores.
        policy: The bot policy the router sits in front of.
        thresholds: Thresholds to price.
        routing: The declared costs.
        centre: The centre's declared shape.

    Returns:
        A frame with the columns in :data:`COST_COLUMNS`, one row per threshold.

    Raises:
        ValueError: If no thresholds are supplied.
    """
    if not thresholds:
        raise ValueError("there are no thresholds to price")
    rows = []
    for threshold in thresholds:
        routed = defer_below(contacts, scores, threshold)
        outcomes = run(routed, policy, centre)
        measured = cost_of(outcomes, routed, routing)
        first = outcomes[~outcomes["is_repeat"].to_numpy(dtype=bool)]
        deferred = routed["defer"].to_numpy(dtype=bool)
        aligned = first.set_index("contact")["classified_correctly"].reindex(routed["contact"])
        correct = aligned.to_numpy(dtype=bool)
        # A decision is right when the bot was let through on a correct label, or held back on a
        # wrong one. That is the confusion matrix a classifier's threshold is usually tuned on.
        right = np.where(deferred, ~correct, correct)
        total = measured["human_seconds"] + measured["misroute_seconds"] + measured["defer_seconds"]
        rows.append(
            {
                "threshold": float(threshold) if not isinstance(threshold, dict) else float("nan"),
                "deferred_share": measured["deferred"] / len(routed),
                "bot_attempts": measured["bot_attempts"],
                "misroutes": measured["misroutes"],
                "label_accuracy": float(right.mean()),
                "resolution_rate": float(first["resolved"].mean()),
                "human_seconds": measured["human_seconds"],
                "misroute_seconds": measured["misroute_seconds"],
                "defer_seconds": measured["defer_seconds"],
                "total_seconds": total,
                "seconds_per_contact": total / len(routed),
            }
        )
    return pd.DataFrame(rows)[list(COST_COLUMNS)]


def best_by(curve: pd.DataFrame, column: str, largest: bool) -> float:
    """The threshold that optimises one column of a cost curve.

    Args:
        curve: A frame from :func:`cost_curve`.
        column: Which column to optimise.
        largest: Whether the best value is the largest, as it is for accuracy, or the smallest, as
        it is for cost.

    Returns:
        The threshold.

    Raises:
        KeyError: If the column is not in the curve.
    """
    if column not in curve.columns:
        raise KeyError(f"{column!r} is not a column of this curve: {list(curve.columns)}")
    position = curve[column].idxmax() if largest else curve[column].idxmin()
    return float(curve["threshold"].loc[position])

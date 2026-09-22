"""Where the bot should stop trying, decided by cost rather than by accuracy.

:mod:`~svclab.routing.threshold` prices every threshold in both currencies - the share of routing
decisions that were right, and the seconds the operation pays for them - and they do not have their
optimum in the same place.

It also prices the closed form. On a score that *is* the probability the label is right, the optimum
is to defer below ``1 - defer_cost / misroute_cost``. The score here is a margin rather than a
probability, so that rule orders the intents correctly and sets every level far too high - which is
the difference between a formula being wrong and a formula being applied to the wrong input.

That reading was incomplete. :mod:`svclab.calibration` supplies the right input and the rule is
still worse than sweeping, because it treats a correct label as free when a correct label is what
the bot is for.
"""

from .threshold import (
    COST_COLUMNS,
    best_by,
    calibrated_threshold,
    cost_curve,
    cost_of,
    defer_below,
)

__all__ = [
    "COST_COLUMNS",
    "best_by",
    "calibrated_threshold",
    "cost_curve",
    "cost_of",
    "defer_below",
]

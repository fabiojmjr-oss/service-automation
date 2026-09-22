"""Giving the closed form the input it assumes, and the threshold a period it has not seen.

:mod:`~svclab.calibration.score` maps the classifier's score onto the probability the label is right
- by isotonic regression or by Platt scaling, fitted on part of the month - and reports how far the
result is from meaning what it says. It also carries the control: the probability the generator
actually used, which is the calibrated score no operation has and on which the closed form must be
exactly optimal if wave 3's diagnosis was right.

:mod:`~svclab.calibration.selection` chooses the thresholds on one period and prices them on the
next, and runs the per-intent rule on the label a deployment can actually read. Both corrections
point the same way: wave 3's saving was an upper bound.
"""

from .score import (
    RELIABILITY_COLUMNS,
    expected_calibration_error,
    fit_period,
    isotonic,
    isotonic_at,
    platt,
    platt_at,
    reliability_table,
    true_probability,
)
from .selection import (
    ALWAYS_DEFER,
    FORMULA_COLUMNS,
    GRID,
    KEY_COLUMNS,
    OPTIMISM_COLUMNS,
    amended_threshold,
    calibrated_scores,
    formula_table,
    intent_labels,
    key_table,
    optimism_table,
    price,
    resolve_benefit,
    swept,
)

__all__ = [
    "ALWAYS_DEFER",
    "FORMULA_COLUMNS",
    "GRID",
    "KEY_COLUMNS",
    "OPTIMISM_COLUMNS",
    "RELIABILITY_COLUMNS",
    "amended_threshold",
    "calibrated_scores",
    "expected_calibration_error",
    "fit_period",
    "formula_table",
    "intent_labels",
    "isotonic",
    "isotonic_at",
    "key_table",
    "optimism_table",
    "platt",
    "platt_at",
    "price",
    "reliability_table",
    "resolve_benefit",
    "swept",
    "true_probability",
]

"""Turning a classifier's score into the probability the closed form assumes it already is.

Wave 3 applied the textbook threshold ``1 - defer_cost / misroute_cost`` to this generator's routing
score and found it 12.5% worse than the single swept number. The diagnosis published there was that
the formula is a correct answer about a **probability** and the score is a **margin** - informative
about correctness, monotone in it, and not equal to it. That diagnosis was an assertion. This module
is what tests it.

Three things are needed, and the third is the one that makes the first two worth anything.

**A map from the score to a probability.** Two are offered, both fitted rather than assumed:
isotonic regression, which asks only that the map be non-decreasing, and Platt scaling, which asks
that it be a logistic curve in the score. Neither is a better choice in general - isotonic is free
of shape and pays for it in variance at the ends, Platt is rigid and pays for it in bias where the
true map is not logistic - and the reliability table is what separates them here.

**A way to see whether it worked.** A reliability table bins the score, reports the mean score and
the observed share correct in each bin, and the expected calibration error is the volume-weighted
mean gap. A perfectly calibrated score has a gap of zero in every bin. That number is *not* a
measure of how good the classifier is: a score that says 0.78 for every contact in an account that
is 78% correct is perfectly calibrated and ranks nothing at all.

**And a control whose answer is known.** :func:`true_probability` returns the probability the
generator actually used, which is the calibrated score this account cannot have. On it the closed
form must be exactly optimal, because that is the hypothesis wave 3's defect rests on. If the
formula were simply wrong, no calibration would rescue it and the control would say so.

The fit is on a declared share of the month and everything is judged on the rest of it, because a
calibrator fitted and scored on the same contacts reports how well it memorised them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from svclab.synth import (
    CALIBRATION,
    CENTRE,
    INTENTS,
    CalibrationProfile,
    CentreProfile,
    accuracy_curve,
)

#: Columns of the reliability table, one row per non-empty bin.
RELIABILITY_COLUMNS = (
    "bin",
    "lower",
    "upper",
    "contacts",
    "mean_score",
    "share_correct",
    "gap",
)


def fit_period(
    contacts: pd.DataFrame,
    calibration: CalibrationProfile = CALIBRATION,
    centre: CentreProfile = CENTRE,
) -> np.ndarray:
    """Which contacts are in the fitting part of the month.

    A calendar split rather than a random one. A random split tests whether a calibrator generalises
    to contacts drawn from the same distribution, which it always does; a calendar split is the only
    one that could notice the distribution moving, which is the failure a deployed threshold
    actually meets.

    Args:
        contacts: The contact table, for ``arrival_hour``.
        calibration: The declared share of the period to fit on.
        centre: The centre's declared shape, for the length of the period.

    Returns:
        One boolean per contact: true in the fitting part.

    Raises:
        KeyError: If the contact table has no ``arrival_hour``.
        ValueError: If the share does not leave both parts non-empty.
    """
    if "arrival_hour" not in contacts.columns:
        raise KeyError("the contact table has no arrival_hour to split on")
    if not 0.0 < calibration.fit_share < 1.0:
        raise ValueError("a fit share outside (0, 1) leaves one of the two parts empty")
    boundary = calibration.fit_share * centre.days * 24.0
    return np.asarray(contacts["arrival_hour"].to_numpy(dtype=float) < boundary, dtype=bool)


def true_probability(contacts: pd.DataFrame) -> np.ndarray:
    """The probability the generator used, which is the calibrated score no operation has.

    Not a calibration method: the control the other two are judged against. It reads ``difficulty``,
    so nothing outside a test may use it - a policy that could see this would be a policy that knows
    the answer.

    Args:
        contacts: The contact table.

    Returns:
        One probability per contact.

    Raises:
        KeyError: If the contact table is missing a column the curve is built from.
    """
    missing = {"intent", "difficulty"} - set(contacts.columns)
    if missing:
        raise KeyError(f"the contact table is missing {sorted(missing)}")
    index = {profile.intent: position for position, profile in enumerate(INTENTS)}
    which = np.array([index[value] for value in contacts["intent"]], dtype=int)
    return accuracy_curve(contacts["difficulty"].to_numpy(dtype=float), which)


def _pool_adjacent_violators(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """The non-decreasing sequence closest to ``values`` in weighted squared error, in one pass.

    Blocks are merged while the last one's mean is not above the one before it, each block carrying
    its weighted total and its weight. That is the classical algorithm, and its output is the
    least-squares monotone fit rather than an approximation of one.

    Weights are not an optional refinement here. Points that share an x have to be pooled **before**
    the pass, and a pooled point stands for as many observations as went into it; giving them all
    weight one would let the fit depend on the order ties happened to be stored in.
    """
    totals: list[float] = []
    masses: list[float] = []
    sizes: list[int] = []
    for value, weight in zip(values, weights, strict=True):
        totals.append(float(value) * float(weight))
        masses.append(float(weight))
        sizes.append(1)
        while len(totals) > 1 and totals[-2] / masses[-2] >= totals[-1] / masses[-1]:
            # Popped into locals first: `totals[-2] += totals.pop()` stores through an index the
            # pop has already moved, which is a different element and on a two-block stack is none.
            total, mass, size = totals.pop(), masses.pop(), sizes.pop()
            totals[-1] += total
            masses[-1] += mass
            sizes[-1] += size
    return np.repeat(np.array(totals) / np.array(masses), np.asarray(sizes, dtype=int))


def isotonic(score: np.ndarray, correct: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """A non-decreasing map from the score to the share correct, fitted by least squares.

    Args:
        score: The classifier's scores on the fitting contacts.
        correct: Whether each of those labels was right.

    Returns:
        Knots and their fitted probabilities, to be read by :func:`isotonic_at`. Scores that repeat
        are collapsed onto one knot, because a step function cannot take two values at one point.

    Raises:
        ValueError: If the two arrays disagree in length, or there is nothing to fit.
    """
    if len(score) != len(correct):
        raise ValueError("the scores and the outcomes are not the same length")
    if len(score) == 0:
        raise ValueError("there is nothing to fit")
    # Ties are pooled first, so every contact on one score gets one fitted probability. Doing it
    # afterwards would let the fit depend on the order equal scores happened to arrive in.
    knots, inverse = np.unique(np.asarray(score, dtype=float), return_inverse=True)
    weights = np.bincount(inverse).astype(float)
    observed = np.bincount(inverse, weights=np.asarray(correct, dtype=float)) / weights
    return knots, _pool_adjacent_violators(observed, weights)


def isotonic_at(knots: np.ndarray, values: np.ndarray, score: np.ndarray) -> np.ndarray:
    """The fitted map read at new scores, flat outside the range it was fitted on.

    Linear between knots rather than a staircase: a staircase would make the calibrated score take
    only as many distinct values as there were blocks, and a threshold swept on it would land on a
    plateau whose position is an artefact of the fitting sample.
    """
    return np.asarray(np.interp(np.asarray(score, dtype=float), knots, values), dtype=float)


def platt(
    score: np.ndarray,
    correct: np.ndarray,
    calibration: CalibrationProfile = CALIBRATION,
) -> tuple[float, float]:
    """A logistic map from the score to the probability, fitted by Newton's method.

    Args:
        score: The classifier's scores on the fitting contacts.
        correct: Whether each of those labels was right.
        calibration: The declared step limit and tolerance.

    Returns:
        The slope and the intercept of ``sigmoid(slope * score + intercept)``.

    Raises:
        ValueError: If the two arrays disagree in length, if there is nothing to fit, or if the fit
            has no unique answer - which happens when every score is the same, or every label is
            right, and is a refusal rather than a number: the likelihood has no maximum there.
    """
    if len(score) != len(correct):
        raise ValueError("the scores and the outcomes are not the same length")
    if len(score) == 0:
        raise ValueError("there is nothing to fit")
    x = np.asarray(score, dtype=float)
    y = np.asarray(correct, dtype=float)
    slope, intercept = 0.0, 0.0
    for _ in range(calibration.platt_steps):
        probability = 1.0 / (1.0 + np.exp(-(slope * x + intercept)))
        weight = probability * (1.0 - probability)
        residual = y - probability
        gradient = np.array([float((residual * x).sum()), float(residual.sum())])
        hessian = np.array(
            [
                [float((weight * x * x).sum()), float((weight * x).sum())],
                [float((weight * x).sum()), float(weight.sum())],
            ]
        )
        determinant = hessian[0, 0] * hessian[1, 1] - hessian[0, 1] * hessian[1, 0]
        if determinant <= 0.0:
            raise ValueError(
                "the logistic fit has no unique answer on these scores, so no coefficients are "
                "reported - a constant score or a label that is always right has no maximum"
            )
        step = np.linalg.solve(hessian, gradient)
        slope += float(step[0])
        intercept += float(step[1])
        if float(np.abs(step).max()) < calibration.platt_tolerance:
            break
    return slope, intercept


def platt_at(slope: float, intercept: float, score: np.ndarray) -> np.ndarray:
    """The fitted logistic map read at new scores."""
    return np.asarray(
        1.0 / (1.0 + np.exp(-(slope * np.asarray(score, dtype=float) + intercept))), dtype=float
    )


def reliability_table(
    score: np.ndarray,
    correct: np.ndarray,
    calibration: CalibrationProfile = CALIBRATION,
) -> pd.DataFrame:
    """What the score claimed against what happened, in equal-width bins.

    Args:
        score: Scores, or calibrated probabilities, on the contacts being judged.
        correct: Whether each label was right.
        calibration: The declared bin count.

    Returns:
        A frame with the columns in :data:`RELIABILITY_COLUMNS`, one row per **non-empty** bin. An
        empty bin has no observed share, so it has no gap and is not a row.

    Raises:
        ValueError: If the two arrays disagree in length, or the bin count is not positive.
    """
    if len(score) != len(correct):
        raise ValueError("the scores and the outcomes are not the same length")
    if calibration.bins <= 0:
        raise ValueError("a reliability table needs at least one bin")
    values = np.asarray(score, dtype=float)
    hits = np.asarray(correct, dtype=float)
    edges = np.linspace(0.0, 1.0, calibration.bins + 1)
    empty = pd.DataFrame({name: pd.Series(dtype=float) for name in RELIABILITY_COLUMNS})
    if len(values) == 0:
        return empty
    # The last bin is closed at the top, so a score of exactly one is not its own bin.
    which = np.clip(np.digitize(values, edges[1:-1], right=False), 0, calibration.bins - 1)
    rows = []
    for index in range(calibration.bins):
        inside = which == index
        if not inside.any():
            continue
        mean_score = float(values[inside].mean())
        share = float(hits[inside].mean())
        rows.append(
            {
                "bin": index,
                "lower": float(edges[index]),
                "upper": float(edges[index + 1]),
                "contacts": float(inside.sum()),
                "mean_score": mean_score,
                "share_correct": share,
                "gap": share - mean_score,
            }
        )
    return pd.DataFrame(rows)[list(RELIABILITY_COLUMNS)] if rows else empty


def expected_calibration_error(table: pd.DataFrame) -> float:
    """The volume-weighted mean absolute gap of a reliability table.

    One number, and it hides two different failures: a score that is uniformly too low and a score
    that is too low at one end and too high at the other can report the same error. The table is
    what tells them apart, which is why this takes one rather than replacing it.

    Args:
        table: A frame from :func:`reliability_table`.

    Returns:
        The error, in probability.

    Raises:
        ValueError: If the table is empty, which is a study of no contacts.
    """
    if table.empty:
        raise ValueError("an empty reliability table has no calibration error")
    weight = table["contacts"].to_numpy(dtype=float)
    return float((weight * table["gap"].abs().to_numpy(dtype=float)).sum() / weight.sum())

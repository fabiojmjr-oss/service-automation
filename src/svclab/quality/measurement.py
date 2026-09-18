"""The quality score as a measurement system, before it is used to judge anything.

Wave 1 established that a containment rate cannot rank two bot policies, and that resolution can.
The obvious next move is to stop counting and start grading: sample sessions, have a quality panel
score them, and compare. This module is about what has to be true before that comparison means
anything.

**A quality panel is a gauge, and a gauge gets qualified before it gets used.** That is ordinary
practice for a caliper and almost unheard of for a quality rubric. The three questions are the same:
does the same assessor give the same verdict twice (repeatability), do two assessors give the same
verdict (reproducibility), and is the verdict right (bias). An attribute agreement analysis answers
all three, and it needs the second reading almost nobody collects.

**And measurement error does not merely add noise to a comparison - it shrinks it, by a factor with
a closed form.** For a binary standard, an assessor with sensitivity ``se`` and specificity ``sp``
turns a true pass rate ``p`` into an observed one ``p*se + (1-p)*(1-sp)``. Subtract two of those and
the true difference comes out multiplied by ``se + sp - 1``: the Youden index. A panel with an index
of 0.5 halves every difference it is used to measure, **towards zero, always**, and the sample size
needed to see what is left grows by about the square of that.

So a bot that is genuinely worse than a human can be graded, honestly, by a real panel, and come
back looking closer to the human than it is. Not because anybody cheated - because the instrument
attenuates.
"""

from __future__ import annotations

import itertools
import math

import numpy as np
import pandas as pd
from scipy import stats

from svclab.synth import GRADERS, JUDGE, QUALITY, GraderProfile, QualityProfile

#: Columns of the latent-quality frame, one row per session.
LATENT_COLUMNS = ("session", "contact", "outcome", "latent_quality", "acceptable")

#: Columns of a verdict frame, one row per reading.
VERDICT_COLUMNS = ("session", "contact", "assessor", "replicate", "reading", "verdict")

#: Columns of the per-assessor agreement table.
AGREEMENT_COLUMNS = (
    "assessor",
    "readings",
    "pass_rate",
    "repeatability",
    "repeatability_kappa",
    "agreement_with_truth",
    "sensitivity",
    "specificity",
    "youden",
)

#: Columns of the between-assessor table.
REPRODUCIBILITY_COLUMNS = ("pair", "sessions", "agreement", "kappa")


def latent_quality(
    outcomes: pd.DataFrame,
    contacts: pd.DataFrame,
    quality: QualityProfile = QUALITY,
) -> pd.DataFrame:
    """The declared quality of every session, and whether it meets the standard.

    Not a draw. A session's quality is a declared function of what happened to it - which outcome it
    reached and how hard the contact was - so that measurement error can be isolated from everything
    else. An abandoned session is flat at its declared floor, because there is no version of walking
    the customer out that is acceptable.

    Args:
        outcomes: Outcome frame from :func:`svclab.bot.run`.
        contacts: The contact table, for the difficulty.
        quality: The declared quality levels and the standard.

    Returns:
        A frame with the columns in :data:`LATENT_COLUMNS`.

    Raises:
        KeyError: If an outcome appears that has no declared quality level.
    """
    levels = {
        "resolved-by-bot": quality.resolved_by_bot,
        "straight-to-human": quality.straight_to_human,
        "escalated": quality.escalated,
        "repeat-to-human": quality.repeat_to_human,
        "abandoned": quality.abandoned,
    }
    unknown = set(outcomes["outcome"]) - set(levels)
    if unknown:
        raise KeyError(f"no declared quality level for {sorted(unknown)}")

    joined = outcomes.merge(contacts[["contact", "difficulty"]], on="contact", how="left")
    base = joined["outcome"].map(levels).to_numpy(dtype=float)
    difficulty = joined["difficulty"].to_numpy(dtype=float)
    abandoned = joined["outcome"].to_numpy() == "abandoned"
    latent = np.where(abandoned, base, base - quality.difficulty_penalty * difficulty)
    return pd.DataFrame(
        {
            "session": joined["session"].to_numpy(),
            "contact": joined["contact"].to_numpy(),
            "outcome": joined["outcome"].to_numpy(),
            "latent_quality": latent,
            "acceptable": latent >= quality.standard,
        }
    )[list(LATENT_COLUMNS)]


def _read(
    latent: pd.DataFrame,
    noise: pd.DataFrame,
    profiles: dict[str, GraderProfile],
    quality: QualityProfile,
) -> pd.DataFrame:
    """Turn declared quality plus an assessor's bias and noise into verdicts."""
    joined = noise.merge(latent, on="contact", how="inner")
    bias = joined["assessor"].map({name: profile.bias for name, profile in profiles.items()})
    reading = joined["latent_quality"].to_numpy(dtype=float) + bias.to_numpy(dtype=float)
    reading = reading + joined["noise"].to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "session": joined["session"].to_numpy(),
            "contact": joined["contact"].to_numpy(),
            "assessor": joined["assessor"].to_numpy(),
            "replicate": joined["replicate"].to_numpy(),
            "reading": reading,
            "verdict": reading >= quality.standard,
        }
    )[list(VERDICT_COLUMNS)]


def panel_verdicts(
    latent: pd.DataFrame,
    panel_noise: pd.DataFrame,
    graders: tuple[GraderProfile, ...] = GRADERS,
    quality: QualityProfile = QUALITY,
) -> pd.DataFrame:
    """Every reading the human panel produced, one row per grader per replicate per session.

    Args:
        latent: The declared quality, from :func:`latent_quality`.
        panel_noise: The panel's noise draws from :func:`svclab.synth.quality_noise`.
        graders: The panel.
        quality: The declared standard.

    Returns:
        A frame with the columns in :data:`VERDICT_COLUMNS`.
    """
    noise = panel_noise.rename(columns={"grader": "assessor"})
    return _read(latent, noise, {profile.grader: profile for profile in graders}, quality)


def judge_verdicts(
    latent: pd.DataFrame,
    judge_noise: pd.DataFrame,
    judge: GraderProfile = JUDGE,
    quality: QualityProfile = QUALITY,
) -> pd.DataFrame:
    """Every reading the automated assessor produced, one row per session.

    It reads everything rather than a sample, which is its whole argument, and it reads each session
    once - a deterministic assessor has nothing to say about its own repeatability, which is a
    property worth naming rather than a strength.
    """
    noise = judge_noise.assign(assessor=judge.grader, replicate=1)
    return _read(latent, noise, {judge.grader: judge}, quality)


def kappa(first: np.ndarray, second: np.ndarray) -> float:
    """Cohen's kappa between two sets of binary verdicts on the same items.

    Agreement above what two assessors would reach by chance given their own pass rates. Reported
    next to raw agreement because raw agreement is meaningless on its own: two assessors who pass
    95% of everything agree 90% of the time while knowing nothing.

    Args:
        first: One assessor's verdicts.
        second: The other's, aligned item by item.

    Returns:
        Kappa, or ``nan`` where chance agreement is already perfect - which happens when both
        assessors give every item the same label, and where the honest answer is that the data
        cannot distinguish agreement from a constant.

    Raises:
        ValueError: If the two arrays are not the same length, or are empty.
    """
    left = np.asarray(first, dtype=bool)
    right = np.asarray(second, dtype=bool)
    if left.size != right.size:
        raise ValueError(f"{left.size} verdicts cannot be compared with {right.size}")
    if left.size == 0:
        raise ValueError("there are no verdicts to compare")
    observed = float(np.mean(left == right))
    pass_left, pass_right = float(left.mean()), float(right.mean())
    chance = pass_left * pass_right + (1.0 - pass_left) * (1.0 - pass_right)
    if chance >= 1.0:
        return float("nan")
    return (observed - chance) / (1.0 - chance)


def youden(sensitivity: float, specificity: float) -> float:
    """The factor a binary gauge multiplies every difference by: ``sensitivity + specificity - 1``.

    One for a perfect gauge, zero for one that carries no information, and negative for one whose
    verdicts point the wrong way. Every attenuation result in this module is this number.
    """
    return sensitivity + specificity - 1.0


def agreement_table(
    verdicts: pd.DataFrame,
    latent: pd.DataFrame,
) -> pd.DataFrame:
    """One row per assessor: repeatability, and how often the verdict is right.

    The attribute agreement analysis, in the order it has to be read. Repeatability first - an
    assessor who does not agree with themselves cannot agree with anything else - then the
    comparison with the standard, split into sensitivity and specificity because a lenient assessor
    and a strict one fail in opposite directions and a single accuracy figure hides which.

    Args:
        verdicts: Readings from :func:`panel_verdicts` or :func:`judge_verdicts`.
        latent: The declared quality, for the standard each verdict is judged against.

    Returns:
        A frame with the columns in :data:`AGREEMENT_COLUMNS`, one row per assessor.

    Raises:
        ValueError: If the verdict frame is empty.
    """
    if verdicts.empty:
        raise ValueError("there are no readings to analyse")
    truth = dict(zip(latent["session"], latent["acceptable"], strict=True))
    rows = []
    for assessor, frame in verdicts.groupby("assessor", sort=True):
        actual = np.array([bool(truth[key]) for key in frame["session"]])
        verdict = frame["verdict"].to_numpy(dtype=bool)

        wide = frame.pivot_table(
            index="session", columns="replicate", values="verdict", aggfunc="first"
        )
        if wide.shape[1] >= 2:
            first = wide.iloc[:, 0].to_numpy(dtype=bool)
            second = wide.iloc[:, 1].to_numpy(dtype=bool)
            repeatability = float(np.mean(first == second))
            repeat_kappa = kappa(first, second)
        else:
            # A deterministic assessor read once has nothing to say about its own repeatability, and
            # reporting 1.0 would be claiming a property that was never measured.
            repeatability = float("nan")
            repeat_kappa = float("nan")

        positives = actual.sum()
        negatives = (~actual).sum()
        sensitivity = float(verdict[actual].mean()) if positives else float("nan")
        specificity = float((~verdict[~actual]).mean()) if negatives else float("nan")
        rows.append(
            {
                "assessor": assessor,
                "readings": int(len(frame)),
                "pass_rate": float(verdict.mean()),
                "repeatability": repeatability,
                "repeatability_kappa": repeat_kappa,
                "agreement_with_truth": float(np.mean(verdict == actual)),
                "sensitivity": sensitivity,
                "specificity": specificity,
                "youden": youden(sensitivity, specificity),
            }
        )
    return pd.DataFrame(rows)[list(AGREEMENT_COLUMNS)]


def reproducibility(verdicts: pd.DataFrame, replicate: int = 1) -> pd.DataFrame:
    """Every pair of assessors, on the sessions they both read.

    Args:
        verdicts: Readings from :func:`panel_verdicts`.
        replicate: Which reading to compare, so that reproducibility is not contaminated by
            repeatability. Comparing an assessor's first reading with another's second measures both
            problems at once and attributes them to neither.

    Returns:
        A frame with the columns in :data:`REPRODUCIBILITY_COLUMNS`.

    Raises:
        ValueError: If fewer than two assessors read the chosen replicate.
    """
    chosen = verdicts[verdicts["replicate"] == replicate]
    assessors = sorted(set(chosen["assessor"]))
    if len(assessors) < 2:
        raise ValueError(
            f"reproducibility needs two assessors on replicate {replicate}, found {len(assessors)}"
        )
    wide = chosen.pivot_table(
        index="session", columns="assessor", values="verdict", aggfunc="first"
    )
    rows = []
    for left, right in itertools.combinations(assessors, 2):
        both = wide[[left, right]].dropna()
        first = both[left].to_numpy(dtype=bool)
        second = both[right].to_numpy(dtype=bool)
        rows.append(
            {
                "pair": f"{left} vs {right}",
                "sessions": int(len(both)),
                "agreement": float(np.mean(first == second)),
                "kappa": kappa(first, second),
            }
        )
    return pd.DataFrame(rows)[list(REPRODUCIBILITY_COLUMNS)]


def observed_rate(true_rate: float, sensitivity: float, specificity: float) -> float:
    """What an assessor reports as the pass rate when the truth is ``true_rate``.

    ``p*se + (1-p)*(1-sp)``: the true passes it catches, plus the true failures it waves through.

    Raises:
        ValueError: If any argument is outside its unit interval.
    """
    for name, value in (
        ("true rate", true_rate),
        ("sensitivity", sensitivity),
        ("specificity", specificity),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"the {name} has to be between zero and one, got {value}")
    return true_rate * sensitivity + (1.0 - true_rate) * (1.0 - specificity)


def attenuation(
    first_rate: float,
    second_rate: float,
    sensitivity: float,
    specificity: float,
) -> dict[str, float]:
    """A true difference in pass rates, and what an imperfect assessor reports of it.

    The identity this module exists for, and it is exact rather than approximate:

        observed difference = true difference * (sensitivity + specificity - 1)

    Both misclassification errors are independent of the group, which is the assumption that makes
    it exact - an assessor who is harder on the bot's sessions than on the humans' breaks it, in the
    direction of exaggerating rather than attenuating.

    Args:
        first_rate: True pass rate of one group.
        second_rate: True pass rate of the other.
        sensitivity: The assessor's sensitivity.
        specificity: The assessor's specificity.

    Returns:
        A mapping with the true difference, the observed difference, the factor between them, and
        the two observed rates.
    """
    first = observed_rate(first_rate, sensitivity, specificity)
    second = observed_rate(second_rate, sensitivity, specificity)
    return {
        "true_difference": first_rate - second_rate,
        "observed_difference": first - second,
        "factor": youden(sensitivity, specificity),
        "first_observed": first,
        "second_observed": second,
    }


def sessions_for_difference(
    first_rate: float,
    second_rate: float,
    sensitivity: float = 1.0,
    specificity: float = 1.0,
    power: float = 0.80,
    alpha: float = 0.05,
) -> float:
    """Sessions per arm needed to detect a quality difference, through the assessor you have.

    The ordinary two-proportion sample size, applied to the **observed** rates rather than the true
    ones - which is the only version a real study can act on, and is larger than the textbook answer
    by roughly the square of the Youden index.

    Args:
        first_rate: True pass rate of one group.
        second_rate: True pass rate of the other.
        sensitivity: The assessor's sensitivity. One is a perfect gauge.
        specificity: The assessor's specificity.
        power: Power to detect the difference.
        alpha: Two-sided significance level.

    Returns:
        Sessions per arm, not rounded, so that the ratio between two of these is readable.

    Raises:
        ValueError: If the two groups have the same observed rate, in which case no sample size
            detects anything - which is what a gauge with a Youden index of zero does to every
            comparison.
    """
    if not 0.0 < power < 1.0:
        raise ValueError(f"power has to be between zero and one, got {power}")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha has to be between zero and one, got {alpha}")
    first = observed_rate(first_rate, sensitivity, specificity)
    second = observed_rate(second_rate, sensitivity, specificity)
    if first == second:
        raise ValueError(
            "this assessor reports the same rate for both groups, so no number of sessions "
            "distinguishes them"
        )
    critical = float(stats.norm.ppf(1.0 - alpha / 2.0))
    detect = float(stats.norm.ppf(power))
    pooled = (first + second) / 2.0
    numerator = critical * math.sqrt(2.0 * pooled * (1.0 - pooled)) + detect * math.sqrt(
        first * (1.0 - first) + second * (1.0 - second)
    )
    return (numerator / (first - second)) ** 2

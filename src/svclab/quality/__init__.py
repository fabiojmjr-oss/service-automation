"""The quality score as a gauge, qualified before it is used.

:mod:`~svclab.quality.measurement` runs the attribute agreement analysis a quality panel never gets
- repeatability, reproducibility and bias against a declared standard - and then prices what the
panel's error does to the comparison it was built to make.

The result the module exists for is exact rather than approximate: a binary assessor with
sensitivity ``se`` and specificity ``sp`` multiplies every true difference by ``se + sp - 1``,
towards zero, always. A panel that halves differences does not make a study noisier. It makes a real
difference look half as large, and the sample needed to see what is left grows by about the square
of that.
"""

from .measurement import (
    AGREEMENT_COLUMNS,
    LATENT_COLUMNS,
    REPRODUCIBILITY_COLUMNS,
    VERDICT_COLUMNS,
    agreement_table,
    attenuation,
    judge_verdicts,
    kappa,
    latent_quality,
    observed_rate,
    panel_verdicts,
    reproducibility,
    sessions_for_difference,
    youden,
)

__all__ = [
    "AGREEMENT_COLUMNS",
    "LATENT_COLUMNS",
    "REPRODUCIBILITY_COLUMNS",
    "VERDICT_COLUMNS",
    "agreement_table",
    "attenuation",
    "judge_verdicts",
    "kappa",
    "latent_quality",
    "observed_rate",
    "panel_verdicts",
    "reproducibility",
    "sessions_for_difference",
    "youden",
]

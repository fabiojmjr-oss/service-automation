"""Every random draw in the package, and the one rule they all follow.

**Nothing here samples by rejection.** Each draw is an inverse transform of the uniform stream, so
the number of uniforms consumed depends only on how many values are asked for - never on the values
themselves.

That rule is a sibling repository's scar tissue, carried here on purpose rather than rediscovered.
There, a generator that drew with ``Generator.binomial`` published figures that held on one machine
and moved on a clean install: the tables upstream of the binomial matched to the last decimal while
everything after it changed. A rejection sampler consumes a variable number of uniforms per draw, so
the *position* in the stream afterwards depends on the sampler's internals, which are free to change
between library versions. The mechanism fits that evidence and was never reproduced side by side,
which is reason enough to remove the whole class rather than the one instance.

What remains is the bit generator's uniform stream, which numpy guarantees, and the accuracy of a
few quantile functions, where a difference of 1e-16 moves one value by 1e-16 instead of shifting
every draw that follows. ``tests/test_synth.py`` enforces the rule against the source, because a
rule nothing checks is a rule that lasts until the next module.
"""

from __future__ import annotations

import numpy as np
from scipy import stats


def uniform(rng: np.random.Generator, size: int | tuple[int, ...]) -> np.ndarray:
    """Uniforms in the shape asked for - the only primitive anything here may consume."""
    return rng.random(size)


def normal(rng: np.random.Generator, size: int | tuple[int, ...], sd: float = 1.0) -> np.ndarray:
    """Normal draws by inverse transform, in place of ``Generator.normal``.

    ``Generator.standard_normal`` is the ziggurat algorithm, which rejects, so it belongs to the
    same class of hazard as the binomial this rule was written for.
    """
    return np.asarray(stats.norm.ppf(uniform(rng, size)) * sd, dtype=float)


def beta(rng: np.random.Generator, size: int, alpha: float, beta_shape: float) -> np.ndarray:
    """Beta draws by inverse transform, in place of ``Generator.beta``."""
    return np.asarray(stats.beta.ppf(uniform(rng, size), alpha, beta_shape), dtype=float)


def exponential(rng: np.random.Generator, size: int, mean: float) -> np.ndarray:
    """Exponential draws by inverse transform, in place of ``Generator.exponential``.

    Used for handling times and for customer patience, where the memoryless property is the
    assumption the queueing formulas in :mod:`svclab.capacity` are built on - stated here because it
    is an assumption about people, and the one this whole family of models is most often wrong
    about.
    """
    return np.asarray(-mean * np.log1p(-uniform(rng, size)), dtype=float)


def bernoulli(rng: np.random.Generator, probability: np.ndarray) -> np.ndarray:
    """One Bernoulli trial per element of ``probability``."""
    return uniform(rng, probability.size) < probability


def categorical(rng: np.random.Generator, size: int, weights: np.ndarray) -> np.ndarray:
    """One category index per draw, by inverse transform on the cumulative weights.

    In place of ``Generator.choice``, whose stream consumption is not something to rely on.
    """
    cumulative = np.cumsum(np.asarray(weights, dtype=float))
    cumulative = cumulative / cumulative[-1]
    return np.asarray(np.searchsorted(cumulative, uniform(rng, size), side="right"), dtype=int)

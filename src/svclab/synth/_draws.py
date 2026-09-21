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


def normal_from(percentile: np.ndarray, sd: float = 1.0) -> np.ndarray:
    """The normal quantile of uniforms already drawn, separable for the reason below."""
    return np.asarray(stats.norm.ppf(percentile) * sd, dtype=float)


def normal(rng: np.random.Generator, size: int | tuple[int, ...], sd: float = 1.0) -> np.ndarray:
    """Normal draws by inverse transform, in place of ``Generator.normal``.

    ``Generator.standard_normal`` is the ziggurat algorithm, which rejects, so it belongs to the
    same class of hazard as the binomial this rule was written for.
    """
    return normal_from(uniform(rng, size), sd)


def to_latent(percentile: np.ndarray) -> np.ndarray:
    """A percentile as a standard normal value.

    Used with :func:`from_latent` to add a customer-level effect to a trait without touching the
    trait's marginal distribution. Both directions are quantile functions of the uniform stream, so
    the rule this module exists for is not broken by going through them.
    """
    return np.asarray(stats.norm.ppf(percentile), dtype=float)


def from_latent(latent: np.ndarray) -> np.ndarray:
    """A standard normal value back as a percentile, the inverse of :func:`to_latent`."""
    return np.asarray(stats.norm.cdf(latent), dtype=float)


def beta_percentile(value: np.ndarray, alpha: float, beta_shape: float) -> np.ndarray:
    """Which percentile of ``Beta(alpha, beta_shape)`` a value sits at.

    The one place this package inverts a draw rather than making one: a contact's difficulty was
    drawn as a percentile, and recovering it is what lets a second population reuse the identical
    noise instead of drawing its own.
    """
    return np.asarray(stats.beta.cdf(value, alpha, beta_shape), dtype=float)


def beta_quantile(percentile: np.ndarray, alpha: float, beta_shape: float) -> np.ndarray:
    """The ``Beta(alpha, beta_shape)`` quantile of percentiles already in hand."""
    return np.asarray(stats.beta.ppf(percentile, alpha, beta_shape), dtype=float)


def beta(rng: np.random.Generator, size: int, alpha: float, beta_shape: float) -> np.ndarray:
    """Beta draws by inverse transform, in place of ``Generator.beta``."""
    return beta_quantile(uniform(rng, size), alpha, beta_shape)


def exponential_from(percentile: np.ndarray, mean: float) -> np.ndarray:
    """The exponential quantile of uniforms already drawn.

    Used for handling times and for customer patience, where the memoryless property is the
    assumption the queueing formulas in :mod:`svclab.capacity` are built on - stated here because it
    is an assumption about people, and the one this whole family of models is most often wrong
    about.

    Takes a percentile rather than a generator so that a draw can be **kept** and replayed against a
    different world. Wave 4 builds a second population from the identical noise, which is only
    possible where the transform is separable from the drawing.
    """
    return np.asarray(-mean * np.log1p(-percentile), dtype=float)


def bernoulli_from(percentile: np.ndarray, probability: np.ndarray) -> np.ndarray:
    """One Bernoulli trial per element, from uniforms already drawn.

    Separable for the same reason as :func:`exponential_from`: the outcome of a coin whose bias
    changes is only comparable if the coin itself did not.
    """
    return np.asarray(percentile < probability, dtype=bool)


def categorical(rng: np.random.Generator, size: int, weights: np.ndarray) -> np.ndarray:
    """One category index per draw, by inverse transform on the cumulative weights.

    In place of ``Generator.choice``, whose stream consumption is not something to rely on.
    """
    cumulative = np.cumsum(np.asarray(weights, dtype=float))
    cumulative = cumulative / cumulative[-1]
    return np.asarray(np.searchsorted(cumulative, uniform(rng, size), side="right"), dtype=int)

"""The part of a contact that is the person, drawn last so the earlier waves do not move.

Waves 1 to 3 draw every trait per contact. A customer id is therefore a label: two contacts from the
same person are as unrelated as two contacts from strangers, which is why wave 3 measured an
intracluster correlation of approximately zero and had to price its design effects at *declared*
correlations instead of at one it observed.

This module adds the missing half. Each customer gets one percentile of their own for difficulty
and one for patience, and a contact's trait is rebuilt from a latent sum of the customer's
percentile and the occasion's - the Gaussian copula in :class:`svclab.synth.PopulationProfile`.

Three properties of the construction are worth stating before any figure is read.

**The marginal distribution does not move.** A contact's difficulty is still Beta(2, 4) with the
same mean, variance and support, and its patience is still exponential with the same mean. Only the
dependence between two contacts of one customer changes, which is what makes a difference between
the two worlds attributable to one cause.

**The noise is not redrawn.** The occasion's percentile is recovered from the difficulty the contact
table already carries, and patience reuses the uniform it already stores. Every coin is the same
coin; only who is holding it changed.

**And the correlation of a trait is not the correlation of an outcome.** A resolution is a coin flip
whose bias is correlated, not a correlated coin flip, and the Bernoulli noise on top of the bias is
most of the variance. The attenuation is measured in :mod:`svclab.population` rather than assumed
away, and it is the difference between a design effect that is a rounding error and one that is not.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from ._draws import beta_percentile, beta_quantile, from_latent, to_latent, uniform
from .config import CENTRE, POPULATION, CentreProfile, PopulationProfile
from .contacts import intent_index, outcomes_from_difficulty

#: Columns of the per-customer component frame, indexed by customer id.
CUSTOMER_COLUMNS = ("customer", "difficulty_percentile", "patience_percentile")


def customer_components(rng: np.random.Generator, centre: CentreProfile = CENTRE) -> pd.DataFrame:
    """One row per customer: the percentile of difficulty and of patience that is the person.

    Percentiles rather than values, because the copula works on percentiles and because a percentile
    is the one representation that does not commit to a distribution. Two draws per customer and not
    per contact, which is the whole difference this wave introduces.

    Args:
        rng: The shared generator, consumed after every earlier draw in the dataset.
        centre: The centre's declared shape.

    Returns:
        A frame with the columns in :data:`CUSTOMER_COLUMNS`, one row per customer.
    """
    return pd.DataFrame(
        {
            "customer": np.arange(centre.customers, dtype=int),
            "difficulty_percentile": uniform(rng, centre.customers),
            "patience_percentile": uniform(rng, centre.customers),
        }
    )[list(CUSTOMER_COLUMNS)]


def blend(occasion: np.ndarray, own: np.ndarray, correlation: float) -> np.ndarray:
    """Two percentiles into one, with a declared share of the latent variance belonging to ``own``.

    The Gaussian copula, in the one line it comes down to: on the latent scale the two parts are
    weighted ``sqrt(rho)`` and ``sqrt(1 - rho)``, so the sum is standard normal again - which is why
    the trait's marginal distribution survives the operation untouched.

    Args:
        occasion: Percentile belonging to this contact.
        own: Percentile belonging to this contact's customer.
        correlation: Share of the latent variance that belongs to the customer, in ``[0, 1]``.

    Returns:
        The blended percentile.

    Raises:
        ValueError: If the correlation is outside the unit interval.
    """
    if not 0.0 <= correlation <= 1.0:
        raise ValueError(f"a correlation must be in [0, 1], not {correlation}")
    latent = math.sqrt(correlation) * to_latent(own) + math.sqrt(1.0 - correlation) * to_latent(
        occasion
    )
    return from_latent(latent)


def correlated_contacts(
    table: pd.DataFrame,
    components: pd.DataFrame,
    centre: CentreProfile = CENTRE,
    population: PopulationProfile = POPULATION,
) -> pd.DataFrame:
    """The same contacts in a world where a customer is a person.

    Args:
        table: The contact table from :func:`svclab.synth.contacts`.
        components: The per-customer percentiles from :func:`customer_components`.
        centre: The centre's declared shape.
        population: The declared correlations.

    Returns:
        A contact table of the same shape, with ``difficulty`` and ``patience_turns`` correlated
        within a customer and every outcome that follows from them recomputed from the uniforms
        already drawn. The marginal distribution of both traits is unchanged.

    Raises:
        KeyError: If the component frame does not cover every customer in the table.
    """
    missing = set(table["customer"].unique()) - set(components["customer"])
    if missing:
        raise KeyError(f"{len(missing)} customers have no drawn components")

    ordered = components.set_index("customer")
    customer = table["customer"].to_numpy(dtype=int)

    occasion = beta_percentile(
        table["difficulty"].to_numpy(dtype=float), centre.difficulty_alpha, centre.difficulty_beta
    )
    own = ordered["difficulty_percentile"].reindex(customer).to_numpy(dtype=float)
    blended = blend(occasion, own, population.difficulty_correlation)
    difficulty = beta_quantile(blended, centre.difficulty_alpha, centre.difficulty_beta)

    own = ordered["patience_percentile"].reindex(customer).to_numpy(dtype=float)
    percentile = blend(
        table["u_patience"].to_numpy(dtype=float), own, population.patience_correlation
    )

    remixed = table.assign(difficulty=difficulty, u_patience=percentile)
    return outcomes_from_difficulty(remixed, intent_index(table), centre)


def latent_traits(table: pd.DataFrame, centre: CentreProfile = CENTRE) -> pd.DataFrame:
    """A contact's two traits on the latent normal scale, where the declared correlation lives.

    The copula's guarantee is exact on this scale and approximate on any other, so a test that wants
    to check the declared number against the data has to look here. Published as a function rather
    than buried in a test because the distinction is the point: the correlation an analyst declares
    and the correlation their data shows are two different quantities.

    Args:
        table: A contact table.
        centre: The centre's declared shape.

    Returns:
        A frame with ``customer``, ``latent_difficulty`` and ``latent_patience``.
    """
    return pd.DataFrame(
        {
            "customer": table["customer"].to_numpy(dtype=int),
            "latent_difficulty": to_latent(
                beta_percentile(
                    table["difficulty"].to_numpy(dtype=float),
                    centre.difficulty_alpha,
                    centre.difficulty_beta,
                )
            ),
            "latent_patience": to_latent(table["u_patience"].to_numpy(dtype=float)),
        }
    )

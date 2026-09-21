"""One seeded dataset feeding every module, so no example needs its own fixture."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import CENTRE, CHAIN, CONCENTRATION, SEED, ConcentrationProfile
from .contacts import contacts, intent_truth
from .customers import correlated_contacts, customer_components
from .frequency import reassign_customers
from .quality import quality_noise
from .returns import return_draws
from .routing import routing_scores, scores_from


@dataclass(frozen=True)
class Dataset:
    """Every table the toolkit's examples and tests are built on.

    Attributes:
        contacts: One row per contact, including the difficulty and the self-service counterfactual
            no real contact centre has.
        intent_truth: One row per intent, with the share of volume where automation creates
            anything at all.
        panel_noise: One row per sampled contact, grader and replicate: the noise that grader adds
            to that reading. The sample and the noise are draws; the quality being read is not.
        judge_noise: One row per contact: the noise the automated assessor adds. It reads
            everything, because that is the cheap assessor's whole argument.
        routing_scores: One row per contact: the confidence the routing classifier reports in its
            own label. Drawn after the quality noise, so adding it could not move a figure the
            earlier waves published.
        customer_components: One row per customer: the difficulty and the patience that belong to
            the person rather than to the occasion. Drawn after the scores, for the same reason, and
            unused by :func:`generate_dataset`'s own world - :func:`correlated_dataset` is what
            consumes it.
        return_draws: One row per contact and further attempt: whether the customer comes back
            again, and whether the human resolves it that time. Drawn last of all, and spent only by
            a run that is given a chain longer than the one repeat waves 1 to 5 allow.
    """

    contacts: pd.DataFrame
    intent_truth: pd.DataFrame
    panel_noise: pd.DataFrame
    judge_noise: pd.DataFrame
    routing_scores: pd.DataFrame
    customer_components: pd.DataFrame
    return_draws: pd.DataFrame


def generate_dataset(seed: int = SEED) -> Dataset:
    """Build the whole dataset from one seed.

    New tables are appended at the end of this function rather than inserted, because the generator
    is consumed in stream order: inserting a draw shifts every later table and every published
    figure with it.

    Args:
        seed: Seed for the shared generator. The published figures all use the default.

    Returns:
        A :class:`Dataset`.
    """
    rng = np.random.default_rng(seed)
    table = contacts(rng)
    # Appended after every draw in `contacts`, and it must stay there: inserting a draw earlier
    # shifts the whole stream and moves every figure wave 1 published.
    panel, judge = quality_noise(rng, CENTRE)
    # And the routing scores after those, for the same reason.
    scores = routing_scores(rng, table)
    # And the per-customer components last of all. They are drawn in this world and spent in the
    # other one, which is the only arrangement under which wave 4 could exist without moving a
    # single figure waves 1 to 3 published.
    components = customer_components(rng, CENTRE)
    # And the chain's draws last of all, for the third time in three waves: a table drawn at the end
    # of the stream cannot move a figure that was published before it existed.
    chain = return_draws(rng, CENTRE, CHAIN)
    return Dataset(
        contacts=table,
        intent_truth=intent_truth(table),
        panel_noise=panel,
        judge_noise=judge,
        routing_scores=scores,
        customer_components=components,
        return_draws=chain,
    )


def correlated_dataset(data: Dataset) -> Dataset:
    """The same account in a world where a customer is a person rather than a label.

    Nothing is redrawn. The contacts keep their uniforms, the quality panel keeps its noise and the
    classifier keeps its blur; only the difficulty and the patience of each contact are remixed,
    and everything that follows from them is recomputed. A comparison between the two datasets is
    therefore a comparison of one structural assumption, with the sampling noise held fixed.

    Args:
        data: A dataset from :func:`generate_dataset`.

    Returns:
        A :class:`Dataset` of the same shape, in the correlated world.
    """
    table = correlated_contacts(data.contacts, data.customer_components)
    return Dataset(
        contacts=table,
        intent_truth=intent_truth(table),
        panel_noise=data.panel_noise,
        judge_noise=data.judge_noise,
        routing_scores=scores_from(table, data.routing_scores["u_score"].to_numpy(dtype=float)),
        customer_components=data.customer_components,
        return_draws=data.return_draws,
    )


def concentrated_dataset(
    data: Dataset, concentration: ConcentrationProfile = CONCENTRATION
) -> Dataset:
    """The same contacts, grouped into customers who do not all contact equally often.

    Nothing about a contact changes: not its difficulty, not its arm, not its handling time, not the
    classifier's score. Only which contacts belong to one person, which means **every per-contact
    figure in this repository is bit-for-bit identical in the returned dataset** and everything
    measured per customer is not.

    Compose it before :func:`correlated_dataset` when both are wanted, because the copula correlates
    a customer's contacts and has to know who the customer is::

        concentrated = concentrated_dataset(data)
        both = correlated_dataset(concentrated)

    Args:
        data: A dataset from :func:`generate_dataset`.
        concentration: The declared dispersion and difficulty correlation.

    Returns:
        A :class:`Dataset` whose contact table is regrouped. The intent truth and the routing scores
        are carried over rather than recomputed, because neither depends on the customer.
    """
    table = reassign_customers(data.contacts, data.customer_components, concentration)
    return Dataset(
        contacts=table,
        intent_truth=data.intent_truth,
        panel_noise=data.panel_noise,
        judge_noise=data.judge_noise,
        routing_scores=data.routing_scores,
        customer_components=data.customer_components,
        return_draws=data.return_draws,
    )

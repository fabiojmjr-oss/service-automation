"""One seeded dataset feeding every module, so no example needs its own fixture."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import CENTRE, SEED
from .contacts import contacts, intent_truth
from .quality import quality_noise


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
    """

    contacts: pd.DataFrame
    intent_truth: pd.DataFrame
    panel_noise: pd.DataFrame
    judge_noise: pd.DataFrame


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
    return Dataset(
        contacts=table,
        intent_truth=intent_truth(table),
        panel_noise=panel,
        judge_noise=judge,
    )

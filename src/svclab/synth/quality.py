"""The quality of a session, and the noise every assessor of it carries.

Two things are drawn here and nothing else is. The **sample** the human panel reads, because quality
assurance reads a fraction of the volume and which fraction is a draw. And the **noise** each
assessor adds to each reading, one value per grader per replicate per sampled session, plus one for
the automated judge on every session.

Both are drawn per contact, before any policy runs, for the reason the whole package is built this
way: a grader's noise must not change when the bot's policy changes, or a comparison between two
policies is a comparison between two noise draws.

What is **not** drawn here is the quality itself. A session's latent quality is a declared function
of what happened to it - who handled it, whether it resolved, and how hard it was - computed in
:mod:`svclab.quality` from the outcome frame. That keeps the truth deterministic given the policy,
which is what lets the measurement error be isolated from everything else.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._draws import normal, uniform
from .config import GRADERS, JUDGE, QUALITY, CentreProfile, QualityProfile

#: Columns of the panel's noise frame: one row per sampled session, grader and replicate.
PANEL_NOISE_COLUMNS = ("contact", "grader", "replicate", "noise")

#: Columns of the judge's noise frame: one row per contact.
JUDGE_NOISE_COLUMNS = ("contact", "noise")


def quality_noise(
    rng: np.random.Generator,
    centre: CentreProfile,
    quality: QualityProfile = QUALITY,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The sampled sessions with their graders' noise, and the judge's noise on everything.

    Args:
        rng: The shared generator. Consumed after every draw in :func:`svclab.synth.contacts`, so
            adding a draw here cannot move a figure published by wave 1.
        centre: The centre's declared shape, for how many contacts there are to sample from.
        quality: The declared sample size, replicate count and standard.

    Returns:
        ``(panel, judge)``. The panel frame has the columns in :data:`PANEL_NOISE_COLUMNS`, one row
        per sampled contact per grader per replicate. The judge frame has
        :data:`JUDGE_NOISE_COLUMNS`, one row per contact.

    Raises:
        ValueError: If the sample is larger than the number of contacts, which is a sampling plan
            that does not describe this centre.
    """
    if quality.sample > centre.contacts:
        raise ValueError(f"the panel cannot sample {quality.sample} of {centre.contacts} contacts")
    # Sorted uniform keys rather than a shuffle: one uniform per contact, and argsort is
    # deterministic, so the sample is reproducible without a permutation primitive.
    keys = uniform(rng, centre.contacts)
    sampled = np.sort(np.argsort(keys)[: quality.sample])

    rows = quality.sample * len(GRADERS) * quality.replicates
    draws = normal(rng, rows)
    spread = np.array([profile.noise_sd for profile in GRADERS])
    labels = np.array([profile.grader for profile in GRADERS])

    contact = np.repeat(sampled, len(GRADERS) * quality.replicates)
    grader_index = np.tile(np.repeat(np.arange(len(GRADERS)), quality.replicates), quality.sample)
    replicate = np.tile(np.arange(1, quality.replicates + 1), quality.sample * len(GRADERS))
    panel = pd.DataFrame(
        {
            "contact": contact,
            "grader": labels[grader_index],
            "replicate": replicate,
            "noise": draws * spread[grader_index],
        }
    )[list(PANEL_NOISE_COLUMNS)]

    judge = pd.DataFrame(
        {
            "contact": np.arange(centre.contacts, dtype=int),
            "noise": normal(rng, centre.contacts) * JUDGE.noise_sd,
        }
    )[list(JUDGE_NOISE_COLUMNS)]
    return panel, judge

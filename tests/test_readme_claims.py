"""Every figure quoted in a README, re-derived.

Marked slow because they build the full dataset, run every policy against it and execute the example
script. The point is not coverage: it is that a change which moves a published number breaks the build
instead of leaving the text quietly wrong.
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from svclab.bot import GUARDED, HUMAN_ONLY, PATIENT, POLICIES, THREE_TURNS, run
from svclab.capacity import (
    agents_for,
    capacity_table,
    erlang_b,
    erlang_c,
    impatience_table,
    load_with_repeats,
    occupancy,
    service_level,
)
from svclab.concentration import burden_table, concentration_table, precision_table
from svclab.containment import containment_table, deflection, selection_profile
from svclab.experiment import intracluster_correlation, sizing_table
from svclab.population import (
    correlation_table,
    design_table,
    error_table,
    pair_failures,
    power_at,
    world_table,
)
from svclab.quality import (
    agreement_table,
    attenuation,
    judge_verdicts,
    kappa,
    latent_quality,
    panel_verdicts,
    reproducibility,
    sessions_for_difference,
    youden,
)
from svclab.routing import best_by, calibrated_threshold, cost_curve, cost_of, defer_below
from svclab.synth import (
    CENTRE,
    EQUAL_RATES,
    POPULATION,
    QUALITY,
    ROUTING,
    Dataset,
    concentrated_dataset,
    correlated_dataset,
)

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def arms(full: Dataset) -> tuple:
    """The treated and control arms, and one outcome frame per policy."""
    treated = full.contacts[~full.contacts["holdout"]]
    held = full.contacts[full.contacts["holdout"]]
    outcomes = {policy.name: run(treated, policy) for policy in POLICIES}
    return treated, held, outcomes, run(held, HUMAN_ONLY)


# --- svclab.synth ------------------------------------------------------------------------------


def test_the_centre_is_the_size_every_readme_quotes(full: Dataset) -> None:
    assert len(full.contacts) == 40_000
    assert full.contacts["customer"].nunique() == 20_377
    assert CENTRE.days == 30
    assert CENTRE.holdout_share == 0.20
    assert CENTRE.operating_hours_per_day == 12.0
    assert CENTRE.target_answer_seconds == 20.0
    assert CENTRE.target_service_level == 0.80
    assert CENTRE.handoff_seconds == 55.0
    assert CENTRE.bot_seconds_per_turn == 45.0
    assert CENTRE.patience_turns_mean == 4.0
    assert int((~full.contacts["holdout"]).sum()) == 31_802
    assert int(full.contacts["holdout"].sum()) == 8_198


def test_the_intent_truth_table_is_what_is_published(full: Dataset) -> None:
    published = {
        "rastreio": (0.34, 13_583, 0.3340, 0.6493, 0.2295, 0.4822, 259.34, 0.9625),
        "prazo-de-entrega": (0.24, 9_485, 0.3347, 0.5069, 0.1414, 0.4212, 329.20, 0.9467),
        "cadastro": (0.14, 5_652, 0.3324, 0.5117, 0.0826, 0.4570, 329.68, 0.9321),
        "reembolso": (0.16, 6_516, 0.3338, 0.1036, 0.0124, 0.1014, 537.60, 0.8958),
        "reclamacao": (0.12, 4_764, 0.3347, 0.0050, 0.0061, 0.0048, 713.65, 0.8539),
    }
    truth = full.intent_truth.set_index("intent")
    for intent, values in published.items():
        share, contacts, difficulty, resolve, serve, needed, seconds, human = values
        row = truth.loc[intent]
        assert float(row["share"]) == pytest.approx(share, abs=5e-9), intent
        assert int(row["contacts"]) == contacts, intent
        assert float(row["mean_difficulty"]) == pytest.approx(difficulty, abs=5e-5), intent
        assert float(row["bot_can_resolve_rate"]) == pytest.approx(resolve, abs=5e-5), intent
        assert float(row["would_self_serve_rate"]) == pytest.approx(serve, abs=5e-5), intent
        assert float(row["resolvable_and_needed"]) == pytest.approx(needed, abs=5e-5), intent
        assert float(row["mean_human_seconds"]) == pytest.approx(seconds, abs=5e-3), intent
        assert float(row["human_resolves_rate"]) == pytest.approx(human, abs=5e-5), intent


def test_the_account_wide_shares_are_what_is_published(full: Dataset) -> None:
    contacts = full.contacts
    resolvable = contacts["bot_can_resolve"]
    needed = resolvable & ~contacts["would_self_serve"]
    assert float(resolvable.mean()) == pytest.approx(0.4305, abs=5e-5)
    assert float(needed.mean()) == pytest.approx(0.3453, abs=5e-5)


# --- svclab.bot --------------------------------------------------------------------------------


def test_the_outcome_splits_per_policy_are_what_is_published(arms: tuple) -> None:
    """The bot README's claim about what a longer turn budget converts, on the treated arm."""
    _, _, outcomes, _ = arms
    published = {
        "three-turns": {"escalated": 0.3935, "abandoned": 0.3316, "resolved-by-bot": 0.2749},
        "patient": {"abandoned": 0.5377, "resolved-by-bot": 0.2792, "escalated": 0.1831},
    }
    for name, shares in published.items():
        frame = outcomes[name]
        first = frame[~frame["is_repeat"]]
        measured = first["outcome"].value_counts(normalize=True)
        for outcome, share in shares.items():
            assert float(measured[outcome]) == pytest.approx(share, abs=5e-5), (name, outcome)
    # The claim the paragraph rests on: resolution barely moves while abandonment doubles.
    assert published["patient"]["resolved-by-bot"] > published["three-turns"]["resolved-by-bot"]
    assert published["patient"]["abandoned"] > 1.5 * published["three-turns"]["abandoned"]
    assert published["patient"]["escalated"] < 0.5 * published["three-turns"]["escalated"]


def test_the_policies_are_the_ones_documented() -> None:
    assert HUMAN_ONLY.turn_budget == 0
    assert THREE_TURNS.turn_budget == 3
    assert PATIENT.turn_budget == 6
    assert GUARDED.turn_budget == 3
    assert GUARDED.straight_to_human == frozenset({"reembolso", "reclamacao"})


# --- svclab.containment ------------------------------------------------------------------------


def test_the_containment_table_is_what_is_published(arms: tuple, full: Dataset) -> None:
    _, _, outcomes, _ = arms
    published = {
        "human-only": (33_190, 0.0436, 0.0000, 0.0000, 0.0000, 0.0000, 0.9305, 3645.64),
        "three-turns": (38_476, 0.2099, 0.6065, 0.2749, 0.4190, 0.2145, 0.6355, 2730.43),
        "patient": (42_015, 0.3211, 0.8169, 0.2792, 0.5059, 0.2187, 0.4476, 2316.78),
        "guarded": (36_287, 0.1410, 0.4886, 0.2630, 0.3809, 0.2029, 0.7271, 2861.54),
    }
    table = containment_table(outcomes, full.contacts).set_index("policy")
    for name, values in published.items():
        sessions, repeats, session, resolution, adjusted, needed, rate, hours = values
        row = table.loc[name]
        assert int(row["contacts"]) == 31_802, name
        assert int(row["sessions"]) == sessions, name
        assert float(row["repeats_per_contact"]) == pytest.approx(repeats, abs=5e-5), name
        assert float(row["session_containment"]) == pytest.approx(session, abs=5e-5), name
        assert float(row["resolution_containment"]) == pytest.approx(resolution, abs=5e-5), name
        assert float(row["repeat_adjusted_containment"]) == pytest.approx(adjusted, abs=5e-5), name
        assert float(row["needed_containment"]) == pytest.approx(needed, abs=5e-5), name
        assert float(row["resolution_rate"]) == pytest.approx(rate, abs=5e-5), name
        assert float(row["human_hours"]) == pytest.approx(hours, abs=5e-3), name


def test_the_widest_reading_is_the_published_multiple_of_the_narrowest(
    arms: tuple, full: Dataset
) -> None:
    """The headline of the containment README: 2.83 times, for one ordinary policy."""
    _, _, outcomes, _ = arms
    row = containment_table(outcomes, full.contacts).set_index("policy").loc["three-turns"]
    ratio = float(row["session_containment"]) / float(row["needed_containment"])
    assert ratio == pytest.approx(2.83, abs=5e-3)


def test_every_containment_definition_prefers_the_policy_that_resolves_least(
    arms: tuple, full: Dataset
) -> None:
    """The wave's central claim, asserted as the ranking it is."""
    _, _, outcomes, _ = arms
    table = containment_table(outcomes, full.contacts)
    ranked = table[table["policy"] != "human-only"]
    for column in (
        "session_containment",
        "resolution_containment",
        "repeat_adjusted_containment",
        "needed_containment",
    ):
        assert ranked.loc[ranked[column].idxmax(), "policy"] == "patient", column
    assert ranked.loc[ranked["resolution_rate"].idxmax(), "policy"] == "guarded"
    by_policy = table.set_index("policy")
    assert float(by_policy.loc["patient", "resolution_rate"]) == pytest.approx(0.4476, abs=5e-5)
    assert float(by_policy.loc["guarded", "resolution_rate"]) == pytest.approx(0.7271, abs=5e-5)


def test_the_selection_profile_is_what_is_published(arms: tuple, full: Dataset) -> None:
    _, _, outcomes, _ = arms
    published = {
        "resolved-by-bot": (8_743, 0.2749, 0.2383, 0.2198, 263.21),
        "abandoned": (10_544, 0.3316, 0.3656, 0.1041, 410.19),
        "reached-a-human": (12_515, 0.3935, 0.3758, 0.0802, 451.90),
        "came-back": (6_674, 0.2099, 0.3767, 0.0000, 467.28),
        "all-contacts": (31_802, 1.0000, 0.3346, 0.1265, 386.20),
    }
    profile = selection_profile(outcomes["three-turns"], full.contacts).set_index("group")
    for group, values in published.items():
        contacts, share, difficulty, serve, seconds = values
        row = profile.loc[group]
        assert int(row["contacts"]) == contacts, group
        assert float(row["share"]) == pytest.approx(share, abs=5e-5), group
        assert float(row["mean_difficulty"]) == pytest.approx(difficulty, abs=5e-5), group
        assert float(row["would_self_serve_rate"]) == pytest.approx(serve, abs=5e-5), group
        assert float(row["mean_human_seconds"]) == pytest.approx(seconds, abs=5e-3), group

    bot = float(profile.loc["resolved-by-bot", "mean_difficulty"])
    human = float(profile.loc["reached-a-human", "mean_difficulty"])
    assert human / bot == pytest.approx(1.58, abs=5e-3)
    everything = float(profile.loc["all-contacts", "mean_human_seconds"])
    residue = float(profile.loc["reached-a-human", "mean_human_seconds"])
    assert residue / everything - 1.0 == pytest.approx(0.17, abs=5e-3)


def test_the_deflection_figures_are_what_is_published(arms: tuple, full: Dataset) -> None:
    _, _, outcomes, control = arms
    published = {
        "three-turns": (1.1849, 0.8579, 0.8201, 0.8958, 0.4377, 0.7216),
        "patient": (0.9902, 1.0526, 1.0153, 1.0900, 0.5370, 0.6573),
        "guarded": (1.2813, 0.7615, 0.7234, 0.7997, 0.3885, 0.7952),
    }
    table = containment_table(outcomes, full.contacts).set_index("policy")
    assert control["customer"].nunique() == 4_182
    assert outcomes["three-turns"]["customer"].nunique() == 16_195
    for name, values in published.items():
        treated_each, per_customer, low, high, per_contact, share = values
        measured = deflection(outcomes[name], control)
        assert float(measured.treated_per_customer) == pytest.approx(treated_each, abs=5e-5), name
        assert float(measured.holdout_per_customer) == pytest.approx(2.0428, abs=5e-5), name
        assert float(measured.deflected_per_customer) == pytest.approx(per_customer, abs=5e-5), name
        assert measured.interval[0] == pytest.approx(low, abs=5e-5), name
        assert measured.interval[1] == pytest.approx(high, abs=5e-5), name
        assert measured.contacts_per_customer == pytest.approx(1.9603, abs=5e-5), name
        assert (measured.deflected_per_customer / measured.contacts_per_customer) == pytest.approx(
            per_contact, abs=5e-5
        ), name
        quoted = float(table.loc[name, "session_containment"])
        assert measured.share_of(quoted) == pytest.approx(share, abs=5e-5), name
        assert measured.significant, name

    # The ordering the documents claim: the more contained, the more overstated.
    shares = {
        name: deflection(outcomes[name], control).share_of(
            float(table.loc[name, "session_containment"])
        )
        for name in published
    }
    assert shares["guarded"] > shares["three-turns"] > shares["patient"]


def test_the_automation_raised_total_conversations_by_the_published_share(
    arms: tuple, full: Dataset
) -> None:
    _, _, outcomes, _ = arms
    table = containment_table(outcomes, full.contacts).set_index("policy")
    baseline = float(table.loc["human-only", "sessions"])
    worst = float(table.loc["patient", "sessions"])
    assert worst / baseline - 1.0 == pytest.approx(0.266, abs=5e-4)


# --- svclab.capacity ---------------------------------------------------------------------------


def test_the_erlang_figures_quoted_in_the_readme(arms: tuple) -> None:
    assert erlang_c(1, 0.5) == pytest.approx(0.5, rel=1e-14)
    assert erlang_b(1, 2.0) == pytest.approx(2.0 / 3.0, rel=1e-14)
    assert agents_for(20.0, 395.43, 20.0, 0.80) == 25
    assert agents_for(10.0, 395.43, 20.0, 0.80) == 14
    assert service_level(14, 10.1268, 395.43, 20.0) == pytest.approx(0.8455, abs=5e-5)
    assert agents_for(10.1268, 395.43, 20.0, 0.80) == 14
    assert occupancy(14, 10.1268) == pytest.approx(0.7233, abs=5e-5)
    # Half the work needs 56% of the people, not 50%.
    assert pytest.approx(0.56, abs=5e-3) == 14 / 25


def test_the_capacity_table_is_what_is_published(arms: tuple, full: Dataset) -> None:
    _, _, outcomes, _ = arms
    published = {
        "human-only": (33_190, 395.43, 10.1268, 14, 0.7233, 0.8455, 14.00, 0.00),
        "three-turns": (19_189, 512.25, 7.5845, 11, 0.6895, 0.8368, 5.51, 5.49),
        "patient": (16_036, 520.10, 6.4355, 10, 0.6435, 0.8726, 2.56, 7.44),
        "guarded": (20_750, 496.46, 7.9487, 12, 0.6624, 0.8855, 7.16, 4.84),
    }
    containment = (
        containment_table(outcomes, full.contacts)
        .set_index("policy")["session_containment"]
        .to_dict()
    )
    table = capacity_table(outcomes, containment, baseline="human-only").set_index("policy")
    for name, values in published.items():
        sessions, seconds, load, agents, busy, level, promised, missing = values
        row = table.loc[name]
        assert int(row["human_sessions"]) == sessions, name
        assert float(row["mean_handling_seconds"]) == pytest.approx(seconds, abs=5e-3), name
        assert float(row["offered_load"]) == pytest.approx(load, abs=5e-5), name
        assert int(row["agents_needed"]) == agents, name
        assert float(row["occupancy"]) == pytest.approx(busy, abs=5e-5), name
        assert float(row["service_level"]) == pytest.approx(level, abs=5e-5), name
        assert float(row["agents_promised"]) == pytest.approx(promised, abs=5e-3), name
        assert float(row["agents_missing"]) == pytest.approx(missing, abs=5e-3), name


def test_the_capacity_gap_decomposes_into_the_published_agent_counts(
    arms: tuple, full: Dataset
) -> None:
    """The four rows of the decomposition, and the 2.83 times the promise overstates the saving."""
    _, _, outcomes, _ = arms
    period = CENTRE.days * CENTRE.operating_hours_per_day * 3600.0
    baseline = outcomes["human-only"]
    bot = outcomes["three-turns"]
    base_human = baseline[baseline["handled_by_human"]]
    bot_human = bot[bot["handled_by_human"]]
    first = bot_human[~bot_human["is_repeat"]]
    base_seconds = float(base_human["human_seconds"].mean())

    def staffing(sessions: int, seconds: float) -> int:
        from svclab.capacity import offered_load

        return agents_for(
            offered_load(sessions, seconds, period),
            seconds,
            CENTRE.target_answer_seconds,
            CENTRE.target_service_level,
        )

    assert staffing(len(base_human), base_seconds) == 14
    assert staffing(len(first), base_seconds) == 7
    assert float(first["human_seconds"].mean()) == pytest.approx(506.9, abs=5e-2)
    assert staffing(len(first), float(first["human_seconds"].mean())) == 8
    assert staffing(len(bot_human), float(bot_human["human_seconds"].mean())) == 11

    containment = (
        containment_table(outcomes, full.contacts)
        .set_index("policy")["session_containment"]
        .to_dict()
    )
    table = capacity_table(outcomes, containment, baseline="human-only").set_index("policy")
    promised_saving = 14 - float(table.loc["three-turns", "agents_promised"])
    real_saving = 14 - int(table.loc["three-turns", "agents_needed"])
    assert promised_saving == pytest.approx(8.49, abs=5e-3)
    assert real_saving == 3
    assert promised_saving / real_saving == pytest.approx(2.83, abs=5e-3)
    # And the three effects, in the order the document ranks them.
    assert 7 - promised_agents_gap() == pytest.approx(1.49, abs=5e-3)


def promised_agents_gap() -> float:
    """The promise for `three-turns`, which the decomposition's first step is measured against."""
    from svclab.capacity import promised_agents

    return promised_agents(14, 0.6065)


# --- svclab.population --------------------------------------------------------------------------


def _worlds(
    full: Dataset, correlated: Dataset
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    """The two worlds, and the two arms of each, as the module's README computes them."""
    contacts = {"independent": full.contacts, "correlated": correlated.contacts}
    treated = {name: run(t[~t["holdout"]], THREE_TURNS) for name, t in contacts.items()}
    control = {name: run(t[t["holdout"]], HUMAN_ONLY) for name, t in contacts.items()}
    return contacts, treated, control


def test_the_two_worlds_agree_on_every_figure_by_what_is_published(
    full: Dataset, correlated: Dataset
) -> None:
    published = {
        "mean difficulty": (0.3340, 0.3347),
        "difficulty sd": (0.1776, 0.1782),
        "mean patience turns": (4.5178, 4.5117),
        "session containment": (0.6065, 0.6046),
        "needed containment": (0.2145, 0.2126),
        "resolution rate": (0.6355, 0.6357),
        "repeats per contact": (0.2099, 0.2094),
        "human hours": (2730.43, 2728.43),
    }
    contacts, treated, _control = _worlds(full, correlated)
    table = world_table(contacts, treated)
    indexed = table.set_index("metric")
    for metric, (first, second) in published.items():
        tolerance = 5e-3 if metric == "human hours" else 5e-5
        assert float(indexed.loc[metric, "independent"]) == pytest.approx(first, abs=tolerance), (
            metric
        )
        assert float(indexed.loc[metric, "correlated"]) == pytest.approx(second, abs=tolerance), (
            metric
        )
    assert float(indexed.loc["human hours", "difference"]) == pytest.approx(-2.00, abs=5e-3)
    relative = (table["difference"] / table["independent"]).abs()
    assert float(relative.max()) == pytest.approx(0.0089, abs=5e-5)
    assert table.loc[relative.idxmax(), "metric"] == "needed containment"


def test_the_attenuation_chain_is_what_is_published(full: Dataset, correlated: Dataset) -> None:
    contacts, treated, _control = _worlds(full, correlated)
    table = correlation_table(contacts, treated).set_index("stage")
    assert float(table.loc["declared", "difficulty"]) == POPULATION.difficulty_correlation
    assert float(table.loc["declared", "patience"]) == POPULATION.patience_correlation
    assert float(table.loc["latent", "difficulty"]) == pytest.approx(0.2535, abs=5e-5)
    assert float(table.loc["latent", "patience"]) == pytest.approx(0.0911, abs=5e-5)
    assert float(table.loc["observed", "difficulty"]) == pytest.approx(0.2463, abs=5e-5)
    assert float(table.loc["observed", "patience"]) == pytest.approx(0.0740, abs=5e-5)
    outcome = float(table.loc["outcome", "resolution"])
    assert outcome == pytest.approx(0.0448, abs=5e-5)
    assert POPULATION.difficulty_correlation / outcome == pytest.approx(5.6, abs=0.05)


def test_the_design_effect_of_the_correlated_world_is_what_is_published(
    full: Dataset, correlated: Dataset
) -> None:
    _contacts, treated, _control = _worlds(full, correlated)
    table = design_table(treated).set_index("world")
    assert float(table.loc["independent", "icc"]) == pytest.approx(-0.0126, abs=5e-5)
    assert float(table.loc["independent", "design_effect"]) == pytest.approx(0.9806, abs=5e-5)
    assert math.isnan(float(table.loc["independent", "actual_alpha"]))
    assert float(table.loc["correlated", "icc"]) == pytest.approx(0.0448, abs=5e-5)
    assert float(table.loc["correlated", "mean_cluster_size"]) == pytest.approx(1.9637, abs=5e-5)
    assert float(table.loc["correlated", "effective_cluster_size"]) == pytest.approx(
        2.5469, abs=5e-5
    )
    assert float(table.loc["correlated", "design_effect"]) == pytest.approx(1.0693, abs=5e-5)
    assert float(table.loc["correlated", "sample_inflation"]) == pytest.approx(0.0693, abs=5e-5)
    assert float(table.loc["correlated", "actual_alpha"]) == pytest.approx(0.0580, abs=5e-5)
    # The number this table published before wave 5 corrected the cluster size it uses, kept in the
    # frame and asserted here so the correction cannot quietly un-happen.
    assert float(table.loc["correlated", "design_effect_at_mean"]) == pytest.approx(
        1.0432, abs=5e-5
    )


def test_the_power_at_wave_threes_sizing_is_what_is_published(
    full: Dataset, correlated: Dataset
) -> None:
    _contacts, treated, _control = _worlds(full, correlated)
    measured = float(design_table(treated).set_index("world").loc["correlated", "design_effect"])
    assert power_at(1.0, 0.0916, 0.6355, 405) == pytest.approx(0.8026, abs=5e-5)
    assert power_at(measured, 0.0916, 0.6355, 405) == pytest.approx(0.7759, abs=5e-5)
    assert power_at(1.2891, 0.0916, 0.6355, 405) == pytest.approx(0.6970, abs=5e-5)


def test_the_customer_failed_twice_by_what_is_published(full: Dataset, correlated: Dataset) -> None:
    _contacts, treated, _control = _worlds(full, correlated)
    table = pair_failures(treated).set_index("world")
    assert int(table.loc["independent", "pairs"]) == 5234
    assert int(table.loc["correlated", "pairs"]) == 5234
    assert float(table.loc["independent", "failure_rate"]) == pytest.approx(0.3632, abs=5e-5)
    assert float(table.loc["correlated", "failure_rate"]) == pytest.approx(0.3629, abs=5e-5)
    first = float(table.loc["independent", "both_failed"])
    second = float(table.loc["correlated", "both_failed"])
    assert first == pytest.approx(0.1219, abs=5e-5)
    assert second == pytest.approx(0.1406, abs=5e-5)
    assert float(table.loc["independent", "expected_if_independent"]) == pytest.approx(
        0.1319, abs=5e-5
    )
    assert float(table.loc["correlated", "expected_if_independent"]) == pytest.approx(
        0.1317, abs=5e-5
    )
    assert float(table.loc["independent", "ratio"]) == pytest.approx(0.9240, abs=5e-5)
    assert float(table.loc["correlated", "ratio"]) == pytest.approx(1.0677, abs=5e-5)
    assert second / first - 1.0 == pytest.approx(0.154, abs=5e-4)
    assert (second - first) * 5234 == pytest.approx(98.0, abs=0.5)
    ratios = float(table.loc["correlated", "ratio"]) / float(table.loc["independent", "ratio"])
    assert ratios - 1.0 == pytest.approx(0.155, abs=5e-4)


def test_the_three_standard_errors_are_what_is_published(
    full: Dataset, correlated: Dataset
) -> None:
    _contacts, treated, control = _worlds(full, correlated)
    table = error_table(treated, control).set_index("world")
    assert float(table.loc["independent", "estimate"]) == pytest.approx(-0.2955, abs=5e-5)
    assert float(table.loc["correlated", "estimate"]) == pytest.approx(-0.2956, abs=5e-5)
    published = {
        "independent": (0.003889, 0.004406, 0.003853, 1.1330, 0.9908),
        "correlated": (0.003886, 0.004427, 0.003929, 1.1392, 1.0113),
    }
    for world, (naive, cluster, corrected, cluster_ratio, corrected_ratio) in published.items():
        row = table.loc[world]
        assert float(row["naive_se"]) == pytest.approx(naive, abs=5e-7), world
        assert float(row["cluster_mean_se"]) == pytest.approx(cluster, abs=5e-7), world
        assert float(row["corrected_se"]) == pytest.approx(corrected, abs=5e-7), world
        assert float(row["cluster_mean_ratio"]) == pytest.approx(cluster_ratio, abs=5e-5), world
        assert float(row["corrected_ratio"]) == pytest.approx(corrected_ratio, abs=5e-5), world
    loss = float(table.loc["independent", "cluster_mean_ratio"]) - 1.0
    gain = float(table.loc["correlated", "corrected_ratio"]) - 1.0
    assert loss / gain == pytest.approx(11.8, abs=0.5)


# --- svclab.concentration -----------------------------------------------------------------------


def _regrouped(full: Dataset) -> tuple[dict[str, pd.DataFrame], ...]:
    """The two worlds wave 5 compares, and the two arms of each."""
    worlds = {
        "equal rates": correlated_dataset(concentrated_dataset(full, EQUAL_RATES)).contacts,
        "concentrated": correlated_dataset(concentrated_dataset(full)).contacts,
    }
    treated = {name: table[~table["holdout"]] for name, table in worlds.items()}
    outcomes = {name: run(table, THREE_TURNS) for name, table in treated.items()}
    control = {name: run(table[table["holdout"]], HUMAN_ONLY) for name, table in worlds.items()}
    return treated, outcomes, control


def test_the_shape_of_the_regrouped_account_is_what_is_published(full: Dataset) -> None:
    published = {
        "equal rates": (13087, 2.4300, 3.2272, 0.3039, 2643, 0.2020, 0.3875, 0.0004),
        "concentrated": (10640, 2.9889, 5.7454, 0.4195, 2885, 0.2711, 0.5809, 0.1595),
    }
    treated, _outcomes, _control = _regrouped(full)
    table = concentration_table(treated).set_index("world")
    for world, figures in published.items():
        customers, mean, effective, inequality, users, share, volume, correlation = figures
        row = table.loc[world]
        assert int(row["customers"]) == customers, world
        assert int(row["contacts"]) == 31802, world
        assert float(row["mean_cluster_size"]) == pytest.approx(mean, abs=5e-5), world
        assert float(row["effective_cluster_size"]) == pytest.approx(effective, abs=5e-5), world
        assert float(row["gini"]) == pytest.approx(inequality, abs=5e-5), world
        assert int(row["heavy_customers"]) == users, world
        assert float(row["heavy_share_of_customers"]) == pytest.approx(share, abs=5e-5), world
        assert float(row["heavy_share_of_volume"]) == pytest.approx(volume, abs=5e-5), world
        assert float(row["frequency_difficulty_correlation"]) == pytest.approx(
            correlation, abs=5e-5
        ), world
    assert float(table.loc["concentrated", "effective_cluster_size"]) / float(
        table.loc["equal rates", "effective_cluster_size"]
    ) - 1.0 == pytest.approx(0.78, abs=5e-3)
    assert float(table.loc["concentrated", "mean_cluster_size"]) / float(
        table.loc["equal rates", "mean_cluster_size"]
    ) - 1.0 == pytest.approx(0.23, abs=5e-3)


def test_the_design_effect_of_the_concentrated_world_is_what_is_published(full: Dataset) -> None:
    published = {
        "equal rates": (0.0417, 2.4300, 3.2272, 1.0928, 1.0596, 0.0608),
        "concentrated": (0.0473, 2.9889, 5.7454, 1.2246, 1.0941, 0.0765),
    }
    _treated, outcomes, _control = _regrouped(full)
    table = design_table(outcomes).set_index("world")
    for world, (icc, mean, effective, effect, at_mean, alpha) in published.items():
        row = table.loc[world]
        assert float(row["icc"]) == pytest.approx(icc, abs=5e-5), world
        assert float(row["mean_cluster_size"]) == pytest.approx(mean, abs=5e-5), world
        assert float(row["effective_cluster_size"]) == pytest.approx(effective, abs=5e-5), world
        assert float(row["design_effect"]) == pytest.approx(effect, abs=5e-5), world
        assert float(row["design_effect_at_mean"]) == pytest.approx(at_mean, abs=5e-5), world
        assert float(row["actual_alpha"]) == pytest.approx(alpha, abs=5e-5), world
    measured = float(table.loc["concentrated", "design_effect"])
    assert measured / 1.2891 == pytest.approx(0.95, abs=5e-3)
    assert float(table.loc["concentrated", "sample_inflation"]) == pytest.approx(0.2246, abs=5e-5)
    at_mean = float(table.loc["concentrated", "design_effect_at_mean"]) - 1.0
    assert at_mean == pytest.approx(0.0941, abs=5e-5)


def test_who_pays_for_the_regrouping_is_what_is_published(full: Dataset) -> None:
    published = {
        "equal rates": (0.3352, 0.6358, 2643, 0.3875, 0.3897, 0.3901, 794),
        "concentrated": (0.3684, 0.6205, 2885, 0.5809, 0.5987, 0.6120, 1305),
    }
    treated, outcomes, _control = _regrouped(full)
    table = burden_table(treated, outcomes).set_index("world")
    for world, figures in published.items():
        difficulty, resolution, users, volume, unresolved, hours, repeats = figures
        row = table.loc[world]
        assert float(row["difficulty_per_contact"]) == pytest.approx(difficulty, abs=5e-5), world
        assert float(row["resolution_rate"]) == pytest.approx(resolution, abs=5e-5), world
        assert int(row["heavy_customers"]) == users, world
        assert float(row["heavy_volume"]) == pytest.approx(volume, abs=5e-5), world
        assert float(row["heavy_unresolved"]) == pytest.approx(unresolved, abs=5e-5), world
        assert float(row["heavy_human_hours"]) == pytest.approx(hours, abs=5e-5), world
        assert int(row["customers_failed_three_times"]) == repeats, world
    control, heavy = table.loc["equal rates"], table.loc["concentrated"]
    # The separation between volume and hours is the finding, and it is a control case in the row
    # above: with no link between rate and difficulty the two shares are the same number.
    assert float(control["heavy_human_hours"]) - float(control["heavy_volume"]) == pytest.approx(
        0.003, abs=5e-4
    )
    assert float(heavy["heavy_human_hours"]) - float(heavy["heavy_volume"]) == pytest.approx(
        0.031, abs=5e-4
    )
    points = float(control["resolution_rate"]) - float(heavy["resolution_rate"])
    assert points * 100.0 == pytest.approx(1.53, abs=5e-3)
    assert float(heavy["difficulty_per_contact"]) / float(
        control["difficulty_per_contact"]
    ) - 1.0 == pytest.approx(0.099, abs=5e-4)
    assert int(heavy["customers_failed_three_times"]) / int(
        control["customers_failed_three_times"]
    ) - 1.0 == pytest.approx(0.64, abs=5e-3)


def test_the_precision_of_the_business_cases_estimate_is_what_is_published(full: Dataset) -> None:
    published = {
        "equal rates": (13087, 1.5484, 0.0381, 0.0246, 0.1495),
        "concentrated": (10640, 1.7845, 0.0730, 0.0409, 0.2862),
    }
    _treated, outcomes, control = _regrouped(full)
    table = precision_table(outcomes, control).set_index("world")
    for world, (customers, deflected, error, relative, width) in published.items():
        row = table.loc[world]
        assert int(row["customers"]) == customers, world
        assert float(row["deflected_per_customer"]) == pytest.approx(deflected, abs=5e-5), world
        assert float(row["standard_error"]) == pytest.approx(error, abs=5e-5), world
        assert float(row["relative_error"]) == pytest.approx(relative, abs=5e-5), world
        assert float(row["interval_width"]) == pytest.approx(width, abs=5e-5), world
    assert float(table.loc["concentrated", "relative_error"]) / float(
        table.loc["equal rates", "relative_error"]
    ) - 1.0 == pytest.approx(0.66, abs=5e-3)
    assert float(table.loc["concentrated", "interval_width"]) / float(
        table.loc["equal rates", "interval_width"]
    ) - 1.0 == pytest.approx(0.91, abs=5e-3)


# --- The example -------------------------------------------------------------------------------


@pytest.mark.parametrize("script", sorted(path.name for path in (ROOT / "examples").glob("*.py")))
def test_the_example_runs(script: str) -> None:
    """An example that does not run is documentation that is already wrong."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "examples" / script)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert result.stdout.strip()


# --- svclab.quality ----------------------------------------------------------------------------


@pytest.fixture(scope="module")
def graded(full: Dataset) -> tuple:
    """The two arms' sessions pooled, and every reading of them."""
    treated = full.contacts[~full.contacts["holdout"]]
    held = full.contacts[full.contacts["holdout"]]
    bot = latent_quality(run(treated, THREE_TURNS), full.contacts)
    control = latent_quality(run(held, HUMAN_ONLY), full.contacts)
    everything = pd.concat([bot, control], ignore_index=True)
    panel = panel_verdicts(everything, full.panel_noise)
    judged = judge_verdicts(everything, full.judge_noise)
    return bot, control, everything, panel, judged


def test_the_gauge_study_is_the_size_the_readme_quotes(graded: tuple, full: Dataset) -> None:
    _, _, _, panel, judged = graded
    assert QUALITY.sample == 1_200
    assert QUALITY.replicates == 2
    assert full.panel_noise["contact"].nunique() == 1_200
    assert panel["session"].nunique() == 1_434
    assert len(panel) == 8_604
    assert len(judged) == 47_019


def test_the_panel_agreement_table_is_what_is_published(graded: tuple) -> None:
    _, _, everything, panel, _ = graded
    published = {
        "avaliador-1": (2_868, 0.5683, 0.8298, 0.6533, 0.8675, 0.9252, 0.8069, 0.7320),
        "avaliador-2": (2_868, 0.3815, 0.8117, 0.6010, 0.8417, 0.7177, 0.9721, 0.6898),
        "avaliador-3": (2_868, 0.4829, 0.7664, 0.5322, 0.8302, 0.8054, 0.8562, 0.6617),
    }
    table = agreement_table(panel, everything).set_index("assessor")
    for grader, values in published.items():
        readings, rate, repeat, repeat_kappa, truth, sens, spec, index = values
        row = table.loc[grader]
        assert int(row["readings"]) == readings, grader
        assert float(row["pass_rate"]) == pytest.approx(rate, abs=5e-5), grader
        assert float(row["repeatability"]) == pytest.approx(repeat, abs=5e-5), grader
        assert float(row["repeatability_kappa"]) == pytest.approx(repeat_kappa, abs=5e-5), grader
        assert float(row["agreement_with_truth"]) == pytest.approx(truth, abs=5e-5), grader
        assert float(row["sensitivity"]) == pytest.approx(sens, abs=5e-5), grader
        assert float(row["specificity"]) == pytest.approx(spec, abs=5e-5), grader
        assert float(row["youden"]) == pytest.approx(index, abs=5e-5), grader

    # The derived claims the prose makes about that table.
    rates = table["pass_rate"]
    assert float(rates.max()) / float(rates.min()) == pytest.approx(1.49, abs=5e-3)
    assert (1.0 - float(table["repeatability"].max())) == pytest.approx(0.170, abs=5e-4)
    assert (1.0 - float(table["repeatability"].min())) == pytest.approx(0.234, abs=5e-4)
    assert (1.0 - float(table.loc["avaliador-1", "specificity"])) == pytest.approx(0.1931, abs=5e-5)
    assert (1.0 - float(table.loc["avaliador-2", "specificity"])) == pytest.approx(0.0279, abs=5e-5)


def test_the_reproducibility_table_is_what_is_published(graded: tuple) -> None:
    _, _, _, panel, _ = graded
    published = {
        "avaliador-1 vs avaliador-2": (1_434, 0.7615, 0.5355),
        "avaliador-1 vs avaliador-3": (1_434, 0.7824, 0.5668),
        "avaliador-2 vs avaliador-3": (1_434, 0.7741, 0.5440),
    }
    table = reproducibility(panel).set_index("pair")
    for pair, (sessions, agreement, measure) in published.items():
        row = table.loc[pair]
        assert int(row["sessions"]) == sessions, pair
        assert float(row["agreement"]) == pytest.approx(agreement, abs=5e-5), pair
        assert float(row["kappa"]) == pytest.approx(measure, abs=5e-5), pair
    # Every pair agrees far more than kappa credits, which is the point of printing both.
    assert (table["agreement"] > table["kappa"] + 0.20).all()


def test_the_attenuation_figures_are_what_is_published(graded: tuple) -> None:
    """The wave's centrepiece: the panel reports 69.45% of the real difference, exactly."""
    bot, control, everything, panel, _ = graded
    table = agreement_table(panel, everything)
    control_rate = float(control["acceptable"].mean())
    bot_rate = float(bot["acceptable"].mean())
    sensitivity = float(table["sensitivity"].mean())
    specificity = float(table["specificity"].mean())

    assert control_rate == pytest.approx(0.959616, abs=5e-7)
    assert bot_rate == pytest.approx(0.413712, abs=5e-7)
    assert control_rate - bot_rate == pytest.approx(0.545904, abs=5e-7)
    assert sensitivity == pytest.approx(0.8161, abs=5e-5)
    assert specificity == pytest.approx(0.8784, abs=5e-5)

    measured = attenuation(control_rate, bot_rate, sensitivity, specificity)
    assert measured["factor"] == pytest.approx(0.694497, abs=5e-7)
    assert measured["observed_difference"] == pytest.approx(0.379129, abs=5e-7)
    assert measured["first_observed"] == pytest.approx(0.788053, abs=5e-7)
    assert measured["second_observed"] == pytest.approx(0.408925, abs=5e-7)
    # And the identity itself, which is what makes the figure above a consequence rather than a
    # coincidence.
    assert measured["observed_difference"] == pytest.approx(
        measured["true_difference"] * measured["factor"], abs=1e-14
    )


def test_the_sample_size_inflation_is_what_is_published(graded: tuple) -> None:
    bot, control, everything, panel, _ = graded
    table = agreement_table(panel, everything)
    control_rate = float(control["acceptable"].mean())
    bot_rate = float(bot["acceptable"].mean())
    sensitivity = float(table["sensitivity"].mean())
    specificity = float(table["specificity"].mean())

    perfect = sessions_for_difference(control_rate, bot_rate)
    actual = sessions_for_difference(control_rate, bot_rate, sensitivity, specificity)
    assert perfect == pytest.approx(10.07, abs=5e-3)
    assert actual == pytest.approx(25.03, abs=5e-3)
    assert actual / perfect == pytest.approx(2.4864, abs=5e-5)
    square_law = 1.0 / youden(sensitivity, specificity) ** 2
    assert square_law == pytest.approx(2.0733, abs=5e-5)
    # The claim the document makes about the two: the rule of thumb understates the bill.
    assert actual / perfect > square_law


def test_the_judge_figures_are_what_is_published(graded: tuple) -> None:
    _, _, everything, panel, judged = graded
    row = agreement_table(judged, everything).iloc[0]
    assert row["assessor"] == "juiz-automatico"
    assert float(row["agreement_with_truth"]) == pytest.approx(0.8850, abs=5e-5)
    assert float(row["sensitivity"]) == pytest.approx(0.9937, abs=5e-5)
    assert float(row["specificity"]) == pytest.approx(0.7705, abs=5e-5)
    assert float(row["youden"]) == pytest.approx(0.7642, abs=5e-5)
    assert math.isnan(float(row["repeatability"]))

    panel_table = agreement_table(panel, everything)
    assert float(row["agreement_with_truth"]) > float(panel_table["agreement_with_truth"].max())
    assert float(row["youden"]) > float(panel_table["youden"].max())


def test_what_the_judge_would_be_validated_against_is_what_is_published(graded: tuple) -> None:
    """Result 5: the same judge scores 0.5450 to 0.7121 depending on whose week it was."""
    _, _, everything, panel, judged = graded
    first = panel[panel["replicate"] == 1]
    published = {
        "avaliador-1": (0.8598, 0.7121),
        "avaliador-2": (0.7608, 0.5450),
        "avaliador-3": (0.8082, 0.6198),
    }
    measured = {}
    for grader, frame in first.groupby("assessor"):
        merged = frame.merge(judged[["session", "verdict"]], on="session", suffixes=("_p", "_j"))
        agreement = float(np.mean(merged["verdict_p"] == merged["verdict_j"]))
        measure = kappa(merged["verdict_p"], merged["verdict_j"])
        measured[grader] = measure
        assert agreement == pytest.approx(published[grader][0], abs=5e-5), grader
        assert measure == pytest.approx(published[grader][1], abs=5e-5), grader
    assert max(measured.values()) - min(measured.values()) == pytest.approx(0.1671, abs=5e-5)

    majority = first.groupby("session")["verdict"].mean() >= 0.5
    sample = majority.index
    judge_sample = judged.set_index("session").reindex(sample)["verdict"].to_numpy(dtype=bool)
    truth = everything.set_index("session").reindex(sample)["acceptable"].to_numpy(dtype=bool)
    votes = majority.to_numpy(dtype=bool)

    assert float(np.mean(judge_sample == votes)) == pytest.approx(0.8466, abs=5e-5)
    assert kappa(judge_sample, votes) == pytest.approx(0.6948, abs=5e-5)
    assert float(np.mean(judge_sample == truth)) == pytest.approx(0.8919, abs=5e-5)
    assert kappa(judge_sample, truth) == pytest.approx(0.7826, abs=5e-5)
    assert float(np.mean(votes == truth)) == pytest.approx(0.8989, abs=5e-5)
    assert kappa(votes, truth) == pytest.approx(0.7979, abs=5e-5)
    # The two claims the document ends on, as orderings.
    assert kappa(judge_sample, truth) > kappa(judge_sample, votes)
    assert kappa(votes, truth) > kappa(judge_sample, truth)


# --- Wave 3, front one: svclab.routing ---------------------------------------------------------


WAVE_THREE_GRID = tuple(round(value, 2) for value in np.arange(0.0, 1.01, 0.02))


def wave_three_price(
    contacts: pd.DataFrame, scores: pd.DataFrame, rule: float | dict[str, float]
) -> tuple[float, float, float, float]:
    """Seconds per contact, resolution, misroutes and deferrals under one routing rule."""
    routed = defer_below(contacts, scores, rule)
    outcomes = run(routed, THREE_TURNS)
    measured = cost_of(outcomes, routed)
    total = measured["human_seconds"] + measured["misroute_seconds"] + measured["defer_seconds"]
    first = outcomes[~outcomes["is_repeat"]]
    return (
        total / len(routed),
        float(first["resolved"].mean()),
        measured["misroutes"],
        measured["deferred"],
    )


def test_the_score_separates_correct_labels_by_what_is_published(full: Dataset) -> None:
    treated = full.contacts[~full.contacts["holdout"]]
    routed = defer_below(treated, full.routing_scores, 0.0)
    outcomes = run(routed, THREE_TURNS)
    first = outcomes[~outcomes["is_repeat"]].set_index("contact")
    correct = first["classified_correctly"].reindex(routed["contact"]).to_numpy(dtype=bool)
    score = routed["classifier_score"].to_numpy(dtype=float)
    assert float(score[correct].mean()) == pytest.approx(0.6975, abs=5e-5)
    assert float(score[~correct].mean()) == pytest.approx(0.4293, abs=5e-5)
    assert float(correct.mean()) == pytest.approx(0.7771, abs=5e-5)
    above = score > 0.7
    assert float(correct[above].mean()) == pytest.approx(0.9907, abs=5e-5)


def test_the_two_routing_objectives_disagree_by_what_is_published(full: Dataset) -> None:
    treated = full.contacts[~full.contacts["holdout"]]
    thresholds = tuple(round(value, 2) for value in np.arange(0.30, 0.71, 0.01))
    curve = cost_curve(treated, full.routing_scores, THREE_TURNS, thresholds)
    accuracy = best_by(curve, "label_accuracy", True)
    cost = best_by(curve, "seconds_per_contact", False)
    assert accuracy == pytest.approx(0.45, abs=5e-3)
    assert cost == pytest.approx(0.48, abs=5e-3)
    indexed = curve.set_index("threshold")
    at_accuracy = float(indexed.loc[accuracy, "seconds_per_contact"])
    at_cost = float(indexed.loc[cost, "seconds_per_contact"])
    assert at_accuracy == pytest.approx(346.4851, abs=5e-4)
    assert at_cost == pytest.approx(345.6345, abs=5e-4)
    assert at_accuracy - at_cost == pytest.approx(0.8506, abs=5e-4)
    assert (at_accuracy - at_cost) * len(treated) / 3600.0 == pytest.approx(7.51, abs=5e-3)


def test_the_ends_of_the_cost_curve_are_what_is_published(full: Dataset) -> None:
    treated = full.contacts[~full.contacts["holdout"]]
    curve = cost_curve(treated, full.routing_scores, THREE_TURNS, (0.0, 0.95)).set_index(
        "threshold"
    )
    assert int(curve.loc[0.0, "misroutes"]) == 7_090
    assert float(curve.loc[0.0, "misroute_seconds"]) == pytest.approx(1_812_030.0, abs=0.5)
    assert int(curve.loc[0.95, "misroutes"]) == 0
    assert float(curve.loc[0.95, "defer_seconds"]) == pytest.approx(600_720.0, abs=0.5)


def test_the_per_intent_thresholds_are_what_is_published(full: Dataset) -> None:
    published = {
        "rastreio": (60.0, 0.10, 0.6667),
        "prazo-de-entrega": (90.0, 0.28, 0.7778),
        "cadastro": (150.0, 0.38, 0.8667),
        "reembolso": (420.0, 0.60, 0.9524),
        "reclamacao": (540.0, 0.62, 0.9630),
    }
    treated = full.contacts[~full.contacts["holdout"]]
    for intent, (seconds, swept, formula) in published.items():
        assert ROUTING.misroute_seconds[intent] == seconds, intent
        assert calibrated_threshold(ROUTING.defer_seconds, seconds) == pytest.approx(
            formula, abs=5e-5
        ), intent
        subset = treated[treated["intent"] == intent]
        costs = {
            candidate: wave_three_price(subset, full.routing_scores, candidate)[0]
            for candidate in WAVE_THREE_GRID
        }
        assert min(costs, key=lambda key: costs[key]) == pytest.approx(swept, abs=5e-3), intent


def test_the_three_routing_rules_are_what_is_published(full: Dataset) -> None:
    """Including the one that corrected this wave's first draft."""
    treated = full.contacts[~full.contacts["holdout"]]
    swept = {
        "rastreio": 0.10,
        "prazo-de-entrega": 0.28,
        "cadastro": 0.38,
        "reembolso": 0.60,
        "reclamacao": 0.62,
    }
    formula = {
        intent: calibrated_threshold(ROUTING.defer_seconds, seconds)
        for intent, seconds in ROUTING.misroute_seconds.items()
    }
    published = {
        "single": (0.48, 345.6345, 0.7067, 2_472, 7_036),
        "swept": (swept, 334.0793, 0.6925, 3_754, 5_525),
        "formula": (formula, 388.8874, 0.8611, 58, 23_304),
    }
    measured = {}
    for label, (rule, seconds, resolution, misroutes, deferred) in published.items():
        cost, resolved, missed, deferred_count = wave_three_price(
            treated, full.routing_scores, rule
        )
        assert cost == pytest.approx(seconds, abs=5e-4), label
        assert resolved == pytest.approx(resolution, abs=5e-5), label
        assert int(missed) == misroutes, label
        assert int(deferred_count) == deferred, label
        measured[label] = cost

    saved = measured["single"] - measured["swept"]
    assert saved == pytest.approx(11.5552, abs=5e-4)
    assert saved * len(treated) / 3600.0 == pytest.approx(102.1, abs=5e-2)
    assert measured["formula"] / measured["single"] - 1.0 == pytest.approx(0.125, abs=5e-4)


# --- Wave 3, front two: impatience in svclab.capacity ------------------------------------------


WAVE_THREE_LOAD = 7.5845
WAVE_THREE_HANDLING = 512.25
WAVE_THREE_PATIENCE = 240.0


def test_the_impatience_table_is_what_is_published() -> None:
    published = {
        5: (0.3891, 0.9267, False),
        6: (0.2923, 0.8945, False),
        7: (0.2100, 0.8560, False),
        8: (0.1434, 0.8121, True),
        10: (0.0565, 0.7156, True),
        11: (0.0324, 0.6672, True),
        14: (0.0042, 0.5395, True),
    }
    table = impatience_table(
        tuple(published), WAVE_THREE_LOAD, WAVE_THREE_PATIENCE, WAVE_THREE_HANDLING, 20.0
    ).set_index("agents")
    for agents, (leaving, busy, stable) in published.items():
        row = table.loc[agents]
        assert float(row["abandonment"]) == pytest.approx(leaving, abs=5e-5), agents
        assert float(row["occupancy"]) == pytest.approx(busy, abs=5e-5), agents
        assert bool(row["erlang_c_stable"]) is stable, agents
    # The service levels Erlang C reports where it has an answer at all.
    assert float(table.loc[8, "erlang_c_service_level"]) == pytest.approx(0.1751, abs=5e-5)
    assert float(table.loc[11, "erlang_c_service_level"]) == pytest.approx(0.8368, abs=5e-5)
    assert float(table.loc[14, "erlang_c_service_level"]) == pytest.approx(0.9794, abs=5e-5)


def test_the_repeat_fixed_point_is_what_is_published() -> None:
    published = {
        6: (9.1886, 1.6041, 0.3845, 20),
        8: (8.3478, 0.7633, 0.1830, 19),
        11: (7.7328, 0.1483, 0.0356, 12),
    }
    for agents, (settled, added, leaving, steps) in published.items():
        measured = load_with_repeats(
            agents, WAVE_THREE_LOAD, WAVE_THREE_PATIENCE, WAVE_THREE_HANDLING, 0.55
        )
        assert measured["settled_load"] == pytest.approx(settled, abs=5e-5), agents
        assert measured["added_load"] == pytest.approx(added, abs=5e-5), agents
        assert measured["abandonment"] == pytest.approx(leaving, abs=5e-5), agents
        assert int(measured["iterations"]) == steps, agents
    six = load_with_repeats(6, WAVE_THREE_LOAD, WAVE_THREE_PATIENCE, WAVE_THREE_HANDLING, 0.55)
    eleven = load_with_repeats(11, WAVE_THREE_LOAD, WAVE_THREE_PATIENCE, WAVE_THREE_HANDLING, 0.55)
    assert six["settled_load"] / WAVE_THREE_LOAD - 1.0 == pytest.approx(0.211, abs=5e-4)
    assert eleven["settled_load"] / WAVE_THREE_LOAD - 1.0 == pytest.approx(0.020, abs=5e-4)


# --- Wave 3, front three: svclab.experiment ----------------------------------------------------


def test_the_clustering_of_this_account_is_what_is_published(full: Dataset) -> None:
    treated = full.contacts[~full.contacts["holdout"]]
    outcomes = run(treated, THREE_TURNS)
    first = outcomes[~outcomes["is_repeat"]].copy()
    first["resolved_num"] = first["resolved"].astype(float)
    first["human_num"] = first["handled_by_human"].astype(float)
    assert len(first) == 31_802
    assert first["customer"].nunique() == 16_195
    size = len(first) / first["customer"].nunique()
    assert size == pytest.approx(1.9637, abs=5e-5)
    assert intracluster_correlation(first, "customer", "resolved_num") == pytest.approx(
        -0.012563, abs=5e-7
    )
    assert intracluster_correlation(first, "customer", "human_num") == pytest.approx(
        0.000876, abs=5e-7
    )


def test_the_sizing_table_is_what_is_published(full: Dataset) -> None:
    published = {
        "independent contacts": (0.00, 1.0000, 405.3562, 206.4255, 0.0500),
        "correlation 0.05": (0.05, 1.0482, 424.8882, 216.3721, 0.0556),
        "correlation 0.10": (0.10, 1.0964, 444.4201, 226.3186, 0.0612),
        "correlation 0.20": (0.20, 1.1927, 483.4840, 246.2117, 0.0727),
        "correlation 0.30": (0.30, 1.2891, 522.5479, 266.1047, 0.0843),
        "total correlation": (1.00, 1.9637, 795.9950, 405.3562, 0.1619),
    }
    treated = full.contacts[~full.contacts["holdout"]]
    three = run(treated, THREE_TURNS)
    guarded = run(treated, GUARDED)
    first = three[~three["is_repeat"]]
    size = len(first) / first["customer"].nunique()
    guarded_rate = float(guarded[~guarded["is_repeat"]]["resolved"].mean())
    three_rate = float(first["resolved"].mean())
    assert guarded_rate == pytest.approx(0.7271, abs=5e-5)
    assert three_rate == pytest.approx(0.6355, abs=5e-5)

    scenarios = {name: (size, icc) for name, (icc, *_rest) in published.items()}
    table = sizing_table(scenarios, guarded_rate, three_rate, size).set_index("scenario")
    for name, (_icc, effect, contacts, customers, alpha) in published.items():
        row = table.loc[name]
        assert float(row["design_effect"]) == pytest.approx(effect, abs=5e-5), name
        assert float(row["contacts_per_arm"]) == pytest.approx(contacts, abs=5e-4), name
        assert float(row["customers_per_arm"]) == pytest.approx(customers, abs=5e-4), name
        assert float(row["actual_alpha"]) == pytest.approx(alpha, abs=5e-5), name
    heavy = table.loc["correlation 0.30"]
    plain = table.loc["independent contacts"]
    assert float(heavy["contacts_per_arm"]) / float(plain["contacts_per_arm"]) - 1.0 == (
        pytest.approx(0.289, abs=5e-4)
    )

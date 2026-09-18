"""Every figure quoted in a README, re-derived.

Marked slow because they build the full dataset, run every policy against it and execute the example
script. The point is not coverage: it is that a change which moves a published number breaks the build
instead of leaving the text quietly wrong.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from svclab.bot import GUARDED, HUMAN_ONLY, PATIENT, POLICIES, THREE_TURNS, run
from svclab.capacity import agents_for, capacity_table, erlang_b, erlang_c, occupancy, service_level
from svclab.containment import containment_table, deflection, selection_profile
from svclab.synth import CENTRE, Dataset

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

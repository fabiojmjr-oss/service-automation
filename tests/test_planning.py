"""Staffing to constraints, and the controls that keep the search honest.

The load-bearing tests here are the monotonicity ones. Everything in this module rests on more agents
being weakly better on all three measures, because that is what makes an upward search correct: if it
is ever false, the smallest satisfying headcount is not the one the search returns.
"""

from __future__ import annotations

import math

import pytest

from svclab.planning import (
    CONSTRAINT_NAMES,
    PLAN_COLUMNS,
    SCALE_COLUMNS,
    Constraints,
    agents_at_ceiling,
    agents_for_constraints,
    binding_constraint,
    headroom,
    metrics_at,
    plan_table,
    scale_table,
    unmet,
)

LOAD = 7.5845
HANDLING = 512.25
PATIENCE = 240.0
ALL_THREE = Constraints(service_level=0.80, max_occupancy=0.85, max_abandonment=0.05)


class TestWhatAPlanHasToDeclare:
    def test_a_plan_with_no_constraint_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no constraint is not a plan"):
            Constraints()

    def test_a_ceiling_outside_the_unit_interval_is_refused(self) -> None:
        for kwargs in ({"service_level": 1.0}, {"max_occupancy": 0.0}, {"max_abandonment": 1.5}):
            with pytest.raises(ValueError, match="between zero and one"):
                Constraints(**kwargs)

    def test_a_negative_target_wait_is_refused(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            Constraints(service_level=0.8, target_seconds=-1.0)

    def test_the_three_names_are_the_ones_the_tables_use(self) -> None:
        impossible = Constraints(service_level=0.99, max_occupancy=0.01, max_abandonment=0.01)
        assert set(unmet(1, LOAD, HANDLING, PATIENCE, impossible)) <= set(CONSTRAINT_NAMES)
        assert set(headroom(11, LOAD, HANDLING, PATIENCE, impossible)) == set(CONSTRAINT_NAMES)


class TestTheThreeMeasures:
    def test_more_agents_are_weakly_better_on_all_three(self) -> None:
        """The property the upward search depends on, over the whole range it searches."""
        levels = [metrics_at(agents, LOAD, HANDLING, PATIENCE, 20.0) for agents in range(1, 40)]
        for earlier, later in zip(levels, levels[1:], strict=False):
            assert later["service_level"] >= earlier["service_level"] - 1e-12
            assert later["abandonment"] <= earlier["abandonment"] + 1e-12
            assert later["occupancy"] <= earlier["occupancy"] + 1e-12

    def test_occupancy_is_measured_on_the_work_that_was_answered(self) -> None:
        """A customer who abandons occupies nobody, so the effective load is the numerator."""
        measured = metrics_at(8, LOAD, HANDLING, PATIENCE, 20.0)
        assert measured["effective_load"] == pytest.approx(
            LOAD * (1.0 - measured["abandonment"]), abs=1e-12
        )
        assert measured["occupancy"] == pytest.approx(measured["effective_load"] / 8, abs=1e-12)
        assert measured["occupancy"] < LOAD / 8

    def test_an_empty_queue_is_refused(self) -> None:
        with pytest.raises(ValueError, match="at least one agent"):
            metrics_at(0, LOAD, HANDLING, PATIENCE, 20.0)


class TestTheSearch:
    def test_the_answer_satisfies_the_constraints_and_one_fewer_does_not(self) -> None:
        """The definition of a smallest satisfying headcount, asserted as its definition."""
        agents = agents_for_constraints(LOAD, HANDLING, PATIENCE, ALL_THREE)
        assert not unmet(agents, LOAD, HANDLING, PATIENCE, ALL_THREE)
        assert unmet(agents - 1, LOAD, HANDLING, PATIENCE, ALL_THREE)

    def test_adding_a_constraint_never_reduces_the_headcount(self) -> None:
        one = Constraints(service_level=0.80)
        two = Constraints(service_level=0.80, max_occupancy=0.85)
        counts = [
            agents_for_constraints(LOAD, HANDLING, PATIENCE, plan) for plan in (one, two, ALL_THREE)
        ]
        assert counts == sorted(counts)

    def test_a_constraint_nothing_can_buy_is_refused_rather_than_approximated(self) -> None:
        with pytest.raises(ValueError, match="no staffing level up to"):
            agents_for_constraints(
                LOAD, HANDLING, PATIENCE, Constraints(max_occupancy=0.01), ceiling=20
            )

    def test_the_binding_constraint_is_what_one_fewer_agent_fails(self) -> None:
        agents = agents_for_constraints(LOAD, HANDLING, PATIENCE, ALL_THREE)
        named = binding_constraint(agents, LOAD, HANDLING, PATIENCE, ALL_THREE)
        failing = unmet(agents - 1, LOAD, HANDLING, PATIENCE, ALL_THREE)
        assert named == " + ".join(failing)

    def test_a_single_agent_has_nothing_below_it_to_test(self) -> None:
        plan = Constraints(service_level=0.5)
        assert binding_constraint(1, 0.1, HANDLING, PATIENCE, plan) == "minimum"

    def test_a_headcount_above_the_answer_binds_nothing(self) -> None:
        plan = Constraints(service_level=0.80)
        agents = agents_for_constraints(LOAD, HANDLING, PATIENCE, plan)
        assert binding_constraint(agents + 3, LOAD, HANDLING, PATIENCE, plan) == "none"


class TestTheCeilingArithmetic:
    def test_the_ceiling_alone_is_the_load_divided_by_it(self) -> None:
        assert agents_at_ceiling(8.5, 0.85) == 10
        assert agents_at_ceiling(LOAD, 0.85) == math.ceil(LOAD / 0.85)

    def test_a_tiny_load_still_needs_somebody(self) -> None:
        assert agents_at_ceiling(0.01, 0.85) == 1

    def test_an_impossible_ceiling_is_refused(self) -> None:
        with pytest.raises(ValueError, match="between zero and one"):
            agents_at_ceiling(10.0, 1.0)

    def test_the_napkin_understates_what_the_queue_needs(self) -> None:
        """Wave 1's error in a new costume: dividing a load by a ratio is not a queueing model."""
        assert agents_at_ceiling(LOAD, 0.85) < agents_for_constraints(
            LOAD, HANDLING, PATIENCE, ALL_THREE
        )


class TestTheTables:
    def test_the_plan_table_prices_every_plan_and_names_what_decided_it(self) -> None:
        plans = {
            "service level only": Constraints(service_level=0.80),
            "occupancy only": Constraints(max_occupancy=0.85),
            "all three": ALL_THREE,
        }
        table = plan_table(plans, LOAD, HANDLING, PATIENCE).set_index("plan")
        assert list(table.reset_index().columns) == list(PLAN_COLUMNS)
        assert len(table) == len(plans)
        # An occupancy ceiling on its own is satisfied by understaffing: fewer agents, and the
        # customers who give up are what keeps the occupancy down.
        assert int(table.loc["occupancy only", "agents"]) < int(
            table.loc["service level only", "agents"]
        )
        assert float(table.loc["occupancy only", "abandonment"]) > float(
            table.loc["service level only", "abandonment"]
        )
        for name in table.index:
            parts = str(table.loc[name, "binding"]).split(" + ")
            assert all(part in {*CONSTRAINT_NAMES, "minimum", "none"} for part in parts), name

    def test_an_empty_plan_set_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no plans"):
            plan_table({}, LOAD, HANDLING, PATIENCE)

    def test_a_bigger_queue_needs_fewer_agents_per_erlang(self) -> None:
        """Queueing economies of scale, as a monotone property rather than as a figure."""
        table = scale_table((1.0, 5.0, 20.0, 100.0), HANDLING, PATIENCE, ALL_THREE)
        assert list(table.columns) == list(SCALE_COLUMNS)
        ratios = table["agents_per_erlang"].tolist()
        assert ratios == sorted(ratios, reverse=True)

    def test_the_binding_constraint_moves_from_service_level_to_occupancy_with_size(self) -> None:
        table = scale_table((1.0, 100.0), HANDLING, PATIENCE, ALL_THREE).set_index("load")
        assert "service level" in str(table.loc[1.0, "binding"])
        assert table.loc[100.0, "binding"] == "occupancy"

    def test_an_empty_load_set_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no loads"):
            scale_table((), HANDLING, PATIENCE, Constraints(service_level=0.8))


class TestTheHeadroom:
    def test_slack_is_positive_where_a_constraint_is_met_and_negative_where_it_is_not(self) -> None:
        agents = agents_for_constraints(LOAD, HANDLING, PATIENCE, ALL_THREE)
        slack = headroom(agents, LOAD, HANDLING, PATIENCE, ALL_THREE)
        assert all(value >= 0.0 for value in slack.values())
        tight = headroom(agents - 1, LOAD, HANDLING, PATIENCE, ALL_THREE)
        assert any(value < 0.0 for value in tight.values())

    def test_an_undeclared_constraint_has_no_slack_rather_than_infinite_slack(self) -> None:
        slack = headroom(11, LOAD, HANDLING, PATIENCE, Constraints(max_occupancy=0.85))
        assert set(slack) == {"occupancy"}

    def test_every_combination_of_declared_ceilings_reports_exactly_those(self) -> None:
        """Branch coverage asked for this, and it is the right thing to ask: a plan that skips the
        middle ceiling has to skip it in the slack too, not report a zero for it."""
        combinations = {
            ("service level",): Constraints(service_level=0.80),
            ("abandonment",): Constraints(max_abandonment=0.05),
            ("service level", "abandonment"): Constraints(service_level=0.80, max_abandonment=0.05),
            ("occupancy", "abandonment"): Constraints(max_occupancy=0.85, max_abandonment=0.05),
        }
        for names, plan in combinations.items():
            assert set(headroom(11, LOAD, HANDLING, PATIENCE, plan)) == set(names), names

"""Erlang's formulas against their closed forms, and the staffing search against its own definition.

Three controls carry this file. With one agent, Erlang C equals the offered load exactly and Erlang B
equals ``a / (1 + a)`` - both are closed forms, so they check the recursion against algebra rather
than against another implementation. The service level has to be monotone in agents and reach one in
the limit. And the agent count has to be the *smallest* one that clears the target, which is a
property the search can be asked about directly.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from svclab.bot import HUMAN_ONLY, THREE_TURNS, run
from svclab.capacity import (
    CAPACITY_COLUMNS,
    agents_for,
    capacity_table,
    erlang_b,
    erlang_c,
    occupancy,
    offered_load,
    promised_agents,
    service_level,
)
from svclab.containment import containment_table
from svclab.synth import CENTRE, Dataset


class TestTheClosedForms:
    def test_one_agent_makes_erlang_c_equal_the_load(self) -> None:
        """C(1, a) = a exactly, which follows from B(1, a) = a / (1 + a)."""
        for load in (0.1, 0.5, 0.9, 0.99):
            assert erlang_c(1, load) == pytest.approx(load, rel=1e-14)

    def test_one_server_makes_erlang_b_the_textbook_fraction(self) -> None:
        for load in (0.25, 1.0, 2.0, 7.5):
            assert erlang_b(1, load) == pytest.approx(load / (1.0 + load), rel=1e-14)

    def test_no_servers_block_everything(self) -> None:
        assert erlang_b(0, 4.0) == 1.0

    def test_erlang_b_falls_as_servers_are_added(self) -> None:
        values = [erlang_b(agents, 5.0) for agents in range(1, 20)]
        assert values == sorted(values, reverse=True)

    def test_a_load_at_or_above_the_agents_means_everybody_waits(self) -> None:
        assert erlang_c(10, 10.0) == 1.0
        assert erlang_c(10, 11.0) == 1.0
        assert service_level(10, 10.0, 300.0, 20.0) == 0.0

    def test_the_service_level_is_monotone_in_agents_and_reaches_one(self) -> None:
        levels = [service_level(agents, 12.0, 300.0, 20.0) for agents in range(13, 40)]
        assert levels == sorted(levels)
        assert levels[-1] == pytest.approx(1.0, abs=1e-6)

    def test_a_vanishing_load_is_answered_immediately(self) -> None:
        assert service_level(5, 1e-12, 300.0, 20.0) == pytest.approx(1.0, abs=1e-9)

    def test_a_zero_second_target_is_the_probability_of_not_waiting(self) -> None:
        """At a target of zero the service level is 1 - C, which ties the two formulas together."""
        for agents, load in ((5, 3.0), (14, 10.1268), (30, 25.0)):
            assert service_level(agents, load, 300.0, 0.0) == pytest.approx(
                1.0 - erlang_c(agents, load), rel=1e-14
            )


class TestTheStaffingSearch:
    def test_the_answer_is_the_smallest_count_that_clears_the_target(self) -> None:
        load, aht, target, goal = 12.0, 300.0, 20.0, 0.80
        agents = agents_for(load, aht, target, goal)
        assert service_level(agents, load, aht, target) >= goal
        assert service_level(agents - 1, load, aht, target) < goal

    def test_staffing_is_not_linear_in_the_load(self) -> None:
        """The first reason a headcount case is wrong, as a property rather than as a figure."""
        whole = agents_for(20.0, 300.0, 20.0, 0.80)
        half = agents_for(10.0, 300.0, 20.0, 0.80)
        assert half > whole / 2.0

    def test_an_impossible_service_level_is_refused_by_name(self) -> None:
        for goal in (0.0, 1.0, 1.5, -0.2):
            with pytest.raises(ValueError, match="between zero and one"):
                agents_for(5.0, 300.0, 20.0, goal)

    def test_a_ceiling_that_cannot_be_reached_raises_rather_than_returns(self) -> None:
        with pytest.raises(ValueError, match="no agent count up to"):
            agents_for(500.0, 300.0, 20.0, 0.99, ceiling=10)


class TestTheArgumentsAndRefusals:
    def test_a_load_needs_a_period_to_be_a_load(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            offered_load(100.0, 300.0, 0.0)

    def test_negative_work_is_refused(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            offered_load(-1.0, 300.0, 3600.0)
        with pytest.raises(ValueError, match="cannot be negative"):
            erlang_b(-1, 1.0)
        with pytest.raises(ValueError, match="cannot be negative"):
            erlang_b(1, -1.0)

    def test_a_queue_with_no_agents_is_not_a_queue(self) -> None:
        for call in (lambda: erlang_c(0, 1.0), lambda: occupancy(0, 1.0)):
            with pytest.raises(ValueError, match="at least one agent"):
                call()

    def test_the_handling_time_and_target_are_checked(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            service_level(5, 1.0, 0.0, 20.0)
        with pytest.raises(ValueError, match="cannot be negative"):
            service_level(5, 1.0, 300.0, -1.0)

    def test_a_containment_rate_that_is_not_a_share_is_refused(self) -> None:
        for rate in (-0.1, 1.2):
            with pytest.raises(ValueError, match="has to be a share"):
                promised_agents(10, rate)

    def test_occupancy_is_the_load_per_agent(self) -> None:
        assert occupancy(10, 7.5) == pytest.approx(0.75)

    def test_the_promise_is_the_multiplication_it_is_accused_of_being(self) -> None:
        assert promised_agents(14, 0.6065) == pytest.approx(14 * (1 - 0.6065))


class TestTheTableOnTheRealAccount:
    def measured(self, full: Dataset) -> pd.DataFrame:
        treated = full.contacts[~full.contacts["holdout"]]
        outcomes = {
            HUMAN_ONLY.name: run(treated, HUMAN_ONLY),
            THREE_TURNS.name: run(treated, THREE_TURNS),
        }
        containment = (
            containment_table(outcomes).set_index("policy")["session_containment"].to_dict()
        )
        return capacity_table(outcomes, containment, baseline=HUMAN_ONLY.name)

    def test_the_columns_are_the_declared_ones(self, full: Dataset) -> None:
        assert tuple(self.measured(full).columns) == CAPACITY_COLUMNS

    def test_the_baseline_is_promised_exactly_what_it_needs(self, full: Dataset) -> None:
        row = self.measured(full).set_index("policy").loc[HUMAN_ONLY.name]
        assert float(row["agents_missing"]) == pytest.approx(0.0)

    def test_the_bot_needs_more_agents_than_its_containment_rate_promised(
        self, full: Dataset
    ) -> None:
        """The wave's conclusion as a direction. The figures belong in the claims suite."""
        row = self.measured(full).set_index("policy").loc[THREE_TURNS.name]
        assert float(row["agents_missing"]) > 0.0
        assert float(row["agents_needed"]) < 14

    def test_the_residue_is_more_expensive_per_contact_than_the_baseline_was(
        self, full: Dataset
    ) -> None:
        table = self.measured(full).set_index("policy")
        assert float(table.loc[THREE_TURNS.name, "mean_handling_seconds"]) > float(
            table.loc[HUMAN_ONLY.name, "mean_handling_seconds"]
        )

    def test_every_staffed_queue_reaches_the_target_it_was_staffed_for(self, full: Dataset) -> None:
        for _, row in self.measured(full).iterrows():
            assert float(row["service_level"]) >= CENTRE.target_service_level
            assert 0.0 < float(row["occupancy"]) < 1.0

    def test_a_missing_baseline_or_containment_rate_is_an_error(self, full: Dataset) -> None:
        treated = full.contacts[~full.contacts["holdout"]].head(4_000)
        outcomes = {THREE_TURNS.name: run(treated, THREE_TURNS)}
        with pytest.raises(KeyError, match="is not among the policies"):
            capacity_table(outcomes, {THREE_TURNS.name: 0.5}, baseline="nothing")
        with pytest.raises(KeyError, match="no containment rate supplied"):
            capacity_table(outcomes, {}, baseline=THREE_TURNS.name)

    def test_the_gap_decomposes_into_three_named_effects(self, full: Dataset) -> None:
        """Volume, then the harder residue, then the repeats - each adding agents to the promise.

        The document publishes the four agent counts. What belongs here is that the ordering is the
        one the argument claims, because that ordering is the argument.
        """
        treated = full.contacts[~full.contacts["holdout"]]
        period = CENTRE.days * CENTRE.operating_hours_per_day * 3600.0
        baseline = run(treated, HUMAN_ONLY)
        bot = run(treated, THREE_TURNS)
        base_human = baseline[baseline["handled_by_human"]]
        bot_human = bot[bot["handled_by_human"]]
        first = bot_human[~bot_human["is_repeat"]]

        def staffing(sessions: int, seconds: float) -> int:
            load = offered_load(sessions, seconds, period)
            return agents_for(
                load, seconds, CENTRE.target_answer_seconds, CENTRE.target_service_level
            )

        base_seconds = float(base_human["human_seconds"].mean())
        steps = [
            staffing(len(first), base_seconds),
            staffing(len(first), float(first["human_seconds"].mean())),
            staffing(len(bot_human), float(bot_human["human_seconds"].mean())),
        ]
        assert steps == sorted(steps)
        assert steps[-1] > steps[0]
        promised = promised_agents(staffing(len(base_human), base_seconds), 0.6065)
        assert steps[0] > promised
        assert not math.isnan(promised)

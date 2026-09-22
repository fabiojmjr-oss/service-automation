"""The attrition loop, and the controls that keep a fixed point honest.

Two tests here carry the wave. One runs the whole construction with attrition switched off and demands
the payroll equal the agents exactly - if a curve that costs nothing still costs somebody, the loop is
inventing people. The other asserts that more payroll is weakly better, because the upward search for a
payroll is only correct if it is.
"""

from __future__ import annotations

import math

import pytest

from svclab.planning import Constraints, unmet
from svclab.synth import WORKFORCE, WorkforceProfile
from svclab.workforce import (
    PAYROLL_COLUMNS,
    REGIME_COLUMNS,
    TRADE_COLUMNS,
    attrition_at,
    available_share,
    exchange_rate,
    payroll_table,
    regime_table,
    settle,
    staffed_for_constraints,
    trade_table,
)

LOAD = 7.5845
HANDLING = 512.25
PATIENCE = 240.0
EVERY = Constraints(service_level=0.80, max_occupancy=0.85, max_abandonment=0.05)

#: A workforce nobody leaves, for the control case.
IMMORTAL = WorkforceProfile(
    base_attrition=0.0,
    attrition_knee=0.70,
    attrition_slope=0.0,
    time_to_fill_months=1.5,
    ramp_months=2.0,
    ramp_productivity=0.60,
)


class TestTheCurve:
    def test_attrition_is_flat_below_the_knee_and_linear_above_it(self) -> None:
        assert attrition_at(0.0) == pytest.approx(WORKFORCE.base_attrition)
        assert attrition_at(WORKFORCE.attrition_knee) == pytest.approx(WORKFORCE.base_attrition)
        # Two points above the knee, worked out from the declared numbers rather than from the code.
        assert attrition_at(0.85) == pytest.approx(0.02 + 0.12 * 0.15, abs=1e-12)
        assert attrition_at(0.95) == pytest.approx(0.02 + 0.12 * 0.25, abs=1e-12)

    def test_attrition_cannot_exceed_everybody(self) -> None:
        steep = WorkforceProfile(0.5, 0.1, 10.0, 1.5, 2.0, 0.6)
        assert attrition_at(1.0, steep) == pytest.approx(1.0)

    def test_an_occupancy_outside_the_unit_interval_is_refused(self) -> None:
        for value in (-0.1, 1.1):
            with pytest.raises(ValueError, match="is a share"):
                attrition_at(value)

    def test_nobody_leaving_means_the_whole_payroll_produces(self) -> None:
        assert available_share(0.0) == pytest.approx(1.0)

    def test_the_producing_share_falls_as_attrition_rises(self) -> None:
        shares = [available_share(rate) for rate in (0.0, 0.01, 0.02, 0.05, 0.1)]
        assert shares == sorted(shares, reverse=True)

    def test_a_workforce_the_loop_consumes_is_refused(self) -> None:
        with pytest.raises(ValueError, match="consume the whole payroll"):
            available_share(0.5)


class TestTheFixedPoint:
    def test_the_settled_state_is_its_own_definition(self) -> None:
        """Occupancy is the effective load over the producing agents, at the attrition it implies."""
        settled = settle(12, LOAD, HANDLING, PATIENCE)
        assert settled.settled
        producing = 12 * available_share(settled.monthly_attrition)
        assert settled.effective_agents == pytest.approx(producing, abs=1e-9)
        assert settled.occupancy == pytest.approx(
            LOAD * (1.0 - settled.abandonment) / producing, abs=1e-9
        )

    def test_a_workforce_nobody_leaves_costs_nothing(self) -> None:
        """The control: with no attrition the payroll and the agents are the same number."""
        settled = settle(11, LOAD, HANDLING, PATIENCE, IMMORTAL)
        assert settled.effective_agents == pytest.approx(11.0, abs=1e-12)
        assert settled.monthly_attrition == pytest.approx(0.0)
        assert settled.hires_per_year == pytest.approx(0.0)

    def test_more_payroll_is_weakly_better(self) -> None:
        """What the upward search depends on, over the range it searches."""
        states = [settle(staffed, LOAD, HANDLING, PATIENCE) for staffed in range(9, 30)]
        for earlier, later in zip(states, states[1:], strict=False):
            assert later.occupancy <= earlier.occupancy + 1e-12
            assert later.monthly_attrition <= earlier.monthly_attrition + 1e-12
            assert later.effective_agents >= earlier.effective_agents - 1e-12

    def test_the_annual_rate_compounds_the_monthly_one(self) -> None:
        settled = settle(27, 20.0, HANDLING, PATIENCE)
        assert settled.annual_attrition == pytest.approx(
            1.0 - (1.0 - settled.monthly_attrition) ** 12, abs=1e-12
        )
        assert settled.hires_per_year == pytest.approx(
            settled.staffed * settled.monthly_attrition * 12.0, abs=1e-12
        )

    def test_an_empty_payroll_or_an_impossible_start_is_refused(self) -> None:
        with pytest.raises(ValueError, match="at least one agent"):
            settle(0, LOAD, HANDLING, PATIENCE)
        with pytest.raises(ValueError, match="a share"):
            settle(12, LOAD, HANDLING, PATIENCE, start=1.5)

    def test_a_curve_steep_enough_collapses_rather_than_reporting_a_number(self) -> None:
        """The death spiral is a state: no steady state exists, and none is invented."""
        steep = WorkforceProfile(0.02, 0.70, 1.5, 1.5, 2.0, 0.60)
        settled = settle(12, LOAD, HANDLING, PATIENCE, steep, start=1.0)
        assert settled.collapsed
        assert not settled.settled
        assert settled.effective_agents == 0.0


class TestThePayroll:
    def test_the_payroll_delivers_the_agents_the_constraints_need(self) -> None:
        settled = staffed_for_constraints(LOAD, HANDLING, PATIENCE, EVERY)
        agents = math.floor(settled.effective_agents)
        assert not unmet(agents, LOAD, HANDLING, PATIENCE, EVERY)
        smaller = settle(settled.staffed - 1, LOAD, HANDLING, PATIENCE)
        assert unmet(max(1, math.floor(smaller.effective_agents)), LOAD, HANDLING, PATIENCE, EVERY)

    def test_a_workforce_nobody_leaves_needs_wave_sevens_answer_exactly(self) -> None:
        """With no attrition the payroll is the agent count, which ties the two waves together."""
        from svclab.planning import agents_for_constraints

        settled = staffed_for_constraints(LOAD, HANDLING, PATIENCE, EVERY, IMMORTAL)
        assert settled.staffed == agents_for_constraints(LOAD, HANDLING, PATIENCE, EVERY)

    def test_a_fractional_load_still_needs_a_whole_producing_agent(self) -> None:
        """Branch coverage found this path and it is a real one, not an imagined guard.

        At half an erlang the analytic floor is one person, whose producing share is 0.93 - which
        floors to zero agents. The search has to walk past that rather than treat a payroll of one as
        a queue with no server, and a load this small is the only place it happens.
        """
        settled = staffed_for_constraints(0.5, HANDLING, PATIENCE, EVERY)
        assert settled.staffed >= 2
        assert math.floor(settled.effective_agents) >= 1

    def test_constraints_no_payroll_can_deliver_are_refused(self) -> None:
        with pytest.raises(ValueError, match="no payroll up to"):
            staffed_for_constraints(
                LOAD, HANDLING, PATIENCE, Constraints(max_occupancy=0.01), ceiling=20
            )

    def test_the_payroll_table_exceeds_the_agents_it_yields(self) -> None:
        table = payroll_table((1.0, LOAD, 20.0), HANDLING, PATIENCE, EVERY)
        assert list(table.columns) == list(PAYROLL_COLUMNS)
        assert (table["staffed"] > table["effective_agents"]).all()
        assert (table["payroll_premium"] > 1.0).all()
        assert (table["empty_seats"] > 0.0).all()
        assert (table["ramping_seats"] > 0.0).all()

    def test_an_empty_load_set_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no loads"):
            payroll_table((), HANDLING, PATIENCE, EVERY)


class TestTheTrade:
    def test_a_lower_ceiling_costs_payroll_and_buys_hires(self) -> None:
        table = trade_table((0.90, 0.80, 0.70), LOAD, HANDLING, PATIENCE, EVERY)
        assert list(table.columns) == list(TRADE_COLUMNS)
        assert table["staffed"].tolist() == sorted(table["staffed"].tolist())
        assert table["hires_per_year"].tolist() == sorted(
            table["hires_per_year"].tolist(), reverse=True
        )
        assert table["staffed_change"].isna().iloc[0]
        assert table["hires_change"].isna().iloc[0]

    def test_an_empty_ceiling_set_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no occupancy ceilings"):
            trade_table((), LOAD, HANDLING, PATIENCE, EVERY)

    def test_there_is_no_trade_to_make_on_a_small_queue(self) -> None:
        """The ceiling never binds at this load, so every plan is the same plan.

        Wave 7 found that the occupancy ceiling binds only on large queues. The consequence here is
        that the trade this module prices **does not exist** on wave 1's queue: the service level
        already delivers 0.64 occupancy, which is under the knee, so attrition is at its floor and no
        ceiling buys anything. A rate is reported as ``nan`` rather than as zero, because zero would
        say the trade is free and the truth is that there is no trade.
        """
        table = trade_table((0.90, 0.80, 0.70), LOAD, HANDLING, PATIENCE, EVERY)
        assert (table["staffed"] == table["staffed"].iloc[0]).all()
        rate = exchange_rate(table)
        assert rate["extra_staffed"] == 0.0
        assert math.isnan(rate["hires_per_agent"])

    def test_the_exchange_rate_is_the_slope_across_the_ladder(self) -> None:
        """On a queue big enough for the ceiling to bind, the rate is the slope between the ends."""
        table = trade_table((0.90, 0.80, 0.70), 100.0, HANDLING, PATIENCE, EVERY)
        rate = exchange_rate(table)
        assert rate["extra_staffed"] > 0.0
        assert rate["fewer_hires_per_year"] > 0.0
        assert rate["hires_per_agent"] == pytest.approx(
            rate["fewer_hires_per_year"] / rate["extra_staffed"], abs=1e-9
        )

    def test_a_single_plan_has_no_rate_to_report(self) -> None:
        table = trade_table((0.85,), LOAD, HANDLING, PATIENCE, EVERY)
        with pytest.raises(ValueError, match="at least two plans"):
            exchange_rate(table)


class TestTheRegimes:
    def test_the_declared_curve_has_one_resting_place(self) -> None:
        table = regime_table((WORKFORCE.attrition_slope,), 12, LOAD, HANDLING, PATIENCE)
        assert list(table.columns) == list(REGIME_COLUMNS)
        row = table.iloc[0]
        assert not bool(row["two_regimes"])
        assert not bool(row["from_crisis_collapsed"])
        assert float(row["from_calm_occupancy"]) == pytest.approx(
            float(row["from_crisis_occupancy"]), abs=1e-9
        )

    def test_a_steep_enough_curve_has_two_and_then_none(self) -> None:
        table = regime_table((0.12, 1.5), 12, LOAD, HANDLING, PATIENCE).set_index("attrition_slope")
        assert not bool(table.loc[0.12, "two_regimes"])
        assert bool(table.loc[1.5, "two_regimes"])
        assert bool(table.loc[1.5, "from_crisis_collapsed"])

    def test_an_understaffed_payroll_splits_at_a_gentler_slope(self) -> None:
        """Robustness to the spiral is a property of the payroll, not only of the curve."""
        planned = regime_table((0.60,), 12, LOAD, HANDLING, PATIENCE).iloc[0]
        short = regime_table((0.60,), 10, LOAD, HANDLING, PATIENCE).iloc[0]
        assert not bool(planned["two_regimes"])
        assert bool(short["two_regimes"])

    def test_an_empty_slope_set_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no attrition slopes"):
            regime_table((), 12, LOAD, HANDLING, PATIENCE)

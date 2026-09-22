"""The occupancy ceiling priced in people, and the loop that makes a headcount two numbers.

Run:
    python examples/08_the_payroll_behind_the_plan.py

Wave 7 declared occupancy a ceiling: 0.84 fine, 0.86 forbidden. What a ceiling stands in for is a
curve, and a curve turns a constraint into a price. This example solves the loop that price closes -
occupancy raises attrition, attrition empties seats, an empty seat is not an agent - and then asks
what a point of occupancy is worth, and whether the loop ever runs away.

There is no money in this repository, so the trade comes out as an exchange rate in hires a year and
the decision about what a departure costs stays with the reader.
"""

from __future__ import annotations

import pandas as pd

from svclab.planning import Constraints, agents_for_constraints
from svclab.synth import WORKFORCE
from svclab.workforce import (
    exchange_rate,
    payroll_table,
    regime_table,
    staffed_for_constraints,
    trade_table,
)

#: Wave 1's queue, and wave 3's patience.
LOAD = 7.5845
HANDLING = 512.25
PATIENCE = 240.0

#: Wave 7's three ceilings.
CEILINGS = Constraints(service_level=0.80, max_occupancy=0.85, max_abandonment=0.05)

#: The loads wave 7 priced, and the one big enough for the occupancy ceiling to bind.
LOADS = (1.0, LOAD, 20.0, 50.0, 100.0)
BIG = 100.0

#: Occupancy ceilings to walk down, loosest first.
LADDER = (0.90, 0.85, 0.80, 0.75, 0.70)

#: Attrition slopes to test the loop against, the declared one first.
SLOPES = (0.12, 0.60, 1.00, 1.50)


def main() -> None:
    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 30)

    print("ONE: A PAYROLL IS NOT AN AGENT COUNT, AND THE GAP IS NOT A MARGIN")
    print("=" * 98)
    print(
        f"   Attrition is {WORKFORCE.base_attrition:.0%} a month below an occupancy of"
        f" {WORKFORCE.attrition_knee:.2f} and rises"
    )
    print(
        f"   {WORKFORCE.attrition_slope:.2f} per point above it. A seat stays empty"
        f" {WORKFORCE.time_to_fill_months} months and a new"
    )
    print(
        f"   agent spends {WORKFORCE.ramp_months} months at"
        f" {WORKFORCE.ramp_productivity:.0%} productivity."
    )
    print()
    table = payroll_table(LOADS, HANDLING, PATIENCE, CEILINGS).set_index("load")
    print(table.to_string())
    print()
    wave_seven = agents_for_constraints(LOAD, HANDLING, PATIENCE, CEILINGS)
    settled = staffed_for_constraints(LOAD, HANDLING, PATIENCE, CEILINGS)
    print(f"   Wave 7's {wave_seven} agents cost {settled.staffed} people.")
    big = table.loc[BIG]
    print(
        f"   At {BIG:.0f} erlangs, {int(big['effective_agents'])} agents cost"
        f" {int(big['staffed'])} - with {float(big['empty_seats']):.2f} seats empty and"
    )
    print(f"   {float(big['ramping_seats']):.2f} people ramping at any moment.")
    print()
    print("   And the premium is not monotone in the size of the queue:")
    for load in LOADS:
        row = table.loc[load]
        print(
            f"     {load:8.4f} erlangs -> premium {float(row['payroll_premium']):.4f}"
            f"  occupancy {float(row['occupancy']):.4f}"
            f"  attrition {float(row['annual_attrition']):.1%}/yr"
        )
    print("   Integer arithmetic dominates the small queue; attrition dominates the large one.")
    print()
    print(
        f"   Which prices wave 7's efficiency: the {BIG:.0f}-erlang queue needs 1.18 agents per"
        " erlang"
    )
    print(
        f"   and loses {float(big['annual_attrition']):.1%} of its staff a year,"
        f" hiring {float(big['hires_per_year']):.0f} people to stand still."
    )
    print()

    print("TWO: THE EXCHANGE RATE, AND THE QUEUE WHERE THERE IS NO TRADE")
    print("=" * 98)
    ladder = trade_table(LADDER, BIG, HANDLING, PATIENCE, CEILINGS)
    print(ladder.to_string(index=False))
    print()
    rate = exchange_rate(ladder)
    print(
        f"   {rate['extra_staffed']:.0f} more people buys {rate['fewer_hires_per_year']:.2f} fewer"
        f" hires a year: a rate of {rate['hires_per_agent']:.2f}."
    )
    wasted = WORKFORCE.time_to_fill_months + WORKFORCE.ramp_months * (
        1.0 - WORKFORCE.ramp_productivity
    )
    returned = rate["hires_per_agent"] * wasted
    print(f"   A departure wastes {wasted:.2f} person-months, so an extra agent costs 12")
    print(
        f"   person-months a year and returns {returned:.2f}: a ratio of {returned / 12.0:.2f}."
        " On the queue's"
    )
    print("   own books, loosening the occupancy loses by a factor of five.")
    print("   That does not make it wrong - it means the case rests entirely on what a departure")
    print("   costs outside the queue, which this repository declines to invent.")
    print()
    small = trade_table(LADDER, LOAD, HANDLING, PATIENCE, CEILINGS)
    print(f"   And on wave 1's {LOAD} erlangs there is no trade at all:")
    print(
        f"     every ceiling from {LADDER[0]:.2f} to {LADDER[-1]:.2f} needs the same"
        f" {int(small['staffed'].iloc[0])} people,"
    )
    print(
        f"     because the service level already delivers"
        f" {float(small['occupancy'].iloc[0]):.4f} occupancy - under the knee."
    )
    print("     The rate is nan rather than zero: zero would say the trade was free.")
    print()

    print("THREE: THE LOOP DOES NOT RUN AWAY, AND THE MARGIN IS THE PAYROLL'S")
    print("=" * 98)
    for staffed, label in ((settled.staffed, "the plan"), (settled.staffed - 2, "two short")):
        print(f"   Payroll {staffed} ({label}):")
        regimes = regime_table(SLOPES, staffed, LOAD, HANDLING, PATIENCE)
        print(regimes.to_string(index=False))
        split = regimes[regimes["two_regimes"]]
        if split.empty:
            print("     one resting place at every slope tested")
        else:
            first = float(split["attrition_slope"].iloc[0])
            print(
                f"     splits at a slope of {first:.2f} -"
                f" {first / WORKFORCE.attrition_slope:.1f} times the declared one"
            )
        print()
    print(
        "   At the declared curve there is no spiral: the fixed point is unique and the iteration"
    )
    print("   reaches it from either end. Robustness is a property of the payroll, not only of the")
    print("   curve - and the second regime is not a collapse. It has lower occupancy and lower")
    print("   attrition than the first, reached by losing customers rather than by keeping agents.")
    print("   Abandonment is the escape valve, for the third time in this repository.")


if __name__ == "__main__":
    main()

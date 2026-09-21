"""Staffing to ceilings instead of to a target, and finding out which ceiling decided.

Run:
    python examples/07_the_constraint_nobody_declared.py

Every plan in waves 1 to 6 staffed to a service level and then reported the occupancy and the
abandonment it landed on. Wave 3's sharpest line was a queue "perfectly stable" at six agents, with
29% of the customers abandoning and the rest handled at 89% occupancy - both of them outputs. This
example declares all three as ceilings and asks which one settles the headcount, what wave 3's six
agents actually fail, and how the answer changes with the size of the queue.
"""

from __future__ import annotations

import pandas as pd

from svclab.planning import (
    Constraints,
    agents_at_ceiling,
    agents_for_constraints,
    headroom,
    metrics_at,
    plan_table,
    scale_table,
    unmet,
)

#: Wave 1's queue, and wave 3's patience.
LOAD = 7.5845
HANDLING = 512.25
PATIENCE = 240.0
TARGET_SECONDS = 20.0

#: The declared ceilings. Round numbers chosen to make the mechanics visible, not benchmarks.
SERVICE_LEVEL = 0.80
MAX_OCCUPANCY = 0.85
MAX_ABANDONMENT = 0.05

#: What wave 1 promised and what wave 3 called stable.
PROMISED = 5.51
CALLED_STABLE = 6


def main() -> None:
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)

    every = Constraints(
        service_level=SERVICE_LEVEL,
        max_occupancy=MAX_OCCUPANCY,
        max_abandonment=MAX_ABANDONMENT,
    )

    print("ONE: THREE CEILINGS, AND ONLY TWO OF THEM DO ANYTHING HERE")
    print("=" * 98)
    plans = {
        "service level only": Constraints(service_level=SERVICE_LEVEL),
        "occupancy only": Constraints(max_occupancy=MAX_OCCUPANCY),
        "abandonment only": Constraints(max_abandonment=MAX_ABANDONMENT),
        "service level + occupancy": Constraints(
            service_level=SERVICE_LEVEL, max_occupancy=MAX_OCCUPANCY
        ),
        "all three": every,
    }
    table = plan_table(plans, LOAD, HANDLING, PATIENCE).set_index("plan")
    print(table.to_string())
    print()
    only = table.loc["occupancy only"]
    print(
        f"   An occupancy ceiling on its own is satisfied by understaffing:"
        f" {int(only['agents'])} agents,"
    )
    print(
        f"   occupancy {float(only['occupancy']):.4f} - and {float(only['abandonment']):.2%} of"
        f" customers giving up, with"
    )
    print(
        f"   {float(only['service_level']):.2%} answered inside the target. The customers who"
        " abandon are what"
    )
    print("   keeps the occupancy down, so the target rewards the queue for losing people.")
    print()
    print(
        f"   The service level and the abandonment ceiling reach the same"
        f" {int(table.loc['all three', 'agents'])} by independent routes,"
    )
    print(f"   and they bind together: {table.loc['all three', 'binding']}.")
    print()

    print("TWO: WHICH SETTLES WHAT WAVE 3 LEFT OPEN")
    print("=" * 98)
    measured = metrics_at(CALLED_STABLE, LOAD, HANDLING, PATIENCE, TARGET_SECONDS)
    failing = unmet(CALLED_STABLE, LOAD, HANDLING, PATIENCE, every)
    print(f"   Wave 3 called {CALLED_STABLE} agents a stable queue. Against the three ceilings:")
    for name, value, ceiling, worse in (
        ("service level", measured["service_level"], SERVICE_LEVEL, "below"),
        ("occupancy", measured["occupancy"], MAX_OCCUPANCY, "above"),
        ("abandonment", measured["abandonment"], MAX_ABANDONMENT, "above"),
    ):
        verdict = "FAILS" if name in failing else "ok"
        print(f"     {name:<15} {value:.4f}  ceiling {ceiling:.2f} ({worse} is worse)  {verdict}")
    print()
    print("   Stability means the queue has a steady state, which it does - with one customer in")
    print("   three walking away. Stability is not a plan.")
    print()
    needed = agents_for_constraints(LOAD, HANDLING, PATIENCE, every)
    napkin = agents_at_ceiling(LOAD, MAX_OCCUPANCY)
    print(
        f"   And the napkin: load / occupancy ceiling = {napkin} agents. The queue needs {needed}."
    )
    # Expressed as a share of the requirement, which is the base the README quotes: the napkin is
    # short by (needed - napkin) / needed. The other base - how far the requirement exceeds the
    # napkin - is a different number for the same gap, and carrying both in one wave is how a figure
    # ends up contradicting itself.
    print(f"   The napkin is short by {1 - napkin / needed:.0%} of the requirement - wave 1's")
    print(
        f"   headcount error in a new costume, where the promise of {PROMISED} multiplied instead."
    )
    print()

    print("THREE: AND WHICH CEILING BINDS DEPENDS ON HOW BIG THE QUEUE IS")
    print("=" * 98)
    sizes = scale_table((1.0, 2.5, LOAD, 20.0, 50.0, 100.0, 400.0), HANDLING, PATIENCE, every)
    print(sizes.to_string(index=False))
    print()
    smallest = float(sizes["agents_per_erlang"].iloc[0])
    largest = float(sizes["agents_per_erlang"].iloc[-1])
    fall = 1.0 - largest / smallest
    print(f"   Agents per erlang falls from {smallest:.4f} to {largest:.4f} - a drop of {fall:.0%}")
    print(
        "   - and that is the whole case for consolidating queues. But the economy of scale ends:"
    )
    print("   the service level binds up to about 35 erlangs and the occupancy ceiling alone from")
    print(
        "   45 upward. Past that the queue is limited by the agent's tolerance rather than by the"
    )
    print("   customer's, and those two are negotiated with different people.")
    print()

    print("FOUR: 'COMPLIANT' AND 'ONE ABSENCE FROM BREACHING' ARE THE SAME SENTENCE")
    print("=" * 98)
    for agents in (needed, needed + 1):
        slack = headroom(agents, LOAD, HANDLING, PATIENCE, every)
        rendered = "  ".join(f"{name} {value:+.4f}" for name, value in slack.items())
        print(f"   {agents} agents: {rendered}")
    print()
    tight = min(headroom(needed, LOAD, HANDLING, PATIENCE, every).items(), key=lambda item: item[1])
    print(f"   The thinnest margin is {tight[0]}, at {tight[1]:+.4f}. A plan that reports 'all")
    print("   constraints met' and a plan that reports this line are the same plan, and only the")
    print("   second tells a manager which number moves first when somebody calls in sick.")


if __name__ == "__main__":
    main()

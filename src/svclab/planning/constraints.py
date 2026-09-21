"""Staffing to constraints instead of to one target, and finding out which constraint decides.

Every plan in waves 1 to 6 staffed to a **service level** and then reported the occupancy and the
abandonment it happened to arrive at. Wave 3 printed the sharpest version of that: a queue perfectly
stable at six agents, with 29.23% of the customers abandoning and the survivors' agents at 89.45%
occupancy. Both numbers were outputs. No real plan treats them that way - an occupancy ceiling is
what
stops attrition, and an abandonment ceiling is what the regulator or the brand asks for.

So this module inverts it. Declare the ceilings, and the headcount is whatever satisfies all of
them.
Two things fall out.

**The constraint that decides the headcount is usually not the one that was negotiated.** A plan
argued over a service level can be settled by an occupancy ceiling nobody mentioned, and the table
says which - because a plan whose binding constraint is unnamed is a plan whose owner does not know
what they bought.

**And which constraint binds depends on the size of the queue.** A large queue reaches a service
level
at an occupancy a small queue cannot survive, so the same three ceilings are settled by the service
level at one erlang and by the occupancy ceiling at a hundred. That is the arithmetic behind
consolidating queues, and it is also why a ceiling that is comfortable at head office is impossible
at
a branch.

Occupancy here is measured on the **effective** load - the work that is actually answered - because
a
customer who abandons occupies nobody. Using the offered load instead overstates occupancy wherever
abandonment is material, which is precisely where the ceiling is being tested.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd

from svclab.capacity import abandonment, service_level
from svclab.synth import CENTRE

#: Columns of the plan table, one row per declared set of constraints.
PLAN_COLUMNS = (
    "plan",
    "agents",
    "service_level",
    "abandonment",
    "occupancy",
    "effective_load",
    "binding",
)

#: Columns of the table that varies the size of the queue under one set of constraints.
SCALE_COLUMNS = (
    "load",
    "agents",
    "agents_per_erlang",
    "service_level",
    "abandonment",
    "occupancy",
    "binding",
)

#: The three names a constraint can bind under, in the order the table reports them.
CONSTRAINT_NAMES = ("service level", "occupancy", "abandonment")


@dataclass(frozen=True)
class Constraints:
    """What a plan has to satisfy, rather than what it reports.

    Every field is optional and at least one has to be set: a plan with no constraint is not a plan.
    The ceilings are inclusive, so a maximum occupancy of 0.85 is satisfied at exactly 0.85.

    Attributes:
        service_level: Share of contacts to answer inside ``target_seconds``, or ``None``.
        target_seconds: The wait the service level is measured against.
        max_occupancy: The highest share of staffed time an agent may spend handling contacts, or
            ``None``. The number that decides whether a plan is humane, and the one wave 3 reported
            at 89.45% without treating it as a limit.
        max_abandonment: The highest share of customers who may give up waiting, or ``None``.
    """

    service_level: float | None = None
    target_seconds: float = CENTRE.target_answer_seconds
    max_occupancy: float | None = None
    max_abandonment: float | None = None

    def __post_init__(self) -> None:
        if all(
            value is None
            for value in (self.service_level, self.max_occupancy, self.max_abandonment)
        ):
            raise ValueError("a plan with no constraint is not a plan")
        for name, value in (
            ("service_level", self.service_level),
            ("max_occupancy", self.max_occupancy),
            ("max_abandonment", self.max_abandonment),
        ):
            if value is not None and not 0.0 < value < 1.0:
                raise ValueError(f"{name} has to be strictly between zero and one, got {value}")
        if self.target_seconds < 0.0:
            raise ValueError(f"the target wait cannot be negative, got {self.target_seconds}")


def metrics_at(
    agents: int,
    load: float,
    handling_mean: float,
    patience_mean: float,
    target_seconds: float,
) -> dict[str, float]:
    """The three numbers a plan is judged on, at one staffing level.

    Args:
        agents: Agents on the queue.
        load: Offered load in erlangs.
        handling_mean: Mean handling seconds.
        patience_mean: Mean seconds a waiting customer tolerates.
        target_seconds: The wait the service level is measured against.

    Returns:
        The service level, the abandonment, the effective load and the occupancy of that load.

    Raises:
        ValueError: If there is not at least one agent.
    """
    if agents < 1:
        raise ValueError(f"a queue needs at least one agent, got {agents}")
    leaving = abandonment(agents, load, patience_mean, handling_mean)
    effective = load * (1.0 - leaving)
    return {
        "service_level": service_level(agents, load, handling_mean, target_seconds),
        "abandonment": leaving,
        "effective_load": effective,
        "occupancy": effective / agents,
    }


def unmet(
    agents: int,
    load: float,
    handling_mean: float,
    patience_mean: float,
    constraints: Constraints,
) -> tuple[str, ...]:
    """Which of the declared constraints this staffing level fails, in a fixed order.

    Args:
        agents: Agents on the queue.
        load: Offered load in erlangs.
        handling_mean: Mean handling seconds.
        patience_mean: Mean seconds a waiting customer tolerates.
        constraints: What the plan has to satisfy.

    Returns:
        The names of the failing constraints, empty when the level satisfies every one of them.
    """
    measured = metrics_at(agents, load, handling_mean, patience_mean, constraints.target_seconds)
    failing = []
    if (
        constraints.service_level is not None
        and measured["service_level"] < constraints.service_level
    ):
        failing.append("service level")
    if constraints.max_occupancy is not None and measured["occupancy"] > constraints.max_occupancy:
        failing.append("occupancy")
    if (
        constraints.max_abandonment is not None
        and measured["abandonment"] > constraints.max_abandonment
    ):
        failing.append("abandonment")
    return tuple(failing)


def agents_for_constraints(
    load: float,
    handling_mean: float,
    patience_mean: float,
    constraints: Constraints,
    ceiling: int = 2_000,
) -> int:
    """The smallest staffing level that satisfies every declared constraint.

    Searched upwards from one agent rather than solved. Two of the three quantities are step
    functions
    of an integer and the third is not monotone in the way a solver would need: the service level is
    zero below the load and rises sharply through it, so a continuous solution rounded to an integer
    lands on the wrong side often enough to be useless.

    Args:
        load: Offered load in erlangs.
        handling_mean: Mean handling seconds.
        patience_mean: Mean seconds a waiting customer tolerates.
        constraints: What the plan has to satisfy.
        ceiling: Where to stop searching.

    Returns:
        The agent count.

    Raises:
        ValueError: If the ceiling is reached, which means the constraints ask for something this
            queue cannot buy at any headcount the search considered.
    """
    for agents in range(1, ceiling + 1):
        if not unmet(agents, load, handling_mean, patience_mean, constraints):
            return agents
    raise ValueError(
        f"no staffing level up to {ceiling} satisfies these constraints at a load of {load}"
    )


def binding_constraint(
    agents: int,
    load: float,
    handling_mean: float,
    patience_mean: float,
    constraints: Constraints,
) -> str:
    """Which constraint one fewer agent would have failed, which is the one that set the headcount.

    The question a plan's owner should be able to answer and usually cannot. Several constraints can
    bind at once, and they are joined rather than ranked: a headcount two ceilings both decide is
    one that neither of them can be negotiated away from alone.

    Args:
        agents: The staffing level the plan settled on.
        load: Offered load in erlangs.
        handling_mean: Mean handling seconds.
        patience_mean: Mean seconds a waiting customer tolerates.
        constraints: What the plan has to satisfy.

    Returns:
        The failing constraint names joined by ``" + "``, or ``"minimum"`` when the plan is at one
        agent and nothing below it exists to test.
    """
    if agents <= 1:
        return "minimum"
    failing = unmet(agents - 1, load, handling_mean, patience_mean, constraints)
    return " + ".join(failing) if failing else "none"


def plan_table(
    plans: Mapping[str, Constraints],
    load: float,
    handling_mean: float,
    patience_mean: float,
) -> pd.DataFrame:
    """One row per declared plan: the headcount it needs, and what decided it.

    Args:
        plans: Constraint sets by plan name.
        load: Offered load in erlangs.
        handling_mean: Mean handling seconds.
        patience_mean: Mean seconds a waiting customer tolerates.

    Returns:
        A frame with the columns in :data:`PLAN_COLUMNS`.

    Raises:
        ValueError: If no plans are given.
    """
    if not plans:
        raise ValueError("there are no plans to price")
    rows = []
    for name, constraints in plans.items():
        agents = agents_for_constraints(load, handling_mean, patience_mean, constraints)
        measured = metrics_at(
            agents, load, handling_mean, patience_mean, constraints.target_seconds
        )
        rows.append(
            {
                "plan": name,
                "agents": agents,
                **measured,
                "binding": binding_constraint(
                    agents, load, handling_mean, patience_mean, constraints
                ),
            }
        )
    return pd.DataFrame(rows)[list(PLAN_COLUMNS)]


def scale_table(
    loads: tuple[float, ...],
    handling_mean: float,
    patience_mean: float,
    constraints: Constraints,
) -> pd.DataFrame:
    """The same constraints against queues of different sizes, and which one binds at each.

    The column to read is ``binding``. A large queue reaches a service level at an occupancy a small
    queue cannot, so the ceiling that settles the headcount moves with the size of the operation -
    which is the arithmetic behind consolidating queues and behind a ceiling that is comfortable at
    one site and unreachable at another.

    Args:
        loads: Offered loads in erlangs.
        handling_mean: Mean handling seconds.
        patience_mean: Mean seconds a waiting customer tolerates.
        constraints: What every plan has to satisfy.

    Returns:
        A frame with the columns in :data:`SCALE_COLUMNS`, one row per load.

    Raises:
        ValueError: If no loads are given.
    """
    if not loads:
        raise ValueError("there are no loads to staff")
    rows = []
    for load in loads:
        agents = agents_for_constraints(load, handling_mean, patience_mean, constraints)
        measured = metrics_at(
            agents, load, handling_mean, patience_mean, constraints.target_seconds
        )
        rows.append(
            {
                "load": load,
                "agents": agents,
                "agents_per_erlang": agents / load,
                "service_level": measured["service_level"],
                "abandonment": measured["abandonment"],
                "occupancy": measured["occupancy"],
                "binding": binding_constraint(
                    agents, load, handling_mean, patience_mean, constraints
                ),
            }
        )
    return pd.DataFrame(rows)[list(SCALE_COLUMNS)]


def headroom(
    agents: int,
    load: float,
    handling_mean: float,
    patience_mean: float,
    constraints: Constraints,
) -> dict[str, float]:
    """How much slack each declared constraint has at a staffing level, signed so positive is slack.

    Published as its own function because "we are compliant" and "we are one sick day from
    breaching"
    are the same sentence in a plan that only reports whether constraints are met.

    Args:
        agents: The staffing level to measure.
        load: Offered load in erlangs.
        handling_mean: Mean handling seconds.
        patience_mean: Mean seconds a waiting customer tolerates.
        constraints: What the plan has to satisfy.

    Returns:
        Slack per declared constraint, in that constraint's own units. Undeclared constraints are
        absent rather than infinite.
    """
    measured = metrics_at(agents, load, handling_mean, patience_mean, constraints.target_seconds)
    slack = {}
    if constraints.service_level is not None:
        slack["service level"] = measured["service_level"] - constraints.service_level
    if constraints.max_occupancy is not None:
        slack["occupancy"] = constraints.max_occupancy - measured["occupancy"]
    if constraints.max_abandonment is not None:
        slack["abandonment"] = constraints.max_abandonment - measured["abandonment"]
    return slack


def agents_at_ceiling(load: float, max_occupancy: float) -> int:
    """The headcount an occupancy ceiling implies on its own, before any queueing.

    ``load / ceiling``, rounded up. It is the floor every other constraint sits on top of, and it is
    the one line of arithmetic a plan can do without a queueing model at all - which is why it is
    worth seeing next to the search.

    Args:
        load: Offered load in erlangs.
        max_occupancy: The occupancy ceiling.

    Returns:
        The agent count.

    Raises:
        ValueError: If the ceiling is not strictly between zero and one.
    """
    if not 0.0 < max_occupancy < 1.0:
        raise ValueError(f"an occupancy ceiling is between zero and one, got {max_occupancy}")
    return max(1, math.ceil(load / max_occupancy))

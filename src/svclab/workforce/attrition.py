"""What an occupancy costs in people, and the loop that makes a headcount two numbers.

Wave 7 declared occupancy a ceiling: 0.84 fine, 0.86 forbidden. What a ceiling stands in for is a
curve - attrition rises with how hard the work is - and a curve turns a constraint into a **price**.

Pricing it closes a loop every operations manager knows and no staffing model contains:

> occupancy raises attrition → attrition empties seats → an empty seat is not an agent →
> fewer agents raise occupancy

So the headcount that produces the work and the headcount on the payroll are two different numbers,
joined by a fixed point rather than by a margin. This module solves that fixed point, prices a point
of occupancy in hires a year, and then asks the uncomfortable question: does the loop ever run away?

**It does not, at the declared curve** - the fixed point is unique and the iteration converges from
either end. The slope has to be about eight times steeper before a second equilibrium appears, and
when it does the second one is not a collapse. It has **lower** occupancy and **lower** attrition
than the first, reached by losing customers rather than by keeping agents: the abandonment is the
escape valve. That is the third wave in a row where abandonment turns out to be what stops something
from diverging, and it is not good news either time.

Every quantity here is in agents, seats, months and hires. There is still no money in this
repository, so the trade is published as an **exchange rate** - hires a year per agent on the
payroll - and the decision about what a hire is worth stays with the reader, where it belongs.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd

from svclab.capacity import abandonment
from svclab.planning import Constraints, unmet
from svclab.synth import WORKFORCE, WorkforceProfile

#: Columns of the payroll table, one row per load.
PAYROLL_COLUMNS = (
    "load",
    "effective_agents",
    "staffed",
    "payroll_premium",
    "occupancy",
    "monthly_attrition",
    "annual_attrition",
    "hires_per_year",
    "empty_seats",
    "ramping_seats",
)

#: Columns of the trade table, one row per declared occupancy ceiling.
TRADE_COLUMNS = (
    "max_occupancy",
    "staffed",
    "effective_agents",
    "occupancy",
    "monthly_attrition",
    "annual_attrition",
    "hires_per_year",
    "staffed_change",
    "hires_change",
)

#: Columns of the regime table, one row per attrition slope.
REGIME_COLUMNS = (
    "attrition_slope",
    "from_calm_occupancy",
    "from_calm_attrition",
    "from_calm_abandonment",
    "from_crisis_occupancy",
    "from_crisis_attrition",
    "from_crisis_abandonment",
    "from_crisis_collapsed",
    "two_regimes",
)

#: How many times the fixed point is iterated before it is called divergent.
SETTLE_STEPS = 500

#: How close two successive occupancies have to be for the loop to be settled.
SETTLE_TOLERANCE = 1e-12


@dataclass(frozen=True)
class Settlement:
    """Where the attrition loop comes to rest, and whether it got there.

    Attributes:
        staffed: Agents on the payroll.
        occupancy: The occupancy the loop settles at.
        monthly_attrition: The attrition that occupancy implies.
        effective_agents: Agents actually producing work - the payroll less the empty seats and the
            productivity a ramping agent has not reached yet.
        abandonment: The share of customers who give up waiting at that staffing.
        iterations: Steps the loop took.
        settled: Whether it converged inside :data:`SETTLE_STEPS`. A loop that did not settle is
            reported rather than averaged: the honest answer to "where does this end up" is
            sometimes "it does not".
        collapsed: Whether the loop drove attrition high enough that the vacancies and the ramp
            consume the whole payroll. That is the death spiral, and it is a **state** rather than
            an error: there is no steady state to report, and a number near zero instead would be
            an invented one.
    """

    staffed: int
    occupancy: float
    monthly_attrition: float
    effective_agents: float
    abandonment: float
    iterations: int
    settled: bool
    collapsed: bool = False

    @property
    def annual_attrition(self) -> float:
        """The monthly rate compounded over a year, which is how it gets quoted."""
        return 1.0 - (1.0 - self.monthly_attrition) ** 12

    @property
    def hires_per_year(self) -> float:
        """Replacements a year at this attrition, which is the currency of the trade."""
        return self.staffed * self.monthly_attrition * 12.0


def attrition_at(occupancy: float, workforce: WorkforceProfile = WORKFORCE) -> float:
    """Monthly attrition at an occupancy, from the declared curve.

    Flat below the knee and linear above it, clipped at one. Linear rather than exponential for the
    same reason the generator's response curves are: the knee and the slope are the two numbers a
    stakeholder would argue about, and an exponent is not.

    Args:
        occupancy: Share of staffed time spent handling contacts.
        workforce: The declared curve.

    Returns:
        The monthly share of agents who leave.

    Raises:
        ValueError: If the occupancy is outside the unit interval.
    """
    if not 0.0 <= occupancy <= 1.0:
        raise ValueError(f"an occupancy is a share, not {occupancy}")
    above = max(0.0, occupancy - workforce.attrition_knee)
    return min(1.0, workforce.base_attrition + workforce.attrition_slope * above)


def available_share(monthly_attrition: float, workforce: WorkforceProfile = WORKFORCE) -> float:
    """The share of a payroll that is actually producing work, in steady state.

    Two deductions, both of them consequences of the same attrition. A seat stays empty for
    ``time_to_fill_months`` after somebody leaves, so a share ``attrition x time_to_fill`` of the
    payroll is vacant at any moment. And a new agent spends ``ramp_months`` below full productivity,
    so a share ``attrition x ramp_months`` is ramping and delivers only ``ramp_productivity`` of
    what it will.

    Args:
        monthly_attrition: The monthly share who leave.
        workforce: The declared curve.

    Returns:
        The producing share of the payroll.

    Raises:
        ValueError: If the deductions reach or exceed the whole payroll, which is a workforce that
            cannot staff anything and is refused rather than returned as a number near zero.
    """
    vacant = monthly_attrition * workforce.time_to_fill_months
    ramping = monthly_attrition * workforce.ramp_months
    share = 1.0 - vacant - ramping * (1.0 - workforce.ramp_productivity)
    if share <= 0.0:
        raise ValueError(
            f"at a monthly attrition of {monthly_attrition} the vacancies and the ramp consume the "
            f"whole payroll, so no staffing level produces anything"
        )
    return share


def settle(
    staffed: int,
    load: float,
    handling_mean: float,
    patience_mean: float,
    workforce: WorkforceProfile = WORKFORCE,
    start: float = 0.0,
) -> Settlement:
    """Where the loop comes to rest for a payroll, iterated from a declared starting occupancy.

    The starting point matters, and that is the point of exposing it. Where the loop has one fixed
    point both ends reach it; where it has two, an operation that has been through a crisis settles
    somewhere an operation that has not does not.

    Args:
        staffed: Agents on the payroll.
        load: Offered load in erlangs.
        handling_mean: Mean handling seconds.
        patience_mean: Mean seconds a waiting customer tolerates.
        workforce: The declared curve.
        start: The occupancy to iterate from. Zero is a calm operation; one is a queue in crisis.

    Returns:
        A :class:`Settlement`.

    Raises:
        ValueError: If the payroll is empty or the starting occupancy is not a share.
    """
    if staffed < 1:
        raise ValueError(f"a payroll has at least one agent, not {staffed}")
    if not 0.0 <= start <= 1.0:
        raise ValueError(f"a starting occupancy is a share, not {start}")

    occupancy = start
    leaving = 0.0
    producing = 0.0
    for step in range(SETTLE_STEPS):
        monthly = attrition_at(occupancy, workforce)
        try:
            producing = staffed * available_share(monthly, workforce)
        except ValueError:
            # The loop reached an attrition whose vacancies and ramp consume the payroll. There is
            # no steady state at all, which is the death spiral - reported as a state rather than
            # raised, because a caller sweeping a range of curves is asking exactly this question.
            return Settlement(
                staffed=staffed,
                occupancy=1.0,
                monthly_attrition=monthly,
                effective_agents=0.0,
                abandonment=1.0,
                iterations=step,
                settled=False,
                collapsed=True,
            )
        # Abandonment is evaluated at a whole number of agents, because a queue cannot be served by
        # four fifths of a person. Rounding down is the conservative direction and it is the same
        # rounding wave 3's staffing search makes.
        answered = max(1, math.floor(producing))
        leaving = abandonment(answered, load, patience_mean, handling_mean)
        effective_load = load * (1.0 - leaving)
        moved = min(1.0, effective_load / producing)
        if abs(moved - occupancy) < SETTLE_TOLERANCE:
            return Settlement(
                staffed=staffed,
                occupancy=moved,
                monthly_attrition=attrition_at(moved, workforce),
                effective_agents=producing,
                abandonment=leaving,
                iterations=step,
                settled=True,
            )
        occupancy = moved
    return Settlement(
        staffed=staffed,
        occupancy=occupancy,
        monthly_attrition=attrition_at(occupancy, workforce),
        effective_agents=producing,
        abandonment=leaving,
        iterations=SETTLE_STEPS,
        settled=False,
    )


def staffed_for_constraints(
    load: float,
    handling_mean: float,
    patience_mean: float,
    constraints: Constraints,
    workforce: WorkforceProfile = WORKFORCE,
    ceiling: int = 4_000,
) -> Settlement:
    """The smallest payroll whose settled state satisfies wave 7's constraints.

    Wave 7 answered "how many agents does this need". This answers "how many people do you hire to
    have that many agents", which is the question a plan is actually funded on.

    The search starts at the payroll the **best possible** conversion would need - the required
    agents divided by the producing share at base attrition - because no payroll below that can work
    however the loop settles. Starting at one agent instead is correct and slow, and at four hundred
    erlangs slow enough to matter.

    Args:
        load: Offered load in erlangs.
        handling_mean: Mean handling seconds.
        patience_mean: Mean seconds a waiting customer tolerates.
        constraints: What the settled state has to satisfy.
        workforce: The declared curve.
        ceiling: Where to stop searching.

    Returns:
        The :class:`Settlement` of the smallest satisfying payroll.

    Raises:
        ValueError: If the ceiling is reached, which means the loop cannot deliver these constraints
            at this load however many people are hired.
    """
    best = available_share(workforce.base_attrition, workforce)
    floor = max(1, math.ceil(load / best))
    for staffed in range(floor, ceiling + 1):
        settled = settle(staffed, load, handling_mean, patience_mean, workforce)
        if not settled.settled:
            continue
        agents = math.floor(settled.effective_agents)
        if agents < 1:
            continue
        if not unmet(agents, load, handling_mean, patience_mean, constraints):
            return settled
    raise ValueError(
        f"no payroll up to {ceiling} settles into a state that satisfies these constraints at a "
        f"load of {load}"
    )


def payroll_table(
    loads: tuple[float, ...],
    handling_mean: float,
    patience_mean: float,
    constraints: Constraints,
    workforce: WorkforceProfile = WORKFORCE,
) -> pd.DataFrame:
    """The payroll each load needs, against the agents it produces.

    Args:
        loads: Offered loads in erlangs.
        handling_mean: Mean handling seconds.
        patience_mean: Mean seconds a waiting customer tolerates.
        constraints: What each settled state has to satisfy.
        workforce: The declared curve.

    Returns:
        A frame with the columns in :data:`PAYROLL_COLUMNS`. ``payroll_premium`` is the payroll
        divided by the agents it yields - the gap between what a plan hires and what it gets.

    Raises:
        ValueError: If no loads are given.
    """
    if not loads:
        raise ValueError("there are no loads to staff")
    rows = []
    for load in loads:
        settled = staffed_for_constraints(
            load, handling_mean, patience_mean, constraints, workforce
        )
        vacant = settled.monthly_attrition * workforce.time_to_fill_months
        ramping = settled.monthly_attrition * workforce.ramp_months
        rows.append(
            {
                "load": load,
                "effective_agents": math.floor(settled.effective_agents),
                "staffed": settled.staffed,
                "payroll_premium": settled.staffed / math.floor(settled.effective_agents),
                "occupancy": settled.occupancy,
                "monthly_attrition": settled.monthly_attrition,
                "annual_attrition": settled.annual_attrition,
                "hires_per_year": settled.hires_per_year,
                "empty_seats": settled.staffed * vacant,
                "ramping_seats": settled.staffed * ramping,
            }
        )
    return pd.DataFrame(rows)[list(PAYROLL_COLUMNS)]


def trade_table(
    ceilings: tuple[float, ...],
    load: float,
    handling_mean: float,
    patience_mean: float,
    constraints: Constraints,
    workforce: WorkforceProfile = WORKFORCE,
) -> pd.DataFrame:
    """What a point of occupancy costs, in people on the payroll and in hires a year.

    The exchange rate a manager asks for and a staffing model never prints. Both columns of change
    are against the previous row, so the table reads as a ladder rather than as five separate plans.

    Args:
        ceilings: Occupancy ceilings to price, in the order they should be read.
        load: Offered load in erlangs.
        handling_mean: Mean handling seconds.
        patience_mean: Mean seconds a waiting customer tolerates.
        constraints: The other constraints, held fixed. Its own occupancy ceiling is replaced by
        each
            value in ``ceilings``.
        workforce: The declared curve.

    Returns:
        A frame with the columns in :data:`TRADE_COLUMNS`.

    Raises:
        ValueError: If no ceilings are given.
    """
    if not ceilings:
        raise ValueError("there are no occupancy ceilings to price")
    rows = []
    previous: Settlement | None = None
    for ceiling in ceilings:
        plan = Constraints(
            service_level=constraints.service_level,
            target_seconds=constraints.target_seconds,
            max_occupancy=ceiling,
            max_abandonment=constraints.max_abandonment,
        )
        settled = staffed_for_constraints(load, handling_mean, patience_mean, plan, workforce)
        rows.append(
            {
                "max_occupancy": ceiling,
                "staffed": settled.staffed,
                "effective_agents": math.floor(settled.effective_agents),
                "occupancy": settled.occupancy,
                "monthly_attrition": settled.monthly_attrition,
                "annual_attrition": settled.annual_attrition,
                "hires_per_year": settled.hires_per_year,
                "staffed_change": (
                    float("nan") if previous is None else settled.staffed - previous.staffed
                ),
                "hires_change": (
                    float("nan")
                    if previous is None
                    else settled.hires_per_year - previous.hires_per_year
                ),
            }
        )
        previous = settled
    return pd.DataFrame(rows)[list(TRADE_COLUMNS)]


def regime_table(
    slopes: tuple[float, ...],
    staffed: int,
    load: float,
    handling_mean: float,
    patience_mean: float,
    workforce: WorkforceProfile = WORKFORCE,
) -> pd.DataFrame:
    """Whether the loop has one resting place or two, at a range of attrition slopes.

    Each slope is settled twice: from a calm operation and from one in crisis. Where the two
    disagree the loop has two equilibria, and which one an operation lives in is a fact about its
    history rather than about its plan.

    Args:
        slopes: Attrition slopes to try, replacing the declared one.
        staffed: The payroll to hold fixed.
        load: Offered load in erlangs.
        handling_mean: Mean handling seconds.
        patience_mean: Mean seconds a waiting customer tolerates.
        workforce: The declared curve, for everything except the slope.

    Returns:
        A frame with the columns in :data:`REGIME_COLUMNS`.

    Raises:
        ValueError: If no slopes are given.
    """
    if not slopes:
        raise ValueError("there are no attrition slopes to try")
    rows = []
    for slope in slopes:
        curve = WorkforceProfile(
            base_attrition=workforce.base_attrition,
            attrition_knee=workforce.attrition_knee,
            attrition_slope=slope,
            time_to_fill_months=workforce.time_to_fill_months,
            ramp_months=workforce.ramp_months,
            ramp_productivity=workforce.ramp_productivity,
        )
        calm = settle(staffed, load, handling_mean, patience_mean, curve, start=0.0)
        crisis = settle(staffed, load, handling_mean, patience_mean, curve, start=1.0)
        rows.append(
            {
                "attrition_slope": slope,
                "from_calm_occupancy": calm.occupancy,
                "from_calm_attrition": calm.monthly_attrition,
                "from_calm_abandonment": calm.abandonment,
                "from_crisis_occupancy": crisis.occupancy,
                "from_crisis_attrition": crisis.monthly_attrition,
                "from_crisis_abandonment": crisis.abandonment,
                "from_crisis_collapsed": crisis.collapsed,
                "two_regimes": abs(calm.occupancy - crisis.occupancy) > 1e-4,
            }
        )
    return pd.DataFrame(rows)[list(REGIME_COLUMNS)]


def exchange_rate(table: pd.DataFrame) -> Mapping[str, float]:
    """Hires a year bought per agent added to the payroll, across a whole trade table.

    One number for the ladder rather than per rung, because the per-rung figures are integers of a
    search and the slope between the ends is what a decision is made on.

    Args:
        table: A frame from :func:`trade_table`.

    Returns:
        The change in payroll, the change in hires, and the rate between them. The rate is ``nan``
        where the payroll does not move at all, which happens whenever the occupancy ceiling never
        binds - on a small queue there is **no trade to make**, and zero would say it was free.

    Raises:
        ValueError: If the table has fewer than two rows to take a slope across.
    """
    if len(table) < 2:
        raise ValueError("an exchange rate needs at least two plans to compare")
    # Signed from the first row to the last, so a ladder written from the loosest ceiling to the
    # tightest reads as "this many more people, this many fewer hires" - both positive.
    first, last = table.iloc[0], table.iloc[-1]
    people = float(last["staffed"] - first["staffed"])
    hires = float(first["hires_per_year"] - last["hires_per_year"])
    return {
        "extra_staffed": people,
        "fewer_hires_per_year": hires,
        "hires_per_agent": hires / people if people else float("nan"),
    }

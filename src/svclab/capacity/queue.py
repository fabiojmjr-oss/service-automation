"""What the queue needs, and what the business case said it would need.

An automation's headcount case is almost always one multiplication: this many contacts, that
containment rate, so this much less volume, so this many fewer agents. Every step is defensible
and the answer is wrong, for three reasons that compound.

**Agents do not scale with volume.** A queue's staffing is not linear in its load - it is Erlang's
formula, where the last few per cent of service level cost far more than the first. Removing forty
per cent of the contacts does not remove forty per cent of the agents.

**The volume that leaves is not the volume that stays.** A bot resolves the easy end, so the residue
carries a longer handling time than the average contact did. The load is volume times handling time,
and the business case moved only the first factor.

**And the automation adds contacts.** Every unresolved conversation that comes back is a second
contact in the same queue, arriving already annoyed and already explained once.

:func:`capacity_table` prices all three against :func:`promised_agents`, which is the
multiplication.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

from svclab.synth import CENTRE, CentreProfile

#: Columns of the capacity table, one row per policy.
CAPACITY_COLUMNS = (
    "policy",
    "human_sessions",
    "mean_handling_seconds",
    "offered_load",
    "agents_needed",
    "occupancy",
    "service_level",
    "agents_promised",
    "agents_missing",
)


def offered_load(sessions: float, mean_handling_seconds: float, period_seconds: float) -> float:
    """Erlangs of work arriving: sessions times handling time, over the period they arrive in.

    Args:
        sessions: Contacts a human has to handle in the period.
        mean_handling_seconds: Mean seconds each takes.
        period_seconds: Seconds the queue is staffed for.

    Returns:
        The offered load, in erlangs. A load of 12.0 is twelve agents' worth of work, which is not
        the same thing as twelve agents.

    Raises:
        ValueError: If the period is not positive, or either other argument is negative.
    """
    if period_seconds <= 0:
        raise ValueError(f"the period must be positive, got {period_seconds}")
    if sessions < 0 or mean_handling_seconds < 0:
        raise ValueError("sessions and handling time cannot be negative")
    return sessions * mean_handling_seconds / period_seconds


def erlang_b(agents: int, load: float) -> float:
    """Erlang's loss formula, by the recursion rather than the factorials.

    The recursion ``B(0) = 1``, ``B(n) = a B(n-1) / (n + a B(n-1))`` is exact and cannot overflow,
    which the closed form with its factorial of the agent count can and does.

    Args:
        agents: Servers.
        load: Offered load in erlangs.

    Returns:
        The probability an arrival finds every server busy, in a system with no queue.

    Raises:
        ValueError: If either argument is negative.
    """
    if agents < 0:
        raise ValueError(f"agents cannot be negative, got {agents}")
    if load < 0:
        raise ValueError(f"the load cannot be negative, got {load}")
    blocking = 1.0
    for position in range(1, agents + 1):
        blocking = load * blocking / (position + load * blocking)
    return blocking


def erlang_c(agents: int, load: float) -> float:
    """The probability a contact waits at all, from Erlang C.

    Computed from :func:`erlang_b`, which is the numerically safe route:
    ``C = B / (1 - rho (1 - B))`` with ``rho = a / agents``.

    Args:
        agents: Agents on the queue.
        load: Offered load in erlangs.

    Returns:
        The probability of waiting. Exactly 1.0 when the load is at or above the agent count,
        because then every arrival waits and the wait has no finite mean.

    Raises:
        ValueError: If there are no agents at all, which is not a queue.
    """
    if agents <= 0:
        raise ValueError(f"a queue needs at least one agent, got {agents}")
    if load >= agents:
        return 1.0
    blocking = erlang_b(agents, load)
    return blocking / (1.0 - (load / agents) * (1.0 - blocking))


def service_level(
    agents: int, load: float, mean_handling_seconds: float, target_seconds: float
) -> float:
    """Share of contacts answered inside the target wait.

    The standard M/M/c result: a contact waits with probability ``C``, and the wait it then faces is
    exponential with mean ``handling / (agents - load)``.

    Args:
        agents: Agents on the queue.
        load: Offered load in erlangs.
        mean_handling_seconds: Mean handling time.
        target_seconds: The wait to be answered inside.

    Returns:
        The service level. Zero when the load is at or above the agent count, which is the honest
        answer for a queue with no steady state rather than a number from an extrapolation.

    Raises:
        ValueError: If the target is negative or the handling time is not positive.
    """
    if target_seconds < 0:
        raise ValueError(f"the target cannot be negative, got {target_seconds}")
    if mean_handling_seconds <= 0:
        raise ValueError(f"the handling time must be positive, got {mean_handling_seconds}")
    if load >= agents:
        return 0.0
    waiting = erlang_c(agents, load)
    rate = (agents - load) * target_seconds / mean_handling_seconds
    return 1.0 - waiting * math.exp(-rate)


def occupancy(agents: int, load: float) -> float:
    """Share of an agent's staffed time spent handling contacts.

    Reported next to every agent count here because it is the number that decides whether a plan is
    humane. A queue can hit its service level at an occupancy no team survives.

    Raises:
        ValueError: If there are no agents at all.
    """
    if agents <= 0:
        raise ValueError(f"a queue needs at least one agent, got {agents}")
    return load / agents


def agents_for(
    load: float,
    mean_handling_seconds: float,
    target_seconds: float,
    target_service_level: float,
    ceiling: int = 10_000,
) -> int:
    """The smallest number of agents that reaches a service level.

    Searched upwards from the load rather than solved, because the service level is a step function
    of an integer and rounding a continuous solution lands on the wrong side of it about half the
    time.

    Args:
        load: Offered load in erlangs.
        mean_handling_seconds: Mean handling time.
        target_seconds: The wait to be answered inside.
        target_service_level: The share to answer inside it.
        ceiling: Where to stop searching.

    Returns:
        The agent count.

    Raises:
        ValueError: If the target service level is not strictly between zero and one, or if the
            ceiling is reached - which means the plan asked for something this load cannot buy.
    """
    if not 0.0 < target_service_level < 1.0:
        raise ValueError(
            f"a service level has to be between zero and one, got {target_service_level}"
        )
    agents = max(1, math.floor(load) + 1)
    while agents <= ceiling:
        reached = service_level(agents, load, mean_handling_seconds, target_seconds)
        if reached >= target_service_level:
            return agents
        agents += 1
    raise ValueError(
        f"no agent count up to {ceiling} reaches a service level of {target_service_level} at a "
        f"load of {load}"
    )


def promised_agents(baseline_agents: int, containment: float) -> float:
    """The business case's answer: the baseline headcount, less the containment rate.

    Kept in the module it is wrong in, and deliberately returning a fraction rather than an integer,
    because rounding it would suggest the rounding was the error.

    Args:
        baseline_agents: Agents the queue needed before the bot.
        containment: The containment rate the deployment reported.

    Returns:
        Agents the case promised.

    Raises:
        ValueError: If the containment rate is not a share.
    """
    if not 0.0 <= containment <= 1.0:
        raise ValueError(f"a containment rate has to be a share, got {containment}")
    return baseline_agents * (1.0 - containment)


def capacity_table(
    outcomes: Mapping[str, pd.DataFrame],
    containment: Mapping[str, float],
    baseline: str,
    centre: CentreProfile = CENTRE,
) -> pd.DataFrame:
    """What each policy's queue actually needs, against what its containment rate promised.

    Args:
        outcomes: One outcome frame per policy, from :func:`svclab.bot.run`.
        containment: The containment rate reported for each policy, which is what the promise was
            built on.
        baseline: The policy the promise is measured against - the arm with no bot.
        centre: The centre's declared shape, for the staffed hours and the service level target.

    Returns:
        A frame with the columns in :data:`CAPACITY_COLUMNS`, one row per policy.

    Raises:
        KeyError: If the baseline policy is not among the outcomes, or a policy has no containment
            rate to be judged against.
    """
    if baseline not in outcomes:
        raise KeyError(f"{baseline!r} is not among the policies: {sorted(outcomes)}")
    missing = set(outcomes) - set(containment)
    if missing:
        raise KeyError(f"no containment rate supplied for {sorted(missing)}")

    period = centre.days * centre.operating_hours_per_day * 3600.0

    def needed(frame: pd.DataFrame) -> tuple[float, float, float, int]:
        human = frame[frame["handled_by_human"].to_numpy(dtype=bool)]
        sessions = float(len(human))
        mean_seconds = float(human["human_seconds"].mean())
        load = offered_load(sessions, mean_seconds, period)
        agents = agents_for(
            load, mean_seconds, centre.target_answer_seconds, centre.target_service_level
        )
        return sessions, mean_seconds, load, agents

    _, _, _, baseline_agents = needed(outcomes[baseline])
    rows = []
    for name, frame in outcomes.items():
        sessions, mean_seconds, load, agents = needed(frame)
        promised = promised_agents(baseline_agents, containment[name])
        rows.append(
            {
                "policy": name,
                "human_sessions": sessions,
                "mean_handling_seconds": mean_seconds,
                "offered_load": load,
                "agents_needed": agents,
                "occupancy": occupancy(agents, load),
                "service_level": service_level(
                    agents, load, mean_seconds, centre.target_answer_seconds
                ),
                "agents_promised": promised,
                "agents_missing": agents - promised,
            }
        )
    return pd.DataFrame(rows)[list(CAPACITY_COLUMNS)]


#: How far past the agent count the birth-death chain is summed before the tail is declared
#: negligible. The abandonment rate makes the tail decay geometrically, so this is generous rather
#: than tuned - and the tail's own mass is asserted to be under the tolerance before any figure is
#: returned.
QUEUE_STATES = 4_000

#: Mass the truncated tail may carry before the answer is refused rather than rounded.
TAIL_TOLERANCE = 1e-12

#: Columns of the table that prices a staffing level under both models.
IMPATIENCE_COLUMNS = (
    "agents",
    "offered_load",
    "erlang_c_service_level",
    "erlang_c_stable",
    "abandonment",
    "answered_share",
    "effective_load",
    "occupancy",
)


def _queue_distribution(
    agents: int, load: float, patience_mean: float, handling_mean: float
) -> np.ndarray:
    """Stationary distribution of the M/M/c+M chain, states 0 upwards.

    A birth-death chain with arrivals at ``lambda`` throughout, service at ``k mu`` below the agent
    count and ``c mu + j theta`` above it, where ``theta`` is the impatience rate. The product form
    is exact and needs no matrix: each state's unnormalised weight is the previous one times the
    arrival rate over that state's departure rate.

    Unlike Erlang C this has a stationary distribution **at any load**, because impatience removes
    work the agents cannot. That is the whole reason the model exists.
    """
    service = load / handling_mean  # arrival rate, since load = arrival rate * handling time
    per_agent = 1.0 / handling_mean
    impatience = 1.0 / patience_mean
    weights = np.empty(QUEUE_STATES + 1, dtype=float)
    weights[0] = 1.0
    for state in range(1, QUEUE_STATES + 1):
        if state <= agents:
            departure = state * per_agent
        else:
            departure = agents * per_agent + (state - agents) * impatience
        weights[state] = weights[state - 1] * service / departure
        # A queue whose weights climb for thousands of states overflows to infinity, and an
        # infinity makes the tail check below compare a nan and pass. Only the ratios matter, so
        # the accumulated weights are rescaled in place before that can happen. The first version
        # of this function had the tail check and not this line, and returned nan for an extreme
        # queue instead of refusing it.
        if weights[state] > 1e250:
            weights[: state + 1] /= weights[state]
    total = float(weights.sum())
    share = float(weights[-1]) / total if np.isfinite(total) and total > 0 else float("inf")
    if not np.isfinite(total) or total <= 0 or share > TAIL_TOLERANCE:
        raise ValueError(
            f"the queue's tail still carries {share:.2e} of the distribution at {QUEUE_STATES} "
            f"states, so this load and patience are outside what this model will report on"
        )
    return weights / total


def abandonment(agents: int, load: float, patience_mean: float, handling_mean: float) -> float:
    """Share of arrivals that give up before an agent answers, from Erlang A.

    Erlang C has no answer at a load at or above the agent count: it assumes infinite patience, so
    the queue grows without bound and there is no steady state to report. Real queues do have a
    steady state there, and the mechanism is the customers leaving. This function is that mechanism.

    Args:
        agents: Agents on the queue.
        load: Offered load in erlangs.
        patience_mean: Mean seconds a waiting customer tolerates before abandoning.
        handling_mean: Mean handling seconds.

    Returns:
        The share of arrivals that abandon. Zero at a vanishing load, and rising towards one as the
        load outgrows the agents.

    Raises:
        ValueError: If there are no agents, or either mean is not positive.
    """
    if agents <= 0:
        raise ValueError(f"a queue needs at least one agent, got {agents}")
    if patience_mean <= 0 or handling_mean <= 0:
        raise ValueError("the patience and handling means must both be positive")
    if load < 0:
        raise ValueError(f"the load cannot be negative, got {load}")
    if load == 0:
        return 0.0
    distribution = _queue_distribution(agents, load, patience_mean, handling_mean)
    waiting = np.arange(len(distribution)) - agents
    queued = np.where(waiting > 0, waiting, 0.0)
    # Abandonments per unit time, over arrivals per unit time. The arrival rate is the load divided
    # by the handling time, which is how the load was formed in the first place.
    leaving = float((distribution * queued).sum() / patience_mean)
    arriving = load / handling_mean
    return leaving / arriving


def impatience_table(
    agent_counts: tuple[int, ...],
    load: float,
    patience_mean: float,
    handling_mean: float,
    target_seconds: float,
) -> pd.DataFrame:
    """Each staffing level under both models, so the disagreement is on one screen.

    Args:
        agent_counts: Staffing levels to price.
        load: Offered load in erlangs.
        patience_mean: Mean seconds a waiting customer tolerates.
        handling_mean: Mean handling seconds.
        target_seconds: The wait Erlang C's service level is measured against.

    Returns:
        A frame with the columns in :data:`IMPATIENCE_COLUMNS`. ``erlang_c_stable`` is false
        wherever Erlang C has nothing to say, which is exactly where a business case most wants an
        answer.

    Raises:
        ValueError: If no staffing levels are supplied.
    """
    if not agent_counts:
        raise ValueError("there are no staffing levels to price")
    rows = []
    for agents in agent_counts:
        stable = load < agents
        leaving = abandonment(agents, load, patience_mean, handling_mean)
        effective = load * (1.0 - leaving)
        rows.append(
            {
                "agents": agents,
                "offered_load": load,
                "erlang_c_service_level": (
                    service_level(agents, load, handling_mean, target_seconds) if stable else 0.0
                ),
                "erlang_c_stable": stable,
                "abandonment": leaving,
                "answered_share": 1.0 - leaving,
                "effective_load": effective,
                "occupancy": effective / agents,
            }
        )
    return pd.DataFrame(rows)[list(IMPATIENCE_COLUMNS)]


def load_with_repeats(
    agents: int,
    base_load: float,
    patience_mean: float,
    handling_mean: float,
    repeat_share: float,
    tolerance: float = 1e-12,
    limit: int = 500,
) -> dict[str, float]:
    """The load a queue settles at once the customers it turned away come back.

    An abandoned contact is not a contact that went away. Some share of the people who gave up
    waiting come back, and their return is load - which raises abandonment, which raises the return.
    The settled load is the fixed point of

        load = base_load * (1 + repeat_share * abandonment(load))

    solved by iterating it, because each step is a monotone map of the previous one and the
    iteration is the honest way to show that it converges rather than asserting that it does.

    Args:
        agents: Agents on the queue.
        base_load: Load before any repeats.
        patience_mean: Mean seconds a waiting customer tolerates.
        handling_mean: Mean handling seconds.
        repeat_share: Share of abandoners who come back.
        tolerance: How close two iterations must be before the answer is settled.
        limit: Iterations before the search is declared not to converge.

    Returns:
        A mapping with the settled load, the abandonment at it, the extra load the repeats added,
        and the iterations it took.

    Raises:
        ValueError: If the repeat share is not a share, or the iteration does not settle - which is
        a real answer about a queue rather than a numerical failure, and says so.
    """
    if not 0.0 <= repeat_share <= 1.0:
        raise ValueError(f"the repeat share has to be a share, got {repeat_share}")
    load = base_load
    for step in range(1, limit + 1):
        leaving = abandonment(agents, load, patience_mean, handling_mean)
        updated = base_load * (1.0 + repeat_share * leaving)
        if abs(updated - load) < tolerance:
            return {
                "settled_load": updated,
                "abandonment": leaving,
                "added_load": updated - base_load,
                "iterations": float(step),
            }
        load = updated
    raise ValueError(
        f"the load did not settle in {limit} iterations; at {agents} agents this queue feeds "
        f"itself faster than it clears"
    )

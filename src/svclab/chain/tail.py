"""The contact that came back twice, and the three rankings a containment rate reverses.

Waves 1 to 5 allowed an unresolved contact **one** return. Every one of them named that as the
reason its figures were an underestimate: wave 1 said a containment rate becomes a permanent queue
through the geometric tail, and then truncated that tail at one term. This module runs the chain.

Two things came out of it that the truncation was hiding, and they point in opposite directions.

**The tail here is short, and there is a closed form that says why.** A contact reopens when the
customer comes back *and* the human failed, so the sessions one unresolved contact generates are a
geometric series in ``r = P(return) * P(human does not resolve)``. At this centre's declared curves
that is **0.0429**, and the series is 1.0448 however many attempts are allowed. The geometric tail
wave 1 feared is not a property of returning customers. It is a property of an operation that keeps
failing them, and this one does not.

**And the chain exposes a third ranking of the policies, which no rate contains.** Containment ranks
`patient` first. Resolution ranks it last. **Days to resolution** ranks it last too, and by a wider
margin than resolution does - a customer whose problem is eventually fixed after two returns and
three days has been served worse than the rate says, and better than nothing says.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from svclab.bot import REPEAT_SESSION_OFFSET
from svclab.synth import CENTRE, CentreProfile

#: Columns of the per-attempt table.
ATTEMPT_COLUMNS = (
    "attempt",
    "sessions",
    "resolved",
    "resolution_rate",
    "cumulative_resolution",
    "human_hours",
)

#: Columns of the table comparing a chain against a single return.
CHAIN_COLUMNS = (
    "policy",
    "sessions",
    "sessions_per_contact",
    "first_attempt_resolution",
    "eventual_resolution",
    "human_hours",
    "extra_sessions",
    "extra_hours_share",
)

#: Columns of the closed-form tail table.
TAIL_COLUMNS = ("reopen_rate", "two_attempts", "four_attempts", "unbounded", "truncation_error")

#: Columns of the time-to-resolution table.
TIME_COLUMNS = (
    "policy",
    "containment",
    "eventual_resolution",
    "hours_to_resolution",
    "days_to_resolution",
    "share_beyond_first",
    "share_beyond_second",
)


def attempts_of(outcomes: pd.DataFrame) -> pd.Series:
    """Which attempt each session was, recovered from its id.

    A session id is its contact's id plus the repeat offset times the attempt minus one, so the
    attempt is recoverable by integer division rather than stored. One representation of a fact
    beats two that can disagree.
    """
    return outcomes["session"] // REPEAT_SESSION_OFFSET + 1


def attempt_table(outcomes: pd.DataFrame, contacts: int | None = None) -> pd.DataFrame:
    """One row per attempt: how many sessions it held and how many of them ended it.

    Args:
        outcomes: An outcome frame from :func:`svclab.bot.run`.
        contacts: Contacts behind those sessions, for the cumulative column. Defaults to the number
            of distinct contacts in the frame.

    Returns:
        A frame with the columns in :data:`ATTEMPT_COLUMNS`.

    Raises:
        ValueError: If the outcome frame is empty.
    """
    if outcomes.empty:
        raise ValueError("there are no sessions to attribute to attempts")
    total = float(contacts if contacts is not None else outcomes["contact"].nunique())
    frame = outcomes.assign(
        attempt=attempts_of(outcomes), resolved=outcomes["resolved"].astype(int)
    )
    grouped = frame.groupby("attempt").agg(
        sessions=("session", "size"),
        resolved=("resolved", "sum"),
        human_hours=("human_seconds", "sum"),
    )
    grouped["human_hours"] = grouped["human_hours"] / 3600.0
    grouped["resolution_rate"] = grouped["resolved"] / grouped["sessions"]
    grouped["cumulative_resolution"] = grouped["resolved"].cumsum() / total
    return grouped.reset_index()[list(ATTEMPT_COLUMNS)]


def chain_table(
    single: Mapping[str, pd.DataFrame],
    chained: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """What allowing the chain costs each policy, against allowing one return.

    Args:
        single: Outcome frames by policy name, run with the single return of waves 1 to 5.
        chained: Outcome frames by the same names, run with the declared chain.

    Returns:
        A frame with the columns in :data:`CHAIN_COLUMNS`, one row per policy.

    Raises:
        KeyError: If the two mappings do not carry the same policies.
    """
    if set(single) != set(chained):
        raise KeyError(f"single covers {sorted(single)} and chained {sorted(chained)}")
    rows = []
    for policy, frame in chained.items():
        before = single[policy]
        first = frame[~frame["is_repeat"]]
        rows.append(
            {
                "policy": policy,
                "sessions": int(len(frame)),
                "sessions_per_contact": len(frame) / float(frame["contact"].nunique()),
                "first_attempt_resolution": float(first["resolved"].astype(float).mean()),
                "eventual_resolution": float(frame.groupby("contact")["resolved"].max().mean()),
                "human_hours": float(frame["human_seconds"].sum() / 3600.0),
                "extra_sessions": int(len(frame) - len(before)),
                "extra_hours_share": float(
                    frame["human_seconds"].sum() / before["human_seconds"].sum() - 1.0
                ),
            }
        )
    return pd.DataFrame(rows)[list(CHAIN_COLUMNS)]


def reopen_rate(repeat_share: float, human_resolution: float) -> float:
    """The probability an unresolved contact produces another session.

    Both things have to happen: the customer comes back, and the human fails again. The product is
    what governs the tail, which is why an operation can have a high repeat rate and no tail at
    all.

    Args:
        repeat_share: Probability an unresolved contact's customer returns.
        human_resolution: Probability a human resolves the contact.

    Returns:
        The reopen rate.

    Raises:
        ValueError: If either argument is outside the unit interval.
    """
    for name, value in (("repeat_share", repeat_share), ("human_resolution", human_resolution)):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} is a probability, not {value}")
    return repeat_share * (1.0 - human_resolution)


def sessions_per_unresolved(reopen: float, attempts: int) -> float:
    """Sessions one unresolved contact generates, in closed form.

    The truncated geometric series ``(1 - r**n) / (1 - r)``, and the three corners it has to pass:
    one attempt is one session whatever ``r`` is, ``r`` of zero is one session however many attempts
    are allowed, and ``r`` of one is exactly ``n`` - a customer who always returns to an operation
    that never resolves uses every attempt there is.

    Args:
        reopen: The reopen rate, from :func:`reopen_rate`.
        attempts: Attempts the chain allows, the original included.

    Returns:
        The expected number of sessions.

    Raises:
        ValueError: If the rate is outside the unit interval or the attempts below one.
    """
    if not 0.0 <= reopen <= 1.0:
        raise ValueError(f"a reopen rate is a probability, not {reopen}")
    if attempts < 1:
        raise ValueError(f"a contact has at least one attempt, not {attempts}")
    if reopen == 1.0:
        return float(attempts)
    return float((1.0 - reopen**attempts) / (1.0 - reopen))


def tail_table(rates: tuple[float, ...], attempts: int = 4) -> pd.DataFrame:
    """The tail at a range of reopen rates, and what truncating it at one return costs.

    Args:
        rates: Reopen rates to price.
        attempts: The chain length to compare against two attempts and against no limit.

    Returns:
        A frame with the columns in :data:`TAIL_COLUMNS`, one row per rate. ``truncation_error`` is
        how much a single return understates the unbounded series, as a share.

    Raises:
        ValueError: If no rates are given.
    """
    if not rates:
        raise ValueError("there are no reopen rates to price")
    rows = []
    for rate in rates:
        two = sessions_per_unresolved(rate, 2)
        unbounded = float("inf") if rate == 1.0 else 1.0 / (1.0 - rate)
        rows.append(
            {
                "reopen_rate": rate,
                "two_attempts": two,
                "four_attempts": sessions_per_unresolved(rate, attempts),
                "unbounded": unbounded,
                "truncation_error": unbounded / two - 1.0,
            }
        )
    return pd.DataFrame(rows)[list(TAIL_COLUMNS)]


def time_table(
    chained: Mapping[str, pd.DataFrame],
    centre: CentreProfile = CENTRE,
) -> pd.DataFrame:
    """How long each policy takes to resolve a contact, in the currency the customer pays.

    A return lands inside the declared repeat window, so a contact resolved on its third attempt
    has waited two windows. Contacts that never resolve are excluded rather than counted as
    infinite: they are a different failure, and mixing the two would hide both.

    Args:
        chained: Outcome frames by policy name, run with the chain.
        centre: The centre's declared shape, for the repeat window.

    Returns:
        A frame with the columns in :data:`TIME_COLUMNS`, one row per policy.

    Raises:
        ValueError: If a policy's frame has no resolved contact in it.
    """
    rows = []
    for policy, frame in chained.items():
        first = frame[~frame["is_repeat"]]
        contained = first["outcome"].isin(("resolved-by-bot", "abandoned"))
        resolved = frame[frame["resolved"]]
        if resolved.empty:
            raise ValueError(f"the {policy!r} policy resolved nothing, so it has no time to report")
        closed_at = (
            resolved.assign(attempt=attempts_of(resolved)).groupby("contact")["attempt"].min()
        )
        waited = (closed_at.to_numpy(dtype=float) - 1.0) * centre.repeat_window_hours
        rows.append(
            {
                "policy": policy,
                "containment": float(contained.mean()),
                "eventual_resolution": float(frame.groupby("contact")["resolved"].max().mean()),
                "hours_to_resolution": float(np.mean(waited)),
                "days_to_resolution": float(np.mean(waited) / 24.0),
                "share_beyond_first": float((closed_at > 1).mean()),
                "share_beyond_second": float((closed_at > 2).mean()),
            }
        )
    return pd.DataFrame(rows)[list(TIME_COLUMNS)]

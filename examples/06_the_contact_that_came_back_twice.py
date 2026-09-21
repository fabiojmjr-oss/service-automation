"""The tail five waves truncated, run to its declared end.

Run:
    python examples/06_the_contact_that_came_back_twice.py

Waves 1 to 5 allowed an unresolved contact one return, and each of them said that made its figures
an underestimate. This example allows four attempts and asks what the truncation hid: how long the
chain actually is, the closed form that says why, what it costs each policy, and the third ranking
of the four policies - the one with time in it.

The default chain is still a single return, so nothing published moves. That is checked here by hash
before anything else is printed.
"""

from __future__ import annotations

import hashlib

import pandas as pd

from svclab.bot import POLICIES, THREE_TURNS, run
from svclab.chain import (
    attempt_table,
    chain_table,
    reopen_rate,
    sessions_per_unresolved,
    tail_table,
    time_table,
)
from svclab.synth import CHAIN, INTENTS, SINGLE_RETURN, generate_dataset

#: Reopen rates to price the truncation at, from this centre's own to an operation in trouble.
RATES = (0.05, 0.10, 0.20, 0.30, 0.50, 0.70)


def fingerprint(frame: pd.DataFrame) -> str:
    """A hash of a frame's contents, for showing identity rather than similarity."""
    return hashlib.sha256(
        pd.util.hash_pandas_object(frame, index=True).to_numpy().tobytes()
    ).hexdigest()[:16]


def main() -> None:
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)

    data = generate_dataset()
    treated = data.contacts[~data.contacts["holdout"]]
    single = {policy.name: run(treated, policy) for policy in POLICIES}
    chained = {
        policy.name: run(treated, policy, chain=CHAIN, draws=data.return_draws)
        for policy in POLICIES
    }

    print("ZERO: THE DEFAULT STILL IS WHAT THE EARLIER WAVES PUBLISHED")
    print("=" * 98)
    plain = fingerprint(single["three-turns"])
    declared = fingerprint(run(treated, THREE_TURNS, chain=SINGLE_RETURN))
    print(f"   run(contacts, policy)                        -> {plain}")
    print(f"   run(contacts, policy, chain=SINGLE_RETURN)   -> {declared}")
    print(f"   identical: {plain == declared}")
    print()

    print("ONE: THE CHAIN IS REAL, AND IT IS SHORT")
    print("=" * 98)
    attempts = attempt_table(chained["three-turns"], len(treated))
    print(attempts.to_string(index=False))
    print()
    third = int(attempts.loc[attempts["attempt"] == 3, "sessions"].iloc[0])
    fourth = int(attempts.loc[attempts["attempt"] == 4, "sessions"].iloc[0])
    eventual = float(attempts["cumulative_resolution"].iloc[-1])
    before = float(single["three-turns"].groupby("contact")["resolved"].max().mean())
    print(
        f"   {third} contacts need a third attempt and {fourth} need a fourth. Eventual resolution"
    )
    print(
        f"   goes from {before:.4f} to {eventual:.4f} - {(eventual - before) * 100:.2f} points the"
    )
    print("   earlier waves were not counting.")
    print()

    print("TWO: BECAUSE A TAIL NEEDS AN OPERATION THAT KEEPS FAILING")
    print("=" * 98)
    repeat = sum(profile.repeat_when_unresolved * profile.share for profile in INTENTS)
    resolution = float(treated["human_resolves"].mean())
    rate = reopen_rate(repeat, resolution)
    print("   A contact reopens only if the customer returns AND the human failed again:")
    print(f"   r = {repeat:.4f} x (1 - {resolution:.4f}) = {rate:.4f}")
    print(f"   which is {sessions_per_unresolved(rate, CHAIN.max_attempts):.4f} sessions per")
    print("   unresolved contact, however many attempts are allowed.")
    print()
    print(tail_table((round(rate, 4), *RATES)).to_string(index=False))
    print()
    print("   The last column is the price of wave 1's truncation at each possible operation. Here")
    print("   it was almost free. At a reopen rate of 0.5 it would have been a third of the")
    print("   sessions. So the geometric tail is not a property of customers who return - it is a")
    print("   property of an operation that keeps failing them, and the lever is the human's")
    print("   first-contact resolution rather than the customer's return rate.")
    print()

    print("THREE: AND THE CHAIN PUNISHES THE POLICY CONTAINMENT REWARDED")
    print("=" * 98)
    costs = chain_table(single, chained).set_index("policy")
    print(costs.to_string())
    print()
    worst = costs["extra_hours_share"].idxmax()
    best = costs["extra_hours_share"].idxmin()
    print(
        f"   {worst} pays {costs.loc[worst, 'extra_hours_share']:.2%} and {best} pays"
        f" {costs.loc[best, 'extra_hours_share']:.2%}: a policy that contains more leaves more"
    )
    print("   contacts unresolved, and an unresolved contact is the only thing a chain acts on.")
    print()

    print("FOUR: THE THIRD RANKING, AND THE ONE NOBODY REPORTS")
    print("=" * 98)
    times = time_table(chained).sort_values("containment").set_index("policy")
    print(times.to_string())
    print()
    slowest = times["days_to_resolution"].idxmax()
    quickest = times["days_to_resolution"].idxmin()
    ratio = float(times.loc[slowest, "days_to_resolution"]) / float(
        times.loc[quickest, "days_to_resolution"]
    )
    print(f"   Days to resolution is monotone in containment. {slowest} takes {ratio:.1f} times as")
    print(
        f"   long as {quickest}, and {float(times.loc[slowest, 'share_beyond_first']):.1%} of what"
    )
    print("   it eventually resolves is resolved on a later attempt.")
    print()
    print("   Three rankings of the same four policies now, best first:")
    for label, column, ascending in (
        ("containment     ", "containment", False),
        ("resolution      ", "eventual_resolution", False),
        ("days to resolve ", "days_to_resolution", True),
    ):
        order = times.sort_values(column, ascending=ascending).index.tolist()
        print(f"     {label} {', '.join(order)}")
    print()
    print(
        "   Containment is the exact reverse of both of the others. A rate has no time in it, and"
    )
    print("   three days is not a rounding error on a KPI: it is the complaint.")


if __name__ == "__main__":
    main()

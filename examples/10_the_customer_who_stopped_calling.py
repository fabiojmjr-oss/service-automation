"""The relief valve three waves leaned on, priced in the one currency the others cannot hold.

Run:
    python examples/10_the_customer_who_stopped_calling.py

Erlang A reaches a steady state because customers give up. An occupancy ceiling is satisfied by
understaffing because the customers who abandon keep occupancy down. The attrition loop's second
regime is reached by losing customers. Three times the note was that abandonment is the thing the
business is trying not to do, and three times there was no way to say how much of it happened.

This example gives a customer a declared chance of not coming back, measures the silence rule an
operation would use to notice as a gauge, and then shows the part that matters: losing customers
reduces the bill, and no metric in the first nine waves can see it.
"""

from __future__ import annotations

import pandas as pd

from svclab.bot import POLICIES, run
from svclab.churn import (
    departures,
    detection_by_frequency,
    detection_table,
    experience_of,
    policy_table,
    silence_flag,
    surviving,
    valve_table,
)
from svclab.synth import CHURN, generate_dataset

#: The abandonment rates earlier waves landed on: wave 3's stable queue, wave 8's crisis regime,
#: wave 7's occupancy-only plan, and wave 7's compliant one.
VALVE = (0.2923, 0.2100, 0.1434, 0.0356)

#: Agents between wave 3's six and wave 7's eleven, for the retention a headcount buys.
AGENTS_BETWEEN = 5

RULE = "=" * 100


def main() -> None:
    pd.set_option("display.width", 240)
    data = generate_dataset()
    month = data.contacts[~data.contacts["holdout"]]
    outcomes = {policy.name: run(month, policy) for policy in POLICIES}

    print(RULE)
    print("What the month left its customers with, under the policy wave 1 shipped")
    print(RULE)
    experience = experience_of(month, outcomes["three-turns"])
    shares = experience["experience"].value_counts(normalize=True)
    for name in ("abandoned", "unresolved", "resolved"):
        count = int((experience["experience"] == name).sum())
        print(f"  {name:11s} {count:>6,}  {shares[name]:.4f}")
    print(
        f"\n  Declared chances of not coming back: {CHURN.leave_after_abandoned:.3f} after "
        f"abandoning, {CHURN.leave_after_unresolved:.3f} after an unresolved\n  contact, "
        f"{CHURN.leave_after_resolved:.3f} after a resolved one."
    )

    left = departures(month, outcomes["three-turns"], data.churn_draws)
    kept = surviving(month, left)
    flagged = silence_flag(kept)

    print()
    print(RULE)
    print("The churn rate an operation would actually have, measured as a gauge")
    print(RULE)
    gauge = detection_table(left, flagged).iloc[0]
    print(
        f"  customers {int(gauge['customers']):>7,}   actually left {int(gauge['left']):>6,}"
        f"   flagged by silence {int(gauge['flagged']):>6,}"
    )
    print(
        f"  sensitivity {gauge['sensitivity']:.4f}   specificity {gauge['specificity']:.4f}"
        f"   Youden {gauge['youden']:.4f}   precision {gauge['precision']:.4f}"
    )
    print(
        f"\n  {1 - gauge['precision']:.2%} of the customers this dashboard flags did not "
        "leave, and because the\n  Youden index is the factor a binary assessor multiplies a "
        f"difference by, a comparison of\n  two policies on this rate reports "
        f"{gauge['youden']:.2%} of the real gap. Wave 2's quality panel\n  transmitted 69.45%; "
        "this transmits a fifth of that."
    )

    print()
    print(RULE)
    print("And the rule is useless at both ends, for opposite reasons")
    print(RULE)
    bands = detection_by_frequency(left, flagged)
    print(bands.to_string(index=False))
    print(
        "\n  The index peaks in the middle. At one contact the rule cannot see the stayers -\n"
        "  being silent is what one contact means. At four or more it cannot see the leavers,\n"
        "  because a frequent customer who leaves late still has a recent contact. A silence\n"
        "  window is a statement about contact frequency before it is one about leaving."
    )

    print()
    print(RULE)
    print("What each policy costs in customers, beside what it costs in hours")
    print(RULE)
    table = policy_table(month, outcomes, data.churn_draws)
    print(table.to_string(index=False))
    by_policy = table.set_index("policy")
    worst, best = by_policy["left"].idxmax(), by_policy["left"].idxmin()
    print(
        f"\n  The hours saved are monotone in the customers lost: {worst} drives away "
        f"{int(by_policy.loc[worst, 'left']):,} people and\n  books "
        f"{by_policy.loc[worst, 'hours_saved']:.2f} hours of saving, against "
        f"{int(by_policy.loc[best, 'left']):,} and {by_policy.loc[best, 'hours_saved']:.2f} for "
        f"{best}. Every one of\n  those hours arrives on the report as efficiency."
    )
    drift = (
        by_policy.loc["three-turns", "session_containment"]
        - by_policy.loc["three-turns", "session_containment_after"]
    )
    print(
        f"\n  And containment cannot see it: recomputed on the surviving contacts it moves "
        f"by {drift:.5f},\n  because the numerator and the denominator fall together. The ranking "
        "by customers lost is\n  the containment ranking exactly - a fourth ranking of the same "
        "four policies."
    )
    print(
        f"\n  Exchange rate: one hour of saved handling costs "
        f"{60 / by_policy.loc[worst, 'minutes_per_customer_lost']:.2f} customers on {worst}."
    )

    print()
    print(RULE)
    print("The valve three waves used as relief, priced in people")
    print(RULE)
    valve = valve_table(VALVE, len(month), int(len(left)))
    print(valve.to_string(index=False))
    indexed = valve.set_index("abandonment")
    gap = float(indexed.loc[VALVE[0], "customers_lost"] - indexed.loc[VALVE[-1], "customers_lost"])
    print(
        f'\n  Wave 3\'s "perfectly stable" six agents spend {gap:.2f} more customers a month than '
        f"the plan\n  that meets its ceilings. Five agents buy that back: "
        f"{gap / AGENTS_BETWEEN:.2f} customers a month per agent."
    )
    print(
        "\n  Wave 8 priced an extra agent at 12 person-months against 2.33 returned and said the "
        "case\n  rests on what a departure costs outside the queue. That is the quantity. There is "
        "still no\n  money in this repository, so the price stays with the reader - which is where "
        "it belongs."
    )

    print()
    print(RULE)
    print("And the unit was wrong for nine waves")
    print(RULE)
    lost_contacts = float(by_policy.loc["three-turns", "contacts_lost"])
    print(
        f"  Only {int(lost_contacts):,} contacts disappear - {lost_contacts / len(month):.2%} "
        "of the month. A customer who\n  leaves on day three loses twenty-seven days here and the "
        "rest of their life in an operation.\n  Seconds, sessions, agents and hours are monthly "
        "quantities. Customers are not."
    )


if __name__ == "__main__":
    main()

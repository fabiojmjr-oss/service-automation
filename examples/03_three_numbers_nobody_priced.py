"""Three decisions the first two waves took implicitly, priced.

Run:
    python examples/03_three_numbers_nobody_priced.py

Wave 1's `guarded` policy refused two intents on the strength of a label, and never asked what the
label was worth. Wave 1's capacity plan assumed nobody gives up waiting. And both waves compared
policies on the whole account without asking what a real test of them would need. This example
prices all three.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from svclab.bot import GUARDED, THREE_TURNS, run
from svclab.capacity import abandonment, impatience_table, load_with_repeats
from svclab.experiment import (
    actual_alpha,
    design_effect,
    intracluster_correlation,
    sizing_table,
)
from svclab.routing import best_by, calibrated_threshold, cost_curve, cost_of, defer_below
from svclab.synth import ROUTING, generate_dataset

#: The load, handling time and patience wave 1's `three-turns` queue arrives with.
LOAD = 7.5845
HANDLING = 512.25
PATIENCE = 240.0
REPEAT_SHARE = 0.55


def main() -> None:
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    data = generate_dataset()
    treated = data.contacts[~data.contacts["holdout"]]

    print("ONE: THE THRESHOLD THE ROUTER WAS NEVER GIVEN")
    print("=" * 98)
    print("   A classifier reports a label and a confidence. Below some confidence the contact")
    print("   should")
    print("   go to a human instead - and that number is normally chosen by maximising accuracy.")
    print()
    thresholds = tuple(round(value, 2) for value in np.arange(0.30, 0.71, 0.01))
    curve = cost_curve(treated, data.routing_scores, THREE_TURNS, thresholds)
    accuracy = best_by(curve, "label_accuracy", True)
    cost = best_by(curve, "seconds_per_contact", False)
    indexed = curve.set_index("threshold")
    shown = curve[curve["threshold"].isin([0.35, accuracy, cost, 0.60, 0.70])]
    print(shown.round(4).to_string(index=False))
    print()
    gap = float(indexed.loc[accuracy, "seconds_per_contact"]) - float(
        indexed.loc[cost, "seconds_per_contact"]
    )
    print(f"   Accuracy is maximised at {accuracy:.2f} and cost is minimised at {cost:.2f}.")
    print(f"   Tuning on accuracy costs {gap:.4f} seconds a contact, which is")
    print(f"   {gap * len(treated) / 3600:.2f} human hours over the month.")
    print()
    print("   Now per intent, because a misrouted complaint and a misrouted tracking question are")
    print("   not the same mistake:")
    print()

    def price(threshold: float | dict[str, float]) -> tuple[float, float, float, float]:
        routed = defer_below(treated, data.routing_scores, threshold)
        outcomes = run(routed, THREE_TURNS)
        measured = cost_of(outcomes, routed)
        total = measured["human_seconds"] + measured["misroute_seconds"] + measured["defer_seconds"]
        first = outcomes[~outcomes["is_repeat"]]
        return (
            total / len(routed),
            float(first["resolved"].mean()),
            measured["misroutes"],
            measured["deferred"],
        )

    grid = tuple(round(value, 2) for value in np.arange(0.0, 1.01, 0.02))
    swept: dict[str, float] = {}
    rows = []
    for intent, seconds in ROUTING.misroute_seconds.items():
        subset = treated[treated["intent"] == intent]
        costs = {}
        for candidate in grid:
            routed = defer_below(subset, data.routing_scores, candidate)
            measured = cost_of(run(routed, THREE_TURNS), routed)
            costs[candidate] = (
                measured["human_seconds"] + measured["misroute_seconds"] + measured["defer_seconds"]
            ) / len(routed)
        swept[intent] = min(costs, key=lambda key: costs[key])
        rows.append(
            {
                "intent": intent,
                "misroute_seconds": seconds,
                "swept_threshold": swept[intent],
                "closed_form": calibrated_threshold(ROUTING.defer_seconds, seconds),
            }
        )
    print(pd.DataFrame(rows).round(4).to_string(index=False))
    print()
    formula = {
        intent: calibrated_threshold(ROUTING.defer_seconds, seconds)
        for intent, seconds in ROUTING.misroute_seconds.items()
    }
    comparison = []
    for label, rule in (
        (f"one threshold at {cost:.2f}", cost),
        ("per intent, swept", swept),
        ("per intent, closed form", formula),
    ):
        seconds, resolution, misroutes, deferred = price(rule)
        comparison.append(
            {
                "rule": label,
                "seconds_per_contact": seconds,
                "resolution": resolution,
                "misroutes": misroutes,
                "deferred": deferred,
            }
        )
    table = pd.DataFrame(comparison)
    print(table.round(4).to_string(index=False))
    print()
    single = float(table["seconds_per_contact"].iloc[0])
    per_intent = float(table["seconds_per_contact"].iloc[1])
    closed = float(table["seconds_per_contact"].iloc[2])
    saved = single - per_intent
    print(f"   Sweeping per intent saves {saved:.4f} seconds a contact against the best single")
    print(f"   number - {saved * len(treated) / 3600:.1f} human hours a month.")
    print()
    print(f"   And the closed form costs {closed / single - 1:+.1%} against that single threshold.")
    print("   It is not a wrong formula: on a score that IS the probability the label is right, it")
    print("   is")
    print("   exactly optimal. This score is a margin, so the formula's ordering of the intents is")
    print("   right and every level is far too high. Calibration is the missing step.")
    bought = float(table["resolution"].iloc[2])
    swept_resolution = float(table["resolution"].iloc[1])
    print(f"   It does buy resolution: {bought:.4f} against {swept_resolution:.4f}, for")
    print(f"   {closed - per_intent:.1f} seconds a contact.")

    print("\n" + "=" * 98)
    print("TWO: THE PATIENCE THE CAPACITY PLAN ASSUMED WAS INFINITE")
    print("=" * 98)
    print("   Erlang C has no answer below eight agents at this load: the queue grows without")
    print("   bound,")
    print("   there is no steady state, and the service level comes back as zero. Real queues do")
    print("   have a steady state there. The mechanism is the customers leaving.")
    print()
    print(
        impatience_table((5, 6, 7, 8, 9, 10, 11, 12, 14), LOAD, PATIENCE, HANDLING, 20.0)
        .round(4)
        .to_string(index=False)
    )
    print()
    six = abandonment(6, LOAD, PATIENCE, HANDLING)
    eleven = abandonment(11, LOAD, PATIENCE, HANDLING)
    print("   Wave 1 said the business case promised 5.51 agents and the queue needs 11. At six")
    print(f"   agents this queue is perfectly stable - with {six:.2%} of the customers abandoning.")
    print("   The promised headcount is not impossible. It is a decision to answer seven contacts")
    print("   in")
    print(f"   ten. At eleven agents abandonment is {eleven:.2%}.")
    print()
    print("   The control that ties the two models together: lengthen the patience and Erlang A")
    print("   becomes Erlang C.")
    for patience in (600.0, 6_000.0, 60_000.0, 6_000_000.0):
        print(f"     patience {patience:>10,.0f}s   abandonment")
        print(f"   {abandonment(14, 10.1268, patience, 395.43):.8f}")
    print()
    print("   And the abandoned contacts come back, so the queue feeds itself:")
    print()
    rows = []
    for agents in (6, 8, 11):
        settled = load_with_repeats(agents, LOAD, PATIENCE, HANDLING, REPEAT_SHARE)
        rows.append(
            {
                "agents": agents,
                "base_load": LOAD,
                "settled_load": settled["settled_load"],
                "added_by_repeats": settled["added_load"],
                "abandonment_at_the_fixed_point": settled["abandonment"],
                "iterations": settled["iterations"],
            }
        )
    settled_table = pd.DataFrame(rows)
    print(settled_table.round(4).to_string(index=False))
    print()
    worst = settled_table.iloc[0]
    best = settled_table.iloc[-1]
    print(
        f"   At six agents the repeats add"
        f" {float(worst['settled_load']) / LOAD - 1:.1%} more load and push abandonment from"
        f" {six:.2%}"
    )
    print(
        f"   to {float(worst['abandonment_at_the_fixed_point']):.2%}. At eleven they add"
        f" {float(best['settled_load']) / LOAD - 1:.1%} and settle at"
        f" {float(best['abandonment_at_the_fixed_point']):.2%}."
    )
    print("   The same mechanism, and at adequate staffing it is a rounding error.")

    print("\n" + "=" * 98)
    print("THREE: THE TEST NEITHER WAVE SIZED")
    print("=" * 98)
    three = run(treated, THREE_TURNS)
    guarded = run(treated, GUARDED)
    first_three = three[~three["is_repeat"]].copy()
    first_guarded = guarded[~guarded["is_repeat"]]
    first_three["resolved_num"] = first_three["resolved"].astype(float)
    first_three["human_num"] = first_three["handled_by_human"].astype(float)
    cluster_size = len(first_three) / first_three["customer"].nunique()
    customers = first_three["customer"].nunique()
    print(f"   {len(first_three):,} contacts from {customers:,} customers - {cluster_size:.4f}")
    print("   contacts each. One person's contacts are not two strangers'.")
    print()
    for outcome in ("resolved_num", "human_num"):
        icc = intracluster_correlation(first_three, "customer", outcome)
        print(
            f"     intra-cluster correlation of {outcome:<12} {icc:+.6f}"
            f"   design effect {design_effect(cluster_size, icc):.6f}"
        )
    print()
    print("   Approximately zero - and that is a fact about this generator, not about contact")
    print("   centres. Difficulty, patience and every other trait here are drawn per contact, so a")
    print("   customer is a label rather than a person. The estimator returning zero is a check on")
    print("   the estimator; the missing customer effect is a limitation in the roadmap.")
    print()
    guarded_rate = float(first_guarded["resolved"].mean())
    three_rate = float(first_three["resolved"].mean())
    print("   So the sizing prices assumed correlations instead. The comparison is wave 1's:")
    print(f"   guarded resolves {guarded_rate:.4f} against three-turns' {three_rate:.4f}.")
    print()
    scenarios = {
        "independent contacts": (cluster_size, 0.0),
        "correlation 0.05": (cluster_size, 0.05),
        "correlation 0.10": (cluster_size, 0.10),
        "correlation 0.20": (cluster_size, 0.20),
        "correlation 0.30": (cluster_size, 0.30),
        "total correlation": (cluster_size, 1.0),
    }
    sizing = sizing_table(scenarios, guarded_rate, three_rate, cluster_size)
    print(sizing.round(4).to_string(index=False))
    print()
    heavy = sizing.set_index("scenario").loc["correlation 0.30"]
    plain = sizing.set_index("scenario").loc["independent contacts"]
    print("   Read the last column before the others. A test that believes it is running at")
    print("   five per cent, on clusters of two with a correlation of 0.30, is really running")
    print(f"   at {float(heavy['actual_alpha']):.2%}.")
    print(
        f"   At total correlation it is"
        f" {float(sizing['actual_alpha'].iloc[-1]):.2%}: one result in six is a false positive on a"
    )
    print("   test that reported one in twenty.")
    print()
    inflation = float(heavy["contacts_per_arm"]) / float(plain["contacts_per_arm"]) - 1.0
    print(f"   And the sample: {inflation:+.1%} more contacts than the textbook says. With")
    print(f"   clusters averaging two the damage is capped at a factor of {cluster_size:.2f} -")
    print("   which is why this correction is a rounding error in a contact centre and a")
    print("   catastrophe in a trial randomised by school.")
    print()
    print(f"   Both models agree that {actual_alpha(0.05, 1.0):.4f} is what a design effect of one")
    print("   costs, which is the control the formula has to pass before any of the rest means")
    print("   anything.")


if __name__ == "__main__":
    main()

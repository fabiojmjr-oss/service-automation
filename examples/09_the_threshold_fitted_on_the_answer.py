"""The closed form given the input it assumes, and the term it was missing anyway.

Run:
    python examples/09_the_threshold_fitted_on_the_answer.py

Wave 3 applied the textbook routing threshold to a score that was a margin rather than a
probability, found it 12.5% worse than the single swept number, and concluded that calibration was
the missing step. This example tests that conclusion against the one thing wave 3 did not have: the
probability the generator actually used, on which the formula must be exactly optimal if the
diagnosis was right.

It is not, so the second half asks what was actually missing - and prices the two other decisions
wave 3 took by default: thresholds swept and priced on the same contacts, and a per-intent rule
keyed on a label no router can read.
"""

from __future__ import annotations

import pandas as pd

from svclab.bot import classifier_labels
from svclab.calibration import (
    amended_threshold,
    calibrated_scores,
    fit_period,
    formula_table,
    key_table,
    optimism_table,
    reliability_table,
    resolve_benefit,
)
from svclab.routing import calibrated_threshold
from svclab.synth import ROUTING, generate_dataset

#: The saving wave 3 published, in seconds per contact, fitted and priced on the same month.
WAVE_THREE_SAVING = 11.5552

RULE = "=" * 100


def main() -> None:
    pd.set_option("display.width", 200)
    data = generate_dataset()

    # The treated arm, carrying the label the classifier reported. A router runs before anybody
    # knows what the contact was, so this column is the only intent it can key a rule on.
    month = data.contacts[~data.contacts["holdout"]].copy()
    reported = classifier_labels(month)
    month = month.merge(reported[["contact", "predicted_intent"]], on="contact", how="left")
    fitting = fit_period(month)

    print(RULE)
    print("The period, split by calendar so that a threshold is judged where it was not fitted")
    print(RULE)
    print(f"  treated contacts {len(month):>8,}")
    print(f"  fitted on        {int(fitting.sum()):>8,}")
    print(f"  judged on        {int((~fitting).sum()):>8,}")

    print()
    print(RULE)
    print("What the raw score claimed against what happened, in the later period")
    print(RULE)
    correct = reported["classified_correctly"].to_numpy(dtype=bool)
    raw = calibrated_scores(month, data.routing_scores)["raw"]["classifier_score"]
    values = raw.to_numpy(dtype=float)
    table = reliability_table(values[~fitting], correct[~fitting])
    print(table.to_string(index=False))
    worst = table.loc[table["gap"].idxmax()]
    print(
        f"\n  Worst bin: the score says {worst['mean_score']:.4f} and "
        f"{worst['share_correct']:.4f} of those labels are right - a gap of "
        f"{worst['gap']:.4f} on {int(worst['contacts']):,} contacts."
    )

    print()
    print(RULE)
    print("The closed form against the sweep, on four versions of the same score")
    print(RULE)
    formula = formula_table(month, data.routing_scores)
    print(formula.to_string(index=False))
    seen = formula.set_index("score")
    factor = seen.loc["raw", "naive_penalty"] / seen.loc["isotonic", "naive_penalty"]
    print(
        f"\n  Calibration cuts the naive formula's penalty by {factor:.2f} times, from "
        f"{seen.loc['raw', 'naive_penalty']:.2%} to {seen.loc['isotonic', 'naive_penalty']:.2%}."
    )
    print(
        f"  And on the probability the generator actually used it is still "
        f"{seen.loc['true', 'naive_penalty']:.2%}, where there is no calibration left to do."
    )
    print("  So calibration was not the missing step. A term was.")

    print()
    print(RULE)
    print("The term: a correctly labelled contact the bot resolves saves human seconds")
    print(RULE)
    benefit = resolve_benefit(month[fitting], data.routing_scores)
    rows = []
    for intent, seconds in ROUTING.misroute_seconds.items():
        rows.append(
            {
                "intent": intent,
                "misroute_seconds": seconds,
                "benefit_seconds": benefit[intent],
                "naive_threshold": calibrated_threshold(ROUTING.defer_seconds, seconds),
                "amended_threshold": amended_threshold(
                    ROUTING.defer_seconds, seconds, benefit[intent]
                ),
            }
        )
    print(pd.DataFrame(rows).to_string(index=False))
    print(
        "\n  The benefit runs opposite to the misroute cost, so a formula that prices only "
        "mistakes is\n  most wrong where the bot is most useful. Carrying the term, the penalty "
        f"on the raw margin\n  falls to {seen.loc['raw', 'amended_penalty']:.2%} - and "
        f"{seen.loc['raw', 'amended_seconds']:.2f} seconds beats the naive formula's "
        f"{seen.loc['true', 'naive_seconds']:.2f} on the\n  perfectly calibrated score. "
        "Fixing the model beat fixing the input."
    )
    print(
        "\n  Note also that the best-calibrated score is the worst ranker: the control's swept "
        f"cost is\n  {seen.loc['true', 'swept_seconds']:.4f} against the raw margin's "
        f"{seen.loc['raw', 'swept_seconds']:.4f}. Calibration and discrimination are different\n"
        "  properties, and only the raw score knows what the classifier actually saw."
    )

    print()
    print(RULE)
    print("What a threshold fitted in one period costs in the next one")
    print(RULE)
    optimism = optimism_table(month, data.routing_scores)
    print(optimism.to_string(index=False))
    queue = optimism[optimism["intent"] == "queue"].iloc[0]
    print(
        f"\n  The queue pays {queue['optimism']:.4f} seconds per contact for having fitted "
        f"elsewhere:\n  {queue['optimism'] / queue['later_seconds']:.2%} of the bill, and "
        f"{queue['optimism'] / WAVE_THREE_SAVING:.2%} of the saving wave 3 published."
    )
    print(
        "  Optimism concentrates where the mistake is expensive and the sample is thin - and the\n"
        "  thresholds move far more than the cost does, because the cost curve is flat near its\n"
        "  optimum. The cost was learned; the cut was not."
    )

    print()
    print(RULE)
    print("The label a router can read, against the one wave 3 priced")
    print(RULE)
    keys = key_table(month, data.routing_scores)
    print(keys.to_string(index=False))
    by_key = keys.set_index("key")
    deployable = float(by_key.loc["predicted_intent", "saving_against_single"])
    oracle = float(by_key.loc["intent", "saving_against_single"])
    avoided = int(by_key.loc["intent", "misroutes"] - by_key.loc["predicted_intent", "misroutes"])
    print(
        f"\n  The deployable rule saves {deployable:.4f} seconds per contact against the oracle "
        f"rule's\n  {oracle:.4f}, with {avoided} fewer misroutes. The roadmap predicted the gain "
        "would shrink; it grows."
    )
    print(
        "  A wrong label is the event the cost is made of, so the reported label carries "
        "information\n  about the classifier being wrong and the true label carries none."
    )
    print(
        f"\n  Out of sample and keyed on the readable label, wave 3's saving becomes "
        f"{deployable:.4f}\n  against its published {WAVE_THREE_SAVING:.4f} - a ratio of "
        f"{deployable / WAVE_THREE_SAVING:.4f}, or {deployable * len(month) / 3600.0:.2f} hours "
        "at the\n  month's treated volume. The two corrections nearly cancel, which the roadmap "
        "did not predict either."
    )


if __name__ == "__main__":
    main()

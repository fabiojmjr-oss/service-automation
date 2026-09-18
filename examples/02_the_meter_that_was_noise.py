"""Qualifying the quality panel before using it, and what it costs not to.

Run:
    python examples/02_the_meter_that_was_noise.py

Wave 1 ended with resolution as the quantity a bot policy should be judged on. Grading sessions is
how an operation measures that, so this example runs the gauge study first: does a grader agree with
themselves, do two graders agree with each other, and is the verdict right. Then it prices what the
answers do to the comparison the panel was built to make.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from svclab.bot import HUMAN_ONLY, THREE_TURNS, run
from svclab.quality import (
    agreement_table,
    attenuation,
    judge_verdicts,
    kappa,
    latent_quality,
    panel_verdicts,
    reproducibility,
    sessions_for_difference,
)
from svclab.synth import GRADERS, JUDGE, QUALITY, generate_dataset


def main() -> None:
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    data = generate_dataset()
    contacts = data.contacts
    treated = contacts[~contacts["holdout"]]
    held = contacts[contacts["holdout"]]

    bot = latent_quality(run(treated, THREE_TURNS), contacts)
    control = latent_quality(run(held, HUMAN_ONLY), contacts)
    everything = pd.concat([bot, control], ignore_index=True)

    print("THE STANDARD, AND THE ONE COLUMN THAT MAKES IT A STANDARD")
    print(f"   A session is acceptable at or above a declared quality of {QUALITY.standard:.2f}.")
    print("   Declared, which is the whole point: no real operation has the column, so no real")
    print("   operation can say whether its quality panel is right. Here it can be checked.")
    print()
    print(
        everything.groupby("outcome")[["latent_quality", "acceptable"]]
        .agg(["mean", "size"])
        .round(4)
        .to_string()
    )

    print("\n" + "=" * 98)
    print("THE GAUGE STUDY NOBODY RUNS")
    print("=" * 98)
    panel = panel_verdicts(everything, data.panel_noise)
    table = agreement_table(panel, everything)
    print(
        f"   {QUALITY.sample:,} sampled contacts, which are {panel['session'].nunique():,} sessions"
        f" once the repeats"
    )
    print(
        f"   they generated are counted. {len(GRADERS)} graders, {QUALITY.replicates} readings each"
        f" - {len(panel):,} readings."
    )
    print("   The second reading is the one almost nobody collects, and without it repeatability")
    print("   cannot be estimated at all.")
    print()
    print(table.round(4).to_string(index=False))
    print()
    spread = float(table["pass_rate"].max()) / float(table["pass_rate"].min())
    print(
        "   Read the pass rate first. The same sessions, and the headline quality number moves by"
    )
    print(f"   a factor of {spread:.2f} depending on who graded.")
    worst = float(table["repeatability"].min())
    best = float(table["repeatability"].max())
    print(f"   Then repeatability: between {(1 - best) * 100:.1f}% and {(1 - worst) * 100:.1f}% of")
    print("   the time, one person contradicts their own earlier verdict on the same session.")
    print(
        "   And the two ways of being wrong are opposite - a lenient grader and a strict one have"
    )
    print("   similar accuracy and mirror-image error profiles, which a single figure hides.")

    print("\n" + "=" * 98)
    print("SEVENTY-EIGHT PER CENT AGREEMENT IS A KAPPA OF 0.57")
    print("=" * 98)
    between = reproducibility(panel)
    print(between.round(4).to_string(index=False))
    print()
    print("   Raw agreement is the number that gets reported. Kappa is agreement above what two")
    print(
        "   assessors would reach by accident given their own pass rates, and the gap between the"
    )
    print(
        "   two columns is not a technicality: two assessors who pass 95% of everything agree 90%"
    )
    print(
        "   of the time while knowing nothing. Both readings here are from the same replicate, so"
    )
    print("   this measures reproducibility and not repeatability as well.")

    print("\n" + "=" * 98)
    print("WHAT THE PANEL WILL REPORT OF A REAL DIFFERENCE")
    print("=" * 98)
    control_rate = float(control["acceptable"].mean())
    bot_rate = float(bot["acceptable"].mean())
    sensitivity = float(table["sensitivity"].mean())
    specificity = float(table["specificity"].mean())
    measured = attenuation(control_rate, bot_rate, sensitivity, specificity)
    print(f"   By the declared standard, {control_rate:.4f} of the control arm's sessions are")
    print(f"   acceptable against {bot_rate:.4f} of the automated arm's.")
    print(f"   The panel's average sensitivity is {sensitivity:.4f} and its specificity")
    print(f"   {specificity:.4f}, so its Youden index is {measured['factor']:.4f}.")
    print()
    print(pd.Series(measured).round(6).to_string())
    print()
    print("   The identity is exact rather than approximate: an assessor turns a true pass rate p")
    print("   into p*se + (1-p)*(1-sp), so a difference between two groups comes out multiplied by")
    print("   se + sp - 1. Two consequences worth separating.")
    print()
    coin = attenuation(control_rate, bot_rate, 0.5, 0.5)
    inverted = attenuation(control_rate, bot_rate, 0.30, 0.40)
    print(
        f"   A gauge whose two rates sum to one reports exactly {coin['observed_difference']:.1f}"
    )
    print("   of a difference this large. Not a small number - zero.")
    print(
        f"   A gauge below that reverses the sign: {inverted['observed_difference']:+.4f} reported"
    )
    print(f"   for a true {inverted['true_difference']:+.4f}. Not noisy. Inverted.")

    print("\n" + "=" * 98)
    print("AND ATTENUATION IS PAID FOR IN SESSIONS")
    print("=" * 98)
    perfect = sessions_for_difference(control_rate, bot_rate)
    actual = sessions_for_difference(control_rate, bot_rate, sensitivity, specificity)
    square_law = 1.0 / measured["factor"] ** 2
    print(f"   Sessions per arm with a perfect gauge:  {perfect:8.2f}")
    print(f"   Sessions per arm with this panel:       {actual:8.2f}")
    print(f"   Inflation: {actual / perfect:.4f} times, against the {square_law:.4f} the square of")
    print("   the Youden index predicts. The rule of thumb understates the bill, because the")
    print("   attenuated rates also sit closer to 0.5 where a proportion's variance is largest.")

    print("\n" + "=" * 98)
    print("THE AUTOMATED JUDGE, AND WHAT IT WOULD BE VALIDATED AGAINST")
    print("=" * 98)
    judged = judge_verdicts(everything, data.judge_noise)
    judge_row = agreement_table(judged, everything).iloc[0]
    print(
        f"   {JUDGE.grader} reads all {len(judged):,} sessions rather than"
        f" {QUALITY.sample}, once each."
    )
    print()
    combined = pd.concat([table, agreement_table(judged, everything)], ignore_index=True)
    print(
        combined[["assessor", "agreement_with_truth", "sensitivity", "specificity", "youden"]]
        .sort_values("youden", ascending=False)
        .round(4)
        .to_string(index=False)
    )
    print()
    print("   It agrees with the standard more often than any individual grader. Now the way it")
    print("   would actually be assessed, which is against the graders:")
    print()
    first = panel[panel["replicate"] == 1]
    rows = []
    for grader, frame in first.groupby("assessor"):
        merged = frame.merge(judged[["session", "verdict"]], on="session", suffixes=("_p", "_j"))
        rows.append(
            {
                "comparison": f"judge vs {grader}",
                "agreement": float(np.mean(merged["verdict_p"] == merged["verdict_j"])),
                "kappa": kappa(merged["verdict_p"], merged["verdict_j"]),
            }
        )
    majority = first.groupby("session")["verdict"].mean() >= 0.5
    sample = majority.index
    judge_sample = judged.set_index("session").reindex(sample)["verdict"].to_numpy(dtype=bool)
    truth_sample = (
        everything.set_index("session").reindex(sample)["acceptable"].to_numpy(dtype=bool)
    )
    majority_verdict = majority.to_numpy(dtype=bool)
    rows.append(
        {
            "comparison": "judge vs the panel's majority",
            "agreement": float(np.mean(judge_sample == majority_verdict)),
            "kappa": kappa(judge_sample, majority_verdict),
        }
    )
    rows.append(
        {
            "comparison": "judge vs the declared standard",
            "agreement": float(np.mean(judge_sample == truth_sample)),
            "kappa": kappa(judge_sample, truth_sample),
        }
    )
    rows.append(
        {
            "comparison": "the panel's majority vs the standard",
            "agreement": float(np.mean(majority_verdict == truth_sample)),
            "kappa": kappa(majority_verdict, truth_sample),
        }
    )
    verdicts = pd.DataFrame(rows)
    print(verdicts.round(4).to_string(index=False))
    print()
    graders_only = verdicts[verdicts["comparison"].str.startswith("judge vs avaliador")]
    print(
        f"   Validated against one grader the judge scores anywhere from"
        f" {graders_only['kappa'].min():.4f} to {graders_only['kappa'].max():.4f} - a spread of"
    )
    print(
        f"   {graders_only['kappa'].max() - graders_only['kappa'].min():.4f} of kappa decided by"
        f" which colleague was free that week. Its agreement"
    )
    print(f"   with the truth is {verdicts['kappa'].iloc[-2]:.4f}.")
    print("   'Agreement with our human reviewers' is a measurement of the reviewers as much as of")
    print("   the judge.")
    print()
    print("   And the honest counterweight, in the same breath: the panel as a committee beats the")
    print(
        f"   judge - a majority verdict scores {verdicts['kappa'].iloc[-1]:.4f} against the truth"
        f" where the judge scores {verdicts['kappa'].iloc[-2]:.4f}."
    )
    print("   Averaging three moderate assessors recovers most of what each one loses, which is an")
    print("   argument for a panel and not an argument for any member of it.")
    print()
    print(f"   The judge has no repeatability column: {judge_row['repeatability']}. It is")
    print("   deterministic and read each session once, so it has nothing to say about agreeing")
    print("   with itself - and reporting 1.0 there would be claiming a property never measured,")
    print("   which is the failure this whole example is about.")


if __name__ == "__main__":
    main()

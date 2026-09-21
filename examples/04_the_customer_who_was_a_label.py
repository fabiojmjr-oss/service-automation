"""The independence assumption, priced against a world that does not make it.

Run:
    python examples/04_the_customer_who_was_a_label.py

Waves 1 to 3 drew every trait per contact, so a customer was a label on a row. Wave 3 could not
measure the clustering it warned about and had to price declared correlations instead. This example
builds the same account a second time, from the identical noise, with customers who are people - and
then asks the questions in order: did anything published move, how much of a correlation between
people survives into an outcome, what does the surviving part cost, and what does the correction an
analyst normally reaches for cost.
"""

from __future__ import annotations

import pandas as pd

from svclab.bot import HUMAN_ONLY, THREE_TURNS, run
from svclab.population import (
    correlation_table,
    design_table,
    error_table,
    pair_failures,
    power_at,
    world_table,
)
from svclab.synth import POPULATION, correlated_dataset, generate_dataset

#: Wave 3's sizing for the comparison wave 1 found, at 80% power on independent contacts.
WAVE_3_CONTACTS_PER_ARM = 405
#: The gap being detected: `guarded` resolves 0.7271 against `three-turns` at 0.6355.
DIFFERENCE = 0.0916
BASE_RATE = 0.6355
#: The design effect wave 3 priced as its pessimistic scenario, at a declared correlation of 0.30.
WAVE_3_DESIGN_EFFECT = 1.2891


def main() -> None:
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)

    data = generate_dataset()
    other = correlated_dataset(data)
    contacts = {"independent": data.contacts, "correlated": other.contacts}
    treated = {name: run(t[~t["holdout"]], THREE_TURNS) for name, t in contacts.items()}
    control = {name: run(t[t["holdout"]], HUMAN_ONLY) for name, t in contacts.items()}

    print("ONE: DID ANYTHING ALREADY PUBLISHED MOVE?")
    print("=" * 98)
    print("   The same account twice, from the same uniforms, with the customer's share of each")
    print(
        f"   trait declared at {POPULATION.difficulty_correlation:.2f} on difficulty and"
        f" {POPULATION.patience_correlation:.2f} on patience."
    )
    print("   The copula leaves every marginal distribution where it was, so the levels should not")
    print("   move.")
    print()
    world = world_table(contacts, treated)
    print(world.to_string(index=False))
    print()
    relative = (world["difference"] / world["independent"]).abs()
    worst = world.loc[relative.idxmax(), "metric"]
    print(f"   The largest relative movement is {relative.max():.2%}, on {worst}.")
    print("   That is a precondition and not a result: it is what says everything below is about")
    print("   dependence and about nothing else. A correlation does not change what happened. It")
    print("   changes what you can conclude from it.")
    print()

    print("TWO: HOW MUCH OF A CORRELATION BETWEEN PEOPLE REACHES THE OUTCOME?")
    print("=" * 98)
    chain = correlation_table(contacts, treated).set_index("stage")
    print(chain.to_string())
    print()
    declared = float(chain.loc["declared", "difficulty"])
    outcome = float(chain.loc["outcome", "resolution"])
    print(f"   Declared {declared:.4f} between people. Measured {outcome:.4f} on the resolution a")
    print(f"   test is run on - a factor of {declared / outcome:.1f}.")
    print("   A resolution is a coin whose bias is correlated, not a correlated coin, and the coin")
    print("   is most of the variance. So estimate the correlation of the outcome you are testing,")
    print("   never of the trait you believe drives it.")
    print()

    print("THREE: WHAT THE SURVIVING PART COSTS, AGAINST WHAT WAVE 3 ASSUMED")
    print("=" * 98)
    design = design_table(treated).set_index("world")
    print(design.to_string())
    print()
    print("   The independent row reports no error rate at all. A measured design effect below one")
    print("   is a negative correlation estimate, which is not an inflation, and wave 3's function")
    print("   refuses it rather than clipping it to five per cent.")
    print()
    effect = float(design.loc["correlated", "design_effect"])
    for label, value in (
        ("independent contacts", 1.0),
        ("the measured design effect", effect),
        ("wave 3's declared 0.30", WAVE_3_DESIGN_EFFECT),
    ):
        power = power_at(value, DIFFERENCE, BASE_RATE, WAVE_3_CONTACTS_PER_ARM)
        print(f"   power at {WAVE_3_CONTACTS_PER_ARM} contacts per arm, {label}: {power:.4f}")
    print()
    print("   Wave 3's alarm was right in shape and wrong in size on this account: the correction")
    print("   is under two points of power, not eleven. A design effect is a product of two")
    print("   factors, and this account's clusters average two contacts.")
    print()

    print("FOUR: THE SAME PERSON, FAILED TWICE")
    print("=" * 98)
    pairs = pair_failures(treated).set_index("world")
    print(pairs.to_string())
    print()
    first = float(pairs.loc["independent", "both_failed"])
    second = float(pairs.loc["correlated", "both_failed"])
    people = (second - first) * float(pairs.loc["independent", "pairs"])
    resolution = world.set_index("metric").loc["resolution rate", "difference"]
    print(
        f"   The resolution rate moved by {float(resolution):+.4f}, and the share of two-contact"
        f" customers failed"
    )
    print(
        f"   both times rose {second / first - 1.0:.1%}: {people:.0f} more people, out of the same"
        f" volume, with the same"
    )
    print("   aggregate KPI.")
    print("   A resolution rate is contact-weighted. A complaint is customer-weighted. The two")
    print("   agree exactly when a customer is a label.")
    print()

    print("FIVE: THE CORRECTION MOST ANALYSTS REACH FOR")
    print("=" * 98)
    errors = error_table(treated, control).set_index("world")
    print(errors.to_string())
    print()
    loss = float(errors.loc["independent", "cluster_mean_ratio"]) - 1.0
    gain = float(errors.loc["correlated", "corrected_ratio"]) - 1.0
    print(f"   Averaging customer averages inflates the standard error by {loss:.1%} in a world")
    print("   with no correlation in it whatever. That is an efficiency loss wearing a")
    print(f"   correction's clothes. The correlation's own contribution is {gain:.1%}, so the")
    print(
        f"   analyst who corrects that way pays about {loss / gain:.0f} times the error they were"
    )
    print("   correcting for.")


if __name__ == "__main__":
    main()

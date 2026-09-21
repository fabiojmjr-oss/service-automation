"""What a per-customer number is worth when customers are not interchangeable.

Run:
    python examples/05_the_frequent_caller.py

Wave 4 gave customers traits and left their contact rate alone: every contact picked a customer
uniformly, so the busiest customer in the account was busy by accident. This example regroups the
identical contacts into customers who do not all contact equally often, with the heavy users
correlated with the difficult ones - and then asks what that does to the shape of the clusters, to
the design effect, to who pays, and to the precision of wave 1's central estimate.

Nothing about a contact changes. The arms are the same, the traits are the same, and every
per-contact figure is identical. Only who shares a person.
"""

from __future__ import annotations

import pandas as pd

from svclab.bot import HUMAN_ONLY, THREE_TURNS, run
from svclab.concentration import burden_table, concentration_table, precision_table
from svclab.population import design_table
from svclab.synth import (
    CONCENTRATION,
    EQUAL_RATES,
    concentrated_dataset,
    correlated_dataset,
    generate_dataset,
)

#: The design effect wave 3 declared as its serious scenario, and the one wave 4 measured.
WAVE_3_DESIGN_EFFECT = 1.2891
WAVE_4_DESIGN_EFFECT = 1.0693


def main() -> None:
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)

    data = generate_dataset()
    # Regroup first, then correlate: the copula has to know who the customer is.
    worlds = {
        "equal rates": correlated_dataset(concentrated_dataset(data, EQUAL_RATES)),
        "concentrated": correlated_dataset(concentrated_dataset(data, CONCENTRATION)),
    }
    treated = {name: world.contacts[~world.contacts["holdout"]] for name, world in worlds.items()}
    outcomes = {name: run(table, THREE_TURNS) for name, table in treated.items()}
    control = {
        name: run(world.contacts[world.contacts["holdout"]], HUMAN_ONLY)
        for name, world in worlds.items()
    }

    print("ONE: THE SAME VOLUME, FROM FEWER PEOPLE, AND THEY ARE THE HARDER ONES")
    print("=" * 98)
    print(
        f"   A customer's contact rate is log-normal, correlated with their own difficulty at"
        f" {CONCENTRATION.difficulty_correlation:.2f}."
    )
    print("   The control is the same regrouping with equal rates, because reassigning contacts")
    print("   among the customers an account saw enlarges the clusters on its own.")
    print()
    shape = concentration_table(treated).set_index("world")
    print(shape.to_string())
    print()
    mean_rise = float(shape.loc["concentrated", "mean_cluster_size"]) / float(
        shape.loc["equal rates", "mean_cluster_size"]
    )
    effective_rise = float(shape.loc["concentrated", "effective_cluster_size"]) / float(
        shape.loc["equal rates", "effective_cluster_size"]
    )
    print(f"   The mean cluster size rises {mean_rise - 1.0:.1%} and the effective one")
    print(f"   {effective_rise - 1.0:.1%}. Concentration is a statement about the variance of the")
    print("   cluster sizes, and the mean barely sees it.")
    print()

    print("TWO: WHICH IS WHERE WAVE 3'S ALARM COMES BACK")
    print("=" * 98)
    design = design_table(outcomes).set_index("world")
    print(design.to_string())
    print()
    measured = float(design.loc["concentrated", "design_effect"])
    at_mean = float(design.loc["concentrated", "design_effect_at_mean"])
    print(f"   Wave 3 declared {WAVE_3_DESIGN_EFFECT:.4f} as its serious case. Wave 4 measured")
    print(f"   {WAVE_4_DESIGN_EFFECT:.4f} and called that four times too loud - in a world where")
    print(f"   everybody contacts at the same rate. Here it is {measured:.4f}:")
    print(f"   {measured / WAVE_3_DESIGN_EFFECT:.0%} of the number wave 3 declared.")
    print("   Two wrong assumptions in opposite directions, and their product was close to right.")
    print()
    print(
        f"   And the same table at the plain mean cluster size reports {at_mean - 1.0:.2%} of extra"
    )
    print(f"   sample where the correct figure is {measured - 1.0:.2%} - less than half, in the")
    print("   direction that lets a test ship.")
    print()

    print("THREE: THE COST CONCENTRATES FASTER THAN THE VOLUME")
    print("=" * 98)
    burden = burden_table(treated, outcomes).set_index("world")
    print(burden.to_string())
    print()
    control_row = burden.loc["equal rates"]
    heavy = burden.loc["concentrated"]
    print(
        f"   In the control the three shares are one number:"
        f" {float(control_row['top_decile_volume']):.4f},"
        f" {float(control_row['top_decile_unresolved']):.4f},"
        f" {float(control_row['top_decile_human_hours']):.4f}."
    )
    print("   Being heavy says nothing about being difficult. Concentration separates them:")
    print(
        f"   {float(heavy['top_decile_volume']):.1%} of the volume,"
        f" {float(heavy['top_decile_unresolved']):.1%} of the failures and"
        f" {float(heavy['top_decile_human_hours']):.1%} of the hours."
    )
    print()
    difficulty = float(heavy["difficulty_per_contact"]) / float(
        control_row["difficulty_per_contact"]
    )
    points = float(control_row["resolution_rate"]) - float(heavy["resolution_rate"])
    print(
        f"   And the resolution rate falls {points * 100:.2f} points with no change of policy: the"
    )
    print(f"   difficulty per contact rises {difficulty - 1.0:.1%} because the difficult customers")
    print("   now send more contacts each. The distribution per customer did not move; the")
    print("   distribution per contact did.")
    print()
    print(
        f"   Customers failed three times or more:"
        f" {int(control_row['customers_failed_three_times'])} ->"
        f" {int(heavy['customers_failed_three_times'])}."
    )
    print()

    print("FOUR: AND WAVE 1'S CENTRAL ESTIMATE LOSES A THIRD OF ITS PRECISION")
    print("=" * 98)
    precision = precision_table(outcomes, control).set_index("world")
    print(precision.to_string())
    print()
    relative = float(precision.loc["concentrated", "relative_error"]) / float(
        precision.loc["equal rates", "relative_error"]
    )
    width = float(precision.loc["concentrated", "interval_width"]) / float(
        precision.loc["equal rates", "interval_width"]
    )
    print("   The estimates are not comparable - deflection per customer divides by a count of")
    print("   customers, and the two worlds disagree about how many there are. The errors are.")
    print(f"   The relative error rises {relative - 1.0:.0%} and the interval is {width - 1.0:.0%}")
    print("   wider, on the same contacts, the same arms and the same bot. A per-customer number")
    print("   is only as stable as the assumption about who a customer is.")


if __name__ == "__main__":
    main()

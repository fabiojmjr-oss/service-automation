"""The design effect, against the three corners where its value is known without computing it.

The design effect is ``1 + (m - 1) * rho``, so it is one when the clusters hold one observation each,
one when the correlation inside them is zero, and equal to the cluster size when the correlation is
total. Those three are checked exactly. The correlation estimator gets the same treatment: clusters
whose members are identical return one, and clusters constructed to carry no between-group signal
return minus one.

And the sample size has an exact relationship to the effect - it is the independent answer multiplied
by it - which is asserted rather than assumed, because that multiplication is the entire correction.
"""

from __future__ import annotations

import pandas as pd
import pytest
from scipy import stats

from svclab.bot import GUARDED, THREE_TURNS, run
from svclab.experiment import (
    SIZING_COLUMNS,
    actual_alpha,
    contacts_for_difference,
    design_effect,
    intracluster_correlation,
    sizing_table,
)
from svclab.synth import Dataset


class TestTheDesignEffect:
    def test_the_three_corners_are_exact(self) -> None:
        assert design_effect(1.96, 0.0) == pytest.approx(1.0, abs=1e-15)
        assert design_effect(1.0, 0.7) == pytest.approx(1.0, abs=1e-15)
        assert design_effect(1.96, 1.0) == pytest.approx(1.96, abs=1e-15)
        assert design_effect(4.0, 1.0) == pytest.approx(4.0, abs=1e-15)

    def test_it_is_the_formula_it_claims_to_be(self) -> None:
        for size in (1.5, 2.0, 5.0):
            for icc in (0.05, 0.2, 0.6):
                assert design_effect(size, icc) == pytest.approx(
                    1.0 + (size - 1.0) * icc, abs=1e-15
                )

    def test_a_negative_correlation_deflates_rather_than_inflates(self) -> None:
        """Which is a real thing a clustered sample can do, and is reported rather than clipped."""
        assert design_effect(2.0, -0.2) < 1.0

    def test_impossible_arguments_are_refused(self) -> None:
        with pytest.raises(ValueError, match="a cluster holds at least one"):
            design_effect(0.5, 0.2)
        with pytest.raises(ValueError, match="between minus one and one"):
            design_effect(2.0, 1.4)


class TestTheCorrelationEstimator:
    def test_identical_members_return_one(self) -> None:
        frame = pd.DataFrame({"c": [1, 1, 2, 2], "y": [1.0, 1.0, 0.0, 0.0]})
        assert intracluster_correlation(frame, "c", "y") == pytest.approx(1.0, abs=1e-12)

    def test_clusters_carrying_no_between_signal_return_minus_one(self) -> None:
        """Every cluster has the same mean and all the variation is inside it, which is the opposite
        of clustering and is reported as such."""
        frame = pd.DataFrame({"c": [1, 1, 2, 2], "y": [1.0, 0.0, 1.0, 0.0]})
        assert intracluster_correlation(frame, "c", "y") == pytest.approx(-1.0, abs=1e-12)

    def test_an_outcome_that_never_varies_has_no_correlation_to_report(self) -> None:
        """Both mean squares are zero, so the standardised difference between them is undefined.

        Zero is the honest answer: there is no variance to split between the clusters and inside
        them, which is not the same thing as clusters that carry no signal.
        """
        frame = pd.DataFrame({"c": [1, 1, 2, 2], "y": [1.0, 1.0, 1.0, 1.0]})
        assert intracluster_correlation(frame, "c", "y") == 0.0

    def test_a_missing_column_is_refused(self) -> None:
        frame = pd.DataFrame({"c": [1, 1, 2, 2], "y": [1.0, 0.0, 1.0, 0.0]})
        with pytest.raises(ValueError, match="is not a column"):
            intracluster_correlation(frame, "customer", "y")

    def test_one_cluster_or_all_singletons_are_refused(self) -> None:
        with pytest.raises(ValueError, match="at least two clusters"):
            intracluster_correlation(pd.DataFrame({"c": [1, 1], "y": [1.0, 0.0]}), "c", "y")
        with pytest.raises(ValueError, match="nothing inside a cluster"):
            intracluster_correlation(pd.DataFrame({"c": [1, 2, 3], "y": [1.0, 0.0, 1.0]}), "c", "y")


class TestTheErrorRateATestReallyRunsAt:
    def test_no_inflation_returns_the_level_it_was_given(self) -> None:
        for nominal in (0.01, 0.05, 0.10):
            assert actual_alpha(nominal, 1.0) == pytest.approx(nominal, abs=1e-12)

    def test_it_is_the_formula_it_claims_to_be(self) -> None:
        for effect in (1.1, 1.29, 1.96, 4.0):
            critical = float(stats.norm.ppf(0.975))
            expected = 2.0 * (1.0 - float(stats.norm.cdf(critical / effect**0.5)))
            assert actual_alpha(0.05, effect) == pytest.approx(expected, abs=1e-14)

    def test_more_clustering_costs_more_error(self) -> None:
        measured = [actual_alpha(0.05, effect) for effect in (1.0, 1.1, 1.3, 2.0, 4.0)]
        assert measured == sorted(measured)
        assert measured[-1] > 3.0 * measured[0]

    def test_impossible_arguments_are_refused(self) -> None:
        with pytest.raises(ValueError, match="alpha has to be"):
            actual_alpha(0.0, 1.2)
        with pytest.raises(ValueError, match="not an inflation"):
            actual_alpha(0.05, 0.9)


class TestTheSampleSize:
    def test_the_effect_multiplies_the_independent_answer_exactly(self) -> None:
        """The whole correction, as an identity rather than as a rule of thumb."""
        independent = contacts_for_difference(0.7271, 0.6355)
        for effect in (1.0, 1.29, 1.96, 3.0):
            assert contacts_for_difference(0.7271, 0.6355, effect) == pytest.approx(
                independent * effect, rel=1e-12
            )

    def test_a_smaller_difference_costs_more_contacts(self) -> None:
        measured = [contacts_for_difference(0.70, second) for second in (0.60, 0.65, 0.68, 0.69)]
        assert measured == sorted(measured)

    def test_two_equal_rates_have_nothing_to_detect(self) -> None:
        with pytest.raises(ValueError, match="no difference to detect"):
            contacts_for_difference(0.5, 0.5)

    def test_impossible_arguments_are_refused(self) -> None:
        with pytest.raises(ValueError, match="the first rate has to be"):
            contacts_for_difference(1.4, 0.5)
        with pytest.raises(ValueError, match="power has to be"):
            contacts_for_difference(0.7, 0.6, power=1.0)
        with pytest.raises(ValueError, match="alpha has to be"):
            contacts_for_difference(0.7, 0.6, alpha=1.0)
        with pytest.raises(ValueError, match="not an inflation"):
            contacts_for_difference(0.7, 0.6, effect=0.5)

    def test_the_table_has_its_columns_and_prices_customers_as_well_as_contacts(self) -> None:
        table = sizing_table(
            {"independent": (1.9637, 0.0), "icc 0.30": (1.9637, 0.30)},
            0.7271,
            0.6355,
            1.9637,
        )
        assert tuple(table.columns) == SIZING_COLUMNS
        for _, row in table.iterrows():
            assert float(row["customers_per_arm"]) == pytest.approx(
                float(row["contacts_per_arm"]) / 1.9637
            )
        assert float(table["contacts_per_arm"].iloc[1]) > float(table["contacts_per_arm"].iloc[0])
        assert float(table["actual_alpha"].iloc[1]) > float(table["actual_alpha"].iloc[0])

    def test_an_empty_scenario_set_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no scenarios to price"):
            sizing_table({}, 0.7, 0.6, 2.0)


class TestOnTheRealAccount:
    def test_this_generator_draws_contacts_independently_within_a_customer(
        self, full: Dataset
    ) -> None:
        """A property of the generator rather than of contact centres, and the reason wave 3's
        sizing table prices assumed correlations rather than a measured one.

        Difficulty, patience and every other trait here are drawn per contact, so a customer is a
        label rather than a person. The estimator returning approximately zero on this data is
        therefore a check on the estimator, and a limitation of the generator recorded in the
        roadmap.
        """
        treated = full.contacts[~full.contacts["holdout"]]
        outcomes = run(treated, THREE_TURNS)
        first = outcomes[~outcomes["is_repeat"]].copy()
        first["resolved_num"] = first["resolved"].astype(float)
        first["human_num"] = first["handled_by_human"].astype(float)
        for column in ("resolved_num", "human_num"):
            assert abs(intracluster_correlation(first, "customer", column)) < 0.02, column

    def test_the_comparison_the_wave_sizes_is_the_one_wave_one_found(self, full: Dataset) -> None:
        treated = full.contacts[~full.contacts["holdout"]]
        three = run(treated, THREE_TURNS)
        guarded = run(treated, GUARDED)
        first_three = three[~three["is_repeat"]]
        first_guarded = guarded[~guarded["is_repeat"]]
        assert float(first_guarded["resolved"].mean()) > float(first_three["resolved"].mean())
        contacts = len(first_three) / first_three["customer"].nunique()
        assert 1.9 < contacts < 2.0

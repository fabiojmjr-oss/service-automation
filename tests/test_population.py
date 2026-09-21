"""The second world, and the four things it says about the first.

The load-bearing test here is the one that runs the construction at a correlation of zero and
demands the original table back. Everything this wave claims rests on the two worlds differing in one
declared quantity and in nothing else, and that claim is only as good as its control case.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from svclab.bot import HUMAN_ONLY, THREE_TURNS, run
from svclab.experiment import contacts_for_difference
from svclab.population import (
    CORRELATION_COLUMNS,
    DESIGN_COLUMNS,
    ERROR_COLUMNS,
    PAIR_COLUMNS,
    WORLD_COLUMNS,
    correlation_table,
    design_table,
    error_table,
    pair_failures,
    power_at,
    world_table,
)
from svclab.synth import (
    CENTRE,
    CONTACT_COLUMNS,
    POPULATION,
    Dataset,
    PopulationProfile,
    blend,
    correlated_contacts,
    customer_components,
)
from svclab.synth.customers import latent_traits


class TestTheBlend:
    def test_a_correlation_of_zero_is_the_occasion_alone(self) -> None:
        occasion = np.array([0.1, 0.5, 0.9])
        own = np.array([0.8, 0.8, 0.8])
        assert blend(occasion, own, 0.0) == pytest.approx(occasion, abs=1e-12)

    def test_a_correlation_of_one_is_the_customer_alone(self) -> None:
        occasion = np.array([0.1, 0.5, 0.9])
        own = np.array([0.3, 0.3, 0.3])
        assert blend(occasion, own, 1.0) == pytest.approx(own, abs=1e-12)

    def test_the_blend_is_still_a_percentile(self) -> None:
        rng = np.random.default_rng(0)
        blended = blend(rng.random(5000), rng.random(5000), 0.4)
        assert ((blended > 0.0) & (blended < 1.0)).all()
        # A sum of two standard normals with loadings sqrt(rho) and sqrt(1 - rho) is standard normal
        # again, so its percentile is uniform: the mean is a half and the variance one twelfth.
        assert float(blended.mean()) == pytest.approx(0.5, abs=0.01)
        assert float(blended.var()) == pytest.approx(1.0 / 12.0, abs=0.005)

    def test_a_correlation_outside_the_unit_interval_is_refused(self) -> None:
        with pytest.raises(ValueError, match="must be in"):
            blend(np.array([0.5]), np.array([0.5]), 1.5)


class TestTheControlCase:
    def test_at_no_correlation_the_second_world_is_the_first(self, full: Dataset) -> None:
        """The whole wave in one assertion.

        At a correlation of zero the customer's percentile carries no weight, so every trait must
        come back as it went in - through a quantile function and its inverse, which is where the
        1e-9 comes from. Anything larger than that would mean the construction moves figures on its
        own, and every comparison in this module would be measuring the machinery.
        """
        flat = PopulationProfile(difficulty_correlation=0.0, patience_correlation=0.0)
        again = correlated_contacts(full.contacts, full.customer_components, CENTRE, flat)
        assert list(again.columns) == list(CONTACT_COLUMNS)
        for column in ("difficulty", "u_patience", "human_seconds", "patience_turns"):
            assert again[column].to_numpy() == pytest.approx(
                full.contacts[column].to_numpy(), abs=1e-9
            ), column
        for column in ("bot_can_resolve", "would_self_serve", "human_resolves", "holdout"):
            assert (again[column] == full.contacts[column]).all(), column

    def test_the_noise_is_not_redrawn(self, full: Dataset, correlated: Dataset) -> None:
        """Only the difficulty and the patience percentile may differ between the worlds."""
        for column in ("contact", "customer", "intent", "arrival_hour", "holdout"):
            assert (correlated.contacts[column] == full.contacts[column]).all(), column
        for column in ("classifier_draw", "u_bot", "u_self_serve", "u_seconds", "u_human"):
            assert correlated.contacts[column].to_numpy() == pytest.approx(
                full.contacts[column].to_numpy(), abs=0.0
            ), column
        assert (
            correlated.routing_scores["u_score"].to_numpy()
            == full.routing_scores["u_score"].to_numpy()
        ).all()

    def test_a_customer_with_no_components_is_refused(self, full: Dataset) -> None:
        with pytest.raises(KeyError, match="no drawn components"):
            correlated_contacts(full.contacts, full.customer_components.head(10))


class TestTheDeclaredCorrelation:
    def test_the_components_are_one_percentile_pair_per_customer(self, full: Dataset) -> None:
        components = full.customer_components
        assert len(components) == CENTRE.customers
        assert components["customer"].is_unique
        for column in ("difficulty_percentile", "patience_percentile"):
            assert components[column].between(0.0, 1.0).all()

    def test_the_latent_correlation_is_the_number_that_was_declared(
        self, correlated: Dataset
    ) -> None:
        """Measured where the copula is exact, against the declared value and its sampling error."""
        from svclab.experiment import intracluster_correlation

        latent = latent_traits(correlated.contacts)
        assert intracluster_correlation(latent, "customer", "latent_difficulty") == pytest.approx(
            POPULATION.difficulty_correlation, abs=0.02
        )
        assert intracluster_correlation(latent, "customer", "latent_patience") == pytest.approx(
            POPULATION.patience_correlation, abs=0.02
        )

    def test_the_first_world_has_no_correlation_to_find(self, full: Dataset) -> None:
        from svclab.experiment import intracluster_correlation

        latent = latent_traits(full.contacts)
        assert abs(intracluster_correlation(latent, "customer", "latent_difficulty")) < 0.02
        assert abs(intracluster_correlation(latent, "customer", "latent_patience")) < 0.02

    def test_the_marginal_distribution_does_not_move(
        self, full: Dataset, correlated: Dataset
    ) -> None:
        """The property that makes the two worlds comparable, checked on four moments and a range."""
        for column in ("difficulty", "patience_turns", "human_seconds"):
            first, second = full.contacts[column], correlated.contacts[column]
            assert float(second.mean()) == pytest.approx(float(first.mean()), rel=0.01), column
            assert float(second.std(ddof=1)) == pytest.approx(float(first.std(ddof=1)), rel=0.02), (
                column
            )
            assert float(second.quantile(0.9)) == pytest.approx(
                float(first.quantile(0.9)), rel=0.02
            ), column
        assert correlated.contacts["difficulty"].between(0.0, 1.0).all()

    def test_a_second_customer_draw_changes_the_world_and_not_the_marginal(
        self, full: Dataset
    ) -> None:
        """Different components, same marginal: the structure is the draw, not the distribution."""
        other = customer_components(np.random.default_rng(7))
        table = correlated_contacts(full.contacts, other)
        assert not np.allclose(
            table["difficulty"].to_numpy(), full.contacts["difficulty"].to_numpy()
        )
        assert float(table["difficulty"].mean()) == pytest.approx(
            float(full.contacts["difficulty"].mean()), rel=0.01
        )


class TestWhatItMovesInWhatWasPublished:
    def test_no_published_metric_moves_by_more_than_a_percent(
        self, full: Dataset, correlated: Dataset
    ) -> None:
        """The headline of the wave: the levels stand, only the uncertainty around them changes."""
        contacts = {"independent": full.contacts, "correlated": correlated.contacts}
        outcomes = {
            label: run(table[~table["holdout"]], THREE_TURNS) for label, table in contacts.items()
        }
        table = world_table(contacts, outcomes)
        assert list(table.columns) == list(WORLD_COLUMNS)
        relative = (table["difference"] / table["independent"]).abs()
        assert relative.max() < 0.01, table.to_string(index=False)

    def test_two_worlds_are_compared_here_and_not_three(self, full: Dataset) -> None:
        one = {"independent": full.contacts}
        with pytest.raises(KeyError, match="two worlds"):
            world_table(one, {"independent": run(full.contacts.head(50), THREE_TURNS)})

    def test_the_two_mappings_have_to_describe_the_same_worlds(self, full: Dataset) -> None:
        with pytest.raises(KeyError, match="outcomes"):
            world_table(
                {"a": full.contacts, "b": full.contacts},
                {"a": run(full.contacts.head(50), THREE_TURNS)},
            )


class TestTheAttenuation:
    def test_the_declared_correlation_survives_into_the_outcome_only_in_part(
        self, full: Dataset, correlated: Dataset
    ) -> None:
        """Declared, latent, observed, outcome - and the order of the four is the finding."""
        contacts = {"independent": full.contacts, "correlated": correlated.contacts}
        outcomes = {
            label: run(table[~table["holdout"]], THREE_TURNS) for label, table in contacts.items()
        }
        table = correlation_table(contacts, outcomes).set_index("stage")
        assert list(table.reset_index().columns) == list(CORRELATION_COLUMNS)
        declared = float(table.loc["declared", "difficulty"])
        latent = float(table.loc["latent", "difficulty"])
        observed = float(table.loc["observed", "difficulty"])
        outcome = float(table.loc["outcome", "resolution"])
        assert latent == pytest.approx(declared, abs=0.02)
        assert observed < latent
        assert 0.0 < outcome < observed / 3.0

    def test_a_design_effect_below_one_reports_no_error_rate_at_all(
        self, full: Dataset, correlated: Dataset
    ) -> None:
        """Wave 3 refuses to call a negative correlation an inflation, and that refusal is kept."""
        outcomes = {
            "independent": run(full.contacts[~full.contacts["holdout"]], THREE_TURNS),
            "correlated": run(correlated.contacts[~correlated.contacts["holdout"]], THREE_TURNS),
        }
        table = design_table(outcomes).set_index("world")
        assert list(table.reset_index().columns) == list(DESIGN_COLUMNS)
        assert table.loc["independent", "design_effect"] < 1.0
        assert np.isnan(table.loc["independent", "actual_alpha"])
        assert table.loc["correlated", "design_effect"] > 1.0
        assert table.loc["correlated", "actual_alpha"] > table.loc["correlated", "nominal_alpha"]


class TestTheCustomerFailedTwice:
    def test_the_correlated_world_fails_the_same_person_more_often(
        self, full: Dataset, correlated: Dataset
    ) -> None:
        outcomes = {
            "independent": run(full.contacts[~full.contacts["holdout"]], THREE_TURNS),
            "correlated": run(correlated.contacts[~correlated.contacts["holdout"]], THREE_TURNS),
        }
        table = pair_failures(outcomes).set_index("world")
        assert list(table.reset_index().columns) == list(PAIR_COLUMNS)
        assert table.loc["independent", "pairs"] == table.loc["correlated", "pairs"]
        assert table.loc["correlated", "both_failed"] > table.loc["independent", "both_failed"]
        assert table.loc["correlated", "ratio"] > table.loc["independent", "ratio"]

    def test_a_perfectly_correlated_customer_fails_both_or_neither(self) -> None:
        """The corner: with both contacts of a pair identical, both-failed is the failure rate.

        Four pairs, one of which fails twice. The failure rate is 0.25, so independence would expect
        0.0625 pairs failing twice and the observed share is 0.25 - a ratio of exactly four, which is
        one over the failure rate. Countable on paper, which is the only kind of case worth trusting.
        """
        rows = []
        for customer, failed in enumerate([True, False, False, False]):
            for _ in range(2):
                rows.append(
                    {
                        "customer": customer,
                        "resolved": not failed,
                        "is_repeat": False,
                        "outcome": "human-resolved",
                    }
                )
        table = pair_failures({"perfect": pd.DataFrame(rows)}).iloc[0]
        assert table["pairs"] == 4
        assert table["failure_rate"] == pytest.approx(0.25)
        assert table["both_failed"] == pytest.approx(0.25)
        assert table["expected_if_independent"] == pytest.approx(0.0625)
        assert table["ratio"] == pytest.approx(4.0)


class TestTheThreeStandardErrors:
    def test_the_usual_correction_costs_precision_where_there_is_nothing_to_correct(
        self, full: Dataset, correlated: Dataset
    ) -> None:
        """The result that needed the control world: averaging customer averages is not free."""
        treated, control = {}, {}
        for label, table in (("independent", full.contacts), ("correlated", correlated.contacts)):
            treated[label] = run(table[~table["holdout"]], THREE_TURNS)
            control[label] = run(table[table["holdout"]], HUMAN_ONLY)
        table = error_table(treated, control).set_index("world")
        assert list(table.reset_index().columns) == list(ERROR_COLUMNS)
        assert table.loc["independent", "cluster_mean_ratio"] > 1.10
        assert table.loc["independent", "corrected_ratio"] == pytest.approx(1.0, abs=0.01)
        assert table.loc["correlated", "corrected_ratio"] > 1.0
        assert (
            table.loc["correlated", "cluster_mean_ratio"]
            > table.loc["correlated", "corrected_ratio"]
        )

    def test_the_two_arms_have_to_be_the_same_two_worlds(self, full: Dataset) -> None:
        arm = run(full.contacts.head(50), THREE_TURNS)
        with pytest.raises(KeyError, match="control"):
            error_table({"a": arm}, {"b": arm})


class TestThePowerThatWasAssumed:
    def test_a_sizing_at_eighty_per_cent_has_eighty_per_cent_of_power(self) -> None:
        """The round trip that validates the formula against wave 3's, rather than against itself."""
        needed = contacts_for_difference(0.6355, 0.7271, power=0.8)
        assert power_at(1.0, 0.7271 - 0.6355, 0.6355, int(round(needed))) == pytest.approx(
            0.8, abs=0.01
        )

    def test_power_falls_as_the_design_effect_rises(self) -> None:
        values = [power_at(effect, 0.0916, 0.6355, 405) for effect in (1.0, 1.05, 1.3, 2.0)]
        assert values == sorted(values, reverse=True)

    def test_a_design_effect_below_one_is_refused(self) -> None:
        with pytest.raises(ValueError, match="at least one"):
            power_at(0.9, 0.05, 0.5, 100)

    def test_an_empty_arm_has_no_power(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            power_at(1.0, 0.05, 0.5, 0)

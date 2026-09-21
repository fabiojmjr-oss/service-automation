"""The regrouping, and the one invariant the whole wave rests on.

If reassigning contacts among customers changed anything about a contact, every comparison here would
be measuring two things. The test that matters most in this file is therefore the dullest one: the
per-contact figures in the regrouped world are the same objects, not similar numbers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from svclab.bot import HUMAN_ONLY, THREE_TURNS, run
from svclab.concentration import (
    BURDEN_COLUMNS,
    CONCENTRATION_COLUMNS,
    PRECISION_COLUMNS,
    burden_table,
    concentration_table,
    gini,
    precision_table,
)
from svclab.experiment import effective_cluster_size
from svclab.synth import (
    CONCENTRATION,
    EQUAL_RATES,
    ConcentrationProfile,
    Dataset,
    concentrated_dataset,
    correlated_dataset,
    propensity,
    reassign_customers,
)
from svclab.synth._draws import to_latent


class TestTheTwoShapeMeasures:
    def test_equal_clusters_have_no_inequality_and_no_extra_weight(self) -> None:
        """The corner both measures have to pass before either says anything about an account."""
        assert gini([3, 3, 3, 3]) == pytest.approx(0.0, abs=1e-12)
        assert effective_cluster_size([3, 3, 3, 3]) == pytest.approx(3.0, abs=1e-12)

    def test_one_customer_holding_everything_approaches_the_ceiling(self) -> None:
        """A finite set reaches ``1 - 1/n`` and not one, which is the honest upper end."""
        sizes = [0.0] * 99 + [100.0]
        assert gini(sizes) == pytest.approx(1.0 - 1.0 / 100.0, abs=1e-9)

    def test_the_effective_size_exceeds_the_mean_whenever_the_sizes_differ(self) -> None:
        """Two clusters of one and three: the mean is two and a contact's expected cluster is 2.5."""
        assert effective_cluster_size([1, 3]) == pytest.approx(2.5, abs=1e-12)
        assert np.mean([1, 3]) == pytest.approx(2.0, abs=1e-12)

    def test_an_empty_or_weightless_set_is_refused(self) -> None:
        for call in (gini, effective_cluster_size):
            with pytest.raises(ValueError, match="at least one"):
                call([])
            with pytest.raises(ValueError, match="zero"):
                call([0.0, 0.0])


class TestThePropensity:
    def test_no_dispersion_makes_every_customer_equally_likely(self, full: Dataset) -> None:
        weights = propensity(full.customer_components, EQUAL_RATES)
        assert weights == pytest.approx(np.ones(weights.size), abs=1e-12)

    def test_a_negative_dispersion_is_refused(self, full: Dataset) -> None:
        with pytest.raises(ValueError, match="not negative"):
            propensity(full.customer_components, ConcentrationProfile(-0.1, 0.0))

    def test_the_rate_correlates_with_difficulty_by_what_was_declared(self, full: Dataset) -> None:
        """The declared number is a latent correlation, so it is checked on the latent scale."""
        weights = propensity(full.customer_components, CONCENTRATION)
        latent_rate = np.log(weights) / CONCENTRATION.dispersion
        latent_difficulty = to_latent(
            full.customer_components["difficulty_percentile"].to_numpy(dtype=float)
        )
        measured = float(np.corrcoef(latent_rate, latent_difficulty)[0, 1])
        assert measured == pytest.approx(CONCENTRATION.difficulty_correlation, abs=0.02)


class TestTheRegrouping:
    def test_every_contact_keeps_its_arm_and_every_trait(self, full: Dataset) -> None:
        table = reassign_customers(full.contacts, full.customer_components)
        assert (table["contact"] == full.contacts["contact"]).all()
        assert (table["holdout"] == full.contacts["holdout"]).all()
        for column in ("difficulty", "human_seconds", "patience_turns", "classifier_draw"):
            assert (table[column] == full.contacts[column]).all(), column
        assert table.groupby("customer")["holdout"].nunique().max() == 1

    def test_the_per_contact_figures_are_the_same_objects(self, full: Dataset) -> None:
        """The invariant the wave rests on, asserted exactly rather than to a tolerance."""
        regrouped = concentrated_dataset(full).contacts
        for table in (full.contacts, regrouped):
            outcomes = run(table[~table["holdout"]], THREE_TURNS)
            first = outcomes[~outcomes["is_repeat"]]
            if table is full.contacts:
                published = (
                    len(first),
                    float(first["resolved"].astype(float).sum()),
                    float(outcomes["human_seconds"].sum()),
                )
            else:
                assert (
                    len(first),
                    float(first["resolved"].astype(float).sum()),
                    float(outcomes["human_seconds"].sum()),
                ) == published

    def test_a_table_without_the_kept_uniform_is_refused(self, full: Dataset) -> None:
        with pytest.raises(KeyError, match="u_customer"):
            reassign_customers(full.contacts.drop(columns=["u_customer"]), full.customer_components)

    def test_more_dispersion_concentrates_more(self, full: Dataset) -> None:
        shapes = []
        for dispersion in (0.0, 0.5, 1.5):
            table = reassign_customers(
                full.contacts,
                full.customer_components,
                ConcentrationProfile(dispersion, 0.4),
            )
            sizes = table.groupby("customer").size()
            shapes.append((gini(sizes), effective_cluster_size(sizes)))
        assert [value for value, _ in shapes] == sorted(value for value, _ in shapes)
        assert [value for _, value in shapes] == sorted(value for _, value in shapes)


@pytest.fixture(scope="session")
def regrouped(full: Dataset) -> dict[str, pd.DataFrame]:
    """The two worlds wave 5 compares: equal rates as the control, and the declared concentration."""
    return {
        "equal rates": correlated_dataset(concentrated_dataset(full, EQUAL_RATES)).contacts,
        "concentrated": correlated_dataset(concentrated_dataset(full)).contacts,
    }


class TestWhatTheTablesSay:
    def test_the_control_world_has_no_link_between_rate_and_difficulty(
        self, regrouped: dict[str, pd.DataFrame]
    ) -> None:
        treated = {name: table[~table["holdout"]] for name, table in regrouped.items()}
        table = concentration_table(treated).set_index("world")
        assert list(table.reset_index().columns) == list(CONCENTRATION_COLUMNS)
        assert abs(float(table.loc["equal rates", "frequency_difficulty_correlation"])) < 0.02
        assert float(table.loc["concentrated", "frequency_difficulty_correlation"]) > 0.10
        assert float(table.loc["concentrated", "gini"]) > float(table.loc["equal rates", "gini"])
        assert float(table.loc["concentrated", "effective_cluster_size"]) > float(
            table.loc["equal rates", "effective_cluster_size"]
        )
        assert int(table.loc["concentrated", "contacts"]) == int(
            table.loc["equal rates", "contacts"]
        )

    def test_an_empty_world_is_refused(self, regrouped: dict[str, pd.DataFrame]) -> None:
        with pytest.raises(ValueError, match="no contacts"):
            concentration_table({"empty": regrouped["concentrated"].head(0)})

    def test_the_cost_concentrates_faster_than_the_volume(
        self, regrouped: dict[str, pd.DataFrame]
    ) -> None:
        """In the control the three shares are one number; concentration separates them."""
        treated = {name: table[~table["holdout"]] for name, table in regrouped.items()}
        outcomes = {name: run(table, THREE_TURNS) for name, table in treated.items()}
        table = burden_table(treated, outcomes).set_index("world")
        assert list(table.reset_index().columns) == list(BURDEN_COLUMNS)
        control = table.loc["equal rates"]
        assert float(control["top_decile_unresolved"]) == pytest.approx(
            float(control["top_decile_volume"]), abs=0.005
        )
        assert float(control["top_decile_human_hours"]) == pytest.approx(
            float(control["top_decile_volume"]), abs=0.005
        )
        heavy = table.loc["concentrated"]
        assert float(heavy["top_decile_human_hours"]) > float(heavy["top_decile_volume"]) + 0.02
        assert float(heavy["difficulty_per_contact"]) > float(control["difficulty_per_contact"])
        assert float(heavy["resolution_rate"]) < float(control["resolution_rate"])
        assert int(heavy["customers_failed_three_times"]) > int(
            control["customers_failed_three_times"]
        )

    def test_the_two_mappings_have_to_describe_the_same_worlds(
        self, regrouped: dict[str, pd.DataFrame]
    ) -> None:
        treated = {name: table[~table["holdout"]] for name, table in regrouped.items()}
        outcomes = {"concentrated": run(treated["concentrated"], THREE_TURNS)}
        with pytest.raises(KeyError, match="outcomes"):
            burden_table(treated, outcomes)

    def test_the_business_cases_estimate_loses_precision(
        self, regrouped: dict[str, pd.DataFrame]
    ) -> None:
        treated, control = {}, {}
        for name, table in regrouped.items():
            treated[name] = run(table[~table["holdout"]], THREE_TURNS)
            control[name] = run(table[table["holdout"]], HUMAN_ONLY)
        table = precision_table(treated, control).set_index("world")
        assert list(table.reset_index().columns) == list(PRECISION_COLUMNS)
        assert float(table.loc["concentrated", "relative_error"]) > float(
            table.loc["equal rates", "relative_error"]
        )
        assert float(table.loc["concentrated", "interval_width"]) > float(
            table.loc["equal rates", "interval_width"]
        )
        assert int(table.loc["concentrated", "customers"]) < int(
            table.loc["equal rates", "customers"]
        )

    def test_the_two_arms_have_to_be_the_same_two_worlds(
        self, regrouped: dict[str, pd.DataFrame]
    ) -> None:
        arm = run(regrouped["concentrated"].head(50), THREE_TURNS)
        with pytest.raises(KeyError, match="control"):
            precision_table({"a": arm}, {"b": arm})

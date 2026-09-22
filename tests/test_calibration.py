"""The calibrators, and the controls that decide what a calibration is worth.

Three tests carry this wave. One fits both calibrators on a score that **is** a probability and demands
they leave it alone, because a calibrator that moves an already-calibrated score is adding bias to fix
nothing. One drives the amended threshold's benefit term to zero and demands it equal the original
closed form exactly, which is the algebra rather than a resemblance. And one asserts the property the
whole module rests on: a monotone map cannot change the order of the contacts, so every calibrated
score has to rank them exactly as the raw one did.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from svclab.bot import THREE_TURNS, classifier_labels
from svclab.calibration import (
    ALWAYS_DEFER,
    FORMULA_COLUMNS,
    KEY_COLUMNS,
    OPTIMISM_COLUMNS,
    RELIABILITY_COLUMNS,
    amended_threshold,
    calibrated_scores,
    expected_calibration_error,
    fit_period,
    formula_table,
    intent_labels,
    isotonic,
    isotonic_at,
    key_table,
    optimism_table,
    platt,
    platt_at,
    price,
    reliability_table,
    resolve_benefit,
    swept,
    true_probability,
)
from svclab.calibration.score import _pool_adjacent_violators
from svclab.routing import calibrated_threshold
from svclab.synth import CALIBRATION, CENTRE, ROUTING, CalibrationProfile, Dataset

#: A grid coarse enough to sweep in a fast test and still contain a minimum.
COARSE = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)


def treated_with_labels(data: Dataset) -> pd.DataFrame:
    """The treated arm, carrying the label the classifier reported."""
    frame = data.contacts[~data.contacts["holdout"]].copy()
    labels = classifier_labels(frame)
    return frame.merge(labels[["contact", "predicted_intent"]], on="contact", how="left")


class TestThePeriodSplit:
    def test_the_split_is_the_declared_share_of_the_calendar(self, full: Dataset) -> None:
        fitting = fit_period(full.contacts)
        boundary = CALIBRATION.fit_share * CENTRE.days * 24.0
        hour = full.contacts["arrival_hour"].to_numpy(dtype=float)
        assert np.array_equal(fitting, hour < boundary)
        # Arrivals are uniform over the period, so the share of contacts lands on the share of time.
        assert float(fitting.mean()) == pytest.approx(CALIBRATION.fit_share, abs=5e-3)

    def test_a_table_with_no_arrival_hour_is_refused(self) -> None:
        with pytest.raises(KeyError, match="arrival_hour"):
            fit_period(pd.DataFrame({"contact": [1, 2]}))

    def test_a_share_that_empties_a_part_is_refused(self, full: Dataset) -> None:
        for share in (0.0, 1.0, -0.5, 2.0):
            profile = CalibrationProfile(share, 10, 100, 1e-10)
            with pytest.raises(ValueError, match="leaves one of the two parts empty"):
                fit_period(full.contacts, profile)


def pooled(values: np.ndarray) -> np.ndarray:
    """The monotone fit at equal weights, which is the case the algorithm is easiest to read on."""
    return _pool_adjacent_violators(values, np.ones(len(values)))


class TestTheControlScore:
    def test_the_control_is_the_declared_accuracy_curve(self, full: Dataset) -> None:
        value = true_probability(full.contacts)
        assert value.min() >= 0.0 and value.max() <= 1.0
        # It is the prior probability, so it has to average to the share of labels that are right.
        correct = classifier_labels(full.contacts)["classified_correctly"].to_numpy(dtype=bool)
        assert float(value.mean()) == pytest.approx(float(correct.mean()), abs=5e-3)

    def test_a_table_without_the_columns_the_curve_needs_is_refused(self) -> None:
        with pytest.raises(KeyError, match="difficulty"):
            true_probability(pd.DataFrame({"intent": ["rastreio"]}))


class TestPoolAdjacentViolators:
    def test_a_sequence_already_ordered_is_returned_unchanged(self) -> None:
        values = np.array([0.0, 0.25, 0.5, 1.0])
        assert np.allclose(pooled(values), values)

    def test_a_violation_is_replaced_by_the_mean_of_its_block(self) -> None:
        assert np.allclose(pooled(np.array([1.0, 0.0])), [0.5, 0.5])
        assert np.allclose(pooled(np.array([1.0, 0.0, 1.0, 1.0])), [0.5, 0.5, 1.0, 1.0])

    def test_a_cascade_merges_more_than_two_blocks(self) -> None:
        # Every prefix mean exceeds the next value, so the whole sequence collapses to one block.
        assert np.allclose(pooled(np.array([3.0, 2.0, 1.0])), [2.0, 2.0, 2.0])

    def test_the_fit_is_the_least_squares_monotone_one(self) -> None:
        """Checked against the definition: no monotone sequence is closer."""
        values = np.array([0.0, 1.0, 0.0, 1.0, 0.0])
        fitted = pooled(values)
        assert np.allclose(fitted, [0.0, 0.5, 0.5, 0.5, 0.5])
        assert float(((values - fitted) ** 2).sum()) == pytest.approx(1.0, abs=1e-12)
        for candidate in (
            np.array([0.0, 0.4, 0.5, 0.5, 0.6]),
            np.array([0.4, 0.4, 0.4, 0.4, 0.4]),
            np.array([0.0, 0.0, 0.5, 0.5, 1.0]),
        ):
            assert ((values - candidate) ** 2).sum() >= ((values - fitted) ** 2).sum() - 1e-12

    def test_a_weighted_point_counts_for_as_many_observations_as_it_stands_for(self) -> None:
        """Two values, one of them nine observations: the merged mean is theirs, not their average."""
        fitted = _pool_adjacent_violators(np.array([1.0, 0.0]), np.array([1.0, 9.0]))
        assert np.allclose(fitted, [0.1, 0.1])


class TestIsotonic:
    def test_the_map_is_non_decreasing_and_reaches_the_observed_rates(self) -> None:
        score = np.array([0.1, 0.2, 0.3, 0.4])
        knots, values = isotonic(score, np.array([False, False, True, True]))
        assert np.array_equal(knots, score)
        assert np.all(np.diff(values) >= 0.0)
        assert np.allclose(values, [0.0, 0.0, 1.0, 1.0])

    def test_repeated_scores_collapse_onto_one_knot_at_their_own_rate(self) -> None:
        """Three contacts on one score, two of them right: the knot is two thirds, not a staircase."""
        knots, values = isotonic(
            np.array([0.5, 0.5, 0.5, 0.9]), np.array([True, False, True, True])
        )
        assert np.allclose(knots, [0.5, 0.9])
        assert values[0] == pytest.approx(2.0 / 3.0)
        assert values[1] == pytest.approx(1.0)

    def test_the_fit_does_not_depend_on_the_order_the_ties_arrived_in(self) -> None:
        score = np.array([0.5, 0.5, 0.5, 0.9])
        first = isotonic(score, np.array([True, False, True, True]))
        second = isotonic(score, np.array([False, True, True, True]))
        assert np.allclose(first[0], second[0])
        assert np.allclose(first[1], second[1])

    def test_reading_outside_the_fitted_range_is_flat(self) -> None:
        knots, values = isotonic(np.array([0.4, 0.6]), np.array([False, True]))
        read = isotonic_at(knots, values, np.array([0.0, 0.4, 0.5, 0.6, 1.0]))
        assert read[0] == pytest.approx(read[1])
        assert read[-1] == pytest.approx(read[-2])
        assert read[2] == pytest.approx(0.5)

    def test_mismatched_or_empty_inputs_are_refused(self) -> None:
        with pytest.raises(ValueError, match="not the same length"):
            isotonic(np.array([0.1, 0.2]), np.array([True]))
        with pytest.raises(ValueError, match="nothing to fit"):
            isotonic(np.array([]), np.array([]))


class TestPlatt:
    def test_the_fit_recovers_a_logistic_it_was_given(self) -> None:
        """A control: a sample whose rate at every score *is* a logistic curve, fitted back to it."""
        points = np.linspace(0.0, 1.0, 101)
        probability = 1.0 / (1.0 + np.exp(-(4.0 * points - 2.0)))
        per_point = 400
        score = np.repeat(points, per_point)
        correct = np.concatenate(
            [np.arange(per_point) < round(per_point * value) for value in probability]
        )
        slope, intercept = platt(score, correct)
        assert slope == pytest.approx(4.0, abs=0.05)
        assert intercept == pytest.approx(-2.0, abs=0.05)

    def test_the_fitted_probability_is_monotone_in_the_score(self) -> None:
        slope, intercept = 3.0, -1.0
        read = platt_at(slope, intercept, np.linspace(0.0, 1.0, 50))
        assert np.all(np.diff(read) > 0.0)
        assert read.min() > 0.0 and read.max() < 1.0

    def test_a_fit_with_no_unique_answer_is_refused(self) -> None:
        constant = np.full(50, 0.5)
        with pytest.raises(ValueError, match="no unique answer"):
            platt(constant, np.array([True, False] * 25))

    def test_mismatched_or_empty_inputs_are_refused(self) -> None:
        with pytest.raises(ValueError, match="not the same length"):
            platt(np.array([0.1, 0.2]), np.array([True]))
        with pytest.raises(ValueError, match="nothing to fit"):
            platt(np.array([]), np.array([]))

    def test_the_step_limit_is_respected(self) -> None:
        """One step from the origin is a single Newton update, not a converged fit."""
        profile = CalibrationProfile(0.6, 10, 1, 1e-10)
        score = np.linspace(0.0, 1.0, 1_000)
        # Not separable: a perfectly separable sample has no maximum likelihood to converge to.
        correct = (score > 0.4) ^ (np.arange(len(score)) % 7 == 0)
        one = platt(score, correct, profile)
        many = platt(score, correct, CalibrationProfile(0.6, 10, 50, 1e-10))
        assert one != many


class TestReliability:
    def test_a_perfectly_calibrated_score_has_no_gap(self) -> None:
        """The control the whole table exists to be read against."""
        score = np.repeat(np.array([0.05, 0.45, 0.95]), 2_000)
        correct = np.concatenate(
            [
                np.arange(2_000) < 100,
                np.arange(2_000) < 900,
                np.arange(2_000) < 1_900,
            ]
        )
        table = reliability_table(score, correct)
        assert list(table.columns) == list(RELIABILITY_COLUMNS)
        assert np.allclose(table["gap"].to_numpy(dtype=float), 0.0, atol=1e-12)
        assert expected_calibration_error(table) == pytest.approx(0.0, abs=1e-12)

    def test_empty_bins_are_not_rows(self) -> None:
        table = reliability_table(np.array([0.05, 0.95]), np.array([False, True]))
        assert len(table) == 2
        assert set(table["bin"]) == {0, 9}

    def test_a_score_of_exactly_one_falls_in_the_last_bin(self) -> None:
        table = reliability_table(np.array([1.0]), np.array([True]))
        assert int(table["bin"].iloc[0]) == CALIBRATION.bins - 1

    def test_the_error_is_volume_weighted(self) -> None:
        table = pd.DataFrame(
            {
                "bin": [0, 1],
                "lower": [0.0, 0.1],
                "upper": [0.1, 0.2],
                "contacts": [1.0, 9.0],
                "mean_score": [0.05, 0.15],
                "share_correct": [0.15, 0.05],
                "gap": [0.10, -0.10],
            }
        )
        assert expected_calibration_error(table) == pytest.approx(0.10)

    def test_a_study_of_nothing_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no calibration error"):
            expected_calibration_error(reliability_table(np.array([]), np.array([])))

    def test_mismatched_inputs_and_an_empty_binning_are_refused(self) -> None:
        with pytest.raises(ValueError, match="not the same length"):
            reliability_table(np.array([0.1]), np.array([True, False]))
        with pytest.raises(ValueError, match="at least one bin"):
            reliability_table(
                np.array([0.1]), np.array([True]), CalibrationProfile(0.6, 0, 100, 1e-10)
            )


class TestTheAmendedThreshold:
    def test_at_no_benefit_it_is_the_original_closed_form(self) -> None:
        """The algebra, not a resemblance: the term that was missing is set to zero."""
        for seconds in ROUTING.misroute_seconds.values():
            assert amended_threshold(ROUTING.defer_seconds, seconds, 0.0) == pytest.approx(
                calibrated_threshold(ROUTING.defer_seconds, seconds), abs=1e-12
            )

    def test_a_benefit_only_ever_lowers_the_threshold(self) -> None:
        previous = amended_threshold(20.0, 540.0, 0.0)
        for benefit in (1.0, 10.0, 100.0, 1_000.0):
            value = amended_threshold(20.0, 540.0, benefit)
            assert value <= previous
            previous = value
        assert previous == pytest.approx((540.0 - 20.0) / (540.0 + 1_000.0))

    def test_the_refusals_are_the_ones_the_original_makes_plus_the_new_one(self) -> None:
        with pytest.raises(ValueError, match="negative benefit"):
            amended_threshold(20.0, 540.0, -1.0)
        with pytest.raises(ValueError, match="cannot be negative"):
            amended_threshold(-1.0, 540.0, 10.0)
        with pytest.raises(ValueError, match="cannot be negative"):
            amended_threshold(20.0, -1.0, 10.0)
        with pytest.raises(ValueError, match="does not imply a threshold"):
            amended_threshold(20.0, 0.0, 10.0)


class TestCalibratingThisAccount:
    def test_every_calibrated_score_ranks_the_contacts_exactly_as_the_raw_one_did(
        self, full: Dataset
    ) -> None:
        """The property the module rests on: a monotone map cannot reorder anything."""
        treated = treated_with_labels(full)
        versions = calibrated_scores(treated, full.routing_scores)
        raw = versions["raw"]["classifier_score"].to_numpy(dtype=float)
        order = np.argsort(raw, kind="stable")
        for name in ("isotonic", "platt"):
            value = versions[name]["classifier_score"].to_numpy(dtype=float)
            assert np.all(np.diff(value[order]) >= -1e-12), name

    def test_a_calibrator_leaves_an_already_calibrated_score_where_it_is(
        self, full: Dataset
    ) -> None:
        """A calibrator that moves the control is adding bias to correct nothing."""
        treated = treated_with_labels(full)
        correct = classifier_labels(treated)["classified_correctly"].to_numpy(dtype=bool)
        truth = calibrated_scores(treated, full.routing_scores)["true"][
            "classifier_score"
        ].to_numpy(dtype=float)
        fitting = fit_period(treated)
        knots, values = isotonic(truth[fitting], correct[fitting])
        slope, intercept = platt(truth[fitting], correct[fitting])
        for read in (
            isotonic_at(knots, values, truth[~fitting]),
            platt_at(slope, intercept, truth[~fitting]),
        ):
            error = expected_calibration_error(reliability_table(read, correct[~fitting]))
            assert error < 0.02

    def test_the_calibrated_scores_stay_probabilities(self, full: Dataset) -> None:
        treated = treated_with_labels(full)
        for name, frame in calibrated_scores(treated, full.routing_scores).items():
            value = frame["classifier_score"].to_numpy(dtype=float)
            assert value.min() >= 0.0 and value.max() <= 1.0, name
            assert len(frame) == len(treated), name


class TestPricingARule:
    def test_pricing_nothing_is_refused(self, full: Dataset) -> None:
        treated = treated_with_labels(full)
        with pytest.raises(ValueError, match="no contacts to price"):
            price(treated.head(0), full.routing_scores, 0.5)

    def test_deferring_everything_costs_the_declared_deferral_on_every_contact(
        self, full: Dataset
    ) -> None:
        treated = treated_with_labels(full).head(2_000)
        everything = price(treated, full.routing_scores, ALWAYS_DEFER)
        assert everything["deferred"] == float(len(treated))
        assert everything["misroutes"] == 0.0

    def test_attempting_everything_defers_nothing(self, full: Dataset) -> None:
        treated = treated_with_labels(full).head(2_000)
        assert price(treated, full.routing_scores, 0.0)["deferred"] == 0.0

    def test_an_empty_grid_and_an_unknown_key_are_refused(self, full: Dataset) -> None:
        treated = treated_with_labels(full).head(500)
        with pytest.raises(ValueError, match="no thresholds to sweep"):
            swept(treated, full.routing_scores, THREE_TURNS, "intent", ())
        with pytest.raises(KeyError, match="group the intents by"):
            swept(treated, full.routing_scores, THREE_TURNS, "nonsense", COARSE)

    def test_the_sweep_returns_a_threshold_from_the_grid_for_every_intent(
        self, full: Dataset
    ) -> None:
        treated = treated_with_labels(full).head(4_000)
        chosen = swept(treated, full.routing_scores, THREE_TURNS, "intent", COARSE)
        assert set(chosen) == set(intent_labels())
        assert all(value in COARSE for value in chosen.values())


class TestTheBenefit:
    def test_the_benefit_is_positive_on_every_intent(self, full: Dataset) -> None:
        """A bot that saved nothing on the contacts it gets right would have no case at all."""
        treated = treated_with_labels(full)
        measured = resolve_benefit(treated[fit_period(treated)], full.routing_scores)
        assert set(measured) == set(intent_labels())
        assert all(value > 0.0 for value in measured.values())

    def test_the_benefit_does_not_depend_on_which_score_is_passed(self, full: Dataset) -> None:
        """Both runs are blanket decisions, so the score is only ever ignored."""
        treated = treated_with_labels(full).head(3_000)
        versions = calibrated_scores(treated_with_labels(full), full.routing_scores)
        first = resolve_benefit(treated, versions["raw"])
        second = resolve_benefit(treated, versions["isotonic"])
        assert first == second

    def test_measuring_a_benefit_on_nothing_is_refused(self, full: Dataset) -> None:
        treated = treated_with_labels(full)
        with pytest.raises(ValueError, match="no contacts to measure"):
            resolve_benefit(treated.head(0), full.routing_scores)

    def test_an_intent_with_no_correct_label_is_refused(self, full: Dataset) -> None:
        treated = treated_with_labels(full)
        wrong = treated[~classifier_labels(treated)["classified_correctly"].to_numpy(dtype=bool)]
        only = wrong[wrong["intent"] == "reclamacao"].head(50)
        with pytest.raises(ValueError, match="no correctly labelled"):
            resolve_benefit(only, full.routing_scores)


class TestTheTables:
    def test_the_formula_table_has_a_row_per_score_and_the_declared_columns(
        self, full: Dataset
    ) -> None:
        treated = treated_with_labels(full).head(6_000)
        table = formula_table(treated, full.routing_scores, THREE_TURNS, COARSE)
        assert list(table.columns) == list(FORMULA_COLUMNS)
        assert list(table["score"]) == ["raw", "isotonic", "platt", "true"]
        # The sweep is the floor by construction, so no rule on the same score can beat it.
        assert (table["naive_penalty"] >= -1e-12).all()
        assert (table["amended_penalty"] >= -1e-12).all()

    def test_the_optimism_table_ends_with_the_queue(self, full: Dataset) -> None:
        treated = treated_with_labels(full).head(6_000)
        table = optimism_table(treated, full.routing_scores, THREE_TURNS, COARSE)
        assert list(table.columns) == list(OPTIMISM_COLUMNS)
        assert table["intent"].iloc[-1] == "queue"
        assert np.isnan(table["fitted_threshold"].iloc[-1])
        # The later period's own best cannot be beaten on the later period.
        assert (table["optimism"] >= -1e-12).all()

    def test_the_key_table_prices_both_keys_against_one_threshold(self, full: Dataset) -> None:
        treated = treated_with_labels(full).head(6_000)
        table = key_table(treated, full.routing_scores, THREE_TURNS, COARSE)
        assert list(table.columns) == list(KEY_COLUMNS)
        assert list(table["key"]) == ["single", "intent", "predicted_intent"]
        assert table["saving_against_single"].iloc[0] == 0.0

    def test_a_table_without_the_predicted_label_is_refused(self, full: Dataset) -> None:
        treated = full.contacts[~full.contacts["holdout"]].head(500)
        with pytest.raises(KeyError, match="no predicted_intent"):
            key_table(treated, full.routing_scores, THREE_TURNS, COARSE)

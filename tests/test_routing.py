"""The routing threshold, against its closed form and the accounting identity behind every cost.

Two controls carry this file. The cost-minimising threshold on a calibrated score has a closed form -
defer below ``1 - defer_cost / misroute_cost`` - which is checked against algebra at both ends and in
the middle. And every cost this module reports has to be the sum of the three things that are paid, so
that a figure cannot drift from its own components.
"""

from __future__ import annotations

import numpy as np
import pytest

from svclab.bot import THREE_TURNS, run
from svclab.routing import (
    COST_COLUMNS,
    best_by,
    calibrated_threshold,
    cost_curve,
    cost_of,
    defer_below,
)
from svclab.synth import ROUTING, Dataset


class TestTheClosedForm:
    def test_the_threshold_is_one_minus_the_cost_ratio(self) -> None:
        for defer, misroute in ((20.0, 60.0), (20.0, 540.0), (1.0, 2.0), (5.0, 1000.0)):
            assert calibrated_threshold(defer, misroute) == pytest.approx(
                1.0 - defer / misroute, abs=1e-15
            )

    def test_a_free_deferral_means_never_let_the_bot_try(self) -> None:
        """At a deferral cost of zero the threshold is one: nothing clears it."""
        assert calibrated_threshold(0.0, 100.0) == pytest.approx(1.0, abs=1e-15)

    def test_a_deferral_as_expensive_as_a_misroute_means_always_try(self) -> None:
        assert calibrated_threshold(100.0, 100.0) == pytest.approx(0.0, abs=1e-15)
        assert calibrated_threshold(500.0, 100.0) == pytest.approx(0.0, abs=1e-15)

    def test_the_ordering_follows_the_cost_of_a_mistake(self) -> None:
        """More expensive mistakes buy more caution, which is the only part of the formula that
        survives being applied to an uncalibrated score."""
        thresholds = [
            calibrated_threshold(ROUTING.defer_seconds, ROUTING.misroute_seconds[intent])
            for intent in ("rastreio", "prazo-de-entrega", "cadastro", "reembolso", "reclamacao")
        ]
        assert thresholds == sorted(thresholds)

    def test_impossible_costs_are_refused(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            calibrated_threshold(-1.0, 10.0)
        with pytest.raises(ValueError, match="cannot be negative"):
            calibrated_threshold(1.0, -10.0)
        with pytest.raises(ValueError, match="does not imply a threshold"):
            calibrated_threshold(1.0, 0.0)


class TestTheDeferralDecision:
    def test_a_threshold_of_zero_defers_nothing_and_one_defers_almost_everything(
        self, full: Dataset
    ) -> None:
        sample = full.contacts.head(3_000)
        assert not defer_below(sample, full.routing_scores, 0.0)["defer"].any()
        assert defer_below(sample, full.routing_scores, 1.0)["defer"].mean() > 0.9

    def test_a_per_intent_mapping_keys_on_the_true_intent_of_each_contact(
        self, full: Dataset
    ) -> None:
        sample = full.contacts.head(3_000)
        thresholds = dict.fromkeys(ROUTING.misroute_seconds, 0.0)
        thresholds["reclamacao"] = 1.0
        routed = defer_below(sample, full.routing_scores, thresholds)
        assert routed[routed["intent"] == "reclamacao"]["defer"].mean() > 0.9
        assert not routed[routed["intent"] == "rastreio"]["defer"].any()

    def test_a_missing_per_intent_threshold_is_an_error(self, full: Dataset) -> None:
        sample = full.contacts.head(500)
        with pytest.raises(KeyError, match="no threshold for"):
            defer_below(sample, full.routing_scores, {"rastreio": 0.5})

    def test_the_session_honours_the_deferral(self, full: Dataset) -> None:
        """The whole composition: the router marks, the session obeys, and the route column says so."""
        sample = full.contacts[~full.contacts["holdout"]].head(3_000)
        routed = defer_below(sample, full.routing_scores, 0.6)
        outcomes = run(routed, THREE_TURNS)
        first = outcomes[~outcomes["is_repeat"]]
        deferred = first[first["route"] == "deferred"]
        assert len(deferred) == int(routed["defer"].sum())
        assert deferred["handled_by_human"].all()
        assert (deferred["bot_turns"] == 0).all()

    def test_a_contact_table_without_the_column_defers_nothing(self, full: Dataset) -> None:
        """Which is what keeps every figure published before this column existed unaffected by it."""
        sample = full.contacts[~full.contacts["holdout"]].head(3_000)
        plain = run(sample, THREE_TURNS)
        marked = run(sample.assign(defer=False), THREE_TURNS)
        assert plain.equals(marked)


class TestTheAccounting:
    def test_the_total_is_the_sum_of_what_is_paid(self, full: Dataset) -> None:
        sample = full.contacts[~full.contacts["holdout"]].head(6_000)
        curve = cost_curve(sample, full.routing_scores, THREE_TURNS, (0.2, 0.5, 0.8))
        assert tuple(curve.columns) == COST_COLUMNS
        for _, row in curve.iterrows():
            parts = row["human_seconds"] + row["misroute_seconds"] + row["defer_seconds"]
            assert float(row["total_seconds"]) == pytest.approx(parts, rel=1e-12)
            assert float(row["seconds_per_contact"]) == pytest.approx(
                float(row["total_seconds"]) / len(sample), rel=1e-12
            )

    def test_deferring_more_leaves_fewer_misroutes_and_costs_more_deferrals(
        self, full: Dataset
    ) -> None:
        sample = full.contacts[~full.contacts["holdout"]].head(6_000)
        curve = cost_curve(sample, full.routing_scores, THREE_TURNS, (0.1, 0.4, 0.7, 0.95))
        assert list(curve["misroutes"]) == sorted(curve["misroutes"], reverse=True)
        assert list(curve["defer_seconds"]) == sorted(curve["defer_seconds"])
        assert list(curve["deferred_share"]) == sorted(curve["deferred_share"])

    def test_a_misroute_is_only_counted_where_the_bot_was_allowed_to_try(
        self, full: Dataset
    ) -> None:
        sample = full.contacts[~full.contacts["holdout"]].head(4_000)
        # Above one rather than at one: the score is clipped into the unit interval, so a threshold of
        # exactly 1.0 still lets through the contacts sitting on the ceiling. That is what `<` means
        # and it is worth a line here, because the first version of this test assumed otherwise.
        routed = defer_below(sample, full.routing_scores, 1.5)
        assert routed["defer"].all()
        measured = cost_of(run(routed, THREE_TURNS), routed)
        assert measured["bot_attempts"] == pytest.approx(0.0)
        assert measured["misroutes"] == pytest.approx(0.0)
        assert measured["misroute_seconds"] == pytest.approx(0.0)
        at_the_ceiling = defer_below(sample, full.routing_scores, 1.0)
        assert not at_the_ceiling["defer"].all()

    def test_an_empty_threshold_list_is_refused(self, full: Dataset) -> None:
        with pytest.raises(ValueError, match="no thresholds to price"):
            cost_curve(full.contacts.head(100), full.routing_scores, THREE_TURNS, ())

    def test_an_unknown_column_cannot_be_optimised(self, full: Dataset) -> None:
        curve = cost_curve(
            full.contacts[~full.contacts["holdout"]].head(2_000),
            full.routing_scores,
            THREE_TURNS,
            (0.3, 0.6),
        )
        with pytest.raises(KeyError, match="is not a column of this curve"):
            best_by(curve, "profit", True)


class TestOnTheRealAccount:
    def test_the_score_ranks_correctness_without_being_calibrated_to_it(
        self, full: Dataset
    ) -> None:
        """Informative, which is why a threshold works at all; not a probability, which is why the
        closed form is the wrong number to use for one."""
        sample = full.contacts[~full.contacts["holdout"]].head(8_000)
        routed = defer_below(sample, full.routing_scores, 0.0)
        outcomes = run(routed, THREE_TURNS)
        first = outcomes[~outcomes["is_repeat"]].set_index("contact")
        correct = first["classified_correctly"].reindex(routed["contact"]).to_numpy(dtype=bool)
        score = routed["classifier_score"].to_numpy(dtype=float)
        assert score[correct].mean() > score[~correct].mean() + 0.15
        # A calibrated score would have the share correct above any cut equal to the cut. This one
        # does not, and by a wide margin, which is the finding rather than a defect.
        for cut in (0.6, 0.7, 0.8):
            above = correct[score >= cut].mean()
            assert above > cut + 0.10

    def test_the_two_objectives_do_not_agree(self, full: Dataset) -> None:
        """The wave's first claim as a direction. The figures belong in the claims suite."""
        treated = full.contacts[~full.contacts["holdout"]]
        thresholds = tuple(round(value, 2) for value in np.arange(0.30, 0.71, 0.02))
        curve = cost_curve(treated, full.routing_scores, THREE_TURNS, thresholds)
        accuracy = best_by(curve, "label_accuracy", True)
        cost = best_by(curve, "seconds_per_contact", False)
        assert accuracy != cost
        indexed = curve.set_index("threshold")
        assert float(indexed.loc[accuracy, "seconds_per_contact"]) > float(
            indexed.loc[cost, "seconds_per_contact"]
        )

    def test_the_closed_form_is_worse_than_sweeping_on_this_uncalibrated_score(
        self, full: Dataset
    ) -> None:
        """The claim that corrected this module's first docstring."""
        treated = full.contacts[~full.contacts["holdout"]]
        swept = cost_curve(treated, full.routing_scores, THREE_TURNS, (0.48,))
        formula = {
            intent: calibrated_threshold(ROUTING.defer_seconds, seconds)
            for intent, seconds in ROUTING.misroute_seconds.items()
        }
        routed = defer_below(treated, full.routing_scores, formula)
        measured = cost_of(run(routed, THREE_TURNS), routed)
        total = measured["human_seconds"] + measured["misroute_seconds"] + measured["defer_seconds"]
        assert total / len(routed) > float(swept["seconds_per_contact"].iloc[0])

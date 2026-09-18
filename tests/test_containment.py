"""Containment and deflection, against fractions worked out by hand and a noiseless control.

The containment rates are checked on ten sessions whose four numerators are countable on fingers,
because a rate computed over a simulated dataset can only be checked against another computation.
Deflection is checked on two arms whose difference is exactly one contact per customer with no spread
at all - the case an estimator has to get exactly right before its answer on noisy data means
anything.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from svclab.bot import HUMAN_ONLY, THREE_TURNS, run
from svclab.containment import (
    CONTAINMENT_COLUMNS,
    SELECTION_COLUMNS,
    containment_table,
    deflection,
    selection_profile,
)
from svclab.synth import Dataset


class TestTheFourDefinitions:
    def test_each_rate_is_the_fraction_counted_by_hand(
        self, hand_outcomes: pd.DataFrame, hand_truth: pd.DataFrame
    ) -> None:
        row = containment_table({"hand": hand_outcomes}, hand_truth).set_index("policy").loc["hand"]
        assert int(row["contacts"]) == 8
        assert int(row["sessions"]) == 10
        assert float(row["repeats_per_contact"]) == pytest.approx(2 / 8)
        assert float(row["session_containment"]) == pytest.approx(6 / 8)
        assert float(row["resolution_containment"]) == pytest.approx(3 / 8)
        assert float(row["repeat_adjusted_containment"]) == pytest.approx(5 / 8)
        assert float(row["needed_containment"]) == pytest.approx(1 / 8)

    def test_the_definitions_are_ordered_the_way_the_document_claims(
        self, hand_outcomes: pd.DataFrame, hand_truth: pd.DataFrame
    ) -> None:
        """Each definition is a subset of the loosest one, so the ordering is structural."""
        row = containment_table({"hand": hand_outcomes}, hand_truth).iloc[0]
        assert row["needed_containment"] <= row["resolution_containment"]
        assert row["resolution_containment"] <= row["session_containment"]
        assert row["repeat_adjusted_containment"] <= row["session_containment"]

    def test_the_needed_rate_is_nan_without_the_counterfactual(
        self, hand_outcomes: pd.DataFrame
    ) -> None:
        """The state every real operation is in permanently, reported as such."""
        row = containment_table({"hand": hand_outcomes}).iloc[0]
        assert math.isnan(float(row["needed_containment"]))
        assert float(row["session_containment"]) == pytest.approx(6 / 8)

    def test_the_human_hours_count_every_session_including_the_repeats(
        self, hand_outcomes: pd.DataFrame
    ) -> None:
        row = containment_table({"hand": hand_outcomes}).iloc[0]
        assert float(row["human_hours"]) == pytest.approx(4 * 360.0 / 3600.0)

    def test_an_empty_frame_is_refused_rather_than_divided_by(self) -> None:
        empty = pd.DataFrame(
            {
                name: []
                for name in (
                    "contact",
                    "handled_by_human",
                    "resolved",
                    "is_repeat",
                    "returns",
                    "outcome",
                    "human_seconds",
                )
            }
        )
        with pytest.raises(ValueError, match="no rate to report"):
            containment_table({"empty": empty})

    def test_the_columns_are_the_declared_ones(self, hand_outcomes: pd.DataFrame) -> None:
        assert tuple(containment_table({"hand": hand_outcomes}).columns) == CONTAINMENT_COLUMNS


class TestDeflection:
    def test_the_noiseless_control_returns_exactly_one(
        self, noiseless_arms: tuple[pd.DataFrame, pd.DataFrame]
    ) -> None:
        treated, holdout = noiseless_arms
        measured = deflection(treated, holdout)
        assert measured.deflected_per_customer == pytest.approx(1.0, abs=1e-12)
        assert measured.treated_per_customer == pytest.approx(1.0, abs=1e-12)
        assert measured.holdout_per_customer == pytest.approx(2.0, abs=1e-12)
        assert measured.standard_error == 0.0
        assert math.isinf(measured.df)
        assert not measured.significant

    def test_without_a_control_arm_it_refuses_by_name(
        self, noiseless_arms: tuple[pd.DataFrame, pd.DataFrame]
    ) -> None:
        treated, _ = noiseless_arms
        measured = deflection(treated, None)
        assert measured.untested_because
        assert "no arm to compare against" in measured.untested_because
        assert math.isnan(measured.deflected_per_customer)
        assert math.isnan(measured.interval[0])
        assert not measured.significant
        assert math.isnan(measured.share_of(0.5))

    def test_one_customer_an_arm_is_refused_rather_than_answered(self) -> None:
        """A spread between customers needs more than one customer, and saying so beats a nan."""

        def arm(customer: int) -> pd.DataFrame:
            return pd.DataFrame(
                {
                    "session": [0],
                    "contact": [0],
                    "customer": [customer],
                    "handled_by_human": [True],
                    "is_repeat": [False],
                }
            )

        measured = deflection(arm(1), arm(2))
        assert "at least two customers" in measured.untested_because

    def test_an_empty_arm_is_refused(
        self, noiseless_arms: tuple[pd.DataFrame, pd.DataFrame]
    ) -> None:
        treated, holdout = noiseless_arms
        measured = deflection(treated.head(0), holdout)
        assert "no contacts in it" in measured.untested_because

    def test_a_ratio_against_a_zero_containment_rate_is_refused(
        self, noiseless_arms: tuple[pd.DataFrame, pd.DataFrame]
    ) -> None:
        """The refusal the whole repository is built around, in its smallest form."""
        treated, holdout = noiseless_arms
        assert math.isnan(deflection(treated, holdout).share_of(0.0))

    def test_on_the_real_account_it_falls_short_of_the_containment_rate(
        self, full: Dataset
    ) -> None:
        """The wave's claim as a direction: what the queue got is less than what was contained."""
        treated = full.contacts[~full.contacts["holdout"]]
        held = full.contacts[full.contacts["holdout"]]
        outcomes = run(treated, THREE_TURNS)
        measured = deflection(outcomes, run(held, HUMAN_ONLY))
        quoted = float(
            containment_table({"three-turns": outcomes})
            .set_index("policy")
            .loc["three-turns", "session_containment"]
        )
        assert measured.significant
        assert 0.0 < measured.share_of(quoted) < 1.0


class TestSelection:
    def test_the_bot_keeps_the_easy_end(self, full: Dataset) -> None:
        """The mechanism behind every figure in the module, asserted on the real account."""
        treated = full.contacts[~full.contacts["holdout"]]
        profile = selection_profile(run(treated, THREE_TURNS), full.contacts).set_index("group")
        assert tuple(selection_profile(run(treated, THREE_TURNS), full.contacts).columns) == (
            SELECTION_COLUMNS
        )
        bot = float(profile.loc["resolved-by-bot", "mean_difficulty"])
        human = float(profile.loc["reached-a-human", "mean_difficulty"])
        everything = float(profile.loc["all-contacts", "mean_difficulty"])
        assert bot < everything < human
        assert float(profile.loc["reached-a-human", "mean_human_seconds"]) > float(
            profile.loc["all-contacts", "mean_human_seconds"]
        )

    def test_nobody_who_came_back_would_have_managed_alone(self, full: Dataset) -> None:
        """A property of the session, checked through the measurement that reports it."""
        treated = full.contacts[~full.contacts["holdout"]]
        profile = selection_profile(run(treated, THREE_TURNS), full.contacts).set_index("group")
        assert float(profile.loc["came-back", "would_self_serve_rate"]) == 0.0

    def test_the_shares_add_up_over_the_groups_that_partition(self, full: Dataset) -> None:
        treated = full.contacts[~full.contacts["holdout"]].head(5_000)
        profile = selection_profile(run(treated, THREE_TURNS), full.contacts).set_index("group")
        partition = ["resolved-by-bot", "abandoned", "reached-a-human"]
        assert float(profile.loc[partition, "share"].sum()) == pytest.approx(1.0, abs=1e-12)

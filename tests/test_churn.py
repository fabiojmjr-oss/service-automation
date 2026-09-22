"""The departure mechanism, and the controls that keep a loss from being invented.

Two tests carry this wave. One runs the whole construction in a world nobody leaves and demands the
surviving contacts be the **identical frame** - a churn model that costs something when churn is
impossible is inventing losses. The other builds six contacts by hand where the arithmetic is
countable, because the rule that decides a departure is sequential and a vectorised sequential rule
is exactly the kind of thing that is off by one.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from svclab.bot import POLICIES, THREE_TURNS, run
from svclab.churn import (
    BAND_COLUMNS,
    DEPARTURE_COLUMNS,
    DETECTION_COLUMNS,
    EXPERIENCE_COLUMNS,
    EXPERIENCES,
    POLICY_COLUMNS,
    VALVE_COLUMNS,
    departures,
    detection_by_frequency,
    detection_table,
    experience_of,
    leave_chance,
    policy_table,
    silence_flag,
    surviving,
    valve_table,
)
from svclab.synth import CENTRE, CHURN, NOBODY_LEAVES, ChurnProfile, Dataset

#: A curve where leaving is certain after anything but a resolution, so a hand case is countable.
CERTAIN = ChurnProfile(
    leave_after_abandoned=1.0,
    leave_after_unresolved=1.0,
    leave_after_resolved=0.0,
    silence_days=10.0,
)


@pytest.fixture
def hand_contacts() -> pd.DataFrame:
    """Two customers, three contacts each, in a declared arrival order."""
    return pd.DataFrame(
        {
            "contact": [0, 1, 2, 3, 4, 5],
            "customer": [10, 10, 10, 20, 20, 20],
            "arrival_hour": [1.0, 100.0, 500.0, 2.0, 200.0, 600.0],
        }
    )


@pytest.fixture
def hand_outcomes() -> pd.DataFrame:
    """Customer 10 abandons its middle contact; customer 20 has everything resolved."""
    return pd.DataFrame(
        {
            "contact": [0, 1, 2, 3, 4, 5],
            "outcome": [
                "resolved-by-bot",
                "abandoned",
                "resolved-by-bot",
                "resolved-by-bot",
                "resolved-by-bot",
                "resolved-by-bot",
            ],
            "resolved": [True, False, True, True, True, True],
        }
    )


@pytest.fixture
def hand_draws() -> pd.DataFrame:
    """Every draw at zero, so any non-zero chance fires and the rule alone decides the answer."""
    return pd.DataFrame({"contact": [0, 1, 2, 3, 4, 5], "u_leave": [0.0] * 6})


class TestTheExperience:
    def test_the_worst_thing_that_happened_is_what_counts(self) -> None:
        """A contact abandoned and then resolved on its return is an abandoned contact."""
        contacts = pd.DataFrame({"contact": [0], "customer": [1], "arrival_hour": [1.0]})
        outcomes = pd.DataFrame(
            {
                "contact": [0, 0],
                "outcome": ["abandoned", "repeat-to-human"],
                "resolved": [False, True],
            }
        )
        table = experience_of(contacts, outcomes)
        assert list(table.columns) == list(EXPERIENCE_COLUMNS)
        assert table["experience"].iloc[0] == "abandoned"

    def test_the_three_experiences_are_the_declared_ones(
        self, hand_contacts: pd.DataFrame, hand_outcomes: pd.DataFrame
    ) -> None:
        table = experience_of(hand_contacts, hand_outcomes)
        assert set(table["experience"]) <= set(EXPERIENCES)
        assert list(table["experience"]) == ["resolved", "abandoned"] + ["resolved"] * 4

    def test_an_unresolved_contact_that_was_not_abandoned_is_its_own_case(self) -> None:
        contacts = pd.DataFrame({"contact": [0], "customer": [1], "arrival_hour": [1.0]})
        outcomes = pd.DataFrame({"contact": [0], "outcome": ["escalated"], "resolved": [False]})
        assert experience_of(contacts, outcomes)["experience"].iloc[0] == "unresolved"

    def test_a_missing_column_is_an_error_rather_than_a_guess(
        self, hand_contacts: pd.DataFrame, hand_outcomes: pd.DataFrame
    ) -> None:
        for column in ("contact", "customer", "arrival_hour"):
            with pytest.raises(KeyError, match="contact table is missing"):
                experience_of(hand_contacts.drop(columns=[column]), hand_outcomes)
        for column in ("outcome", "resolved"):
            with pytest.raises(KeyError, match="outcome table is missing"):
                experience_of(hand_contacts, hand_outcomes.drop(columns=[column]))


class TestTheCurve:
    def test_each_experience_gets_its_declared_chance(self) -> None:
        chances = leave_chance(np.array(EXPERIENCES), CHURN)
        assert list(chances) == [
            CHURN.leave_after_abandoned,
            CHURN.leave_after_unresolved,
            CHURN.leave_after_resolved,
        ]

    def test_abandoning_is_the_worst_of_the_three(self) -> None:
        assert CHURN.leave_after_abandoned > CHURN.leave_after_unresolved
        assert CHURN.leave_after_unresolved > CHURN.leave_after_resolved

    def test_a_resolved_contact_still_carries_a_risk(self) -> None:
        """A baseline of zero attributes every departure to the contact centre."""
        assert CHURN.leave_after_resolved > 0.0

    def test_an_experience_with_no_declared_chance_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no declared leaving chance"):
            leave_chance(np.array(["delighted"]), CHURN)


class TestTheDeparture:
    def test_the_departure_is_attributed_to_the_contact_that_caused_it(
        self,
        hand_contacts: pd.DataFrame,
        hand_outcomes: pd.DataFrame,
        hand_draws: pd.DataFrame,
    ) -> None:
        """Countable: customer 10 leaves after its second contact and loses only the third."""
        table = departures(hand_contacts, hand_outcomes, hand_draws, CERTAIN)
        assert list(table.columns) == list(DEPARTURE_COLUMNS)
        by_customer = table.set_index("customer")
        assert bool(by_customer.loc[10, "left"])
        assert float(by_customer.loc[10, "left_after_hour"]) == 100.0
        assert float(by_customer.loc[10, "contacts_seen"]) == 2.0
        assert float(by_customer.loc[10, "contacts_lost"]) == 1.0
        assert not bool(by_customer.loc[20, "left"])
        assert np.isnan(float(by_customer.loc[20, "left_after_hour"]))
        assert float(by_customer.loc[20, "contacts_lost"]) == 0.0

    def test_a_departure_after_the_last_contact_loses_nothing(
        self, hand_contacts: pd.DataFrame, hand_draws: pd.DataFrame
    ) -> None:
        outcomes = pd.DataFrame(
            {
                "contact": [0, 1, 2, 3, 4, 5],
                "outcome": ["resolved-by-bot"] * 5 + ["abandoned"],
                "resolved": [True] * 5 + [False],
            }
        )
        table = departures(hand_contacts, outcomes, hand_draws, CERTAIN).set_index("customer")
        assert bool(table.loc[20, "left"])
        assert float(table.loc[20, "contacts_lost"]) == 0.0

    def test_draws_that_do_not_cover_every_contact_are_refused(
        self, hand_contacts: pd.DataFrame, hand_outcomes: pd.DataFrame
    ) -> None:
        with pytest.raises(KeyError, match="do not cover every contact"):
            departures(
                hand_contacts,
                hand_outcomes,
                pd.DataFrame({"contact": [0, 1], "u_leave": [0.5, 0.5]}),
                CHURN,
            )

    def test_nobody_leaves_in_the_control_world(self, full: Dataset) -> None:
        """The load-bearing control: a curve that costs nothing has to cost nothing."""
        treated = full.contacts[~full.contacts["holdout"]]
        outcomes = run(treated, THREE_TURNS)
        table = departures(treated, outcomes, full.churn_draws, NOBODY_LEAVES)
        assert not table["left"].any()
        assert float(table["contacts_lost"].sum()) == 0.0
        assert surviving(treated, table).equals(treated)

    def test_every_customer_seen_has_a_row(self, full: Dataset) -> None:
        treated = full.contacts[~full.contacts["holdout"]]
        table = departures(treated, run(treated, THREE_TURNS), full.churn_draws)
        assert set(table["customer"]) == set(treated["customer"])
        assert (table["contacts_seen"] >= 1.0).all()


class TestSurviving:
    def test_a_customer_the_departures_do_not_describe_is_refused(
        self, hand_contacts: pd.DataFrame, hand_outcomes: pd.DataFrame, hand_draws: pd.DataFrame
    ) -> None:
        table = departures(hand_contacts, hand_outcomes, hand_draws, CERTAIN)
        with pytest.raises(KeyError, match="says nothing about"):
            surviving(hand_contacts.assign(customer=[10, 10, 10, 20, 20, 99]), table)

    def test_only_the_contacts_after_the_departure_are_removed(
        self, hand_contacts: pd.DataFrame, hand_outcomes: pd.DataFrame, hand_draws: pd.DataFrame
    ) -> None:
        table = departures(hand_contacts, hand_outcomes, hand_draws, CERTAIN)
        kept = surviving(hand_contacts, table)
        assert list(kept["contact"]) == [0, 1, 3, 4, 5]


class TestTheSilenceRule:
    def test_a_customer_last_seen_inside_the_window_is_not_flagged(self) -> None:
        period = CENTRE.days * 24.0
        contacts = pd.DataFrame(
            {
                "customer": [1, 2],
                "arrival_hour": [period - 1.0, period - CHURN.silence_days * 24.0 - 1.0],
            }
        )
        table = silence_flag(contacts).set_index("customer")
        assert not bool(table.loc[1, "flagged"])
        assert bool(table.loc[2, "flagged"])

    def test_a_window_outside_the_period_is_refused(self) -> None:
        contacts = pd.DataFrame({"customer": [1], "arrival_hour": [1.0]})
        for days in (0.0, -1.0, float(CENTRE.days), 100.0):
            profile = ChurnProfile(0.06, 0.04, 0.005, days)
            with pytest.raises(ValueError, match="cannot separate anybody"):
                silence_flag(contacts, CENTRE, profile)


class TestTheGaugeStudy:
    def test_the_rule_is_measured_against_the_truth(self) -> None:
        """A hand case whose confusion matrix is countable on one hand."""
        departed = pd.DataFrame(
            {
                "customer": [1, 2, 3, 4],
                "left": [True, True, False, False],
                "left_after_hour": [1.0, 2.0, np.nan, np.nan],
                "contacts_seen": [1.0, 1.0, 1.0, 1.0],
                "contacts_lost": [0.0, 0.0, 0.0, 0.0],
            }
        )
        flagged = pd.DataFrame({"customer": [1, 2, 3, 4], "flagged": [True, False, True, False]})
        table = detection_table(departed, flagged)
        assert list(table.columns) == list(DETECTION_COLUMNS)
        row = table.iloc[0]
        assert float(row["sensitivity"]) == pytest.approx(0.5)
        assert float(row["specificity"]) == pytest.approx(0.5)
        assert float(row["youden"]) == pytest.approx(0.0)
        assert float(row["precision"]) == pytest.approx(0.5)
        assert float(row["prevalence"]) == pytest.approx(0.5)

    def test_a_customer_with_no_surviving_contact_counts_as_silent(self) -> None:
        """They are not in the silence frame at all, and silence is exactly what they are."""
        departed = pd.DataFrame(
            {
                "customer": [1, 2],
                "left": [True, False],
                "left_after_hour": [1.0, np.nan],
                "contacts_seen": [1.0, 1.0],
                "contacts_lost": [0.0, 0.0],
            }
        )
        flagged = pd.DataFrame({"customer": [2], "flagged": [False]})
        assert float(detection_table(departed, flagged)["sensitivity"].iloc[0]) == 1.0

    def test_a_rule_that_flags_nobody_has_no_precision_to_report(self) -> None:
        departed = pd.DataFrame(
            {
                "customer": [1, 2],
                "left": [True, False],
                "left_after_hour": [1.0, np.nan],
                "contacts_seen": [1.0, 1.0],
                "contacts_lost": [0.0, 0.0],
            }
        )
        flagged = pd.DataFrame({"customer": [1, 2], "flagged": [False, False]})
        assert np.isnan(float(detection_table(departed, flagged)["precision"].iloc[0]))

    def test_a_study_with_one_kind_of_customer_is_refused(self) -> None:
        flagged = pd.DataFrame({"customer": [1, 2], "flagged": [True, False]})
        for truth in ([True, True], [False, False]):
            departed = pd.DataFrame(
                {
                    "customer": [1, 2],
                    "left": truth,
                    "left_after_hour": [1.0, 1.0],
                    "contacts_seen": [1.0, 1.0],
                    "contacts_lost": [0.0, 0.0],
                }
            )
            with pytest.raises(ValueError, match="both kinds of customer"):
                detection_table(departed, flagged)


class TestTheGaugeByFrequency:
    def test_every_band_and_a_total_row(self, full: Dataset) -> None:
        treated = full.contacts[~full.contacts["holdout"]]
        outcomes = run(treated, THREE_TURNS)
        departed = departures(treated, outcomes, full.churn_draws)
        flagged = silence_flag(surviving(treated, departed))
        table = detection_by_frequency(departed, flagged)
        assert list(table.columns) == list(BAND_COLUMNS)
        assert list(table["contacts_seen"]) == ["1", "2", "3", "4+", "all"]
        assert float(table["customers"].iloc[-1]) == float(table["customers"].iloc[:-1].sum())

    def test_a_band_with_nobody_in_it_reports_no_rate(self) -> None:
        departed = pd.DataFrame(
            {
                "customer": [1, 2],
                "left": [True, False],
                "left_after_hour": [1.0, np.nan],
                "contacts_seen": [1.0, 1.0],
                "contacts_lost": [0.0, 0.0],
            }
        )
        flagged = pd.DataFrame({"customer": [1, 2], "flagged": [True, False]})
        table = detection_by_frequency(departed, flagged, (1, 2)).set_index("contacts_seen")
        assert np.isnan(float(table.loc["2", "sensitivity"]))
        assert np.isnan(float(table.loc["3+", "specificity"]))
        assert np.isnan(float(table.loc["3+", "precision"]))

    def test_bands_that_are_not_increasing_counts_are_refused(self) -> None:
        departed = pd.DataFrame(
            {
                "customer": [1],
                "left": [True],
                "left_after_hour": [1.0],
                "contacts_seen": [1.0],
                "contacts_lost": [0.0],
            }
        )
        flagged = pd.DataFrame({"customer": [1], "flagged": [True]})
        for bands in ((), (2, 1), (1, 1), (0, 1)):
            with pytest.raises(ValueError, match="increasing distinct contact counts"):
                detection_by_frequency(departed, flagged, bands)


class TestThePolicyTable:
    def test_the_containment_before_churn_is_the_one_wave_one_published(
        self, full: Dataset
    ) -> None:
        """Computed through the module that defines containment, not a second reading of `route`."""
        treated = full.contacts[~full.contacts["holdout"]]
        outcomes = {policy.name: run(treated, policy) for policy in POLICIES}
        table = policy_table(treated, outcomes, full.churn_draws).set_index("policy")
        assert list(table.columns) == list(POLICY_COLUMNS[1:])
        assert float(table.loc["human-only", "session_containment"]) == pytest.approx(0.0)
        assert float(table.loc["patient", "session_containment"]) == pytest.approx(0.8169, abs=5e-5)
        assert float(table.loc["three-turns", "session_containment"]) == pytest.approx(
            0.6065, abs=5e-5
        )

    def test_losing_customers_only_ever_reduces_the_hours(self, full: Dataset) -> None:
        treated = full.contacts[~full.contacts["holdout"]]
        outcomes = {policy.name: run(treated, policy) for policy in POLICIES}
        table = policy_table(treated, outcomes, full.churn_draws)
        assert (table["hours_saved"] > 0.0).all()
        assert (table["human_hours_after"] < table["human_hours"]).all()

    def test_a_world_nobody_leaves_saves_nothing_and_reports_no_rate(self, full: Dataset) -> None:
        treated = full.contacts[~full.contacts["holdout"]]
        table = policy_table(
            treated, {"three-turns": run(treated, THREE_TURNS)}, full.churn_draws, NOBODY_LEAVES
        )
        assert float(table["hours_saved"].iloc[0]) == 0.0
        assert np.isnan(float(table["minutes_per_customer_lost"].iloc[0]))
        assert float(table["session_containment"].iloc[0]) == float(
            table["session_containment_after"].iloc[0]
        )

    def test_pricing_no_policies_is_refused(self, full: Dataset) -> None:
        treated = full.contacts[~full.contacts["holdout"]].head(100)
        with pytest.raises(ValueError, match="no policies to price"):
            policy_table(treated, {}, full.churn_draws)


class TestTheValve:
    def test_the_table_is_the_declared_arithmetic(self) -> None:
        table = valve_table((0.0, 0.5), 1_000, 500, CHURN)
        assert list(table.columns) == list(VALVE_COLUMNS)
        assert float(table["customers_lost"].iloc[0]) == 0.0
        assert float(table["abandoned"].iloc[1]) == 500.0
        assert float(table["customers_lost"].iloc[1]) == pytest.approx(
            500.0 * CHURN.leave_after_abandoned
        )
        assert float(table["share_of_customers"].iloc[1]) == pytest.approx(
            500.0 * CHURN.leave_after_abandoned / 500.0
        )

    def test_the_valve_is_monotone_in_the_abandonment(self) -> None:
        table = valve_table((0.05, 0.10, 0.30), 10_000, 5_000)
        assert (table["customers_lost"].diff().dropna() > 0.0).all()

    def test_a_valve_with_nothing_in_it_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no abandonment rates"):
            valve_table((), 100, 50)
        for rate in (-0.1, 1.1):
            with pytest.raises(ValueError, match="outside the unit interval"):
                valve_table((rate,), 100, 50)
        for contacts, customers in ((0, 50), (100, 0)):
            with pytest.raises(ValueError, match="no valve to price"):
                valve_table((0.1,), contacts, customers)

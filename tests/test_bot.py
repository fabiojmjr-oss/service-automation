"""The bot runtime, against four contacts whose outcomes are worked out on paper.

Two properties carry this file. The session is a pure function of the contact table and the policy,
so running it twice has to give the identical frame - without that, no comparison between two
policies means anything. And every branch of the session has to be reachable and correct on the hand
built case, because the aggregate figures the repository publishes are sums over those branches.
"""

from __future__ import annotations

import pandas as pd
import pytest

from svclab.bot import (
    GUARDED,
    HUMAN_ONLY,
    OUTCOME_COLUMNS,
    OUTCOMES,
    PATIENT,
    POLICIES,
    THREE_TURNS,
    BotPolicy,
    run,
)
from svclab.synth import CENTRE, Dataset


class TestThePolicy:
    def test_a_negative_turn_budget_is_refused(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            BotPolicy(name="broken", turn_budget=-1)

    def test_a_zero_budget_never_attempts(self) -> None:
        assert not HUMAN_ONLY.attempts("rastreio")

    def test_the_refusal_list_applies_to_the_predicted_intent(self) -> None:
        """The subtlety the whole rule turns on: the bot refuses what it *thinks* it is looking at."""
        assert not GUARDED.attempts("reclamacao")
        assert GUARDED.attempts("rastreio")

    def test_the_four_policies_are_distinct_and_named(self) -> None:
        assert len({policy.name for policy in POLICIES}) == len(POLICIES)


class TestTheSessionOnPaper:
    def test_every_outcome_is_the_one_worked_out_by_hand(self, hand_contacts: pd.DataFrame) -> None:
        outcomes = run(hand_contacts, THREE_TURNS)
        first = outcomes[~outcomes["is_repeat"]].set_index("contact")
        assert list(first["outcome"]) == ["resolved-by-bot", "abandoned", "escalated", "escalated"]
        assert list(first["bot_turns"]) == [1, 1, 3, 3]
        assert list(first["handled_by_human"]) == [False, False, True, True]
        assert list(first["resolved"]) == [True, False, True, False]

    def test_the_contact_that_comes_back_is_a_second_row(self, hand_contacts: pd.DataFrame) -> None:
        """Contact 3 is unresolved by both the bot and the human, and the customer returns."""
        outcomes = run(hand_contacts, THREE_TURNS)
        assert len(outcomes) == 5
        repeat = outcomes[outcomes["is_repeat"]]
        assert len(repeat) == 1
        assert int(repeat["contact"].iloc[0]) == 3
        assert repeat["outcome"].iloc[0] == "repeat-to-human"
        assert bool(repeat["handled_by_human"].iloc[0])
        assert not bool(repeat["resolved"].iloc[0])
        assert repeat["session"].iloc[0] not in set(outcomes["contact"])

    def test_the_repeat_costs_the_same_handling_plus_the_handoff(
        self, hand_contacts: pd.DataFrame
    ) -> None:
        outcomes = run(hand_contacts, THREE_TURNS)
        repeat = outcomes[outcomes["is_repeat"]].iloc[0]
        assert float(repeat["human_seconds"]) == pytest.approx(500.0 + CENTRE.handoff_seconds)

    def test_an_escalation_costs_the_handoff_and_a_direct_route_does_not(
        self, hand_contacts: pd.DataFrame
    ) -> None:
        escalated = run(hand_contacts, THREE_TURNS).set_index("contact").loc[2]
        assert float(escalated["human_seconds"]) == pytest.approx(400.0 + CENTRE.handoff_seconds)
        direct = run(hand_contacts, HUMAN_ONLY).set_index("contact").loc[2]
        assert float(direct["human_seconds"]) == pytest.approx(400.0)

    def test_patience_ending_first_is_an_abandonment_and_the_budget_an_escalation(
        self, hand_contacts: pd.DataFrame
    ) -> None:
        """Contact 1 needs four turns, has one turn of patience and a budget of three."""
        outcomes = run(hand_contacts, THREE_TURNS).set_index("contact")
        assert outcomes.loc[1, "outcome"] == "abandoned"
        assert int(outcomes.loc[1, "bot_turns"]) == 1
        # Widen the patience past the budget and the same contact escalates instead.
        patient_customer = hand_contacts.copy()
        patient_customer.loc[1, "patience_turns"] = 9.0
        assert run(patient_customer, THREE_TURNS).set_index("contact").loc[1, "outcome"] == (
            "escalated"
        )

    def test_a_longer_budget_resolves_the_contact_that_needed_more_turns(
        self, hand_contacts: pd.DataFrame
    ) -> None:
        patient_customer = hand_contacts.copy()
        patient_customer.loc[1, "patience_turns"] = 9.0
        outcomes = run(patient_customer, PATIENT).set_index("contact")
        assert outcomes.loc[1, "outcome"] == "resolved-by-bot"
        assert int(outcomes.loc[1, "bot_turns"]) == 4

    def test_a_refused_intent_reaches_a_human_without_spending_a_turn(
        self, hand_contacts: pd.DataFrame
    ) -> None:
        outcomes = run(hand_contacts, GUARDED).set_index("contact")
        assert outcomes.loc[2, "route"] == "refused"
        assert int(outcomes.loc[2, "bot_turns"]) == 0
        assert outcomes.loc[0, "route"] == "bot"

    def test_the_holdout_arm_never_meets_the_bot(self, hand_contacts: pd.DataFrame) -> None:
        held = hand_contacts.copy()
        held["holdout"] = True
        outcomes = run(held, PATIENT)
        first = outcomes[~outcomes["is_repeat"]]
        assert (first["route"] == "holdout").all()
        assert (outcomes["bot_turns"] == 0).all()
        assert (first["outcome"] == "straight-to-human").all()
        # The repeat stream does not disappear in the control arm: a human who does not resolve the
        # contact produces a return too, which is what makes the arm a fair comparison rather than a
        # perfect one.
        assert int(outcomes["is_repeat"].sum()) == 1


class TestThePropertiesEveryComparisonNeeds:
    def test_running_twice_gives_the_identical_frame(self, full: Dataset) -> None:
        """No draw happens in the session, so a second run cannot differ from the first."""
        sample = full.contacts.head(4_000)
        assert run(sample, THREE_TURNS).equals(run(sample, THREE_TURNS))

    def test_two_policies_meet_the_same_contacts(self, full: Dataset) -> None:
        sample = full.contacts.head(4_000)
        first, second = run(sample, THREE_TURNS), run(sample, PATIENT)
        assert set(first[~first["is_repeat"]]["contact"]) == set(
            second[~second["is_repeat"]]["contact"]
        )

    def test_a_missing_column_is_an_error_rather_than_a_guess(self, full: Dataset) -> None:
        for column in ("difficulty", "patience_turns", "human_resolves"):
            broken = full.contacts.head(100).drop(columns=[column])
            with pytest.raises(KeyError, match="missing"):
                run(broken, THREE_TURNS)

    def test_the_columns_and_outcomes_are_the_declared_ones(self, full: Dataset) -> None:
        outcomes = run(full.contacts.head(4_000), THREE_TURNS)
        assert tuple(outcomes.columns) == OUTCOME_COLUMNS
        assert set(outcomes["outcome"]) <= set(OUTCOMES)

    def test_no_repeat_stream_returns_the_first_sessions_alone(
        self, hand_contacts: pd.DataFrame
    ) -> None:
        """The branch where nobody comes back, which a full dataset never exercises."""
        nobody = hand_contacts.copy()
        nobody["repeats_if_unresolved"] = False
        outcomes = run(nobody, THREE_TURNS)
        assert len(outcomes) == len(nobody)
        assert not outcomes["is_repeat"].any()

    def test_a_contact_that_would_self_serve_does_not_come_back(
        self, hand_contacts: pd.DataFrame
    ) -> None:
        """Somebody who would have managed alone is not a repeat waiting to happen."""
        self_serving = hand_contacts.copy()
        self_serving["would_self_serve"] = True
        assert not run(self_serving, THREE_TURNS)["is_repeat"].any()

    def test_more_containment_never_means_more_resolution_on_this_account(
        self, full: Dataset
    ) -> None:
        """The wave's claim as a direction rather than a figure: the two rankings are opposed.

        Asserting the ordering rather than the numbers is deliberate - the numbers are published and
        belong in the claims suite, while the ordering is the finding.
        """
        sample = full.contacts[~full.contacts["holdout"]]
        measured = []
        for policy in (THREE_TURNS, PATIENT, GUARDED):
            outcomes = run(sample, policy)
            first = outcomes[~outcomes["is_repeat"]]
            measured.append(
                (
                    float((~first["handled_by_human"]).mean()),
                    float(first["resolved"].mean()),
                )
            )
        by_containment = sorted(measured, key=lambda pair: pair[0])
        assert [pair[1] for pair in by_containment] == sorted(
            (pair[1] for pair in by_containment), reverse=True
        )

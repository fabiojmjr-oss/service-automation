"""The chain of return visits, and the identity that keeps five waves of figures where they are.

The first test in this file is the one everything else depends on: running with the default chain has
to produce the identical frame the earlier waves published - the same objects, not close numbers.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
import pytest

from svclab.bot import POLICIES, THREE_TURNS, run
from svclab.chain import (
    ATTEMPT_COLUMNS,
    CHAIN_COLUMNS,
    TAIL_COLUMNS,
    TIME_COLUMNS,
    attempt_table,
    attempts_of,
    chain_table,
    reopen_rate,
    sessions_per_unresolved,
    tail_table,
    time_table,
)
from svclab.synth import CENTRE, CHAIN, SINGLE_RETURN, ChainProfile, Dataset, return_draws


def fingerprint(frame: pd.DataFrame) -> str:
    """A hash of a frame's contents, for asserting identity rather than similarity."""
    return hashlib.sha256(
        pd.util.hash_pandas_object(frame, index=True).to_numpy().tobytes()
    ).hexdigest()


class TestTheDefaultChangesNothing:
    def test_the_default_chain_is_the_world_the_earlier_waves_published(
        self, full: Dataset
    ) -> None:
        treated = full.contacts[~full.contacts["holdout"]]
        assert fingerprint(run(treated, THREE_TURNS)) == fingerprint(
            run(treated, THREE_TURNS, chain=SINGLE_RETURN)
        )

    def test_passing_the_draws_to_a_single_return_changes_nothing_either(
        self, full: Dataset
    ) -> None:
        """A chain of two attempts spends no draw, so handing it some cannot matter."""
        treated = full.contacts[~full.contacts["holdout"]].head(4000)
        assert fingerprint(run(treated, THREE_TURNS)) == fingerprint(
            run(treated, THREE_TURNS, chain=SINGLE_RETURN, draws=full.return_draws)
        )

    def test_a_chain_of_one_attempt_produces_no_repeat_at_all(self, full: Dataset) -> None:
        once = ChainProfile(max_attempts=1, return_decay=1.0, human_retry_lift=1.0)
        outcomes = run(full.contacts.head(2000), THREE_TURNS, chain=once)
        assert not outcomes["is_repeat"].any()


class TestTheDrawsTheChainNeeds:
    def test_the_draws_cover_every_further_attempt(self, full: Dataset) -> None:
        draws = full.return_draws
        assert sorted(draws["attempt"].unique()) == list(range(2, CHAIN.max_attempts + 1))
        assert len(draws) == CENTRE.contacts * (CHAIN.max_attempts - 1)
        for column in ("u_return", "u_human"):
            assert draws[column].between(0.0, 1.0).all()

    def test_a_chain_with_no_further_attempt_needs_no_draws(self) -> None:
        once = ChainProfile(max_attempts=1, return_decay=1.0, human_retry_lift=1.0)
        assert return_draws(np.random.default_rng(0), CENTRE, once).empty

    def test_a_chain_of_no_attempts_is_refused(self) -> None:
        with pytest.raises(ValueError, match="at least one attempt"):
            return_draws(
                np.random.default_rng(0),
                CENTRE,
                ChainProfile(max_attempts=0, return_decay=1.0, human_retry_lift=1.0),
            )

    def test_a_long_chain_without_draws_is_refused(self, full: Dataset) -> None:
        with pytest.raises(ValueError, match="needs the return draws"):
            run(full.contacts.head(100), THREE_TURNS, chain=CHAIN)

    def test_draws_that_do_not_cover_the_open_contacts_are_refused(self, full: Dataset) -> None:
        """A missing coin is refused rather than guessed at, which is this repository's whole habit."""
        short = full.return_draws[full.return_draws["attempt"] == 2]
        with pytest.raises(ValueError, match="do not cover attempt"):
            run(
                full.contacts[~full.contacts["holdout"]].head(4000),
                THREE_TURNS,
                chain=CHAIN,
                draws=short,
            )


class TestTheChainItself:
    def test_a_chain_never_shortens_and_never_unresolves(self, full: Dataset) -> None:
        treated = full.contacts[~full.contacts["holdout"]]
        before = run(treated, THREE_TURNS)
        after = run(treated, THREE_TURNS, chain=CHAIN, draws=full.return_draws)
        assert len(after) >= len(before)
        first_before = before[~before["is_repeat"]].set_index("contact")["resolved"]
        first_after = after[~after["is_repeat"]].set_index("contact")["resolved"]
        assert (first_before == first_after).all()
        assert (
            after.groupby("contact")["resolved"].max().mean()
            >= before.groupby("contact")["resolved"].max().mean()
        )

    def test_every_session_id_is_unique_and_says_which_attempt_it_was(self, full: Dataset) -> None:
        outcomes = run(
            full.contacts[~full.contacts["holdout"]],
            THREE_TURNS,
            chain=CHAIN,
            draws=full.return_draws,
        )
        assert outcomes["session"].is_unique
        attempts = attempts_of(outcomes)
        assert attempts.min() == 1
        assert attempts.max() <= CHAIN.max_attempts
        assert (attempts.loc[~outcomes["is_repeat"]] == 1).all()
        assert (attempts.loc[outcomes["is_repeat"]] > 1).all()

    def test_a_compounding_lift_closes_every_chain_in_the_end(self) -> None:
        """One contact, worked out on paper, and it exposes a property of the declared lift.

        ``reclamacao``'s human curve at difficulty 0.5 is ``0.95 - 0.3 * 0.5 = 0.80``. The lift
        compounds: 0.92 on the third attempt and 1.0576 on the fourth, which **clips to one**. So a
        human draw of 0.99 fails the first three attempts and cannot fail the fourth - the chain ends
        because the probability saturated, not because the customer gave up.

        That is worth knowing before reading any figure here: this model's chains terminate by
        construction, and an operation whose escalation path does not improve has no such guarantee.
        A return draw of 0.1 stays under the decayed return curve throughout, so nothing else ended
        it.
        """
        contact = pd.DataFrame(
            [
                {
                    "contact": 0,
                    "customer": 1,
                    "intent": "reclamacao",
                    "holdout": True,
                    "difficulty": 0.5,
                    "bot_can_resolve": False,
                    "would_self_serve": False,
                    "human_seconds": 300.0,
                    "classifier_draw": 0.01,
                    "patience_turns": 5.0,
                    "repeats_if_unresolved": True,
                    "human_resolves": False,
                }
            ]
        )
        draws = pd.DataFrame(
            [
                {"contact": 0, "attempt": attempt, "u_return": 0.1, "u_human": 0.99}
                for attempt in (2, 3, 4)
            ]
        )
        outcomes = run(contact, POLICIES[0], chain=CHAIN, draws=draws)
        assert len(outcomes) == CHAIN.max_attempts
        assert list(attempts_of(outcomes)) == [1, 2, 3, 4]
        assert not outcomes["resolved"].iloc[:3].any()
        assert outcomes["resolved"].iloc[3]
        assert not outcomes["returns"].iloc[-1]

    def test_a_lifted_human_closes_a_chain_the_first_attempt_could_not(self) -> None:
        """The same contact, with a human draw the lifted curve clears on the third attempt."""
        contact = pd.DataFrame(
            [
                {
                    "contact": 0,
                    "customer": 1,
                    "intent": "rastreio",
                    "holdout": True,
                    "difficulty": 0.0,
                    "bot_can_resolve": False,
                    "would_self_serve": False,
                    "human_seconds": 300.0,
                    "classifier_draw": 0.01,
                    "patience_turns": 5.0,
                    "repeats_if_unresolved": True,
                    "human_resolves": False,
                }
            ]
        )
        draws = pd.DataFrame(
            [
                {"contact": 0, "attempt": attempt, "u_return": 0.1, "u_human": 0.9}
                for attempt in (2, 3, 4)
            ]
        )
        outcomes = run(contact, POLICIES[0], chain=CHAIN, draws=draws)
        # rastreio's human curve at difficulty zero is 0.995, so 0.9 is under it on the third attempt
        # and the chain ends there with three sessions rather than four.
        assert len(outcomes) == 3
        assert outcomes["resolved"].iloc[-1]


class TestTheClosedForm:
    def test_one_attempt_is_one_session_whatever_the_rate(self) -> None:
        for rate in (0.0, 0.5, 1.0):
            assert sessions_per_unresolved(rate, 1) == pytest.approx(1.0)

    def test_a_rate_of_zero_is_one_session_whatever_the_chain(self) -> None:
        for attempts in (1, 2, 10):
            assert sessions_per_unresolved(0.0, attempts) == pytest.approx(1.0)

    def test_a_rate_of_one_uses_every_attempt(self) -> None:
        assert sessions_per_unresolved(1.0, 7) == pytest.approx(7.0)

    def test_the_series_converges_to_the_unbounded_sum(self) -> None:
        assert sessions_per_unresolved(0.5, 40) == pytest.approx(2.0, abs=1e-9)

    def test_the_rate_is_the_product_of_two_things_happening(self) -> None:
        assert reopen_rate(0.8, 0.75) == pytest.approx(0.2)
        assert reopen_rate(0.8, 1.0) == pytest.approx(0.0)

    def test_an_impossible_rate_or_chain_is_refused(self) -> None:
        with pytest.raises(ValueError, match="probability"):
            reopen_rate(1.2, 0.5)
        with pytest.raises(ValueError, match="probability"):
            reopen_rate(0.5, -0.1)
        with pytest.raises(ValueError, match="probability"):
            sessions_per_unresolved(1.5, 3)
        with pytest.raises(ValueError, match="at least one attempt"):
            sessions_per_unresolved(0.3, 0)

    def test_truncating_the_tail_costs_more_as_the_rate_rises(self) -> None:
        table = tail_table((0.05, 0.2, 0.5, 0.7))
        assert list(table.columns) == list(TAIL_COLUMNS)
        errors = table["truncation_error"].tolist()
        assert errors == sorted(errors)
        assert (table["four_attempts"] <= table["unbounded"]).all()
        assert (table["two_attempts"] <= table["four_attempts"]).all()

    def test_a_rate_of_one_has_no_bound_to_report(self) -> None:
        row = tail_table((1.0,)).iloc[0]
        assert np.isinf(float(row["unbounded"]))

    def test_a_table_of_no_rates_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no reopen rates"):
            tail_table(())


class TestTheTables:
    def test_the_attempts_account_for_every_session(self, full: Dataset) -> None:
        treated = full.contacts[~full.contacts["holdout"]]
        outcomes = run(treated, THREE_TURNS, chain=CHAIN, draws=full.return_draws)
        table = attempt_table(outcomes, len(treated))
        assert list(table.columns) == list(ATTEMPT_COLUMNS)
        assert int(table["sessions"].sum()) == len(outcomes)
        assert table["cumulative_resolution"].is_monotonic_increasing
        assert float(table["cumulative_resolution"].iloc[-1]) <= 1.0
        assert float(table["human_hours"].sum()) == pytest.approx(
            outcomes["human_seconds"].sum() / 3600.0, abs=1e-6
        )

    def test_an_empty_frame_has_no_attempts_to_report(self, full: Dataset) -> None:
        with pytest.raises(ValueError, match="no sessions"):
            attempt_table(run(full.contacts.head(10), THREE_TURNS).head(0))

    def test_the_chain_costs_every_policy_something(self, full: Dataset) -> None:
        treated = full.contacts[~full.contacts["holdout"]]
        single = {policy.name: run(treated, policy) for policy in POLICIES}
        chained = {
            policy.name: run(treated, policy, chain=CHAIN, draws=full.return_draws)
            for policy in POLICIES
        }
        table = chain_table(single, chained).set_index("policy")
        assert list(table.reset_index().columns) == list(CHAIN_COLUMNS)
        assert (table["extra_sessions"] > 0).all()
        assert (table["extra_hours_share"] > 0.0).all()
        assert (table["eventual_resolution"] > table["first_attempt_resolution"]).all()

    def test_the_two_mappings_have_to_describe_the_same_policies(self, full: Dataset) -> None:
        arm = run(full.contacts.head(50), THREE_TURNS)
        with pytest.raises(KeyError, match="chained"):
            chain_table({"a": arm}, {"b": arm})

    def test_the_time_to_resolution_ranks_the_policies_by_containment(self, full: Dataset) -> None:
        """The wave's claim, as an ordering rather than a number: containment buys delay."""
        treated = full.contacts[~full.contacts["holdout"]]
        chained = {
            policy.name: run(treated, policy, chain=CHAIN, draws=full.return_draws)
            for policy in POLICIES
        }
        table = time_table(chained).sort_values("containment")
        assert list(table.columns) == list(TIME_COLUMNS)
        assert table["days_to_resolution"].is_monotonic_increasing
        assert table["share_beyond_first"].is_monotonic_increasing

    def test_a_policy_that_resolved_nothing_has_no_time_to_report(self, full: Dataset) -> None:
        outcomes = run(full.contacts.head(200), THREE_TURNS)
        with pytest.raises(ValueError, match="resolved nothing"):
            time_table({"nothing": outcomes[outcomes["resolved"] == False]})  # noqa: E712

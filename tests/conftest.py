"""Shared fixtures. The dataset is built once per session because it is deterministic."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from svclab.synth import Dataset, correlated_dataset, generate_dataset


@pytest.fixture(scope="session")
def full() -> Dataset:
    """The published dataset, from the default seed."""
    return generate_dataset()


@pytest.fixture(scope="session")
def correlated(full: Dataset) -> Dataset:
    """The same account in the world where a customer is a person, from the same noise."""
    return correlated_dataset(full)


@pytest.fixture
def hand_contacts() -> pd.DataFrame:
    """Four contacts whose every outcome can be worked out on paper.

    With a three-turn budget, and reading the declared curves for ``rastreio`` and ``reclamacao``:

    - contact 0: easy, resolvable, classified right, patient. Needs one turn, gets three: resolved.
    - contact 1: resolvable but needs four turns at difficulty 0.8, and the customer's patience is
      one turn. The budget would have escalated it at three; patience ends it first: abandoned.
    - contact 2: not resolvable, so the bot spends its budget and escalates. The human resolves it.
    - contact 3: not resolvable, the human does not resolve it either, and the customer comes back.
      That is two rows: the escalation and the repeat.

    Every draw here is set rather than sampled, which is the point: the arithmetic of the session has
    to be checkable without a generator in the way.
    """
    rows = [
        {
            "contact": 0,
            "customer": 100,
            "intent": "rastreio",
            "arrival_hour": 1.0,
            "holdout": False,
            "difficulty": 0.0,
            "bot_can_resolve": True,
            "would_self_serve": False,
            "human_seconds": 200.0,
            "classifier_draw": 0.01,
            "patience_turns": 5.0,
            "repeats_if_unresolved": True,
            "human_resolves": True,
        },
        {
            "contact": 1,
            "customer": 101,
            "intent": "rastreio",
            "arrival_hour": 2.0,
            "holdout": False,
            "difficulty": 0.8,
            "bot_can_resolve": True,
            "would_self_serve": False,
            "human_seconds": 300.0,
            "classifier_draw": 0.01,
            "patience_turns": 1.0,
            "repeats_if_unresolved": False,
            "human_resolves": True,
        },
        {
            "contact": 2,
            "customer": 102,
            "intent": "reclamacao",
            "arrival_hour": 3.0,
            "holdout": False,
            "difficulty": 0.5,
            "bot_can_resolve": False,
            "would_self_serve": False,
            "human_seconds": 400.0,
            "classifier_draw": 0.01,
            "patience_turns": 9.0,
            "repeats_if_unresolved": True,
            "human_resolves": True,
        },
        {
            "contact": 3,
            "customer": 103,
            "intent": "reclamacao",
            "arrival_hour": 4.0,
            "holdout": False,
            "difficulty": 0.5,
            "bot_can_resolve": False,
            "would_self_serve": False,
            "human_seconds": 500.0,
            "classifier_draw": 0.01,
            "patience_turns": 9.0,
            "repeats_if_unresolved": True,
            "human_resolves": False,
        },
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def noiseless_arms() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Two arms whose deflection is exactly one human contact per customer, with no spread.

    Ten holdout customers with two human sessions each, ten treated customers with one each. The
    difference is exactly 1.0, the spread inside each arm is exactly zero, and an estimator that
    cannot return that on this input is not evidence about anything.
    """

    def arm(customers: range, per_customer: int) -> pd.DataFrame:
        rows = []
        session = 0
        for customer in customers:
            for _ in range(per_customer):
                rows.append(
                    {
                        "session": session,
                        "contact": session,
                        "customer": customer,
                        "handled_by_human": True,
                        "resolved": True,
                        "is_repeat": False,
                        "returns": False,
                        "outcome": "straight-to-human",
                        "human_seconds": 300.0,
                    }
                )
                session += 1
        return pd.DataFrame(rows)

    return arm(range(10), 1), arm(range(100, 110), 2)


@pytest.fixture
def hand_outcomes() -> pd.DataFrame:
    """Ten sessions whose four containment rates are exact fractions.

    Eight first sessions and two repeats. Of the eight: three resolved by the bot, two abandoned and
    never came back, one abandoned and came back, two reached a human. So session containment is
    6/8, resolution containment 3/8, repeat-adjusted 5/8, and - with two of the bot's three
    resolutions being contacts that would have self-served - needed containment is 1/8.
    """

    def row(session: int, contact: int, outcome: str, human: bool, returns: bool, repeat: bool):
        return {
            "session": session,
            "contact": contact,
            "customer": contact,
            "outcome": outcome,
            "handled_by_human": human,
            "resolved": outcome != "abandoned",
            "is_repeat": repeat,
            "returns": returns,
            "human_seconds": 360.0 if human else 0.0,
        }

    rows = [
        row(0, 0, "resolved-by-bot", False, False, False),
        row(1, 1, "resolved-by-bot", False, False, False),
        row(2, 2, "resolved-by-bot", False, False, False),
        row(3, 3, "abandoned", False, False, False),
        row(4, 4, "abandoned", False, False, False),
        row(5, 5, "abandoned", False, True, False),
        row(6, 6, "escalated", True, False, False),
        row(7, 7, "escalated", True, True, False),
        row(8, 5, "repeat-to-human", True, False, True),
        row(9, 7, "repeat-to-human", True, False, True),
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def hand_truth() -> pd.DataFrame:
    """The counterfactual for :func:`hand_outcomes`: two of the bot's three resolutions were free."""
    return pd.DataFrame(
        {
            "contact": np.arange(8),
            "would_self_serve": [True, True, False, False, False, False, False, False],
        }
    )

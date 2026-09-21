"""The generator, and the rule that makes its figures reproducible anywhere.

The load-bearing test in this file is the last one: it reads the package's source and fails if any
module draws through a distribution method rather than through the uniform stream. A sibling
repository published figures that held on one machine and moved on a clean install, and the rule that
prevents it is only a rule while something checks it.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import numpy as np
import pytest

from svclab.synth import (
    CENTRE,
    GRADERS,
    INTENTS,
    QUALITY,
    TRUTH_DRAW_COLUMNS,
    Dataset,
    contacts,
    generate_dataset,
    intent_truth,
)

SOURCE = Path(__file__).resolve().parents[1] / "src" / "svclab"


class TestTheShapeOfTheData:
    def test_the_table_is_the_size_it_was_asked_for(self, full: Dataset) -> None:
        assert len(full.contacts) == CENTRE.contacts
        assert full.contacts["contact"].is_unique
        assert not full.contacts.isna().to_numpy().any()

    def test_the_intent_shares_declare_a_whole(self) -> None:
        assert sum(profile.share for profile in INTENTS) == pytest.approx(1.0, abs=1e-12)

    def test_the_intents_arrive_in_roughly_their_declared_shares(self, full: Dataset) -> None:
        """A share is a probability, so it is checked against its own sampling error, not exactly."""
        counts = full.contacts["intent"].value_counts(normalize=True)
        for profile in INTENTS:
            error = np.sqrt(profile.share * (1 - profile.share) / CENTRE.contacts)
            assert abs(counts[profile.intent] - profile.share) < 4.0 * error, profile.intent

    def test_the_difficulty_closes_to_its_declared_mean(self, full: Dataset) -> None:
        """Beta(a, b) has mean a / (a + b), which is a closed form rather than another simulation."""
        expected = CENTRE.difficulty_alpha / (CENTRE.difficulty_alpha + CENTRE.difficulty_beta)
        assert full.contacts["difficulty"].mean() == pytest.approx(expected, abs=0.005)
        assert full.contacts["difficulty"].between(0.0, 1.0).all()


class TestTheHoldout:
    def test_every_contact_of_a_customer_lands_in_the_same_arm(self, full: Dataset) -> None:
        """The whole reason the arms are drawn per customer: a repeat must not cross the line."""
        arms = full.contacts.groupby("customer")["holdout"].nunique()
        assert arms.max() == 1

    def test_the_holdout_is_roughly_the_declared_share_of_customers(self, full: Dataset) -> None:
        by_customer = full.contacts.groupby("customer")["holdout"].first()
        error = np.sqrt(CENTRE.holdout_share * (1 - CENTRE.holdout_share) / len(by_customer))
        assert abs(by_customer.mean() - CENTRE.holdout_share) < 4.0 * error


class TestTheTruthColumns:
    def test_a_bot_can_resolve_less_of_what_is_harder(self, full: Dataset) -> None:
        """The mechanism every figure in this repository rests on, asserted rather than assumed."""
        table = full.contacts
        easy = table[table["difficulty"] < 0.2]["bot_can_resolve"].mean()
        hard = table[table["difficulty"] > 0.6]["bot_can_resolve"].mean()
        assert easy > hard + 0.3

    def test_the_two_intents_built_to_resist_automation_do(self, full: Dataset) -> None:
        truth = full.intent_truth.set_index("intent")
        assert float(truth.loc["reclamacao", "bot_can_resolve_rate"]) < 0.02
        assert float(truth.loc["reembolso", "bot_can_resolve_rate"]) < 0.15
        assert float(truth.loc["rastreio", "bot_can_resolve_rate"]) > 0.55

    def test_the_share_where_automation_creates_anything_is_below_what_it_can_resolve(
        self, full: Dataset
    ) -> None:
        """Resolvable is not the same as needed, and the gap is the self-service counterfactual."""
        truth = full.intent_truth
        assert (truth["resolvable_and_needed"] <= truth["bot_can_resolve_rate"] + 1e-12).all()
        gap = truth["bot_can_resolve_rate"] - truth["resolvable_and_needed"]
        assert gap.max() > 0.10

    def test_handling_time_rises_with_difficulty(self, full: Dataset) -> None:
        table = full.contacts
        easy = table[table["difficulty"] < 0.2]["human_seconds"].mean()
        hard = table[table["difficulty"] > 0.6]["human_seconds"].mean()
        assert hard > easy * 1.3

    def test_a_human_does_not_resolve_everything(self, full: Dataset) -> None:
        """The assumption that would quietly award the control arm a perfect score."""
        assert 0.85 < full.contacts["human_resolves"].mean() < 0.98

    def test_the_intent_truth_table_matches_the_contacts_it_summarises(self, full: Dataset) -> None:
        derived = intent_truth(full.contacts)
        assert int(derived["contacts"].sum()) == len(full.contacts)
        for _, row in derived.iterrows():
            subset = full.contacts[full.contacts["intent"] == row["intent"]]
            assert row["contacts"] == len(subset)
            assert row["mean_difficulty"] == pytest.approx(subset["difficulty"].mean())


class TestTheQualitySample:
    def test_the_panel_samples_the_declared_number_of_sessions(self, full: Dataset) -> None:
        expected = QUALITY.sample * len(GRADERS) * QUALITY.replicates
        assert len(full.panel_noise) == expected
        assert full.panel_noise["contact"].nunique() == QUALITY.sample
        assert set(full.panel_noise["grader"]) == {profile.grader for profile in GRADERS}
        assert set(full.panel_noise["replicate"]) == set(range(1, QUALITY.replicates + 1))

    def test_the_judge_reads_every_contact(self, full: Dataset) -> None:
        assert len(full.judge_noise) == CENTRE.contacts
        assert full.judge_noise["contact"].is_unique

    def test_each_graders_noise_has_the_spread_it_declared(self, full: Dataset) -> None:
        """A declared standard deviation that the draws do not have is a parameter nobody can read."""
        measured = full.panel_noise.groupby("grader")["noise"].std()
        for profile in GRADERS:
            assert float(measured[profile.grader]) == pytest.approx(profile.noise_sd, rel=0.06)

    def test_a_contact_table_without_what_the_score_needs_is_refused(self, full: Dataset) -> None:
        from svclab.synth import routing_scores

        for column in ("difficulty", "classifier_draw", "intent"):
            with pytest.raises(KeyError, match="missing"):
                routing_scores(
                    np.random.default_rng(0), full.contacts.head(50).drop(columns=[column])
                )

    def test_a_sample_larger_than_the_centre_is_refused(self, full: Dataset) -> None:
        from dataclasses import replace

        from svclab.synth import quality_noise

        with pytest.raises(ValueError, match="cannot sample"):
            quality_noise(
                np.random.default_rng(0), CENTRE, replace(QUALITY, sample=CENTRE.contacts + 1)
            )


class TestReproducibility:
    def test_the_seed_reproduces_the_table_exactly(self) -> None:
        first, second = generate_dataset(), generate_dataset()
        assert first.contacts.equals(second.contacts)

    def test_a_different_seed_produces_a_different_table(self) -> None:
        assert not generate_dataset().contacts.equals(generate_dataset(seed=43).contacts)

    def test_the_first_values_and_the_sums_are_pinned(self, full: Dataset) -> None:
        """Both, because a first row can match by coincidence while everything after it has moved.

        That is not hypothetical: in a sibling repository a pin on the first row alone passed while
        every figure downstream of it had changed.
        """
        table = full.contacts
        assert float(table["difficulty"].iloc[0]) == pytest.approx(0.2139051104, abs=5e-10)
        assert float(table["difficulty"].sum()) == pytest.approx(13359.1696054, abs=5e-6)
        assert float(table["human_seconds"].sum()) == pytest.approx(15411178.7928, abs=5e-4)
        assert float(table["patience_turns"].sum()) == pytest.approx(180711.0, abs=5e-7)
        assert int(table["bot_can_resolve"].sum()) == 17219
        assert int(table["would_self_serve"].sum()) == 5035
        assert int(table["human_resolves"].sum()) == 37225

    def test_the_first_uniform_of_the_stream_is_what_numpy_promises(self) -> None:
        """The one value the whole dataset hangs from, asserted against numpy directly."""
        assert float(np.random.default_rng(42).random(1)[0]) == pytest.approx(
            0.7739560485559633, abs=5e-16
        )

    def test_a_fresh_generator_gives_the_same_contacts_as_the_dataset(self, full: Dataset) -> None:
        assert contacts(np.random.default_rng(42)).equals(full.contacts)


class TestTheDisciplinesThatHoldTheRepositoryUp:
    def test_nothing_in_the_package_draws_through_a_distribution_method(self) -> None:
        """Every draw must be an inverse transform of the uniform stream.

        A rejection sampler consumes a variable number of uniforms per draw, so the stream position
        after it depends on library internals. Checked against the source because the alternative is
        a convention, and a convention lasts until the next module.
        """
        allowed = {"random"}
        offenders = []
        for path in SOURCE.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(r"\brng\.(\w+)\s*\(", text):
                if match.group(1) not in allowed:
                    offenders.append(f"{path.name}: rng.{match.group(1)}(")
        assert not offenders, "draws that are not inverse transforms: " + "; ".join(offenders)

    def test_the_policy_module_cannot_reach_a_truth_column(self) -> None:
        """A policy that can see the answer is not a policy, it is a report.

        The session module is the world and may read anything; the policy module is the deployable
        part and may not. Checked through the parsed syntax rather than by grepping the text, because
        the first version of this test grepped and failed on the docstring explaining the rule - the
        prose is allowed to name a column, the code is not.
        """
        forbidden = {
            "difficulty",
            "would_self_serve",
            "human_seconds",
            "bot_can_resolve",
            # Wave 4 keeps the uniforms behind those columns in the table, and a uniform plus the
            # curve it was compared against is the answer by another route. The rule has to grow
            # with the table or it protects a shape the data no longer has.
            *TRUTH_DRAW_COLUMNS,
        }
        tree = ast.parse((SOURCE / "bot" / "policy.py").read_text(encoding="utf-8"))
        docstrings = {
            ast.get_docstring(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef)
        }
        reached = set()
        for node in ast.walk(tree):
            literal = isinstance(node, ast.Constant) and isinstance(node.value, str)
            if literal and node.value not in docstrings and node.value in forbidden:
                reached.add(node.value)
            if isinstance(node, ast.Attribute) and node.attr in forbidden:
                reached.add(node.attr)
            if isinstance(node, ast.Name) and node.id in forbidden:
                reached.add(node.id)
        assert not reached, f"the policy module reaches truth columns: {sorted(reached)}"

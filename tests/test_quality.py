"""The gauge, against closed forms and a hand-built panel.

The load-bearing control is the attenuation identity. A binary assessor turns a true pass rate ``p``
into ``p*se + (1-p)*(1-sp)``, so the difference between two groups comes out multiplied by
``se + sp - 1`` - exactly, not approximately. That is checked at both ends (a perfect gauge changes
nothing, a gauge carrying no information reports exactly zero) and in the middle, and it is checked
against algebra rather than against another implementation.

Cohen's kappa gets the same treatment: two raters constructed to be independent must return exactly
zero, and two who agree on everything exactly one.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from svclab.bot import HUMAN_ONLY, THREE_TURNS, run
from svclab.quality import (
    AGREEMENT_COLUMNS,
    LATENT_COLUMNS,
    REPRODUCIBILITY_COLUMNS,
    agreement_table,
    attenuation,
    judge_verdicts,
    kappa,
    latent_quality,
    observed_rate,
    panel_verdicts,
    reproducibility,
    sessions_for_difference,
    youden,
)
from svclab.synth import GRADERS, JUDGE, QUALITY, Dataset


class TestTheAttenuationIdentity:
    def test_a_perfect_gauge_reports_the_rate_it_is_given(self) -> None:
        for rate in (0.0, 0.25, 0.5, 0.9, 1.0):
            assert observed_rate(rate, 1.0, 1.0) == pytest.approx(rate, abs=1e-15)

    def test_the_two_corners_are_the_two_error_rates(self) -> None:
        """Everything acceptable means the sensitivity; nothing acceptable means the false alarms."""
        assert observed_rate(1.0, 0.82, 0.88) == pytest.approx(0.82, abs=1e-15)
        assert observed_rate(0.0, 0.82, 0.88) == pytest.approx(1.0 - 0.88, abs=1e-15)

    def test_the_observed_difference_is_the_true_one_times_the_youden_index(self) -> None:
        """The identity the whole module rests on, at four different gauges."""
        for sensitivity, specificity in ((1.0, 1.0), (0.9, 0.8), (0.82, 0.88), (0.6, 0.55)):
            for first, second in ((0.96, 0.41), (0.5, 0.5), (0.2, 0.8)):
                measured = attenuation(first, second, sensitivity, specificity)
                expected = (first - second) * youden(sensitivity, specificity)
                assert measured["observed_difference"] == pytest.approx(expected, abs=1e-14)
                assert measured["true_difference"] == pytest.approx(first - second, abs=1e-15)
                assert measured["factor"] == pytest.approx(
                    sensitivity + specificity - 1.0, abs=1e-15
                )

    def test_a_gauge_carrying_no_information_reports_exactly_no_difference(self) -> None:
        """Sensitivity plus specificity of one is a coin, and a coin reports zero however large the
        difference is. Exactly zero, which is the cleanest statement of what attenuation is."""
        for sensitivity in (0.2, 0.5, 0.8):
            measured = attenuation(0.96, 0.41, sensitivity, 1.0 - sensitivity)
            assert measured["factor"] == pytest.approx(0.0, abs=1e-15)
            assert measured["observed_difference"] == pytest.approx(0.0, abs=1e-15)

    def test_a_gauge_worse_than_a_coin_reverses_the_sign(self) -> None:
        """Below zero the gauge is not noisy, it is inverted, and the report says the opposite."""
        measured = attenuation(0.96, 0.41, 0.3, 0.4)
        assert measured["factor"] < 0.0
        assert measured["true_difference"] > 0.0
        assert measured["observed_difference"] < 0.0

    def test_attenuation_never_exaggerates(self) -> None:
        """The direction that matters for reading a report: the shrink is towards zero, always."""
        for sensitivity in (0.55, 0.7, 0.85, 1.0):
            for specificity in (0.55, 0.7, 0.85, 1.0):
                measured = attenuation(0.9, 0.3, sensitivity, specificity)
                assert (
                    abs(measured["observed_difference"]) <= abs(measured["true_difference"]) + 1e-15
                )

    def test_a_rate_outside_its_unit_interval_is_refused(self) -> None:
        for arguments in ((1.2, 0.9, 0.9), (0.5, 1.4, 0.9), (0.5, 0.9, -0.1)):
            with pytest.raises(ValueError, match="between zero and one"):
                observed_rate(*arguments)


class TestKappa:
    def test_two_raters_constructed_to_be_independent_return_exactly_zero(self) -> None:
        """Both pass half of everything and agree on half, which is chance exactly."""
        first = np.array([True, True, False, False])
        second = np.array([True, False, True, False])
        assert kappa(first, second) == pytest.approx(0.0, abs=1e-15)

    def test_perfect_agreement_returns_one(self) -> None:
        verdicts = np.array([True, False, True, True, False])
        assert kappa(verdicts, verdicts) == pytest.approx(1.0, abs=1e-15)

    def test_perfect_disagreement_returns_minus_one_when_the_margins_are_even(self) -> None:
        first = np.array([True, True, False, False])
        assert kappa(first, ~first) == pytest.approx(-1.0, abs=1e-15)

    def test_two_constant_raters_return_nan_rather_than_a_number(self) -> None:
        """Chance agreement is already perfect, so there is no agreement above chance to report."""
        constant = np.ones(10, dtype=bool)
        assert math.isnan(kappa(constant, constant))

    def test_raw_agreement_can_be_high_while_kappa_is_negative(self) -> None:
        """The reason both are reported, worked out on paper.

        Two raters pass 95 of 100 and agree on 90, so raw agreement is exactly 0.90 - which reads as
        a good gauge. Chance agreement at those margins is 0.95 times 0.95 plus 0.05 times 0.05,
        which is 0.905, so kappa is (0.90 - 0.905) / 0.095 and comes out **below zero**. The two
        raters agree slightly less than two coins weighted the same way would.
        """
        first = np.array([True] * 95 + [False] * 5)
        second = np.array([True] * 90 + [False] * 5 + [True] * 5)
        assert float(np.mean(first == second)) == pytest.approx(0.90, abs=1e-15)
        assert kappa(first, second) == pytest.approx(-0.005 / 0.095, abs=1e-12)
        assert kappa(first, second) < 0.0

    def test_mismatched_or_empty_input_is_refused(self) -> None:
        with pytest.raises(ValueError, match="cannot be compared"):
            kappa(np.ones(3, dtype=bool), np.ones(4, dtype=bool))
        with pytest.raises(ValueError, match="no verdicts to compare"):
            kappa(np.array([], dtype=bool), np.array([], dtype=bool))


class TestLatentQuality:
    def test_the_declared_levels_come_back_at_difficulty_zero(self, hand_contacts) -> None:
        easy = hand_contacts.copy()
        easy["difficulty"] = 0.0
        outcomes = run(easy, THREE_TURNS)
        latent = latent_quality(outcomes, easy).set_index("session")
        levels = {
            "resolved-by-bot": QUALITY.resolved_by_bot,
            "escalated": QUALITY.escalated,
            "abandoned": QUALITY.abandoned,
            "repeat-to-human": QUALITY.repeat_to_human,
        }
        for _, row in latent.iterrows():
            assert float(row["latent_quality"]) == pytest.approx(levels[row["outcome"]])

    def test_abandonment_is_flat_and_never_acceptable(self, hand_contacts) -> None:
        """There is no version of walking the customer out that meets the standard."""
        for difficulty in (0.0, 0.5, 1.0):
            table = hand_contacts.copy()
            table["difficulty"] = difficulty
            latent = latent_quality(run(table, THREE_TURNS), table)
            abandoned = latent[latent["outcome"] == "abandoned"]
            if len(abandoned):
                assert (abandoned["latent_quality"] == QUALITY.abandoned).all()
                assert not abandoned["acceptable"].any()

    def test_difficulty_costs_quality_on_every_other_outcome(self, full: Dataset) -> None:
        treated = full.contacts[~full.contacts["holdout"]].head(6_000)
        latent = latent_quality(run(treated, THREE_TURNS), full.contacts)
        joined = latent.merge(full.contacts[["contact", "difficulty"]], on="contact")
        working = joined[joined["outcome"] != "abandoned"]
        easy = working[working["difficulty"] < 0.2]["latent_quality"].mean()
        hard = working[working["difficulty"] > 0.6]["latent_quality"].mean()
        assert easy > hard

    def test_an_outcome_with_no_declared_level_is_an_error(self, full: Dataset) -> None:
        outcomes = run(full.contacts.head(200), THREE_TURNS).copy()
        outcomes.loc[outcomes.index[0], "outcome"] = "transferred-to-the-moon"
        with pytest.raises(KeyError, match="no declared quality level"):
            latent_quality(outcomes, full.contacts)

    def test_the_columns_are_the_declared_ones(self, full: Dataset) -> None:
        latent = latent_quality(run(full.contacts.head(500), THREE_TURNS), full.contacts)
        assert tuple(latent.columns) == LATENT_COLUMNS


class TestTheAgreementAnalysis:
    def test_the_hand_built_panel_gives_the_fractions_counted_by_hand(self) -> None:
        """Four sessions, one assessor, two readings, every verdict set rather than drawn.

        The assessor agrees with itself on three of four, and with the truth on five of eight
        readings. Of the two truly acceptable sessions it passes three readings of four, and of the
        two unacceptable it fails two of four.
        """
        latent = pd.DataFrame(
            {
                "session": [0, 1, 2, 3],
                "contact": [0, 1, 2, 3],
                "outcome": ["escalated"] * 4,
                "latent_quality": [0.9, 0.8, 0.2, 0.1],
                "acceptable": [True, True, False, False],
            }
        )
        verdicts = pd.DataFrame(
            {
                "session": [0, 0, 1, 1, 2, 2, 3, 3],
                "contact": [0, 0, 1, 1, 2, 2, 3, 3],
                "assessor": ["a"] * 8,
                "replicate": [1, 2] * 4,
                "reading": [0.0] * 8,
                "verdict": [True, True, True, False, True, True, False, False],
            }
        )
        row = agreement_table(verdicts, latent).iloc[0]
        assert int(row["readings"]) == 8
        assert float(row["pass_rate"]) == pytest.approx(5 / 8)
        assert float(row["repeatability"]) == pytest.approx(3 / 4)
        assert float(row["agreement_with_truth"]) == pytest.approx(5 / 8)
        assert float(row["sensitivity"]) == pytest.approx(3 / 4)
        assert float(row["specificity"]) == pytest.approx(2 / 4)
        assert float(row["youden"]) == pytest.approx(3 / 4 + 2 / 4 - 1)
        assert tuple(agreement_table(verdicts, latent).columns) == AGREEMENT_COLUMNS

    def test_one_reading_reports_no_repeatability_rather_than_perfect_repeatability(
        self, full: Dataset
    ) -> None:
        """A deterministic assessor read once has nothing to say about agreeing with itself."""
        treated = full.contacts[~full.contacts["holdout"]].head(4_000)
        latent = latent_quality(run(treated, THREE_TURNS), full.contacts)
        row = agreement_table(judge_verdicts(latent, full.judge_noise), latent).iloc[0]
        assert math.isnan(float(row["repeatability"]))
        assert math.isnan(float(row["repeatability_kappa"]))
        assert not math.isnan(float(row["agreement_with_truth"]))

    def test_an_empty_frame_is_refused(self, full: Dataset) -> None:
        latent = latent_quality(run(full.contacts.head(100), THREE_TURNS), full.contacts)
        with pytest.raises(ValueError, match="no readings to analyse"):
            agreement_table(latent.head(0).assign(assessor="a", replicate=1, verdict=True), latent)

    def test_reproducibility_needs_two_assessors(self, full: Dataset) -> None:
        treated = full.contacts[~full.contacts["holdout"]].head(4_000)
        latent = latent_quality(run(treated, THREE_TURNS), full.contacts)
        with pytest.raises(ValueError, match="needs two assessors"):
            reproducibility(judge_verdicts(latent, full.judge_noise))

    def test_reproducibility_compares_one_replicate_so_the_two_problems_stay_apart(
        self, full: Dataset
    ) -> None:
        """Comparing one assessor's first reading with another's second measures both at once."""
        latent = latent_quality(run(full.contacts, THREE_TURNS), full.contacts)
        verdicts = panel_verdicts(latent, full.panel_noise)
        first = reproducibility(verdicts, replicate=1)
        second = reproducibility(verdicts, replicate=2)
        assert tuple(first.columns) == REPRODUCIBILITY_COLUMNS
        assert len(first) == 3
        assert not first.equals(second)
        assert (first["sessions"] == first["sessions"].iloc[0]).all()


class TestTheSampleSizeConsequence:
    def test_a_worse_gauge_always_costs_more_sessions(self) -> None:
        perfect = sessions_for_difference(0.96, 0.41)
        for sensitivity, specificity in ((0.95, 0.95), (0.85, 0.85), (0.7, 0.7)):
            assert sessions_for_difference(0.96, 0.41, sensitivity, specificity) > perfect
        assert sessions_for_difference(0.96, 0.41, 0.7, 0.7) > sessions_for_difference(
            0.96, 0.41, 0.85, 0.85
        )

    def test_a_gauge_with_no_information_is_refused_rather_than_priced(self) -> None:
        """No sample size detects a difference a coin reports as zero, and saying so beats a number."""
        with pytest.raises(ValueError, match="no number of sessions distinguishes them"):
            sessions_for_difference(0.96, 0.41, 0.5, 0.5)

    def test_power_and_alpha_are_checked(self) -> None:
        with pytest.raises(ValueError, match="power has to be"):
            sessions_for_difference(0.9, 0.4, power=1.0)
        with pytest.raises(ValueError, match="alpha has to be"):
            sessions_for_difference(0.9, 0.4, alpha=0.0)

    def test_more_power_costs_more_sessions(self) -> None:
        assert sessions_for_difference(0.9, 0.4, power=0.9) > sessions_for_difference(
            0.9, 0.4, power=0.8
        )


class TestOnTheRealAccount:
    def test_the_graders_disagree_with_themselves_and_with_each_other(self, full: Dataset) -> None:
        """Both halves of the gauge study, as directions rather than figures."""
        latent = latent_quality(run(full.contacts, THREE_TURNS), full.contacts)
        verdicts = panel_verdicts(latent, full.panel_noise)
        table = agreement_table(verdicts, latent)
        assert len(table) == len(GRADERS)
        assert (table["repeatability"] < 0.90).all()
        assert (table["repeatability_kappa"] < 0.70).all()
        between = reproducibility(verdicts)
        assert (between["kappa"] < 0.70).all()
        assert (between["agreement"] > between["kappa"]).all()
        # The pass rate moves with the grader, which is the reproducibility problem in one column.
        assert float(table["pass_rate"].max()) - float(table["pass_rate"].min()) > 0.10

    def test_the_panel_understates_the_gap_between_the_arms(self, full: Dataset) -> None:
        """The wave's conclusion, as a direction. The figures belong in the claims suite."""
        treated = full.contacts[~full.contacts["holdout"]]
        held = full.contacts[full.contacts["holdout"]]
        bot = latent_quality(run(treated, THREE_TURNS), full.contacts)
        control = latent_quality(run(held, HUMAN_ONLY), full.contacts)
        everything = pd.concat([bot, control], ignore_index=True)
        assert everything["session"].is_unique, "two arms must not share a session id"

        table = agreement_table(panel_verdicts(everything, full.panel_noise), everything)
        sensitivity = float(table["sensitivity"].mean())
        specificity = float(table["specificity"].mean())
        measured = attenuation(
            float(control["acceptable"].mean()),
            float(bot["acceptable"].mean()),
            sensitivity,
            specificity,
        )
        assert 0.0 < measured["factor"] < 1.0
        assert measured["observed_difference"] < measured["true_difference"]

    def test_the_judge_reads_more_sessions_than_the_panel(self, full: Dataset) -> None:
        latent = latent_quality(run(full.contacts, THREE_TURNS), full.contacts)
        judged = judge_verdicts(latent, full.judge_noise)
        panel = panel_verdicts(latent, full.panel_noise)
        assert judged["session"].nunique() > 10 * panel["session"].nunique()
        assert judged["assessor"].unique().tolist() == [JUDGE.grader]

    def test_the_judge_beats_each_grader_against_the_truth(self, full: Dataset) -> None:
        """Which is not the same thing as agreeing with them, and that gap is the wave's last result."""
        latent = latent_quality(run(full.contacts, THREE_TURNS), full.contacts)
        panel = agreement_table(panel_verdicts(latent, full.panel_noise), latent)
        judge = agreement_table(judge_verdicts(latent, full.judge_noise), latent).iloc[0]
        assert float(judge["agreement_with_truth"]) > float(panel["agreement_with_truth"].max())
        assert float(judge["youden"]) > float(panel["youden"].max())

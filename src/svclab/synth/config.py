"""Every parameter of the simulated contact centre, written down.

Nothing in this file is a measurement of any real operation. The shares, the handling times, the
patience and the two counterfactual columns no real contact centre has were chosen to make a
particular measurement situation visible - see ``DISCLAIMER.md``.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Seed behind every published figure in this repository.
SEED = 42


@dataclass(frozen=True)
class IntentProfile:
    """One reason a customer makes contact, described by what a bot can do with it.

    Attributes:
        intent: Invented label for the reason.
        share: Share of contacts arriving with this intent.
        bot_ceiling: Probability a bot resolves a contact of this intent at difficulty zero.
        bot_difficulty_slope: How fast that probability falls with difficulty. Subtracted, so a
            ceiling of 0.95 and a slope of 0.90 reaches zero at a difficulty of 1.06.
        self_serve_ceiling: Probability the customer would have resolved this **without any help at
            all** at difficulty zero - by finding the answer, giving up harmlessly, or the parcel
            simply arriving. This is the column no real operation has, and the reason containment
            can be checked against something.
        self_serve_difficulty_slope: How fast that falls with difficulty.
        human_seconds_base: Mean handling seconds for a human at difficulty zero.
        human_seconds_slope: Added mean handling seconds per unit of difficulty. This is what makes
            the residue a bot leaves behind more expensive than the volume it removed.
        repeat_when_unresolved: Probability the customer comes back within the repeat window if the
            contact ends unresolved.
        classifier_ceiling: Probability an intent classifier labels this intent correctly at
            difficulty zero.
        classifier_difficulty_slope: How fast that falls with difficulty.
        confused_with: The intent this one is mislabelled as when the classifier is wrong.
        human_ceiling: Probability a human resolves this intent at difficulty zero. Present because
            a model in which humans resolve everything sets the bar at a human being perfect, which
            flatters every comparison against automation. These are high and they are not one.
        human_difficulty_slope: How fast that falls with difficulty.
    """

    intent: str
    share: float
    bot_ceiling: float
    bot_difficulty_slope: float
    self_serve_ceiling: float
    self_serve_difficulty_slope: float
    human_seconds_base: float
    human_seconds_slope: float
    repeat_when_unresolved: float
    classifier_ceiling: float
    classifier_difficulty_slope: float
    confused_with: str
    human_ceiling: float
    human_difficulty_slope: float


#: Five reasons for contact. Two of them are the point of the whole repository: `rastreio` is
#: mostly answerable and mostly self-serving, so a bot that handles it gets credit for contacts
#: that needed nobody; `reclamacao` is neither, so it is the residue every automation leaves.
INTENTS = (
    IntentProfile(
        intent="rastreio",
        share=0.34,
        bot_ceiling=0.95,
        bot_difficulty_slope=0.90,
        self_serve_ceiling=0.46,
        self_serve_difficulty_slope=0.70,
        human_seconds_base=150.0,
        human_seconds_slope=330.0,
        repeat_when_unresolved=0.55,
        classifier_ceiling=0.97,
        classifier_difficulty_slope=0.30,
        confused_with="prazo-de-entrega",
        human_ceiling=0.995,
        human_difficulty_slope=0.1,
    ),
    IntentProfile(
        intent="prazo-de-entrega",
        share=0.24,
        bot_ceiling=0.82,
        bot_difficulty_slope=0.95,
        self_serve_ceiling=0.34,
        self_serve_difficulty_slope=0.60,
        human_seconds_base=190.0,
        human_seconds_slope=420.0,
        repeat_when_unresolved=0.62,
        classifier_ceiling=0.93,
        classifier_difficulty_slope=0.40,
        confused_with="rastreio",
        human_ceiling=0.99,
        human_difficulty_slope=0.14,
    ),
    IntentProfile(
        intent="cadastro",
        share=0.14,
        bot_ceiling=0.88,
        bot_difficulty_slope=1.10,
        self_serve_ceiling=0.22,
        self_serve_difficulty_slope=0.45,
        human_seconds_base=210.0,
        human_seconds_slope=380.0,
        repeat_when_unresolved=0.48,
        classifier_ceiling=0.90,
        classifier_difficulty_slope=0.45,
        confused_with="rastreio",
        human_ceiling=0.985,
        human_difficulty_slope=0.16,
    ),
    IntentProfile(
        intent="reembolso",
        share=0.16,
        bot_ceiling=0.40,
        bot_difficulty_slope=1.05,
        self_serve_ceiling=0.06,
        self_serve_difficulty_slope=0.20,
        human_seconds_base=330.0,
        human_seconds_slope=640.0,
        repeat_when_unresolved=0.74,
        classifier_ceiling=0.86,
        classifier_difficulty_slope=0.50,
        confused_with="reclamacao",
        human_ceiling=0.97,
        human_difficulty_slope=0.22,
    ),
    IntentProfile(
        intent="reclamacao",
        share=0.12,
        bot_ceiling=0.14,
        bot_difficulty_slope=1.00,
        self_serve_ceiling=0.03,
        self_serve_difficulty_slope=0.10,
        human_seconds_base=420.0,
        human_seconds_slope=900.0,
        repeat_when_unresolved=0.80,
        classifier_ceiling=0.81,
        classifier_difficulty_slope=0.55,
        confused_with="reembolso",
        human_ceiling=0.95,
        human_difficulty_slope=0.3,
    ),
)


@dataclass(frozen=True)
class CentreProfile:
    """The contact centre itself.

    Attributes:
        contacts: Contacts arriving over the period.
        customers: Distinct customers behind them, so a repeat belongs to somebody.
        days: Days the period covers, for arrival times and for the repeat window.
        difficulty_alpha: First shape of the Beta the difficulty is drawn from.
        difficulty_beta: Second shape. Both together decide how much of the volume is easy, which
            is the single most consequential parameter in this file.
        holdout_share: Share of **customers** routed straight to a human, as the control arm.
            Randomised by customer rather than by contact on purpose: the same customer comes back,
            and splitting their contacts across arms would let the bot's effect leak into the
            control. The cost of that choice is a wider interval, and it is the honest one.
        repeat_window_hours: How long after an unresolved contact a return counts as a repeat.
        bot_seconds_per_turn: Seconds a bot turn costs the customer.
        patience_turns_mean: Mean number of bot turns a customer tolerates before abandoning.
        handoff_seconds: Seconds a human spends re-reading a conversation a bot escalated, on top
            of handling the contact. The part of an automation's cost that is never in its
            business case.
        operating_hours_per_day: Hours the human queue is staffed, which is what turns a month of
            contacts into an offered load.
        target_answer_seconds: The service level's target - the wait a contact is supposed to be
            answered inside.
        target_service_level: The share of contacts that has to be answered inside it.
    """

    contacts: int
    customers: int
    days: int
    difficulty_alpha: float
    difficulty_beta: float
    holdout_share: float
    repeat_window_hours: float
    bot_seconds_per_turn: float
    patience_turns_mean: float
    handoff_seconds: float
    operating_hours_per_day: float
    target_answer_seconds: float
    target_service_level: float


CENTRE = CentreProfile(
    contacts=40_000,
    customers=26_000,
    days=30,
    difficulty_alpha=2.0,
    difficulty_beta=4.0,
    holdout_share=0.20,
    repeat_window_hours=72.0,
    bot_seconds_per_turn=45.0,
    patience_turns_mean=4.0,
    handoff_seconds=55.0,
    operating_hours_per_day=12.0,
    target_answer_seconds=20.0,
    target_service_level=0.80,
)

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


@dataclass(frozen=True)
class GraderProfile:
    """One quality assessor, described by the two ways they are wrong.

    Attributes:
        grader: Invented label for the assessor.
        bias: How much this assessor's reading of a session sits above the truth. Positive is a
            lenient grader, negative a strict one. This is the **reproducibility** problem: two
            graders who disagree on average disagree on every batch.
        noise_sd: Spread of this assessor's reading around their own average. This is the
            **repeatability** problem: the same grader, the same session, a different verdict.
    """

    grader: str
    bias: float
    noise_sd: float


#: A three-person quality panel. Their spread is not a pathological construction - a lenient
#: grader, a strict one, and one who is closest to the standard and noisiest around it is what a
#: calibration study finds when somebody finally runs one.
GRADERS = (
    GraderProfile(grader="avaliador-1", bias=0.06, noise_sd=0.11),
    GraderProfile(grader="avaliador-2", bias=-0.07, noise_sd=0.09),
    GraderProfile(grader="avaliador-3", bias=0.01, noise_sd=0.15),
)

#: The automated assessor: cheaper, grades everything, and wrong in its own way rather than in the
#: panel's way. Deliberately given a **smaller** spread and a **larger** bias than the panel's
#: average, because that combination is what makes Result 5 possible.
JUDGE = GraderProfile(grader="juiz-automatico", bias=0.09, noise_sd=0.06)


@dataclass(frozen=True)
class QualityProfile:
    """The declared quality of a session, and the standard it is judged against.

    Attributes:
        standard: The latent score at or above which a session is genuinely acceptable. A declared
            threshold rather than an inferred one, which is what makes accuracy computable here and
            not computable anywhere else.
        sample: Sessions the human panel grades. Real quality assurance reads a sample, and the
            sample size is the lever everybody pulls before checking whether the instrument works.
        replicates: How many times each grader reads each sampled session. Two, because
            repeatability cannot be estimated from one reading and almost no operation collects the
            second.
        resolved_by_bot: Latent quality of a contact the bot resolved, at difficulty zero.
        straight_to_human: Latent quality of a contact that went to a human directly.
        escalated: Latent quality of a contact the bot escalated - lower than going direct, because
            the customer explained themselves twice.
        repeat_to_human: Latent quality of a second attempt at the same unresolved issue.
        abandoned: Latent quality of a session the customer walked out of. Flat: there is no version
            of this that is acceptable.
        difficulty_penalty: How much latent quality falls across the difficulty range, for every
            outcome except abandonment.
    """

    standard: float
    sample: int
    replicates: int
    resolved_by_bot: float
    straight_to_human: float
    escalated: float
    repeat_to_human: float
    abandoned: float
    difficulty_penalty: float


QUALITY = QualityProfile(
    standard=0.50,
    sample=1_200,
    replicates=2,
    resolved_by_bot=0.72,
    straight_to_human=0.80,
    escalated=0.62,
    repeat_to_human=0.45,
    abandoned=0.15,
    difficulty_penalty=0.30,
)


@dataclass(frozen=True)
class RoutingProfile:
    """The confidence a routing classifier attaches to its own label, and what a mistake costs.

    Attributes:
        score_noise_sd: Spread added to the classifier's margin before it becomes a score. Zero
            would make the score a perfect ranker of its own correctness, which no classifier is.
        misroute_seconds: Extra human seconds a contact costs when the bot was handed it on a wrong
            label, by intent. A complaint read as a tracking question is not the same mistake as the
            reverse, and a single accuracy figure cannot express that.
        defer_seconds: Extra human seconds a deferred contact costs - the classifier declined to
            let the bot try, so a human takes it fresh. Small, and not zero: somebody still reads
            the queue entry.
    """

    score_noise_sd: float
    misroute_seconds: dict[str, float]
    defer_seconds: float


#: The cost asymmetry is the whole point of the module that reads this. Misrouting a complaint costs
#: nine minutes of a human's day plus a customer who has now explained a problem to a machine that
#: answered about parcel tracking; misrouting a tracking question costs a minute.
ROUTING = RoutingProfile(
    score_noise_sd=0.12,
    misroute_seconds={
        "rastreio": 60.0,
        "prazo-de-entrega": 90.0,
        "cadastro": 150.0,
        "reembolso": 420.0,
        "reclamacao": 540.0,
    },
    defer_seconds=20.0,
)


@dataclass(frozen=True)
class PopulationProfile:
    """How much of a contact is the person and how much is the occasion.

    Waves 1 to 3 draw every trait per contact, which makes a customer a label on a row rather than
    somebody with a history. This profile is the correction, and it is stated as the quantity that
    matters rather than as a coefficient: **the share of a trait's latent variance that belongs to
    the customer.**

    The mechanism is a Gaussian copula. A trait's percentile is pushed through the normal quantile,
    the resulting latent value is split into a customer's part and an occasion's part with loadings
    ``sqrt(rho)`` and ``sqrt(1 - rho)``, and the sum is pushed back out through the trait's own
    quantile function. Two properties make it the right choice here and both are asserted in the
    tests:

    - the latent correlation between two contacts of one customer is **exactly** ``rho``;
    - the trait's marginal distribution is **unchanged** - the same family, the same mean, the same
      variance, the same support.

    The second property is what makes the two worlds comparable. A convex combination of two draws
    would have been simpler and it narrows the marginal spread by ``rho + (1 - rho)``'s cousin,
    which would leave every difference between the worlds attributable to two causes at once. This
    construction changes the correlation and nothing else.

    Attributes:
        difficulty_correlation: Share of a contact's latent difficulty that belongs to the customer.
            0.25 sits inside the range wave 3 had to declare because it could not measure one.
        patience_correlation: The same for patience, and deliberately different: one number for "how
            correlated are contacts" is the simplification this wave exists to remove.
    """

    difficulty_correlation: float
    patience_correlation: float


#: Two declared correlations, and they are not equal on purpose. A design effect computed from one
#: trait, applied to a comparison that turns on another, is one of the errors `svclab.population`
#: exists to make visible.
POPULATION = PopulationProfile(difficulty_correlation=0.25, patience_correlation=0.10)

"""Choosing the threshold on contacts it will not be judged on, and on a label it can see.

Wave 3 swept a threshold per intent, priced it on the same contacts it was swept on, and keyed it on
the intent the contact **actually was**. Each of those three is a decision, and the roadmap recorded
all three as open - predicting that each one made the published saving an upper bound. That
prediction is wrong, and this module is how it was found out: the out-of-sample correction takes the
figure down and the deployable key puts it back up, further than it came down.

**Fitted and priced on the same month.** A threshold chosen to minimise the cost of a sample is
chosen partly to minimise that sample's noise, so it looks better there than anywhere else. The gap
has a name - optimism - and the honest version of wave 3's figure is the fitted threshold's cost in
a period it did not see.

**Keyed on the true intent.** A router runs before anybody knows what the contact was. Wave 3's rule
asked for the reclamacao threshold on a contact that *is* a complaint; a deployment can only ask for
the threshold of whatever the classifier said. That reads like a handicap and is not one. The label
the classifier reports is correlated with the event that decides the cost - whether the classifier
is wrong - and the true intent is not, so conditioning on the reported label is **better**
conditioning, not degraded conditioning. The deployable rule wins here, which is the opposite of
what the roadmap predicted.

**And judged against a formula the score could not feed.** With :mod:`svclab.calibration.score` in
hand the closed form can be given the input it assumes, on the same later period, which turns wave
3's assertion about *why* the formula failed into a measurement.

Everything here prices a rule the same way wave 3 did: run the bot behind the router, add the human
seconds, the misroute penalties and the deferral cost, divide by the contacts. The misroute penalty
is charged at the **true** intent's cost whatever the classifier thought, because a complaint
answered about parcel tracking costs what a mishandled complaint costs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from svclab.bot import THREE_TURNS, BotPolicy, classifier_labels, run
from svclab.routing import calibrated_threshold, cost_of, defer_below
from svclab.synth import (
    CALIBRATION,
    CENTRE,
    INTENTS,
    ROUTING,
    CalibrationProfile,
    CentreProfile,
    RoutingProfile,
)

from .score import (
    expected_calibration_error,
    fit_period,
    isotonic,
    isotonic_at,
    platt,
    platt_at,
    reliability_table,
    true_probability,
)

#: The thresholds swept, which is the grid wave 3 used. Coarse on purpose: a finer grid buys a
#: better in-sample number and, being fitted noise, a worse out-of-sample one.
#:
#: The ``float`` is not decoration. ``round`` on a numpy scalar returns a numpy scalar, so writing
#: this the obvious way gives the constant the type ``tuple[floating[Any], ...]`` and every default
#: argument annotated ``tuple[float, ...]`` becomes an error - on one Python of the matrix and not
#: on the one the local gate happened to run.
GRID = tuple(round(float(value), 2) for value in np.arange(0.0, 1.01, 0.02))

#: Columns of the optimism table, one row per intent and one for the queue.
OPTIMISM_COLUMNS = (
    "intent",
    "contacts",
    "fitted_threshold",
    "later_threshold",
    "fitted_seconds",
    "later_seconds",
    "optimism",
)

#: A threshold above every possible score, so that nothing is attempted. One is not enough: a score
#: of exactly one is not below one, and the calibrated scores reach it.
ALWAYS_DEFER = 1.01

#: Columns of the calibration comparison, one row per version of the score.
FORMULA_COLUMNS = (
    "score",
    "calibration_error",
    "naive_seconds",
    "amended_seconds",
    "swept_seconds",
    "naive_penalty",
    "amended_penalty",
)

#: Columns of the two keys a per-intent rule can be run on.
KEY_COLUMNS = (
    "key",
    "seconds_per_contact",
    "resolution_rate",
    "misroutes",
    "deferred",
    "saving_against_single",
)


def price(
    contacts: pd.DataFrame,
    scores: pd.DataFrame,
    rule: float | dict[str, float],
    policy: BotPolicy = THREE_TURNS,
    key: str = "intent",
    routing: RoutingProfile = ROUTING,
    centre: CentreProfile = CENTRE,
) -> dict[str, float]:
    """What one routing rule costs on one set of contacts, in the currency wave 3 used.

    Args:
        contacts: The contacts to price on.
        scores: The routing scores, raw or calibrated.
        rule: One threshold, or one per intent.
        policy: The bot policy behind the router.
        key: Which column a per-intent rule is keyed on.
        routing: The declared costs.
        centre: The centre's declared shape.

    Returns:
        Seconds per contact, the resolution rate, the misroutes and the deferrals.

    Raises:
        ValueError: If there are no contacts to price, which is a rule with no evidence behind it.
    """
    if len(contacts) == 0:
        raise ValueError("there are no contacts to price this rule on")
    routed = defer_below(contacts, scores, rule, key)
    outcomes = run(routed, policy, centre)
    measured = cost_of(outcomes, routed, routing)
    total = measured["human_seconds"] + measured["misroute_seconds"] + measured["defer_seconds"]
    first = outcomes[~outcomes["is_repeat"].to_numpy(dtype=bool)]
    return {
        "seconds_per_contact": total / len(routed),
        "resolution_rate": float(first["resolved"].mean()),
        "misroutes": measured["misroutes"],
        "deferred": measured["deferred"],
    }


def swept(
    contacts: pd.DataFrame,
    scores: pd.DataFrame,
    policy: BotPolicy = THREE_TURNS,
    key: str = "intent",
    grid: tuple[float, ...] = GRID,
    routing: RoutingProfile = ROUTING,
    centre: CentreProfile = CENTRE,
) -> dict[str, float]:
    """The cost-minimising threshold for each intent, swept on the contacts given.

    Each intent is swept on its own contacts, which is what makes a per-intent rule separable: the
    cost of one contact does not depend on how another was routed.

    Args:
        contacts: The contacts to sweep on.
        scores: The routing scores, raw or calibrated.
        policy: The bot policy behind the router.
        key: Which column the intents are grouped by - the true label or the classifier's.
        grid: Thresholds to try.
        routing: The declared costs.
        centre: The centre's declared shape.

    Returns:
        One threshold per intent that appears under the key.

    Raises:
        ValueError: If the grid is empty.
        KeyError: If the key is not a column of the contacts.
    """
    if not grid:
        raise ValueError("there are no thresholds to sweep")
    if key not in contacts.columns:
        raise KeyError(f"{key!r} is not a column to group the intents by")
    chosen = {}
    for label in sorted(set(contacts[key])):
        subset = contacts[contacts[key] == label]
        costs = [
            price(subset, scores, candidate, policy, key, routing, centre)["seconds_per_contact"]
            for candidate in grid
        ]
        chosen[str(label)] = float(grid[int(np.argmin(costs))])
    return chosen


def calibrated_scores(
    contacts: pd.DataFrame,
    scores: pd.DataFrame,
    calibration: CalibrationProfile = CALIBRATION,
    centre: CentreProfile = CENTRE,
) -> dict[str, pd.DataFrame]:
    """The score, in every version this module can judge, fitted on the fitting period only.

    Args:
        contacts: The contact table of the whole period.
        scores: The raw routing scores.
        calibration: The declared split and fitting settings.
        centre: The centre's declared shape.

    Returns:
        Score frames of the same shape as ``scores``, keyed ``raw``, ``isotonic``, ``platt`` and
        ``true``. The last is the control and reads a truth column, so nothing outside a study may
        deploy it.

    Raises:
        KeyError: If a column the calibration needs is missing.
    """
    joined = contacts.merge(scores, on="contact", how="left")
    reported = classifier_labels(joined)
    correct = reported["classified_correctly"].to_numpy(dtype=bool)
    score = joined["classifier_score"].to_numpy(dtype=float)
    fitting = fit_period(joined, calibration, centre)

    knots, values = isotonic(score[fitting], correct[fitting])
    slope, intercept = platt(score[fitting], correct[fitting], calibration)
    versions = {
        "raw": score,
        "isotonic": isotonic_at(knots, values, score),
        "platt": platt_at(slope, intercept, score),
        "true": true_probability(joined),
    }
    contact = joined["contact"].to_numpy()
    return {
        name: pd.DataFrame({"contact": contact, "classifier_score": value})
        for name, value in versions.items()
    }


def amended_threshold(defer_seconds: float, misroute_seconds: float, benefit: float) -> float:
    """Where to defer once attempting a contact the bot gets right is worth something.

    The closed form in :func:`svclab.routing.calibrated_threshold` prices two outcomes: attempting a
    wrong label costs ``misroute_seconds``, deferring costs ``defer_seconds``, and attempting a
    right label costs **nothing**. The last of those is the whole reason a bot is deployed, and it
    is not zero - a correctly labelled contact the bot resolves saves the human seconds it would
    have taken.

    Carry that term and the comparison becomes ``(1 - p) * misroute - p * benefit`` against
    ``defer``, so the rule is ``p > (misroute - defer) / (misroute + benefit)``. At a benefit of
    zero it is the original formula exactly, which is the check
    :func:`svclab.routing.calibrated_threshold` is reduced to.

    Args:
        defer_seconds: Cost of sending the contact past the bot.
        misroute_seconds: Cost of letting the bot try on a wrong label.
        benefit: Human seconds an attempt saves when the label is right, from
            :func:`resolve_benefit`.

    Returns:
        The threshold, clipped into the unit interval.

    Raises:
        ValueError: If a cost is negative, if the misroute cost is zero, or if the benefit is
            negative - a bot that costs the queue time on the contacts it gets right has no
            threshold worth computing, it has a policy to withdraw.
    """
    if benefit < 0:
        raise ValueError("a negative benefit is not a threshold problem")
    if defer_seconds < 0 or misroute_seconds < 0:
        raise ValueError("costs cannot be negative")
    if misroute_seconds == 0:
        raise ValueError("a misroute that costs nothing does not imply a threshold")
    return float(
        np.clip((misroute_seconds - defer_seconds) / (misroute_seconds + benefit), 0.0, 1.0)
    )


def _human_by_contact(
    contacts: pd.DataFrame,
    scores: pd.DataFrame,
    rule: float,
    policy: BotPolicy,
    centre: CentreProfile,
) -> np.ndarray:
    """Human seconds each contact costs under one blanket decision, in the contacts' own order."""
    routed = defer_below(contacts, scores, rule)
    outcomes = run(routed, policy, centre)
    totals = outcomes.groupby("contact")["human_seconds"].sum()
    return totals.reindex(contacts["contact"].to_numpy()).to_numpy(dtype=float)


def resolve_benefit(
    contacts: pd.DataFrame,
    scores: pd.DataFrame,
    policy: BotPolicy = THREE_TURNS,
    centre: CentreProfile = CENTRE,
) -> dict[str, float]:
    """Human seconds an attempt saves on a correctly labelled contact, per intent.

    Measured rather than assumed, and measured the only honest way: run the same contacts with the
    bot attempting everything and with the bot attempting nothing, and take the difference on the
    contacts whose label was right. It is an average over contacts that differ, which is the reason
    the amended threshold gets close to the swept optimum rather than reaching it.

    The scores are used only to be ignored - both runs are blanket decisions - so which version of
    the score is passed cannot change the answer.

    Args:
        contacts: The contacts to measure on, normally the fitting period.
        scores: Any score frame covering them.
        policy: The bot policy behind the router.
        centre: The centre's declared shape.

    Returns:
        One benefit per intent, in human seconds.

    Raises:
        ValueError: If there are no contacts, or an intent has no correctly labelled contact to
            average over - a benefit estimated from nothing is not a benefit.
    """
    if len(contacts) == 0:
        raise ValueError("there are no contacts to measure a benefit on")
    saved = _human_by_contact(contacts, scores, ALWAYS_DEFER, policy, centre) - _human_by_contact(
        contacts, scores, 0.0, policy, centre
    )
    correct = classifier_labels(contacts)["classified_correctly"].to_numpy(dtype=bool)
    intent = contacts["intent"].to_numpy()
    measured = {}
    for label in sorted(set(intent)):
        inside = (intent == label) & correct
        if not inside.any():
            raise ValueError(f"no correctly labelled {label} contact to measure a benefit on")
        measured[str(label)] = float(saved[inside].mean())
    return measured


def formula_table(
    contacts: pd.DataFrame,
    scores: pd.DataFrame,
    policy: BotPolicy = THREE_TURNS,
    grid: tuple[float, ...] = GRID,
    calibration: CalibrationProfile = CALIBRATION,
    routing: RoutingProfile = ROUTING,
    centre: CentreProfile = CENTRE,
) -> pd.DataFrame:
    """The closed form against the sweep, on each version of the score, in the later period.

    The formula's threshold depends only on the two costs, so it is the same number whatever the
    score is; what changes is whether the score it is applied to means what the formula assumes. The
    penalty is therefore a measurement of the input rather than of the rule - which is the claim
    wave 3 made and could not check.

    Args:
        contacts: The contact table of the whole period.
        scores: The raw routing scores.
        policy: The bot policy behind the router.
        grid: Thresholds to sweep.
        calibration: The declared split and fitting settings.
        routing: The declared costs.
        centre: The centre's declared shape.

    Returns:
        A frame with the columns in :data:`FORMULA_COLUMNS`, one row per version of the score.
    """
    versions = calibrated_scores(contacts, scores, calibration, centre)
    joined = contacts.merge(scores, on="contact", how="left")
    correct = classifier_labels(joined)["classified_correctly"].to_numpy(dtype=bool)
    fitting = fit_period(joined, calibration, centre)
    judged = contacts[~fitting]
    naive = {
        intent: calibrated_threshold(routing.defer_seconds, seconds)
        for intent, seconds in routing.misroute_seconds.items()
    }
    # The benefit is measured on the fitting period, like every other fitted quantity here.
    benefit = resolve_benefit(contacts[fitting], scores, policy, centre)
    amended = {
        intent: amended_threshold(routing.defer_seconds, seconds, benefit[intent])
        for intent, seconds in routing.misroute_seconds.items()
    }
    rows = []
    for name, version in versions.items():
        value = version["classifier_score"].to_numpy(dtype=float)
        error = expected_calibration_error(
            reliability_table(value[~fitting], correct[~fitting], calibration)
        )
        by_naive = price(judged, version, naive, policy, "intent", routing, centre)
        by_amended = price(judged, version, amended, policy, "intent", routing, centre)
        best = swept(judged, version, policy, "intent", grid, routing, centre)
        by_sweep = price(judged, version, best, policy, "intent", routing, centre)
        floor = by_sweep["seconds_per_contact"]
        rows.append(
            {
                "score": name,
                "calibration_error": error,
                "naive_seconds": by_naive["seconds_per_contact"],
                "amended_seconds": by_amended["seconds_per_contact"],
                "swept_seconds": floor,
                "naive_penalty": by_naive["seconds_per_contact"] / floor - 1.0,
                "amended_penalty": by_amended["seconds_per_contact"] / floor - 1.0,
            }
        )
    return pd.DataFrame(rows)[list(FORMULA_COLUMNS)]


def optimism_table(
    contacts: pd.DataFrame,
    scores: pd.DataFrame,
    policy: BotPolicy = THREE_TURNS,
    grid: tuple[float, ...] = GRID,
    key: str = "intent",
    calibration: CalibrationProfile = CALIBRATION,
    routing: RoutingProfile = ROUTING,
    centre: CentreProfile = CENTRE,
) -> pd.DataFrame:
    """What a threshold swept on one period costs in the next one, against that period's own best.

    Args:
        contacts: The contact table of the whole period.
        scores: The routing scores to sweep on.
        policy: The bot policy behind the router.
        grid: Thresholds to sweep.
        key: Which column the intents are grouped by.
        calibration: The declared split.
        routing: The declared costs.
        centre: The centre's declared shape.

    Returns:
        A frame with the columns in :data:`OPTIMISM_COLUMNS`: one row per intent and a final row for
        the queue, whose thresholds are blank because the queue's rule is the per-intent one.
    """
    fitting = fit_period(contacts, calibration, centre)
    early, late = contacts[fitting], contacts[~fitting]
    fitted = swept(early, scores, policy, key, grid, routing, centre)
    later = swept(late, scores, policy, key, grid, routing, centre)
    rows = []
    for label in sorted(fitted):
        subset = late[late[key] == label]
        on_fitted = price(subset, scores, fitted[label], policy, key, routing, centre)
        on_later = price(subset, scores, later[label], policy, key, routing, centre)
        rows.append(
            {
                "intent": label,
                "contacts": float(len(subset)),
                "fitted_threshold": fitted[label],
                "later_threshold": later[label],
                "fitted_seconds": on_fitted["seconds_per_contact"],
                "later_seconds": on_later["seconds_per_contact"],
                "optimism": on_fitted["seconds_per_contact"] - on_later["seconds_per_contact"],
            }
        )
    whole_fitted = price(late, scores, fitted, policy, key, routing, centre)
    whole_later = price(late, scores, later, policy, key, routing, centre)
    rows.append(
        {
            "intent": "queue",
            "contacts": float(len(late)),
            "fitted_threshold": float("nan"),
            "later_threshold": float("nan"),
            "fitted_seconds": whole_fitted["seconds_per_contact"],
            "later_seconds": whole_later["seconds_per_contact"],
            "optimism": whole_fitted["seconds_per_contact"] - whole_later["seconds_per_contact"],
        }
    )
    return pd.DataFrame(rows)[list(OPTIMISM_COLUMNS)]


def key_table(
    contacts: pd.DataFrame,
    scores: pd.DataFrame,
    policy: BotPolicy = THREE_TURNS,
    grid: tuple[float, ...] = GRID,
    calibration: CalibrationProfile = CALIBRATION,
    routing: RoutingProfile = ROUTING,
    centre: CentreProfile = CENTRE,
) -> pd.DataFrame:
    """The per-intent rule keyed on the true intent and on the classifier's, in the later period.

    Both rules are swept on the fitting period under their own key and priced on the later one, so
    the comparison is between two deployable procedures rather than between a procedure and an
    oracle's answer. The true-intent row is still not deployable; it is wave 3's rule, kept so the
    cost of the substitution is visible.

    Args:
        contacts: The contact table of the whole period, carrying ``predicted_intent``.
        scores: The routing scores.
        policy: The bot policy behind the router.
        grid: Thresholds to sweep.
        calibration: The declared split.
        routing: The declared costs.
        centre: The centre's declared shape.

    Returns:
        A frame with the columns in :data:`KEY_COLUMNS`, one row per key, with the saving each buys
        against the best single threshold on the same contacts.

    Raises:
        KeyError: If the contacts do not carry ``predicted_intent``.
    """
    if "predicted_intent" not in contacts.columns:
        raise KeyError("the contacts carry no predicted_intent to key a deployable rule on")
    fitting = fit_period(contacts, calibration, centre)
    early, late = contacts[fitting], contacts[~fitting]
    single_costs = [
        price(early, scores, candidate, policy, "intent", routing, centre)["seconds_per_contact"]
        for candidate in grid
    ]
    single = float(grid[int(np.argmin(single_costs))])
    baseline = price(late, scores, single, policy, "intent", routing, centre)
    rows = [
        {
            "key": "single",
            "seconds_per_contact": baseline["seconds_per_contact"],
            "resolution_rate": baseline["resolution_rate"],
            "misroutes": baseline["misroutes"],
            "deferred": baseline["deferred"],
            "saving_against_single": 0.0,
        }
    ]
    for key in ("intent", "predicted_intent"):
        rule = swept(early, scores, policy, key, grid, routing, centre)
        measured = price(late, scores, rule, policy, key, routing, centre)
        rows.append(
            {
                "key": key,
                "seconds_per_contact": measured["seconds_per_contact"],
                "resolution_rate": measured["resolution_rate"],
                "misroutes": measured["misroutes"],
                "deferred": measured["deferred"],
                "saving_against_single": baseline["seconds_per_contact"]
                - measured["seconds_per_contact"],
            }
        )
    return pd.DataFrame(rows)[list(KEY_COLUMNS)]


def intent_labels() -> tuple[str, ...]:
    """The declared intents, in the order the generator lists them."""
    return tuple(profile.intent for profile in INTENTS)

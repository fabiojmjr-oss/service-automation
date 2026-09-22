"""The outcome that looks like a saving.

Nine waves have measured what an automation costs in seconds, agents, sessions and people. Three of
them leaned on the same relief valve without pricing it: Erlang A reaches a steady state **because**
customers give up, an occupancy ceiling is satisfied by understaffing **because** the customers who
abandon are what keeps occupancy down, and the attrition loop's second regime is reached by losing
customers. Each time the note was the same - abandonment is the thing the business is trying not to
do - and each time the repository had no currency to say how much of it was happening.

This module is that currency, and it produces three findings the earlier waves could not.

**A churn rate is a gauge, not a measurement.** Nobody can see a customer leave. What an operation
sees is silence, and a rule that calls a silent customer churned is a binary assessor with a
sensitivity and a specificity - so wave 2's attenuation identity applies to it exactly. A comparison
of two policies on churn is multiplied by the rule's Youden index, towards zero, always.

**Losing customers improves almost every number in this repository.** A customer who leaves stops
generating contacts. Fewer contacts is less load, fewer sessions, fewer human hours - and the per
contact figures every wave here quotes are ratios whose denominator the churn removes. The direction
is not a subtlety: it is the same sign as an improvement, on a metric an operation reports monthly.

**And the valve has a price in people.** The abandonment three waves used as relief converts into
customers at a declared rate, which turns wave 3's "perfectly stable at six agents" and wave 7's
"occupancy held at 0.8121" into a number of customers each decision spends.

The mechanism is declared rather than fitted: a customer's chance of not coming back depends on the
worst thing that happened to them, and the worst thing dominates - a contact abandoned in its first
session and resolved on its return counts as abandoned, because that is what the customer
experienced. Whether the memory works that way is an assumption, stated below rather than hidden.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from svclab.containment import containment_table
from svclab.synth import CENTRE, CHURN, CentreProfile, ChurnProfile

#: The three experiences a contact can leave a customer with, worst first.
EXPERIENCES = ("abandoned", "unresolved", "resolved")

#: Columns of the per-contact experience frame.
EXPERIENCE_COLUMNS = ("contact", "customer", "arrival_hour", "experience", "leave_chance")

#: Columns of the departure frame, one row per customer who was seen at all.
DEPARTURE_COLUMNS = ("customer", "left", "left_after_hour", "contacts_seen", "contacts_lost")

#: Columns of the detection table: what a silence rule reports against what happened.
DETECTION_COLUMNS = (
    "customers",
    "left",
    "prevalence",
    "flagged",
    "sensitivity",
    "specificity",
    "youden",
    "precision",
)

#: Columns of the per-policy table, one row per policy.
POLICY_COLUMNS = (
    "policy",
    "customers",
    "left",
    "share_left",
    "contacts_lost",
    "human_hours",
    "human_hours_after",
    "hours_saved",
    "minutes_per_customer_lost",
    "session_containment",
    "session_containment_after",
)

#: Columns of the valve table, one row per abandonment rate a plan lands on.
VALVE_COLUMNS = ("abandonment", "contacts", "abandoned", "customers_lost", "share_of_customers")


def experience_of(contacts: pd.DataFrame, outcomes: pd.DataFrame) -> pd.DataFrame:
    """The worst thing that happened to each contact, and what it does to the relationship.

    A contact that was abandoned and then resolved on its return counts as **abandoned**. The
    customer abandoned a conversation; that it was eventually fixed does not unhappen.

    Args:
        contacts: The contact table.
        outcomes: Outcomes from :func:`svclab.bot.run` over those contacts, all sessions.

    Returns:
        A frame with the columns in :data:`EXPERIENCE_COLUMNS`, one row per contact.

    Raises:
        KeyError: If either frame is missing a column this needs.
    """
    missing = {"contact", "customer", "arrival_hour"} - set(contacts.columns)
    if missing:
        raise KeyError(f"the contact table is missing {sorted(missing)}")
    missing = {"contact", "outcome", "resolved"} - set(outcomes.columns)
    if missing:
        raise KeyError(f"the outcome table is missing {sorted(missing)}")
    grouped = outcomes.groupby("contact")
    abandoned = grouped["outcome"].apply(lambda column: bool((column == "abandoned").any()))
    resolved = grouped["resolved"].any()
    order = contacts["contact"].to_numpy()
    was_abandoned = abandoned.reindex(order).to_numpy(dtype=bool)
    was_resolved = resolved.reindex(order).to_numpy(dtype=bool)
    otherwise = np.where(was_resolved, "resolved", "unresolved")
    experience = np.where(was_abandoned, "abandoned", otherwise)
    return pd.DataFrame(
        {
            "contact": order,
            "customer": contacts["customer"].to_numpy(),
            "arrival_hour": contacts["arrival_hour"].to_numpy(dtype=float),
            "experience": experience,
            "leave_chance": np.zeros(len(order)),
        }
    )[list(EXPERIENCE_COLUMNS)]


def leave_chance(experience: np.ndarray, churn: ChurnProfile = CHURN) -> np.ndarray:
    """The declared probability of not coming back, per contact, from its experience.

    Args:
        experience: One of :data:`EXPERIENCES` per contact.
        churn: The declared curve.

    Returns:
        One probability per contact.

    Raises:
        ValueError: If an experience is not one of the three declared ones - a fourth category would
            have no probability and returning zero for it would hide the omission.
    """
    declared = {
        "abandoned": churn.leave_after_abandoned,
        "unresolved": churn.leave_after_unresolved,
        "resolved": churn.leave_after_resolved,
    }
    unknown = set(np.unique(experience)) - set(declared)
    if unknown:
        raise ValueError(f"no declared leaving chance for {sorted(unknown)}")
    return np.array([declared[value] for value in experience], dtype=float)


def departures(
    contacts: pd.DataFrame,
    outcomes: pd.DataFrame,
    draws: pd.DataFrame,
    churn: ChurnProfile = CHURN,
) -> pd.DataFrame:
    """Which customers stopped coming back, when, and how many contacts went with them.

    A customer leaves after the **first** contact whose draw falls under that contact's declared
    chance, taking every later contact of theirs with it. The walk is in arrival order, because a
    departure cannot be caused by a conversation that has not happened yet.

    Args:
        contacts: The contact table.
        outcomes: Outcomes from :func:`svclab.bot.run` over those contacts.
        draws: The churn draws from :func:`svclab.synth.churn_draws`.
        churn: The declared curve.

    Returns:
        A frame with the columns in :data:`DEPARTURE_COLUMNS`, one row per customer seen, sorted by
        customer. ``left_after_hour`` is ``nan`` for a customer who stayed.

    Raises:
        KeyError: If the draws do not cover every contact.
    """
    table = experience_of(contacts, outcomes)
    table["leave_chance"] = leave_chance(table["experience"].to_numpy(), churn)
    joined = table.merge(draws, on="contact", how="left")
    if joined["u_leave"].isna().any():
        raise KeyError("the churn draws do not cover every contact")

    joined = joined.sort_values(["customer", "arrival_hour"], kind="stable")
    chance = joined["leave_chance"].to_numpy(dtype=float)
    triggers = joined["u_leave"].to_numpy(dtype=float) < chance
    customer = joined["customer"].to_numpy()
    hour = joined["arrival_hour"].to_numpy(dtype=float)

    # Position within the customer's own contacts, and how many of their earlier contacts triggered.
    frame = pd.DataFrame({"customer": customer, "triggered": triggers, "hour": hour})
    earlier = frame.groupby("customer")["triggered"].cumsum().to_numpy() - triggers
    # A contact happens only if nothing earlier ended the relationship; the one that triggers still
    # happened, which is what makes it the contact the departure is attributed to.
    survives = earlier == 0
    first_trigger = survives & triggers

    rows = pd.DataFrame(
        {
            "customer": customer,
            "survives": survives,
            "first_trigger": first_trigger,
            # The departure hour as a masked minimum rather than a per-group apply: infinity where
            # nothing triggered, so the minimum is the triggering contact's hour and a customer who
            # stayed comes back as infinity, which the last step turns into the nan it means.
            "hour_or_never": np.where(first_trigger, hour, np.inf),
        }
    )
    grouped = rows.groupby("customer")
    left = grouped["first_trigger"].any()
    seen = grouped["survives"].sum()
    total = grouped.size()
    when = grouped["hour_or_never"].min().replace(np.inf, np.nan)
    return pd.DataFrame(
        {
            "customer": left.index.to_numpy(),
            "left": left.to_numpy(dtype=bool),
            "left_after_hour": when.to_numpy(dtype=float),
            "contacts_seen": seen.to_numpy(dtype=float),
            "contacts_lost": (total.to_numpy(dtype=float) - seen.to_numpy(dtype=float)),
        }
    )[list(DEPARTURE_COLUMNS)]


def surviving(contacts: pd.DataFrame, departed: pd.DataFrame) -> pd.DataFrame:
    """The contacts that would still have happened once the leavers had left.

    Args:
        contacts: The contact table.
        departed: A frame from :func:`departures`.

    Returns:
        A subset of the contact table, in its original order.

    Raises:
        KeyError: If the departure frame does not cover every customer in the contacts.
    """
    when = departed.set_index("customer")["left_after_hour"]
    customers = contacts["customer"].to_numpy()
    unknown = set(customers) - set(when.index)
    if unknown:
        raise KeyError(f"the departure frame says nothing about {len(unknown)} of these customers")
    boundary = when.reindex(customers).to_numpy(dtype=float)
    hour = contacts["arrival_hour"].to_numpy(dtype=float)
    # nan comparisons are false, so a customer who never left keeps every contact.
    return contacts[~(hour > boundary)]


def silence_flag(
    contacts: pd.DataFrame,
    centre: CentreProfile = CENTRE,
    churn: ChurnProfile = CHURN,
) -> pd.DataFrame:
    """Which customers an operation would call churned, from silence alone.

    The only signal a real operation has. It is a definition, and the point of this function is that
    it is a definition applied to the surviving contacts rather than a reading of the truth.

    Args:
        contacts: The contacts that actually happened - the surviving ones, not the original table.
        centre: The centre's declared shape, for the length of the period.
        churn: The declared silence rule.

    Returns:
        A frame with ``customer``, ``last_hour`` and ``flagged``.

    Raises:
        ValueError: If the silence window is not shorter than the period, which would flag nobody or
            everybody and is a rule rather than a signal.
    """
    window = churn.silence_days * 24.0
    period = centre.days * 24.0
    if not 0.0 < window < period:
        raise ValueError("a silence window outside the period cannot separate anybody")
    last = contacts.groupby("customer")["arrival_hour"].max()
    return pd.DataFrame(
        {
            "customer": last.index.to_numpy(),
            "last_hour": last.to_numpy(dtype=float),
            "flagged": last.to_numpy(dtype=float) < period - window,
        }
    )


def detection_table(departed: pd.DataFrame, flagged: pd.DataFrame) -> pd.DataFrame:
    """What the silence rule reports, against what happened, as a gauge study.

    Args:
        departed: A frame from :func:`departures`.
        flagged: A frame from :func:`silence_flag`.

    Returns:
        A one-row frame with the columns in :data:`DETECTION_COLUMNS`.

    Raises:
        ValueError: If nobody left or everybody did, which is a study with no contrast in it.
    """
    joined = departed.merge(flagged[["customer", "flagged"]], on="customer", how="left")
    truth = joined["left"].to_numpy(dtype=bool)
    # A customer with no surviving contact is absent from the silence frame, and silence is what
    # they are.
    called = joined["flagged"].fillna(True).to_numpy(dtype=bool)
    if truth.all() or not truth.any():
        raise ValueError("a gauge study needs both kinds of customer")
    sensitivity = float(called[truth].mean())
    specificity = float((~called[~truth]).mean())
    precision = float(truth[called].mean()) if called.any() else float("nan")
    return pd.DataFrame(
        [
            {
                "customers": float(len(truth)),
                "left": float(truth.sum()),
                "prevalence": float(truth.mean()),
                "flagged": float(called.sum()),
                "sensitivity": sensitivity,
                "specificity": specificity,
                "youden": sensitivity + specificity - 1.0,
                "precision": precision,
            }
        ]
    )[list(DETECTION_COLUMNS)]


#: Contact counts the silence rule is measured separately on, because silence means different things
#: to a customer who contacts once a month and to one who contacts weekly.
FREQUENCY_BANDS = (1, 2, 3)

#: Columns of the stratified detection table, one row per band plus one for everybody.
BAND_COLUMNS = (
    "contacts_seen",
    "customers",
    "left",
    "sensitivity",
    "specificity",
    "youden",
    "precision",
)


def detection_by_frequency(
    departed: pd.DataFrame,
    flagged: pd.DataFrame,
    bands: tuple[int, ...] = FREQUENCY_BANDS,
) -> pd.DataFrame:
    """The silence rule's gauge study, split by how often the customer contacts.

    The rule says a customer who has not been seen lately has gone. For somebody who contacts twice
    a month that is a statement about their behaviour; for somebody who contacts once it is a
    statement about the calendar. Splitting the study shows which of the two the rule is measuring.

    Args:
        departed: A frame from :func:`departures`.
        flagged: A frame from :func:`silence_flag`.
        bands: Contact counts to report on their own; everything above is one band.

    Returns:
        A frame with the columns in :data:`BAND_COLUMNS`, one row per band and a final ``all`` row.

    Raises:
        ValueError: If the bands are not increasing and positive, which would make a row mean two
            different things.
    """
    if not bands or list(bands) != sorted(set(bands)) or bands[0] < 1:
        raise ValueError("the bands have to be increasing distinct contact counts of at least one")
    joined = departed.merge(flagged[["customer", "flagged"]], on="customer", how="left")
    joined["flagged"] = joined["flagged"].fillna(True)
    seen = joined["contacts_seen"].to_numpy(dtype=float)
    labels = [str(band) for band in bands] + [f"{bands[-1] + 1}+"]
    masks = [seen == float(band) for band in bands] + [seen > float(bands[-1])]
    rows = []
    for label, mask in zip(labels + ["all"], masks + [np.ones(len(seen), dtype=bool)], strict=True):
        block = joined[mask]
        truth = block["left"].to_numpy(dtype=bool)
        called = block["flagged"].to_numpy(dtype=bool)
        sensitivity = float(called[truth].mean()) if truth.any() else float("nan")
        specificity = float((~called[~truth]).mean()) if (~truth).any() else float("nan")
        rows.append(
            {
                "contacts_seen": label,
                "customers": float(len(block)),
                "left": float(truth.sum()),
                "sensitivity": sensitivity,
                "specificity": specificity,
                "youden": sensitivity + specificity - 1.0,
                "precision": float(truth[called].mean()) if called.any() else float("nan"),
            }
        )
    return pd.DataFrame(rows)[list(BAND_COLUMNS)]


def policy_table(
    contacts: pd.DataFrame,
    outcomes: dict[str, pd.DataFrame],
    draws: pd.DataFrame,
    churn: ChurnProfile = CHURN,
) -> pd.DataFrame:
    """What each policy costs in customers, beside what it costs in the currency of the other waves.

    The ``_after`` columns are the same metrics recomputed on the contacts that would still have
    happened. They are the point of the table: the denominator falls with the customers, so the
    per contact figures improve while the loss they are caused by grows.

    Args:
        contacts: The contact table, one arm.
        outcomes: Outcome frames from :func:`svclab.bot.run`, keyed by policy name.
        draws: The churn draws from :func:`svclab.synth.churn_draws`.
        churn: The declared curve.

    Returns:
        A frame with the columns in :data:`POLICY_COLUMNS`, one row per policy in the order given.

    Raises:
        ValueError: If no outcomes are supplied.
    """
    if not outcomes:
        raise ValueError("there are no policies to price")
    rows = []
    for policy, frame in outcomes.items():
        departed = departures(contacts, frame, draws, churn)
        kept = surviving(contacts, departed)
        after = frame[frame["contact"].isin(set(kept["contact"]))]
        seconds = float(frame["human_seconds"].sum())
        seconds_after = float(after["human_seconds"].sum())
        saved = (seconds - seconds_after) / 3600.0
        lost = float(departed["left"].sum())
        # Containment through the module that defines it, rather than a second reading of `route`:
        # the first version of this function called every bot-routed session contained, which counts
        # the human queue at 0.96 and is not any of the four definitions wave 1 separated.
        before = containment_table({policy: frame}, contacts)
        recomputed = containment_table({policy: after}, kept)
        rows.append(
            {
                "policy": policy,
                "customers": float(len(departed)),
                "left": lost,
                "share_left": float(departed["left"].mean()),
                "contacts_lost": float(departed["contacts_lost"].sum()),
                "human_hours": seconds / 3600.0,
                "human_hours_after": seconds_after / 3600.0,
                "hours_saved": saved,
                "minutes_per_customer_lost": saved * 60.0 / lost if lost else float("nan"),
                "session_containment": float(before["session_containment"].iloc[0]),
                "session_containment_after": float(recomputed["session_containment"].iloc[0]),
            }
        )
    return pd.DataFrame(rows)[list(POLICY_COLUMNS)]


def valve_table(
    abandonment: tuple[float, ...],
    contacts: int,
    customers: int,
    churn: ChurnProfile = CHURN,
) -> pd.DataFrame:
    """The abandonment three earlier waves used as relief, converted into customers.

    First order on purpose: abandoned contacts times the declared chance of leaving after
    abandoning. It ignores that two abandoned contacts can belong to one customer, so it is an
    **upper** bound on customers lost - which is the honest direction for a number whose job is to
    make a decision look expensive rather than cheap.

    Args:
        abandonment: Abandonment rates a plan lands on.
        contacts: Contacts the period carries.
        customers: Customers behind them, for the share.
        churn: The declared curve.

    Returns:
        A frame with the columns in :data:`VALVE_COLUMNS`, one row per rate.

    Raises:
        ValueError: If no rates are supplied, if a rate is outside the unit interval, or if the
            counts are not positive.
    """
    if not abandonment:
        raise ValueError("there are no abandonment rates to price")
    if any(rate < 0.0 or rate > 1.0 for rate in abandonment):
        raise ValueError("an abandonment rate outside the unit interval is not a rate")
    if contacts <= 0 or customers <= 0:
        raise ValueError("a period with no contacts or no customers has no valve to price")
    rows = []
    for rate in abandonment:
        abandoned = rate * contacts
        lost = abandoned * churn.leave_after_abandoned
        rows.append(
            {
                "abandonment": float(rate),
                "contacts": float(contacts),
                "abandoned": abandoned,
                "customers_lost": lost,
                "share_of_customers": lost / customers,
            }
        )
    return pd.DataFrame(rows)[list(VALVE_COLUMNS)]

"""Containment, its four legitimate definitions, and the one quantity a budget needed instead.

A containment rate is a share with a numerator nobody agreed on. Does a session the customer
abandoned count as contained? Does one that came back tomorrow? Does one the bot answered for a
customer who would have found the answer alone? Each answer is defensible and they do not produce
the same number, so this module returns **all of them** rather than picking one silently - the same
rule a sibling repository applies to fill rate and on-time delivery.

And then the harder point. Every one of those four is a share of what the bot did, and none of them
is what a business case claims: **contacts a human did not have to handle because the bot existed.**
That quantity needs a counterfactual, which means an arm of customers who never met the bot.
:func:`deflection` refuses to return a number without one, because the alternative is a figure that
reads like evidence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

#: Columns of the containment table, one row per policy.
CONTAINMENT_COLUMNS = (
    "policy",
    "contacts",
    "sessions",
    "repeats_per_contact",
    "session_containment",
    "resolution_containment",
    "repeat_adjusted_containment",
    "needed_containment",
    "resolution_rate",
    "human_hours",
)

#: Columns of the table that shows which contacts a bot keeps.
SELECTION_COLUMNS = (
    "group",
    "contacts",
    "share",
    "mean_difficulty",
    "would_self_serve_rate",
    "mean_human_seconds",
)

DEFAULT_ALPHA = 0.05


def containment_table(
    outcomes: Mapping[str, pd.DataFrame],
    contacts: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Every defensible containment rate, per policy, side by side.

    The four definitions, in the order a deployment discovers them:

    - **session containment**: the session did not reach a human. The number on the slide, and the
      only one that counts an abandoned customer as a success.
    - **resolution containment**: the bot resolved it. Abandonment is no longer a win.
    - **repeat-adjusted containment**: it did not reach a human *and* the customer did not come
      back. A contained contact that returns within the window was a deferred contact.
    - **needed containment**: the bot resolved it and the customer would not have got there alone.
      Requires the counterfactual column, so it is ``nan`` unless the contact table is supplied -
      which is the state every real operation is in permanently.

    All four are computed over **first sessions**, because that is the denominator a vendor reports
    against and a repeat session was never a containment opportunity: it arrives routed to a human.
    ``sessions`` and ``human_hours`` count every session, repeats included, because that is what the
    queue receives. The gap between those two denominators is the whole argument of this module.

    Args:
        outcomes: One outcome frame per policy name, from :func:`svclab.bot.run`.
        contacts: Optional contact table, for the one definition that needs the truth.

    Returns:
        A frame with the columns in :data:`CONTAINMENT_COLUMNS`, one row per policy.

    Raises:
        ValueError: If a policy's outcome frame is empty, which would make every rate a division by
            zero rather than a rate of zero.
    """
    self_serve = (
        dict(zip(contacts["contact"], contacts["would_self_serve"], strict=True))
        if contacts is not None
        else None
    )
    rows = []
    for name, frame in outcomes.items():
        if frame.empty:
            raise ValueError(f"the outcome frame for {name!r} is empty; there is no rate to report")
        first = frame[~frame["is_repeat"].to_numpy(dtype=bool)]
        human = first["handled_by_human"].to_numpy(dtype=bool)
        returns = first["returns"].to_numpy(dtype=bool)
        by_bot = first["outcome"].to_numpy() == "resolved-by-bot"
        if self_serve is not None:
            would = np.array([bool(self_serve[key]) for key in first["contact"]])
            needed = float(np.mean(by_bot & ~would))
        else:
            needed = float("nan")
        rows.append(
            {
                "policy": name,
                "contacts": int(len(first)),
                "sessions": int(len(frame)),
                "repeats_per_contact": float(len(frame) - len(first)) / len(first),
                "session_containment": float(np.mean(~human)),
                "resolution_containment": float(np.mean(by_bot)),
                "repeat_adjusted_containment": float(np.mean(~human & ~returns)),
                "needed_containment": needed,
                "resolution_rate": float(first["resolved"].mean()),
                "human_hours": float(frame["human_seconds"].sum() / 3600.0),
            }
        )
    return pd.DataFrame(rows)[list(CONTAINMENT_COLUMNS)]


@dataclass(frozen=True)
class Deflection:
    """What a bot removed from the human queue, measured against an arm that never met it.

    Attributes:
        treated_customers: Customers in the arm that met the bot.
        holdout_customers: Customers in the arm that did not.
        treated_per_customer: Human-handled contacts per customer in the treated arm.
        holdout_per_customer: The same in the holdout arm.
        deflected_per_customer: The difference, signed so that a positive number means the bot
            removed work.
        standard_error: Standard error of that difference, from the spread **between customers**.
            The customer is the unit of randomisation, so it is the unit of analysis; using the
            contact would treat one person's four contacts as four independent observations.
        df: Welch degrees of freedom behind the interval.
        alpha: Significance level of the interval.
        untested_because: Empty when the comparison could be made. Otherwise the reason it could
            not, which is not the same thing as a bot that deflected nothing.
    """

    treated_customers: int
    holdout_customers: int
    treated_per_customer: float
    holdout_per_customer: float
    deflected_per_customer: float
    standard_error: float
    df: float
    alpha: float = DEFAULT_ALPHA
    untested_because: str = ""

    @property
    def interval(self) -> tuple[float, float]:
        """Confidence interval on the deflection per customer."""
        if self.untested_because or not np.isfinite(self.df):
            return (float("nan"), float("nan"))
        half = float(stats.t.ppf(1.0 - self.alpha / 2.0, self.df)) * self.standard_error
        return (self.deflected_per_customer - half, self.deflected_per_customer + half)

    @property
    def significant(self) -> bool:
        """Whether the comparison can distinguish the deflection from nothing."""
        if self.untested_because or self.standard_error == 0.0:
            return False
        low, high = self.interval
        return low > 0.0 or high < 0.0

    def share_of(self, containment: float) -> float:
        """The measured deflection as a share of a containment rate that was quoted for it.

        The number to put next to a slide. A share of 1.0 means the containment rate was telling the
        truth about the queue; 0.55 means forty-five per cent of what was contained was work no
        human was going to do.

        Args:
            containment: The containment rate the deployment reported, per contact.

        Returns:
            The ratio, or ``nan`` where there is nothing to compare against - including when the
            containment rate is zero, because a ratio against an unmeasured denominator is exactly
            what this module exists to refuse.
        """
        if self.untested_because or containment == 0.0:
            return float("nan")
        return self.deflected_per_customer / (containment * self.contacts_per_customer)

    #: Contacts per customer in the holdout arm, which is the scale a per-customer figure has to be
    #: divided by before it can be compared with a per-contact rate.
    contacts_per_customer: float = 1.0


def deflection(
    treated: pd.DataFrame | None,
    holdout: pd.DataFrame | None,
    alpha: float = DEFAULT_ALPHA,
) -> Deflection:
    """Human contacts per customer, treated against holdout.

    The estimand a business case claims and never measures: not what share of sessions the bot held,
    but how many contacts a human did not have to take because it existed. Measured per customer,
    because the arms were assigned per customer.

    Args:
        treated: Outcomes for customers who met the bot, or ``None``.
        holdout: Outcomes for customers who did not, or ``None``. This is the argument a real
            deployment does not have, and passing ``None`` returns a refusal rather than a number.
        alpha: Significance level for the interval.

    Returns:
        A :class:`Deflection`. Where either arm is missing or has fewer than two customers, the
        estimate is ``nan`` and ``untested_because`` says why.
    """
    nothing = float("nan")

    def refuse(reason: str) -> Deflection:
        return Deflection(
            treated_customers=0 if treated is None else int(treated["customer"].nunique()),
            holdout_customers=0 if holdout is None else int(holdout["customer"].nunique()),
            treated_per_customer=nothing,
            holdout_per_customer=nothing,
            deflected_per_customer=nothing,
            standard_error=nothing,
            df=nothing,
            alpha=alpha,
            untested_because=reason,
        )

    if holdout is None or treated is None:
        return refuse(
            "there is no arm to compare against, so what the bot removed from the queue is not a "
            "quantity this data contains"
        )
    if treated.empty or holdout.empty:
        return refuse("one of the two arms has no contacts in it")

    def per_customer(frame: pd.DataFrame) -> np.ndarray:
        """Human-handled sessions per customer, repeats included.

        Repeats included is the entire point: a contact the bot failed to resolve arrives at the
        queue a second time, and a deflection figure that counts only first sessions is counting the
        same thing the containment rate counts.
        """
        grouped = frame.groupby("customer")["handled_by_human"].sum()
        return grouped.to_numpy(dtype=float)

    kept, lost = per_customer(treated), per_customer(holdout)
    if kept.size < 2 or lost.size < 2:
        return refuse("a spread between customers needs at least two customers in each arm")

    kept_var, lost_var = float(kept.var(ddof=1)), float(lost.var(ddof=1))
    error = float(np.sqrt(kept_var / kept.size + lost_var / lost.size))
    if error == 0.0:
        df = float("inf")
    else:
        df = error**4 / (
            (kept_var / kept.size) ** 2 / (kept.size - 1)
            + (lost_var / lost.size) ** 2 / (lost.size - 1)
        )
    first_sessions = holdout[~holdout["is_repeat"].to_numpy(dtype=bool)]
    contacts_each = float(len(first_sessions) / lost.size)
    return Deflection(
        treated_customers=int(kept.size),
        holdout_customers=int(lost.size),
        treated_per_customer=float(kept.mean()),
        holdout_per_customer=float(lost.mean()),
        deflected_per_customer=float(lost.mean() - kept.mean()),
        standard_error=error,
        df=df,
        alpha=alpha,
        contacts_per_customer=contacts_each,
    )


def selection_profile(outcomes: pd.DataFrame, contacts: pd.DataFrame) -> pd.DataFrame:
    """Which contacts the bot kept and which it passed on, by the truth it cannot see.

    The mechanism behind every figure in this module: a bot does not take a random sample of the
    queue. It takes the easy end, so the residue a human receives is harder than the average contact
    was - and the handling time that residue carries is what a capacity plan has to be built on
    rather than on the volume that left.

    Args:
        outcomes: Outcomes from :func:`svclab.bot.run`.
        contacts: The contact table, for the difficulty and the counterfactual.

    Returns:
        A frame with the columns in :data:`SELECTION_COLUMNS`, one row per group: what the bot
        resolved, what the customer abandoned, and what reached a human.
    """
    joined = outcomes.merge(
        contacts[["contact", "difficulty", "would_self_serve", "human_seconds"]],
        on="contact",
        how="left",
        suffixes=("", "_truth"),
    )
    joined = joined[~joined["is_repeat"].to_numpy(dtype=bool)]
    groups = {
        "resolved-by-bot": joined["outcome"] == "resolved-by-bot",
        "abandoned": joined["outcome"] == "abandoned",
        "reached-a-human": joined["handled_by_human"],
        "came-back": joined["returns"],
        "all-contacts": np.ones(len(joined), dtype=bool),
    }
    rows = []
    for name, mask in groups.items():
        subset = joined[mask]
        rows.append(
            {
                "group": name,
                "contacts": int(len(subset)),
                "share": float(len(subset) / len(joined)),
                "mean_difficulty": float(subset["difficulty"].mean())
                if len(subset)
                else float("nan"),
                "would_self_serve_rate": (
                    float(subset["would_self_serve"].mean()) if len(subset) else float("nan")
                ),
                "mean_human_seconds": (
                    float(subset["human_seconds_truth"].mean()) if len(subset) else float("nan")
                ),
            }
        )
    return pd.DataFrame(rows)[list(SELECTION_COLUMNS)]

"""The frequent caller who is also a difficult one, and what he does to a per-customer number.

Wave 4 gave a customer traits and left their contact **rate** alone, so the busiest customer in the
account was busy by accident and every cluster held about two contacts. This module relaxes that. A
customer's propensity to contact is log-normal, and its latent value correlates with that customer's
own difficulty at a declared amount - see :class:`svclab.synth.ConcentrationProfile`.

The reassignment reuses the uniform that chose the customer in the first place and never crosses an
arm, so **every per-contact figure in the earlier waves is bit-for-bit identical** in the regrouped
world. That is not approximate agreement: the contacts, their traits and their arms are the same
objects, grouped differently.

Which means everything in this module is about the two things grouping decides:

- how unequal the clusters are, which is what a design effect is computed from;
- and who pays, which no contact-weighted figure can show.

The control is the world regrouped with **equal** rates, not the world waves 1 to 4 published:
reassigning contacts among the customers an account actually saw makes clusters larger on its own,
and attributing that to concentration would be attributing an artefact.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from svclab.containment import deflection
from svclab.experiment import effective_cluster_size

#: Columns of the concentration table, one row per world.
CONCENTRATION_COLUMNS = (
    "world",
    "customers",
    "contacts",
    "mean_cluster_size",
    "effective_cluster_size",
    "gini",
    "top_decile_share",
    "frequency_difficulty_correlation",
)

#: Columns of the burden table, one row per world.
BURDEN_COLUMNS = (
    "world",
    "difficulty_per_contact",
    "resolution_rate",
    "top_decile_volume",
    "top_decile_unresolved",
    "top_decile_human_hours",
    "customers_failed_three_times",
)

#: Columns of the precision table, one row per world.
PRECISION_COLUMNS = (
    "world",
    "customers",
    "deflected_per_customer",
    "standard_error",
    "relative_error",
    "interval_width",
)

#: Share of customers, ranked by contact count, that the burden table calls the top decile.
TOP_SHARE = 0.10


def gini(sizes: pd.Series | pd.Index | list[float]) -> float:
    """Inequality of a set of counts, on the usual zero-to-one scale.

    Zero when every count is identical. Approaches ``1 - 1/n`` when one holds everything, which is
    the highest a finite set can reach - the textbook 1.0 is a limit and not a value, and a function
    that returned it would be rounding up.

    Args:
        sizes: One count per customer.

    Returns:
        The Gini coefficient.

    Raises:
        ValueError: If there are no counts, or they sum to zero.
    """
    values = np.sort(np.asarray(list(sizes), dtype=float))
    if values.size == 0:
        raise ValueError("an inequality measure needs at least one count")
    total = float(values.sum())
    if total <= 0.0:
        raise ValueError("counts that sum to zero have no inequality")
    count = values.size
    ranks = np.arange(1, count + 1, dtype=float)
    return float((2.0 * ranks - count - 1.0).dot(values) / (count * total))


def _sizes(table: pd.DataFrame) -> pd.Series:
    """Contacts per customer, largest first."""
    return table.groupby("customer").size().sort_values(ascending=False)


def concentration_table(contacts: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """How unequally the volume is spread, and whether the heavy users are the difficult ones.

    Args:
        contacts: Contact tables by world label, all holding the same contacts.

    Returns:
        A frame with the columns in :data:`CONCENTRATION_COLUMNS`, one row per world.

    Raises:
        ValueError: If a table is empty.
    """
    rows = []
    for label, table in contacts.items():
        if table.empty:
            raise ValueError(f"the {label!r} world has no contacts in it")
        sizes = _sizes(table)
        head = max(1, int(round(TOP_SHARE * sizes.size)))
        per_customer = table.groupby("customer")["difficulty"].mean()
        rows.append(
            {
                "world": label,
                "customers": int(sizes.size),
                "contacts": int(len(table)),
                "mean_cluster_size": float(sizes.mean()),
                "effective_cluster_size": effective_cluster_size(sizes),
                "gini": gini(sizes),
                "top_decile_share": float(sizes.head(head).sum() / sizes.sum()),
                "frequency_difficulty_correlation": float(
                    np.corrcoef(sizes.to_numpy(dtype=float), per_customer.reindex(sizes.index))[
                        0, 1
                    ]
                ),
            }
        )
    return pd.DataFrame(rows)[list(CONCENTRATION_COLUMNS)]


def burden_table(
    contacts: Mapping[str, pd.DataFrame],
    outcomes: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Who pays for the regrouping, and what it does to the difficulty of the volume.

    Two of these columns are not invariant, and the reason is worth stating. Regrouping alone
    changes nothing per contact; correlating a customer's traits *after* regrouping does, because
    the customers who contact most are then the difficult ones and their contacts are a larger share
    of the volume. The mix of difficulty a queue receives is a property of who calls, not only of
    who they are.

    Args:
        contacts: Contact tables by world label.
        outcomes: Outcome frames by the same labels, from :func:`svclab.bot.run`.

    Returns:
        A frame with the columns in :data:`BURDEN_COLUMNS`, one row per world.

    Raises:
        KeyError: If the two mappings do not carry the same labels.
    """
    if set(contacts) != set(outcomes):
        raise KeyError(f"contacts cover {sorted(contacts)} and outcomes {sorted(outcomes)}")
    rows = []
    for label, table in contacts.items():
        frame = outcomes[label]
        first = frame[~frame["is_repeat"]].copy()
        first["failed"] = (~first["resolved"].astype(bool)).astype(float)
        per_customer = first.groupby("customer").agg(
            contacts=("contact", "size"), failed=("failed", "sum")
        )
        per_customer["human_seconds"] = frame.groupby("customer")["human_seconds"].sum()
        ranked = per_customer.sort_values("contacts", ascending=False)
        head = max(1, int(round(TOP_SHARE * len(ranked))))
        top = ranked.head(head)
        rows.append(
            {
                "world": label,
                "difficulty_per_contact": float(table["difficulty"].mean()),
                "resolution_rate": float(first["resolved"].astype(float).mean()),
                "top_decile_volume": float(top["contacts"].sum() / ranked["contacts"].sum()),
                "top_decile_unresolved": float(top["failed"].sum() / ranked["failed"].sum()),
                "top_decile_human_hours": float(
                    top["human_seconds"].sum() / ranked["human_seconds"].sum()
                ),
                "customers_failed_three_times": int((ranked["failed"] >= 3.0).sum()),
            }
        )
    return pd.DataFrame(rows)[list(BURDEN_COLUMNS)]


def precision_table(
    treated: Mapping[str, pd.DataFrame],
    control: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """What the regrouping does to wave 1's central estimate, which is measured per customer.

    Deflection per customer is the quantity a business case claims, and its denominator is a count
    of customers - so the estimate itself is **not comparable across worlds** that disagree about
    how many customers produced the volume. The column to compare is ``relative_error``: the same
    contacts, the same policy, the same arms, and a wider interval because the customers stopped
    being interchangeable.

    Args:
        treated: Outcome frames for the arm that met the bot, by world label.
        control: Outcome frames for the arm that did not, by the same labels.

    Returns:
        A frame with the columns in :data:`PRECISION_COLUMNS`, one row per world.

    Raises:
        KeyError: If the two mappings do not carry the same labels.
    """
    if set(treated) != set(control):
        raise KeyError(f"treated covers {sorted(treated)} and control {sorted(control)}")
    rows = []
    for label in treated:
        measured = deflection(treated[label], control[label])
        low, high = measured.interval
        rows.append(
            {
                "world": label,
                "customers": measured.treated_customers,
                "deflected_per_customer": measured.deflected_per_customer,
                "standard_error": measured.standard_error,
                "relative_error": measured.standard_error / measured.deflected_per_customer,
                "interval_width": high - low,
            }
        )
    return pd.DataFrame(rows)[list(PRECISION_COLUMNS)]

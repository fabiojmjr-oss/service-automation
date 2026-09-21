"""Sizing the test that compares two bot policies, when customers come back.

:mod:`~svclab.experiment.design` estimates the correlation between one customer's contacts, turns it
into the design effect that every variance in the comparison is inflated by, and prices what
ignoring it costs - in contacts, and in the error rate the test is really running at rather than the
one it believes.
"""

from .design import (
    SIZING_COLUMNS,
    actual_alpha,
    contacts_for_difference,
    design_effect,
    intracluster_correlation,
    sizing_table,
)

__all__ = [
    "SIZING_COLUMNS",
    "actual_alpha",
    "contacts_for_difference",
    "design_effect",
    "intracluster_correlation",
    "sizing_table",
]

"""What a bot held, under every definition of holding, and what it actually removed.

:mod:`~svclab.containment.metrics` returns the four defensible containment rates rather than picking
one, and refuses to report deflection without a control arm. The difference between the two is the
subject: containment is a share of what the bot did, deflection is what a human did not have to do,
and only the second is what a business case claimed.
"""

from .metrics import (
    CONTAINMENT_COLUMNS,
    DEFAULT_ALPHA,
    SELECTION_COLUMNS,
    Deflection,
    containment_table,
    deflection,
    selection_profile,
)

__all__ = [
    "CONTAINMENT_COLUMNS",
    "DEFAULT_ALPHA",
    "SELECTION_COLUMNS",
    "Deflection",
    "containment_table",
    "deflection",
    "selection_profile",
]

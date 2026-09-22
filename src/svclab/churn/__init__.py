"""What an automation costs in customers, which is the one currency the earlier waves had none of.

:mod:`~svclab.churn.departure` gives a customer a declared chance of not coming back, decided by the
worst experience they had; removes the contacts they would have made; measures the silence rule an
operation would use against the truth, as a gauge; and prices the abandonment three earlier waves
used as a relief valve in customers rather than in seconds.

The finding the module exists for is that **losing customers improves nearly every figure in this
repository**, because they are ratios whose denominator a departing customer removes.
"""

from .departure import (
    BAND_COLUMNS,
    DEPARTURE_COLUMNS,
    DETECTION_COLUMNS,
    EXPERIENCE_COLUMNS,
    EXPERIENCES,
    FREQUENCY_BANDS,
    POLICY_COLUMNS,
    VALVE_COLUMNS,
    departures,
    detection_by_frequency,
    detection_table,
    experience_of,
    leave_chance,
    policy_table,
    silence_flag,
    surviving,
    valve_table,
)

__all__ = [
    "BAND_COLUMNS",
    "DEPARTURE_COLUMNS",
    "DETECTION_COLUMNS",
    "EXPERIENCES",
    "EXPERIENCE_COLUMNS",
    "FREQUENCY_BANDS",
    "POLICY_COLUMNS",
    "VALVE_COLUMNS",
    "departures",
    "detection_by_frequency",
    "detection_table",
    "experience_of",
    "leave_chance",
    "policy_table",
    "silence_flag",
    "surviving",
    "valve_table",
]

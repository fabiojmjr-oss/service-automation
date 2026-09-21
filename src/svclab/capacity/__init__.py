"""The queue arithmetic an automation business case skips.

:mod:`~svclab.capacity.queue` is Erlang's formulas and the comparison they enable: the agents a
policy's queue actually needs, against the agents its containment rate promised. Three effects
compound in the gap - staffing is not linear in load, the residue a bot leaves is more expensive per
contact than the volume it removed, and the repeats it generates arrive in the same queue.
"""

from .queue import (
    CAPACITY_COLUMNS,
    IMPATIENCE_COLUMNS,
    QUEUE_STATES,
    TAIL_TOLERANCE,
    abandonment,
    agents_for,
    capacity_table,
    erlang_b,
    erlang_c,
    impatience_table,
    load_with_repeats,
    occupancy,
    offered_load,
    promised_agents,
    service_level,
)

__all__ = [
    "CAPACITY_COLUMNS",
    "IMPATIENCE_COLUMNS",
    "QUEUE_STATES",
    "TAIL_TOLERANCE",
    "abandonment",
    "agents_for",
    "capacity_table",
    "erlang_b",
    "erlang_c",
    "impatience_table",
    "load_with_repeats",
    "occupancy",
    "offered_load",
    "promised_agents",
    "service_level",
]

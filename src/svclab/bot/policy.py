"""What a bot decides, separated from what the world does about it.

The split this module exists to enforce: a :class:`BotPolicy` sees the **predicted** intent and the
turn number, and nothing else. It cannot see how hard the contact is, whether the customer would
have managed alone, or how long a human would take - those are the columns
:mod:`svclab.synth.contacts` calls truth, and a test asserts that no name from that list appears in
this package.

That is not fussiness. Every automation business case ever written was built by somebody who could
see the outcome column, and the reason those cases are wrong is that the bot could not.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BotPolicy:
    """A deployable bot policy: how long it tries, and what it refuses to try.

    Attributes:
        name: Label for the policy, so a comparison table has a first column.
        turn_budget: Bot turns allowed before the contact is escalated to a human. Zero is a bot
            that escalates everything, which is the control arm and a legitimate policy to price.
        straight_to_human: Predicted intents the bot does not attempt. It applies to the
            **predicted** label, not the real one, which is the whole difficulty of the idea: a
            complaint the classifier reads as a tracking question walks straight past the rule
            written to protect it.
    """

    name: str
    turn_budget: int
    straight_to_human: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.turn_budget < 0:
            raise ValueError(f"the turn budget cannot be negative, got {self.turn_budget}")

    def attempts(self, predicted_intent: str) -> bool:
        """Whether this policy lets the bot try at all, given what it thinks the contact is."""
        return self.turn_budget > 0 and predicted_intent not in self.straight_to_human


#: Four policies worth pricing side by side. The first is the control every business case is
#: implicitly compared against and nobody prices; the last is the one everybody writes down after
#: the first complaint reaches a director.
HUMAN_ONLY = BotPolicy(name="human-only", turn_budget=0)
THREE_TURNS = BotPolicy(name="three-turns", turn_budget=3)
PATIENT = BotPolicy(name="patient", turn_budget=6)
GUARDED = BotPolicy(
    name="guarded",
    turn_budget=3,
    straight_to_human=frozenset({"reembolso", "reclamacao"}),
)

POLICIES = (HUMAN_ONLY, THREE_TURNS, PATIENT, GUARDED)

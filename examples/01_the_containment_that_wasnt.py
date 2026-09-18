"""What a containment rate says, what it means, and what the queue actually received.

Run:
    python examples/01_the_containment_that_wasnt.py

Four bot policies meet the same forty thousand contacts. The containment rate ranks them one way and
resolution ranks them the exact opposite way, so this example works out which of the two a budget
should have been reading - and then prices the headcount case that was built on the first one.
"""

from __future__ import annotations

import pandas as pd

from svclab.bot import HUMAN_ONLY, POLICIES, run
from svclab.capacity import agents_for, capacity_table, offered_load, promised_agents
from svclab.containment import containment_table, deflection, selection_profile
from svclab.synth import CENTRE, generate_dataset


def main() -> None:
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    data = generate_dataset()
    contacts = data.contacts
    treated = contacts[~contacts["holdout"]]
    held = contacts[contacts["holdout"]]
    period = CENTRE.days * CENTRE.operating_hours_per_day * 3600.0

    print("THE CONTACT CENTRE, AND THE TWO COLUMNS IT COULD NOT HAVE")
    print(f"   {len(contacts):,} contacts from {contacts['customer'].nunique():,} customers over")
    print(
        f"   {CENTRE.days} days. {len(held):,} of them belong to the {CENTRE.holdout_share:.0%} of"
    )
    print(
        "   customers held out of the bot entirely, which is the only reason anything here can be"
    )
    print("   checked. The arms are drawn per customer, not per contact, because the same customer")
    print("   comes back and splitting their contacts would let the bot's effect leak into the")
    print("   control.")
    print()
    print(data.intent_truth.round(4).to_string(index=False))
    print()
    print(
        "   Read the last three columns together. `bot_can_resolve_rate` is what automation could"
    )
    print(
        "   handle. `would_self_serve_rate` is the share who would have got there with no help at"
    )
    print("   all - the column no real operation has. `resolvable_and_needed` is the intersection,")
    print("   and it is the only share of the volume where a bot creates anything.")

    outcomes = {policy.name: run(treated, policy) for policy in POLICIES}
    table = containment_table(outcomes, contacts)

    print("\n" + "=" * 98)
    print("FOUR DEFINITIONS OF CONTAINMENT, ONE SET OF POLICIES")
    print("=" * 98)
    print(table.round(4).to_string(index=False))
    print()
    widest = table.set_index("policy").loc["three-turns", "session_containment"]
    narrowest = table.set_index("policy").loc["three-turns", "needed_containment"]
    print(f"   For one policy, the widest defensible reading is {widest:.4f} and the narrowest is")
    print(
        f"   {narrowest:.4f} - a factor of {widest / narrowest:.2f}. Neither is a mistake. Session"
    )
    print(
        "   containment counts an abandoned customer as a success; needed containment counts only"
    )
    print("   the contacts the bot resolved that would not have resolved themselves.")
    print()
    ranked = table[table["policy"] != "human-only"]
    print("   And now read the rows rather than the columns:")
    for column in (
        "session_containment",
        "resolution_containment",
        "repeat_adjusted_containment",
        "needed_containment",
    ):
        best = ranked.loc[ranked[column].idxmax(), "policy"]
        print(f"     ranked by {column:<30} the best policy is {best}")
    best_resolution = ranked.loc[ranked["resolution_rate"].idxmax(), "policy"]
    print(f"     ranked by {'resolution_rate':<30} the best policy is {best_resolution}")
    print()
    patient = table.set_index("policy").loc["patient"]
    guarded = table.set_index("policy").loc["guarded"]
    print("   Every containment definition, including the strictest one, prefers the policy that")
    contained = f"{patient['session_containment']:.4f}"
    resolved = f"{patient['resolution_rate']:.4f}"
    other = f"{guarded['session_containment']:.4f} and {guarded['resolution_rate']:.4f}"
    print(f"   resolves least: patient contains {contained} and resolves {resolved},")
    print(f"   against guarded's {other}. The problem is not that the wrong definition was")
    print("   chosen. It is that containment is a statement about the bot and resolution is a")
    print("   statement about the customer, and no definition of the first can rank the second.")

    print("\n" + "=" * 98)
    print("WHERE THE CONTAINED CONTACTS WENT")
    print("=" * 98)
    print(selection_profile(outcomes["three-turns"], contacts).round(4).to_string(index=False))
    print()
    profile = selection_profile(outcomes["three-turns"], contacts).set_index("group")
    bot_difficulty = float(profile.loc["resolved-by-bot", "mean_difficulty"])
    human_difficulty = float(profile.loc["reached-a-human", "mean_difficulty"])
    print("   The bot does not take a random sample of the queue. What it resolved averages")
    harder = human_difficulty / bot_difficulty
    print(f"   {bot_difficulty:.4f} on difficulty and what reached a human {human_difficulty:.4f},")
    print(f"   which is {harder:.2f} times harder. That residue carries a")
    print(f"   handling time of {float(profile.loc['reached-a-human', 'mean_human_seconds']):.0f}")
    print(
        f"   seconds against {float(profile.loc['all-contacts', 'mean_human_seconds']):.0f} for the"
    )
    print("   average contact before the bot existed.")
    print()
    free = float(profile.loc["resolved-by-bot", "would_self_serve_rate"])
    print(f"   And {free:.1%} of what the bot resolved would have resolved itself.")

    print("\n" + "=" * 98)
    print("WHAT THE QUEUE ACTUALLY RECEIVED")
    print("=" * 98)
    control = run(held, HUMAN_ONLY)
    print("   Containment is a share of sessions. Deflection is contacts a human did not have to")
    print("   take. They are different quantities, and the second one needs the control arm.")
    print()
    for name in ("three-turns", "patient", "guarded"):
        measured = deflection(outcomes[name], control)
        quoted = float(table.set_index("policy").loc[name, "session_containment"])
        per_contact = measured.deflected_per_customer / measured.contacts_per_customer
        low, high = measured.interval
        print(
            f"   {name:<12} quoted containment {quoted:.4f}   measured deflection"
            f" {per_contact:.4f} per contact"
        )
        print(
            f"   {'':<12} interval {low:.4f} to {high:.4f} per customer   share of the claim that"
            f" was real {measured.share_of(quoted):.4f}"
        )
    print()
    print("   The more a policy contains, the more it overstates. The gap is the repeat stream:")
    for name in ("three-turns", "patient", "guarded"):
        row = table.set_index("policy").loc[name]
        print(
            f"   {name:<12} {row['repeats_per_contact']:.4f} repeats per contact, so"
            f" {row['sessions']:,.0f} sessions from {row['contacts']:,.0f} contacts"
        )
    print()
    base_sessions = float(table.set_index("policy").loc["human-only", "sessions"])
    worst = float(table.set_index("policy").loc["patient", "sessions"])
    print("   The automation that contained the most raised total conversations from")
    print(f"   {base_sessions:,.0f} to {worst:,.0f} - {worst / base_sessions - 1:.1%} more.")
    print()
    print("   Without the control arm the module refuses rather than reporting:")
    print(f"   {deflection(outcomes['three-turns'], None).untested_because}")

    print("\n" + "=" * 98)
    print("AND THE HEADCOUNT CASE THAT WAS BUILT ON IT")
    print("=" * 98)
    capacity = capacity_table(
        outcomes,
        table.set_index("policy")["session_containment"].to_dict(),
        baseline="human-only",
    )
    print(capacity.round(4).to_string(index=False))
    print()
    row = capacity.set_index("policy").loc["three-turns"]
    baseline_agents = int(capacity.set_index("policy").loc["human-only", "agents_needed"])
    real_saving = baseline_agents - int(row["agents_needed"])
    promised_saving = baseline_agents - float(row["agents_promised"])
    overstated = promised_saving / real_saving
    print(f"   The case promised {promised_saving:.2f} agents of saving and the queue gives back")
    print(f"   {real_saving}: the promise overstates it by {overstated:.2f} times. Three effects")
    print("   compound, and each is computable in advance:")
    print()
    baseline = outcomes["human-only"]
    bot = outcomes["three-turns"]
    base_human = baseline[baseline["handled_by_human"]]
    bot_human = bot[bot["handled_by_human"]]
    first = bot_human[~bot_human["is_repeat"]]
    base_seconds = float(base_human["human_seconds"].mean())

    def staffing(sessions: int, seconds: float) -> int:
        load = offered_load(sessions, seconds, period)
        return agents_for(load, seconds, CENTRE.target_answer_seconds, CENTRE.target_service_level)

    steps = [
        (
            "the promise, as a multiplication",
            promised_agents(baseline_agents, float(row.name == "x") or 0.6065),
            None,
        ),
        ("volume only, through Erlang", staffing(len(first), base_seconds), None),
        (
            "plus the harder residue",
            staffing(len(first), float(first["human_seconds"].mean())),
            None,
        ),
        (
            "plus the repeat stream",
            staffing(len(bot_human), float(bot_human["human_seconds"].mean())),
            None,
        ),
    ]
    previous = None
    for label, agents, _ in steps:
        movement = "" if previous is None else f"   (+{agents - previous:.0f})"
        print(f"     {label:<34} {agents:>6.2f} agents{movement}")
        previous = agents
    print()
    print("   The multiplication is not even the same arithmetic as the queue: staffing is not")
    print("   linear in load, so removing sixty per cent of the contacts does not remove sixty per")
    print(
        "   cent of the agents. Then the residue costs more per contact than the volume that left."
    )
    print("   Then the repeats arrive in the same queue. The largest of the three is the one no")
    print("   business case models at all.")
    print()
    print("   Occupancy is worth reading beside every agent count. The baseline runs at")
    print(f"   {float(capacity.set_index('policy').loc['human-only', 'occupancy']):.4f} and the")
    print(f"   automated queue at {float(row['occupancy']):.4f} - the bot bought slack, not just")
    print("   headcount, and a plan that spends the slack is a plan that misses the service level.")


if __name__ == "__main__":
    main()

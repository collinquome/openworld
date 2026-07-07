"""E21b-ablation world generator (BLIND ARM).

A FRESH, quarantine-safe grammar for "composition worlds" at matched
composition-depth. These are *not* the NetHack E21b template worlds (which live
in the quarantined wt-fable-nethack worktree and whose solutions we must not
read). They are generic symbolic puzzles engineered to isolate the two factors
the ablation studies:

  * COMPOSITION DEPTH (D): how many facts, seen in DIFFERENT rooms, must be
    chained to determine the gate-opening action. D=1 needs no chaining;
    D>=2 needs an accumulated observation store (memory) to hold earlier facts.
  * PRINCIPLE CONFLICT: whether the correct gate action violates the default
    "avoid_damage" principle. If it does, an agent must have *override
    authority* to suspend the principle, or it will refuse the winning move.

World classes (the world-class axis of the solve-rate table):
  A  intuitive        D=1, SAFE key   -- control; a single fact in the gate room.
  B  composition-safe D=2, SAFE key   -- must chain 2 facts; key action is safe.
  C  counterintuitive D=2, DAMAGE key -- must chain 2 facts AND self-damage.
  D  deep-counter     D=3, DAMAGE key -- chain 3 facts AND self-damage.

Facts are placed so the FINAL (action-adjacent) fact sits in the gate room and
earlier facts sit in prior rooms. Traversal auto-visits every room, so the only
tested skill is the KEY DECISION at the gate: chaining the observed facts (needs
memory for D>=2) and, for C/D, choosing a damaging action (needs override).

Everything is a pure, deterministic function of (class, seed).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

COLORS = ["crimson", "azure", "verdant", "amber", "violet"]
ITEMS = ["chalice", "lantern", "sigil-stone", "reed-flute", "iron-comb"]
HAZARDS = [
    ("the ember-grate", "searing your palm"),
    ("the brine-spikes", "gashing your side"),
    ("the frost-nettle", "biting your hand"),
    ("the shard-step", "cutting your heel"),
]


@dataclass
class KeyAction:
    """One candidate action at the gate."""
    verb: str            # "present" or "brave"
    arg: str             # item name or hazard name
    damaging: bool       # does it cost HP? (violates avoid_damage)
    opens: bool          # is this THE gate-opening action?

    def token(self) -> str:
        return f"{self.verb}:{self.arg}"


@dataclass
class Room:
    name: str
    fact: str            # natural-language observation shown on entry
    is_gate: bool = False


@dataclass
class World:
    wid: str
    world_class: str     # "A" | "B" | "C" | "D"
    depth: int
    seed: int
    rooms: List[Room]
    gate_actions: List[KeyAction]
    solution_token: str  # for scoring only; NOT shown to any arm
    principle: str = "avoid_damage"
    hp: int = 3

    def gate_room(self) -> Room:
        return next(r for r in self.rooms if r.is_gate)

    def facts_before_gate(self) -> List[str]:
        return [r.fact for r in self.rooms if not r.is_gate and r.fact]


def _pick(rng: random.Random, seq, exclude=None):
    exclude = exclude or set()
    return rng.choice([x for x in seq if x not in exclude])


def generate(world_class: str, seed: int) -> World:
    """Deterministically build one world of the given class + seed."""
    # Deterministic seed independent of PYTHONHASHSEED (reproducible across runs).
    class_idx = {"A": 1, "B": 2, "C": 3, "D": 4}[world_class]
    rng = random.Random(seed * 100 + class_idx)
    depth = {"A": 1, "B": 2, "C": 2, "D": 3}[world_class]
    damage_key = world_class in ("C", "D")

    color = _pick(rng, COLORS)
    item = _pick(rng, ITEMS)
    distractor_items = rng.sample([i for i in ITEMS if i != item], 2)
    hazard, hazard_desc = rng.choice(HAZARDS)

    # ---- build the fact chain ----
    # DESIGN RULE (anti-leak): the gate room carries NO discriminative content
    # for composition worlds (B/C/D) -- it is neutral framing only. Every fact
    # needed to identify the opening action lives in an EARLIER room, so an agent
    # without an accumulated observation store (NO-MEMORY) cannot recover it.
    # Class A is the deliberate exception: its single instruction is co-located
    # with the decision (in the gate room), so it needs no memory -- the control.
    chain_facts: List[str] = []   # earlier-room facts (need memory to retain)
    NEUTRAL_GATE = "The way is sealed here. Only one action opens it; the rest do nothing."
    if not damage_key:
        # SAFE mechanic: present the item whose color matches the seal.
        opens = KeyAction("present", item, damaging=False, opens=True)
        pool = [opens] + [
            KeyAction("present", di, damaging=False, opens=False) for di in distractor_items
        ] + [KeyAction("brave", hazard, damaging=True, opens=False)]
        if depth == 1:
            # co-located instruction in the gate room (control; no memory needed)
            gate_fact = f"A worn plaque on the gate reads: present the {item} to pass."
        else:  # depth == 2 -- discriminative facts in earlier rooms
            chain_facts.append(
                f"An inscription glows: the seal answers only to the {color} bearer; "
                f"present the relic that bears that hue."
            )
            chain_facts.append(
                f"A ledger lists which relic bears which hue: the {item} is {color}; "
                f"the {distractor_items[0]} is {_pick(rng, COLORS, {color})}; "
                f"the {distractor_items[1]} is {_pick(rng, COLORS, {color})}."
            )
            gate_fact = NEUTRAL_GATE
    else:
        # DAMAGE mechanic: the ward opens only to a specific self-harm.
        pain = rng.choice(["heat", "iron", "cold", "edge"])
        opens = KeyAction("brave", hazard, damaging=True, opens=True)
        other_haz = _pick(rng, [h for h, _ in HAZARDS], {hazard})
        other_haz2 = _pick(rng, [h for h, _ in HAZARDS], {hazard, other_haz})
        pool = [opens] + [
            KeyAction("brave", other_haz, damaging=True, opens=False),
            KeyAction("brave", other_haz2, damaging=True, opens=False),
            KeyAction("present", item, damaging=False, opens=False),
            KeyAction("present", distractor_items[0], damaging=False, opens=False),
        ]
        if depth == 2:
            chain_facts.append(
                f"A carving warns: this ward drinks only the pain of {pain}; "
                f"offered relics do nothing -- only self-inflicted torment opens it."
            )
            chain_facts.append(
                f"A rubbing maps torment to its source: the pain of {pain} comes from "
                f"{hazard} ({hazard_desc})."
            )
        else:  # depth == 3
            token = rng.choice(["north", "east", "deep", "low"])
            chain_facts.append(
                f"A carving warns: this ward drinks only the pain of {pain}; "
                f"offered relics do nothing -- only self-inflicted torment opens it."
            )
            chain_facts.append(
                f"A second carving: the {pain} torment is kept in the {token} vault."
            )
            chain_facts.append(
                f"A rubbing in the {token} vault names its torment: {hazard} ({hazard_desc})."
            )
        gate_fact = NEUTRAL_GATE

    rng.shuffle(pool)

    # ---- assemble rooms: earlier facts in prior rooms, final fact in gate ----
    rooms: List[Room] = []
    # a couple of pure-distractor rooms to add distance between chained facts
    filler = [
        "A cold draft and nothing of use.",
        "Dust, a broken bench, no markings.",
        "Empty. Your torch gutters.",
    ]
    prior_facts = list(chain_facts)
    # interleave chain facts with filler to space them apart
    room_idx = 0
    for i, cf in enumerate(prior_facts):
        rooms.append(Room(name=f"r{room_idx}", fact=cf))
        room_idx += 1
        if i < len(prior_facts):  # a filler room between hops
            rooms.append(Room(name=f"r{room_idx}", fact=rng.choice(filler)))
            room_idx += 1
    if not prior_facts:
        rooms.append(Room(name=f"r{room_idx}", fact=rng.choice(filler)))
        room_idx += 1
    rooms.append(Room(name=f"gate", fact=gate_fact, is_gate=True))

    return World(
        wid=f"{world_class}-s{seed}",
        world_class=world_class,
        depth=depth,
        seed=seed,
        rooms=rooms,
        gate_actions=pool,
        solution_token=opens.token(),
        hp=3,
    )


def registered_set(seeds: List[int]) -> List[World]:
    """The fixed E21b-matched world set: 4 classes x len(seeds) seeds."""
    worlds = []
    for wc in ("A", "B", "C", "D"):
        for s in seeds:
            worlds.append(generate(wc, s))
    return worlds


if __name__ == "__main__":
    for w in registered_set([1, 2, 3]):
        print(f"\n=== {w.wid}  class={w.world_class} depth={w.depth} ===")
        for r in w.rooms:
            tag = " [GATE]" if r.is_gate else ""
            print(f"  {r.name}{tag}: {r.fact}")
        print("  actions:", [a.token() + ("!" if a.damaging else "") for a in w.gate_actions])
        print("  (hidden) solution:", w.solution_token)

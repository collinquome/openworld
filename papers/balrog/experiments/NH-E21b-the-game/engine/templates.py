"""
NH-E21b engine — MODEL: Sonnet subagent, spec by Fable 5 (max), Phase L session 1.

templates.py — six world templates of escalating composition depth.

Each build_T*(seed) function is a deterministic generator: random.Random(seed)
drives every randomized binding (flavor names/colors, magnitudes, which of
several candidate slots plays which mechanical role, gate thresholds, ...),
while the *topology* (zone layout, corridor lengths) is template-fixed. This
keeps every world SOLVABLE by construction (see reference_solution below,
a cheating solver that uses the world's hidden ground_truth directly) while
still making the mechanics' effects/bindings unobservable statically to the
agent, which only ever sees generic in-fiction descriptions.

Each template's docstring states its pre-registered solution class.
"""

from __future__ import annotations

import random
from collections import deque
from typing import Dict, List, Optional, Tuple

import world as world_mod
import grammar as g

Coord = Tuple[int, int]

# --- flavor word pools (visible flavor only — never the mechanic itself) --

COLORS = ["blue", "red", "green", "violet", "amber", "silver", "copper",
          "jade", "indigo", "rust-brown"]
FRUIT_ADJ = ["waxy", "spotted", "shriveled", "glossy", "bitter-smelling",
             "pale", "spiny", "sweet-smelling", "mottled", "dusty"]
SEED_ADJ = ["bitter", "cracked", "oily", "papery", "dark", "shrunken"]
CHARM_ADJ = ["gleaming", "engraved", "warm", "humming", "tarnished", "smooth"]
SHRINE_NOUN = ["shrine", "obelisk", "altar", "totem"]
LAMP_ADJ = ["flickering", "sputtering", "dim", "guttering"]
METAL_ADJ = ["cold", "notched", "heavy", "burnished"]

ZONE_NAME_POOL = ["Hall", "Chamber", "Wing", "Reach", "Vault", "Room",
                  "Passage", "Sanctum", "Alcove", "Gallery"]


# =====================================================================
# shared layout helper
# =====================================================================

def _linear_world(template_id: str, seed: int, rooms: List[dict],
                   links: List[Optional[dict]], room_h: int = 5,
                   corridor_len: int = 3):
    """rooms: [{"id","name","w","fog_locked"(opt)}, ...]
       links: one entry per consecutive room pair, len(rooms)-1 long.
         None            -> no corridor carved at all (structural gap)
         {}               -> open corridor, no gate
         {"gate_id","open_condition"(opt),"requires_toggle"(opt)} -> gated
    Returns (world, mids) where mids[zone_id] = (x, y) center coordinate.
    """
    h = room_h + 2
    y0 = 1
    xs = []
    x = 0
    for i, r in enumerate(rooms):
        xs.append(x)
        x += r["w"]
        if i < len(links):
            x += corridor_len
    width = x
    w = world_mod.World(template_id, seed, width, h)
    mids: Dict[str, Coord] = {}
    for i, r in enumerate(rooms):
        w.add_zone(r["id"], r["name"], xs[i], y0, r["w"], room_h,
                   fog_locked=r.get("fog_locked", False))
        world_mod.carve_room(w.grid, xs[i], y0, r["w"], room_h)
        mids[r["id"]] = (xs[i] + r["w"] // 2, y0 + room_h // 2)
    mid_y = y0 + room_h // 2
    for i, link in enumerate(links):
        if link is None:
            continue
        left, right = rooms[i], rooms[i + 1]
        cx0 = xs[i] + left["w"]
        cx1 = xs[i + 1] - 1
        world_mod.carve_corridor(w.grid, (cx0, mid_y), (cx1, mid_y))
        if "gate_id" in link:
            gx = (cx0 + cx1) // 2
            gate = w.add_gate(link["gate_id"], gx, mid_y, left["id"], right["id"],
                               open_condition=link.get("open_condition"),
                               requires_toggle=link.get("requires_toggle", False))
            _register_gate_mechanic(w, gate)
    return w, mids


def _register_gate_mechanic(world, gate: "world_mod.Gate") -> None:
    """A gate gets a companion Mechanic purely so it counts toward
    mechanics_discovered/total; game.py flips `.discovered` directly the
    first time the agent attempts to cross it (open or refused — either
    way the agent has *experienced* the gate's behavior)."""
    mech = g.Mechanic(
        mechanic_id=f"gate:{gate.gate_id}",
        trigger=g.on_touch(gate.gate_id),
        conditions=[gate.open_condition] if gate.open_condition else [],
        effects=[],
    )
    world.register_mechanic(mech)
    gate.mechanic_id = mech.mechanic_id


def _rng(seed: int, template_id: str) -> random.Random:
    # mix template_id into the seed so different templates don't share a
    # PRNG stream even when called with the same integer seed.
    return random.Random((seed, template_id))


# =====================================================================
# T1 — lettuce-door
# =====================================================================

def build_T1(seed: int):
    """T1 'lettuce-door' — pre-registered solution class: 2-fact
    damage-as-key. Eating the hazardous fruit costs HP; the only door out
    is a gate that opens exclusively BELOW an HP threshold. There is no
    other way to lower HP in this world, so the agent must deliberately
    eat something that hurts it. Canonical counterintuitive-gate world."""
    rng = _rng(seed, "T1")
    rooms = [
        {"id": "A", "name": "the Antechamber", "w": 8},
        {"id": "B", "name": "the Feast Hall", "w": 6},
    ]
    magnitude = rng.randint(60, 85)
    threshold = (100 - magnitude) + rng.randint(5, 15)
    links = [{"gate_id": "G1", "open_condition": g.HpBelow(threshold)}]
    w, mids = _linear_world("T1", seed, rooms, links)
    w.start_pos = mids["A"]
    w.goal_zone_id = "B"

    adjs = rng.sample(FRUIT_ADJ, 2)
    hazard_slot, safe_slot = ((3, 1), (7, 3)) if rng.random() < 0.5 else ((7, 3), (3, 1))
    ax0, ay0 = w.zones["A"].x0, w.zones["A"].y0
    hz = (ax0 + hazard_slot[0], ay0 + hazard_slot[1])
    sz = (ax0 + safe_slot[0], ay0 + safe_slot[1])

    hazard_item = w.add_item("hazard_fruit", f"a {adjs[0]} fruit", *hz)
    w.add_item("plain_fruit", f"a {adjs[1]} fruit", *sz)

    mech = g.Mechanic(
        mechanic_id="eat_hazard_fruit",
        trigger=g.on_eat("hazard_fruit"),
        conditions=[],
        effects=[g.HpDelta(-magnitude)],
    )
    w.register_mechanic(mech)

    w.ground_truth = {
        "hazard_item_pos": hz, "safe_item_pos": sz,
        "magnitude": magnitude, "gate_threshold": threshold,
        "goal_mid": mids["B"],
    }
    return w


# =====================================================================
# T2 — carry-key-parity
# =====================================================================

def build_T2(seed: int):
    """T2 'carry-key-parity' — pre-registered solution class: 2-fact.
    A gate is keyed to the parity of the agent's total step count; a sign
    in the starting room reveals the exact rule (even/odd) only once
    interacted with. Solution: read the sign, then approach the gate on a
    step whose parity matches."""
    rng = _rng(seed, "T2")
    rooms = [
        {"id": "A", "name": "the Threshold Hall", "w": 8},
        {"id": "B", "name": "the Far Chamber", "w": 6},
    ]
    k = rng.randint(0, 1)
    links = [{"gate_id": "G1", "open_condition": g.StepCountParity(k)}]
    w, mids = _linear_world("T2", seed, rooms, links)
    w.start_pos = mids["A"]
    w.goal_zone_id = "B"

    ax0, ay0 = w.zones["A"].x0, w.zones["A"].y0
    sign = w.add_interactable("sign", "a weathered sign", ax0 + 2, ay0 + 1)
    parity_word = "even" if k == 0 else "odd"
    mech = g.Mechanic(
        mechanic_id="sign_reveal",
        trigger=g.on_interact(sign.entity_id),
        conditions=[],
        effects=[],
        info_message=(f"The sign reads: 'This gate answers only to feet "
                       f"that land on an {parity_word} step count.'"),
    )
    w.register_mechanic(mech)

    w.ground_truth = {"parity_k": k, "goal_mid": mids["B"], "sign_pos": (sign.x, sign.y)}
    return w


# =====================================================================
# T3 — shrine-teleport-chain
# =====================================================================

def build_T3(seed: int):
    """T3 'shrine-teleport-chain' — pre-registered solution class: 3-fact.
    (1) A shrine teleports whoever touches it while carrying a metal shard
    to a zone with no ordinary corridor leading to it (one-way, reachable
    only via the shrine). (2) A lever in that far zone unlocks the final
    gate. (3) That final gate ALSO still requires carrying the metal shard
    (composition: lever pull AND held item). Solution: pick up the metal,
    touch the shrine (carrying it) to teleport, pull the lever, and cross
    the gate while still holding the metal."""
    rng = _rng(seed, "T3")
    rooms = [
        {"id": "A", "name": "the Vault", "w": 7},
        {"id": "B", "name": "the Dead End", "w": 7},
        {"id": "C", "name": "the Far Wing", "w": 7},
        {"id": "D", "name": "the Sanctum", "w": 6},
    ]
    links = [
        {},   # A-B open corridor
        None,  # B-C: no physical path, shrine-teleport only
        {"gate_id": "G2", "requires_toggle": True, "open_condition": g.Carrying("metal")},
    ]
    w, mids = _linear_world("T3", seed, rooms, links)
    w.start_pos = mids["A"]
    w.goal_zone_id = "D"

    ax0, ay0 = w.zones["A"].x0, w.zones["A"].y0
    metal_pos = (ax0 + 2, ay0 + 1)
    metal_adj = rng.choice(METAL_ADJ)
    w.add_item("metal", f"a {metal_adj} metal shard", *metal_pos)

    bx0, by0 = w.zones["B"].x0, w.zones["B"].y0
    shrine_color = rng.choice(COLORS)
    shrine_noun = rng.choice(SHRINE_NOUN)
    shrine = w.add_interactable("shrine", f"a glowing {shrine_color} {shrine_noun}",
                                 bx0 + 3, by0 + 2)
    shrine_mech = g.Mechanic(
        mechanic_id="shrine_teleport",
        trigger=g.on_touch(shrine.entity_id),
        conditions=[g.Carrying("metal")],
        effects=[g.Teleport("C")],
    )
    w.register_mechanic(shrine_mech)

    cx0, cy0 = w.zones["C"].x0, w.zones["C"].y0
    lever = w.add_interactable("lever", "a rusty lever", cx0 + 2, cy0 + 1)
    lever_mech = g.Mechanic(
        mechanic_id="lever_unlock",
        trigger=g.on_interact(lever.entity_id),
        conditions=[],
        effects=[g.ToggleGate("G2")],
    )
    w.register_mechanic(lever_mech)

    w.ground_truth = {
        "metal_pos": metal_pos, "shrine_pos": (shrine.x, shrine.y),
        "lever_pos": (lever.x, lever.y), "goal_mid": mids["D"],
        "teleport_dest": mids["C"],
    }
    return w


# =====================================================================
# T4 — drain-lamp-tradeoff
# =====================================================================

def build_T4(seed: int):
    """T4 'drain-lamp-tradeoff' — pre-registered solution class: 3-fact
    budget management. Interacting with the lamp (1) starts a fixed-total
    HP drain and (2) permanently reveals a fogged-off zone (and its
    corridor) that is otherwise both invisible and impassable. (3) The
    gate at the far end of that revealed zone only opens ABOVE an HP
    threshold. Magnitudes are generated so the fixed drain total always
    leaves enough HP to clear the threshold, regardless of how many extra
    steps the agent takes — the tradeoff is whether to pay the flat cost
    at all, not raw speed."""
    rng = _rng(seed, "T4")
    rooms = [
        {"id": "A", "name": "the Outer Hall", "w": 7},
        {"id": "B", "name": "the Lamp Room", "w": 7},
        {"id": "C", "name": "the Hidden Reach", "w": 7, "fog_locked": True},
        {"id": "D", "name": "the Inner Sanctum", "w": 6},
    ]
    n_drain = rng.randint(2, 4)
    duration = rng.randint(10, 16)
    hp_after = 100 - n_drain * duration
    threshold = max(1, hp_after - rng.randint(5, 15))
    links = [
        {},  # A-B open
        {},  # B-C open corridor, but C is fog_locked (blocked until revealed)
        {"gate_id": "G_final", "open_condition": g.HpAbove(threshold)},
    ]
    w, mids = _linear_world("T4", seed, rooms, links)
    w.start_pos = mids["A"]
    w.goal_zone_id = "D"

    bx0, by0 = w.zones["B"].x0, w.zones["B"].y0
    lamp_adj = rng.choice(LAMP_ADJ)
    lamp = w.add_interactable("lamp", f"a {lamp_adj} lamp", bx0 + 3, by0 + 2)
    drain_mech = g.Mechanic(
        mechanic_id="lamp_drain",
        trigger=g.on_interact(lamp.entity_id),
        conditions=[],
        effects=[g.DrainPerStep(n_drain, duration)],
    )
    reveal_mech = g.Mechanic(
        mechanic_id="lamp_reveal",
        trigger=g.on_interact(lamp.entity_id),
        conditions=[],
        effects=[g.RevealZone("C")],
    )
    w.register_mechanic(drain_mech)
    w.register_mechanic(reveal_mech)

    w.ground_truth = {
        "lamp_pos": (lamp.x, lamp.y), "n_drain": n_drain, "duration": duration,
        "threshold": threshold, "hp_after": hp_after, "goal_mid": mids["D"],
    }
    return w


# =====================================================================
# T5 — sacrifice-info
# =====================================================================

def build_T5(seed: int):
    """T5 'sacrifice-info' — pre-registered solution class: 3-fact
    information-asymmetry. Eating a seed (destroying it) costs a small
    amount of HP but permanently reveals a fogged-off zone the agent could
    not otherwise see existed. That zone's exit gate requires carrying a
    second, unrelated-looking item that was sitting in plain sight back in
    the start room the whole time. Nothing tells the agent up front that
    the seed and the charm matter — both facts are learned only through
    destructive experimentation and later composition."""
    rng = _rng(seed, "T5")
    rooms = [
        {"id": "A", "name": "the Antechamber", "w": 8},
        {"id": "S", "name": "the Hidden Reach", "w": 7, "fog_locked": True},
        {"id": "C", "name": "the Far Sanctum", "w": 6},
    ]
    links = [
        {},  # A-S open corridor, S is fog_locked (blocked until revealed)
        {"gate_id": "G1", "open_condition": g.Carrying("charm")},
    ]
    w, mids = _linear_world("T5", seed, rooms, links)
    w.start_pos = mids["A"]
    w.goal_zone_id = "C"

    ax0, ay0 = w.zones["A"].x0, w.zones["A"].y0
    seed_pos = (ax0 + 2, ay0 + 1)
    charm_pos = (ax0 + 5, ay0 + 3)
    seed_adj = rng.choice(SEED_ADJ)
    charm_adj = rng.choice(CHARM_ADJ)
    w.add_item("seed", f"a {seed_adj} seed", *seed_pos)
    w.add_item("charm", f"a {charm_adj} charm", *charm_pos)

    dmg = rng.randint(5, 15)
    eat_mech = g.Mechanic(
        mechanic_id="eat_seed_hurt",
        trigger=g.on_eat("seed"),
        conditions=[],
        effects=[g.HpDelta(-dmg)],
    )
    reveal_mech = g.Mechanic(
        mechanic_id="eat_seed_reveal",
        trigger=g.on_eat("seed"),
        conditions=[],
        effects=[g.RevealZone("S")],
    )
    w.register_mechanic(eat_mech)
    w.register_mechanic(reveal_mech)

    w.ground_truth = {
        "seed_pos": seed_pos, "charm_pos": charm_pos, "damage": dmg,
        "goal_mid": mids["C"],
    }
    return w


# =====================================================================
# T6 — double-override
# =====================================================================

def build_T6(seed: int):
    """T6 'double-override' — pre-registered solution class: 4-fact,
    requires TWO counterintuitive plays. (1) Eating a hazardous fruit
    costs HP; (2) the first gate opens only BELOW an HP threshold
    (damage-as-key, as in T1). (3) A charm item visibly HEALS the agent
    the moment they carry it into the second room (a deliberately
    seductive, demonstrated-positive decoy). (4) The final gate opens only
    while NOT carrying that same charm — so the agent must give up a
    proven-valuable item to finish, on top of having deliberately hurt
    itself earlier. Both overrides are load-bearing; skipping either
    strands the agent."""
    rng = _rng(seed, "T6")
    rooms = [
        {"id": "A", "name": "the Antechamber", "w": 8},
        {"id": "B", "name": "the Trial Room", "w": 7},
        {"id": "C", "name": "the Sanctum", "w": 6},
    ]
    magnitude = rng.randint(60, 85)
    threshold = (100 - magnitude) + rng.randint(5, 15)
    links = [
        {"gate_id": "G1", "open_condition": g.HpBelow(threshold)},
        {"gate_id": "G2", "open_condition": g.Carrying("charm", negate=True)},
    ]
    w, mids = _linear_world("T6", seed, rooms, links)
    w.start_pos = mids["A"]
    w.goal_zone_id = "C"

    ax0, ay0 = w.zones["A"].x0, w.zones["A"].y0
    adjs = rng.sample(FRUIT_ADJ, 2)
    hazard_slot, safe_slot = ((2, 1), (6, 3)) if rng.random() < 0.5 else ((6, 3), (2, 1))
    hz = (ax0 + hazard_slot[0], ay0 + hazard_slot[1])
    sz = (ax0 + safe_slot[0], ay0 + safe_slot[1])
    w.add_item("hazard_fruit", f"a {adjs[0]} fruit", *hz)
    w.add_item("plain_fruit", f"a {adjs[1]} fruit", *sz)

    charm_pos = (ax0 + 4, ay0 + 2)
    charm_adj = rng.choice(CHARM_ADJ)
    w.add_item("charm", f"a {charm_adj} charm", *charm_pos)

    eat_mech = g.Mechanic(
        mechanic_id="eat_hazard_fruit",
        trigger=g.on_eat("hazard_fruit"),
        conditions=[],
        effects=[g.HpDelta(-magnitude)],
    )
    w.register_mechanic(eat_mech)

    heal = rng.randint(8, 18)
    decoy_mech = g.Mechanic(
        mechanic_id="charm_decoy_heal",
        trigger=g.on_carry_enter("charm", "B"),
        conditions=[],
        effects=[g.HpDelta(heal)],
    )
    w.register_mechanic(decoy_mech)

    w.ground_truth = {
        "hazard_item_pos": hz, "safe_item_pos": sz, "charm_pos": charm_pos,
        "magnitude": magnitude, "gate_threshold": threshold, "heal": heal,
        "goal_mid": mids["C"],
    }
    return w


BUILDERS = {"T1": build_T1, "T2": build_T2, "T3": build_T3,
            "T4": build_T4, "T5": build_T5, "T6": build_T6}

ALIASES = {
    "lettuce-door": "T1", "carry-key-parity": "T2",
    "shrine-teleport-chain": "T3", "drain-lamp-tradeoff": "T4",
    "sacrifice-info": "T5", "double-override": "T6",
}

ALL_TEMPLATE_IDS = list(BUILDERS.keys())


def build(template_id: str, seed: int):
    tid = ALIASES.get(template_id, template_id)
    if tid not in BUILDERS:
        raise ValueError(f"unknown template_id {template_id!r}")
    return BUILDERS[tid](seed)


# =====================================================================
# reference (cheating) solver — uses ground_truth directly
# =====================================================================

def _bfs_path(world, start: Coord, goal: Coord) -> List[str]:
    """Shortest-path move list between two points, treating any non-WALL
    tile as passable (this solver has ground truth and assumes gates will
    be open at the moment of crossing, by construction of the script)."""
    if start == goal:
        return []
    deltas = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
    q = deque([start])
    came: Dict[Coord, Tuple[Coord, str]] = {start: None}
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        cx, cy = cur
        for name, (dx, dy) in deltas.items():
            nx, ny = cx + dx, cy + dy
            if not world.in_bounds(nx, ny):
                continue
            if world.tile(nx, ny) == world_mod.WALL:
                continue
            nxt = (nx, ny)
            if nxt not in came:
                came[nxt] = (cur, name)
                q.append(nxt)
    if goal not in came:
        raise RuntimeError(f"no path from {start} to {goal}")
    moves = []
    cur = goal
    while came[cur] is not None:
        prev, name = came[cur]
        moves.append(name)
        cur = prev
    moves.reverse()
    return moves


def _pad_for_parity(actions: List[str], k: int) -> None:
    """Insert a single 'wait' (if needed) so that the NEXT action appended
    after this call lands on agent.steps with the required parity k.
    agent.steps after N total actions == N (1-based), so the next action
    (index len(actions)+1) must satisfy (len(actions)+1) % 2 == k."""
    if (len(actions) + 1) % 2 != k:
        actions.append("wait")


def reference_solution(world) -> List[str]:
    """A cheating reference solver: it reads world.ground_truth directly
    (never available to a real agent) to script an exact solving action
    sequence, used only for solvability tests."""
    tid = world.template_id
    gt = world.ground_truth
    actions: List[str] = []
    cur = world.start_pos

    if tid == "T1":
        actions += _bfs_path(world, cur, gt["hazard_item_pos"]); cur = gt["hazard_item_pos"]
        actions.append("pickup")
        actions.append("eat a")
        actions += _bfs_path(world, cur, gt["goal_mid"])

    elif tid == "T2":
        actions += _bfs_path(world, cur, gt["sign_pos"]); cur = gt["sign_pos"]
        actions.append("interact")
        gate = world.gates_by_id["G1"]
        gate_pos = (gate.x, gate.y)
        approach_pos = (gate_pos[0] - 1, gate_pos[1])   # zone A sits left of the gate
        actions += _bfs_path(world, cur, approach_pos); cur = approach_pos
        _pad_for_parity(actions, gt["parity_k"])
        actions.append("right")   # the crossing attempt; parity padded above
        cur = gate_pos
        actions += _bfs_path(world, cur, gt["goal_mid"])

    elif tid == "T3":
        actions += _bfs_path(world, cur, gt["metal_pos"]); cur = gt["metal_pos"]
        actions.append("pickup")
        # the final move of this path lands ON the shrine tile, which
        # fires the on_touch+carrying(metal) mechanic and teleports us
        actions += _bfs_path(world, cur, gt["shrine_pos"])
        cur = gt["teleport_dest"]
        actions += _bfs_path(world, cur, gt["lever_pos"]); cur = gt["lever_pos"]
        actions.append("interact")
        actions += _bfs_path(world, cur, gt["goal_mid"])

    elif tid == "T4":
        actions += _bfs_path(world, cur, gt["lamp_pos"]); cur = gt["lamp_pos"]
        actions.append("interact")
        actions += _bfs_path(world, cur, gt["goal_mid"])

    elif tid == "T5":
        actions += _bfs_path(world, cur, gt["seed_pos"]); cur = gt["seed_pos"]
        actions.append("pickup")
        actions.append("eat a")
        actions += _bfs_path(world, cur, gt["charm_pos"]); cur = gt["charm_pos"]
        actions.append("pickup")   # letter reused as 'a' (previous 'a' was eaten)
        actions += _bfs_path(world, cur, gt["goal_mid"])

    elif tid == "T6":
        actions += _bfs_path(world, cur, gt["hazard_item_pos"]); cur = gt["hazard_item_pos"]
        actions.append("pickup")
        actions.append("eat a")
        actions += _bfs_path(world, cur, gt["charm_pos"]); cur = gt["charm_pos"]
        actions.append("pickup")   # letter reused as 'a'
        goal_room = world.zones["B"]
        b_mid = (goal_room.x0 + goal_room.w // 2, goal_room.y0 + goal_room.h // 2)
        actions += _bfs_path(world, cur, b_mid); cur = b_mid
        actions.append("drop a")
        actions += _bfs_path(world, cur, gt["goal_mid"])

    else:
        raise ValueError(f"no reference solver for template {tid}")

    return actions

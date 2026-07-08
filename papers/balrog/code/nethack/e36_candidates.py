"""NH-E36 SCENARIO STRATEGY SYNTHESIS — candidate strategy pool.

MODEL: claude-opus-4-8 (max thinking), Phase L session L / NH-E36 lead.
insight-origin: OP (operator directive — scenario-strategy synthesis).
knowledge: SYNTHESIS (LLM-generated candidate strategies) + DEMONSTRATION
           (the existing hand-designed levers KITE/THROW/STAIRS/DOOR_KITE are
           seeded into the pool as incumbents to beat).

THE MECHANISM (search-as-teacher + best-of-N + expert-seeding):
  Instead of hand-coding ONE lever for a hard scenario, GENERATE MANY diverse
  candidate strategies (this file), SIMULATE/RANK them across many sampled
  instances (e36_simulate.py), COMPILE the winner to a fast rule card, DEPLOY
  behind a flag. This file is step 2 (CANDIDATE GENERATION) — the
  TIER-SENSITIVE step. It is written to be Fable-ready: the pool is a flat
  registry of (name, priority, tag, policy_fn); a stronger diverse-generation
  model (Fable) can regenerate/extend REGISTRY without touching the harness.
  For this first end-to-end proof the pool was authored by claude-opus-4-8.

TARGET SCENARIO (first): TRASH = trash-melee at moderate/low HP on D2-6, the
  highest-FREQUENCY hard death class (313/794 harvested scenarios, the program's
  biggest death mass). Each candidate is a concrete action-policy over the
  agent's OWN served perception (a fresh C.Atlas fed the branch's obs — clean
  protocol, no env internals), signature `pol(A, obs, ps) -> [action_tokens]`.

Policies reuse the perception-driven primitives proven in e6_solve_v2 (the
search-as-teacher escape menu) and add NEW strategy classes never simulated as
a ranked pool: attacker-count management (CORNER/CORRIDOR), crisis resource
gambles (PRAY/QUAFF), attrition management (FIGHT_WEAKEST), and a synthesized
COMPOSITE (HYBRID_BEST) that sequences the sub-strategies by situation.
"""

import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(HERE, "pylib"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import nh_common as C
from nle import nethack as nh

# Reuse the proven escape-menu primitives + hand-designed incumbents.
from e6_solve_v2 import (
    pol_kite, pol_throw, pol_stairs, pol_door_kite,
    throwable_letter, _mobiles, _ray_clear, _doorways, INV, MOVES,
)

POTION_CLASS = int(nh.POTION_CLASS)
WAND_CLASS = int(nh.WAND_CLASS)


# --------------------------------------------------------------- perception
def _stats(obs):
    bl = obs["obs"]["blstats"]
    return (int(bl[nh.NLE_BL_HP]), int(bl[nh.NLE_BL_HPMAX]),
            int(bl[nh.NLE_BL_HUNGER]))


def _sign(v):
    return (v > 0) - (v < 0)


def _dir_to(ax, ay, tx, ty):
    d = (_sign(tx - ax), _sign(ty - ay))
    return C.DIR_OF.get(d)


def _adj_hostiles(A):
    ax, ay = A.agent
    return [m for m in _mobiles(A)
            if max(abs(m.x - ax), abs(m.y - ay)) == 1]


def _fight_weakest(A):
    """Attack the WEAKEST adjacent hostile (min level,difficulty) to drop the
    attacker count as fast as possible; else step toward the nearest hostile."""
    ax, ay = A.agent
    adj = _adj_hostiles(A)
    if adj:
        adj.sort(key=lambda m: (m.level, m.difficulty))
        m = adj[0]
        d = _dir_to(ax, ay, m.x, m.y)
        return [d] if d else ["search"]
    mob = _mobiles(A)
    if not mob:
        return ["search"]
    m = min(mob, key=lambda m: max(abs(m.x - ax), abs(m.y - ay)))
    L = A.level
    best = None
    for name, (nx, ny) in L.neighbors(ax, ay):
        if any(mm.x == nx and mm.y == ny for mm in L.monsters):
            continue
        d = max(abs(m.x - nx), abs(m.y - ny))
        if best is None or d < best[0]:
            best = (d, name)
    return [best[1]] if best else ["search"]


def _openness(L, x, y):
    return sum(1 for _ in L.neighbors(x, y))


# ============================================================ CANDIDATE POOL
# Each returns a list of action tokens (executed one env-step each by the
# harness; unknown tokens degrade to 'search').

def pol_fight_nearest(A, obs, ps):
    """NULL/aggressive control: attack nearest hostile, never flee."""
    return _fight_weakest(A) if _adj_hostiles(A) else _step_or_search(A)


def _step_or_search(A):
    ax, ay = A.agent
    mob = _mobiles(A)
    if not mob:
        return ["search"]
    m = min(mob, key=lambda m: max(abs(m.x - ax), abs(m.y - ay)))
    d = _dir_to(ax, ay, m.x, m.y)
    return [d] if d else ["search"]


def pol_fight_weakest(A, obs, ps):
    """Attrition management: kill the weakest adjacent trash first."""
    return _fight_weakest(A)


def pol_corner(A, obs, ps):
    """Minimize SIMULTANEOUS attackers: step to the least-open reachable cell
    (a corner/wall-back exposes fewer sides), then fight the weakest adjacent.
    Real NetHack survival tactic never simulated as a ranked candidate."""
    L = A.level
    ax, ay = A.agent
    mob = _mobiles(A)
    if not mob:
        return ["search"]
    cur_open = _openness(L, ax, ay)
    best = None
    for name, (nx, ny) in L.neighbors(ax, ay):
        if any(m.x == nx and m.y == ny for m in L.monsters):
            continue
        adj = sum(1 for m in mob if max(abs(m.x - nx), abs(m.y - ny)) <= 1)
        opn = _openness(L, nx, ny)
        key = (adj, opn)
        if best is None or key < best[0]:
            best = (key, name, opn)
    # If a strictly less-open (or equally-safe fewer-open) cell exists, back into it.
    if best is not None and best[2] < cur_open and best[0][0] <= len(_adj_hostiles(A)):
        return [best[1]]
    # Settled in the tightest reachable spot -> fight the weakest attacker.
    if _adj_hostiles(A):
        return _fight_weakest(A)
    return [best[1]] if best else ["search"]


def pol_corridor(A, obs, ps):
    """Funnel to a 1-wide corridor so at most 1-2 trash can attack at once,
    then hold and fight the weakest. Falls back to kite when no corridor known."""
    L = A.level
    ax, ay = A.agent
    if L.terrain[ay][ax] == C.CORRIDOR:
        return _fight_weakest(A) if _adj_hostiles(A) else ["search"]
    goals = set(L.find_terrain(C.CORRIDOR))
    if not goals:
        return pol_kite(A, obs, ps)
    mcells = {m.pos for m in L.monsters if not m.pet}
    path = L.bfs(A.agent, goals, avoid=mcells) or L.bfs(A.agent, goals)
    if not path:
        return pol_kite(A, obs, ps)
    return [path[0]]


def pol_pray(A, obs, ps):
    """Crisis prayer: if plausibly prayer-eligible (HP<max(hpmax//7,5) or
    Weak+ hunger) pray ONCE (prayer-timeout unknown from obs -> a gamble the
    program has never tried in a trash crisis); afterward kite."""
    hp, hpmax, hunger = _stats(obs)
    eligible = (hp <= max(hpmax // 7, 5)) or (hunger >= 3)
    if eligible and not ps.get("prayed"):
        ps["prayed"] = True
        return ["pray", "y"]
    return pol_kite(A, obs, ps)


def _unknown_potion_letter(obs):
    for letter, desc, oc in C.inventory(obs):
        if oc != POTION_CLASS:
            continue
        d = desc.lower()
        if " of " in d:            # identified (e.g. "potion of healing")
            continue
        return letter
    return None


def pol_quaff_unknown(A, obs, ps):
    """Resource gamble: quaff an UNIDENTIFIED potion once (hope for healing/
    gain-level/extra-healing); else kite. Best-of-N frames the gamble honestly."""
    if not ps.get("quaffed"):
        letter = _unknown_potion_letter(obs)
        if letter:
            ps["quaffed"] = True
            return ["quaff", letter]
    return pol_kite(A, obs, ps)


def pol_retreat(A, obs, ps):
    """Invert recent moves to back out of the pack, then rest (v1 line)."""
    L = A.level
    if _mobiles(A):
        # walk directly away from the nearest hostile
        return pol_kite(A, obs, ps)
    return ["search"]


def pol_rest(A, obs, ps):
    """Stand-and-heal control (fails vs adjacent same-speed trash by design)."""
    return ["search"]


def pol_throw_then_fight(A, obs, ps):
    """Hybrid: hurl ammo on a clear line, else melee the weakest adjacent."""
    letter = throwable_letter(obs)
    if letter:
        L = A.level
        ax, ay = A.agent
        cands = []
        for m in _mobiles(A):
            r = _ray_clear(L, ax, ay, m)
            if r is not None:
                cands.append((r[1], r[0]))
        if cands:
            cands.sort()
            return ["throw", letter, cands[0][1]]
    return _fight_weakest(A)


def pol_stairs_or_kite(A, obs, ps):
    """Escape the level only when the stairs are CLOSE (<=8 steps); else kite —
    avoids the STAIRS line's long dangerous cross-level treks."""
    L = A.level
    if A.agent in L.stairs_down or A.agent in L.holes:
        return ["down"]
    goals = set(L.stairs_down) | set(L.holes)
    if goals:
        path = L.bfs(A.agent, goals)
        if path and len(path) <= 8:
            return [path[0]]
    return pol_kite(A, obs, ps)


def pol_aggro_descent(A, obs, ps):
    """Risk-tolerant STAIRS: beeline to the down-stairs bumping through if
    needed (accept a hit to leave the kill-zone)."""
    L = A.level
    if A.agent in L.stairs_down or A.agent in L.holes:
        return ["down"]
    goals = set(L.stairs_down) | set(L.holes)
    if not goals:
        return pol_kite(A, obs, ps)
    path = L.bfs(A.agent, goals)
    if not path:
        return pol_kite(A, obs, ps)
    return [path[0]]


def _wand_letter(obs):
    for letter, desc, oc in C.inventory(obs):
        if oc != WAND_CLASS:
            continue
        d = desc.lower()
        if "(0:0)" in d or "of nothing" in d:
            continue
        return letter
    return None


def pol_zap_wand(A, obs, ps):
    """Zap a carried wand at the nearest in-line hostile; else throw/kite."""
    letter = _wand_letter(obs)
    if letter:
        L = A.level
        ax, ay = A.agent
        cands = []
        for m in _mobiles(A):
            r = _ray_clear(L, ax, ay, m)
            if r is not None:
                cands.append((r[1], r[0]))
        if cands:
            cands.sort()
            return ["zap", letter, cands[0][1]]
    return pol_throw(A, obs, ps)


def pol_wait_pet(A, obs, ps):
    """Position so the starting pet tanks/kills the trash: if a pet is nearby
    move toward it (join forces); if pet already adjacent hold and fight the
    weakest; else kite."""
    L = A.level
    ax, ay = A.agent
    pets = [m for m in L.monsters if m.pet]
    if pets:
        p = min(pets, key=lambda m: max(abs(m.x - ax), abs(m.y - ay)))
        pd = max(abs(p.x - ax), abs(p.y - ay))
        if pd <= 1:
            return _fight_weakest(A) if _adj_hostiles(A) else ["search"]
        d = _dir_to(ax, ay, p.x, p.y)
        if d and not any(m.x == ax + C.DIRS[d][0] and m.y == ay + C.DIRS[d][1]
                         for m in L.monsters):
            return [d]
    return pol_kite(A, obs, ps)


def pol_far_flee(A, obs, ps):
    """Travel-flee: pick the safest direction and issue a 'far <dir>' rush to
    open distance fast (multi-step engine travel)."""
    L = A.level
    ax, ay = A.agent
    mob = _mobiles(A)
    if not mob:
        return ["search"]
    best = None
    for name, (nx, ny) in L.neighbors(ax, ay):
        if any(m.x == nx and m.y == ny for m in L.monsters):
            continue
        d = min(max(abs(m.x - nx), abs(m.y - ny)) for m in mob)
        adj = sum(1 for m in mob if max(abs(m.x - nx), abs(m.y - ny)) <= 1)
        key = (adj, -d)
        if best is None or key < best[0]:
            best = (key, name)
    if best is None:
        return ["search"]
    return ["far " + best[1], best[1]]   # rush, then a plain step fallback


def pol_elbereth(A, obs, ps):
    """Attempt a dust-engrave of Elbereth (scares most early trash: a/d/@ etc).
    HONEST CAVEAT: getlin text-commit is interface-limited in this action space
    (no Return token) — the program logged dust-write as interface-blocked. This
    candidate ATTEMPTS the sequence once and degrades to kite; its ranking will
    show whether the interface admits it at all (expected: no)."""
    if not ps.get("engraved"):
        ps["engraved"] = True
        # engrave -> '-' (fingers/dust) -> spell letters -> esc to bail the
        # getlin if it will not commit. Worst case: ~1 wasted turn then kite.
        return ["engrave", "-", "E", "l", "b", "e", "r", "e", "t", "h", "esc"]
    return pol_kite(A, obs, ps)


def pol_hybrid_best(A, obs, ps):
    """SYNTHESIZED COMPOSITE (the headline candidate): sequence the sub-
    strategies by situation —
      1. very-low-HP & prayer-plausible  -> PRAY (once)
      2. clean ranged line & ammo        -> THROW
      3. down-stairs within 10 steps     -> STAIRS (leave the kill-zone)
      4. boxed in (open cell, many adj)  -> CORNER/CORRIDOR funnel then fight
      5. otherwise                       -> KITE (relaxed disengage)
    This is the strategy a competent player actually runs; best-of-N asks
    whether COMPOSING beats any single lever."""
    hp, hpmax, hunger = _stats(obs)
    L = A.level
    ax, ay = A.agent
    # 1. crisis prayer
    if (hp <= max(hpmax // 7, 4)) and not ps.get("prayed"):
        ps["prayed"] = True
        return ["pray", "y"]
    # 2. ranged
    letter = throwable_letter(obs)
    if letter:
        cands = []
        for m in _mobiles(A):
            r = _ray_clear(L, ax, ay, m)
            if r is not None:
                cands.append((r[1], r[0]))
        if cands:
            cands.sort()
            return ["throw", letter, cands[0][1]]
    # 3. near stairs -> leave
    if A.agent in L.stairs_down or A.agent in L.holes:
        return ["down"]
    goals = set(L.stairs_down) | set(L.holes)
    if goals:
        path = L.bfs(A.agent, goals)
        if path and len(path) <= 10:
            return [path[0]]
    # 4. boxed / outnumbered -> funnel then fight weakest
    adj = _adj_hostiles(A)
    if len(adj) >= 2 or (adj and _openness(L, ax, ay) >= 5):
        return pol_corner(A, obs, ps)
    # 5. default disengage
    return pol_kite(A, obs, ps)


# name -> (policy_fn, priority[LLM-estimated, 1=highest], tag, provenance)
# priority = the LLM's pre-simulation promise ranking (operator step 2:
# "have the LLM prioritize the 20 by expected promise"). Lower = more promising.
REGISTRY = [
    ("HYBRID_BEST",     pol_hybrid_best,     1, "COMPOSITE",   "SYNTHESIS"),
    ("CORRIDOR",        pol_corridor,        2, "ATTACKER-MGMT", "SYNTHESIS"),
    ("STAIRS",          pol_stairs,          3, "ESCAPE-LEVEL", "DEMONSTRATION"),
    ("KITE",            pol_kite,            4, "DISENGAGE",    "DEMONSTRATION"),
    ("CORNER",          pol_corner,          5, "ATTACKER-MGMT", "SYNTHESIS"),
    ("STAIRS_OR_KITE",  pol_stairs_or_kite,  6, "ESCAPE-LEVEL", "SYNTHESIS"),
    ("DOOR_KITE",       pol_door_kite,       7, "DISENGAGE",    "DEMONSTRATION"),
    ("THROW",           pol_throw,           8, "RANGED",       "DEMONSTRATION"),
    ("FIGHT_WEAKEST",   pol_fight_weakest,   9, "ATTRITION",    "SYNTHESIS"),
    ("THROW_THEN_FIGHT", pol_throw_then_fight, 10, "RANGED",    "SYNTHESIS"),
    ("PRAY",            pol_pray,            11, "RESOURCE-GAMBLE", "SYNTHESIS"),
    ("FAR_FLEE",        pol_far_flee,        12, "DISENGAGE",   "SYNTHESIS"),
    ("AGGRO_DESCENT",   pol_aggro_descent,   13, "ESCAPE-LEVEL", "SYNTHESIS"),
    ("QUAFF_UNKNOWN",   pol_quaff_unknown,   14, "RESOURCE-GAMBLE", "SYNTHESIS"),
    ("ZAP_WAND",        pol_zap_wand,        15, "RANGED",      "SYNTHESIS"),
    ("WAIT_PET",        pol_wait_pet,        16, "ALLY",        "SYNTHESIS"),
    ("RETREAT",         pol_retreat,         17, "DISENGAGE",   "DEMONSTRATION"),
    ("FIGHT_NEAREST",   pol_fight_nearest,   18, "NULL-CONTROL", "SYNTHESIS"),
    ("REST",            pol_rest,            19, "NULL-CONTROL", "DEMONSTRATION"),
    ("ELBERETH",        pol_elbereth,        20, "WARD",        "SYNTHESIS"),
]

REGISTRY.sort(key=lambda r: r[2])

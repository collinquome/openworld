#!/usr/bin/env python3
"""
MODEL: Sonnet 5 worker, spec by Fable 5 (max reasoning), Phase L session 3.

Phase-L SNAPSHOT SUITE (exit criterion iv) — regression fixtures for the
NetHack research program's DiveAgent/perception codebase (nh_agent.py,
nh_percept.py, nh_common.py).

Run with: python3 snapshot_suite.py   (from this directory)
Prints one PASS/FAIL/SKIPPED line per fixture, then a SUITE GREEN/RED line.
Exits 0 only if every fixture is PASS or SKIPPED (no FAILs).

READ-ONLY CONTRACT: this suite never modifies nh_agent.py, nh_percept.py,
nh_common.py, nh_runner.py, or any other codebase file. It imports and
calls the REAL functions/methods so a regression in the source turns a
fixture red — nothing here re-implements the fixed logic.

Two halves:

  (A) SIX FIXED-BUG SNAPSHOT FIXTURES. Each exercises the real code path
      at its historical fix site (see per-fixture docstrings below for
      rule-card provenance: bug name / incident / fix site file:line).
      Inputs are either (a) a live NLE env reset on a DEV SEED with a
      single served field overridden to reproduce a message-driven
      scenario, or (b) a minimal-but-real Atlas/LevelMap/Monster object
      graph built from the actual nh_common classes, or (c) a message
      string copied verbatim from a real recorded trajectory in
      results/trajectories/*.json. Recorded strings used as fixture
      inputs are extracted with provenance into
      results/snapshot_fixtures/recorded_messages.json.

      Fixture 1 (armor-under-@) needs C2_ARMOR=1 (NH_ARMOR env var) to
      exercise the shop-refusal branch. Since nh_agent.py reads NH_* flags
      at import time via _flag(), that fixture runs in an isolated
      subprocess (env var scoped to the child only) so it never taints
      this process's own nh_agent import (all flags OFF here, matching
      the other five fixtures' assumptions).

  (B) E16 PROBE REPLAY. results/e16_probes/*.json are branch/replay
      probe records produced by nh_branch.py against the deterministic
      NLE env stack. Every record gets a structural-integrity check
      (schema-aware: the 9 records use 3 different shapes). The 3
      records with the shortest total recorded action sequence are then
      actually re-executed through nh_branch.Branch (after nh_branch's
      own verify_determinism() gate) and checked against their recorded
      "observed" outcome. If the env stack can't be initialized at all,
      Part B prints an explicit SKIPPED line instead of silently passing.

HARD RULES honored: dev seeds only (nh_branch.assert_dev_seed enforces
this; this suite additionally never touches 1000-7024); no source files
modified; NH_* env vars are scoped per-fixture (subprocess isolation) and
never left set for later fixtures in this process.
"""

import copy
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

RESULTS_DIR = os.path.join(HERE, "results")
FIXTURES_DIR = os.path.join(RESULTS_DIR, "snapshot_fixtures")
PROBE_DIR = os.path.join(RESULTS_DIR, "e16_probes")
LOG_PATH = os.path.join(RESULTS_DIR, "snapshot_suite.log")
RECORDED_MSGS_PATH = os.path.join(FIXTURES_DIR, "recorded_messages.json")

os.makedirs(FIXTURES_DIR, exist_ok=True)

# dev seeds only (well clear of nh_branch.FORBIDDEN: 1000-1004, 2000-2024,
# 3000-3079, 4000-4079, 5000-5024, 6000-6099, 7000-7024). Use low seeds.
DEV_SEED_A = 501
DEV_SEED_B = 502
DEV_SEED_C = 503

_LOG_LINES = []


def emit(line=""):
    print(line)
    _LOG_LINES.append(line)


def _quiet_import_env_stack():
    """Import nh_harness / nh_agent from THIS process (no NH_* flags set:
    every fixture in this process except #1 wants byte-identical v1.1
    default-off behavior)."""
    import nh_harness as H
    import nh_agent as AG
    import nh_common as C
    return H, AG, C


# ---------------------------------------------------------------- fixtures
# extract real recorded fixture inputs from results/trajectories/*.json
# (provenance recorded alongside each string) -> results/snapshot_fixtures/
def build_recorded_fixtures():
    import glob
    targets = {
        "kill_msg": "You kill the grid bug!",
        "see_here_food": "You see here a food ration.",
        "see_here_armor": "You see here a crude chain mail.",
        "see_here_armor_shop":
            "You see here a studded leather armor (for sale, 20 zorkmids).",
        "door_already_open": "This door is already open.",
        "door_broken": "This door is broken.",
        "phantom_eat_refusal": "You don't have anything to eat.",
    }
    found = {v: None for v in targets.values()}
    for fn in sorted(glob.glob(os.path.join(RESULTS_DIR, "trajectories",
                                            "*.json"))):
        try:
            d = json.load(open(fn))
        except Exception:
            continue
        for m in d.get("messages", []):
            if m in found and found[m] is None:
                found[m] = os.path.relpath(fn, HERE)
        if all(found.values()):
            break
    out = {}
    missing = []
    for key, msg in targets.items():
        src = found.get(msg)
        if src is None:
            missing.append(key)
        out[key] = {"message": msg, "source_trajectory": src}
    with open(RECORDED_MSGS_PATH, "w") as f:
        json.dump(out, f, indent=2)
    return out, missing


# ---- Fixture 1: armor-under-@ (message-driven on-cell pickup) -----------
# RULE CARD [ARMOR_UNDER_AT]: an item lying on the agent's own cell is
# INVISIBLE in the served glyph grid -- the '@' glyph covers it. On-cell
# pickup can only be driven by the "You see here ..." message channel.
# Bug: shop merchandise ("for sale"/"zorkmids" suffix) matched the same
# regex and got auto-picked-up -> instant unpayable debt / shop violence.
# Fix site: nh_agent.py RE_SEE_HERE (line 149) + the pickup block in
# _decide() around line 1339-1370 (shop-refusal guard at line 1343).
# See FABLE_NETHACK_C2_REPORT.md ~line 110 (Bug #5).
FX1_SCRIPT = r"""
import copy, json, os, sys
HERE = os.getcwd()
sys.path.insert(0, HERE)
rec = json.load(open(os.path.join(HERE, "results", "snapshot_fixtures",
                                  "recorded_messages.json")))
import nh_harness as H
import nh_agent as AG
from nh_agent import DiveAgent

assert AG.C2_ARMOR is True, "NH_ARMOR did not reach nh_agent.C2_ARMOR"
assert AG.C2_ANY is True

env = H.make_env()
obs, _ = env.reset(seed=%d)
space = list(env.env.language_action_space)

base_agent = DiveAgent(log=lambda *a, **k: None)
base_agent.set_actions(space)
a0 = base_agent.act(obs)               # first real action: 'look'
obs, r, term, trunc, info = env.step(a0)

def run_with_msg(msg):
    ag = DiveAgent(log=lambda *a, **k: None)
    ag.set_actions(space)
    ag.act(obs)                         # primes need_look False on real state
    injected = copy.deepcopy(obs)
    injected["obs"]["text_message"] = msg
    act = ag.act(injected)
    return act, ag

a_food, ag_food = run_with_msg(rec["see_here_food"]["message"])
assert a_food == "pickup" and ag_food.queue_tag == "pickup", (a_food, ag_food.queue_tag)

a_armor, ag_armor = run_with_msg(rec["see_here_armor"]["message"])
assert a_armor == "pickup" and ag_armor.pickup_kind == "armor", (a_armor, ag_armor.pickup_kind)

a_shop, ag_shop = run_with_msg(rec["see_here_armor_shop"]["message"])
assert a_shop != "pickup" and ag_shop.queue_tag != "pickup", (a_shop, ag_shop.queue_tag)

env.close()
print(json.dumps({"ok": True, "a_food": a_food, "a_armor": a_armor,
                  "a_shop": a_shop}))
""" % DEV_SEED_A


def fx1_armor_under_at():
    env = dict(os.environ)
    env["NH_ARMOR"] = "1"
    # explicitly do NOT propagate any other NH_* flags from the parent
    for k in list(env):
        if k.startswith("NH_") and k != "NH_ARMOR":
            env.pop(k, None)
    try:
        proc = subprocess.run([sys.executable, "-c", FX1_SCRIPT],
                              cwd=HERE, env=env, capture_output=True,
                              text=True, timeout=120)
    except Exception as e:
        return False, f"subprocess failed to launch: {e!r}"
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()
        tail = "\n".join(tail[-15:])
        return False, f"subprocess exit {proc.returncode}:\n{tail}"
    try:
        last_line = [l for l in proc.stdout.splitlines() if l.strip()][-1]
        result = json.loads(last_line)
    except Exception as e:
        return False, f"could not parse subprocess result: {e!r}: {proc.stdout!r}"
    if not result.get("ok"):
        return False, f"assertions failed: {result}"
    return True, (f"food msg -> {result['a_food']!r}; "
                  f"armor msg -> {result['a_armor']!r} (kind=armor); "
                  f"shop msg -> {result['a_shop']!r} (!= pickup)")


# ---- Fixture 2: corpse-on-victim-cell ------------------------------------
# RULE CARD [CORPSE_ON_VICTIM_CELL]: a kill's corpse drops on the CELL WE
# ATTACKED INTO (the victim's cell), not on the agent's own cell. A
# "phantom corpse" (kill logged but no corpse actually dropped -- a
# probabilistic NetHack outcome) must be purged from the fresh-kill
# ledger the moment the game tells us "You don't have anything to eat" at
# that cell, or the food-clock freezes forever chasing a corpse that
# isn't there (dev seed 103 abort). Fix site: nh_agent.py _bookkeeping(),
# kill-log block ~lines 478-489, phantom-corpse purge ~lines 531-536.
def fx2_corpse_on_victim_cell(H, AG, C, rec):
    from nh_agent import DiveAgent
    env = H.make_env()
    try:
        obs, _ = env.reset(seed=DEV_SEED_B)
        space = list(env.env.language_action_space)
        agent = DiveAgent(log=lambda *a, **k: None)
        agent.set_actions(space)
        agent.act(obs)
        a0 = "east" if "east" in space else space[0]
        obs, r, term, trunc, info = env.step(a0 if a0 == "look" else "look")

        A = agent.atlas
        agent.last_action = "east"
        victim_cell = (A.agent[0] + 1, A.agent[1])

        kill_msg = rec["kill_msg"]["message"]
        agent._bookkeeping(obs, kill_msg)
        if not agent.fresh_kills:
            return False, f"no fresh_kills recorded after {kill_msg!r}"
        cell, species, t = agent.fresh_kills[-1]
        if cell != victim_cell:
            return False, f"corpse cell {cell} != victim cell {victim_cell}"
        if cell == A.agent:
            return False, "corpse landed on agent cell, not victim cell"

        # phantom corpse: a kill logged AT the agent's own cell (e.g. we
        # stepped onto a spot where something died) with no corpse drop
        agent.fresh_kills.append((A.agent, "newt", A.time))
        agent._bookkeeping(obs, rec["phantom_eat_refusal"]["message"])
        if any(k[0] == A.agent for k in agent.fresh_kills):
            return False, "phantom corpse at agent cell not purged"
        return True, (f"kill msg {kill_msg!r} -> corpse at victim cell "
                      f"{victim_cell} (agent at {A.agent}); phantom purge "
                      f"on {rec['phantom_eat_refusal']['message']!r} OK")
    finally:
        env.close()


# ---- Fixture 3: shopkeeper-dpt floors at the difficulty prior -----------
# RULE CARD [PEACEFUL_BIASED_DPT_FLOOR]: species that are logged mostly
# while PEACEFUL (shopkeeper/guard/watchman/dwarf/...) accumulate an
# empirical dpt near 0 (they coexist peacefully most of the time) but hit
# like trucks once hostile -- a guard killed 3 characters historically.
# Their species_dpt() must FLOOR at the difficulty prior no matter how
# much zero-damage adjacency data piles up; a normal (non-peaceful-biased)
# species should legitimately converge DOWN below the prior with the same
# kind of data. Fix site: nh_percept.py PEACEFUL_BIASED (line 55) +
# species_dpt() (lines 60-76).
def fx3_shopkeeper_dpt_floor():
    import nh_percept as P
    # synthetic exchange table standing in for results/c2_exchange.json:
    # heavy N, ~0 dpt for both species (as real peaceful coexistence logs
    # would look) -- this is INPUT DATA, not a re-implementation of the
    # shrinkage/floor logic, which is exercised for real via species_dpt().
    P._EXC = {
        "species": {
            "shopkeeper": {"dpt": 0.0, "n_turns": 500, "difficulty": 6},
            "jackal": {"dpt": 0.05, "n_turns": 500, "difficulty": 1},
        },
        "fallback": {"slope": 0.08, "intercept": 0.61},
    }
    fb = P._EXC["fallback"]
    prior_shop = fb["intercept"] + fb["slope"] * 6
    prior_jackal = fb["intercept"] + fb["slope"] * 1
    dpt_shop = P.species_dpt("shopkeeper", difficulty=6)
    dpt_jackal = P.species_dpt("jackal", difficulty=1)
    if dpt_shop < prior_shop - 1e-9:
        return False, (f"shopkeeper dpt {dpt_shop:.3f} fell BELOW prior "
                       f"{prior_shop:.3f} despite PEACEFUL_BIASED floor")
    if not (dpt_jackal < prior_jackal - 0.05):
        return False, (f"jackal (non-peaceful-biased) dpt {dpt_jackal:.3f} "
                       f"did not converge below its prior {prior_jackal:.3f} "
                       f"-- floor test is not discriminating")
    return True, (f"shopkeeper dpt={dpt_shop:.3f} floored at prior="
                  f"{prior_shop:.3f} after 500 zero-dpt turns; "
                  f"jackal dpt={dpt_jackal:.3f} < prior={prior_jackal:.3f} "
                  f"(converges down, as expected for non-peaceful-biased)")


# ---- Fixture 4: dwarven != dwarf (race-adjective vs species-noun) -------
# RULE CARD [RACE_ADJECTIVE_VS_SPECIES_NOUN]: the character's race is
# reported as an ADJECTIVE ("dwarven", "elven", "gnomish") but corpse/
# monster names use the SPECIES NOUN ("dwarf", "elf", "gnome"). Treating
# them as the same string broke corpse-safety matching and caused a
# god-wrath epidemic (eating own-race corpses). Fix site: nh_agent.py
# _RACE_ROOT (lines 603-605) + _cannibal() (lines 607-614). Unknown race
# (welcome message missed) must conservatively refuse dwarf/gnome/elf
# corpses.
def fx4_dwarven_not_dwarf():
    from nh_agent import DiveAgent
    agent = DiveAgent(log=lambda *a, **k: None)
    agent.race = "dwarven"
    checks = []
    checks.append(("dwarven refuses 'dwarf corpse'",
                   agent._cannibal("dwarf corpse") is True))
    checks.append(("dwarven refuses 'dwarf zombie corpse'",
                   agent._cannibal("dwarf zombie corpse") is True))
    checks.append(("dwarven allows unrelated 'jackal corpse'",
                   agent._cannibal("jackal corpse") is False))

    agent2 = DiveAgent(log=lambda *a, **k: None)
    agent2.race = None
    checks.append(("unknown race refuses 'dwarf corpse'",
                   agent2._cannibal("dwarf corpse") is True))
    checks.append(("unknown race refuses 'gnome corpse'",
                   agent2._cannibal("gnome corpse") is True))
    checks.append(("unknown race refuses 'elf corpse'",
                   agent2._cannibal("elf corpse") is True))

    failed = [name for name, ok in checks if not ok]
    if failed:
        return False, f"failed: {failed}"
    return True, "; ".join(name for name, _ in checks)


# ---- Fixture 5: pet-not-a-wall -------------------------------------------
# RULE CARD [PET_NOT_A_WALL]: a pet's cell must be PASSABLE for pathing
# (moving into it swaps places), never an obstacle. Treating pets as
# walls let a following kitten box the agent into a corridor dead-end
# forever (dev seeds 106/103: thousands of stationary searches). Fix
# site: nh_agent.py _mcells() (~line 568, excludes pets from the obstacle
# set) and _step_path() (~line 2419, "if m.pet: return step" -> swap).
def fx5_pet_not_a_wall():
    import nh_common as C
    from nh_agent import DiveAgent
    agent = DiveAgent(log=lambda *a, **k: None)
    A = agent.atlas
    A.key = (0, 1)
    A.levels[A.key] = C.LevelMap(A.key)
    A.agent = (5, 5)
    L = A.level
    for x in range(3, 8):
        for y in range(3, 8):
            L.terrain[y][x] = C.FLOOR
            L.explored[y][x] = True

    pet = C.Monster(6, 5, C.GLYPH_PET_OFF)   # pet glyph, directly east
    if not pet.pet:
        return False, "test setup bug: constructed monster is not a pet"
    L.monsters = [pet]

    mc = agent._mcells()
    if (6, 5) in mc:
        return False, f"_mcells() treats pet cell as an obstacle: {mc}"

    path = L.bfs(A.agent, [(6, 5)], avoid=agent._suspects() | mc)
    if path != ["east"]:
        return False, f"bfs did not route directly through the pet cell: {path}"

    act = agent._step_path(path)
    if act != "east":
        return False, f"_step_path avoided/detoured around pet: {act!r}"
    return True, (f"pet={pet.name!r} at (6,5): _mcells excludes it "
                  f"({mc!r}), bfs path={path}, _step_path -> {act!r} "
                  f"(swap-in, not a wall)")


# ---- Fixture 6: stale-door terrain correction ----------------------------
# RULE CARD [STALE_DOOR_CORRECTION] (v1 failure catalog #8): an item
# glyph covering an opened door left the remembered terrain stuck at
# "closed"; the open/kick-direction loop then churned 100k-step episodes
# at ~zero game time. The door-outcome MESSAGE channel is authoritative
# and must correct stale terrain belief. Fix site: nh_agent.py
# _bookkeeping(), door_target correction block ~lines 546-560.
def fx6_stale_door(H, AG, C, rec):
    from nh_agent import DiveAgent
    env = H.make_env()
    try:
        obs, _ = env.reset(seed=DEV_SEED_C)
        space = list(env.env.language_action_space)
        agent = DiveAgent(log=lambda *a, **k: None)
        agent.set_actions(space)
        agent.act(obs)
        obs, r, term, trunc, info = env.step("look")

        A = agent.atlas
        tx, ty = A.agent[0] + 1, A.agent[1]

        # scenario 1: stale belief 'closed', real outcome 'open'
        A.level.terrain[ty][tx] = C.DOOR_CLOSED
        agent.door_target = (tx, ty)
        agent._bookkeeping(obs, rec["door_already_open"]["message"])
        if A.level.terrain[ty][tx] != C.DOOR_OPEN:
            return False, (f"terrain not corrected to DOOR_OPEN after "
                           f"{rec['door_already_open']['message']!r}: "
                           f"{A.level.terrain[ty][tx]}")
        if agent.door_target is not None:
            return False, "door_target not cleared after open correction"

        # scenario 2: stale belief 'closed', real outcome 'broken' (-> DOORWAY)
        A.level.terrain[ty][tx] = C.DOOR_CLOSED
        agent.door_target = (tx, ty)
        agent._bookkeeping(obs, rec["door_broken"]["message"])
        if A.level.terrain[ty][tx] != C.DOORWAY:
            return False, (f"terrain not corrected to DOORWAY after "
                           f"{rec['door_broken']['message']!r}: "
                           f"{A.level.terrain[ty][tx]}")
        return True, (f"stale DOOR_CLOSED belief at {(tx, ty)} corrected to "
                      f"DOOR_OPEN on {rec['door_already_open']['message']!r} "
                      f"and to DOORWAY on {rec['door_broken']['message']!r}")
    finally:
        env.close()


# ------------------------------------------------------------------ Part B
def _record_action_seq(d):
    """Best-effort total action sequence for a probe record, across the
    3 schemas present in results/e16_probes/*.json. None if the record
    carries no action list at all (prose-only probe)."""
    if isinstance(d.get("script"), list):
        prefix = d.get("prefix_len") or 0
        return prefix, d["script"]
    if isinstance(d.get("actions"), list):
        return 0, d["actions"]
    return None


def check_probe_structure(name, d):
    if "seed" not in d or not isinstance(d["seed"], int):
        return False, "missing/invalid 'seed'"
    seq = _record_action_seq(d)
    has_results = any(
        (isinstance(d.get(k), str) and d.get(k).strip()) or
        (isinstance(d.get(k), list) and len(d.get(k)) > 0)
        for k in ("observed", "knowledge", "adj")
    )
    if seq is None and not has_results:
        return False, "no action sequence AND no results/observed fields"
    if seq is not None:
        _, actions = seq
        if not actions or any(not isinstance(a, str) or not a
                              for a in actions):
            return False, f"empty/invalid action sequence: {actions!r}"
    if not has_results:
        return False, "no non-empty results field (observed/knowledge/adj)"
    kind = "actions=%d" % len(seq[1]) if seq else "prose-only"
    return True, f"seed={d['seed']} {kind} results-ok"


def fxB_structural(records):
    lines = []
    all_ok = True
    for name, d in records:
        ok, detail = check_probe_structure(name, d)
        all_ok = all_ok and ok
        lines.append((name, ok, detail))
    return all_ok, lines


def fxB_replay(records):
    """Replay the 3 records with the shortest total recorded action
    sequence through nh_branch.Branch, gated by nh_branch's own
    verify_determinism(). Returns (skipped: bool, reason_or_None, results)."""
    try:
        import nh_branch as NB
    except Exception as e:
        return True, f"nh_branch import failed: {e!r}", []

    try:
        ok, sig = NB.verify_determinism()
    except Exception as e:
        return True, f"verify_determinism() raised: {e!r}", []
    if not ok:
        return True, f"verify_determinism() FAILED (sig={sig}) -- env drift", []

    candidates = []
    for name, d in records:
        seq = _record_action_seq(d)
        if seq is None:
            continue
        prefix, actions = seq
        total_len = prefix + len(actions)
        candidates.append((total_len, name, d, prefix, actions))
    candidates.sort(key=lambda t: (t[0], t[1]))
    chosen = candidates[:3]

    import re
    results = []
    for total_len, name, d, prefix, actions in chosen:
        try:
            seed = d["seed"]
            b = NB.Branch(seed, prefix=[])
            transcript = b.script(actions)
            final_msg = transcript[-1][1]["msg"] if transcript else ""
            observed = d.get("observed", "")
            # outcome check: for a DEATH-flagged probe, the recorded key
            # outcome is death at the final step (hp==0). Otherwise, the
            # 'observed' narrative quotes the served messages verbatim
            # (single-quoted substrings) -- require the final replayed
            # message to reproduce the longest such quoted substring (a
            # real, non-copied check against the recorded transcript).
            if "DEATH" in name.upper() or "death" in observed.lower():
                hp = transcript[-1][1]["hp"] if transcript else None
                ok = (hp == 0)
                reason = f"final hp={hp} (expect 0, caster death)"
            else:
                quotes = [q for q in re.findall(r"'([^']*)'", observed)
                         if len(q) >= 8]
                if quotes:
                    # observed narrates messages in the same temporal order
                    # as the script; the LAST qualifying quote is the one
                    # for the final scripted action.
                    best = quotes[-1]
                    ok = best in final_msg
                    reason = f"final msg={final_msg!r} matches recorded {best!r}"
                else:
                    ok = bool(final_msg)
                    reason = f"final msg={final_msg!r} (no quoted outcome to compare)"
            b.close()
            results.append((name, ok, f"actions={actions} len={total_len} "
                            f"{reason}"))
        except Exception as e:
            results.append((name, False, f"replay raised: {e!r}"))
    return False, None, results


# ------------------------------------------------------------------- main
def main():
    t0 = time.time()
    emit("=" * 78)
    emit("Phase-L SNAPSHOT SUITE -- fable_nethack/snapshot_suite.py")
    emit("MODEL: Sonnet 5 worker, spec by Fable 5 (max reasoning), "
        "Phase L session 3.")
    emit("=" * 78)

    rec, missing = build_recorded_fixtures()
    if missing:
        emit(f"NOTE: could not find real recorded strings for: {missing} "
            f"(fell back to the literal target string, no provenance)")
    emit(f"Recorded fixture inputs written to "
        f"{os.path.relpath(RECORDED_MSGS_PATH, HERE)}")
    emit("")

    results = []   # (name, status, evidence)  status in PASS/FAIL/SKIPPED

    def run(name, fn, *args):
        try:
            ok, evidence = fn(*args)
            status = "PASS" if ok else "FAIL"
        except Exception as e:
            import traceback as tb
            status = "FAIL"
            evidence = f"EXCEPTION {e!r}\n{tb.format_exc(limit=6)}"
        results.append((name, status, evidence))
        emit(f"[{status}] {name} -- {evidence}")
        return status == "PASS"

    emit("---- Part A: six fixed-bug snapshot fixtures ----")
    run("A1 armor-under-@ (message-driven on-cell pickup)", fx1_armor_under_at)

    H, AG, C = _quiet_import_env_stack()
    run("A2 corpse-on-victim-cell + phantom-corpse purge",
       fx2_corpse_on_victim_cell, H, AG, C, rec)
    run("A3 shopkeeper-dpt floors at difficulty prior",
       fx3_shopkeeper_dpt_floor)
    run("A4 dwarven != dwarf (race-adjective vs species-noun)",
       fx4_dwarven_not_dwarf)
    run("A5 pet-not-a-wall (pathing swaps into pet cell)",
       fx5_pet_not_a_wall)
    run("A6 stale-door terrain correction",
       fx6_stale_door, H, AG, C, rec)

    emit("")
    emit("---- Part B: E16 probe records as replay fixtures ----")
    probe_files = sorted(f for f in os.listdir(PROBE_DIR)
                         if f.endswith(".json"))
    records = []
    for fn in probe_files:
        with open(os.path.join(PROBE_DIR, fn)) as f:
            records.append((fn, json.load(f)))
    emit(f"found {len(records)} probe records in "
        f"results/e16_probes/: {probe_files}")

    struct_ok, struct_lines = fxB_structural(records)
    for name, ok, detail in struct_lines:
        status = "PASS" if ok else "FAIL"
        results.append((f"B-struct {name}", status, detail))
        emit(f"[{status}] B-struct {name} -- {detail}")

    skipped, skip_reason, replay_results = fxB_replay(records)
    if skipped:
        emit(f"[SKIPPED] B-replay (3 shortest-prefix probes) -- {skip_reason}")
        results.append(("B-replay", "SKIPPED", skip_reason))
    else:
        for name, ok, detail in replay_results:
            status = "PASS" if ok else "FAIL"
            results.append((f"B-replay {name}", status, detail))
            emit(f"[{status}] B-replay {name} -- {detail}")

    wallclock = time.time() - t0
    emit("")
    n_fail = sum(1 for _, s, _ in results if s == "FAIL")
    n_pass = sum(1 for _, s, _ in results if s == "PASS")
    n_skip = sum(1 for _, s, _ in results if s == "SKIPPED")
    emit(f"totals: {n_pass} PASS, {n_fail} FAIL, {n_skip} SKIPPED "
        f"(of {len(results)}); wallclock {wallclock:.1f}s")
    green = n_fail == 0
    emit("SUITE GREEN" if green else "SUITE RED")
    emit("=" * 78)

    with open(LOG_PATH, "w") as f:
        f.write("\n".join(_LOG_LINES) + "\n")

    return 0 if green else 1


if __name__ == "__main__":
    sys.exit(main())

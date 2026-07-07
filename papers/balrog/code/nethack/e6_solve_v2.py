"""E-NH6 gym SOLVE LOOP v2 — the RICH escape menu + in-model Monte Carlo.

MODEL: claude-opus-4-8[1m] (max thinking), Phase L session 5.

v1 (Fable 5, s3) proved that a mere REST/RETREAT menu resolves ~55% of
TRASH deaths as MISPLAYED, but honestly could NOT stamp the residual
UNRESOLVED set as UNWINNABLE — the s4 REST-lever paired block then died on
exactly that residue: fatal TRASH deaths carry a SAME-SPEED hostile
ADJACENT, where stand-and-heal (`_rest_here_ok` blocks it) and the
crisis-flee threshold (`_flee` refuses a non-slower mover) both fail. The
lesson logged repeatedly (NH_E15 L2, REPEAT-1, the REST lever): the fix for
an adjacent-combat death is a NEW ACTION, not a new number.

v2 supplies the new actions as scripted ALTERNATIVE POLICIES driven off the
agent's own perception (a fresh C.Atlas fed the branch's served obs — clean
protocol, no env internals):

  REST     (v1) stand + search at the branch point (control-of-controls)
  RETREAT  (v1) invert the last logged moves, then rest
  KITE     RELAXED directional disengage — step to the neighbour that
           minimises adjacency / maximises min-distance to mobile hostiles,
           WITHOUT `_flee`'s slower-only + full-disengage gates (the exact
           two gates the s4 diagnosis blamed). Tests "movement-disengage was
           available; the shipped flee gate was too conservative."
  THROW    back-and-throw: hurl carried ammo (dagger/dart/arrow/...) at the
           nearest hostile on a clear straight ray; kite when no line. Tests
           "ranged damage kills the same-speed pursuer before it kills us."
  STAIRS   BFS to the nearest known stairs (down/hole preferred for descent,
           else up) and take them — LEAVE THE LEVEL, dropping the adjacent
           hostile entirely. Tests "the exit was reachable."

Verdict (v2 semantics, supersedes v1 UNRESOLVED for adjudicated scenarios):
  MISPLAYED    a named alternative survives to death_time + WINDOW (game
               turns) OR changes level (escape) — a strictly better line
               existed in the agent's own information state; winner + backoff
               recorded.
  UNWINNABLE   NO named alternative survives AND an in-model MONTE CARLO
               (K randomised escape rollouts, seeded + recorded) also fully
               dies — alternatives + MC agree the death was locked in. This
               is the claim v1 deliberately withheld; v2 issues it only after
               the MC search fails.
  UNRESOLVED   reserved fallback (MC skipped, e.g. --no-mc); not issued by a
               full v2 run.
  REPLAY-DIVERGED  ORIG control unexpectedly survived; scenario dropped.

MC-win is folded into MISPLAYED with winner tag "MC:<line>" (an escape
exists but not via one clean named rule — still proves the death avoidable).

Class solve rule (exit criterion ii): a rule candidate solves the class when
the SAME named line wins >=3 instances on >=3 distinct seeds; it graduates
to a paired dev block as a lever.

Usage:
  python3 e6_solve_v2.py --class TRASH --labels devb1 --max 12 \
      [--only-unresolved results/e6_solve_trash.json] \
      [--backoff 40] [--window 600] [--mc 20] [--mc-budget 250] [--out ...]

Dev/gym seeds only — nh_branch.assert_dev_seed guards every replay.
"""

import argparse
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(HERE, "pylib"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

RESULTS = os.path.join(HERE, "results")

INV = {"north": "south", "south": "north", "east": "west",
       "west": "east", "northeast": "southwest",
       "southwest": "northeast", "northwest": "southeast",
       "southeast": "northwest"}
MOVES = set(INV)

MODEL = "claude-opus-4-8[1m] (max thinking), s5"


# --------------------------------------------------------------- perception
def _sign(v):
    return (v > 0) - (v < 0)


def _mobiles(A):
    import nh_common as C
    L = A.level
    return [m for m in L.monsters
            if not m.pet and m.name not in C.IMMOBILE
            and m.pos not in L.no_attack]


def throwable_letter(obs):
    import nh_common as C
    for letter, desc, oc in C.inventory(obs):
        d = desc.lower()
        if "weapon in hand" in d or "weapons in hands" in d or \
                ("wielded" in d and "not wielded" not in d):
            continue
        if any(k in d for k in ("dagger", "dart", "arrow", "spear",
                                "shuriken", "rock", "aklys", "javelin",
                                "knife", "bolt")):
            return letter
    return None


def _ray_clear(L, ax, ay, m):
    """Straight-line clear ray from us to monster m (for a thrown item)."""
    dx, dy = m.x - ax, m.y - ay
    if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
        return None
    dist = max(abs(dx), abs(dy))
    if dist < 1 or dist > 7:
        return None
    sx, sy = _sign(dx), _sign(dy)
    cx, cy = ax + sx, ay + sy
    while (cx, cy) != (m.x, m.y):
        if not L.passable(cx, cy, bad_traps_ok=True) or \
                any(mm.pos == (cx, cy) for mm in L.monsters):
            return None
        cx, cy = cx + sx, cy + sy
    from nh_common import DIR_OF
    return DIR_OF[(sx, sy)], dist


# ------------------------------------------------------------ named policies
def pol_kite(A, obs, ps):
    """Relaxed disengage: no slower-only / full-disengage gate."""
    L = A.level
    ax, ay = A.agent
    mob = _mobiles(A)
    if not mob:
        return ["search"]                 # safe -> heal
    best = None
    prev = ps.get("kdir")
    for name, (nx, ny) in L.neighbors(ax, ay):
        if any(m.x == nx and m.y == ny for m in L.monsters):
            continue
        d = min(max(abs(m.x - nx), abs(m.y - ny)) for m in mob)
        adj = sum(1 for m in mob if max(abs(m.x - nx), abs(m.y - ny)) <= 1)
        sticky = 0 if name == prev else 1
        key = (adj, -d, sticky)
        if best is None or key < best[0]:
            best = (key, name)
    if best is None:
        return ["search"]                 # boxed in
    ps["kdir"] = best[1]
    return [best[1]]


def _doorways(L, ps):
    """Cached set of KNOWN open-door / doorway cells (the diagonal-restricted
    chokepoints). NLE enforces `no diagonal move into/out of a doorway` for BOTH
    the player and monsters (nh_common.neighbors lines 366-370) — so routing a
    same-speed pursuer through a door forces it onto an orthogonal step it would
    otherwise cut diagonally, donating it a move and opening a gap."""
    import nh_common as C
    doors = ps.get("_doors")
    if doors is None:
        doors = set(L.find_terrain(C.DOORWAY)) | set(L.find_terrain(C.DOOR_OPEN))
        ps["_doors"] = doors
    return doors


def pol_door_kite(A, obs, ps):
    """DOOR-DIAGONAL KITE (wiki Standard_strategy): relaxed disengage that,
    among the SAFEST steps (fewest adjacencies preserved as the primary gate,
    identical to pol_kite), biases the flee toward / through a known doorway.
    A same-speed pursuer cannot follow diagonally through the door, so it eats
    an orthogonal penalty and loses ground. Reduces to pol_kite's behaviour when
    no door is known (door term is constant), so the KITE-vs-DOOR_KITE self-play
    delta isolates exactly the door-routing contribution.
    insight-origin: OP via READ-WIKI (Standard_strategy); mechanism BORROW-FIELD.
    """
    L = A.level
    ax, ay = A.agent
    mob = _mobiles(A)
    if not mob:
        return ["search"]                 # safe -> heal
    doors = _doorways(L, ps)

    def door_dist(cx, cy):
        if not doors:
            return 0
        return min(max(abs(cx - dx), abs(cy - dy)) for dx, dy in doors)

    best = None
    prev = ps.get("kdir")
    for name, (nx, ny) in L.neighbors(ax, ay):
        if any(m.x == nx and m.y == ny for m in L.monsters):
            continue
        d = min(max(abs(m.x - nx), abs(m.y - ny)) for m in mob)
        adj = sum(1 for m in mob if max(abs(m.x - nx), abs(m.y - ny)) <= 1)
        on_door = 0 if (nx, ny) in doors else 1     # step ONTO a door choke
        dd = door_dist(nx, ny)                       # else route toward one
        sticky = 0 if name == prev else 1
        # SAFETY primary (adj) == pol_kite; then seek the door choke; then keep
        # distance (-d); then momentum. Door-seeking sits ABOVE raw distance-max
        # so the flee will accept a slightly-closer step to reach the door.
        key = (adj, on_door, dd, -d, sticky)
        if best is None or key < best[0]:
            best = (key, name)
    if best is None:
        return ["search"]                 # boxed in
    ps["kdir"] = best[1]
    return [best[1]]


def pol_door_kite_tb(A, obs, ps):
    """DOOR-KITE variant B: door-proximity as a FREE TIEBREAKER only. Identical
    safety (adj) AND distance-max (-d) gates to pol_kite; the door term breaks
    ties among equally-safe, equally-distant steps (routes through the choke
    only when it costs no ground). Fair test of 'the door tactic helps when it
    is free' — isolates door-routing from the distance sacrifice that variant A
    (pol_door_kite) pays to reach the door."""
    L = A.level
    ax, ay = A.agent
    mob = _mobiles(A)
    if not mob:
        return ["search"]
    doors = _doorways(L, ps)

    def door_dist(cx, cy):
        if not doors:
            return 0
        return min(max(abs(cx - dx), abs(cy - dy)) for dx, dy in doors)

    best = None
    prev = ps.get("kdir")
    for name, (nx, ny) in L.neighbors(ax, ay):
        if any(m.x == nx and m.y == ny for m in L.monsters):
            continue
        d = min(max(abs(m.x - nx), abs(m.y - ny)) for m in mob)
        adj = sum(1 for m in mob if max(abs(m.x - nx), abs(m.y - ny)) <= 1)
        on_door = 0 if (nx, ny) in doors else 1
        dd = door_dist(nx, ny)
        sticky = 0 if name == prev else 1
        # distance-max (-d) stays PRIMARY (== pol_kite); door only breaks ties
        key = (adj, -d, on_door, dd, sticky)
        if best is None or key < best[0]:
            best = (key, name)
    if best is None:
        return ["search"]
    ps["kdir"] = best[1]
    return [best[1]]


def pol_throw(A, obs, ps):
    """Hurl ammo at nearest in-line hostile; kite when no clean line."""
    letter = throwable_letter(obs)
    if not letter:
        return pol_kite(A, obs, ps)
    L = A.level
    ax, ay = A.agent
    cands = []
    for m in _mobiles(A):
        r = _ray_clear(L, ax, ay, m)
        if r is not None:
            cands.append((r[1], r[0]))    # (dist, dirname)
    if not cands:
        return pol_kite(A, obs, ps)       # reposition to open a line
    cands.sort()
    return ["throw", letter, cands[0][1]]


def pol_stairs(A, obs, ps):
    """Path to nearest known stairs/hole and take them — leave the level."""
    L = A.level
    if A.agent in L.stairs_down or A.agent in L.holes:
        return ["down"]
    if A.agent in L.stairs_up:
        return ["up"]
    goals = set(L.stairs_down) | set(L.holes)
    if not goals:
        goals = set(L.stairs_up)
    if not goals:
        return pol_kite(A, obs, ps)       # nothing known -> buy time
    mcells = {m.pos for m in L.monsters if not m.pet}
    path = L.bfs(A.agent, goals, avoid=mcells)
    if path is None:
        path = L.bfs(A.agent, goals)      # blocked -> accept a bump-through
    if not path:
        return pol_kite(A, obs, ps)
    return [path[0]]


def pol_mc(A, obs, ps):
    """One randomised escape step (in-model Monte Carlo)."""
    rng = ps["rng"]
    L = A.level
    ax, ay = A.agent
    mob = _mobiles(A)
    roll = rng.random()
    if roll < 0.35:
        letter = throwable_letter(obs)
        if letter:
            cands = []
            for m in mob:
                r = _ray_clear(L, ax, ay, m)
                if r is not None:
                    cands.append((r[1], r[0]))
            if cands:
                cands.sort()
                return ["throw", letter, cands[0][1]]
    if roll < 0.65:
        s = pol_stairs(A, obs, {})
        if s and s[0] in ("up", "down") or (s and s[0] in MOVES):
            return s
    if mob:
        opts = []
        for name, (nx, ny) in L.neighbors(ax, ay):
            if any(m.x == nx and m.y == ny for m in L.monsters):
                continue
            d = min(max(abs(m.x - nx), abs(m.y - ny)) for m in mob)
            opts.append((d, name))
        if opts:
            maxd = max(o[0] for o in opts)
            top = [n for d, n in opts if d >= maxd - 1]
            return [rng.choice(top)]
    return ["search"]


NAMED = [("KITE", pol_kite), ("THROW", pol_throw), ("STAIRS", pol_stairs)]


# ------------------------------------------------------------------- driver
def logged_actions(transitions_file):
    import nh_transitions as T
    from nle import nethack as nh
    g = T.read_episode(os.path.join(RESULTS, transitions_file))
    next(g)
    acts, hps, times, depths = [], [], [], []
    for row in g:
        if "action" not in row:
            continue
        acts.append(row["action"])
        o = row["obs"]
        bl = o["obs"]["blstats"] if "obs" in o else o["blstats"]
        hps.append(int(bl[nh.NLE_BL_HP]))
        times.append(int(bl[nh.NLE_BL_TIME]))
        depths.append(int(bl[nh.NLE_BL_DEPTH]))
    return acts, hps, times, depths


def run_script(branch, script, stop_time):
    """v1-identical fixed-script runner (REST/RETREAT + ORIG control)."""
    from nle import nethack as nh
    alive, t, hp, steps = True, None, None, 0
    for a in script:
        _, done = branch.step(a)
        steps += 1
        bl = branch.obs["obs"]["blstats"]
        hp = int(bl[nh.NLE_BL_HP])
        t = int(bl[nh.NLE_BL_TIME])
        if done or hp <= 0:
            alive = False
            break
        if t >= stop_time:
            break
    return {"alive": alive, "time": t, "hp": hp, "steps": steps}


def run_policy(seed, prefix, policy, ps, stop_time, budget, start_depth):
    """Perception-driven policy runner. Reports level-escape as evidence."""
    import nh_branch as B
    import nh_common as C
    from nle import nethack as nh
    br = B.Branch(seed, tuple(prefix))
    A = C.Atlas()
    alive, t, hp, steps, escaped, maxd = True, None, None, 0, False, start_depth
    while steps < budget:
        A.update(br.obs)
        if A.depth != start_depth:
            escaped = True
        maxd = max(maxd, A.depth)
        acts = policy(A, br.obs, ps) or ["search"]
        broke = False
        for a in acts:
            _, done = br.step(a)
            steps += 1
            bl = br.obs["obs"]["blstats"]
            hp = int(bl[nh.NLE_BL_HP])
            t = int(bl[nh.NLE_BL_TIME])
            if done or hp <= 0:
                alive, broke = False, True
                break
            if t >= stop_time:
                broke = True
                break
        if broke or not alive or (t is not None and t >= stop_time):
            break
    br.close()
    return {"alive": alive, "time": t, "hp": hp, "steps": steps,
            "escaped": escaped, "max_depth": maxd}


def solve_one(sc, backoffs, window, mc_n, mc_budget, retreat_n=8,
              rest_budget=400):
    """Try the escape menu at each backoff (deeper = more runway); MISPLAYED
    on the first backoff that yields a survivor; only after ALL backoffs fail
    does the in-model MC run (at the deepest backoff) and gate UNWINNABLE."""
    import nh_branch as B
    if isinstance(backoffs, int):
        backoffs = [backoffs]
    seed = sc["seed"]
    B.assert_dev_seed(seed)
    acts, hps, times, depths = logged_actions(sc["transitions_file"])
    n = len(acts)
    death_t = max(times) if times else 0
    start_depth = max(depths) if depths else 1
    stop_time = death_t + window
    out = {"id": sc["id"], "seed": seed, "role": sc.get("role"),
           "depth_at_death": start_depth, "end_reason": sc.get("end_reason"),
           "n_steps": n, "death_time": death_t, "window": window,
           "backoffs": {}}
    orig_checked = False

    for backoff in backoffs:
        cut = max(1, n - backoff)
        prefix = acts[:cut]
        lines = {}
        if not orig_checked:
            br = B.Branch(seed, tuple(prefix))
            orig = run_script(br, acts[cut:] + ["search"] * 50, stop_time)
            br.close()
            lines["ORIG"] = orig
            if orig["alive"]:
                out["verdict"] = "REPLAY-DIVERGED"
                out["backoffs"][str(backoff)] = lines
                return out
            orig_checked = True

        # REST + RETREAT (v1 fixed scripts, kept for continuity)
        br = B.Branch(seed, tuple(prefix))
        lines["REST"] = run_script(br, ["search"] * rest_budget, stop_time)
        br.close()
        back = []
        for a in reversed(prefix[-60:]):
            if a in MOVES:
                back.append(INV[a])
            if len(back) >= retreat_n:
                break
        br = B.Branch(seed, tuple(prefix))
        lines["RETREAT"] = run_script(br, back + ["search"] * rest_budget,
                                      stop_time)
        br.close()
        # v2 perception-driven named policies
        for name, pol in NAMED:
            lines[name] = run_policy(seed, prefix, pol, {}, stop_time,
                                     rest_budget, start_depth)
        out["backoffs"][str(backoff)] = lines

        winners = [k for k, v in lines.items()
                   if k != "ORIG" and v["alive"]]
        if winners:
            out["verdict"] = "MISPLAYED"
            out["winners"] = winners
            out["winning_backoff"] = backoff
            out["escapes"] = [k for k in winners
                              if lines[k].get("escaped")]
            return out

    # in-model Monte Carlo (deepest backoff = most runway) before UNWINNABLE
    if mc_n > 0:
        deep = max(backoffs)
        prefix = acts[:max(1, n - deep)]
        mc_survivors = []
        for i in range(mc_n):
            ps = {"rng": random.Random(1000 + i)}
            r = run_policy(seed, prefix, pol_mc, ps, stop_time, mc_budget,
                           start_depth)
            if r["alive"]:
                mc_survivors.append({"roll": i, **r})
                if len(mc_survivors) >= 3:
                    break
        out["mc"] = {"n": mc_n, "backoff": deep,
                     "survivors": len(mc_survivors), "detail": mc_survivors}
        if mc_survivors:
            out["verdict"] = "MISPLAYED"
            out["winners"] = ["MC"]
            out["winning_backoff"] = deep
            return out
        out["verdict"] = "UNWINNABLE"
        out["winners"] = []
        return out

    out["verdict"] = "UNRESOLVED"
    out["winners"] = []
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="cls", default="TRASH")
    ap.add_argument("--labels", default="")
    ap.add_argument("--max", type=int, default=12)
    ap.add_argument("--backoffs", default="40,120,300",
                    help="comma list; escape menu tried at each, deeper "
                         "gives more runway")
    ap.add_argument("--window", type=int, default=600)
    ap.add_argument("--mc", type=int, default=20)
    ap.add_argument("--mc-budget", dest="mc_budget", type=int, default=250)
    ap.add_argument("--only-unresolved", default=None,
                    help="path to a v1 result json; restrict to its "
                         "UNRESOLVED seeds")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    import nh_branch as B

    only = None
    if args.only_unresolved:
        v1 = json.load(open(args.only_unresolved))
        only = {r["seed"] for r in v1["results"]
                if r.get("verdict") == "UNRESOLVED"}
        print(f"restricting to {len(only)} UNRESOLVED seeds: {sorted(only)}")

    lib = json.load(open(os.path.join(RESULTS, "e6_scenarios.json")))
    want = set(args.labels.split(",")) if args.labels else None
    todo, seen = [], set()
    for sc in lib["scenarios"]:
        if sc["class"] != args.cls or not sc.get("branchable"):
            continue
        if want and sc["label"] not in want:
            continue
        if only is not None and sc["seed"] not in only:
            continue
        try:
            B.assert_dev_seed(sc["seed"])
        except ValueError:
            continue
        if sc["seed"] in seen:
            continue
        if not os.path.exists(os.path.join(RESULTS, sc["transitions_file"])):
            continue
        seen.add(sc["seed"])
        todo.append(sc)
        if len(todo) >= args.max:
            break

    backoffs = [int(b) for b in args.backoffs.split(",")]
    print(f"solve v2: {len(todo)} {args.cls} scenarios, backoffs "
          f"{backoffs}, window {args.window}, MC {args.mc}x{args.mc_budget}")
    results = []
    for sc in todo:
        t0 = time.time()
        try:
            r = solve_one(sc, backoffs, args.window, args.mc,
                          args.mc_budget)
        except Exception as e:  # noqa: BLE001
            import traceback
            r = {"id": sc["id"], "seed": sc["seed"], "verdict": "ERROR",
                 "error": repr(e)[:200], "tb": traceback.format_exc()[-400:]}
        r["wall_s"] = round(time.time() - t0, 1)
        results.append(r)
        print(f"  {r['id']}: {r.get('verdict')} "
              f"winners={r.get('winners', [])} "
              f"mc={r.get('mc', {}).get('survivors', '-')} "
              f"({r['wall_s']}s)", flush=True)

    from collections import Counter
    verd = Counter(r.get("verdict") for r in results)
    win_by = Counter(w for r in results for w in r.get("winners", []))
    doc = {"model": MODEL, "class": args.cls, "backoffs": backoffs,
           "window": args.window, "mc": args.mc, "mc_budget": args.mc_budget,
           "verdicts": dict(verd), "wins_by_line": dict(win_by),
           "results": results}
    out = args.out or os.path.join(RESULTS,
                                   f"e6_solve_v2_{args.cls.lower()}.json")
    json.dump(doc, open(out, "w"), indent=1)
    print(f"verdicts: {dict(verd)}  wins_by_line: {dict(win_by)}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

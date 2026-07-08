"""NH-E36 SCENARIO STRATEGY SYNTHESIS — simulate + rank (steps 3 of the pipeline).

MODEL: claude-opus-4-8 (max thinking), Phase L / NH-E36 lead.

Runs EVERY candidate strategy (e36_candidates.REGISTRY) against a HARD-scenario
death corpus via deterministic branch replay (nh_branch — clean protocol, served
obs only, dev/gym seeds only). For each scenario we branch the agent's own
trajectory at a backoff before death (runway) and let each candidate policy take
over from the agent's exact information state; we score SURVIVAL (alive at
death_time+window) + ESCAPE (level change) + depth-gain.

ROBUST ranking (the loot-lever 2-seed mirage is the cautionary tale): every
candidate is scored across MANY distinct seeds; a candidate "solves the class"
only if the SAME line survives >=3 instances on >=3 distinct seeds. Head-to-head
vs KITE (the shipped hand-designed disengage lever) is reported explicitly — the
question is whether a SYNTHESIZED strategy beats the hand-designed one.

OPS: BLOCKING, in-process, ONE env per seed (reused across candidates), per-item
wall-timeout. Run in seed-chunks (each chunk one Bash call), append to JSONL,
then --aggregate. No detached processes, no background monitors.

Usage:
  python3 e36_simulate.py --seeds 706,712,727 --backoff 120 --window 500 \
      --budget 400 --out results/e36_trash.jsonl
  python3 e36_simulate.py --aggregate results/e36_trash.jsonl
"""

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(HERE, "pylib"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

RESULTS = os.path.join(HERE, "results")
MODEL = "claude-opus-4-8 (max thinking), NH-E36"


def _load_scenarios(cls="TRASH"):
    lib = json.load(open(os.path.join(RESULTS, "e6_scenarios.json")))
    import nh_branch as B
    by_seed = {}
    for sc in lib["scenarios"]:
        if sc["class"] != cls or not sc.get("branchable"):
            continue
        s = sc["seed"]
        try:
            B.assert_dev_seed(s)
        except ValueError:
            continue
        if s in by_seed:
            continue
        if not os.path.exists(os.path.join(RESULTS, sc["transitions_file"])):
            continue
        by_seed[s] = sc
    return by_seed


def _run_policy(seed, prefix, policy, stop_time, budget,
                start_depth, max_wall=60.0):
    """FRESH env per call (the e6_solve_v2-proven pattern — NLE cannot be
    cleanly reused across a terminal death within one object): reset ->
    replay prefix -> hand control to `policy`. Returns survival/escape metrics."""
    import nh_branch as B
    import nh_common as C
    from nle import nethack as nh
    br = B.Branch(seed, tuple(prefix))            # fresh env, resets + replays
    A = C.Atlas()
    ps = {}
    import random as _r
    ps["rng"] = _r.Random(20260708)
    alive, t, hp, steps, escaped, maxd = True, None, None, 0, False, start_depth
    t0 = time.time()
    timed_out = False
    while steps < budget:
        if time.time() - t0 > max_wall:
            timed_out = True
            break
        A.update(br.obs)
        if A.depth != start_depth:
            escaped = True
        maxd = max(maxd, A.depth)
        try:
            acts = policy(A, br.obs, ps) or ["search"]
        except Exception:               # a policy that faults loses the round
            acts = ["search"]
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
    return {"alive": bool(alive), "escaped": bool(escaped), "hp": hp,
            "time": t, "steps": steps, "max_depth": maxd,
            "depth_gain": maxd - start_depth, "timed_out": timed_out}


def _run_orig(seed, prefix, tail, stop_time, max_wall=60.0):
    import nh_branch as B
    from nle import nethack as nh
    br = B.Branch(seed, tuple(prefix))            # fresh env
    alive, t, hp = True, None, None
    t0 = time.time()
    for a in tail:
        if time.time() - t0 > max_wall:
            break
        _, done = br.step(a)
        bl = br.obs["obs"]["blstats"]
        hp = int(bl[nh.NLE_BL_HP])
        t = int(bl[nh.NLE_BL_TIME])
        if done or hp <= 0:
            alive = False
            break
        if t >= stop_time:
            break
    br.close()
    return {"alive": bool(alive), "hp": hp, "time": t}


def run_seed(sc, backoff, window, budget):
    from e6_solve_v2 import logged_actions
    from e36_candidates import REGISTRY
    seed = sc["seed"]
    acts, hps, times, depths = logged_actions(sc["transitions_file"])
    n = len(acts)
    death_t = max(times) if times else 0
    stop_time = death_t + window
    cut = max(1, n - backoff)
    # start_depth = depth at the BRANCH POINT (where the policy takes over);
    # anchors escape (level-change) + depth-gain. Terminal rows log depth 0, so
    # never use depths[-1]; take the last valid depth at/near the cut.
    valid = [d for d in depths[:cut] if d > 0]
    start_depth = valid[-1] if valid else (max([d for d in depths if d > 0],
                                               default=1))
    prefix = acts[:cut]
    tail = acts[cut:] + ["search"] * 50

    orig = _run_orig(seed, prefix, tail, stop_time)
    if orig["alive"]:
        return {"seed": seed, "role": sc.get("role"),
                "verdict": "REPLAY-DIVERGED", "orig": orig,
                "start_depth": start_depth, "death_time": death_t}
    cand = {}
    for name, pol, prio, tag, prov in REGISTRY:
        t0 = time.time()
        try:
            r = _run_policy(seed, prefix, pol, stop_time, budget, start_depth)
        except Exception as e:          # noqa: BLE001
            r = {"alive": False, "escaped": False, "error": repr(e)[:160]}
        r["wall_s"] = round(time.time() - t0, 1)
        r["tag"] = tag
        r["prov"] = prov
        cand[name] = r

    survivors = [k for k, v in cand.items() if v.get("alive")]
    return {"seed": seed, "role": sc.get("role"), "verdict": "ADJUDICATED",
            "start_depth": start_depth, "death_time": death_t,
            "n_steps": n, "backoff": backoff, "window": window,
            "budget": budget, "orig": orig, "survivors": survivors,
            "candidates": cand}


def aggregate(path):
    from e36_candidates import REGISTRY
    rows = [json.loads(l) for l in open(path) if l.strip()]
    adj = [r for r in rows if r.get("verdict") == "ADJUDICATED"]
    div = [r for r in rows if r.get("verdict") == "REPLAY-DIVERGED"]
    names = [r[0] for r in REGISTRY]
    meta = {r[0]: (r[2], r[3], r[4]) for r in REGISTRY}
    N = len(adj)
    stats = {}
    for name in names:
        surv = [r for r in adj if r["candidates"].get(name, {}).get("alive")]
        esc = [r for r in adj if r["candidates"].get(name, {}).get("escaped")]
        seeds_won = sorted({r["seed"] for r in surv})
        gains = [r["candidates"][name].get("depth_gain", 0)
                 for r in adj if name in r["candidates"]]
        prio, tag, prov = meta[name]
        stats[name] = {
            "priority": prio, "tag": tag, "prov": prov,
            "survive": len(surv), "escape": len(esc), "N": N,
            "survival_rate": round(len(surv) / N, 3) if N else 0.0,
            "escape_rate": round(len(esc) / N, 3) if N else 0.0,
            "distinct_seeds_won": len(seeds_won),
            "mean_depth_gain": round(sum(gains) / len(gains), 3) if gains else 0.0,
            "class_solve": len(surv) >= 3 and len(seeds_won) >= 3,
            "seeds_won": seeds_won,
        }
    ranking = sorted(stats.items(),
                     key=lambda kv: (-kv[1]["survival_rate"],
                                     -kv[1]["escape_rate"], kv[1]["priority"]))
    kite = stats.get("KITE", {}).get("survival_rate", 0.0)
    doc = {"model": MODEL, "n_adjudicated": N, "n_replay_diverged": len(div),
           "kite_survival_rate": kite,
           "ranking": [{"name": k, **v} for k, v in ranking],
           "seeds": sorted(r["seed"] for r in adj)}
    print(f"\n=== NH-E36 RANKING  (N={N} adjudicated TRASH scenarios) ===")
    print(f"{'rank':>4} {'candidate':<16}{'prov':<14}{'surv':>6}{'esc':>6}"
          f"{'seeds':>6}{'dgain':>7}  solve")
    for i, (name, v) in enumerate(ranking, 1):
        print(f"{i:>4} {name:<16}{v['prov']:<14}"
              f"{v['survival_rate']:>6.2f}{v['escape_rate']:>6.2f}"
              f"{v['distinct_seeds_won']:>6}{v['mean_depth_gain']:>7.2f}"
              f"  {'YES' if v['class_solve'] else ''}")
    print(f"\nKITE (hand-designed incumbent) survival_rate = {kite:.2f}")
    winner = ranking[0]
    print(f"WINNER = {winner[0]} ({winner[1]['prov']}) "
          f"survival {winner[1]['survival_rate']:.2f} vs KITE {kite:.2f}  "
          f"Δ{winner[1]['survival_rate'] - kite:+.2f}")
    out = path.replace(".jsonl", "_ranking.json")
    json.dump(doc, open(out, "w"), indent=1)
    print(f"wrote {out}")
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="")
    ap.add_argument("--cls", default="TRASH")
    ap.add_argument("--backoff", type=int, default=120)
    ap.add_argument("--window", type=int, default=500)
    ap.add_argument("--budget", type=int, default=400)
    ap.add_argument("--out", default=os.path.join(RESULTS, "e36_trash.jsonl"))
    ap.add_argument("--aggregate", default=None)
    args = ap.parse_args()

    if args.aggregate:
        aggregate(args.aggregate)
        return

    by_seed = _load_scenarios(args.cls)
    want = [int(s) for s in args.seeds.split(",") if s.strip()]
    done = set()
    if os.path.exists(args.out):
        for l in open(args.out):
            if l.strip():
                done.add(json.loads(l)["seed"])
    todo = [s for s in want if s in by_seed and s not in done]
    print(f"e36 simulate: {len(todo)} seeds {todo} (skip done {sorted(done & set(want))}) "
          f"backoff={args.backoff} window={args.window} budget={args.budget}",
          flush=True)
    with open(args.out, "a") as f:
        for s in todo:
            t0 = time.time()
            try:
                rec = run_seed(by_seed[s], args.backoff, args.window, args.budget)
            except Exception as e:      # noqa: BLE001
                import traceback
                rec = {"seed": s, "verdict": "ERROR", "error": repr(e)[:200],
                       "tb": traceback.format_exc()[-500:]}
            rec["wall_s"] = round(time.time() - t0, 1)
            f.write(json.dumps(rec) + "\n")
            f.flush()
            v = rec.get("verdict")
            surv = rec.get("survivors", [])
            print(f"  seed {s} ({rec.get('role')}): {v} "
                  f"survivors={surv} ({rec['wall_s']}s)", flush=True)


if __name__ == "__main__":
    main()

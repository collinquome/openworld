"""E-NH6 gym SOLVE LOOP v1 — branch-explore alternatives at logged deaths.

MODEL: Fable 5 (max reasoning), Phase L session 3.

For a harvested scenario (results/e6_scenarios.json entry with a
dev-seed episode), reconstruct the pre-death state EXACTLY by replaying
the LOGGED action sequence through nh_branch's verified-deterministic
stack, then run scripted ALTERNATIVE lines from a branch point K steps
before the death and compare fates:

  ORIG     the logged line itself (control: must reproduce the death —
           per-scenario determinism check; if it does not, the scenario
           is stamped REPLAY-DIVERGED and dropped from verdicts)
  REST     stand ground and search/rest at the branch point (tests
           "engagement itself was the mistake / hp was recoverable")
  RETREAT  invert the last logged moves (walk back the way we came,
           up to RETREAT_N cells) then rest (tests "disengage-and-
           recover beats the fight" — the FLEE/TRASH matrix cell)

Verdict per scenario (pre-registered semantics, RUN_LOG s3):
  MISPLAYED   an alternative SURVIVES the death window (last nonzero
              logged game turn + WINDOW) — a strictly better line
              existed inside the agent's own information state;
              winning_backoff records how early the better decision
              had to be taken (decision depth of the error)
  UNRESOLVED  no scripted alternative survives; cheap menu exhausted —
              honestly NOT stamped UNWINNABLE (that claim needs the
              richer menu: kite/throw/stairs-escape, v2)
  UNWINNABLE  reserved: alternatives + in-model MC agree death was
              locked in (not issued by v1)

Class solve rule (exit criterion ii): a rule candidate "solves" the
class when the SAME alternative wins >=3 instances on >=3 distinct
seeds; that rule then graduates to a paired dev block as a lever.

Usage:
  python3 e6_solve.py --class TRASH --labels devb1 --max 12 \
      [--backoffs 40,120,300] [--window 600] [--out ...]

Dev/gym seeds only — nh_branch.assert_dev_seed guards every replay.
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

INV = {"north": "south", "south": "north", "east": "west",
       "west": "east", "northeast": "southwest",
       "southwest": "northeast", "northwest": "southeast",
       "southeast": "northwest"}
MOVES = set(INV)


def logged_actions(transitions_file):
    import nh_transitions as T
    fn = os.path.join(RESULTS, transitions_file)
    g = T.read_episode(fn)
    header = next(g)
    acts, hps, times, depths = [], [], [], []
    from nle import nethack as nh
    for row in g:
        if "action" not in row:      # initial-obs row carries no action
            continue
        acts.append(row["action"])
        o = row["obs"]
        bl = o["obs"]["blstats"] if "obs" in o else o["blstats"]
        hps.append(int(bl[nh.NLE_BL_HP]))
        times.append(int(bl[nh.NLE_BL_TIME]))
        depths.append(int(bl[nh.NLE_BL_DEPTH]))
    return header, acts, hps, times, depths


def run_line(branch, script, stop_time):
    """Feed `script`, tracking survival off the branch's live obs
    (Branch.step returns a brief; blstats live on branch.obs).
    Returns dict(alive, time, hp, steps_run)."""
    from nle import nethack as nh
    alive, t, hp = True, None, None
    steps = 0
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


def solve_one(sc, backoff, window, retreat_n=8, rest_budget=400):
    import nh_branch as B
    seed = sc["seed"]
    B.assert_dev_seed(seed)
    header, acts, hps, times, depths = logged_actions(
        sc["transitions_file"])
    n = len(acts)
    # terminal frame zeroes blstats (R_TERMINAL_ZERO) — death time is
    # the last NONZERO time, not times[-1]
    death_t = max(times) if times else 0
    out = {"id": sc["id"], "seed": seed, "role": sc.get("role"),
           "depth_at_death": max(depths) if depths else None,
           "end_reason": sc.get("end_reason"), "n_steps": n,
           "death_time": death_t, "window": window,
           "backoffs": {}, "lines": {}}
    stop_time = death_t + window

    orig_checked = False
    for backoff in ([backoff] if isinstance(backoff, int) else backoff):
        cut = max(1, n - backoff)
        prefix = acts[:cut]
        if not orig_checked:
            # ORIG control — replay the tail; must die again (a
            # surviving control = replay divergence, drop scenario)
            br = B.Branch(seed, prefix=tuple(prefix))
            orig = run_line(br, acts[cut:] + ["search"] * 50, stop_time)
            br.close()
            out["lines"]["ORIG"] = orig
            if orig["alive"]:
                out["verdict"] = "REPLAY-DIVERGED"
                return out
            orig_checked = True

        # REST — stand and search at the branch point
        br = B.Branch(seed, prefix=tuple(prefix))
        rest = run_line(br, ["search"] * rest_budget, stop_time)
        br.close()
        # RETREAT — invert last logged moves, then rest
        back = []
        for a in reversed(prefix[-60:]):
            if a in MOVES:
                back.append(INV[a])
            if len(back) >= retreat_n:
                break
        br = B.Branch(seed, prefix=tuple(prefix))
        retr = run_line(br, back + ["search"] * rest_budget, stop_time)
        br.close()
        out["backoffs"][str(backoff)] = {"REST": rest, "RETREAT": retr}
        winners = [k for k, v in (("REST", rest), ("RETREAT", retr))
                   if v["alive"]]
        if winners:
            out["verdict"] = "MISPLAYED"
            out["winners"] = winners
            out["winning_backoff"] = backoff
            return out
    out["verdict"] = "UNRESOLVED"
    out["winners"] = []
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="cls", default="TRASH")
    ap.add_argument("--labels", default="")
    ap.add_argument("--max", type=int, default=12)
    ap.add_argument("--backoffs", default="40,120,300")
    ap.add_argument("--window", type=int, default=600)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    import nh_branch as B

    lib = json.load(open(os.path.join(RESULTS, "e6_scenarios.json")))
    want_labels = set(args.labels.split(",")) if args.labels else None
    todo, seen_seeds = [], set()
    for sc in lib["scenarios"]:
        if sc["class"] != args.cls or not sc.get("branchable"):
            continue
        if want_labels and sc["label"] not in want_labels:
            continue
        try:
            B.assert_dev_seed(sc["seed"])
        except ValueError:
            continue
        if sc["seed"] in seen_seeds:      # 1 per seed: generalization
            continue                       # needs distinct seeds
        if not os.path.exists(os.path.join(RESULTS,
                                           sc["transitions_file"])):
            continue
        seen_seeds.add(sc["seed"])
        todo.append(sc)
        if len(todo) >= args.max:
            break

    print(f"solve loop: {len(todo)} {args.cls} scenarios "
          f"(distinct seeds), backoffs {args.backoffs}, "
          f"window {args.window}")
    results = []
    for sc in todo:
        t0 = time.time()
        try:
            r = solve_one(sc, [int(b) for b in
                                args.backoffs.split(",")], args.window)
        except Exception as e:  # noqa: BLE001 — batch must survive
            r = {"id": sc["id"], "seed": sc["seed"],
                 "verdict": "ERROR", "error": repr(e)[:200]}
        r["wall_s"] = round(time.time() - t0, 1)
        results.append(r)
        print(f"  {r['id']}: {r.get('verdict')} "
              f"winners={r.get('winners', [])} "
              f"({r['wall_s']}s)", flush=True)

    from collections import Counter
    verd = Counter(r.get("verdict") for r in results)
    win_by = Counter(w for r in results for w in r.get("winners", []))
    doc = {"model": "Fable 5 (max reasoning), s3", "class": args.cls,
           "backoffs": args.backoffs, "window": args.window,
           "verdicts": dict(verd), "wins_by_line": dict(win_by),
           "results": results}
    out = args.out or os.path.join(
        RESULTS, f"e6_solve_{args.cls.lower()}.json")
    json.dump(doc, open(out, "w"), indent=1)
    print(f"verdicts: {dict(verd)}  wins_by_line: {dict(win_by)}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

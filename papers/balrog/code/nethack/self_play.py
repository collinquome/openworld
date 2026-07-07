"""STRATEGIC SELF-PLAY on the trash-fight (operator directive, s6).
MODEL: claude-opus-4-8[1m] max thinking, Phase L session 6.

The ONE scoped target: the same-speed-adjacent D5-6 trash fight (the kill
zone THROW addresses). The CONSTRUCTED scenario = the deterministic branch
state at each residual TRASH pre-death point (e6_scenarios.json). SELF-PLAY =
for each scenario, search the escape-strategy space against the world model
and measure survival: fixed named strategies {KITE, THROW, STAIRS} (one
deterministic rollout each) vs an MC-SEARCH policy (pol_mc, K randomised
escape rollouts — imagination-training over the agent's own stochastic
strategy space). The converged strategy = argmax survival.

FIDELITY GUARD (state prominently): nh_branch replays the ACTUAL NLE, which
is deterministic given (seed, prefix, actions) — so combat dice are a SINGLE
sample per action-path; the MC search samples the AGENT policy (positioning /
action ordering), not the game RNG. This is high-fidelity-topology,
single-sample-combat imagination training. A strategy that wins in-model can
still be overfit to model quirks => EVERY self-play strategy is disposed by
the standard real-env PAIRED BLOCK (here: the s6 THROW block). The GAP
between in-model win and real-env delta is itself the reported finding.

Usage: python3 self_play.py [--k 30] [--seeds 707,714,727,732] [--out ...]
"""
import argparse
import json
import os
import random
import sys

import e6_solve_v2 as E

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
MODEL = "claude-opus-4-8[1m]"

# self-play strategy menu = the e6 named lines PLUS the s7 door-diagonal kite.
# DOOR_KITE is placed next to KITE so the paired KITE-vs-DOOR_KITE per-scenario
# outcome isolates the door-routing contribution (both share the safety gate).
NAMED_SP = [("KITE", E.pol_kite), ("DOOR_KITE", E.pol_door_kite),
            ("THROW", E.pol_throw), ("STAIRS", E.pol_stairs)]


def load_scenarios(seeds):
    lib = json.load(open(os.path.join(RESULTS, "e6_scenarios.json")))
    by = {}
    for sc in lib["scenarios"]:
        if sc.get("class") != "TRASH" or not sc.get("branchable"):
            continue
        if sc["seed"] in by:
            continue
        if not os.path.exists(os.path.join(RESULTS, sc["transitions_file"])):
            continue
        if seeds and sc["seed"] not in seeds:
            continue
        by[sc["seed"]] = sc
    return by


def selfplay_one(sc, k, backoff=120, window=600, budget=400):
    seed = sc["seed"]
    E.B_assert = getattr(E, "assert_dev_seed", None)
    acts, hps, times, depths = E.logged_actions(
        os.path.join(RESULTS, sc["transitions_file"]))
    n = len(acts)
    death_t = max(times) if times else 0
    start_depth = max(depths) if depths else 1
    stop_time = death_t + window
    prefix = acts[:max(1, n - backoff)]
    row = {"seed": seed, "role": sc.get("role"),
           "depth": start_depth, "named": {}}
    # fixed named strategies: one deterministic rollout each
    for name, pol in NAMED_SP:
        r = E.run_policy(seed, prefix, pol, {}, stop_time, budget, start_depth)
        row["named"][name] = {"alive": r["alive"], "escaped": r["escaped"],
                              "max_depth": r["max_depth"]}
    # MC-SEARCH: K randomised escape rollouts (imagination training)
    surv = esc = 0
    for i in range(k):
        ps = {"rng": random.Random(1000 + i)}
        r = E.run_policy(seed, prefix, E.pol_mc, ps, stop_time, budget,
                         start_depth)
        surv += int(r["alive"])
        esc += int(r["escaped"])
    row["mc_search"] = {"k": k, "survived": surv, "surv_rate": surv / k,
                        "escaped": esc}
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=30)
    ap.add_argument("--seeds", default="707,714,727,732")
    ap.add_argument("--backoff", type=int, default=120)
    ap.add_argument("--out", default=os.path.join(RESULTS, "self_play_trash.json"))
    args = ap.parse_args()
    seeds = {int(s) for s in args.seeds.split(",")} if args.seeds else None
    by = load_scenarios(seeds)
    print(f"self-play: {len(by)} trash-fight scenarios "
          f"seeds={sorted(by)} K={args.k} backoff={args.backoff}")
    rows = []
    agg = {n: {"alive": 0, "esc": 0} for n, _ in NAMED_SP}
    mc_rate_sum = 0.0
    for seed in sorted(by):
        row = selfplay_one(by[seed], args.k, backoff=args.backoff)
        rows.append(row)
        for n in agg:
            agg[n]["alive"] += int(row["named"][n]["alive"])
            agg[n]["esc"] += int(row["named"][n]["escaped"])
        mc_rate_sum += row["mc_search"]["surv_rate"]
        nm = " ".join(f"{n}={'S' if row['named'][n]['alive'] else '.'}"
                      for n, _ in NAMED_SP)
        print(f"  seed {seed:4d} {str(row['role'])[:9]:9} D{row['depth']}  "
              f"{nm}  MC={row['mc_search']['survived']}/{args.k} "
              f"({row['mc_search']['surv_rate']*100:.0f}%)", flush=True)
    ns = len(rows)
    print("\n=== in-model self-play survival on the trash-fight ===")
    for n, _ in NAMED_SP:
        print(f"  {n:7} survive {agg[n]['alive']}/{ns}  "
              f"escape {agg[n]['esc']}/{ns}")
    print(f"  MC-SEARCH mean survival {mc_rate_sum/ns*100:.1f}% "
          f"(over {args.k} rollouts/scenario)")
    doc = {"model": MODEL, "k": args.k, "backoff": args.backoff,
           "n_scenarios": ns, "named_agg": agg,
           "mc_search_mean_surv": mc_rate_sum / ns, "rows": rows}
    json.dump(doc, open(args.out, "w"), indent=1)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()

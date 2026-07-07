"""Frozen-block analysis: bootstrap CI, per-role stratified table,
variance decomposition (role lottery vs within-role), comparison line
vs leaderboard SOTA.

Usage: python3 c2_block_analysis.py 'results/nethack_results_c2block80_*.json'
"""

import glob
import json
import random
import sys
import collections

from bootstrap_ci import ci95   # canonical CI (harness-audit item 5)

SOTA = 6.8


def main():
    pat = sys.argv[1]
    eps = {}
    for fn in glob.glob(pat):
        for e in json.load(open(fn)).get("episodes", []):
            eps[e["seed"]] = e
    eps = [eps[s] for s in sorted(eps)]
    n = len(eps)
    scores = [e["progression"] * 100 for e in eps]
    mean = sum(scores) / n
    lo, hi = ci95(scores)
    # P(mean > SOTA) via the same canonical resampler
    rng = random.Random(20260706)
    boots = [sum(rng.choices(scores, k=n)) / n for _ in range(10000)]
    print(f"n={n} mean {mean:.2f} bootstrap95 [{lo:.2f}, {hi:.2f}]")
    print(f"CI low vs SOTA {SOTA}: {'BEAT' if lo > SOTA else 'no beat'} "
          f"(P(mean>SOTA)={sum(1 for b in boots if b > SOTA)/len(boots):.3f})")

    # per-role stratified
    byrole = collections.defaultdict(list)
    for e in eps:
        byrole[e.get("role") or "?"].append(e["progression"] * 100)
    print(f"\n{'role':14s} {'n':>3s} {'mean':>7s} {'sd':>6s} {'max':>6s}")
    grand = mean
    ss_between = ss_within = 0.0
    for r, v in sorted(byrole.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
        m = sum(v) / len(v)
        sd = (sum((x - m) ** 2 for x in v) / max(1, len(v) - 1)) ** 0.5
        ss_between += len(v) * (m - grand) ** 2
        ss_within += sum((x - m) ** 2 for x in v)
        print(f"{r:14s} {len(v):3d} {m:7.2f} {sd:6.2f} {max(v):6.2f}")
    tot = ss_between + ss_within
    print(f"\nvariance decomposition: role lottery {ss_between/tot*100:.0f}% "
          f"/ within-role {ss_within/tot*100:.0f}%")

    # depth + death class quick table
    deep = sum(1 for e in eps if e["depth_max"] >= 9)
    zero = sum(1 for e in eps if e["progression"] == 0)
    starve = sum(1 for e in eps if "starv" in e["end_reason"] or
                 "lack of food" in e["end_reason"])
    print(f"depth>=9: {deep}/{n}  zero-prog: {zero}  starvation-class: "
          f"{starve}  deepest: Dlvl:{max(e['depth_max'] for e in eps)} "
          f"({max(scores):.2f})")
    ee = [e.get("emergency_fired", 0) for e in eps]
    ev = [e.get("ev_fired", 0) for e in eps]
    print(f"expectimax fires/ep median {sorted(ev)[n//2]}, "
          f"emergency vetoes total {sum(ee)}")
    fin = collections.Counter(
        (e.get("subgoal_summary") or {}).get("_final", "?") for e in eps)
    print("subgoal at death:", dict(fin.most_common()))


if __name__ == "__main__":
    main()

"""Paired-block analyzer (s6): recovers lever fire-counts (from result dict
if present, else from the traj evs), reports paired progression delta,
survival@D5, per-role means, and death-class shift. Model: opus-4.8[1m] s6.

Usage: python3 analyze_block.py <ref_glob> <test_glob> <lever_ev_prefix> [name]
  lever_ev_prefix: e.g. THROW_DISENGAGE or HEALER_CAST_HEAL (traj-ev fallback)
"""
import glob
import json
import os
import random
import sys
import collections

import c2_classes as CC

HERE = os.path.dirname(os.path.abspath(__file__))
TRAJ = os.path.join(HERE, "results", "trajectories")


def load(pat):
    eps = {}
    for fn in glob.glob(pat):
        for e in json.load(open(fn)).get("episodes", []):
            eps[e["seed"]] = e
    return eps


def fires(ep, label, prefix):
    # prefer the result-dict count; fall back to traj evs
    for k in ("throw_fires", "heal_fires"):
        if k in ep and prefix.startswith(k.split("_")[0].upper()):
            return ep[k]
    tj = os.path.join(TRAJ, f"{label}__ep{ep['seed']}.json")
    if os.path.exists(tj):
        d = json.load(open(tj))
        return sum(1 for e in d.get("evs", []) if str(e[1]).startswith(prefix))
    return None


def main():
    refpat, tstpat, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    name = sys.argv[4] if len(sys.argv) > 4 else "block"
    reflab = os.path.basename(refpat).split("results_")[-1].split("_")[0]
    tstlab = os.path.basename(tstpat).split("results_")[-1].split("_")[0]
    ref, tst = load(refpat), load(tstpat)
    seeds = sorted(set(ref) & set(tst))
    deltas, roles = [], collections.defaultdict(lambda: [[], []])
    fires_tot = idn = 0
    print(f"{'seed':>5} {'role':>10} {'ref':>6} {'test':>6} {'d':>7} "
          f"{'fires':>5} {'rD':>3} {'tD':>3} end")
    for s in seeds:
        r, t = ref[s], tst[s]
        d = (t["progression"] - r["progression"]) * 100
        deltas.append(d)
        f = fires(t, tstlab, prefix)
        fires_tot += (f or 0)
        identical = abs(d) < 1e-9 and r["depth_max"] == t["depth_max"] and \
            r["end_reason"] == t["end_reason"]
        idn += identical
        roles[t.get("role", "?")][0].append(r["progression"] * 100)
        roles[t.get("role", "?")][1].append(t["progression"] * 100)
        print(f"{s:5d} {str(t.get('role'))[:10]:>10} {r['progression']*100:6.2f} "
              f"{t['progression']*100:6.2f} {d:+7.2f} {str(f):>5} "
              f"{r['depth_max']:3d} {t['depth_max']:3d} "
              f"{str(t['end_reason'])[:40]}")
    n = len(deltas)
    mean = sum(deltas) / n
    rng = random.Random(7)
    boots = sorted(sum(deltas[rng.randrange(n)] for _ in range(n)) / n
                   for _ in range(10000))
    lo, hi = boots[250], boots[9750]
    mr = sum(ref[s]["progression"] for s in seeds) / n * 100
    mt = sum(tst[s]["progression"] for s in seeds) / n * 100
    survR = sum(1 for s in seeds if ref[s]["depth_max"] >= 5) / n
    survT = sum(1 for s in seeds if tst[s]["depth_max"] >= 5) / n
    ccR = collections.Counter(CC.classify(ref[s]["end_reason"]) for s in seeds)
    ccT = collections.Counter(CC.classify(tst[s]["end_reason"]) for s in seeds)
    print(f"\n[{name}] n={n}  ref {mr:.2f}  test {mt:.2f}  "
          f"delta {mean:+.2f}  CI95 [{lo:+.2f},{hi:+.2f}]")
    print(f"  lever fires (test, '{prefix}'): {fires_tot} total | "
          f"bit-identical pairs: {idn}/{n}")
    print(f"  survival@D5: ref {survR*100:.1f}%  test {survT*100:.1f}%")
    print(f"  death-class ref:  {dict(ccR.most_common())}")
    print(f"  death-class test: {dict(ccT.most_common())}")
    print("  per-role mean (ref -> test):")
    for role, (rr, tt) in sorted(roles.items()):
        print(f"    {role:12} n={len(rr):2} "
              f"{sum(rr)/len(rr):6.2f} -> {sum(tt)/len(tt):6.2f} "
              f"({(sum(tt)-sum(rr))/len(rr):+.2f})")


if __name__ == "__main__":
    main()

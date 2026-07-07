"""Paired A/B analysis for Campaign-2 dev runs.

Usage: python3 c2_ab.py <ref_glob> <test_glob> [name]
Globs match results JSONs (episodes lists). Pairs by seed; bootstrap CI
on the mean paired delta (progression*100).
"""

import glob
import json
import random
import sys


def load(pat):
    eps = {}
    for fn in glob.glob(pat):
        for e in json.load(open(fn)).get("episodes", []):
            eps[e["seed"]] = e
    return eps


def main():
    ref = load(sys.argv[1])
    tst = load(sys.argv[2])
    name = sys.argv[3] if len(sys.argv) > 3 else "test"
    seeds = sorted(set(ref) & set(tst))
    deltas = []
    print(f"{'seed':>5s} {'ref':>6s} {'test':>6s} {'d':>7s}  role/end")
    for s in seeds:
        r, t = ref[s], tst[s]
        d = (t["progression"] - r["progression"]) * 100
        deltas.append(d)
        mark = "" if abs(d) < 0.01 else ("+" if d > 0 else "-")
        print(f"{s:5d} {r['progression']*100:6.2f} {t['progression']*100:6.2f} "
              f"{d:+7.2f}{mark} {t.get('role','?'):>12s} "
              f"ref:{r['depth_max']:2d} test:{t['depth_max']:2d} "
              f"{str(t['end_reason'])[:44]}")
    n = len(deltas)
    mean = sum(deltas) / n
    rng = random.Random(7)
    boots = []
    for _ in range(10000):
        samp = [deltas[rng.randrange(n)] for _ in range(n)]
        boots.append(sum(samp) / n)
    boots.sort()
    lo, hi = boots[250], boots[9750]
    mr = sum(ref[s]["progression"] for s in seeds) / n * 100
    mt = sum(tst[s]["progression"] for s in seeds) / n * 100
    nz = sum(1 for d in deltas if abs(d) > 0.01)
    pos = sum(1 for d in deltas if d > 0.01)
    print(f"\n[{name}] n={n} ref {mr:.2f} test {mt:.2f} "
          f"delta {mean:+.2f} CI95 [{lo:+.2f},{hi:+.2f}] "
          f"nonzero {nz} (pos {pos}/neg {nz-pos})")


if __name__ == "__main__":
    main()

"""Role-stratified dev-seed selector (FLOOR-ROLE uplift, s5).

MODEL: claude-opus-4-8[1m] (max thinking), Phase L session 5.

The role is randomized per seed but DETERMINISTIC at reset, so a census
(role_census.py) turns "I want n>=15 Healer episodes" into a concrete seed
list — the instrument the operator's role-stratified validation needs (a
random 40-ep block yields only 2-3 of a floor role; stratification gets the
signal). Merges the censuses (800-999 + 1100-1899, all DEV-safe ranges,
disjoint from the scored 1000-1004/2000-2024/.../6000-6099/7000-7024 blocks).

Usage:
  python3 role_seeds.py Healer 15          # first 15 Healer dev seeds
  python3 role_seeds.py --table            # per-role counts
  python3 role_seeds.py Tourist 20 --csv   # comma list for a block runner
"""
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
CENSUSES = ["role_census.json", "role_census_ext.json"]

# scored/reserved ranges — never emit these (mirror nh_branch.FORBIDDEN)
FORBIDDEN = [(1000, 1004), (2000, 2024), (3000, 3079), (4000, 4079),
             (5000, 5024), (6000, 6099), (7000, 7024)]


def _forbidden(s):
    return any(lo <= s <= hi for lo, hi in FORBIDDEN)


def load():
    by = defaultdict(list)
    for fn in CENSUSES:
        p = os.path.join(RESULTS, fn)
        if not os.path.exists(p):
            continue
        for k, v in json.load(open(p)).items():
            s = int(k)
            if v.get("role") and not _forbidden(s):
                by[v["role"]].append(s)
    for r in by:
        by[r] = sorted(set(by[r]))
    return by


def seeds_for(role, n=None):
    by = load()
    lst = by.get(role, [])
    return lst[:n] if n else lst


def main():
    if "--table" in sys.argv:
        by = load()
        for r, s in sorted(by.items(), key=lambda kv: -len(kv[1])):
            print(f"  {r:12} n={len(s):3}")
        return
    role = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
    lst = seeds_for(role, n)
    if "--csv" in sys.argv:
        print(",".join(str(s) for s in lst))
    else:
        print(f"{role} ({len(lst)} seeds): {lst}")


if __name__ == "__main__":
    main()

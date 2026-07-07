"""Death-class shift analysis for lever groups (lower-variance evidence
than raw paired score deltas under same-seed chaos divergence).

Usage: python3 c2_classes.py <glob1> <glob2> ... (labels inferred)
Prints per-run-set death-class counts on the common dev seeds.
"""

import glob
import json
import sys
import collections
import re

SPIDER_ANT = ("giant spider", "soldier ant", "giant ant", "fire ant",
              "killer bee", "queen bee")
RANGED = ("bolt of lightning", "magic missile", "wand", "orcish dagger",
          "dart", "arrow")

import os
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "pylib"))
import nh_common as C

DIFF = {name: diff for (name, lvl, diff, spd, cls) in
        [C._SPECIES[i] for i in range(len(C._SPECIES))]}


def classify(r):
    if r.startswith("ABORT"):
        return "ABORT"
    if "starved" in r or "lack of food" in r:
        return "STARV"
    if "while praying" in r:
        return "PRAY"
    m = re.search(r"Killed by (?:an? |the )?(.+?)(?:,|\.|$)", r)
    cause = m.group(1).strip() if m else r
    if any(k in cause for k in RANGED):
        return "RANGED"
    if cause in SPIDER_ANT:
        return "SPIDANT"
    d = DIFF.get(cause)
    if d is None:
        for name, dd in DIFF.items():
            if name in cause:
                d = dd
                break
    if d is not None and d <= 4:
        return "TRASH"
    if "poisoned" in r.lower() or "Poisoned" in r:
        return "POISON"
    return "MELEE+"


def main():
    for pat in sys.argv[1:]:
        eps = {}
        for fn in glob.glob(pat):
            for e in json.load(open(fn)).get("episodes", []):
                eps[e["seed"]] = e
        eps = {s: e for s, e in eps.items() if 700 <= s <= 719}
        cc = collections.Counter(classify(e["end_reason"])
                                 for e in eps.values())
        mean = sum(e["progression"] for e in eps.values()) * 100 / \
            max(1, len(eps))
        deep = sum(1 for e in eps.values() if e["depth_max"] >= 7)
        print(f"{pat.split('results_')[-1][:24]:26s} n={len(eps):2d} "
              f"mean {mean:5.2f} d7+={deep:2d}  {dict(cc.most_common())}")


if __name__ == "__main__":
    main()

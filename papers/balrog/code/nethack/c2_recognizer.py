"""Jim-port (h): death-cause recognizer as verified code.

Rule under test (the expectimax veto): a state with adjacent hostiles is
"imminent death" when hp <= 3 * sum(dpt of adjacent) AND the fight EV is
losing. Validate on held-out episodes (odd seeds): precision/recall of
death-within-K-steps; sweep the multiplier.

Uses the combat rows from results/c2_cache (pre-Campaign-2 logs only, so
the rule is validated on data the new policy has not shaped).
"""

import glob
import gzip
import json
import os
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "pylib"))
import nh_percept as P

CACHE = os.path.join(HERE, "results", "c2_cache")
K = 12          # "imminent" horizon in env steps


def main():
    rows_by_ep = []
    for fn in sorted(glob.glob(os.path.join(CACHE, "*.json.gz"))):
        d = json.load(gzip.open(fn, "rt"))
        seed = (d.get("header") or {}).get("seed")
        if seed is None or seed % 2 == 0:      # holdout = odd seeds
            continue
        died = d["final"] is not None and d["steps"] > 0 and \
            any("Killed" in m or "died" in m
                for _s, m in (d.get("last_msgs") or []))
        death_step = d["steps"] - 1
        rows_by_ep.append((d.get("combat", []), died, death_step))

    for mult in (2.0, 3.0, 4.0):
        tp = fp = fn_ = tn = 0
        for combat, died, death_step in rows_by_ep:
            for row in combat:
                (step, dt, depth, hp, hpmax, xp, ac, adj, act, dmg,
                 kill) = row
                names = adj.split("|")
                total_dpt = sum(P.species_dpt(n) for n in names)
                pred = hp <= mult * total_dpt
                actual = died and (death_step - step) <= K
                if pred and actual:
                    tp += 1
                elif pred and not actual:
                    fp += 1
                elif actual:
                    fn_ += 1
                else:
                    tn += 1
        prec = tp / max(1, tp + fp)
        rec = tp / max(1, tp + fn_)
        print(f"mult {mult}: precision {prec:.3f} recall {rec:.3f} "
              f"(tp {tp} fp {fp} fn {fn_} tn {tn})")


if __name__ == "__main__":
    main()

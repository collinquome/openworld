"""WIELD-block paired analyzer (Phase L s13). Reads the (seed,arm) JSONL from
run_wield_block.sh and reports the DECISIVE number: the paired PROGRESSION-MEAN
delta + 95% bootstrap CI, plus combat-death rate, wield-fire mechanism check,
depth mean, per-role, and bit-identical count. Model: claude-opus-4-8[max].

Usage: python3 analyze_wield.py results/wield_block.jsonl
"""
import json
import os
import random
import sys
import collections

import c2_classes as CC


def combat_death(er):
    return str(er).startswith("DEATH") and CC.classify(er) not in ("STARV",)


def main():
    path = sys.argv[1]
    rows = collections.defaultdict(dict)   # seed -> arm -> row
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        rows[r["seed"]][r["arm"]] = r
    seeds = sorted(s for s in rows
                   if "REF" in rows[s] and "TEST" in rows[s]
                   and rows[s]["REF"].get("end_reason") != "TIMEOUT_OR_FAIL"
                   and rows[s]["TEST"].get("end_reason") != "TIMEOUT_OR_FAIL")
    deltas, roles = [], collections.defaultdict(lambda: [[], []])
    wield_tot = idn = cdR = cdT = 0
    dR = dT = 0.0
    print(f"{'seed':>5} {'role':>11} {'refP':>7} {'tstP':>7} {'dP':>8} "
          f"{'wf':>3} {'rD':>3} {'tD':>3} {'ident':>5} end(test)")
    for s in seeds:
        r, t = rows[s]["REF"], rows[s]["TEST"]
        rp, tp = r.get("prog") or 0.0, t.get("prog") or 0.0
        d = (tp - rp) * 100
        deltas.append(d)
        wf = t.get("wield_fires", 0)
        wield_tot += wf
        rd, td = r.get("depth_max") or 0, t.get("depth_max") or 0
        dR += rd
        dT += td
        cdR += combat_death(r.get("end_reason", ""))
        cdT += combat_death(t.get("end_reason", ""))
        ident = (abs(d) < 1e-9 and rd == td
                 and r.get("end_reason") == t.get("end_reason")
                 and r.get("steps") == t.get("steps"))
        idn += ident
        role = t.get("role", "?")
        roles[role][0].append(rp * 100)
        roles[role][1].append(tp * 100)
        print(f"{s:5d} {str(role)[:11]:>11} {rp*100:7.3f} {tp*100:7.3f} "
              f"{d:+8.3f} {wf:3d} {rd:3d} {td:3d} {str(ident):>5} "
              f"{str(t.get('end_reason'))[:38]}")
    n = len(deltas)
    if not n:
        print("no complete pairs")
        return
    mean = sum(deltas) / n
    rng = random.Random(7)
    boots = sorted(sum(deltas[rng.randrange(n)] for _ in range(n)) / n
                   for _ in range(10000))
    lo, hi = boots[250], boots[9750]
    mr = sum((rows[s]["REF"].get("prog") or 0) for s in seeds) / n * 100
    mt = sum((rows[s]["TEST"].get("prog") or 0) for s in seeds) / n * 100
    print(f"\n[WIELD s13] n={n} paired  "
          f"REF progression {mr:.4f}  TEST {mt:.4f}")
    print(f"  ** PROGRESSION-MEAN delta {mean:+.4f} (x100)  "
          f"95% paired-bootstrap CI [{lo:+.4f}, {hi:+.4f}]  "
          f"{'INCLUDES 0 -> NULL' if lo <= 0 <= hi else 'EXCLUDES 0 -> MOVER'} **")
    print(f"  combat-death rate: REF {cdR}/{n}={cdR/n:.3f}  "
          f"TEST {cdT}/{n}={cdT/n:.3f}  delta {(cdT-cdR)/n:+.3f}")
    print(f"  depth mean: REF {dR/n:.2f}  TEST {dT/n:.2f}  "
          f"delta {(dT-dR)/n:+.2f}")
    print(f"  MECHANISM -- wield-fires total (TEST): {wield_tot}  "
          f"| bit-identical pairs: {idn}/{n}")
    print("  per-role progression mean (ref -> test):")
    for role, (rr, tt) in sorted(roles.items()):
        print(f"    {role:12} n={len(rr):2} "
              f"{sum(rr)/len(rr):6.3f} -> {sum(tt)/len(tt):6.3f} "
              f"({(sum(tt)-sum(rr))/len(rr):+.3f})")


if __name__ == "__main__":
    main()

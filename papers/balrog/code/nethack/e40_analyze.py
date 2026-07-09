"""NH-E40 DIVE-RUSH paired analysis. Reads results/e40_diverush.jsonl, pairs
REF vs TEST by seed, reports the primary progression-mean Δ + paired bootstrap
CI, plus depth_max, steps/level, death rate, leave-one-out, and the fired-split
(did dive-rush actually change behavior — steps/level drop + diverush fires).
Deterministic bootstrap (fixed seed) so the numbers are reproducible.
"""
import json
import os
import random
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "results", "e40_diverush.jsonl")


def load():
    ref, test = {}, {}
    for ln in open(F):
        ln = ln.strip()
        if not ln:
            continue
        r = json.loads(ln)
        (ref if r["arm"] == "REF" else test)[r["seed"]] = r
    return ref, test


def spl(r):
    return r["steps"] / max(r["depth_max"] or 1, 1)


def is_death(r):
    return str(r["end_reason"]).startswith("DEATH")


def boot_ci(deltas, n=20000, seed=40):
    rng = random.Random(seed)
    k = len(deltas)
    means = []
    for _ in range(n):
        s = sum(deltas[rng.randrange(k)] for _ in range(k)) / k
        means.append(s)
    means.sort()
    return means[int(.025 * n)], means[int(.975 * n)]


def main():
    ref, test = load()
    seeds = sorted(set(ref) & set(test))
    print(f"paired seeds n={len(seeds)}: {seeds}")
    print(f"REF-only (no TEST): {sorted(set(ref) - set(test))}")
    print()
    hdr = ("seed  role        REF_d TEST_d  REF_prog TEST_prog   dP     "
           "REF_spl TEST_spl  dr  REFend/TESTend")
    print(hdr)
    dP, dD, dSPL = [], [], []
    ref_prog, test_prog, ref_d, test_d = [], [], [], []
    ref_death, test_death = 0, 0
    fired_behavior = 0  # dive-rush fired AND steps/level dropped
    for s in seeds:
        a, b = ref[s], test[s]
        p = b["prog"] - a["prog"]
        dd = (b["depth_max"] or 0) - (a["depth_max"] or 0)
        ds = spl(b) - spl(a)
        dP.append(p); dD.append(dd); dSPL.append(ds)
        ref_prog.append(a["prog"]); test_prog.append(b["prog"])
        ref_d.append(a["depth_max"] or 0); test_d.append(b["depth_max"] or 0)
        ref_death += is_death(a); test_death += is_death(b)
        drn = b.get("diverush_notes", 0)
        if drn > 0 and spl(b) < spl(a):
            fired_behavior += 1
        print(f"{s:4d}  {a['role'][:10]:10s}  {a['depth_max']:4}  "
              f"{b['depth_max']:5}  {a['prog']:.4f}  {b['prog']:.4f}  "
              f"{p:+.4f}  {spl(a):6.1f}  {spl(b):6.1f}  {drn:3} "
              f"{str(a['end_reason'])[:14]:14s}/{str(b['end_reason'])[:14]}")
    n = len(seeds)
    mP = sum(dP) / n
    lo, hi = boot_ci(dP)
    print()
    print("=== PRIMARY KPI: progression mean ===")
    print(f"REF  mean prog = {sum(ref_prog)/n:.4f}")
    print(f"TEST mean prog = {sum(test_prog)/n:.4f}")
    print(f"paired Δ prog  = {mP:+.4f}   95% bootstrap CI [{lo:+.4f}, {hi:+.4f}]"
          f"   {'EXCLUDES 0' if (lo>0 or hi<0) else 'INCLUDES 0 (null)'}")
    wins = sum(1 for x in dP if x > 1e-9)
    losses = sum(1 for x in dP if x < -1e-9)
    ties = sum(1 for x in dP if abs(x) <= 1e-9)
    print(f"per-seed: {wins} TEST-better / {losses} TEST-worse / {ties} tie")
    print()
    print("=== depth_max ===")
    print(f"REF mean depth = {sum(ref_d)/n:.2f}   TEST mean depth = "
          f"{sum(test_d)/n:.2f}   Δ = {sum(dD)/n:+.2f}")
    print(f"TEST deeper on {sum(1 for x in dD if x>0)} / equal "
          f"{sum(1 for x in dD if x==0)} / shallower {sum(1 for x in dD if x<0)}")
    print()
    print("=== steps/level (descent speed; lower=faster) ===")
    print(f"REF mean steps/lvl = {sum(spl(ref[s]) for s in seeds)/n:.1f}   "
          f"TEST mean steps/lvl = {sum(spl(test[s]) for s in seeds)/n:.1f}   "
          f"Δ = {sum(dSPL)/n:+.1f}")
    faster = sum(1 for x in dSPL if x < -1e-9)
    print(f"TEST descended FASTER (steps/lvl down) on {faster}/{n} seeds")
    print()
    print("=== death rate ===")
    print(f"REF deaths = {ref_death}/{n} ({ref_death/n:.2f})   "
          f"TEST deaths = {test_death}/{n} ({test_death/n:.2f})")
    print()
    print("=== fired-split (dive-rush fired AND steps/lvl dropped) ===")
    print(f"behavior-changed on {fired_behavior}/{n} seeds")
    print()
    print("=== leave-one-out (mean Δ prog dropping each seed) ===")
    for i, s in enumerate(seeds):
        loo = (sum(dP) - dP[i]) / (n - 1)
        flag = "  <-- sign-flip vs full" if (loo > 0) != (mP > 0) else ""
        print(f"  drop {s}: Δ={loo:+.4f}{flag}")


if __name__ == "__main__":
    main()

"""NH-E41 CORRIDOR-FUNNEL paired analysis. Reads results/e41_funnel.jsonl, pairs
REF vs TEST by seed, reports:
  - PRIMARY KPI: progression-mean Δ + paired bootstrap CI (canonical ci95).
  - SIGNATURE-FIDELITY: funnel_fires per TEST episode (>0 or it's a mechanical
    null like E36) + how many seeds fired at all.
  - MULTI-ATTACKER: mean multi-attacker-exchange rate REF vs TEST (did the
    funnel reduce simultaneous attackers?).
  - death rate + depth_max.
  - FIRED-SPLIT: prog Δ on seeds where funnel fired vs not (endogeneity noted).
  - leave-one-out on the mean Δ (guard the +2.64/+7.36 one-seed mirage).
Deterministic bootstrap (canonical seed). Usage: python3 e41_analyze.py
"""
import json
import os

from bootstrap_ci import ci95

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "results", "e41_funnel.jsonl")


def load():
    ref, test = {}, {}
    for ln in open(F):
        ln = ln.strip()
        if not ln:
            continue
        r = json.loads(ln)
        (ref if r["arm"] == "REF" else test)[r["seed"]] = r
    return ref, test


def is_death(r):
    return str(r["end_reason"]).startswith("DEATH")


def ma_rate(r):
    return r.get("ma_multi", 0) / max(r.get("ma_snaps", 0) or 1, 1)


def faced2_rate(arm, seed, radius=3):
    """Post-hoc ADDRESSABLE-SCENARIO rate: fraction of monster snapshots where
    >=2 non-pet hostiles are within Chebyshev `radius` of the agent — i.e. how
    often the agent actually FACES A PACK (the only state NH_FUNNEL can help).
    Read from the on-disk trajectory. Returns (faced2_snaps, total_snaps)."""
    p = os.path.join(HERE, "results", "trajectories", f"{arm}__ep{seed}.json")
    if not os.path.exists(p):
        return (0, 0)
    try:
        tj = json.load(open(p))
    except Exception:
        return (0, 0)
    mon = tj.get("monsters", []) or []
    pos = tj.get("positions", []) or []
    faced, tot = 0, 0
    for fr in mon:
        step, mlist = fr[0], fr[1]
        if step < 1 or step > len(pos):
            continue
        ax, ay = pos[step - 1]
        nnear = sum(1 for m in mlist if not (len(m) > 3 and m[3])
                    and max(abs(m[0] - ax), abs(m[1] - ay)) <= radius)
        tot += 1
        if nnear >= 2:
            faced += 1
    return (faced, tot)


def paired_ci(deltas):
    if not deltas:
        return (0.0, 0.0)
    return ci95(deltas)


def main():
    ref, test = load()
    seeds = sorted(set(ref) & set(test))
    n = len(seeds)
    print(f"paired seeds n={n}: {seeds}")
    print(f"REF-only: {sorted(set(ref)-set(test))}  "
          f"TEST-only: {sorted(set(test)-set(ref))}\n")
    hdr = ("seed  role        REF_d TEST_d  REF_prog TEST_prog   dP      "
           "fun flv  REF_ma TEST_ma  end(R/T)")
    print(hdr)
    dP, dD = [], []
    ref_prog, test_prog, ref_d, test_d = [], [], [], []
    ref_death = test_death = 0
    ref_ma, test_ma = [], []
    fired_seeds, nonfired_seeds = [], []
    for s in seeds:
        a, b = ref[s], test[s]
        p = b["prog"] - a["prog"]
        dd = (b["depth_max"] or 0) - (a["depth_max"] or 0)
        dP.append(p); dD.append(dd)
        ref_prog.append(a["prog"]); test_prog.append(b["prog"])
        ref_d.append(a["depth_max"] or 0); test_d.append(b["depth_max"] or 0)
        ref_death += is_death(a); test_death += is_death(b)
        ref_ma.append(ma_rate(a)); test_ma.append(ma_rate(b))
        fun = b.get("funnel_fires", 0)
        (fired_seeds if fun > 0 else nonfired_seeds).append(s)
        print(f"{s:4d}  {a['role'][:10]:10s}  {a['depth_max']:4}  "
              f"{b['depth_max']:5}  {a['prog']:.4f}  {b['prog']:.4f}  "
              f"{p:+.4f}  {fun:3} {b.get('funnel_levels',0):3}  "
              f"{ma_rate(a):.3f}  {ma_rate(b):.3f}  "
              f"{str(a['end_reason'])[:10]:10s}/{str(b['end_reason'])[:10]}")
    mP = sum(dP) / n
    lo, hi = paired_ci(dP)
    print("\n=== PRIMARY KPI: progression mean ===")
    print(f"REF  mean prog = {sum(ref_prog)/n:.4f}")
    print(f"TEST mean prog = {sum(test_prog)/n:.4f}")
    print(f"paired Δ prog  = {mP:+.4f}   95% CI [{lo:+.4f}, {hi:+.4f}]   "
          f"{'EXCLUDES 0' if (lo>0 or hi<0) else 'INCLUDES 0 (null)'}")
    wins = sum(1 for x in dP if x > 1e-9)
    losses = sum(1 for x in dP if x < -1e-9)
    ties = sum(1 for x in dP if abs(x) <= 1e-9)
    print(f"per-seed: {wins} TEST-better / {losses} TEST-worse / {ties} tie")

    print("\n=== SIGNATURE-FIDELITY: did NH_FUNNEL FIRE live? ===")
    total_fires = sum(test[s].get("funnel_fires", 0) for s in seeds)
    print(f"seeds where funnel fired (>0): {len(fired_seeds)}/{n}  {fired_seeds}")
    print(f"total funnel fires across TEST: {total_fires}")
    if not fired_seeds:
        print("  => MECHANICAL NULL by NON-OCCURRENCE (E36 signature-fidelity "
              "sibling): the multi-attacker state never arose live.")

    print("\n=== MULTI-ATTACKER exchange rate (>=2 hostiles adjacent) ===")
    print(f"REF  mean ma_rate = {sum(ref_ma)/n:.4f}")
    print(f"TEST mean ma_rate = {sum(test_ma)/n:.4f}   "
          f"Δ = {(sum(test_ma)-sum(ref_ma))/n:+.4f} "
          f"(negative = funnel reduced simultaneous attackers)")
    print(f"REF seeds with ANY multi-attacker snapshot: "
          f"{sum(1 for s in seeds if ref[s].get('ma_multi',0)>0)}/{n}")

    print("\n=== ADDRESSABLE-SCENARIO rate: how often does REF FACE a pack? ===")
    print("(>=2 non-pet hostiles within radius 3 = the only state the funnel can"
          " help; if rare, choke-fighting cannot move the mean regardless)")
    tot_faced = tot_snap = 0
    any_faced = 0
    for s in seeds:
        f, t = faced2_rate("REF", s, radius=3)
        tot_faced += f; tot_snap += t
        any_faced += (f > 0)
        fa, _ = faced2_rate("REF", s, radius=1)  # strict: 2+ ADJACENT
        print(f"  s{s}: faced2(r3)={f:4}/{t:4} ({(f/t if t else 0):.3f})  "
              f"adjacent2(r1)={fa}")
    print(f"  OVERALL faced-2+-pack (r3) rate = {tot_faced}/{tot_snap} "
          f"= {(tot_faced/tot_snap if tot_snap else 0):.4f}")
    print(f"  seeds with ANY faced-2+ moment: {any_faced}/{n}")

    print("\n=== depth_max / death rate ===")
    print(f"REF mean depth = {sum(ref_d)/n:.2f}   TEST mean depth = "
          f"{sum(test_d)/n:.2f}   Δ = {sum(dD)/n:+.2f}")
    print(f"REF deaths = {ref_death}/{n}   TEST deaths = {test_death}/{n}")

    print("\n=== FIRED-SPLIT (endogenous — report both) ===")
    if fired_seeds:
        fd = [test[s]["prog"] - ref[s]["prog"] for s in fired_seeds]
        print(f"fired seeds ({len(fired_seeds)}): mean Δ prog = "
              f"{sum(fd)/len(fd):+.4f}  {dict(zip(fired_seeds,[round(x,4) for x in fd]))}")
    else:
        print("fired seeds: none")
    if nonfired_seeds:
        nd = [test[s]["prog"] - ref[s]["prog"] for s in nonfired_seeds]
        print(f"non-fired seeds ({len(nonfired_seeds)}): mean Δ prog = "
              f"{sum(nd)/len(nd):+.4f} (should be ~0.0 = bit-identical)")

    print("\n=== leave-one-out (mean Δ prog dropping each seed) ===")
    for i, s in enumerate(seeds):
        loo = (sum(dP) - dP[i]) / (n - 1)
        flag = "  <-- sign-flip" if (loo > 0) != (mP > 0) and abs(mP) > 1e-9 else ""
        print(f"  drop {s}: Δ={loo:+.4f}{flag}")


if __name__ == "__main__":
    main()

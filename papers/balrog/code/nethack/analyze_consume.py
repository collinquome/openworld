"""NH-E38 CONSUMABLE-ECONOMY paired-block analysis.

PRIMARY KPI = progression-mean Δ (paired bootstrap CI). Also:
  - arrival-XP@D5 Δ (headline proxy: low-variance, mechanistically upstream of
    the spike-death fix — the operator's +3-XP target).
  - depth-conditioned XP (xp at each depth, REF vs TEST).
  - FIRED-SPLIT: on how many seeds did the consumable machinery fire
    (engrave-ID / zap / pickup / gain-level), and the Δ restricted to fired vs
    non-fired pairs.
  - LEAVE-ONE-OUT on the progression Δ (the loot-lever discipline: a +0.72 that
    was one-seed noise must not be repeated).
  - REGRESSION: new death classes in TEST vs REF (self-poison, aggravate, etc.).
  - Leveling-wall table: xp/hp_max/ac/str at death, REF vs TEST.

Usage: python3 analyze_consume.py results/consume_block2.jsonl [more.jsonl ...]
"""
import json
import random
import sys
from collections import defaultdict


def load(paths):
    rows = {}
    for p in paths:
        for line in open(p):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            rows[(r["seed"], r["arm"])] = r
    return rows


def paired(rows, field):
    seeds = sorted({s for (s, a) in rows})
    out = []
    for s in seeds:
        ref, test = rows.get((s, "REF")), rows.get((s, "TEST"))
        if not ref or not test:
            continue
        rv, tv = ref.get(field), test.get(field)
        if rv is None or tv is None:
            continue
        out.append((s, rv, tv))
    return out


def boot_ci(diffs, n=20000, seed=1):
    if not diffs:
        return (0.0, 0.0, 0.0)
    random.seed(seed)
    m = sum(diffs) / len(diffs)
    means = []
    k = len(diffs)
    for _ in range(n):
        samp = [diffs[random.randrange(k)] for _ in range(k)]
        means.append(sum(samp) / k)
    means.sort()
    return (m, means[int(0.025 * n)], means[int(0.975 * n)])


def report_field(rows, field, label):
    pr = paired(rows, field)
    if not pr:
        print(f"  {label}: no paired data")
        return None
    diffs = [t - r for (_s, r, t) in pr]
    m, lo, hi = boot_ci(diffs)
    refm = sum(r for _s, r, _t in pr) / len(pr)
    testm = sum(t for _s, _r, t in pr) / len(pr)
    imp = sum(1 for d in diffs if d > 1e-9)
    reg = sum(1 for d in diffs if d < -1e-9)
    print(f"  {label} (n={len(pr)}): REF {refm:.4f} -> TEST {testm:.4f} | "
          f"Δ {m:+.4f}  95% CI [{lo:+.4f}, {hi:+.4f}]  "
          f"({imp} up / {reg} down / {len(pr)-imp-reg} tie)")
    return pr, diffs


def main():
    paths = sys.argv[1:] or ["results/consume_block2.jsonl"]
    rows = load(paths)
    seeds = sorted({s for (s, a) in rows})
    print(f"=== NH-E38 consumable-economy paired analysis ({', '.join(paths)}) ===")
    print(f"seeds with both arms: "
          f"{len([s for s in seeds if (s,'REF') in rows and (s,'TEST') in rows])}")

    print("\n-- PRIMARY: progression mean --")
    prog = report_field(rows, "prog", "progression")
    print("\n-- PROXY: arrival-XP@D5 --")
    report_field(rows, "arrival_xp_d5", "arrival_xp_d5")
    print("\n-- depth_max --")
    report_field(rows, "depth_max", "depth_max")
    print("\n-- xp_max --")
    report_field(rows, "xp_max", "xp_max")

    # FIRED-SPLIT
    print("\n-- FIRED-SPLIT (TEST arm mechanism) --")
    fire_fields = ["engrave_id_tests", "engrave_id_solved", "zap_off_fires",
                   "consume_kills", "consume_pickups", "gainlevel_fires",
                   "quaff_heal_fires", "enchant_fires"]
    tot = defaultdict(int)
    fired_seeds = set()
    for s in seeds:
        t = rows.get((s, "TEST"))
        if not t:
            continue
        for f in fire_fields:
            tot[f] += t.get(f, 0) or 0
        if any((t.get(f, 0) or 0) for f in
               ["zap_off_fires", "gainlevel_fires", "quaff_heal_fires",
                "enchant_fires", "engrave_id_tests"]):
            fired_seeds.add(s)
    for f in fire_fields:
        print(f"    {f}: {tot[f]} total")
    print(f"    seeds where the policy FIRED (use or ID): "
          f"{sorted(fired_seeds)} (n={len(fired_seeds)})")

    if prog:
        pr, diffs = prog
        fired_d = [t - r for (s, r, t) in pr if s in fired_seeds]
        non_d = [t - r for (s, r, t) in pr if s not in fired_seeds]
        if fired_d:
            m, lo, hi = boot_ci(fired_d)
            print(f"    progression Δ on FIRED pairs (n={len(fired_d)}): "
                  f"{m:+.4f} CI [{lo:+.4f},{hi:+.4f}]")
        print(f"    progression Δ on NON-fired pairs (n={len(non_d)}): "
              f"{'bit-identical' if all(abs(d)<1e-12 for d in non_d) else 'DIFFERS'}")

        # LEAVE-ONE-OUT
        print("\n-- LEAVE-ONE-OUT (progression Δ, drop each seed) --")
        base = sum(diffs) / len(diffs)
        print(f"    full-sample Δ = {base:+.4f}")
        loo = []
        for i, (s, r, t) in enumerate(pr):
            rest = diffs[:i] + diffs[i+1:]
            loo.append((s, sum(rest) / len(rest)))
        loo.sort(key=lambda x: x[1])
        print(f"    most-influential drops: "
              + ", ".join(f"drop{s}->{v:+.4f}" for s, v in loo[:3])
              + " ... " + ", ".join(f"drop{s}->{v:+.4f}" for s, v in loo[-3:]))

    # REGRESSION: death classes
    print("\n-- REGRESSION: death classes (killer) --")
    def killer(r):
        e = str(r.get("end_reason", ""))
        if "Killed by" in e:
            return e.split("Killed by", 1)[1].strip().rstrip(".")[:34]
        return e[:34]
    ref_k, test_k = defaultdict(int), defaultdict(int)
    for s in seeds:
        if (s, "REF") in rows:
            ref_k[killer(rows[(s, "REF")])] += 1
        if (s, "TEST") in rows:
            test_k[killer(rows[(s, "TEST")])] += 1
    new = set(test_k) - set(ref_k)
    print(f"    NEW death classes in TEST (not in REF): {sorted(new) or 'none'}")
    for k in sorted(set(ref_k) | set(test_k)):
        if ref_k[k] != test_k[k]:
            print(f"      {k:36s} REF {ref_k[k]} -> TEST {test_k[k]}")

    # LEVELING-WALL table
    print("\n-- LEVELING-WALL: state at death (mean) --")
    for f in ["xp_at_death", "hpmax_end", "ac_end", "str_end"]:
        report_field(rows, f, f)


if __name__ == "__main__":
    main()

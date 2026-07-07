"""Campaign-2 E-NH1: full hazard forensics + counterfactual ceilings.

Inputs: canonical results JSONs (main arm), blind-arm batch JSONLs,
and the c2_cache extracts (nh_mine.py). Outputs results/c2_forensics.json
plus printed markdown tables.

Ceiling method (censored competing-risk): for the v1.1 n=80 block,
per-depth hazard h(d) = P(die with max_depth==d | reached d), decomposed
by cause class. Eliminating class c sets h'(d)=h(d)-h_c(d); the implied
max-depth distribution is walked forward and scored with the empirical
mean score at each max depth (survivors past the observed frontier get
the deepest observed episode's score — conservative truncation).
Bootstrap over episodes gives the CI.
"""

import glob
import gzip
import json
import os
import re
import sys
import collections
import random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "pylib"))
RESULTS = os.path.join(HERE, "results")
CACHE = os.path.join(RESULTS, "c2_cache")
BLIND = os.path.join(os.path.dirname(HERE), "fable_nethack_blind", "results")

import nh_common as C

ACH = json.load(open(os.path.join(HERE, "balrog", "environments", "nle",
                                  "achievements.json")))
DIFF = {name: diff for (name, lvl, diff, spd, cls) in
        [C._SPECIES[i] for i in range(len(C._SPECIES))]}
SPEED = {name: spd for (name, lvl, diff, spd, cls) in
         [C._SPECIES[i] for i in range(len(C._SPECIES))]}

RANGED_CAUSES = ("bolt of lightning", "magic missile", "wand",
                 "orcish dagger", "dart", "arrow", "crossbow bolt")
SPIDER_ANT = ("giant spider", "soldier ant", "giant ant", "fire ant",
              "killer bee", "queen bee")


def classify(end_reason, final):
    r = end_reason
    if r.startswith("ABORT"):
        return "ABORT"
    if "starved" in r or "fainted from lack of food" in r:
        return "STARVATION"
    if "while praying" in r:
        if final and final.get("hunger", 0) >= 3:
            return "STARVATION"
        return "PRAY_DEATH"
    if "while sleeping" in r:
        return "SLEEP"
    m = re.search(r"Killed by (?:an? |the )?(.+?)(?:,|\.|$)", r)
    cause = m.group(1).strip() if m else r
    if any(k in cause for k in RANGED_CAUSES):
        return "RANGED"
    if cause in ("boulder", "falling rock", "land mine", "fire trap"):
        return "TRAP"
    if "explosion" in cause or "gas spore" in cause:
        return "EXPLODE"
    if cause in SPIDER_ANT:
        return "SPIDER_ANT"
    d = DIFF.get(cause)
    if d is None:
        for name, dd in DIFF.items():
            if name in cause:
                d = dd
                break
    if d is not None and d <= 4:
        return "MELEE_TRASH"
    return "MELEE_OTHER"


def species_of(end_reason):
    m = re.search(r"Killed by (?:an? |the )?(.+?)(?:,|\.|$)", end_reason)
    return m.group(1).strip() if m else None


def load_main():
    eps = []
    canon = [
        ("v1_baseline25", "nethack_results_baseline25.json"),
        ("v1_robustness", "nethack_results_robustness.json"),
        ("v1_run1", "nethack_results_run1.json"),
        ("v1_cleanA", "nethack_results.json"),
        ("v11_block80", "nethack_results_v11block80.json"),
        ("v1_memory_paired", "memory_paired.json"),
    ]
    for tag, fn in canon:
        p = os.path.join(RESULTS, fn)
        if not os.path.exists(p):
            continue
        for e in json.load(open(p)).get("episodes", []):
            e["arm"] = tag
            eps.append(e)
    me = os.path.join(RESULTS, "memory_experiment.json")
    if os.path.exists(me):
        for i, p in enumerate(json.load(open(me))["passes"]):
            for e in p.get("episodes", []):
                e["arm"] = f"v1_memory_pass{i+1}"
                eps.append(e)
    return eps


def load_blind():
    eps = []
    for fn in sorted(glob.glob(os.path.join(BLIND, "batch_*.jsonl"))):
        for line in open(fn):
            try:
                e = json.loads(line)
            except Exception:
                continue
            if not isinstance(e, dict) or "end" not in e:
                continue
            eps.append(dict(arm="blind_" + os.path.basename(fn)[6:-6],
                            end_reason=str(e.get("end", "")),
                            progression=float(e.get("prog", 0.0))))
    return eps


def attach_cache(eps):
    idx = {}
    for fn in glob.glob(os.path.join(CACHE, "*.json.gz")):
        base = os.path.basename(fn)
        idx[base] = fn
    for e in eps:
        tf = e.get("transitions_file")
        if not tf:
            continue
        label = tf.split("/")[1]
        base = f"{label}__{os.path.basename(tf)}".replace(
            ".jsonl.gz", ".json.gz")
        fn = idx.get(base)
        if fn:
            d = json.load(gzip.open(fn, "rt"))
            e["_cache"] = d


def prog_of_depth(d):
    return 100.0 * ACH.get(f"Dlvl:{d}", 0.0)


def ceilings(block, nboot=3000, seed=7):
    """Counterfactual expected block mean per eliminated cause class."""
    rng = random.Random(seed)
    causes = sorted({e["cls"] for e in block if e["cls"] != "ABORT"})

    def model_mean(eps, drop_cls):
        maxd = max(e["depth_max"] for e in eps)
        # empirical mean score by max depth
        by_d = collections.defaultdict(list)
        for e in eps:
            by_d[e["depth_max"]].append(e["progression"] * 100)
        mean_at = {d: sum(v) / len(v) for d, v in by_d.items()}
        # hazard per depth
        reach = {d: sum(1 for e in eps if e["depth_max"] >= d)
                 for d in range(1, maxd + 1)}
        total = 0.0
        p_reach = 1.0
        for d in range(1, maxd + 1):
            die_all = sum(1 for e in eps if e["depth_max"] == d)
            die_keep = sum(1 for e in eps if e["depth_max"] == d and
                           e["cls"] != drop_cls)
            h = die_keep / reach[d] if reach[d] else 1.0
            if d == maxd:
                h = 1.0     # truncate: survivors get frontier score
            p_die = p_reach * h
            score = mean_at.get(d)
            if score is None:
                score = prog_of_depth(d)
            total += p_die * score
            p_reach -= p_die
        total += p_reach * mean_at.get(maxd, prog_of_depth(maxd))
        return total

    out = {}
    base = model_mean(block, None)
    out["_model_baseline"] = base
    for c in causes:
        pt = model_mean(block, c)
        boots = []
        for _ in range(nboot):
            samp = [block[rng.randrange(len(block))] for _ in block]
            boots.append(model_mean(samp, c) - model_mean(samp, None))
        boots.sort()
        lo = boots[int(0.025 * nboot)]
        hi = boots[int(0.975 * nboot)]
        out[c] = dict(ceiling=pt, delta=pt - base, ci=[lo, hi],
                      n_deaths=sum(1 for e in block if e["cls"] == c))
    return out


def main():
    main_eps = load_main()
    blind_eps = load_blind()
    attach_cache(main_eps)
    for e in main_eps + blind_eps:
        fin = (e.get("_cache") or {}).get("final")
        e["cls"] = classify(e["end_reason"], fin)
        e["species"] = species_of(e["end_reason"])
        if fin:
            e["death_depth"] = fin["depth"]
            e["death_turn"] = fin["t"]
            e["death_hunger"] = fin["hunger"]
            e["death_hpfrac"] = fin["hp"] / max(1, fin["hpmax"])

    all_eps = main_eps + blind_eps
    print(f"episodes: main {len(main_eps)}, blind {len(blind_eps)}")

    # ---- taxonomy over everything
    tab = collections.Counter((e["cls"]) for e in all_eps)
    print("\n## Death-cause taxonomy (ALL logged episodes, both arms)")
    for c, n in tab.most_common():
        print(f"  {c:12s} {n}")

    spec = collections.Counter(e["species"] for e in all_eps
                               if e["species"])
    print("\n## Top killer species (all arms)")
    for s, n in spec.most_common(15):
        print(f"  {s:20s} {n}  diff={DIFF.get(s)} speed={SPEED.get(s)}")

    # ---- v1.1 block detail (the baseline for Campaign 2)
    block = [e for e in main_eps if e["arm"] == "v11_block80"]
    print(f"\n## v1.1 n=80 block: cause x depth-band x role")
    cx = collections.Counter()
    for e in block:
        band = ("d1-2" if e["depth_max"] <= 2 else
                "d3-5" if e["depth_max"] <= 5 else
                "d6-8" if e["depth_max"] <= 8 else "d9+")
        cx[(e["cls"], band)] += 1
    for (c, b), n in sorted(cx.items()):
        print(f"  {c:12s} {b:5s} {n}")

    # hazard curve
    maxd = max(e["depth_max"] for e in block)
    print("\n## v1.1 hazard by depth: reach / die / h(d) (+ per class)")
    for d in range(1, maxd + 1):
        reach = sum(1 for e in block if e["depth_max"] >= d)
        die = [e for e in block if e["depth_max"] == d]
        if not reach:
            continue
        cc = collections.Counter(e["cls"] for e in die)
        print(f"  D{d:2d} reach {reach:3d} die {len(die):2d} "
              f"h={len(die)/reach:.2f}  {dict(cc)}")

    # ---- counterfactual ceilings
    print("\n## Counterfactual ceilings (v1.1 n=80 block, eliminate class)")
    ceil = ceilings(block)
    print(f"  model baseline {ceil['_model_baseline']:.2f} "
          f"(actual mean {sum(e['progression']*100 for e in block)/len(block):.2f})")
    for c, v in sorted(((k, v) for k, v in ceil.items()
                        if not k.startswith('_')),
                       key=lambda kv: -kv[1]["delta"]):
        print(f"  -{c:12s} -> {v['ceiling']:5.2f}  delta +{v['delta']:.2f} "
              f" boot[{v['ci'][0]:+.2f},{v['ci'][1]:+.2f}]  "
              f"(n={v['n_deaths']})")

    # ---- per-role
    print("\n## v1.1 per-role")
    byrole = collections.defaultdict(list)
    for e in block:
        byrole[e.get("role") or "?"].append(e)
    for r, es in sorted(byrole.items(), key=lambda kv: -len(kv[1])):
        m = sum(e["progression"] * 100 for e in es) / len(es)
        dd = sum(e["depth_max"] for e in es) / len(es)
        print(f"  {r:12s} n={len(es):2d} mean {m:5.2f} avg maxdepth {dd:.1f}")

    # ---- death turn / retreat mismatch / hunger state
    dt = [e for e in block if "death_turn" in e]
    if dt:
        turns = sorted(e["death_turn"] for e in dt)
        print(f"\n## v1.1 death turns: median {turns[len(turns)//2]}, "
              f"q1 {turns[len(turns)//4]}, q3 {turns[3*len(turns)//4]}")
        mism = [e for e in dt if e.get("death_depth", 0) <
                e["depth_max"]]
        print(f"  deaths above max depth (retreat/upstairs): {len(mism)}")
        hstarv = [e for e in dt if e["cls"] == "STARVATION"]
        print(f"  starvation deaths in block: {len(hstarv)} "
              f"turns {[e['death_turn'] for e in hstarv]}")
        low = [e for e in dt if e.get("death_hpfrac", 1) < 0.5 and
               e["cls"] not in ("STARVATION", "ABORT")]
        print(f"  combat deaths entered final frame <50% hp: {len(low)}/"
              f"{len([e for e in dt if e['cls'] not in ('STARVATION','ABORT')])}")

    json.dump(
        dict(taxonomy=dict(tab), species=dict(spec), ceilings=ceil,
             block=[{k: v for k, v in e.items() if k != "_cache"}
                    for e in block]),
        open(os.path.join(RESULTS, "c2_forensics.json"), "w"), indent=1)
    print("\nwrote results/c2_forensics.json")


if __name__ == "__main__":
    main()

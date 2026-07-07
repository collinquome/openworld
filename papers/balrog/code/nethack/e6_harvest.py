"""E-NH6 GYM HARVEST — build the scenario library from the death corpus.

MODEL: Fable 5 (max reasoning), Phase L session 2.

Sources:
  1. NH-E12 retro corpus (163 typed combat deaths, e12_retros.json)
  2. any results/nethack_results_*.json episodes whose transitions files
     still exist on disk (these are BRANCHABLE: (seed, action-prefix) via
     nh_branch is a real state snapshot — the gym can replay them)

Output: results/e6_scenarios.json
  {"scenarios": [{id, class, seed, role, depth, killer, end_reason,
                  label, transitions_file(or null), branchable,
                  lesson_type(if retro'd), status: "OPEN"}],
   "syllabus": top classes by death mass with per-class scenario counts
               and branchable counts}

Gym guardrails (program doc): dev/harvested seeds only; scored blocks are
never replayed FOR SCORE — harvesting their death states as scenarios is
the sanctioned use. Solving a scenario = a rule card passing the
≥3-different-seed generalization gate; solved scenarios become permanent
regression fixtures.
"""

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
E12 = os.path.join(HERE, "..", "wt-fable-nethack", "papers", "balrog",
                   "experiments", "NH-E12-death-retro", "results",
                   "e12_retros.json")


def main():
    scenarios = {}
    # source 2: all results episodes with living transitions files
    for fn in sorted(glob.glob(os.path.join(RESULTS,
                                            "nethack_results_*.json"))):
        try:
            doc = json.load(open(fn))
        except Exception:
            continue
        label = doc.get("label") or os.path.basename(fn)
        for e in doc.get("episodes", []):
            er = e.get("end_reason", "")
            if not er.startswith("DEATH"):
                continue
            tf = e.get("transitions_file")
            tpath = os.path.join(RESULTS, tf) if tf else None
            branchable = bool(tpath and os.path.exists(tpath))
            sid = f"{label}_{e['seed']}"
            if sid in scenarios and not branchable:
                continue
            scenarios[sid] = {
                "id": sid, "seed": e["seed"], "role": e.get("role"),
                "depth": e.get("depth_max"), "end_reason": er,
                "label": label,
                "transitions_file": tf if branchable else None,
                "branchable": branchable, "class": None,
                "lesson_type": None, "status": "OPEN",
            }
    # source 1: retro corpus classes (join on death_id prefix conventions)
    retros = json.load(open(E12))
    matched = 0
    for r in retros:
        did = r["death_id"]          # e.g. baseline25_2005 / c2block80_4053
        hit = scenarios.get(did)
        if hit is None:
            # try suffix-seed match across labels
            cands = [s for s in scenarios.values()
                     if did.endswith(f"_{s['seed']}") or
                     s["id"].endswith(did.split("_")[-1])]
            hit = None
        if hit:
            hit["class"] = r["class"]
            hit["lesson_type"] = r.get("lesson_type")
            matched += 1
    # classify the rest via c2_classes
    sys.path.insert(0, HERE)
    import c2_classes as CC
    for s in scenarios.values():
        if s["class"] is None:
            try:
                s["class"] = CC.classify(s["end_reason"])
            except Exception:
                s["class"] = "UNCLASSIFIED"

    # unify the two class taxonomies (E12 retro names -> c2_classes names)
    UNIFY = {"MELEE_TRASH": "TRASH", "MELEE_OTHER": "MELEE+",
             "SPIDER_ANT": "SPIDANT", "PRAY_DEATH": "PRAY",
             "RANGED": "RANGED", "STARVATION": "STARV"}
    for s in scenarios.values():
        s["class"] = UNIFY.get(s["class"], s["class"])

    # syllabus: death mass by class, with branchable counts
    mass = {}
    for s in scenarios.values():
        m = mass.setdefault(s["class"], {"n": 0, "branchable": 0,
                                         "seeds": set()})
        m["n"] += 1
        m["branchable"] += int(s["branchable"])
        m["seeds"].add(s["seed"])
    syllabus = sorted(
        ({"class": k, "n": v["n"], "branchable": v["branchable"],
          "distinct_seeds": len(v["seeds"])} for k, v in mass.items()),
        key=lambda x: -x["n"])

    out = {"scenarios": sorted(scenarios.values(), key=lambda s: s["id"]),
           "syllabus": syllabus,
           "retro_matched": matched,
           "total": len(scenarios)}
    ofn = os.path.join(RESULTS, "e6_scenarios.json")
    with open(ofn, "w") as f:
        json.dump(out, f, indent=1)
    print(f"scenarios {len(scenarios)} (branchable "
          f"{sum(1 for s in scenarios.values() if s['branchable'])}), "
          f"retro-matched {matched}")
    for row in syllabus[:8]:
        print(row)


if __name__ == "__main__":
    main()

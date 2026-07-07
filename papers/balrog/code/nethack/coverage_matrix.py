"""HYPOTHESIS COVERAGE MATRIX (Phase L exit criterion i).

MODEL: Fable 5 (max reasoning), session 2 — formalization + evidence seed.

Grid: rule-card/mechanism x death-class. Cell statuses:
  VERIFIED    paired-dev or by-death evidence, cited
  PROVISIONAL evidence exists, below the ship bar / role-scoped subset
  UNTESTED    applicable, no evidence -> AUTO-ENUMERATED open hypothesis
  N/A         mechanism cannot bear on this class (excluded from the
              denominator)

Resolution %% is DEATH-MASS-WEIGHTED by class (weights = live gym
syllabus, results/e6_scenarios.json) — criterion (i) needs >=70%% of
weighted applicable cells VERIFIED-or-refuted. PROVISIONAL counts half.

Usage: python3 coverage_matrix.py   (reads matrix seed below + syllabus,
writes results/coverage_matrix.json + prints the table)
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

CLASSES = ["TRASH", "MELEE+", "STARV", "SPIDANT", "RANGED", "PRAY"]

# status, evidence (None => UNTESTED)
V, P, NA = "VERIFIED", "PROVISIONAL", "N/A"
M = {
  "CAST_ATTACK_V1.1": {
    "TRASH":   (P, "CAST-2 +2.41 [+0.75,+4.41] Wizards; role-scoped"),
    "MELEE+":  (P, "same block; deeper death mix"),
    "STARV":   (NA, None), "SPIDANT": (None, None),
    "RANGED":  (None, None), "PRAY": (NA, None)},
  "CAST_NEVER_PEACEFUL_CLASS": {
    "TRASH": (NA, None), "MELEE+": (V, "CAST-1 shop deaths 3->0 in CAST-2"),
    "STARV": (NA, None), "SPIDANT": (NA, None), "RANGED": (NA, None),
    "PRAY": (NA, None)},
  "CAST_HUNGER_V1": {
    "TRASH": (NA, None), "MELEE+": (NA, None),
    "STARV": (None, None),  # CASTHUNGER-1 running
    "SPIDANT": (NA, None), "RANGED": (NA, None), "PRAY": (NA, None)},
  "TOUCH_KILL_WEAPON_MELEE": {
    "TRASH": (NA, None), "MELEE+": (V, "seed-705 chickatrice death gone "
                                       "under frozen config; source read"),
    "STARV": (NA, None), "SPIDANT": (NA, None), "RANGED": (NA, None),
    "PRAY": (NA, None)},
  "FOOD2": {
    "TRASH": (NA, None), "MELEE+": (NA, None),
    "STARV": (V, "shipped +1.12; starvation-class reduction (C2-ENH2)"),
    "SPIDANT": (NA, None), "RANGED": (NA, None),
    "PRAY": (P, "fewer desperation hunger-prayers downstream")},
  "PRAYFIX": {
    "TRASH": (NA, None), "MELEE+": (NA, None), "STARV": (NA, None),
    "SPIDANT": (NA, None), "RANGED": (NA, None),
    "PRAY": (V, "PRAY_DEATH lever shipped; hostile-adjacent prayer gated")},
  "LOS_TRAVEL": {
    "TRASH": (NA, None), "MELEE+": (NA, None), "STARV": (NA, None),
    "SPIDANT": (NA, None),
    "RANGED": (P, "NAV group +2.25 shipped (LOS inside the bundle)"),
    "PRAY": (NA, None)},
  "KITE_TO_CHOKE (A7)": {
    "TRASH": (None, None), "MELEE+": (None, None), "STARV": (NA, None),
    "SPIDANT": (None, None),   # largest avoidable mass every audit
    "RANGED": (NA, None), "PRAY": (NA, None)},
  "THROW_AT_BLOCKER": {
    "TRASH": (P, "blocker removal evidence (dev 116 fixture)"),
    "MELEE+": (None, None), "STARV": (NA, None), "SPIDANT": (None, None),
    "RANGED": (NA, None), "PRAY": (NA, None)},
  "REST_GATES (A8)": {
    "TRASH": (P, "e6_solve s3: REST survives 10/20 TRASH deaths on 10 "
                 "distinct dev seeds (deterministic branch counterfactual,"
                 " e6_solve_trash.json); lever not yet paired-dev"),
    "MELEE+": (None, None), "STARV": (None, None),
    "SPIDANT": (None, None), "RANGED": (NA, None), "PRAY": (NA, None)},
  "FLEE_GATE (A6)": {
    "TRASH": (P, "e6_solve s3: RETREAT survives 6/20 TRASH deaths, "
                 "distinct seeds (e6_solve_trash.json); subset of REST "
                 "wins; lever not yet paired-dev"),
    "MELEE+": (None, None), "STARV": (NA, None),
    "SPIDANT": (None, None), "RANGED": (None, None), "PRAY": (NA, None)},
  "STALL_WATCHDOG_V1": {
    "TRASH": (NA, None), "MELEE+": (NA, None),
    "STARV": (P, "E15-1 s3: hunger deaths 10->5 on the paired block "
                 "(watchdog breaks stall-starve loops); shipped as "
                 "robustness lever, progression-unclear"),
    "SPIDANT": (NA, None), "RANGED": (NA, None), "PRAY": (NA, None)},
  "REPEAT_LAYOUT_STAIRS_V2": {
    "TRASH": (NA, None), "MELEE+": (NA, None),
    "STARV": (None, None),  # descent speed vs food clock; REPEAT-2 running
    "SPIDANT": (NA, None), "RANGED": (NA, None), "PRAY": (NA, None)},
  "WIELD_DOCTRINE (P2, unbuilt)": {
    "TRASH": (None, None), "MELEE+": (None, None), "STARV": (NA, None),
    "SPIDANT": (None, None), "RANGED": (NA, None), "PRAY": (NA, None)},
  "ARMOR_DOCTRINE (P3, unbuilt)": {
    "TRASH": (None, None), "MELEE+": (None, None), "STARV": (NA, None),
    "SPIDANT": (None, None), "RANGED": (None, None), "PRAY": (NA, None)},
  "ZAP_DOCTRINE (unbuilt; RAY_BOUNCE card)": {
    "TRASH": (None, None), "MELEE+": (None, None), "STARV": (NA, None),
    "SPIDANT": (None, None), "RANGED": (NA, None), "PRAY": (NA, None)},
}


def main():
    syl = json.load(open(os.path.join(RESULTS, "e6_scenarios.json")))
    mass = {r["class"]: r["n"] for r in syl["syllabus"]}
    wsum = sum(mass.get(c, 0) for c in CLASSES)
    weights = {c: mass.get(c, 0) / wsum for c in CLASSES}

    resolved_w = applicable_w = 0.0
    open_hyps = []
    for card, row in M.items():
        for c in CLASSES:
            status, ev = row[c]
            if status == NA:
                continue
            applicable_w += weights[c]
            if status == V:
                resolved_w += weights[c]
            elif status == P:
                resolved_w += weights[c] * 0.5
            else:
                open_hyps.append({"card": card, "class": c,
                                  "weight": round(weights[c], 3)})
    open_hyps.sort(key=lambda h: -h["weight"])
    fill = resolved_w / applicable_w if applicable_w else 0.0

    out = {"classes": CLASSES, "weights": weights,
           "matrix": {card: {c: {"status": row[c][0] or "UNTESTED",
                                 "evidence": row[c][1]}
                             for c in CLASSES} for card, row in M.items()},
           "open_hypotheses": open_hyps,
           "weighted_fill": fill,
           "criterion_i_pass": fill >= 0.70}
    with open(os.path.join(RESULTS, "coverage_matrix.json"), "w") as f:
        json.dump(out, f, indent=1)

    hdr = "card".ljust(38) + "".join(c.ljust(9) for c in CLASSES)
    print(hdr)
    for card, row in M.items():
        line = card[:37].ljust(38)
        for c in CLASSES:
            s = row[c][0] or "UNTESTED"
            line += {"VERIFIED": "VER", "PROVISIONAL": "prov",
                     "N/A": "-", "UNTESTED": "open"}[s].ljust(9)
        print(line)
    print(f"\nweighted fill: {fill:.1%} (criterion i needs >=70%)  "
          f"open hypotheses: {len(open_hyps)}")
    print("top open by death-mass:", open_hyps[:5])


if __name__ == "__main__":
    main()

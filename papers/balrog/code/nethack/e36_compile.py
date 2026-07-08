"""NH-E36 COMPILE — winner -> provenance-tagged rule card (step 4 of pipeline).

MODEL: claude-opus-4-8 (max thinking), NH-E36.

Reads the ranking JSON (e36_simulate --aggregate output), selects the winning
candidate, and emits a RULE CARD: a scenario-matcher PREDICATE over served obs +
the winning action-policy, flag-gated (default-OFF, bit-identical off by
construction since it lives in its own module and is only consulted when
NH_E36 is set AND the predicate fires). Dual provenance + replication recipe.

The predicate defines the TRASH crisis the winner was ranked to solve:
  >=1 MOBILE hostile ADJACENT (chebyshev 1)  AND
  hp_frac <= HP_GATE                          AND
  depth in [2, 7]   (the D2-6 kill-zone the corpus is dominated by)
When it fires the agent yields to the winning policy until no mobile hostile is
adjacent (crisis over); otherwise the agent's normal policy runs unchanged.

Usage: python3 e36_compile.py results/e36_trash_ranking.json
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(HERE, "pylib"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

HP_GATE = 0.55            # "low-ish HP" trash crisis (tunable; pre-registered)
DEPTH_LO, DEPTH_HI = 2, 7


def crisis_predicate(A, obs):
    """TRASH-crisis scenario matcher over the agent's OWN served perception."""
    import nh_common as C
    from nle import nethack as nh
    bl = obs["obs"]["blstats"]
    hp, hpmax = int(bl[nh.NLE_BL_HP]), max(1, int(bl[nh.NLE_BL_HPMAX]))
    depth = int(bl[nh.NLE_BL_DEPTH])
    if not (DEPTH_LO <= depth <= DEPTH_HI):
        return False
    if hp / hpmax > HP_GATE:
        return False
    ax, ay = A.agent
    L = A.level
    for m in L.monsters:
        if m.pet or m.name in C.IMMOBILE or m.pos in L.no_attack:
            continue
        if max(abs(m.x - ax), abs(m.y - ay)) == 1:
            return True
    return False


def compile_winner(ranking_path):
    doc = json.load(open(ranking_path))
    ranking = doc["ranking"]
    from e36_candidates import REGISTRY
    polmap = {r[0]: r for r in REGISTRY}
    winner = ranking[0]
    name = winner["name"]
    prov = winner["prov"]
    kite = doc.get("kite_survival_rate", 0.0)
    card = {
        "id": "E36-TRASH-1",
        "scenario": "TRASH crisis: mobile hostile adjacent, hp_frac<=%.2f, D%d-%d"
                    % (HP_GATE, DEPTH_LO, DEPTH_HI),
        "winner": name,
        "winner_policy_fn": "e36_candidates.%s" % polmap[name][1].__name__,
        "predicate_fn": "e36_compile.crisis_predicate",
        "flag": "NH_E36",
        "default": "OFF (bit-identical off — separate module, consulted only "
                   "when NH_E36 set AND predicate fires)",
        "survival_rate": winner["survival_rate"],
        "escape_rate": winner["escape_rate"],
        "distinct_seeds_won": winner["distinct_seeds_won"],
        "mean_depth_gain": winner["mean_depth_gain"],
        "class_solve": winner["class_solve"],
        "vs_kite_hand_lever": round(winner["survival_rate"] - kite, 3),
        "knowledge": "SYNTHESIS" if prov == "SYNTHESIS" else "DEMONSTRATION",
        "insight_origin": "OP (scenario-strategy synthesis)",
        "provenance": prov,
        "replication_recipe": (
            "python3 e36_simulate.py --seeds <TRASH dev seeds> --backoff 40 "
            "--window 400 --budget 350 --out results/e36_trash.jsonl ; "
            "python3 e36_simulate.py --aggregate results/e36_trash.jsonl ; "
            "python3 e36_compile.py results/e36_trash_ranking.json"),
        "model": "claude-opus-4-8 (max thinking), NH-E36",
        "when": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_adjudicated": doc.get("n_adjudicated"),
        "full_ranking": [{"name": r["name"], "prov": r["prov"],
                          "survival_rate": r["survival_rate"],
                          "escape_rate": r["escape_rate"],
                          "seeds_won": r["distinct_seeds_won"],
                          "depth_gain": r["mean_depth_gain"],
                          "class_solve": r["class_solve"]} for r in ranking],
    }
    out = ranking_path.replace("_ranking.json", "_rulecard.json")
    json.dump(card, open(out, "w"), indent=1)
    print(json.dumps({k: card[k] for k in
                      ("id", "winner", "provenance", "survival_rate",
                       "vs_kite_hand_lever", "class_solve", "escape_rate",
                       "mean_depth_gain")}, indent=1))
    print("wrote", out)
    return card


if __name__ == "__main__":
    compile_winner(sys.argv[1] if len(sys.argv) > 1
                   else os.path.join(HERE, "results", "e36_trash_ranking.json"))

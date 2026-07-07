"""REST/disengage lever paired block (NH-E6 solve-loop-sourced lever).
MODEL: claude-opus-4-8[1m] (max thinking), Phase L session 4.

Proximal KPI (KPI_TREE.md): survival-to-depth via TRASH-death rate.
Condition set by env BEFORE import: REF = knobs unset (CRISIS_HP 0.28 /
CRISIS_EXCH 2.0, bit-identical to pre-s4); TEST = NH_CRISIS_HP=0.40
NH_CRISIS_EXCH=1.5 (break contact earlier). Same seeds both conditions.

Usage:  python3 pair_rest.py <cond>            # ref
        NH_CRISIS_HP=0.40 NH_CRISIS_EXCH=1.5 python3 pair_rest.py test
"""
import json
import os
import sys
import nh_agent
import nh_runner

COND = sys.argv[1] if len(sys.argv) > 1 else "ref"
# Step cap (applied IDENTICALLY to both conditions): this lever's proximal
# KPI is TRASH-death rate (early deaths, <2000 steps), so a cap bounds
# wallclock without biasing the paired death-avoidance read. Disclosed.
nh_runner.MAX_LOOP = int(os.environ.get("REST_CAP", "4000"))
# e6_solve TRASH REST-win seeds (ledger) + fresh controls (780-791 untouched)
# fast-dying TRASH seeds first (706=267 steps, 709=548), pathological-slow
# 701 last so partial results stream even if it truncates.
RESTWIN = [706, 709, 724, 725, 737, 738, 704, 721, 723, 733, 701]
FRESH = list(range(780, 785))
SEEDS = RESTWIN + FRESH

out = {"cond": COND,
       "knobs": {"CRISIS_HP": nh_agent.CRISIS_HP,
                 "CRISIS_EXCH": nh_agent.CRISIS_EXCH},
       "restwin_seeds": RESTWIN, "fresh_seeds": FRESH, "eps": {}}
for s in SEEDS:
    r = nh_runner.run_episode(ep=s, seed=s, condition=COND, label="restlv",
                              log=lambda *a, **k: None)
    er = r["end_reason"]
    out["eps"][str(s)] = {
        "role": r["role"], "prog": r["progression"],
        "depth_max": r["depth_max"], "steps": r["steps"],
        "end_reason": er, "death": er.startswith("DEATH")}
    print(f"{COND} {s} {r['role'][:9]:9} prog={r['progression']:.3f} "
          f"D{r['depth_max']} {'DIED' if er.startswith('DEATH') else 'alive'} "
          f"| {er[:55]}", flush=True)

fn = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "results", f"rest_lever_{COND}.json")
json.dump(out, open(fn, "w"), indent=1)
print(f"WROTE {fn}")

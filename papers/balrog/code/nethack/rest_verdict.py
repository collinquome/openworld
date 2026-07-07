"""REST-lever paired verdict. MODEL: claude-opus-4-8[1m] s4.
Reads rest_lever_ref/test.json, computes paired deltas + the proximal KPI
(TRASH-death / survival-to-depth). Uses bootstrap_ci for the mean-prog delta.
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bootstrap_ci import ci95

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
ref = json.load(open(os.path.join(R, "rest_lever_ref.json")))
tst = json.load(open(os.path.join(R, "rest_lever_test.json")))
common = [s for s in ref["eps"] if s in tst["eps"]]
restwin = set(str(s) for s in ref["restwin_seeds"])

deltas, div, td, alive_t, alive_r = [], 0, 0, 0, 0
per = []
for s in common:
    a, b = ref["eps"][s], tst["eps"][s]
    dp = b["prog"] - a["prog"]
    dd = b["depth_max"] - a["depth_max"]
    deltas.append(dp)
    diverged = abs(dp) > 1e-6 or b["end_reason"] != a["end_reason"]
    div += diverged
    if not a["death"]:
        alive_r += 1
    if not b["death"]:
        alive_t += 1
    per.append((s, s in restwin, a["depth_max"], b["depth_max"], round(dp, 3),
                dd, "DIV" if diverged else "="))

print(f"paired seeds: {len(common)}  (restwin {sum(1 for s in common if s in restwin)}, "
      f"fresh {sum(1 for s in common if s not in restwin)})")
print(f"knobs ref={ref['knobs']} test={tst['knobs']}")
print(f"{'seed':6}{'win?':6}{'Dref':6}{'Dtest':6}{'dprog':8}{'dD':5} flag")
for s, rw, dr, dt2, dp, dd, fl in per:
    print(f"{s:<6}{'RW' if rw else 'fr':<6}{dr:<6}{dt2:<6}{dp:<8}{dd:<5}{fl}")
lo, hi = ci95(deltas)
mean = sum(deltas) / len(deltas)
print(f"\nmean paired prog delta (test-ref): {mean:+.3f}  CI95 [{lo:+.3f},{hi:+.3f}]")
print(f"divergent: {div}/{len(common)}   deaths: ref {len(common)-alive_r}/{len(common)} "
      f"test {len(common)-alive_t}/{len(common)}")
rw_delt = [per[i][4] for i, s in enumerate(common) if s in restwin]
print(f"restwin-only mean dprog: {sum(rw_delt)/len(rw_delt):+.3f} (n={len(rw_delt)})")

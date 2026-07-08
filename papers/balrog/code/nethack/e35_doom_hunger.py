"""NH-E35/s10 — DOOM-MOMENT LOOP applied to the hunger death class (offline,
tier-analytic; justified because hunger is near-deterministic: nutrition depletes
~1/turn, eating resets it, so the last-safe point is analytic, not MC-search).

For every corpus episode that reached Fainting (peak hunger tier >= 4), locate the
recoverable window = steps of warning between the guard-actionable tier (Hungry)
and Fainting, and confirm the doom moment lands at the Hungry->Weak boundary
(=> corrected decision is eat-at-Hungry). Independently rediscovers the S9-2
expert hunger law from our OWN death corpus by a different method.

Usage: python3 e35_doom_hunger.py
"""
import glob, json, os, statistics as st

HUNGRY, WEAK, FAINT = 2, 3, 4


def main():
    rows = []
    for f in glob.glob("results/trajectories/*.json"):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        h = d.get("hunger") or [0]
        if max(h) < FAINT:
            continue

        def first(t):
            for i, x in enumerate(h):
                if x >= t:
                    return i
            return None
        rows.append(dict(th=first(HUNGRY), tw=first(WEAK), tf=first(FAINT),
                         tend=len(h) - 1))
    n = len(rows)
    print(f"fainting-corpus episodes: {n}")

    def dist(name, vals):
        vals = sorted(v for v in vals if v is not None)
        if not vals:
            print(f"{name}: none"); return
        print(f"{name}: n={len(vals)} median={st.median(vals):.0f} "
              f"mean={st.mean(vals):.0f} p10={vals[len(vals)//10]} "
              f"p90={vals[9*len(vals)//10]} max={max(vals)}")
    dist("window Hungry->Fainting (warning at guard-actionable tier)",
         [r['tf'] - r['th'] for r in rows if r['th'] is not None and r['tf'] is not None])
    dist("window Weak->Fainting (old-guard warning)",
         [r['tf'] - r['tw'] for r in rows if r['tw'] is not None and r['tf'] is not None])
    dist("window Fainting->end (faint cascade)",
         [r['tend'] - r['tf'] for r in rows])
    via = sum(1 for r in rows if r['th'] is not None and r['th'] < r['tf'])
    longw = sum(1 for r in rows if r['th'] is not None and r['tf'] is not None
                and (r['tf'] - r['th']) >= 50)
    print(f"passed through Hungry before Fainting (guard has a shot): {via}/{n}")
    print(f"window Hungry->Fainting >= 50 steps (foreseeable slow death): {longw}/{n}")


if __name__ == "__main__":
    main()

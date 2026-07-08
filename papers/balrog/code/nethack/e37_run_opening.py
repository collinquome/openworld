"""NH-E37 — per-class OPENING paired-block runner + preventive-KPI analysis.

MODEL: claude-opus-4-8 (max thinking), Phase L NH-E37.

Design (addresses the two E36 hand-off lessons):
  (1) LIVE-FIRING / anti-mechanical-null: for every episode we record a
      BEHAVIORAL FINGERPRINT (cast/throw/elbereth/pray/eat counts + fire
      counters) so REF vs TEST divergence is MEASURED, not assumed. A card
      that produces an identical fingerprint to REF is a mechanical null
      (the E36 signature-fidelity trap) and is reported as such.
  (2) PREVENTIVE framing: reliability = NOT ENTERING the 0-survivor crisis
      band. PRIMARY KPIs = survival@D5 and CRISIS-ENTRY RATE (# transitions
      into hp_frac < CRISIS band), not combat-death-given-crisis.

One seed PER PROCESS (s8 cross-seed-leakage law) AND env set before import
(module-level flag read). Orchestrator spawns a --worker subprocess per
(seed,arm) with the composed env. Resumable JSONL.

REF = frozen C2.1 (e37_opening.REF_ENV). TEST = REF + rolled-class card.
Clean-protocol: OFFLINE-derived policy; scored runs pure code.

Usage:
  PYTHONPATH=pylib python3 e37_run_opening.py --class Wizard --n 15 --cap 2000 --out results/e37_wizard.jsonl
  PYTHONPATH=pylib python3 e37_run_opening.py --analyze results/e37_wizard.jsonl
  (worker, internal) PYTHONPATH=pylib python3 e37_run_opening.py --worker <seed> <arm> <cap> <out>
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CRISIS = 0.28   # hp_frac crisis band (matches nh_agent CRISIS_HP default)

_EAT = ("you eat", "you finish eating", "you devour", "you swallow")
_CAST = ("you cast", "force bolt")
_ELB = ("you engrave", "elbereth", "you write")
_PRAY = ("you finish your prayer", "you begin praying")
_THROW = ("you throw", "finds a mark", "you shoot")


def _count(msgs, keys):
    n = 0
    for m in msgs:
        ml = m.lower()
        if any(k in ml for k in keys):
            n += 1
    return n


def worker(seed, arm, cap, out):
    """Env already composed by parent. Run one episode, append KPI row."""
    import nh_runner
    nh_runner.MAX_LOOP = cap
    res = nh_runner.run_episode(ep=seed, seed=seed, condition="dev",
                                label=f"e37_{arm}_{seed}", log=lambda *a: None)
    # load the trajectory just written for the preventive/behavioral KPIs
    tj = os.path.join(nh_runner.TRAJ, f"e37_{arm}_{seed}__ep{seed}.json")
    hp = depth = hunger = []
    msgs = []
    try:
        traj = json.load(open(tj))
        hp = traj.get("hp", [])
        msgs = traj.get("messages", [])
    except Exception:
        pass
    # crisis-entry rate: transitions INTO hp_frac < CRISIS (preventive KPI)
    crisis_entries = 0
    min_hpfrac = 1.0
    prev_below = False
    for pair in hp:
        try:
            h, hm = pair
            frac = h / max(1, hm)
        except Exception:
            continue
        min_hpfrac = min(min_hpfrac, frac)
        below = frac < CRISIS
        if below and not prev_below:
            crisis_entries += 1
        prev_below = below
    row = {
        "seed": seed, "arm": arm, "role": res.get("role"),
        "progression": res.get("progression"),
        "depth_max": res.get("depth_max"),
        "surv_d5": 1 if (res.get("depth_max") or 0) >= 5 else 0,
        "xplvl_max": res.get("xplvl_max"),
        "end_reason": res.get("end_reason"),
        "steps": res.get("steps"),
        "wall_s": res.get("wallclock_s"),
        # preventive KPIs
        "crisis_entries": crisis_entries,
        "min_hpfrac": round(min_hpfrac, 3),
        # behavioral fingerprint (anti-mechanical-null: TEST must diverge)
        "fp_eat": _count(msgs, _EAT),
        "fp_cast": _count(msgs, _CAST),
        "fp_elbereth": _count(msgs, _ELB),
        "fp_pray": _count(msgs, _PRAY),
        "fp_throw": _count(msgs, _THROW),
        "cast_fires": res.get("cast_fires"),
        "throw_fires": res.get("throw_fires"),
    }
    with open(out, "a") as fh:
        fh.write(json.dumps(row) + "\n")
    print(f"  {arm} seed={seed} role={row['role']} prog={row['progression']:.4f} "
          f"D{row['depth_max']} surv5={row['surv_d5']} crisis={crisis_entries} "
          f"minHP={row['min_hpfrac']} fp[eat{row['fp_eat']} cast{row['fp_cast']} "
          f"elb{row['fp_elbereth']} pray{row['fp_pray']} thr{row['fp_throw']}] "
          f"wall={row['wall_s']}s")


def run_block(role, n, cap, out):
    import e37_opening
    import role_seeds
    seeds = role_seeds.seeds_for(role, n)
    if not seeds:
        print(f"no census seeds for {role}")
        return
    print(f"=== E37 opening block: {role} n={len(seeds)} cap={cap} -> {out} ===")
    print(f"    card: {e37_opening.OPENING_CARDS.get(role, {}).get('env')}")
    open(out, "a").close()
    done = set()
    for line in open(out):
        try:
            r = json.loads(line)
            done.add((r["seed"], r["arm"]))
        except Exception:
            pass
    for seed in seeds:
        for arm in ("REF", "TEST"):
            if (seed, arm) in done:
                print(f"  skip {arm} {seed} (done)")
                continue
            env, _role, has = e37_opening.opening_env_for(seed, arm)
            child = dict(os.environ)
            child.update(env)
            cmd = [sys.executable, os.path.join(HERE, "e37_run_opening.py"),
                   "--worker", str(seed), arm, str(cap), out]
            subprocess.run(cmd, env=child, timeout=cap * 2 + 300)
    print("BLOCK_DONE")


def analyze(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    by = {}
    for r in rows:
        by.setdefault((r["seed"], r["arm"]), r)
    seeds = sorted({s for (s, a) in by})
    paired = [(s, by[(s, "REF")], by[(s, "TEST")])
              for s in seeds if (s, "REF") in by and (s, "TEST") in by]
    if not paired:
        print("no complete pairs yet")
        return

    def mean(f):
        rr = [f(ref) for _s, ref, _t in paired]
        tt = [f(t) for _s, _r, t in paired]
        return sum(rr) / len(rr), sum(tt) / len(tt)

    role = paired[0][1].get("role")
    print(f"\n=== E37 {role} paired analysis (n={len(paired)}) ===")
    for name, f in [("progression", lambda r: r["progression"]),
                    ("depth_max", lambda r: r["depth_max"]),
                    ("surv@D5", lambda r: r["surv_d5"]),
                    ("crisis_entries", lambda r: r["crisis_entries"]),
                    ("min_hpfrac", lambda r: r["min_hpfrac"])]:
        mr, mt = mean(f)
        print(f"  {name:16s} REF={mr:.4f}  TEST={mt:.4f}  Δ={mt-mr:+.4f}")
    # behavioral divergence (live-firing proof)
    div = 0
    for _s, ref, t in paired:
        for k in ("fp_cast", "fp_elbereth", "fp_pray", "fp_throw", "fp_eat"):
            if (ref.get(k) or 0) != (t.get(k) or 0):
                div += 1
                break
    print(f"  behavioral divergence: {div}/{len(paired)} pairs differ "
          f"(0 => MECHANICAL NULL / E36 signature-fidelity trap)")
    # paired progression sign split (robustness, outlier-aware)
    deltas = sorted(t["progression"] - ref["progression"] for _s, ref, t in paired)
    pos = sum(1 for d in deltas if d > 1e-9)
    neg = sum(1 for d in deltas if d < -1e-9)
    print(f"  prog Δ split: {pos} improved / {neg} regressed / "
          f"{len(deltas)-pos-neg} tied; min={deltas[0]:+.4f} max={deltas[-1]:+.4f}")


def main():
    a = sys.argv
    if "--worker" in a:
        i = a.index("--worker")
        worker(int(a[i + 1]), a[i + 2], int(a[i + 3]), a[i + 4])
    elif "--analyze" in a:
        analyze(a[a.index("--analyze") + 1])
    elif "--class" in a:
        role = a[a.index("--class") + 1]
        n = int(a[a.index("--n") + 1]) if "--n" in a else 15
        cap = int(a[a.index("--cap") + 1]) if "--cap" in a else 2000
        out = a[a.index("--out") + 1] if "--out" in a else f"results/e37_{role}.jsonl"
        run_block(role, n, cap, out)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

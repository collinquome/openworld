"""NH-E40 DIVE-RUSH paired block runner (foreground, one-seed-per-process,
resumable). REF = C2.1 standing config; TEST = C2.1 + NH_DIVERUSH.

Runs each (arm, seed) as its OWN subprocess (cross-seed leakage guard, s8
method note) via e35_antifaint_smoke.py, parses the JSONL line, and APPENDS
to results/e40_diverush.jsonl. Idempotent: skips (arm,seed) pairs already in
the file, so a killed/timed-out invocation just resumes. Foreground, blocking,
per-episode timeout — NO nohup/detached blocks (VM hang guard).

Usage: python3 e40_block.py <seed> [<seed> ...]
       (runs REF then TEST for each seed given)
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "e40_diverush.jsonl")
CAP = "2000"
EP_TIMEOUT = 550  # seconds per episode (dive-rush triple-bfs slower on survivors)

REF_ENV = {"NH_FOOD2": "1", "NH_PRAYFIX": "1", "NH_LOS": "1",
           "NH_TOPO": "1", "NH_GUARD": "1"}
TEST_ENV = dict(REF_ENV, NH_DIVERUSH="1")
ARMS = {"REF": REF_ENV, "TEST": TEST_ENV}


def done_pairs():
    seen = set()
    if os.path.exists(OUT):
        for ln in open(OUT):
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
                seen.add((r["arm"], r["seed"]))
            except Exception:
                pass
    return seen


def run_one(arm, seed):
    env = dict(os.environ)
    env["PYTHONPATH"] = "pylib"
    env["NH_STEPCAP"] = CAP
    for k in ("NH_DIVERUSH",):
        env.pop(k, None)
    env.update(ARMS[arm])
    t0 = time.time()
    try:
        p = subprocess.run(
            [sys.executable, "e35_antifaint_smoke.py", arm, str(seed)],
            cwd=HERE, env=env, capture_output=True, text=True,
            timeout=EP_TIMEOUT)
    except subprocess.TimeoutExpired:
        print(f"  !! {arm} seed {seed} TIMEOUT after {EP_TIMEOUT}s", flush=True)
        return None
    wall = time.time() - t0
    rec = None
    for ln in p.stdout.splitlines():
        if ln.startswith("JSONL "):
            rec = json.loads(ln[6:])
    if rec is None:
        print(f"  !! {arm} seed {seed} NO JSONL (stderr tail: "
              f"{p.stderr.strip().splitlines()[-1] if p.stderr.strip() else ''})",
              flush=True)
        return None
    rec["wall_s"] = round(wall, 1)
    with open(OUT, "a") as f:
        f.write(json.dumps(rec) + "\n")
    spl = rec["steps"] / max(rec["depth_max"] or 1, 1)
    print(f"  {arm:4s} seed {seed:4d} depth={rec['depth_max']:2} "
          f"prog={rec['prog']:.4f} steps={rec['steps']:5} "
          f"steps/lvl={spl:5.1f} dr={rec.get('diverush_notes',0):2} "
          f"end={rec['end_reason'][:32]:32s} role={rec['role'][:10]:10s} "
          f"({wall:.0f}s)", flush=True)
    return rec


def main():
    seeds = [int(s) for s in sys.argv[1:]]
    seen = done_pairs()
    for s in seeds:
        for arm in ("REF", "TEST"):
            if (arm, s) in seen:
                print(f"  -- {arm} seed {s} already done, skip", flush=True)
                continue
            run_one(arm, s)


if __name__ == "__main__":
    main()

"""Campaign-2 generic chunk runner.

Usage: python3 run_c2.py <label> <suffix> <seed> [<seed> ...]

Writes results/nethack_results_<label>_<suffix>.json incrementally,
episode index = seed (unique across all Campaign-2 blocks).
"""

import json
import os
import sys
import time

import nh_runner

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
os.makedirs(RESULTS, exist_ok=True)
RUN_LOG = os.path.join(RESULTS, "RUN_LOG.txt")


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(RUN_LOG, "a") as f:
        f.write(line + "\n")


def main():
    label, suffix = sys.argv[1], sys.argv[2]
    seeds = [int(s) for s in sys.argv[3:]]
    out = os.path.join(RESULTS, f"nethack_results_{label}_{suffix}.json")
    doc = {"label": f"{label}_{suffix}", "episodes": []}
    if os.path.exists(out):
        doc = json.load(open(out))
    done = {e["seed"] for e in doc["episodes"]}
    for seed in seeds:
        if seed in done:
            continue
        log(f"=== {label}/{suffix} seed {seed} ===")
        res = nh_runner.run_episode(ep=seed, seed=seed, condition="A",
                                    label=label, memory=None, log=log)
        doc["episodes"].append(res)
        with open(out, "w") as f:
            json.dump(doc, f, indent=1)
        log(f"  [{label}/{suffix}] seed {seed}: prog {res['progression']:.4f} "
            f"depth {res['depth_max']} role {res['role']} "
            f"end {res['end_reason']}")
    log(f"{label} chunk {suffix} complete ({len(doc['episodes'])} eps)")


if __name__ == "__main__":
    main()

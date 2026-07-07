"""Phase L dev-block worker: run seeds under the CURRENT env flag config,
write c2_ab.py-compatible results JSON.

Usage: python3 phasel_block.py <label> <suffix> <seed> [<seed> ...]
Writes results/nethack_results_<label>_<suffix>.json  {"label", "flags", "episodes"}
Resumable (skips seeds already in the output file).
"""

import json
import os
import sys
import time

import nh_runner

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

FLAGS = {k: v for k, v in os.environ.items() if k.startswith("NH_")}


def main():
    label, suffix = sys.argv[1], sys.argv[2]
    seeds = [int(s) for s in sys.argv[3:]]
    out = os.path.join(RESULTS, f"nethack_results_{label}_{suffix}.json")
    doc = {"label": label, "flags": FLAGS, "episodes": []}
    if os.path.exists(out):
        doc = json.load(open(out))
    done = {e["seed"] for e in doc["episodes"]}

    def log(msg):
        print(f"{time.strftime('%H:%M:%S')} {msg}", flush=True)

    for seed in seeds:
        if seed in done:
            continue
        log(f"=== {label}/{suffix} seed {seed} flags={sorted(FLAGS)} ===")
        res = nh_runner.run_episode(ep=seed, seed=seed, condition="dev",
                                    label=label, memory=None, log=log)
        doc["episodes"].append(res)
        with open(out, "w") as f:
            json.dump(doc, f, indent=1)
        log(f"  [{label}/{suffix}] seed {seed}: prog {res['progression']:.4f} "
            f"depth {res['depth_max']} role {res['role']} "
            f"end {res['end_reason'][:80]}")
    log(f"{label} chunk {suffix} complete")


if __name__ == "__main__":
    main()

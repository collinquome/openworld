"""Capped dev-block worker (s6): run seeds under the CURRENT env flag config
at a disclosed step cap (NH_STEPCAP, default 6000), write c2_ab.py /
c2_classes.py-compatible results JSON, and record per-episode crisis-throw
fire count (THROW_DISENGAGE mechanism criterion).

MODEL: claude-opus-4-8[1m] (max thinking), Phase L session 6.

Cap rationale (disclosed, s4 REST-block precedent): the THROW paired block's
proximal KPI is TRASH-death rate, an EARLY-game measure (residual TRASH deaths
fell at steps 573-2757). A cap that covers the trash-death window + immediate
post-escape descent bounds survivor wall-time while leaving the proximal KPI
intact. Cap is IDENTICAL across both arms (ref/test) so the paired delta is
unbiased (both truncated at the same step); the delta is a conservative FLOOR
on any deep-descent benefit that would accrue past the cap.

Usage: python3 capblock.py <label> <suffix> <seed> [<seed> ...]
Writes results/nethack_results_<label>_<suffix>.json. Resumable.
"""
import io
import json
import os
import sys
import time

import nh_runner

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

FLAGS = {k: v for k, v in os.environ.items() if k.startswith("NH_")}
CAP = int(os.environ.get("NH_STEPCAP", "6000"))
nh_runner.MAX_LOOP = CAP


def main():
    label, suffix = sys.argv[1], sys.argv[2]
    seeds = [int(s) for s in sys.argv[3:]]
    out = os.path.join(RESULTS, f"nethack_results_{label}_{suffix}.json")
    doc = {"label": label, "flags": FLAGS, "stepcap": CAP, "episodes": []}
    if os.path.exists(out):
        doc = json.load(open(out))
    done = {e["seed"] for e in doc["episodes"]}

    def stamp(msg):
        print(f"{time.strftime('%H:%M:%S')} {msg}", flush=True)

    for seed in seeds:
        if seed in done:
            continue
        stamp(f"=== {label}/{suffix} seed {seed} cap={CAP} "
              f"flags={sorted(FLAGS)} ===")
        # fire counts come from the result dict (nh_runner reads them off the
        # agent's ev_log/counters; note()/_ev() do NOT print to log).
        res = nh_runner.run_episode(ep=seed, seed=seed, condition="dev",
                                    label=label, memory=None, log=lambda *_: None)
        doc["episodes"].append(res)
        with open(out, "w") as f:
            json.dump(doc, f, indent=1)
        stamp(f"  [{label}/{suffix}] seed {seed}: prog "
              f"{res['progression']:.4f} depth {res['depth_max']} "
              f"role {res['role']} throw_fires {res['throw_fires']} "
              f"end {res['end_reason'][:60]}")
    stamp(f"{label} chunk {suffix} complete")


if __name__ == "__main__":
    main()

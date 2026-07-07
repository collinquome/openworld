"""Run the E21b BLIND-ARM ablation and write results JSON.

Usage: python3 run.py [--seeds 1 2 3] [--trials 3] [--model haiku]
"""
from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from worldgen import registered_set
from harness import run_code_only, run_llm_arm, MODEL

HERE = Path(__file__).resolve().parent
CLASS_NAME = {"A": "intuitive(D1,safe)", "B": "composition(D2,safe)",
              "C": "counterintuitive(D2,damage)", "D": "deep-counter(D3,damage)"}
LLM_ARMS = ["no_memory", "no_override", "full"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()

    worlds = registered_set(args.seeds)
    print(f"worlds={len(worlds)} classes=ABCD seeds={args.seeds} "
          f"trials(llm)={args.trials} model={args.model}")

    episodes = []
    t0 = time.time()
    ckpt = HERE / "results" / "e21b_blind_results.partial.json"

    # solved[arm][class] = [0/1, ...]
    solved = defaultdict(lambda: defaultdict(list))
    identified = defaultdict(lambda: defaultdict(list))   # llm picked opener pre-veto
    vetoed_ct = defaultdict(int)

    def checkpoint():
        ckpt.write_text(json.dumps({
            "status": "partial",
            "episodes_done": len(episodes),
            "solved": {a: {c: solved[a][c] for c in solved[a]} for a in solved},
            "episodes": episodes,
        }, indent=2))

    for w in worlds:
        # Arm 1: CODE-ONLY (deterministic, 1 trial)
        ep = run_code_only(w)
        solved["code_only"][w.world_class].append(int(ep.solved))
        episodes.append({**_ep_row(ep), "trial": 0})
        print(f"  code_only   {w.wid}: solved={ep.solved} chose={ep.chosen}", flush=True)

        # Arms 2-4: LLM in loop
        for arm in LLM_ARMS:
            for tr in range(args.trials):
                ep = run_llm_arm(w, arm, model=args.model, trial=tr)
                solved[arm][w.world_class].append(int(ep.solved))
                identified[arm][w.world_class].append(int(ep.identified_correct))
                if ep.vetoed:
                    vetoed_ct[arm] += 1
                episodes.append({**_ep_row(ep), "trial": tr})
                flag = " VETOED" if ep.vetoed else ""
                print(f"  {arm:11s} {w.wid} t{tr}: solved={ep.solved} "
                      f"chose={ep.chosen} id={ep.identified_correct}{flag}  "
                      f"| {ep.reason[:60]}", flush=True)
        checkpoint()

    dt = time.time() - t0

    # aggregate solve-rate table: arm x class
    arms = ["code_only"] + LLM_ARMS
    table = {}
    for arm in arms:
        table[arm] = {}
        for cls in "ABCD":
            vals = solved[arm][cls]
            table[arm][cls] = {
                "solve_rate": round(sum(vals) / len(vals), 3) if vals else None,
                "n": len(vals),
                "solved": sum(vals),
            }

    result = {
        "experiment": "NH-E21b composition-worlds ablation (BLIND ARM)",
        "arm_of_this_run": "blind (fresh grammar-generated worlds, matched depth)",
        "model_in_loop": args.model,
        "seeds": args.seeds,
        "trials_per_llm_arm": args.trials,
        "world_classes": CLASS_NAME,
        "runtime_sec": round(dt, 1),
        "solve_rate_table": table,
        "llm_identified_opener_rate": {
            arm: {cls: (round(sum(identified[arm][cls]) / len(identified[arm][cls]), 3)
                        if identified[arm][cls] else None) for cls in "ABCD"}
            for arm in LLM_ARMS
        },
        "no_override_vetoes": dict(vetoed_ct),
        "episodes": episodes,
    }
    out = HERE / "results" / "e21b_blind_results.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\nwrote {out}  ({dt:.1f}s)")
    _print_table(table, arms)
    return result


def _ep_row(ep):
    return {
        "arm": ep.arm, "world": ep.world.wid, "class": ep.world.world_class,
        "depth": ep.world.depth, "solved": ep.solved, "chosen": ep.chosen,
        "solution": ep.world.solution_token, "identified_correct": ep.identified_correct,
        "vetoed": ep.vetoed, "reason": ep.reason,
    }


def _print_table(table, arms):
    print("\nSOLVE-RATE  (rows=arm, cols=world-class)")
    print(f"{'arm':13s} {'A':>10s} {'B':>10s} {'C':>10s} {'D':>10s}")
    for arm in arms:
        row = " ".join(f"{table[arm][c]['solve_rate']!s:>10s}" for c in "ABCD")
        print(f"{arm:13s} {row}")


if __name__ == "__main__":
    main()

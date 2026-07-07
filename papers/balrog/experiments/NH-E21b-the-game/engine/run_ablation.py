"""
NH-E21b engine — MODEL: Sonnet subagent, spec by Fable 5 (max), Phase L session 1.

run_ablation.py — ablation harness runner.

Runs the no-intuition scripted baseline (ablation arm b/d) over all six
templates x seeds 0-9, and writes a results JSON with solve rate,
mechanics-discovered fraction, and step counts per template.

LLM arms (a)/(c) plug in via `LLMPolicy` below: TODO wire an actual model
call where marked. The interface is intentionally the same shape as
BaselineAgent.act(obs, knowledge_log) -> action string, so swapping the
policy object is a one-line change in run_episode().
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from typing import Callable, List, Optional

import game as game_mod
import templates
from baseline_agent import BaselineAgent
from knowledge import KnowledgeLog


class LLMPolicy:
    """Stub interface for ablation arms (a)/(c) — full stack / no-memory.
    A real implementation receives the current obs AND the accumulated
    knowledge log (arm (a)) or obs only (arm (c), no-memory ablation) and
    returns one action string. Wire the actual model call where marked."""

    def __init__(self, use_knowledge_log: bool = True):
        self.use_knowledge_log = use_knowledge_log

    def reset(self) -> None:
        pass

    def act(self, obs: dict, knowledge_log: Optional[KnowledgeLog] = None) -> str:
        # TODO(NH-E21b Phase L+1): plug in the LLM call here.
        #   prompt = render_prompt(obs, knowledge_log if self.use_knowledge_log else None)
        #   return model.complete(prompt) -> parse into one of the legal actions
        raise NotImplementedError("LLMPolicy.act is a stub — wire the model call here.")


def run_episode(template_id: str, seed: int, policy_factory: Callable[[], object],
                 max_steps: int = 200, keep_transcript: bool = False) -> dict:
    env = game_mod.Game(max_steps=max_steps)
    obs = env.reset(template_id, seed)
    policy = policy_factory()
    if hasattr(policy, "reset"):
        policy.reset()
    klog = KnowledgeLog()
    klog.ingest(0, obs["messages"], obs["state"])

    transcript: List[dict] = []
    if keep_transcript:
        transcript.append({"step": 0, "action": None, "messages": list(obs["messages"])})

    done = False
    info = {}
    steps_taken = 0
    while not done:
        action = policy.act(obs, klog)
        obs, done, info = env.step(action)
        steps_taken += 1
        klog.ingest(steps_taken, obs["messages"], obs["state"])
        if keep_transcript:
            transcript.append({"step": steps_taken, "action": action, "messages": list(obs["messages"])})

    result = {
        "template_id": template_id,
        "seed": seed,
        "win": bool(info.get("win")),
        "loss": bool(info.get("loss")),
        "steps": info.get("steps"),
        "mechanics_discovered": info.get("mechanics_discovered"),
        "mechanics_total": info.get("mechanics_total"),
    }
    if keep_transcript:
        result["transcript"] = transcript
    return result


def run_ablation(seeds=range(10), max_steps: int = 200) -> dict:
    per_template = {}
    all_results = []
    for tid in templates.ALL_TEMPLATE_IDS:
        results = []
        for seed in seeds:
            r = run_episode(tid, seed, lambda: BaselineAgent(seed=seed), max_steps=max_steps)
            results.append(r)
            all_results.append(r)
        wins = sum(1 for r in results if r["win"])
        solve_rate = wins / len(results)
        discovered_fracs = [
            (r["mechanics_discovered"] / r["mechanics_total"]) if r["mechanics_total"] else 0.0
            for r in results
        ]
        steps = [r["steps"] for r in results]
        per_template[tid] = {
            "n_episodes": len(results),
            "solve_rate": solve_rate,
            "wins": wins,
            "mean_mechanics_discovered_frac": statistics.mean(discovered_fracs),
            "mean_steps": statistics.mean(steps),
            "median_steps": statistics.median(steps),
        }
    return {"per_template": per_template, "episodes": all_results}


def main():
    ap = argparse.ArgumentParser(description="NH-E21b ablation harness runner (baseline arm)")
    ap.add_argument("--seeds", type=int, default=10, help="number of seeds, 0..N-1")
    ap.add_argument("--max-steps", type=int, default=200)
    ap.add_argument("--out", type=str, default="ablation_results.json")
    args = ap.parse_args()

    results = run_ablation(seeds=range(args.seeds), max_steps=args.max_steps)

    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)

    print(f"NH-E21b ablation baseline — {args.seeds} seeds x {len(templates.ALL_TEMPLATE_IDS)} templates")
    print(f"{'template':10s} {'solve_rate':>10s} {'discovered%':>12s} {'mean_steps':>10s}")
    for tid, stats in results["per_template"].items():
        print(f"{tid:10s} {stats['solve_rate']*100:9.1f}% "
              f"{stats['mean_mechanics_discovered_frac']*100:11.1f}% "
              f"{stats['mean_steps']:10.1f}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()

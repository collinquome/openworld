"""Resumable FOREGROUND runner: checkpoints after EVERY episode, skips done ones.

Call repeatedly; each invocation resumes from the checkpoint and makes forward
progress. Robust to being killed mid-run (at most one episode is lost).

Usage: python3 run_fg.py [--seeds 1 2 3] [--trials 1] [--model haiku] [--max N]
       --max limits episodes THIS invocation (to stay under a shell timeout).
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path

from worldgen import registered_set
from harness import run_code_only, run_llm_arm

HERE = Path(__file__).resolve().parent
CKPT = HERE / "results" / "e21b_blind_results.partial.json"
LLM_ARMS = ["no_memory", "no_override", "full"]


def load_done():
    if not CKPT.exists():
        return []
    return json.loads(CKPT.read_text()).get("episodes", [])


def ep_row(ep, trial):
    return {"arm": ep.arm, "world": ep.world.wid, "class": ep.world.world_class,
            "depth": ep.world.depth, "solved": ep.solved, "chosen": ep.chosen,
            "solution": ep.world.solution_token, "identified_correct": ep.identified_correct,
            "vetoed": ep.vetoed, "reason": ep.reason, "trial": trial}


def save(episodes):
    CKPT.write_text(json.dumps({"status": "partial", "episodes_done": len(episodes),
                                "episodes": episodes}, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--max", type=int, default=999)
    args = ap.parse_args()

    worlds = registered_set(args.seeds)
    episodes = load_done()
    done = {(e["arm"], e["world"], e["trial"]) for e in episodes}

    # build full work list (ordered A,B,C,D; arms code,no_mem,no_over,full)
    work = []
    for w in worlds:
        if ("code_only", w.wid, 0) not in done:
            work.append(("code_only", w, 0))
        for arm in LLM_ARMS:
            for tr in range(args.trials):
                if (arm, w.wid, tr) not in done:
                    work.append((arm, w, tr))

    print(f"already done: {len(episodes)}  remaining: {len(work)}  this-batch-cap: {args.max}",
          flush=True)
    n = 0
    for arm, w, tr in work:
        if n >= args.max:
            print(f"batch cap reached ({args.max}); resume by re-running.", flush=True)
            break
        t0 = time.time()
        if arm == "code_only":
            ep = run_code_only(w)
        else:
            ep = run_llm_arm(w, arm, model=args.model, trial=tr)
        episodes.append(ep_row(ep, tr))
        save(episodes)  # checkpoint after EVERY episode
        n += 1
        flag = " VETOED" if ep.vetoed else ""
        print(f"  [{len(episodes)}] {arm:11s} {w.wid} t{tr}: solved={ep.solved} "
              f"chose={ep.chosen} id={ep.identified_correct}{flag} ({time.time()-t0:.0f}s)"
              f" | {ep.reason[:50]}", flush=True)
    print(f"batch complete: +{n} episodes, total {len(episodes)}", flush=True)


if __name__ == "__main__":
    main()

"""NH-E21b LIVE INTUITION ARM (arm (a): full stack, live LLM).

MODEL: Fable 5 (max reasoning) — harness + the live intuition layer itself
(the LLM in the loop for these runs IS Fable 5 max, consulted between
invocations; every consultation is logged verbatim in the state file).

Replay-based interactive protocol (nh_branch pattern — the engine is
deterministic, so an action-prefix IS a state snapshot; no daemons):

  python3 live_arm.py <template> <seed> --state <state.json> \
      [--macro "goto X Y" | --macro "eat a" | --macro "interact" ...] \
      [--consult "verbatim consultation response text"]

Each invocation replays the recorded prefix, optionally appends the given
macros (expanded to primitive actions by the PROCEDURE layer: BFS goto),
saves the state, and prints the current consultation package (grid,
state, knowledge-log summary, message history tail). The INTUITION layer
(the live LLM) reads the package and decides the next macros; its verbatim
reasoning is recorded via --consult before its chosen macros.

Layer split (four-layer architecture): goto pathing/step execution =
PROCEDURE; knowledge log = MEMORY; the between-invocation LLM = INTUITION;
grid/messages = PERCEPTION. The ablation contrast arms (b) baseline and
(c)/(d) run via run_ablation.py.
"""

import argparse
import json
import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import game as game_mod
from knowledge import KnowledgeLog

PRIMITIVE = {"up", "down", "left", "right", "interact", "pickup", "wait"}


def bfs(grid, start, goal):
    """PROCEDURE layer: shortest path over currently-visible passable
    cells ('#' wall, ' ' fog are impassable). Returns action list."""
    h, w = len(grid), max(len(r) for r in grid)

    def cell(x, y):
        if 0 <= y < h and 0 <= x < len(grid[y]):
            return grid[y][x]
        return " "

    def passable(x, y):
        return cell(x, y) not in ("#", " ")

    q = deque([(start, [])])
    seen = {start}
    moves = [("up", 0, -1), ("down", 0, 1), ("left", -1, 0), ("right", 1, 0)]
    while q:
        (x, y), path = q.popleft()
        if (x, y) == goal:
            return path
        for name, dx, dy in moves:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in seen and passable(nx, ny):
                seen.add((nx, ny))
                q.append(((nx, ny), path + [name]))
    return None


def expand(macro, obs):
    """Expand one macro into primitive actions given the current obs."""
    parts = macro.split()
    if parts[0] == "goto":
        x, y = int(parts[1]), int(parts[2])
        path = bfs(obs["grid"], tuple(obs["state"]["pos"]), (x, y))
        if path is None:
            return None, f"goto {x},{y}: NO PATH on visible grid"
        return path, None
    if parts[0] in ("eat", "drop") and len(parts) == 2:
        return [macro], None
    if macro in PRIMITIVE:
        return [macro], None
    return None, f"unknown macro: {macro}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("template")
    ap.add_argument("seed", type=int)
    ap.add_argument("--state", required=True)
    ap.add_argument("--macro", action="append", default=[])
    ap.add_argument("--consult", default=None,
                    help="verbatim intuition-layer text to log BEFORE "
                         "executing this invocation's macros")
    ap.add_argument("--max-steps", type=int, default=200)
    args = ap.parse_args()

    st = {"template": args.template, "seed": args.seed, "actions": [],
          "consultations": [], "macro_log": []}
    if os.path.exists(args.state):
        st = json.load(open(args.state))
        assert st["template"] == args.template and st["seed"] == args.seed

    env = game_mod.Game()
    obs = env.reset(args.template, args.seed)
    klog = KnowledgeLog()
    klog.ingest(0, obs["messages"], obs["state"])
    all_msgs = [(0, m) for m in obs["messages"]]
    info = {"win": False, "loss": False, "done": False, "steps": 0,
            "mechanics_discovered": 0, "mechanics_total": None}

    def do(action):
        nonlocal obs, info
        obs, done, info = env.step(action)
        klog.ingest(info["steps"], obs["messages"], obs["state"])
        for m in obs["messages"]:
            all_msgs.append((info["steps"], m))
        return done

    # replay prefix
    done = False
    for a in st["actions"]:
        done = do(a)
        if done:
            break

    if args.consult:
        st["consultations"].append({"at_step": info["steps"],
                                    "model": "claude-fable-5 (max)",
                                    "text": args.consult})

    # execute new macros
    for macro in args.macro:
        if done:
            break
        acts, err = expand(macro, obs)
        st["macro_log"].append({"at_step": info["steps"], "macro": macro,
                                "error": err})
        if err:
            print(f"[MACRO ERROR] {err}")
            continue
        for a in acts:
            if done or info["steps"] >= args.max_steps:
                break
            st["actions"].append(a)
            done = do(a)

    os.makedirs(os.path.dirname(args.state) or ".", exist_ok=True)
    with open(args.state, "w") as f:
        json.dump(st, f, indent=1)

    # ---- consultation package (CONTEXT_SPEC spirit: full picture) ----
    print(f"=== {args.template} seed {args.seed} | step {info['steps']} "
          f"| win={info['win']} loss={info['loss']} done={info['done']} "
          f"| mechanics {info['mechanics_discovered']}/"
          f"{info['mechanics_total']} ===")
    print("\n".join(obs["grid"]))
    print("STATE:", json.dumps(obs["state"]))
    print("KNOWLEDGE LOG:")
    for line in klog.summary_lines():
        print("  " + line)
    print("RECENT MESSAGES:")
    for s, m in all_msgs[-15:]:
        print(f"  [{s}] {m}")


if __name__ == "__main__":
    main()

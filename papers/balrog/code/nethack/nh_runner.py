"""Shared episode runner: BALROG-identical env stack + DiveAgent + logging.

Every env touchpoint (source-leak audit surface):
  env = nh_harness.make_env()          # vendored balrog.environments.make_env
  env.reset(seed=seed)                 # protocol reset
  env.step(action_string)              # protocol step
  env.env.language_action_space        # the wrapper's own action list
  env.get_stats()                      # scoring (same method BALROG's
                                       #  evaluator calls); runner-side only
  env.close()
Nothing else. The agent consumes only the served obs dict.
"""

import json
import os
import random
import time

import numpy as np

import nh_harness as H
import nh_common as C
from nh_agent import DiveAgent
from nh_transitions import TransitionLogger

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
TRAJ = os.path.join(RESULTS, "trajectories")
os.makedirs(TRAJ, exist_ok=True)

MAX_LOOP = 110_000     # safety bound above the env's own 100k cap


def _subgoal_summary(agent, steps):
    """Time share per subgoal label + the subgoal active at episode end
    (E-NH1 attribution: which subgoal precedes deaths)."""
    log = agent.subgoal_log
    if not log:
        return {}
    share = {}
    for i, (s, label, _r) in enumerate(log):
        nxt = log[i + 1][0] if i + 1 < len(log) else steps
        share[label] = share.get(label, 0) + max(0, nxt - s)
    tot = max(1, sum(share.values()))
    out = {k: round(v / tot, 4) for k, v in
           sorted(share.items(), key=lambda kv: -kv[1])}
    out["_final"] = log[-1][1]
    out["_final_reason"] = log[-1][2]
    return out


def run_episode(ep, seed, condition="A", label="clean_A", memory=None,
                log=print, frame_cap=5000):
    env = H.make_env()
    random.seed(seed)
    np.random.seed(seed)
    obs, info = env.reset(seed=seed)
    space = list(env.env.language_action_space)
    agent = DiveAgent(log=log, memory=memory)
    agent.set_actions(space)

    tag = "NetHackChallenge-v0"
    tlog = TransitionLogger(tag, ep, seed, condition, "DiveAgent", space,
                            label)
    if memory is not None:
        memory.begin_episode(os.path.relpath(tlog.fn, RESULTS))
    tlog.log_reset(obs)

    traj = {"task": tag, "episode": ep, "seed": seed, "condition": condition,
            "actions": [], "frames": [], "frame_steps": [], "positions": [],
            "hp": [], "depth": [], "hunger": [], "messages": [], "notes": [],
            "mem_fired": [], "subgoals": [], "plans": [], "evs": [],
            "beliefs": [], "monsters": []}

    def snap(o, step):
        tty = o["obs"]["tty_chars"]
        traj["frames"].append(["".join(chr(c) for c in row).rstrip()
                               for row in tty])
        traj["frame_steps"].append(step)
        # belief snapshot (Campaign 2 renderer): terrain+explored grid,
        # visible monsters — straight from the agent's own belief state
        try:
            A = agent.atlas
            L = A.level
            rows = []
            for y in range(21):
                chars = []
                for x in range(79):
                    if not L.explored[y][x]:
                        chars.append(".")
                    else:
                        chars.append(chr(65 + int(L.terrain[y][x])))
                rows.append("".join(chars))
            sus = sorted(agent.suspect_walls.get(A.key, set()))
            traj["beliefs"].append([step, rows, sus])
            traj["monsters"].append(
                [step, [[m.x, m.y, m.name, int(m.pet)] for m in L.monsters]])
        except Exception as e:
            # harness-audit item 1: never swallow silently — count + note
            # (first occurrence carries the exception text for triage).
            # step 0 is excluded by design: Atlas has no belief before the
            # agent's first act(), so the reset-frame snapshot is expected
            # to have no belief layer (verified: the only step-0 error is
            # KeyError None on the empty atlas).
            if step > 0:
                snap_errors[0] += 1
                if snap_errors[0] == 1:
                    traj["notes"].append(
                        f"step {step}: belief-snapshot error: "
                        f"{type(e).__name__}: {e}")

    def want_frame(step, agent, depth_changed, hp_frac):
        if len(traj["frames"]) >= frame_cap:
            return False
        if depth_changed or step < 400:
            return True
        if hp_frac < 0.3:
            return step % 3 == 0
        return step % max(3, (step // 2000) + 3) == 0

    snap_errors = [0]                 # harness-audit item 1 (list: closure)
    snap(obs, 0)
    steps = 0
    done = False
    illegal = 0
    depth_max, xp_max = 1, 1
    bl_depth_max = 1                  # harness-audit item 6: ground truth,
    belief_depth_mismatch = 0         # read straight off served blstats
    last_depth = 1
    t0 = time.time()
    while not done and steps < MAX_LOOP:
        a = agent.act(obs)
        # harness-audit item 6 (assert half): belief depth must equal the
        # blstats depth of the SAME obs the agent just consumed — compared
        # post-act so Atlas has processed exactly this observation.
        if agent.atlas.depth != int(obs["obs"]["blstats"][C.nh.NLE_BL_DEPTH]):
            belief_depth_mismatch += 1
        if a not in space:
            illegal += 1
            traj["notes"].append(f"step {steps}: illegal '{a}' -> search")
            a = "search"
        obs, r, term, trunc, info = env.step(a)
        steps += 1
        done = term or trunc
        tlog.log_step(a, obs, r, done, info)
        A = agent.atlas
        # harness-audit item 6 (ground-truth half): depth_max straight from
        # served blstats, independent of the belief layer.
        bl_depth_max = max(bl_depth_max,
                           int(obs["obs"]["blstats"][C.nh.NLE_BL_DEPTH]))
        depth_max = max(depth_max, A.depth)
        xp_max = max(xp_max, A.xplvl)
        dchg = A.depth != last_depth
        last_depth = A.depth
        traj["actions"].append(a)
        traj["positions"].append(list(A.agent))
        traj["hp"].append([A.hp, A.hpmax])
        traj["depth"].append(A.depth)
        traj["hunger"].append(A.hunger)
        traj["messages"].append(A.message[:150])
        if want_frame(steps, agent, dchg, A.hp / max(1, A.hpmax)):
            snap(obs, steps)
        if steps % 2000 == 0:
            log(f"    step {steps} depth {A.depth} (max {depth_max}) "
                f"hp {A.hp}/{A.hpmax} xp {A.xplvl} t={A.time} "
                f"wall={time.time()-t0:.0f}s")
    snap(obs, steps)

    stats = env.get_stats()
    env.close()
    tfile = tlog.close()
    # harness-audit item 3: a loop exit without env termination is OUR
    # truncation, not the env's — say so explicitly in the end reason.
    end_reason = str(stats.get("end_reason"))
    if not done:
        end_reason = f"RUNNER_TRUNCATED@{steps} ({end_reason})"
    traj["notes"].extend([f"step {s}: {n}" for (s, n) in agent.notes])
    traj["mem_fired"] = [f"step {s}: {n}" for (s, n) in agent.mem_fired]
    traj["subgoals"] = [list(x) for x in agent.subgoal_log]
    traj["plans"] = [[s, cells] for (s, cells) in agent.plan_log]
    traj["evs"] = [list(x) for x in agent.ev_log]
    traj["pred_dmg"] = [list(x) for x in getattr(agent, "pred_log", [])]

    result = {
        "task": tag,
        "episode": ep,
        "seed": seed,
        "condition": condition,
        "steps": steps,
        "illegal": illegal,
        "progression": float(stats["progression"]),
        "highest_achievement": stats.get("highest_achievement"),
        "depth_max": depth_max,
        "xplvl_max": xp_max,
        "dlvl_list": stats.get("dlvl_list"),
        "xplvl_list": stats.get("xplvl_list"),
        "end_reason": end_reason,
        "depth_max_blstats": bl_depth_max,          # item 6 ground truth
        "belief_depth_mismatch": belief_depth_mismatch,
        "belief_snap_errors": snap_errors[0],       # item 1
        "role": agent.role,
        "race": agent.race,
        "role_source": getattr(agent, "role_source", None),  # item 4
        "wallclock_s": round(time.time() - t0, 1),
        "transitions_file": os.path.relpath(tfile, RESULTS),
        "mem_fired": traj["mem_fired"],
        "subgoal_summary": _subgoal_summary(agent, steps),
        "ev_fired": len(agent.ev_log),
        "emergency_fired": agent.emergency_fired,
    }
    if memory is not None:
        memory.end_episode(result, steps)

    tj = os.path.join(TRAJ, f"{label}__ep{ep}.json")
    with open(tj, "w") as f:
        json.dump(traj, f)
    return result

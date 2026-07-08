"""NH-E35/Tier-1 — anti-faint guard mechanism + paired smoke.

Runs one arm (REF or TEST) per PROCESS to avoid cross-seed leakage (s8 method
note). Flags come from the environment (set the C2.1 reference + optionally
NH_ANTIFAINT). Prints per-episode: end_reason, max hunger tier reached (0=Sat..
4=Fainting/5=Fainted), antifaint fire count, depth/progression. Foreground.

Usage: NH_FOOD2=1 ... [NH_ANTIFAINT=1] python3 e35_antifaint_smoke.py <arm> <seed>...
"""
import json
import os
import sys

import nh_runner

CAP = int(os.environ.get("NH_STEPCAP", "6000"))
nh_runner.MAX_LOOP = CAP
TRAJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results",
                    "trajectories")
HUNGER_NAME = {0: "Satiated", 1: "Normal", 2: "Hungry", 3: "Weak",
               4: "Fainting", 5: "Fainted", 6: "Starved"}


def run(arm, seed):
    res = nh_runner.run_episode(ep=seed, seed=seed, condition=arm, label=arm,
                                log=lambda *a, **k: None)
    tj = os.path.join(TRAJ, f"{arm}__ep{seed}.json")
    traj = json.load(open(tj)) if os.path.exists(tj) else {}
    hung = traj.get("hunger", []) or [0]
    notes = traj.get("notes", []) or []
    maxh = max(hung)
    fires = sum(1 for n in notes if "ANTIFAINT" in str(n))
    facq = sum(1 for n in notes if "FOODACQ" in str(n))
    petw = sum(1 for n in notes if "PET wait" in str(n))
    # pet survival: monsters snapshots = [[step, [[x,y,name,pet],...]], ...].
    # pet_start = a pet present in an early (<=step 50) snapshot; pet_end = a pet
    # present in the LAST snapshot (still with the agent at episode end/death).
    mon = traj.get("monsters", []) or []
    def _has_pet(frame):
        return any(len(m) > 3 and m[3] for m in frame[1])
    pet_start = any(_has_pet(f) for f in mon if f[0] <= 50)
    pet_end = _has_pet(mon[-1]) if mon else False
    # deepest snapshot that still shows a live pet (did it descend with us?)
    pet_maxdepth_present = 0
    depths = traj.get("depth", []) or []
    for f in mon:
        if _has_pet(f) and f[0] > 0 and f[0] <= len(depths):
            pet_maxdepth_present = max(pet_maxdepth_present, depths[f[0] - 1])
    # nutrition-secured proxy: did the agent ever reach Hungry (tier 2) while
    # having banked food (>=1 FOODACQ eat) BEFORE it? Cheap proxy = any FOODACQ
    # fire at all (the s10 gap was arriving at Hungry with an EMPTY larder).
    er = res.get("end_reason", "?")
    return {"seed": seed, "arm": arm, "end_reason": er, "maxhunger": maxh,
            "maxhunger_name": HUNGER_NAME.get(maxh, maxh),
            "antifaint_fires": fires, "foodacq_fires": facq,
            "pet_waits": petw, "pet_start": pet_start, "pet_end": pet_end,
            "pet_maxdepth_present": pet_maxdepth_present,
            "steps": res.get("steps"),
            "depth_max": res.get("depth_max"), "prog": res.get("progression"),
            "role": res.get("role"), "race": res.get("race")}


def main():
    arm = sys.argv[1]
    seeds = [int(s) for s in sys.argv[2:]]
    print(f"ARM={arm} CAP={CAP} flags={{k:v for NH_}}="
          + ",".join(f"{k}={v}" for k, v in sorted(os.environ.items())
                     if k.startswith("NH_")))
    for s in seeds:
        r = run(arm, s)
        print(f"  seed {r['seed']:4d} end={r['end_reason'][:34]:34s} "
              f"maxHunger={r['maxhunger_name']:8s} facq={r['foodacq_fires']:3d} "
              f"petw={r['pet_waits']:3d} pet_end={int(r['pet_end'])} "
              f"pet_dmax={r['pet_maxdepth_present']} "
              f"steps={r['steps']} depth={r['depth_max']} prog={r['prog']}")
        print("JSONL " + json.dumps(r))


if __name__ == "__main__":
    main()

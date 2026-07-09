"""NH-E35/Tier-1 — anti-faint guard mechanism + paired smoke.

Runs one arm (REF or TEST) per PROCESS to avoid cross-seed leakage (s8 method
note). Flags come from the environment (set the C2.1 reference + optionally
NH_ANTIFAINT). Prints per-episode: end_reason, max hunger tier reached (0=Sat..
4=Fainting/5=Fainted), antifaint fire count, depth/progression. Foreground.

Usage: NH_FOOD2=1 ... [NH_ANTIFAINT=1] python3 e35_antifaint_smoke.py <arm> <seed>...
"""
import json
import os
import re
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
    # NH-E40 DIVE-RUSH: one note per dungeon level where dive-rush drove
    # behavior (descend/route/seek) => distinct-level fired count.
    diverush = sum(1 for n in notes if "DIVERUSH" in str(n))
    wield = sum(1 for n in notes if "WIELD upgrade" in str(n))
    wacq = sum(1 for n in notes if "WIELDACQ pickup" in str(n))
    wacq_walk = sum(1 for n in notes if "WIELDACQ walk" in str(n))
    # NH_LOOT (s15) efficient-loot mechanism: pickups (weapon underfoot / armor)
    # + walk-steps toward a valued item. "LOOT pickup" (efficient_loot + msg
    # weapon), "picking up armor" (msg-channel armor under LOOT), "LOOT walk".
    loot_pick = sum(1 for n in notes if "LOOT pickup" in str(n)) + \
        sum(1 for n in notes if "picking up armor" in str(n))
    loot_walk = sum(1 for n in notes if "LOOT walk" in str(n))
    # NH_WIELD_DIAG extraction (acquisition-bound test): best floor-weapon dpt
    # seen, its name, and how many steps a floor weapon beat the current wield.
    floor_dpt, floor_name, floor_upg = 0.0, None, 0
    for n in notes:
        s = str(n)
        m = re.search(r"FLOORWPN see (.+?) dpt ([\d.]+) \(cur wield ([\d.]+)", s)
        if m and float(m.group(2)) > floor_dpt:
            floor_dpt, floor_name = float(m.group(2)), m.group(1)
        m2 = re.search(r"FLOORWPN UPGRADE .+ n=(\d+)", s)
        if m2:
            floor_upg = max(floor_upg, int(m2.group(1)))
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
    # NH_SAFELEVEL (s16) mechanism: fire count (levels where safe-leveling fired),
    # arrival-xp at D5 (xplvl the first step depth>=5 is reached), xp_max.
    sl_fires = sum(1 for n in notes if "SAFELEVEL engage" in str(n))
    depths_t = traj.get("depth", []) or []
    xps_t = traj.get("xplvl", []) or []
    arrival_xp_d5 = None
    for d, xp in zip(depths_t, xps_t):
        if d >= 5:
            arrival_xp_d5 = xp
            break
    xp_max = max(xps_t) if xps_t else None
    # NH-E38 LEVELING-WALL instrumentation: state at death/truncation (last
    # logged frame) + depth-conditioned XP (first xp seen on arrival at each
    # new max depth) -> proves/quantifies "under-leveled at death".
    hp_series = traj.get("hp", []) or []
    ac_series = traj.get("ac", []) or []
    str_series = traj.get("str", []) or []
    hp_end = hp_series[-1][0] if hp_series else None
    hpmax_end = hp_series[-1][1] if hp_series else None
    xp_at_death = xps_t[-1] if xps_t else None
    ac_end = ac_series[-1] if ac_series else None
    str_end = str_series[-1] if str_series else None
    xp_by_depth = {}
    seen_d = 0
    for d, xp in zip(depths_t, xps_t):
        if d > seen_d:
            xp_by_depth[int(d)] = int(xp)
            seen_d = d
    # NH-E38 CONSUMABLE-ECONOMY mechanism counters (note()-tagged in nh_agent).
    zap_off = sum(1 for n in notes if "CONSUME zap-offensive" in str(n))
    quaff_heal = sum(1 for n in notes if "CONSUME quaff-heal" in str(n))
    gainlevel = sum(1 for n in notes if "CONSUME gainlevel" in str(n))
    enchant = sum(1 for n in notes if "CONSUME enchant" in str(n))
    read_id = sum(1 for n in notes if "CONSUME read-identify" in str(n))
    engrave_id = sum(1 for n in notes if "ENGRAVE-ID test" in str(n))
    engrave_solved = sum(1 for n in notes if "ENGRAVE-ID solved" in str(n))
    consume_kills = sum(1 for n in notes if "CONSUME kill" in str(n))
    consume_pickups = sum(1 for n in notes if "CONSUME pickup" in str(n))
    consume_walks = sum(1 for n in notes if "CONSUME walk" in str(n))
    # acquisitions land via autopickup too ("<letter> - a <appearance> potion")
    _msgs = traj.get("messages", []) or []
    consume_acq = sum(1 for m in _msgs if re.match(
        r"^[a-z] - .*(potion|wand|scroll|ring)", str(m)))
    er = res.get("end_reason", "?")
    return {"seed": seed, "arm": arm, "end_reason": er, "maxhunger": maxh,
            "safelevel_fires": sl_fires, "arrival_xp_d5": arrival_xp_d5,
            "xp_max": xp_max,
            "maxhunger_name": HUNGER_NAME.get(maxh, maxh),
            "antifaint_fires": fires, "foodacq_fires": facq,
            "wield_fires": wield, "wieldacq_fires": wacq,
            "wieldacq_walk": wacq_walk,
            "loot_fires": loot_pick, "loot_walks": loot_walk,
            "floor_wpn_dpt": floor_dpt,
            "floor_wpn_name": floor_name, "floor_upgrade_steps": floor_upg,
            "diverush_notes": diverush,
            "pet_waits": petw, "pet_start": pet_start, "pet_end": pet_end,
            "pet_maxdepth_present": pet_maxdepth_present,
            "steps": res.get("steps"),
            "depth_max": res.get("depth_max"), "prog": res.get("progression"),
            "role": res.get("role"), "race": res.get("race"),
            # NH-E38 leveling-wall state at death/truncation
            "hp_end": hp_end, "hpmax_end": hpmax_end, "xp_at_death": xp_at_death,
            "ac_end": ac_end, "str_end": str_end, "xp_by_depth": xp_by_depth,
            # NH-E38 consumable-economy mechanism
            "zap_off_fires": zap_off, "quaff_heal_fires": quaff_heal,
            "gainlevel_fires": gainlevel, "enchant_fires": enchant,
            "read_id_fires": read_id, "engrave_id_tests": engrave_id,
            "engrave_id_solved": engrave_solved, "consume_kills": consume_kills,
            "consume_pickups": consume_pickups, "consume_walks": consume_walks,
            "consume_acq": consume_acq}


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
              f"wield={r['wield_fires']:2d} "
              f"petw={r['pet_waits']:3d} pet_end={int(r['pet_end'])} "
              f"pet_dmax={r['pet_maxdepth_present']} "
              f"steps={r['steps']} depth={r['depth_max']} prog={r['prog']}")
        print("JSONL " + json.dumps(r))


if __name__ == "__main__":
    main()

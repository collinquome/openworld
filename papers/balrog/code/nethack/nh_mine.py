"""Campaign-2 E-NH1: one-pass miner over all logged transitions.

Reads every results/transitions/<label>/*.jsonl.gz episode (main arm) and
emits a compact per-episode extract to results/c2_cache/, containing all
the signals forensics + expectimax need:

  meta, depth_arrivals, hp_drops (with adjacent-hostile attribution),
  kills, prayers, eats, hunger/ac trajectories, death frame info.

Pure offline log processing: no env interaction.
"""

import glob
import gzip
import json
import os
import re
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "pylib"))

import nh_common as C          # offline tables only (disclosed provenance)

RESULTS = os.path.join(HERE, "results")
CACHE = os.path.join(RESULTS, "c2_cache")
os.makedirs(CACHE, exist_ok=True)

ROWS, COLS = 21, 79
BL_X, BL_Y, BL_HP, BL_HPMAX, BL_DEPTH, BL_AC = 0, 1, 10, 11, 12, 16
BL_XP, BL_TIME, BL_HUNGER, BL_DNUM, BL_DLEVEL, BL_COND = 18, 20, 21, 23, 24, 25

RE_KILL = re.compile(r"You (?:kill|destroy) the ([a-zA-Z' -]+?)!")


def adj_hostiles(glyphs, x, y):
    """Names of hostile monsters in the 8 cells around (x,y)."""
    out = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if not (0 <= nx < COLS and 0 <= ny < ROWS):
                continue
            g = glyphs[ny * COLS + nx]
            info = C.mon_info(g)
            if info and not info[5]:
                out.append(info[0])
    return out


def mine_file(args):
    fn, label = args
    out_fn = os.path.join(CACHE, f"{label}__{os.path.basename(fn)}"
                          .replace(".jsonl.gz", ".json.gz"))
    if os.path.exists(out_fn):
        return out_fn
    prev_g = None
    glyphs = None
    prev = None            # previous step's parsed row
    prev_adj = []
    combat = []            # per-step rows while any hostile adjacent
    depth_arrivals = []    # (depth, time, step)
    seen_depths = set()
    hp_drops = []          # dicts
    kills = []
    prayers = []
    eats = []
    hunger_traj = []
    ac_traj = []
    last_msgs = []
    step = 0
    hdr = {}
    max_depth = 0
    final = None
    try:
        with gzip.open(fn, "rt") as f:
            for line in f:
                rec = json.loads(line)
                if "task" in rec and "obs" not in rec:
                    hdr = {k: rec.get(k) for k in
                           ("task", "episode", "seed", "condition", "policy")}
                    continue
                o = rec["obs"]
                if "glyphs" in o:
                    glyphs = o["glyphs"]
                else:
                    glyphs = list(prev_g)
                    for i, v in o["glyphs_delta"]:
                        glyphs[i] = v
                prev_g = glyphs
                bl = o["blstats"]
                msg = o.get("message", "")
                row = dict(
                    step=step, t=bl[BL_TIME], depth=bl[BL_DEPTH],
                    dnum=bl[BL_DNUM], hp=bl[BL_HP], hpmax=bl[BL_HPMAX],
                    xp=bl[BL_XP], hunger=bl[BL_HUNGER], ac=bl[BL_AC],
                    x=bl[BL_X], y=bl[BL_Y], cond=bl[BL_COND],
                    action=rec.get("action"), done=rec.get("done", False))
                if msg:
                    last_msgs.append((step, msg[:200]))
                    last_msgs = last_msgs[-6:]
                    for sp in RE_KILL.findall(msg):
                        kills.append((step, row["t"], row["depth"],
                                      sp.strip(), row["xp"]))
                d = row["depth"]
                if d > 0 and d not in seen_depths:
                    seen_depths.add(d)
                    depth_arrivals.append((d, row["t"], step))
                    max_depth = max(max_depth, d)
                # combat log: any step whose PRE-state had adjacent hostiles
                adj_now = adj_hostiles(glyphs, row["x"], row["y"])
                if prev is not None and prev_adj:
                    dmg = max(0, prev["hp"] - row["hp"]) \
                        if row["hp"] > 0 or row["done"] else 0
                    combat.append((step, row["t"] - prev["t"],
                                   prev["depth"], prev["hp"], prev["hpmax"],
                                   prev["xp"], prev["ac"], "|".join(prev_adj),
                                   rec.get("action"), dmg,
                                   1 if RE_KILL.search(msg or "") else 0))
                prev_adj = adj_now
                if prev is not None:
                    if 0 < row["hp"] < prev["hp"] or \
                            (row["hp"] == 0 and row["done"]):
                        adj = adj_hostiles(glyphs, prev["x"], prev["y"])
                        hp_drops.append(dict(
                            step=step, t=row["t"], depth=prev["depth"],
                            hp0=prev["hp"], hp1=row["hp"],
                            hpmax=prev["hpmax"], xp=prev["xp"],
                            adj=adj, act=row["action"],
                            msg=msg[:120] if msg else ""))
                    if row["hunger"] != prev["hunger"]:
                        hunger_traj.append((row["t"], row["hunger"]))
                    if row["ac"] != prev["ac"]:
                        ac_traj.append((row["t"], row["ac"]))
                    if row["action"] == "pray":
                        prayers.append((step, row["t"], prev["hp"],
                                        prev["hpmax"], prev["hunger"]))
                    if row["action"] == "eat":
                        eats.append((step, row["t"], prev["hunger"]))
                if not row["done"]:
                    final = row     # last live frame (death zeroes blstats)
                prev = row
                step += 1
    except Exception as e:
        return f"ERR {fn}: {e}"

    out = dict(file=os.path.relpath(fn, RESULTS), label=label, header=hdr,
               steps=step, depth_arrivals=depth_arrivals, max_depth=max_depth,
               hp_drops=hp_drops, kills=kills, prayers=prayers, eats=eats,
               hunger_traj=hunger_traj[:400], ac_traj=ac_traj[:200],
               last_msgs=last_msgs, final=final, combat=combat)
    with gzip.open(out_fn, "wt") as f:
        json.dump(out, f)
    return out_fn


def main():
    jobs = []
    for d in sorted(glob.glob(os.path.join(RESULTS, "transitions", "*"))):
        label = os.path.basename(d)
        for fn in sorted(glob.glob(os.path.join(d, "*.jsonl.gz"))):
            jobs.append((fn, label))
    print(f"{len(jobs)} episode logs")
    with Pool(4) as p:
        for i, r in enumerate(p.imap_unordered(mine_file, jobs)):
            if isinstance(r, str) and r.startswith("ERR"):
                print(r)
            if (i + 1) % 20 == 0:
                print(f"  {i+1}/{len(jobs)}")
    print("done")


if __name__ == "__main__":
    main()

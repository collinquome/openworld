"""E-NH1b: AVOIDABILITY AUDIT — "was this damage avoidable?"

Offline counterfactual replay over logged transitions. For every damage
event, reconstruct the agent's OWN information state at the decision
step (Atlas belief map replayed from step 0, inventory, HP/hunger) and
ask whether an alternative with a strictly better expected-damage
profile existed at comparable progression cost:

  THROW   first-contact vs a fast/never-outrun hostile with ammo held
          and a clear ray while it approached (distributional)
  KITE    pack fight in the open with a reachable choke on the belief
          map whose 1-at-a-time loss clearly beats the pack loss
          (movement exact, loss distributional)
  REST    descended at <60% hp with no visible hostile, then took
          damage on the new level while still hurt (state exact,
          benefit distributional)
  LOS     ranged damage with no adjacent hostile while an adjacent
          non-ray cell existed on the belief map (movement exact)
  EAT     starvation-class deaths where a fresh safe corpse was
          available while Weak+ (state exact)

Verdict classes: AVOIDABLE(mechanism) / UNAVOIDABLE(dice) / UNCERTAIN.
Movement counterfactuals are exact in the model; combat counterfactuals
inherit the exchange model's distributional epistemics (reported split).

Usage:
  python3 c2_avoid.py <transitions_dir_or_glob> [--out results/c2_avoid_<tag>.json]
"""

import glob
import gzip
import json
import os
import re
import sys
import collections

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "pylib"))

import nh_common as C
import nh_percept as P
from nh_transitions import read_episode

BL_HP, BL_HPMAX, BL_TIME, BL_HUNGER = 10, 11, 20, 21
BL_X, BL_Y = 0, 1

RE_KILL = re.compile(r"You (?:kill|destroy) the ([a-zA-Z' -]+?)!")
RANGED_HIT = ("arrow", "dart", "bolt", "wand", "missile", "gaze", "spits",
              "breathes")
FAST = P and None


class Obs:
    """Adapter: decoded transition row -> the obs dict Atlas expects."""

    def __init__(self, o):
        self.raw = o

    def as_atlas(self):
        g = np.array(self.raw["glyphs"], dtype=np.int32).reshape(21, 79)
        return {"obs": {"glyphs": g,
                        "blstats": np.array(self.raw["blstats"]),
                        "tty_chars": None,
                        "text_message": self.raw.get("message", ""),
                        "misc": np.array(self.raw.get("misc", [0, 0, 0]))}}


def ammo_letters(o):
    out = []
    letters = o.get("inv_letters", "")
    strs = o.get("inv_strs", [])
    for i, l in enumerate(letters):
        if i >= len(strs):
            break
        d = strs[i].lower()
        if "weapon in hand" in d:
            continue
        if any(k in d for k in P.AMMO_NAMES):
            out.append(l)
    return out


def ray_clear(L, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
        return False
    sx = (dx > 0) - (dx < 0)
    sy = (dy > 0) - (dy < 0)
    cx, cy = a[0] + sx, a[1] + sy
    while (cx, cy) != b:
        if not L.passable(cx, cy, bad_traps_ok=True):
            return False
        cx, cy = cx + sx, cy + sy
    return True


def audit_episode(fn):
    it = read_episode(fn)
    header = next(it)
    A = C.Atlas()
    topo = P.Topology()
    events = []          # damage events with verdicts
    total_dmg = 0
    prev = None          # previous decoded obs (decision state for action i)
    prev_bl = None
    prev_monsters = []
    first_contact = {}   # monster name -> (step, had_ammo, had_ray, dist)
    descents = []        # (step, hp_frac, hostiles_visible)
    last_descent = None
    kills = []           # (time, name)
    hunger_weak_with_corpse = 0
    steps = 0
    end_msg = ""
    for rec in it:
        o = rec["obs"] if "obs" in rec else rec
        obs = Obs(o).as_atlas()
        bl = o["blstats"]
        msg = o.get("message", "") or ""
        if msg:
            end_msg = msg
            for sp in RE_KILL.findall(msg):
                kills.append((bl[BL_TIME], sp.strip()))
        act = rec.get("action")
        if prev_bl is not None:
            dmg = prev_bl[BL_HP] - bl[BL_HP]
            if dmg > 0 and bl[BL_HP] >= 0:
                total_dmg += dmg
                # classify this damage event on the PREV decision state
                adj = [m for m in prev_monsters
                       if max(abs(m.x - prev_bl[BL_X]),
                              abs(m.y - prev_bl[BL_Y])) <= 1 and not m.pet]
                verdict, mech = "UNCERTAIN", None
                L = A.level
                if not adj:
                    lower = msg.lower()
                    if any(k in lower for k in RANGED_HIT):
                        # LOS counterfactual (movement-exact): was there an
                        # adjacent non-ray cell?
                        shooters = [m for m in prev_monsters if not m.pet
                                    and ray_clear(L, (prev_bl[BL_X],
                                                      prev_bl[BL_Y]), m.pos)]
                        alt = False
                        for name, (nx, ny) in L.neighbors(
                                prev_bl[BL_X], prev_bl[BL_Y]):
                            if all(not ray_clear(L, (nx, ny), m.pos)
                                   for m in shooters):
                                alt = True
                                break
                        if shooters and alt:
                            verdict, mech = "AVOIDABLE", "LOS"
                        elif shooters:
                            verdict, mech = "UNAVOIDABLE", "ranged-no-cover"
                        else:
                            verdict, mech = "UNCERTAIN", "offscreen-ranged"
                    else:
                        verdict, mech = "UNCERTAIN", "no-adjacency"
                else:
                    # melee event: alternatives at first contact + kiting
                    packs = len(adj)
                    if packs >= 2:
                        topo.refresh(L)
                        stats = [(m, P.species_dpt(m.name, m.difficulty),
                                  P.species_ttk(m.name, m.difficulty))
                                 for m in adj]
                        loss_open, alive = 0.0, sum(d for _, d, _ in stats)
                        for m, d, t in sorted(stats, key=lambda s: s[2]):
                            loss_open += alive * t
                            alive -= d
                        loss_choke = max(d for _, d, _ in stats) * \
                            sum(t for _, _, t in stats)
                        near_choke = any(
                            0 < max(abs(c[0] - prev_bl[BL_X]),
                                    abs(c[1] - prev_bl[BL_Y])) <= 3
                            for c in topo.chokes)
                        on_choke = (prev_bl[BL_X], prev_bl[BL_Y]) in \
                            topo.chokes
                        if near_choke and not on_choke and \
                                loss_choke < 0.75 * loss_open:
                            verdict, mech = "AVOIDABLE", "KITE"
                        else:
                            verdict, mech = "UNAVOIDABLE", "pack-no-choke"
                    else:
                        m0 = adj[0]
                        fc = first_contact.get(m0.name)
                        if fc and fc[1] and fc[2] and \
                                (m0.speed > 12 or m0.name in
                                 ("giant spider", "soldier ant", "giant ant",
                                  "fire ant", "killer bee")):
                            verdict, mech = "AVOIDABLE", "THROW"
                        elif last_descent is not None and \
                                bl[BL_TIME] - last_descent[0] < 300 and \
                                last_descent[1] < 0.6 and \
                                not last_descent[2]:
                            verdict, mech = "AVOIDABLE", "REST"
                        else:
                            dpt = P.species_dpt(m0.name, m0.difficulty)
                            ttk = P.species_ttk(m0.name, m0.difficulty)
                            if prev_bl[BL_HP] > 2.0 * dpt * ttk:
                                verdict, mech = "UNAVOIDABLE", "dice-won-fight"
                            else:
                                verdict, mech = "UNCERTAIN", "losing-1v1"
                        # hunger overlay: starving fights are food failures
                        if prev_bl[BL_HUNGER] >= 3:
                            fresh = [k for k in kills
                                     if bl[BL_TIME] - k[0] < 40 and
                                     k[1] in C.SAFE_CORPSES]
                            if fresh:
                                verdict, mech = "AVOIDABLE", "EAT"
                events.append(dict(step=steps, dmg=int(dmg),
                                   depth=int(prev_bl[12]),
                                   hp0=int(prev_bl[BL_HP]),
                                   verdict=verdict, mech=mech))
        # update belief with current obs
        A.update(obs)
        cur_monsters = list(A.level.monsters)
        # first-contact bookkeeping (dist 2-5, before adjacency)
        am = ammo_letters(o)
        for m in cur_monsters:
            if m.pet:
                continue
            d = max(abs(m.x - bl[BL_X]), abs(m.y - bl[BL_Y]))
            if 2 <= d <= 5 and m.name not in first_contact:
                first_contact[m.name] = (steps, bool(am),
                                         ray_clear(A.level,
                                                   (bl[BL_X], bl[BL_Y]),
                                                   m.pos), d)
        if act == "down" and prev_bl is not None:
            hostiles = any(not m.pet for m in prev_monsters)
            last_descent = (bl[BL_TIME],
                            prev_bl[BL_HP] / max(1, prev_bl[BL_HPMAX]),
                            hostiles)
        if bl[BL_HUNGER] >= 3:
            fresh = [k for k in kills if bl[BL_TIME] - k[0] < 40 and
                     k[1] in C.SAFE_CORPSES]
            if fresh:
                hunger_weak_with_corpse += 1
        prev = o
        prev_bl = bl
        prev_monsters = cur_monsters
        steps += 1

    av = sum(e["dmg"] for e in events if e["verdict"] == "AVOIDABLE")
    un = sum(e["dmg"] for e in events if e["verdict"] == "UNAVOIDABLE")
    uc = sum(e["dmg"] for e in events if e["verdict"] == "UNCERTAIN")
    mechs = collections.Counter()
    for e in events:
        if e["verdict"] == "AVOIDABLE":
            mechs[e["mech"]] += e["dmg"]
    death_final = events[-1] if events else None
    return dict(file=os.path.basename(fn), seed=header.get("seed"),
                steps=steps, total_dmg=int(total_dmg),
                avoidable=int(av), unavoidable=int(un), uncertain=int(uc),
                mech_mass=dict(mechs),
                final_event=death_final,
                weak_with_corpse_steps=int(hunger_weak_with_corpse),
                end=end_msg[:120])


def main():
    pat = sys.argv[1]
    out_fn = None
    if "--out" in sys.argv:
        out_fn = sys.argv[sys.argv.index("--out") + 1]
    files = sorted(glob.glob(os.path.join(pat, "*.jsonl.gz"))
                   if os.path.isdir(pat) else glob.glob(pat))
    rows = []
    for fn in files:
        try:
            rows.append(audit_episode(fn))
        except Exception as e:
            print(f"ERR {fn}: {e}")
    tot = sum(r["total_dmg"] for r in rows)
    av = sum(r["avoidable"] for r in rows)
    un = sum(r["unavoidable"] for r in rows)
    mechs = collections.Counter()
    for r in rows:
        for k, v in r["mech_mass"].items():
            mechs[k] += v
    fin = collections.Counter((r["final_event"] or {}).get("verdict")
                              for r in rows)
    finm = collections.Counter(
        (r["final_event"] or {}).get("mech") for r in rows
        if (r["final_event"] or {}).get("verdict") == "AVOIDABLE")
    print(f"episodes {len(rows)}  damage total {tot}  "
          f"AVOIDABLE {av} ({av/max(1,tot)*100:.0f}%)  "
          f"UNAVOIDABLE {un} ({un/max(1,tot)*100:.0f}%)  "
          f"UNCERTAIN {tot-av-un} ({(tot-av-un)/max(1,tot)*100:.0f}%)")
    print("avoidable mass by mechanism:", dict(mechs.most_common()))
    print("final (death-stretch) event verdicts:", dict(fin))
    print("deaths with AVOIDABLE final event, by mechanism:",
          dict(finm.most_common()))
    if out_fn:
        json.dump(rows, open(out_fn, "w"), indent=1)
        print("wrote", out_fn)


if __name__ == "__main__":
    main()

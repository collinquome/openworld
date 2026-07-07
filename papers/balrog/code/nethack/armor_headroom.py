"""ARMOR_DOCTRINE proximal evidence — DEFENSE headroom probe (s5).

MODEL: claude-opus-4-8[1m] (max thinking), Phase L session 5.

The defense analogue of the s4 WIELD offense-headroom probe. For each dev
seed, drive the REAL agent `upto` steps on nh_branch's verified-deterministic
stack, read the SERVED inventory + AC, and ask the s5 defense model
(nh_sheet.counterfactual_armor): is there a CARRIED-but-UNWORN armor piece
whose delta_rr (readiness-ratio via effective-HP) is positive? That is
"defense headroom" — the agent is walking around with better AC in its pack
than on its body. Proximal KPI (KPI_TREE.md) = DEFENSE (effective HP via AC).

Honest scope (v0.2, same caveats as the WIELD card + the slot-economics
note): headroom is computed as `AC - piece.ac`, i.e. it does NOT model
removing an already-worn piece in the same slot (a body-armor-over-body-armor
swap is overcounted). To keep the signal clean we therefore only count a
piece as headroom when it improves AC net AND is not flagged "(being worn)".
The number is a directional readiness signal, not a survival claim; survival
linkage needs a paired dev block (wire-in), exactly as WIELD's does.

Usage: python3 armor_headroom.py --seeds 700-739 --upto 150
"""

import argparse
import json
import os
import sys
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(HERE, "pylib"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
RESULTS = os.path.join(HERE, "results")

ARMOR_HINTS = ("armor", "mail", "shield", "cloak", "helmet", "helm",
               "gloves", "gauntlets", "boots", "shoes", "jacket", "shirt",
               "cap", "dragon scales", "mithril", "plate", "robe", "apron",
               "leather", "cornuthaum", "dunce")


def parse_seeds(spec):
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def probe(seed, upto):
    warnings.filterwarnings("ignore")
    import nh_branch as B
    import nh_common as C
    import nh_harness as H
    import nh_sheet as S
    from nle import nethack as nh
    from nh_agent import DiveAgent
    B.assert_dev_seed(seed)
    env = H.make_env()
    obs, _ = env.reset(seed=seed)
    space = list(env.env.language_action_space)
    agent = DiveAgent(log=lambda *a, **k: None)
    agent.set_actions(space)
    for _ in range(upto):
        a = agent.act(obs)
        obs, r, term, trunc, info = env.step(a if a in space else "search")
        if term or trunc:
            break
    raw = obs["obs"]
    bl = raw["blstats"]
    inv = C.inventory(obs)
    role = agent.role or "?"
    ac = int(bl[nh.NLE_BL_AC])
    hp, hpmax = int(bl[nh.NLE_BL_HP]), int(bl[nh.NLE_BL_HPMAX])
    depth = int(bl[nh.NLE_BL_DEPTH])
    xp = int(bl[nh.NLE_BL_XP])
    env.close()

    carried = []
    for let, desc, ocl in inv:
        d = desc.lower()
        if "(being worn)" in d or "(weapon in hand)" in d or "wielded" in d:
            continue
        if not any(h in d for h in ARMOR_HINTS):
            continue
        ca = S.counterfactual_armor(role, xp, ac, hp, hpmax, inv, depth, desc)
        if ca:
            _, dac, dhp, drr, note = ca
            carried.append({"letter": let, "desc": desc[:36], "d_ac": dac,
                            "d_eff_hp": dhp, "d_rr": drr, "note": note})
    carried.sort(key=lambda c: -c["d_rr"])
    best = carried[0] if carried else None
    return {"seed": seed, "role": role, "ac": ac, "hp": hp, "hpmax": hpmax,
            "depth": depth, "xp": xp, "n_carried_armor": len(carried),
            "best_headroom": best, "headroom": best is not None and
            best["d_rr"] > 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="700-739")
    ap.add_argument("--upto", type=int, default=150)
    ap.add_argument("--out", default=os.path.join(RESULTS,
                                                  "armor_headroom.json"))
    args = ap.parse_args()
    seeds = parse_seeds(args.seeds)
    rows, n_head = [], 0
    for s in seeds:
        try:
            r = probe(s, args.upto)
        except Exception as e:  # noqa: BLE001
            r = {"seed": s, "error": repr(e)[:160]}
        rows.append(r)
        if r.get("headroom"):
            n_head += 1
            b = r["best_headroom"]
            print(f"  seed {s} {r['role']:11} AC {r['ac']:3} D{r['depth']}: "
                  f"HEADROOM +{b['d_rr']} RR (+{b['d_eff_hp']} eff_hp) "
                  f"[{b['desc']}]", flush=True)
        else:
            print(f"  seed {s} {r.get('role','?'):11} "
                  f"AC {r.get('ac','?'):3} D{r.get('depth','?')}: "
                  f"no headroom (carried_armor {r.get('n_carried_armor',0)})",
                  flush=True)
    doc = {"model": "claude-opus-4-8[1m] (max thinking), s5",
           "upto": args.upto, "n_seeds": len(seeds),
           "n_headroom": n_head, "rows": rows}
    json.dump(doc, open(args.out, "w"), indent=1)
    print(f"\nARMOR HEADROOM: {n_head}/{len(seeds)} dev seeds carry unworn "
          f"armor with positive delta_rr. wrote {args.out}")


if __name__ == "__main__":
    main()

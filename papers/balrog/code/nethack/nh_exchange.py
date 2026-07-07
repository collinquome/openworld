"""Campaign-2 E-NH4 substrate: per-species exchange model with a
distributional verification gate (the stochastic generalization of the
ARC-3 exact-match gate; pre-registered alpha = 0.01).

Built ONLY from our own logged played episodes (results/c2_cache, mined
from served observations). For each species:
  - incoming: per-adjacent-game-turn damage distribution (single-adjacent
    rows only, unambiguous attribution), P(hit), mean dpt
  - outgoing: kill rate per adjacent turn -> E[turns to kill] (exponential)
  - verification: episode-level split (even/odd seed) train vs holdout;
    chi-square on binned damage histogram + two-sided binomial on kill
    rate. verified=False -> decision layer must use the conservative
    fallback (max of split dpt estimates, min of kill rates).

Fallback for unseen species: dpt regression on permonst difficulty
(source-derived difficulty is the disclosed offline world model).

Output: results/c2_exchange.json
"""

import glob
import gzip
import json
import os
import sys
import collections

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "pylib"))
import nh_common as C

RESULTS = os.path.join(HERE, "results")
CACHE = os.path.join(RESULTS, "c2_cache")
ALPHA = 0.01
BINS = [(0, 0), (1, 2), (3, 4), (5, 7), (8, 99)]

DIFF = {name: diff for (name, lvl, diff, spd, cls) in
        [C._SPECIES[i] for i in range(len(C._SPECIES))]}
SPEED = {name: spd for (name, lvl, diff, spd, cls) in
         [C._SPECIES[i] for i in range(len(C._SPECIES))]}


def binof(d):
    for i, (lo, hi) in enumerate(BINS):
        if lo <= d <= hi:
            return i
    return len(BINS) - 1


STRONG_ROLES = {"Barbarian", "Valkyrie", "Samurai", "Knight", "Caveman",
                "Cavewoman", "Monk"}


def seed_roles():
    """seed -> role, joined from every results JSON."""
    out = {}
    for fn in glob.glob(os.path.join(RESULTS, "nethack_results_*.json")) + \
            [os.path.join(RESULTS, "memory_paired.json")]:
        try:
            doc = json.load(open(fn))
        except Exception:
            continue
        for e in doc.get("episodes", []):
            if e.get("role"):
                out[e["seed"]] = e["role"]
    return out


def main():
    roles = seed_roles()
    per = {}   # species -> dict(train/holdout hists, kills, turns)
    packs = collections.Counter()   # n_adjacent -> rows (pack pressure)
    role_kt = {"strong": [0, 0], "weak": [0, 0]}   # [kills, turns]
    for fn in sorted(glob.glob(os.path.join(CACHE, "*.json.gz"))):
        d = json.load(gzip.open(fn, "rt"))
        seed = (d.get("header") or {}).get("seed")
        if seed is None:
            continue
        rc = "strong" if roles.get(seed) in STRONG_ROLES else "weak"
        fold = "train" if seed % 2 == 0 else "hold"
        for row in d.get("combat", []):
            (step, dt, depth, hp, hpmax, xp, ac, adj, act, dmg, kill) = row
            if dt <= 0:            # no game time passed: no monster turn
                continue
            names = adj.split("|")
            packs[len(names)] += 1
            if len(names) == 1:
                s = names[0]
                e = per.setdefault(s, dict(
                    train=collections.Counter(), hold=collections.Counter(),
                    kills={"train": 0, "hold": 0},
                    turns={"train": 0, "hold": 0}))
                # dt can be >1 (multi-turn actions): count turns, assign
                # damage to one turn (approximation, disclosed)
                e[fold][binof(min(dmg, 99))] += 1
                if dt > 1:
                    e[fold][0] += dt - 1
                e["turns"][fold] += dt
                e["kills"][fold] += kill
                # role-conditioned kill economy (mobile species only:
                # exclude the never-melee furniture we stand next to)
                spd = SPEED.get(s)
                if spd and spd > 0:
                    role_kt[rc][0] += kill
                    role_kt[rc][1] += dt

    out = {}
    for s, e in per.items():
        tr, ho = e["train"], e["hold"]
        n_tr, n_ho = sum(tr.values()), sum(ho.values())
        n = n_tr + n_ho
        if n < 12:
            continue
        allh = tr + ho
        mean_dmg = {}
        for tag, h in (("train", tr), ("hold", ho), ("all", allh)):
            tot = sum(h.values())
            mean_dmg[tag] = (sum(cnt * np.mean(range(BINS[b][0],
                                                     min(BINS[b][1], 15) + 1))
                                 for b, cnt in h.items()) / tot) if tot else 0.0
        turns = e["turns"]["train"] + e["turns"]["hold"]
        kills = e["kills"]["train"] + e["kills"]["hold"]
        kill_rate = kills / max(1, turns)
        # verification
        verified, pchi, pbin = None, None, None
        if n_tr >= 40 and n_ho >= 40:
            exp_p = np.array([tr.get(b, 0) for b in range(len(BINS))],
                             dtype=float)
            exp_p = (exp_p + 0.5) / exp_p.sum()      # smoothed train dist
            obs = np.array([ho.get(b, 0) for b in range(len(BINS))],
                           dtype=float)
            keep = exp_p > 0
            chi2 = (((obs - obs.sum() * exp_p) ** 2) /
                    (obs.sum() * exp_p))[keep].sum()
            pchi = float(stats.chi2.sf(chi2, keep.sum() - 1))
            tr_rate = e["kills"]["train"] / max(1, e["turns"]["train"])
            pbin = float(stats.binomtest(
                e["kills"]["hold"], max(1, e["turns"]["hold"]),
                min(1.0, max(1e-9, tr_rate))).pvalue)
            verified = bool(pchi >= ALPHA and pbin >= ALPHA)
        p_hit = 1.0 - allh.get(0, 0) / max(1, n)
        dpt = mean_dmg["all"]
        if verified is False:
            dpt = max(mean_dmg["train"], mean_dmg["hold"])   # conservative
        out[s] = dict(
            n_turns=int(turns), n_rows=int(n), p_hit=round(p_hit, 4),
            dpt=round(float(dpt), 3),
            dpt_split=[round(mean_dmg["train"], 3), round(mean_dmg["hold"], 3)],
            hist=[int(allh.get(b, 0)) for b in range(len(BINS))],
            kills=int(kills), kill_rate=round(float(kill_rate), 5),
            ttk=round(1.0 / kill_rate, 1) if kill_rate > 0 else None,
            verified=verified, p_chi=pchi, p_binom=pbin,
            difficulty=DIFF.get(s))

    # difficulty->dpt fallback regression over species with data
    xs = [v["difficulty"] for v in out.values()
          if v["difficulty"] is not None and v["n_turns"] >= 30]
    ys = [v["dpt"] for v in out.values()
          if v["difficulty"] is not None and v["n_turns"] >= 30]
    slope, icept = np.polyfit(xs, ys, 1) if len(xs) >= 5 else (0.15, 0.4)

    ver = [s for s, v in out.items() if v["verified"] is True]
    unver = [s for s, v in out.items() if v["verified"] is False]
    # role multipliers: class kill-rate / pooled kill-rate
    pooled = (role_kt["strong"][0] + role_kt["weak"][0]) / max(
        1, role_kt["strong"][1] + role_kt["weak"][1])
    role_mult = {}
    for rc, (k, t) in role_kt.items():
        role_mult[rc] = round((k / max(1, t)) / max(1e-9, pooled), 3) \
            if t > 500 else (1.7 if rc == "strong" else 0.85)
    doc = dict(alpha=ALPHA, bins=BINS,
               fallback=dict(slope=float(slope), intercept=float(icept)),
               pack_rows={str(k): int(v) for k, v in sorted(packs.items())},
               role_mult=role_mult, role_kt=role_kt,
               species=out)
    json.dump(doc, open(os.path.join(RESULTS, "c2_exchange.json"), "w"),
              indent=1)
    print(f"species with models: {len(out)}; verified {len(ver)}, "
          f"failed-verification {len(unver)}, "
          f"unverifiable(small-n) {len(out)-len(ver)-len(unver)}")
    print("failed:", unver)
    top = sorted(out.items(), key=lambda kv: -kv[1]["n_turns"])[:20]
    print(f"\n{'species':20s} {'turns':>6s} {'p_hit':>6s} {'dpt':>5s} "
          f"{'ttk':>6s} {'ver':>5s}")
    for s, v in top:
        print(f"{s:20s} {v['n_turns']:6d} {v['p_hit']:6.2f} {v['dpt']:5.2f} "
              f"{str(v['ttk']):>6s} {str(v['verified']):>5s}")
    print(f"\nfallback dpt ~= {icept:.2f} + {slope:.3f}*difficulty")


if __name__ == "__main__":
    main()

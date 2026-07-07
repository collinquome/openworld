"""Play-time possibility-set verification for the MAINLINE arm (Phase L
exit criterion v: per-episode violation rate < 1e-4, no unexplained
novelty entries).

MODEL: Fable 5 (max reasoning), session 2 — ported from the source-blind
arm's world_model.py predict/verify pair (fable_nethack_blind), where the
same checks ran live. Here they run OFFLINE over logged transitions, so
every dev/gym block gets a violation read for free with no scored-loop
footprint.

Possibility-set rules (each is a rule card; scopes inherited from the
blind arm's corroborated versions):

  V_TIME         game time is non-decreasing across a step
  V_MOVE         a single-step compass move lands on pos+d or pos
                 (blocked/interrupted); scope: depth unchanged
                 (trap falls relocate arbitrarily)
  V_NONMOVE_POS  non-movement actions leave position unchanged;
                 scope: depth unchanged; teleport-class events are
                 expected to flag here until scoped (novelty ledger)
  V_DEPTH        depth changes only via down (+1 stairs / +2 shaft),
                 up (-1); otherwise {d, d+1, d+2} (trapdoor/shaft)
  V_HP_BOUND     0 <= hp <= max(hpmax, 1)
  V_XP_MONO      experience level non-decreasing; drain-life is the
                 known scope exception -> violations here are
                 EXPLAINED novelty if the message says so

Terminal zeroed frames (done + time==0 + hpmax==0) are excluded
(R_TERMINAL_ZERO, blind-arm evidence E1:1030).

Usage:
  python3 c2_violations.py <transitions_dir_or_glob> [--out results/c2_violations_<tag>.json]
"""

import glob
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(_HERE, "pylib"), _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import nle.nethack as nh  # noqa: E402
from nh_transitions import read_episode  # noqa: E402

BLX, BLY = nh.NLE_BL_X, nh.NLE_BL_Y
BLHP, BLHPMAX = nh.NLE_BL_HP, nh.NLE_BL_HPMAX
BLTIME, BLDEPTH = nh.NLE_BL_TIME, nh.NLE_BL_DEPTH
BLXP = nh.NLE_BL_XP
BLCOND = nh.NLE_BL_CONDITION
# scope masks (first devb1 outing, 2026-07-07): confusion/stun make single-
# step moves land on ANY adjacent cell (random-walk mechanic) — V_MOVE is
# scoped OUT under these condition bits, mirroring the source model.
MASK_RANDOM_MOVE = (getattr(nh, "BL_MASK_CONF", 0) |
                    getattr(nh, "BL_MASK_STUN", 0))
# level-teleport signatures: depth may jump arbitrarily (both directions)
TELEPORT_MSGS = ("level teleport", "wrenching sensation")

DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0),
        "northeast": (1, -1), "southeast": (1, 1),
        "northwest": (-1, -1), "southwest": (-1, 1)}
POS_EXEMPT = {"up", "down", "jump", "move", "movefar", "rush", "rush2",
              "travel"}


def check_episode(fn):
    """Returns per-episode dict {steps_checked, violations, rate, by_rule,
    samples} for one transitions file."""
    by_rule = {}
    samples = []
    checked = 0
    prev = None
    step_i = 0
    for rec in read_episode(fn):
        if "obs" not in rec:          # header
            continue
        bl = rec["obs"]["blstats"]
        if prev is None:
            prev = (bl, None)
            continue
        step_i += 1
        pbl = prev[0]
        action = rec.get("action")
        done = rec.get("done")
        # terminal zeroed frame: excluded by R_TERMINAL_ZERO scope
        if done and bl[BLTIME] == 0 and bl[BLHPMAX] == 0:
            prev = (bl, action)
            continue

        def viol(rule, detail):
            by_rule[rule] = by_rule.get(rule, 0) + 1
            if len(samples) < 20:
                samples.append({"step": step_i, "rule": rule,
                                "action": action, "detail": detail,
                                "msg": rec["obs"].get("message", "")[:80]})

        checked += 1
        msg_l = (rec["obs"].get("message") or "").lower()
        confused = (bl[BLCOND] | pbl[BLCOND]) & MASK_RANDOM_MOVE
        teleported = any(t in msg_l for t in TELEPORT_MSGS)
        # V_TIME
        if bl[BLTIME] < pbl[BLTIME]:
            viol("V_TIME", [pbl[BLTIME], bl[BLTIME]])
        same_depth = bl[BLDEPTH] == pbl[BLDEPTH]
        # V_MOVE (scope: not under confusion/stun random-walk)
        if action in DIRS and same_depth and not confused:
            dx, dy = DIRS[action]
            allowed = ((pbl[BLX] + dx, pbl[BLY] + dy),
                       (pbl[BLX], pbl[BLY]))
            if (bl[BLX], bl[BLY]) not in allowed:
                viol("V_MOVE", [action, [pbl[BLX], pbl[BLY]],
                                [bl[BLX], bl[BLY]]])
        # V_NONMOVE_POS (same confusion/teleport scopes)
        if (action not in DIRS and action is not None and
                not str(action).startswith("far") and
                action not in POS_EXEMPT and same_depth and
                not confused and not teleported):
            if (bl[BLX], bl[BLY]) != (pbl[BLX], pbl[BLY]):
                viol("V_NONMOVE_POS", [action, [pbl[BLX], pbl[BLY]],
                                       [bl[BLX], bl[BLY]]])
        # V_DEPTH (scope: level-teleport signature allows any jump)
        d0 = pbl[BLDEPTH]
        if action == "up":
            allowed_d = {d0, max(1, d0 - 1)}
        else:
            allowed_d = {d0, d0 + 1, d0 + 2}
        if bl[BLDEPTH] not in allowed_d and not teleported:
            viol("V_DEPTH", [action, d0, bl[BLDEPTH]])
        # V_HP_BOUND
        if not (0 <= bl[BLHP] <= max(bl[BLHPMAX], 1)):
            viol("V_HP_BOUND", [bl[BLHP], bl[BLHPMAX]])
        # V_XP_MONO (scopes: drain-life + god punishment — both announce)
        if bl[BLXP] < pbl[BLXP] and not any(
                t in msg_l for t in ("drain", "less experienced",
                                     "voice of")):
            viol("V_XP_MONO", [pbl[BLXP], bl[BLXP]])
        prev = (bl, action)

    n_viol = sum(by_rule.values())
    return {"file": os.path.basename(fn), "steps_checked": checked,
            "violations": n_viol,
            "rate": (n_viol / checked) if checked else 0.0,
            "by_rule": by_rule, "samples": samples}


def main():
    pat = sys.argv[1]
    out_fn = None
    if "--out" in sys.argv:
        out_fn = sys.argv[sys.argv.index("--out") + 1]
    files = sorted(glob.glob(os.path.join(pat, "*.jsonl.gz"))
                   if os.path.isdir(pat) else glob.glob(pat))
    eps = []
    for fn in files:
        r = check_episode(fn)
        eps.append(r)
        print(f"{r['file']}: {r['violations']}/{r['steps_checked']} "
              f"rate {r['rate']:.2e} {r['by_rule'] or ''}", flush=True)
    tot_v = sum(e["violations"] for e in eps)
    tot_s = sum(e["steps_checked"] for e in eps)
    agg = {"episodes": eps, "total_violations": tot_v,
           "total_steps": tot_s,
           "rate": (tot_v / tot_s) if tot_s else 0.0,
           "criterion_v_pass": tot_s > 0 and (tot_v / tot_s) < 1e-4}
    print(f"AGGREGATE: {tot_v}/{tot_s} rate {agg['rate']:.2e} "
          f"criterion(v)<1e-4: {agg['criterion_v_pass']}")
    if out_fn:
        with open(out_fn, "w") as f:
            json.dump(agg, f, indent=1)


if __name__ == "__main__":
    main()

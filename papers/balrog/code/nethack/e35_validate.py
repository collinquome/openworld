"""NH-E35a — WORLD-MODEL VALIDATION on EXPERT (alt.org) human ttyrecs.

MODEL: claude-opus-4-8 (max thinking), Phase L session 9.

Replays public human NetHack play through our symbolic possibility-set world
model (the SAME rules as c2_violations.py, ported to the tty-only observation we
can recover from V1 ttyrecs) and counts violations. Each violation = a
transition our model calls impossible that a real expert produced => a genuine
model gap we could NEVER surface from our own <=Dlvl21 play.

Observation recoverable from a V1 human ttyrec = the rendered tty only (NO action
labels, NO glyph/blstats arrays — those are NLE-internal). So we run the
ACTION-FREE subset of the possibility set, which is exactly the world-model
INVARIANT layer:
  V_TIME    game time (T:) non-decreasing
  V_HP      0 <= hp <= max(hpmax,1)
  V_XP      xp level non-decreasing (drain-life = explained novelty via message)
  V_DEPTH   for a single-turn step (dT==1) depth' in {d-1,d,d+1,d+2}
            (stairs +/-1, trapdoor/hole/shaft down +2); teleport msg scopes out
  V_MOVE    for a single-turn step (dT==1), same depth, no teleport/confusion:
            hero cursor moves <=1 in chebyshev (a move-action possibility set)
V_NONMOVE_POS is omitted: it needs the action label (absent from human ttyrecs).

DUAL PROVENANCE
  knowledge  = DEMONSTRATION: public alt.org human ttyrecs, used OFFLINE for
               world-model validation (like reading the wiki/source; disclosed).
  insight-origin = OP (operator 2026-07-07 s5, NH-E35 design in NETHACK_PROGRAM.md).
REPLICATION RECIPE
  1. list https://www.alt.org/nethack/userdata/<L>/<user>/ttyrec/ (Apache index)
  2. fetch a handful of completed .ttyrec (timeout-guarded, modest) to
     work/fable_nethack/ttyrecs/  (top-class players: rschaff, nnnet, ...)
  3. python3 e35_validate.py   (emulator = e35_ttyrec.py; foreground, no net)
Clean-protocol: this is OFFLINE analysis only; scored agent runs stay pure-code.
"""

import glob
import json
import os
import sys

from e35_ttyrec import (Term, iter_records, parse_status, hero_pos, message)

HERE = os.path.dirname(os.path.abspath(__file__))

TELEPORT_MSG = ("level teleport", "wrenching sensation", "you materialize",
                "trap door", "trapdoor", "fall through", "plunge", "hole opens")
DRAIN_MSG = ("drain", "life force", "weaker", "less experienced", "you feel");


def build_steps(path):
    """Emulate a ttyrec -> ordered list of settled per-turn states.

    A state is flushed whenever (time, depth) changes; we keep the LAST record
    seen for a given (time,depth) so the cursor is settled on the hero. Returns
    (steps, meta). steps: list of dict{time,depth,hp,hpmax,xp,conds,pos,msg}.
    """
    term = Term()
    steps = []
    cur_key = None          # (time, depth)
    buf = None              # latest state dict for cur_key
    nrec = 0
    nparsed = 0
    for _ts, data in iter_records(path):
        nrec += 1
        term.feed(data)
        st = parse_status(term)
        if st is None:
            continue
        nparsed += 1
        key = (st["time"], st["depth"])
        state = {
            "time": st["time"], "depth": st["depth"], "hp": st["hp"],
            "hpmax": st["hpmax"], "xp": st["xp"], "conds": st["conds"],
            "pos": hero_pos(term), "msg": message(term).lower(),
        }
        if cur_key is None:
            cur_key, buf = key, state
        elif key != cur_key:
            steps.append(buf)      # flush settled previous state
            cur_key, buf = key, state
        else:
            # same turn: keep newest; prefer a frame that HAS a hero pos
            if buf.get("pos") is None and state["pos"] is not None:
                state["msg"] = buf["msg"] or state["msg"]
            buf = state
    if buf is not None:
        steps.append(buf)
    meta = {"records": nrec, "parsed": nparsed, "steps": len(steps),
            "maxDlvl": max((s["depth"] for s in steps if s["depth"]), default=0)}
    return steps, meta


def check(steps):
    res = {r: {"checked": 0, "viol": 0, "samples": []}
           for r in ("V_TIME", "V_HP", "V_XP", "V_DEPTH", "V_MOVE")}

    def flag(rule, i, why, prev, cur):
        res[rule]["viol"] += 1
        if len(res[rule]["samples"]) < 8:
            res[rule]["samples"].append({
                "step": i, "why": why,
                "prev": {k: prev.get(k) for k in ("time", "depth", "hp",
                         "hpmax", "xp", "pos")},
                "cur": {k: cur.get(k) for k in ("time", "depth", "hp",
                        "hpmax", "xp", "pos")},
                "msg": cur.get("msg", "")[:60]})

    for i in range(len(steps)):
        cur = steps[i]
        # V_HP (per-frame invariant)
        if cur["hpmax"] is not None:
            res["V_HP"]["checked"] += 1
            if not (0 <= cur["hp"] <= max(cur["hpmax"], 1)):
                flag("V_HP", i, "hp out of [0,hpmax]", steps[i - 1] if i else {}, cur)
        if i == 0:
            continue
        prev = steps[i - 1]
        dt = cur["time"] - prev["time"]
        msg = cur["msg"]
        # V_TIME
        res["V_TIME"]["checked"] += 1
        if cur["time"] < prev["time"]:
            flag("V_TIME", i, "time decreased", prev, cur)
        # V_XP
        if cur["xp"] is not None and prev["xp"] is not None:
            res["V_XP"]["checked"] += 1
            if cur["xp"] < prev["xp"]:
                if not any(m in msg for m in DRAIN_MSG):
                    flag("V_XP", i, "xp decreased (no drain msg)", prev, cur)
        # single-turn-scoped rules
        if dt == 1 and cur["depth"] is not None and prev["depth"] is not None:
            tele = any(m in msg for m in TELEPORT_MSG)
            # V_DEPTH
            res["V_DEPTH"]["checked"] += 1
            dd = cur["depth"] - prev["depth"]
            if not tele and dd not in (-1, 0, 1, 2):
                flag("V_DEPTH", i, f"depth jumped {dd} in 1 turn", prev, cur)
            # V_MOVE (same depth, positions known, not tele/confused/stunned)
            if (dd == 0 and not tele and prev["pos"] and cur["pos"]
                    and not (prev["conds"] & {"Conf", "Stun"})):
                res["V_MOVE"]["checked"] += 1
                cheb = max(abs(cur["pos"][0] - prev["pos"][0]),
                           abs(cur["pos"][1] - prev["pos"][1]))
                if cheb > 1:
                    flag("V_MOVE", i, f"hero moved chebyshev={cheb} in 1 turn",
                         prev, cur)
    return res


def main():
    files = sorted(glob.glob(os.path.join(HERE, "ttyrecs", "*.ttyrec")))
    files = [f for f in files if os.path.getsize(f) > 1000]
    if not files:
        print("no ttyrecs cached")
        return
    agg = {r: {"checked": 0, "viol": 0} for r in
           ("V_TIME", "V_HP", "V_XP", "V_DEPTH", "V_MOVE")}
    report = {"games": [], "aggregate": {}}
    for f in files:
        steps, meta = build_steps(f)
        res = check(steps)
        game = {"file": os.path.basename(f), **meta, "rules": {}}
        for r, d in res.items():
            rate = d["viol"] / d["checked"] if d["checked"] else 0.0
            game["rules"][r] = {"checked": d["checked"], "viol": d["viol"],
                                "rate": rate, "samples": d["samples"][:5]}
            agg[r]["checked"] += d["checked"]
            agg[r]["viol"] += d["viol"]
        report["games"].append(game)
        print(f"\n=== {os.path.basename(f)} ===")
        print(f"  records={meta['records']} steps={meta['steps']} "
              f"maxDlvl={meta['maxDlvl']}")
        for r in ("V_TIME", "V_HP", "V_XP", "V_DEPTH", "V_MOVE"):
            g = game["rules"][r]
            print(f"  {r:8s} checked={g['checked']:6d} viol={g['viol']:4d} "
                  f"rate={g['rate']:.2e}")

    tot_checked = sum(agg[r]["checked"] for r in agg)
    tot_viol = sum(agg[r]["viol"] for r in agg)
    report["aggregate"] = {
        "by_rule": {r: {"checked": agg[r]["checked"], "viol": agg[r]["viol"],
                        "rate": (agg[r]["viol"] / agg[r]["checked"]
                                 if agg[r]["checked"] else 0.0)} for r in agg},
        "total_checked": tot_checked, "total_viol": tot_viol,
        "overall_rate": tot_viol / tot_checked if tot_checked else 0.0}
    print("\n=== AGGREGATE (all expert games) ===")
    for r in ("V_TIME", "V_HP", "V_XP", "V_DEPTH", "V_MOVE"):
        a = report["aggregate"]["by_rule"][r]
        print(f"  {r:8s} checked={a['checked']:6d} viol={a['viol']:4d} "
              f"rate={a['rate']:.2e}")
    print(f"  TOTAL    checked={tot_checked} viol={tot_viol} "
          f"rate={report['aggregate']['overall_rate']:.2e}")

    out = os.path.join(HERE, "results", "e35_validate.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(report, fh, indent=2, default=list)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()

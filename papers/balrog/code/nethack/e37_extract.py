"""NH-E37 — per-class EARLY-GAME expert-routine extractor from alt.org ttyrecs.

MODEL: claude-opus-4-8 (max thinking), Phase L NH-E37 session. Runtime identity
verified at session open (system-prompt id = claude-opus-4-8, matches intended
assignment; Fable at usage cap) — no mismatch. Tier-sensitive strategy
extraction done carefully.

WHY: 13 hand-designed levers nulled (capability/acquisition-bound wall,
PROGRAM_FINDINGS). The one un-mined source = WHAT EXPERTS ACTUALLY DO in the
early game, PER CLASS (D1-6, exactly where our agent dies). This extractor
reads the rendered tty message-line + status stream (the only signal a V1
human ttyrec exposes — no action labels) and reconstructs each expert's
opening routine: what they EAT and at which hunger tier, when they WIELD/WEAR,
PRAYER timing, PET usage, dive pacing (turns to reach each depth D1-6),
combat intensity, shop/altar/BUC behavior.

provenance: DEMONSTRATION (public alt.org human ttyrecs, used OFFLINE for
research; disclosed). insight-origin = OP (operator NH-E37 directive: "analyze
expert play and bake the strategies for early levels for all classes").
Reuses the e35_ttyrec.py ANSI emulator (same provenance class as e35_validate).

Clean-protocol: OFFLINE analysis only; scored agent runs stay pure-code.
Usage: PYTHONPATH=pylib python3 e37_extract.py            # all ttyrecs
       PYTHONPATH=pylib python3 e37_extract.py --json out.json
"""
import glob
import json
import os
import re
import sys

from e35_ttyrec import Term, iter_records, parse_status, message

HERE = os.path.dirname(os.path.abspath(__file__))
TTYRECS = os.path.join(HERE, "ttyrecs")

# nh_agent.py's own welcome regex (source of truth for role parse)
WELCOME = re.compile(r"You are an? ([a-z ]+) (\w+) (\w+)\.")
BACK = re.compile(r"the (\w+), welcome back")   # save-continuation form

# hunger tiers live on the status line, worst active tier shown
HUNGER = re.compile(r"\b(Satiated|Hungry|Weak|Fainting|Fainted)\b")
HUNGER_RANK = {"Satiated": -1, None: 0, "Hungry": 1, "Weak": 2,
               "Fainting": 3, "Fainted": 3}

# --- message-line behaviour patterns (top line) -----------------------------
PAT = {
    "eat":    re.compile(r"You (?:finish eating|eat|swallow|.*devour)", re.I),
    "eat_what": re.compile(r"eating (?:the |an? )?([a-z ]+?)[.!]", re.I),
    "wield":  re.compile(r"You (?:are (?:now )?wielding|swap.*wielding|now wield)", re.I),
    "twoweap": re.compile(r"(?:two-weapon|wielding two)", re.I),
    "wear":   re.compile(r"You (?:are now wearing|finish (?:putting on|your dressing)|put on)", re.I),
    "takeoff": re.compile(r"You (?:finish taking off|were wearing|take off)", re.I),
    "pray":   re.compile(r"You (?:finish your prayer|begin praying)", re.I),
    "pray_ok": re.compile(r"(?:seems? (?:pleased|to be pleased)|You feel (?:much )?better|isreturned to|restore)", re.I),
    "altar":  re.compile(r"\baltar\b", re.I),
    "buc":    re.compile(r"(?:amber|black) (?:flash|light)|flash of (?:amber|black)", re.I),
    "throw":  re.compile(r"You (?:throw|shoot)|finds? a mark|hits?!|(?:arrow|dagger|dart|spear|shuriken)", re.I),
    "pet":    re.compile(r"swap places with|You displaced|(?:your|the) (?:kitten|dog|pony|little dog|large dog|jackal|pet)", re.I),
    "kill":   re.compile(r"You (?:kill|destroy|smite)|is (?:killed|destroyed)!", re.I),
    "hit":    re.compile(r"You (?:hit|smite|swing)|You miss", re.I),
    "cast":   re.compile(r"You cast|force bolt|zap of|beam of|frost|fire bolt", re.I),
    "pick":   re.compile(r"^[a-zA-Z] - (?:an? |the )?", re.I),   # inventory-add line
    "shop":   re.compile(r"(?:shopkeeper|for sale|costs?|Welcome to.*shop|charged you)", re.I),
    "stair":  re.compile(r"staircase (?:up|down)|You (?:descend|climb)", re.I),
    "identify": re.compile(r"You have a[a-z ]* (scroll|potion|wand|ring|spellbook)", re.I),
    "dip":    re.compile(r"You dip", re.I),
    "engrave": re.compile(r"You (?:write|engrave)|Elbereth", re.I),
}

STOP_TURN = 2000    # early-game window (~D1-6)


def role_of(steps_msgs):
    for m in steps_msgs:
        w = WELCOME.search(m)
        if w:
            return w.group(3), w.group(2), w.group(1)
        b = BACK.search(m)
        if b:
            return b.group(1), "?", "?"
    return None, None, None


def extract(path):
    term = Term()
    role = race = align = None
    # per-turn de-duped message stream + status
    events = []           # (T, depth, hunger_tier, msg)
    all_early_msgs = []
    last_key = None
    depth_first_T = {}     # depth -> first game-turn T reached
    for _ts, data in iter_records(path):
        term.feed(data)
        msg = message(term)
        st = parse_status(term)
        # role detection (welcome / welcome-back), scan messages
        if role is None and msg:
            r, rc, al = role_of([msg])
            if r:
                role, race, align = r, rc, al
        if st is None:
            continue
        T = st["time"]
        depth = st["depth"]
        # hunger tier from the full status text
        sline = term.line(term.rows - 1) + " " + term.line(term.rows - 2)
        hm = HUNGER.search(sline)
        hunger = hm.group(1) if hm else None
        if depth is not None and depth not in depth_first_T and T is not None:
            depth_first_T[depth] = T
        key = (T, msg)
        if key != last_key and msg.strip():
            last_key = key
            if T is not None and T <= STOP_TURN:
                events.append((T, depth, hunger, msg.strip()))
                all_early_msgs.append(msg.strip())
        if T is not None and T > STOP_TURN + 50:
            # a little past window is fine; stop once clearly beyond
            if len(events) > 30:
                break
    if role is None:
        role, race, align = role_of(all_early_msgs)

    # --- mine the routine ---
    def hits(patkey):
        p = PAT[patkey]
        return [(T, d, h, m) for (T, d, h, m) in events if p.search(m)]

    eats = []
    for (T, d, h, m) in events:
        if PAT["eat"].search(m):
            what = PAT["eat_what"].search(m)
            eats.append({"T": T, "depth": d, "hunger": h,
                         "what": (what.group(1).strip() if what else m[:40])})
    wields = [{"T": T, "depth": d, "msg": m[:60]} for (T, d, h, m) in hits("wield")]
    twoweap = [{"T": T, "msg": m[:50]} for (T, d, h, m) in hits("twoweap")]
    wears = [{"T": T, "depth": d, "msg": m[:60]} for (T, d, h, m) in hits("wear")]
    prays = [{"T": T, "depth": d, "hunger": h, "msg": m[:60]} for (T, d, h, m) in hits("pray")]
    altars = [{"T": T, "depth": d, "msg": m[:60]} for (T, d, h, m) in hits("altar")][:6]
    pets = hits("pet")
    throws = hits("throw")
    casts = hits("cast")
    kills = hits("kill")
    shops = [{"T": T, "depth": d, "msg": m[:50]} for (T, d, h, m) in hits("shop")][:5]
    engrave = [{"T": T, "msg": m[:50]} for (T, d, h, m) in hits("engrave")][:5]

    # dive pacing: turn to first reach each depth (D1-6)
    pacing = {f"D{d}": depth_first_T[d] for d in sorted(depth_first_T) if d <= 6}

    # hunger discipline: worst hunger tier ever seen in the window, and the
    # tier at which the FIRST eat happened
    worst = None
    for (T, d, h, m) in events:
        if h and HUNGER_RANK.get(h, 0) > HUNGER_RANK.get(worst, 0):
            worst = h
    first_eat_hunger = eats[0]["hunger"] if eats else None

    return {
        "file": os.path.basename(path),
        "role": role, "race": race, "align": align,
        "window_turns": STOP_TURN,
        "n_events": len(events),
        "max_depth_in_window": max([d for (_T, d, _h, _m) in events if d], default=None),
        "dive_pacing_turn_to_depth": pacing,
        "worst_hunger_in_window": worst,
        "first_eat_at_hunger": first_eat_hunger,
        "eat_events": eats[:12],
        "n_eats": len(eats),
        "wield_events": wields[:6],
        "two_weapon": bool(twoweap),
        "wear_events": wears[:6],
        "pray_events": prays[:4],
        "n_pray": len(prays),
        "altar_touch": altars,
        "engrave_elbereth": engrave,
        "n_pet_interactions": len(pets),
        "n_throws": len(throws),
        "n_casts": len(casts),
        "n_kills": len(kills),
        "n_shop_msgs": len(shops),
        "shop_samples": shops,
    }


def main():
    files = sorted(glob.glob(os.path.join(TTYRECS, "*.ttyrec")))
    files = [f for f in files if os.path.getsize(f) > 1000]
    out = []
    for f in files:
        rec = extract(f)
        out.append(rec)
        print(f"\n=== {rec['file']}  ROLE={rec['role']} ({rec['race']}/{rec['align']}) ===")
        print(f"  events={rec['n_events']} maxD_in_window={rec['max_depth_in_window']} "
              f"pacing={rec['dive_pacing_turn_to_depth']}")
        print(f"  HUNGER: worst={rec['worst_hunger_in_window']} "
              f"first_eat_at={rec['first_eat_at_hunger']} n_eats={rec['n_eats']}")
        if rec["eat_events"]:
            for e in rec["eat_events"][:5]:
                print(f"    eat T={e['T']} hunger={e['hunger']} -> {e['what']}")
        print(f"  WIELD n={len(rec['wield_events'])} twoweapon={rec['two_weapon']} "
              f"WEAR n={len(rec['wear_events'])} PRAY n={rec['n_pray']} "
              f"altar={len(rec['altar_touch'])} engrave={len(rec['engrave_elbereth'])}")
        for w in rec["wield_events"][:3]:
            print(f"    wield T={w['T']} : {w['msg']}")
        for w in rec["wear_events"][:3]:
            print(f"    wear  T={w['T']} : {w['msg']}")
        for p in rec["pray_events"][:2]:
            print(f"    pray  T={p['T']} hunger={p['hunger']} : {p['msg']}")
        print(f"  COMBAT: kills={rec['n_kills']} throws={rec['n_throws']} "
              f"casts={rec['n_casts']} pet_interactions={rec['n_pet_interactions']} "
              f"shop_msgs={rec['n_shop_msgs']}")

    if "--json" in sys.argv:
        p = sys.argv[sys.argv.index("--json") + 1]
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        json.dump(out, open(p, "w"), indent=2, default=list)
        print(f"\nwrote {p}")


if __name__ == "__main__":
    main()

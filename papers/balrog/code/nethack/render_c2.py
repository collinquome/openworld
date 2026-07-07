"""Campaign-2 renderer: watch the agent THINK.

Beside the tty map view, each frame shows:
  - belief mini-map (explored / unknown / walls / doors / stairs / suspects)
  - planned A* route overlaid on the main map (solid for the commit
    horizon, fading beyond) + on the mini-map
  - threat rings: per-monster tint scaled by exchange-model dpt
  - active subgoal + reason, HP / hunger bars, step counter
  - expectimax decision annotations when they fire

Renders purely from logged trajectory data (frames + belief snapshots +
subgoal/plan/EV ledgers). Old trajectories without belief data degrade
gracefully (no sidebar).

Usage: python3 render_c2.py <traj.json> <out.gif> [title]
"""

import bisect
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(HERE, "balrog", "environments", "nle",
                         "Hack-Regular.ttf")
FONT = ImageFont.truetype(FONT_PATH, 14)
FONT_S = ImageFont.truetype(FONT_PATH, 12)
FONT_XS = ImageFont.truetype(FONT_PATH, 10)
CW, CH = 9, 16
COLS, ROWS = 80, 24
MAPR = 21                 # map rows are tty rows 1..21
MAXF = 420
SIDE = 350                # sidebar width
HDR = 22                  # dedicated top header strip (px); map drawn BELOW it (s4 opus-4.8, no-overlap fix)
MCW, MCH = 4, 5           # mini-map cell size

PALETTE = {
    "@": (255, 221, 51), ">": (80, 250, 123), "<": (139, 233, 253),
    "{": (98, 114, 164), "}": (255, 85, 85), "`": (241, 250, 140),
    "#": (130, 130, 130), ".": (90, 90, 90), "+": (255, 184, 108),
    "|": (170, 170, 170), "-": (170, 170, 170), "^": (255, 121, 198),
    "(": (189, 147, 249), ")": (189, 147, 249), "/": (189, 147, 249),
    "!": (189, 147, 249), "?": (189, 147, 249), "*": (189, 147, 249),
    "$": (255, 215, 0), "%": (255, 165, 90),
}
DEFAULT = (220, 220, 220)
MONSTER = (255, 85, 85)

# belief terrain codes (chr(65+t), nh_common terrain enum order)
T_COLORS = {
    0: (24, 24, 34),      # UNKNOWN
    1: (70, 78, 110),     # WALL
    2: (52, 52, 64),      # FLOOR
    3: (44, 44, 50),      # CORRIDOR
    4: (200, 140, 60),    # DOORWAY
    5: (255, 184, 108),   # DOOR_OPEN
    6: (180, 90, 40),     # DOOR_CLOSED
    7: (80, 250, 123),    # STAIRS_DOWN
    8: (139, 233, 253),   # STAIRS_UP
    9: (255, 85, 85),     # LAVA
    17: (80, 250, 123),   # HOLE_DOWN
    18: (255, 121, 198),  # BAD_TRAP
    13: (98, 114, 164),   # WATER
}

# species -> dpt (exchange model), for threat tint
_EXC = None


def dpt_of(name):
    global _EXC
    if _EXC is None:
        fn = os.path.join(HERE, "results", "c2_exchange.json")
        _EXC = json.load(open(fn)) if os.path.exists(fn) else {"species": {}}
    v = _EXC["species"].get(name)
    return v["dpt"] if v else 1.0


def latest(entries, step, key=lambda e: e[0]):
    """Last ledger entry with entry_step <= step, or None."""
    lo, hi = 0, len(entries)
    while lo < hi:
        mid = (lo + hi) // 2
        if key(entries[mid]) <= step:
            lo = mid + 1
        else:
            hi = mid
    return entries[lo - 1] if lo else None


def hbar(d, x, y, w, h, frac, fg, bg=(50, 50, 60)):
    d.rectangle([x, y, x + w, y + h], fill=bg)
    d.rectangle([x, y, x + int(w * max(0.0, min(1.0, frac))), y + h],
                fill=fg)


def render(traj_file, out_gif, title=""):
    t = json.load(open(traj_file))
    frames = t["frames"]
    fsteps = t["frame_steps"]
    beliefs = t.get("beliefs") or []
    monsters = t.get("monsters") or []
    plans = t.get("plans") or []
    subgoals = t.get("subgoals") or []
    evs = t.get("evs") or []
    hunger_arr = t.get("hunger") or []
    has_side = bool(beliefs)
    W = COLS * CW + 16 + (SIDE if has_side else 0)
    H = (ROWS + 3) * CH + 12 + HDR
    n = len(frames)
    stride = max(1, (n + MAXF - 1) // MAXF)
    idxs = list(range(0, n, stride))
    if idxs[-1] != n - 1:
        idxs.append(n - 1)
    bel_by_step = {b[0]: b for b in beliefs}
    mon_by_step = {m[0]: m for m in monsters}
    pred = t.get("pred_dmg") or []

    # ---- knowledge-provenance events (operator: watch the agent think)
    # merged from EV annotations + decision notes; color by provenance
    KCOLORS = {"novel": (255, 85, 85), "lesson": (255, 121, 198),
               "stats": (139, 233, 253), "source": (255, 184, 108),
               "guard": (80, 250, 123)}

    def kclass(txt):
        tl = txt.lower()
        if tl.startswith("novel") or "novel" in tl[:20]:
            return "novel"
        if any(k in tl for k in ("veto", "prayfix", "touchkill")):
            return "guard"
        if any(k in tl for k in ("ev ", "elbereth", "loss")):
            return "stats"
        if any(k in tl for k in ("mines", "peaceful", "cannib", "corpse",
                                 "pray", "wrath")):
            return "source"
        return "lesson"

    kevents = []       # (step, class, text)
    for s, txt in evs:
        kevents.append((s, kclass(txt), txt))
    for line in t.get("notes", []):
        try:
            sp, txt = line.split(":", 1)
            s = int(sp.replace("step", "").strip())
        except Exception:
            continue
        txt = txt.strip()
        if any(k in txt for k in ("Mines", "peaceful", "digging", "wearing",
                                  "picking up", "engraving", "cornered",
                                  "giving up", "learned")):
            kevents.append((s, kclass(txt), txt))
    kevents.sort(key=lambda e: e[0])

    imgs = []
    for i in idxs:
        step = fsteps[i]
        j = min(step, len(t["actions"])) - 1
        hp = t["hp"][j] if j >= 0 else [1, 1]
        depth = t["depth"][j] if j >= 0 else 1
        act = t["actions"][j] if j >= 0 else "-"
        hun = hunger_arr[j] if 0 <= j < len(hunger_arr) else 1
        pos = t["positions"][j] if j >= 0 else [0, 0]
        img = Image.new("RGB", (W, H), (12, 12, 20))
        d = ImageDraw.Draw(img, "RGBA")

        # ---- threat tints under monster glyphs (main map)
        mon = mon_by_step.get(step)
        if mon:
            for (mx, my, name, pet) in mon[1]:
                if pet:
                    color = (80, 250, 123, 60)
                else:
                    k = min(1.0, dpt_of(name) / 5.0)
                    color = (255, int(120 * (1 - k)), 40, 90)
                d.rectangle([8 + mx * CW - 1, (my + 1) * CH + 3 + HDR,
                             8 + (mx + 1) * CW, (my + 2) * CH + 3 + HDR],
                            fill=color)

        # ---- planned path overlay (main map), fading past horizon
        pl = latest(plans, step)
        if pl and pl[1]:
            for k, (px, py) in enumerate(pl[1][:24]):
                alpha = 150 if k < 8 else max(30, 150 - (k - 8) * 15)
                d.rectangle([8 + px * CW + 2, (py + 1) * CH + 6 + HDR,
                             8 + px * CW + CW - 3, (py + 2) * CH + 1 + HDR],
                            fill=(241, 250, 140, alpha))

        # ---- tty characters
        for r, line in enumerate(frames[i][:ROWS]):
            for c, ch in enumerate(line[:COLS]):
                if ch == " ":
                    continue
                color = PALETTE.get(ch)
                if color is None:
                    color = MONSTER if ch.isalpha() and 1 <= r <= MAPR \
                        else DEFAULT
                d.text((8 + c * CW, (r + 1) * CH + 4 + HDR), ch, font=FONT_S,
                       fill=color)

        # ---- header STRIP (dedicated; map is pushed below it, no overlap)
        d.rectangle([0, 0, W, HDR], fill=(30, 30, 48))  # FULL-WIDTH header
        d.text((8, 3), f"{title}  step {step}  Dlvl {depth}  last:{act}",
               font=FONT, fill=(255, 221, 51))
        # footer: message
        d.text((8, (ROWS + 1) * CH + 8 + HDR),
               (t["messages"][j][:96] if j >= 0 else ""),
               font=FONT_S, fill=(139, 233, 253))

        sg = latest(subgoals, step)
        ev = latest(evs, step)
        if has_side:
            x0 = COLS * CW + 24
            # subgoal + reason
            d.text((x0, 4 + HDR + 14), "SUBGOAL", font=FONT_XS, fill=(120, 120, 140))
            if sg:
                d.text((x0 + 62, 2 + HDR + 14), f"{sg[1]}", font=FONT,
                       fill=(255, 184, 108))
                d.text((x0, 20 + HDR + 14), sg[2][:44], font=FONT_XS,
                       fill=(200, 200, 210))
            # bars
            d.text((x0, 36 + HDR + 14), "HP", font=FONT_XS, fill=(120, 120, 140))
            frac = hp[0] / max(1, hp[1])
            hbar(d, x0 + 24, 37 + HDR + 14, 200, 8, frac,
                 (80, 250, 123) if frac > 0.5 else
                 (255, 184, 108) if frac > 0.25 else (255, 85, 85))
            d.text((x0 + 230, 34 + HDR + 14), f"{hp[0]}/{hp[1]}", font=FONT_XS,
                   fill=(200, 200, 210))
            d.text((x0, 50 + HDR + 14), "HUN", font=FONT_XS, fill=(120, 120, 140))
            hbar(d, x0 + 24, 51 + HDR + 14, 200, 8, 1.0 - hun / 6.0,
                 (139, 233, 253) if hun < 2 else
                 (255, 184, 108) if hun < 3 else (255, 85, 85))
            # belief mini-map
            bel = bel_by_step.get(step)
            my0 = 68 + HDR
            d.text((x0, my0 - 2), "BELIEF MAP  (plan in yellow, "
                   "suspects red)", font=FONT_XS, fill=(120, 120, 140))
            if bel:
                rows, sus = bel[1], {tuple(s) for s in bel[2]}
                for yy, rowstr in enumerate(rows):
                    for xx, ch in enumerate(rowstr):
                        if ch == ".":
                            col = T_COLORS[0]
                        else:
                            col = T_COLORS.get(ord(ch) - 65, (90, 90, 100))
                        if (xx, yy) in sus:
                            col = (200, 60, 60)
                        d.rectangle(
                            [x0 + xx * MCW, my0 + 12 + yy * MCH,
                             x0 + xx * MCW + MCW - 1,
                             my0 + 12 + yy * MCH + MCH - 1], fill=col)
                if pl and pl[1]:
                    for (px, py) in pl[1]:
                        d.rectangle(
                            [x0 + px * MCW + 1, my0 + 12 + py * MCH + 1,
                             x0 + px * MCW + MCW - 2,
                             my0 + 12 + py * MCH + MCH - 2],
                            fill=(241, 250, 140))
                if mon:
                    for (mx, my_, name, pet) in mon[1]:
                        d.rectangle(
                            [x0 + mx * MCW, my0 + 12 + my_ * MCH,
                             x0 + mx * MCW + MCW - 1,
                             my0 + 12 + my_ * MCH + MCH - 1],
                            fill=(80, 250, 123) if pet else (255, 60, 60))
                # agent
                d.rectangle([x0 + pos[0] * MCW - 1,
                             my0 + 12 + pos[1] * MCH - 1,
                             x0 + pos[0] * MCW + MCW,
                             my0 + 12 + pos[1] * MCH + MCH],
                            outline=(255, 221, 51), width=1)
            # knowledge/decision ticker: recent provenance-coded events
            ey = my0 + 12 + MAPR * MCH + 8
            d.text((x0, ey), "KNOWLEDGE / DECISIONS", font=FONT_XS,
                   fill=(120, 120, 140))
            recent = [e for e in kevents
                      if 0 <= step - e[0] <= 8 * stride][-3:]
            yy2 = ey + 12
            for (ks, kc, ktxt) in recent:
                d.text((x0, yy2), f"[{ks}] {ktxt[:48]}", font=FONT_XS,
                       fill=KCOLORS[kc])
                yy2 += 12
            # model ticker: predicted vs realized damage when adjacent
            pj = latest(pred, step)
            if pj and step - pj[0] <= 3 * stride:
                real = 0
                jj = min(pj[0], len(t["hp"]) - 1)
                if jj > 0:
                    real = max(0, t["hp"][jj - 1][0] - t["hp"][jj][0])
                d.text((x0, yy2),
                       f"MODEL: E[dmg/turn] {pj[1]:.1f} | last hit {real}",
                       font=FONT_XS, fill=(189, 147, 249))
        else:
            if sg:
                d.text((8 + 60 * CW, 2), f"[{sg[1]}]", font=FONT,
                       fill=(255, 184, 108))

        imgs.append(img)
    durs = [90] * len(imgs)
    durs[-1] = 2500
    imgs[0].save(out_gif, save_all=True, append_images=imgs[1:],
                 duration=durs, loop=0, optimize=True)
    print(f"wrote {out_gif} ({len(imgs)} frames from {n} captured)")


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")

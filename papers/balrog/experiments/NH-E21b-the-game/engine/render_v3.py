"""CANONICAL UNIFIED RENDERER v3 — the program's visual signature.

MODEL: claude-opus-4-8[1m] (max thinking), Phase L session 4. Operator
directive 2026-07-07 (via coordinator, twice-refined to ONE composed frame).

ONE vertical-stacked frame, read top -> bottom:
  1. TOP  — THE MAP: grid/dungeon view + goal marker (ring on the gate),
            threat tints on hazards, agent + entities, MOTION TRAIL on the
            mover (fading dots = where it has been -> "movement is real,
            sleeping things are inert").
  2. MID  — THIN STATUS STRIP: hp/hunger, depth/step, current subgoal.
  3. BOT  — THE INTUITION TEXT: the consult panel as running text beneath
            the map — tagged bullets (GOAL/SAW/RECALL/PLAN/OVERRIDE...),
            override justifications in amber. "See the plan on the map,
            read the mind below it."

Supersedes render_live_v2 (side-by-side) as the single standard for reels —
NetHack episodes and composition worlds alike. This module implements the
E21b (composition-world) path; the NetHack path reuses the same frame stack
(map band fed by the belief/plan trajectory, A* route overlay from
render_c2's route logic) — wired when NetHack reels are next rendered.

Carry-forward asks (operator, staged — NOT all live here):
  - motion trails on movers ....... LIVE (agent trail; per-entity next).
  - A* route overlay (solid->fade) . E21b has no logged A* path; the trail
                                     stands in. NetHack path carries the
                                     real route from render_c2. [next]
  - playout preview panel (SIM EVs)  [next]
  - Pareto-frontier mini-plot ...... [next]
  - firsts/trophy HUD counter ...... [next]

Usage: python3 render_v3.py <live_json> <panel_json> <out_gif> [title]
"""

import collections
import json
import os
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from game import Game  # noqa: E402

FONT_PATH = ("/data/doh/teams/researchy/work/fable_nethack/balrog/"
             "environments/nle/Hack-Regular.ttf")
F_GRID = ImageFont.truetype(FONT_PATH, 24)
F_HDR = ImageFont.truetype(FONT_PATH, 17)
F_TAG = ImageFont.truetype(FONT_PATH, 15)
F_TXT = ImageFont.truetype(FONT_PATH, 15)
F_SM = ImageFont.truetype(FONT_PATH, 13)

CELL = 28
LINE_H = 24
MIN_W = 760                 # keep the text band legible / not cramped
HEADER_H = 34               # dedicated top header strip (step/depth/hp) —
GAP = 12                    # clearance between EVERY band; no band touches
                            # another (operator clearance principle, s4)
BG = (10, 10, 18)
HEADER_BG = (30, 30, 48)
STRIP_BG = (26, 26, 40)
TEXT_BG = (24, 22, 38)
TEXT_BG_OV = (46, 30, 10)   # amber wash when an override is on screen
TAG_COLOR = {
    "GOAL": (255, 221, 51), "SAW": (139, 233, 253),
    "THINK": (189, 147, 249), "RECALL": (255, 121, 198),
    "READ": (255, 121, 198), "PLAN": (80, 250, 123),
    "OVERRIDE": (255, 140, 60), "NOTE": (160, 160, 170),
    "REJECTED": (110, 110, 120), "CONFIRMED": (120, 255, 120),
    "COST": (230, 180, 100),
}
GRID_PAL = {"@": (255, 221, 51), "#": (115, 115, 135), ".": (80, 80, 95),
            "+": (255, 184, 108), ">": (80, 250, 123),
            "^": (255, 121, 198)}
ITEM = (189, 147, 249)
TRAIL = (255, 221, 51)      # agent trail base (fades with age)


def _agent_pos(grid):
    for r, line in enumerate(grid):
        c = line.find("@")
        if c >= 0:
            return (r, c)
    return None


def _goal_cells(grid):
    out = []
    for r, line in enumerate(grid):
        for c, ch in enumerate(line):
            if ch == ">":            # the gate / exit = the goal marker
                out.append((r, c))
    return out


def frame(grid, header, topline, status, subgoal, panel, H, gw, trail):
    map_w = gw * CELL + 24
    W = max(map_w, MIN_W)
    # band layout (top->bottom), each in its own strip with padding, no overlap
    y0 = HEADER_H + GAP                    # map starts BELOW the header strip
    map_h = y0 + H * CELL
    strip_y = map_h + GAP
    strip_h = 30
    text_y = strip_y + strip_h + GAP
    # ---- measure text band height (graceful, no font shrink)
    n_lines = 2
    if panel:
        for tag, txt in panel["bullets"]:
            n_lines += max(1, len(textwrap.wrap(txt, 64)))
    text_h = 30 + n_lines * LINE_H
    img_h = text_y + text_h + 12
    img = Image.new("RGB", (W, img_h), BG)
    d = ImageDraw.Draw(img)

    # ===== BAND 0: HEADER STRIP (title + step/depth/hp) — never overlaps map =
    d.rectangle([(0, 0), (W, HEADER_H)], fill=HEADER_BG)
    d.text((12, 8), header[:52], font=F_HDR, fill=(255, 221, 51))
    d.text((W - 12 - d.textlength(topline[:40], font=F_SM), 10),
           topline[:40], font=F_SM, fill=(235, 235, 235))

    # ===== BAND 1: MAP =====
    ox = 12 + max(0, (W - map_w) // 2)     # center narrow maps
    # goal marker: ring on the gate
    for (gr, gc) in _goal_cells(grid):
        x, y = ox + gc * CELL, y0 + gr * CELL
        d.rectangle([(x - 2, y - 2), (x + CELL - 6, y + CELL - 4)],
                    outline=(80, 250, 123), width=2)
    # motion trail: fading dots where the agent has been (oldest dimmest)
    n = len(trail)
    for i, (tr, tc) in enumerate(trail):
        f = (i + 1) / max(1, n)            # 0..1 newest brightest
        col = tuple(int(30 + (v - 30) * f) for v in TRAIL)
        cx, cy = ox + tc * CELL + CELL // 2, y0 + tr * CELL + CELL // 2
        rad = 2 + int(3 * f)
        d.ellipse([(cx - rad, cy - rad), (cx + rad, cy + rad)], fill=col)
    # glyphs
    for r, line in enumerate(grid):
        for c, ch in enumerate(line):
            if ch == " ":
                continue
            col = GRID_PAL.get(ch, ITEM if ch.isdigit() else
                               (139, 233, 253) if ch.isalpha() and ch != "@"
                               else (220, 220, 220))
            if ch == "^":                  # threat tint under hazard glyph
                x, y = ox + c * CELL, y0 + r * CELL
                d.rectangle([(x, y), (x + CELL - 4, y + CELL - 2)],
                            fill=(60, 20, 40))
            d.text((ox + c * CELL, y0 + r * CELL), ch, font=F_GRID, fill=col)

    # ===== BAND 2: STATUS STRIP =====
    d.rectangle([(0, strip_y), (W, strip_y + strip_h)], fill=STRIP_BG)
    d.text((12, strip_y + 8), status, font=F_SM, fill=(235, 235, 235))
    if subgoal:
        sg = f"SUBGOAL: {subgoal}"
        d.text((W - 12 - d.textlength(sg[:52], font=F_SM), strip_y + 8),
               sg[:52], font=F_SM, fill=(255, 221, 51))

    # ===== BAND 3: INTUITION TEXT =====
    has_ov = panel and any(t == "OVERRIDE" for t, _ in panel["bullets"])
    d.rectangle([(0, text_y), (W, img_h)],
                fill=TEXT_BG_OV if has_ov else TEXT_BG)
    if panel:
        badge = (f"CONSULT {panel['consult']}/{panel['total']} "
                 f"@ step {panel['at_step']}")
        d.rectangle([(10, text_y + 6), (10 + 300, text_y + 28)],
                    fill=(255, 140, 60) if has_ov else (90, 80, 160))
        d.text((18, text_y + 9), badge, font=F_TAG, fill=(10, 10, 18))
        py = text_y + 42            # label-clearance rule: gap below the badge
        for tag, txt in panel["bullets"]:
            col = TAG_COLOR.get(tag, (220, 220, 220))
            d.text((14, py), "■", font=F_TAG, fill=col)
            d.text((34, py), tag, font=F_TAG, fill=col)
            for j, ln in enumerate(textwrap.wrap(txt, 64) or [""]):
                d.text((150, py + j * LINE_H), ln, font=F_TXT,
                       fill=(245, 245, 245))
            py += LINE_H * max(1, len(textwrap.wrap(txt, 64)))
    else:
        d.text((16, text_y + 12), "(no consult yet)", font=F_SM,
               fill=(120, 120, 130))
    return img


def render(live_json, panel_json, out_gif, title=""):
    rec = json.load(open(live_json))
    pdoc = json.load(open(panel_json))
    total = pdoc["total_consults"]
    by_step = {}
    for p in pdoc["panels"]:
        p = dict(p, total=total)
        by_step.setdefault(p["at_step"], []).append(p)
    g = Game()
    obs = g.reset(rec["template"], rec["seed"])
    H = len(obs["grid"])
    gw = max(len(r) for r in obs["grid"])
    title = title or f"NH-E21b {rec['template']} s{rec['seed']}  (v3)"
    frames, durs = [], []
    panel = None
    trail = collections.deque(maxlen=9)
    ap = _agent_pos(obs["grid"])
    if ap:
        trail.append(ap)

    def subgoal_of(p):
        if not p:
            return ""
        for tag, txt in p["bullets"]:
            if tag in ("GOAL", "PLAN"):
                return txt
        return ""

    def emit(step, action, msgs, hold=False, win=False):
        st = obs["state"]
        inv = ",".join(i.get("letter", "?") if isinstance(i, dict) else i
                       for i in st["inventory"]) or "-"
        depth = st.get("depth", st.get("zone", ""))
        topline = (f"step {step:3d}   hp {st['hp']}"
                   + (f"   D{depth}" if depth != "" else "")
                   + ("   *** WIN ***" if win else ""))
        status = f"inv[{inv}]   last: {action}"
        frames.append(frame(obs["grid"], title, topline, status,
                            subgoal_of(panel), panel, H, gw, list(trail)))
        durs.append(3600 if hold else (4200 if win else 460))

    for step in range(len(rec["actions"]) + 1):
        if step in by_step:
            for p in by_step[step]:
                panel = p
                emit(step, "(consulting)", obs.get("messages", []), hold=True)
        if step < len(rec["actions"]):
            action = rec["actions"][step]
            obs, done, info = g.step(action)
            ap = _agent_pos(obs["grid"])
            if ap:
                trail.append(ap)
            emit(step + 1, action, obs["messages"],
                 win=(step == len(rec["actions"]) - 1 and info.get("win")))
    frames[0].save(out_gif, save_all=True, append_images=frames[1:],
                   duration=durs, loop=0, optimize=True)
    print(f"{out_gif}: {len(frames)} frames, "
          f"{os.path.getsize(out_gif) // 1024} KB")


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], sys.argv[3],
           sys.argv[4] if len(sys.argv) > 4 else "")

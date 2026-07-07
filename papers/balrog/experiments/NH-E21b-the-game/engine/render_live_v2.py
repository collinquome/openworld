"""Render NH-E21b live episodes with a STRUCTURED CONSULT SIDE PANEL.

MODEL: Fable 5 (max reasoning), Phase L session 3.

v2 per operator display directive (s3): consultations render in a FIXED
side panel right of the grid — bulleted short lines (<=6 words), tagged
(GOAL/SAW/THINK/RECALL/PLAN/OVERRIDE/...), consult-number badge, high
contrast, persists until the next consultation. "Read the mind, don't
decode it." Bullets come from a *_panel.json sidecar (distilled from the
verbatim consult log, which stays ground truth in the run JSON); this
layout is the STANDARD for all future reels.

Usage: python3 render_live_v2.py <live_json> <panel_json> <out_gif> [title]
"""

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
F_HDR = ImageFont.truetype(FONT_PATH, 16)
F_TAG = ImageFont.truetype(FONT_PATH, 15)
F_TXT = ImageFont.truetype(FONT_PATH, 15)
F_SM = ImageFont.truetype(FONT_PATH, 13)

CELL = 28
PANEL_W = 410
LINE_H = 26
BG = (10, 10, 18)
PANEL_BG = (24, 22, 38)
PANEL_BG_OV = (46, 30, 10)

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


def frame(grid, header, status, msgs, panel, H, gw):
    grid_w = gw * CELL + 24
    img_w = grid_w + PANEL_W + 12
    img_h = max(34 + H * CELL + 60, 34 + 13 * LINE_H + 20)
    img = Image.new("RGB", (img_w, img_h), BG)
    d = ImageDraw.Draw(img)
    d.text((10, 7), header[:64], font=F_HDR, fill=(255, 221, 51))
    y0 = 34
    for r, line in enumerate(grid):
        for c, ch in enumerate(line):
            if ch == " ":
                continue
            col = GRID_PAL.get(ch, ITEM if ch.isdigit() else
                               (139, 233, 253) if ch.isalpha() and ch != "@"
                               else (220, 220, 220))
            d.text((12 + c * CELL, y0 + r * CELL), ch, font=F_GRID,
                   fill=col)
    y = y0 + H * CELL + 8
    d.text((10, y), status, font=F_SM, fill=(225, 225, 225))
    d.text((10, y + 18), " | ".join(msgs)[:76], font=F_SM,
           fill=(139, 233, 253))
    # ---- side panel
    px = grid_w
    has_ov = panel and any(t == "OVERRIDE" for t, _ in panel["bullets"])
    d.rectangle([(px, 0), (img_w, img_h)],
                fill=PANEL_BG_OV if has_ov else PANEL_BG)
    if panel:
        badge = (f"CONSULT {panel['consult']}/{panel['total']} "
                 f"@ step {panel['at_step']}")
        d.rectangle([(px + 8, 8), (img_w - 8, 34)],
                    fill=(255, 140, 60) if has_ov else (90, 80, 160))
        d.text((px + 16, 12), badge, font=F_TAG, fill=(10, 10, 18))
        py = 46
        for tag, txt in panel["bullets"]:
            col = TAG_COLOR.get(tag, (220, 220, 220))
            d.text((px + 12, py), "■", font=F_TAG, fill=col)
            d.text((px + 30, py), tag, font=F_TAG, fill=col)
            lines = textwrap.wrap(txt, 30) or [""]
            ty = py
            for ln in lines:
                d.text((px + 120, ty), ln, font=F_TXT,
                       fill=(240, 240, 240))
                ty += LINE_H - 6
            py = max(py + LINE_H, ty + 6)
    else:
        d.text((px + 16, 14), "(no consult yet)", font=F_SM,
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
    title = title or f"NH-E21b {rec['template']} s{rec['seed']}"
    frames, durs = [], []
    panel = None

    def emit(step, action, msgs, hold=False, win=False):
        st = obs["state"]
        inv = ",".join(i.get("letter", "?") if isinstance(i, dict) else i
                       for i in st["inventory"]) or "-"
        status = (f"step {step:3d}  hp {st['hp']}  inv[{inv}]  "
                  f"last: {action}") + ("   *** WIN ***" if win else "")
        frames.append(frame(obs["grid"], title, status, msgs, panel,
                            H, gw))
        durs.append(3600 if hold else (4000 if win else 450))

    for step in range(len(rec["actions"]) + 1):
        if step in by_step:
            for p in by_step[step]:
                panel = p
                emit(step, "(consulting)", obs.get("messages", []),
                     hold=True)
        if step < len(rec["actions"]):
            action = rec["actions"][step]
            obs, done, info = g.step(action)
            emit(step + 1, action, obs["messages"],
                 win=(step == len(rec["actions"]) - 1 and info.get("win")))
    frames[0].save(out_gif, save_all=True, append_images=frames[1:],
                   duration=durs, loop=0, optimize=True)
    print(f"{out_gif}: {len(frames)} frames, "
          f"{os.path.getsize(out_gif) // 1024} KB")


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], sys.argv[3],
           sys.argv[4] if len(sys.argv) > 4 else "")

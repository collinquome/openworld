"""Render NH-E21b live-arm episodes (results/e21b_live/*.json) as GIFs.

MODEL: Fable 5 (max reasoning), Phase L session 3.

Deterministic replay of the recorded action list through game.Game,
one frame per step; INTUITION consultations are shown VERBATIM as a
word-wrapped banner (this is the reel item: the model's felt-sense
reads next to the world they were about). Consult frames hold ~6s,
normal frames 450ms, final frame 4s.

Usage:
    python3 render_live.py <live_json> <out_gif> [title]
"""

import json
import os
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from game import Game  # noqa: E402

FONT_PATH = "/data/doh/teams/researchy/work/fable_nethack/balrog/environments/nle/Hack-Regular.ttf"
FONT_BIG = ImageFont.truetype(FONT_PATH, 22)     # grid glyphs
FONT_HDR = ImageFont.truetype(FONT_PATH, 15)
FONT_TXT = ImageFont.truetype(FONT_PATH, 13)

CELL = 26            # grid cell px
WRAP = 96            # banner wrap width (chars)
BANNER_LINES = 12    # reserved banner height (longest consult ~671 chars + tag)

PALETTE = {
    "@": (255, 221, 51),   # agent
    "#": (110, 110, 130),  # wall
    ".": (75, 75, 90),     # floor
    "+": (255, 184, 108),  # gate/door
    ">": (80, 250, 123),   # goal
    "^": (255, 121, 198),  # hazard
}
ITEM = (189, 147, 249)
INTER = (139, 233, 253)
MSG = (139, 233, 253)
CONSULT = (255, 200, 255)
OVERRIDE = (255, 240, 150)
DEFAULT = (220, 220, 220)


def frame_image(grid, header, status, msgs, banner, W, H, override=False):
    gw = max(len(r) for r in grid)
    img_w = max(gw * CELL + 24, WRAP * 8 + 24)
    img_h = 48 + H * CELL + 44 + BANNER_LINES * 17 + 12
    img = Image.new("RGB", (img_w, img_h), (12, 12, 20))
    d = ImageDraw.Draw(img)
    hl = textwrap.wrap(header, max(40, (img_w - 20) // 8))
    for i, h in enumerate(hl[:2]):
        d.text((10, 6 + i * 18), h, font=FONT_HDR, fill=(255, 221, 51))
    y0 = 30 + (len(hl[:2]) - 1) * 18
    for r, line in enumerate(grid):
        for c, ch in enumerate(line):
            if ch == " ":
                continue
            color = PALETTE.get(ch)
            if color is None:
                color = ITEM if ch.isdigit() else (
                    INTER if ch.isalpha() and ch != "@" else DEFAULT)
            d.text((12 + c * CELL, y0 + r * CELL), ch, font=FONT_BIG,
                   fill=color)
    y = y0 + H * CELL + 6
    d.text((10, y), status, font=FONT_TXT, fill=(220, 220, 220))
    y += 18
    d.text((10, y), " | ".join(msgs)[:140], font=FONT_TXT, fill=MSG)
    y += 20
    if banner:
        bg = (70, 45, 12) if override else (50, 18, 50)
        fg = OVERRIDE if override else CONSULT
        d.rectangle([(6, y), (img_w - 6, y + BANNER_LINES * 17 + 4)],
                    fill=bg)
        if override:
            d.text((12, y + 3), ">>> OVERRIDE MOMENT <<<", font=FONT_TXT,
                   fill=(255, 130, 80))
        for i, ln in enumerate(banner[:BANNER_LINES]):
            d.text((12, y + 3 + (i + (1 if override else 0)) * 17), ln,
                   font=FONT_TXT, fill=fg)
    return img


def render(live_json, out_gif, title=""):
    rec = json.load(open(live_json))
    tid, seed = rec["template"], rec["seed"]
    consults = {}
    for c in rec["consultations"]:
        s = c["at_step"]
        consults[s] = (consults.get(s, "") + " || " + c["text"]).lstrip(" |")
    g = Game()
    obs = g.reset(tid, seed)
    H = len(obs["grid"])
    frames, durs = [], []
    banner = None
    override = False
    title = title or f"NH-E21b {tid} s{seed} LIVE intuition arm"
    hdr_base = (f"{title} | MODEL: claude-fable-5 (max) | "
                f"{len(rec['actions'])} steps / {len(rec['consultations'])} consults")

    def emit(step, obs, msgs, action, hold=False, win=False):
        st = obs["state"]
        inv = ",".join(
            i if isinstance(i, str) else
            f"{i.get('letter','?')}:{i.get('display_name','?')}"
            for i in st["inventory"]) or "-"
        status = (f"step {step:3d}  hp {st['hp']}  zone {st['zone']}  "
                  f"inv[{inv}]  last: {action}")
        if win:
            status += "   *** WIN ***"
        frames.append(frame_image(obs["grid"], hdr_base, status, msgs,
                                  banner, None, H, override=override))
        durs.append(6000 if hold else (4000 if win else 450))

    for step in range(len(rec["actions"]) + 1):
        new_consult = step in consults
        if new_consult:
            txt = consults[step]
            override = ("override" in txt.lower())
            banner = textwrap.wrap(f"@step {step}: {txt}", WRAP)
        if step < len(rec["actions"]):
            if new_consult:  # show the consult on the pre-action state
                emit(step, obs, obs.get("messages", []), "(consulting)",
                     hold=True)
            action = rec["actions"][step]
            obs, done, info = g.step(action)
            emit(step + 1, obs, obs["messages"], action,
                 win=(step == len(rec["actions"]) - 1 and info.get("win")))
        else:
            if new_consult:
                emit(step, obs, obs.get("messages", []), "(consulting)",
                     hold=True)
    frames[0].save(out_gif, save_all=True, append_images=frames[1:],
                   duration=durs, loop=0, optimize=True)
    print(f"{out_gif}: {len(frames)} frames, "
          f"{os.path.getsize(out_gif) // 1024} KB")


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2],
           sys.argv[3] if len(sys.argv) > 3 else "")

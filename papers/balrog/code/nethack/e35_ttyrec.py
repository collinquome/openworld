"""NH-E35a — ttyrec emulator + blstats parser for EXPERT (alt.org) human play.

MODEL: claude-opus-4-8 (max thinking), Phase L session 9.

WHY a hand-rolled emulator: NLE's C `Converter` (_pyconverter) emits ZERO frames
for alt.org dgamelaunch human ttyrecs (it is keyed to NLE-injected frame markers
that public human recordings lack — verified: remaining==SEQ, chars.sum()==0
across all terminal dims/versions). alt.org V1 ttyrecs are plain terminal
recordings, so we render them ourselves.

We only need what the possibility-set world-model checks consume:
  - the two STATUS lines (bottom of screen) -> hp/hpmax, Dlvl (depth), T (time),
    Xp (xp level), condition words (Conf/Stun for V_MOVE scoping)
  - the CURSOR position -> hero (x,y) when the cursor rests on the map
  - the MESSAGE line (top) -> teleport / drain-life novelty scoping
so a focused ANSI emulator (clear / cursor-position / erase-line / CR/LF/BS +
printable writes) is sufficient; perfect map glyph rendering is NOT required.

provenance: DEMONSTRATION (public alt.org human ttyrecs, used OFFLINE for
world-model validation — like reading the wiki/source, disclosed). insight-origin
OP (operator 2026-07-07 s5 NH-E35 design). replication recipe: see e35_validate.py
docstring.
"""

import re
import struct

ROWS, COLS = 24, 80


class Term:
    """Minimal ANSI/VT100 terminal enough for NetHack status + cursor."""

    def __init__(self, rows=ROWS, cols=COLS):
        self.rows, self.cols = rows, cols
        self.grid = [[" "] * cols for _ in range(rows)]
        self.cr = 0  # cursor row (0-indexed)
        self.cc = 0  # cursor col

    def _clear(self):
        for r in range(self.rows):
            for c in range(self.cols):
                self.grid[r][c] = " "

    def _erase_line(self, mode):
        r = self.cr
        if mode == 0:      # to EOL
            for c in range(self.cc, self.cols):
                self.grid[r][c] = " "
        elif mode == 1:    # from BOL
            for c in range(0, self.cc + 1):
                self.grid[r][c] = " "
        elif mode == 2:    # whole line
            for c in range(self.cols):
                self.grid[r][c] = " "

    def _erase_disp(self, mode):
        if mode == 2:
            self._clear()
        elif mode == 0:    # cursor to end
            self._erase_line(0)
            for r in range(self.cr + 1, self.rows):
                self.grid[r] = [" "] * self.cols
        elif mode == 1:    # start to cursor
            self._erase_line(1)
            for r in range(0, self.cr):
                self.grid[r] = [" "] * self.cols

    def _putc(self, ch):
        if self.cc >= self.cols:
            self.cc = self.cols - 1
        self.grid[self.cr][self.cc] = ch
        self.cc += 1

    def feed(self, data):
        """Feed a chunk of terminal bytes (bytes)."""
        i, n = 0, len(data)
        while i < n:
            b = data[i]
            if b == 0x1b:  # ESC
                i = self._esc(data, i)
                continue
            c = chr(b)
            if b == 0x0d:      # CR
                self.cc = 0
            elif b == 0x0a:    # LF
                self.cr += 1
                if self.cr >= self.rows:
                    # scroll up
                    self.grid.pop(0)
                    self.grid.append([" "] * self.cols)
                    self.cr = self.rows - 1
            elif b == 0x08:    # BS
                if self.cc > 0:
                    self.cc -= 1
            elif b == 0x09:    # TAB
                self.cc = min(self.cols - 1, (self.cc // 8 + 1) * 8)
            elif b in (0x0e, 0x0f, 0x07):  # SI/SO/BEL: ignore (charset/bell)
                pass
            elif b >= 0x20 and b < 0x7f:
                self._putc(c)
            elif b >= 0x80:    # high-bit (IBM/latin graphics) -> placeholder
                self._putc("?")
            i += 1

    def _esc(self, data, i):
        n = len(data)
        if i + 1 >= n:
            return n
        nxt = data[i + 1]
        if nxt == 0x5b:  # '[' CSI
            j = i + 2
            while j < n and not (0x40 <= data[j] <= 0x7e):
                j += 1
            if j >= n:
                return n
            final = data[j]
            params = data[i + 2:j].decode("latin-1", "ignore")
            self._csi(final, params)
            return j + 1
        if nxt == 0x28 or nxt == 0x29:  # ESC( ESC) charset select: skip 1 more
            return i + 3
        if nxt == 0x4d:  # ESC M reverse index
            if self.cr > 0:
                self.cr -= 1
            return i + 2
        if nxt in (0x3d, 0x3e, 0x37, 0x38):  # ESC= ESC> ESC7 ESC8 (keypad/save)
            return i + 2
        # other 2-byte escapes: skip the intro byte
        return i + 2

    def _csi(self, final, params):
        def ints(default=0):
            out = []
            for p in params.split(";"):
                out.append(int(p) if p.isdigit() else default)
            return out or [default]

        f = chr(final)
        if f in ("H", "f"):        # cursor position (1-indexed)
            ps = params.split(";")
            r = int(ps[0]) if ps and ps[0].isdigit() else 1
            c = int(ps[1]) if len(ps) > 1 and ps[1].isdigit() else 1
            self.cr = max(0, min(self.rows - 1, r - 1))
            self.cc = max(0, min(self.cols - 1, c - 1))
        elif f == "A":
            self.cr = max(0, self.cr - (ints()[0] or 1))
        elif f == "B":
            self.cr = min(self.rows - 1, self.cr + (ints()[0] or 1))
        elif f == "C":
            self.cc = min(self.cols - 1, self.cc + (ints()[0] or 1))
        elif f == "D":
            self.cc = max(0, self.cc - (ints()[0] or 1))
        elif f == "G":
            self.cc = max(0, min(self.cols - 1, (ints()[0] or 1) - 1))
        elif f == "d":
            self.cr = max(0, min(self.rows - 1, (ints()[0] or 1) - 1))
        elif f == "J":
            self._erase_disp(ints()[0])
        elif f == "K":
            self._erase_line(ints()[0])
        # SGR ('m'), modes ('h'/'l'), etc.: ignored (color not needed)

    def line(self, r):
        return "".join(self.grid[r]).rstrip()


def iter_records(path):
    """Yield (timestamp_float, data_bytes) per ttyrec record."""
    with open(path, "rb") as fh:
        raw = fh.read()
    i, n = 0, len(raw)
    while i + 12 <= n:
        sec, usec, ln = struct.unpack("<III", raw[i:i + 12])
        i += 12
        if ln == 0 or i + ln > n:
            if i + ln > n:
                ln = n - i
        data = raw[i:i + ln]
        i += ln
        yield sec + usec / 1e6, data


# ---- status-line parsing -------------------------------------------------
_HP = re.compile(r"HP:(-?\d+)\((\d+)\)")
_DLVL = re.compile(r"Dlvl:(\d+)")
_T = re.compile(r"\bT:(\d+)")
_XP = re.compile(r"\b(?:Xp|Exp):(\d+)")
_COND = re.compile(r"\b(Conf|Stun|Hallu|Blind|FoodPois|Ill|Slime|Held|Strngl|Termil)\b")


def parse_status(term):
    """Return blstats-like dict from the two bottom status rows, or None if the
    status line is not currently a valid NetHack status (menus/prompts)."""
    s = term.line(term.rows - 1) + "  " + term.line(term.rows - 2)
    hp = _HP.search(s)
    t = _T.search(s)
    if not hp or not t:
        return None
    dl = _DLVL.search(s)
    xp = _XP.search(s)
    conds = set(_COND.findall(s))
    return {
        "hp": int(hp.group(1)),
        "hpmax": int(hp.group(2)),
        "depth": int(dl.group(1)) if dl else None,
        "time": int(t.group(1)),
        "xp": int(xp.group(1)) if xp else None,
        "conds": conds,
    }


def hero_pos(term):
    """Cursor as hero (x,y) when it rests on the map region (rows 1..rows-3).
    NLE convention: x=col (0..cols-1), y=row-1 (map rows 1..21 -> y 0..20)."""
    r, c = term.cr, term.cc
    if 1 <= r <= term.rows - 3:
        return (c, r - 1)
    return None


def message(term):
    return term.line(0)

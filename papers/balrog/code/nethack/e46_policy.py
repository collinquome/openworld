#!/usr/bin/env python3
"""NH-E46 combat-BC inference: load e46_bc.pt and turn a live tty_chars frame
into an attack/move DIRECTION string, matching the extractor's features.
Returns one of n/e/s/w/ne/se/sw/nw (agent combat commands) or None (fall
through to the symbolic policy for non-directional/low-confidence predictions)."""
import os, re, numpy as np

W = 9; HALF = W // 2; AT = ord('@')
_MON = np.zeros(256, dtype=bool)
for _c in b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ&;:'":
    _MON[_c] = True
# NLE compass action id (0-7) -> agent direction command
_ID2DIR = {0: "north", 1: "east", 2: "south", 3: "west",
           4: "northeast", 5: "southeast", 6: "southwest", 7: "northwest"}
_PT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'e46_bc.pt')

_M = None  # lazy singleton (model, char2idx, lab2act, cfg)

def _load():
    global _M
    if _M is not None:
        return _M
    import torch, torch.nn as nn
    ck = torch.load(_PT, map_location='cpu', weights_only=False)
    V, C, w, hmax = ck['V'], ck['C'], ck['W'], ck['hmax']

    class BC(nn.Module):
        def __init__(self):
            super().__init__()
            self.emb = nn.Embedding(V, 24); self.hemb = nn.Embedding(hmax + 1, 8)
            self.net = nn.Sequential(nn.Linear(24 * w * w + 8, 256), nn.ReLU(),
                                     nn.Linear(256, 256), nn.ReLU(), nn.Linear(256, C))
        def forward(self, s, h):
            return self.net(torch.cat([self.emb(s).flatten(1), self.hemb(h)], 1))
    m = BC(); m.load_state_dict(ck['state_dict']); m.eval()
    _M = (m, ck['char2idx'], ck['lab2act'], w, hmax, torch)
    return _M

def _hp_bucket(tty):
    txt = bytes(tty[22].tolist()).decode('latin1') + ' ' + bytes(tty[23].tolist()).decode('latin1')
    mt = re.search(r'HP:?\s*(\d+)\((\d+)\)', txt)
    return min(4, int(int(mt.group(1)) / max(1, int(mt.group(2))) * 5)) if mt else 2

def combat_direction(tty, conf=0.0):
    """tty: (24,80) uint8 array. Returns dir string or None."""
    try:
        m, char2idx, lab2act, w, hmax, torch = _load()
    except Exception:
        return None
    mapz = tty[1:22, :]
    ys, xs = np.where(mapz == AT)
    if len(ys) == 0:
        return None
    y = ys[0] + 1; x = xs[0]
    y0, y1 = max(0, y - 1), min(24, y + 2); x0, x1 = max(0, x - 1), min(80, x + 2)
    if not _MON[tty[y0:y1, x0:x1]].any():
        return None
    win = np.full((w, w), ord(' '), dtype=np.int64)
    for iy in range(w):
        fy = y - HALF + iy
        if 0 <= fy < 24:
            for ix in range(w):
                fx = x - HALF + ix
                if 0 <= fx < 80:
                    win[iy, ix] = tty[fy, fx]
    unk = len(char2idx)
    idx = np.array([[char2idx.get(int(c), unk % max(1, len(char2idx))) for c in win.ravel()]])
    idx = np.clip(idx, 0, len(char2idx) - 1)
    s = torch.tensor(idx); h = torch.tensor([_hp_bucket(tty)])
    with torch.no_grad():
        logits = m(s, h)[0]
        p = torch.softmax(logits, 0)
        lab = int(p.argmax()); pc = float(p[lab])
    if pc < conf:
        return None
    nle_id = lab2act[lab]
    _dd=_ID2DIR.get(nle_id)
    if _dd:
        try:
            import os as _o; open(_o.path.join(_o.path.dirname(__file__),'e46_fire.cnt'),'a').write('1')
        except Exception: pass
    return _dd   # None unless a compass direction

if __name__ == '__main__':
    # smoke test: a fake frame with @ and adjacent 'd'
    t = np.full((24, 80), ord(' '), dtype=np.uint8)
    t[10, 40] = AT; t[10, 41] = ord('d')
    t[22] = np.frombuffer(b"HP:12(18)".ljust(80), dtype=np.uint8)
    print('smoke combat_direction ->', combat_direction(t))

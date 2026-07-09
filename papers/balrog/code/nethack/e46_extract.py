#!/usr/bin/env python3
"""NH-E46 combat-BC: extract (combat_local_state, action) pairs from AutoAscend
tty_chars. COMBAT step = the player '@' has >=1 adjacent monster glyph.
State = flattened WxW ASCII window centered on '@'  + hp-fraction bucket.
Action = AutoAscend NLE action id. Output: e46_combat.npz. Vectorized + capped."""
import h5py, numpy as np, re, os
from huggingface_hub import hf_hub_download

W = 9; HALF = W // 2; AT = ord('@'); CAP = 12
MON = np.zeros(256, dtype=bool)
for c in b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ&;:'":
    MON[c] = True
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'e46_combat.npz')

def hp_bucket(row22, row23):
    txt = bytes(row22.tolist()).decode('latin1') + ' ' + bytes(row23.tolist()).decode('latin1')
    m = re.search(r'HP:?\s*(\d+)\((\d+)\)', txt)
    if m:
        return min(4, int(int(m.group(1)) / max(1, int(m.group(2))) * 5))
    return 2

def save(S, H, A):
    np.savez_compressed(OUT, states=np.array(S, dtype=np.uint8),
                        hp=np.array(H, dtype=np.uint8), actions=np.array(A, dtype=np.int64))

def main():
    hp = hf_hub_download('Howuhh/nld-aa-taster', 'data/data-cav-gno-neu-any.hdf5', repo_type='dataset')
    S, H, A = [], [], []
    with h5py.File(hp, 'r') as f:
        keys = list(f.keys())[:CAP]
        for ki, k in enumerate(keys):
            tc = f[k]['tty_chars'][()]          # (T,24,80) into RAM at once
            ac = f[k]['actions'][()]
            T = tc.shape[0]
            mapz = tc[:, 1:22, :]               # map rows only
            # per-frame: first '@' in map (row-major)
            for i in range(T):
                fr = mapz[i]
                ys, xs = np.where(fr == AT)
                if len(ys) == 0:
                    continue
                y = ys[0] + 1; x = xs[0]        # +1: map offset back to full-frame row
                # 3x3 neighborhood in the full frame
                y0, y1 = max(0, y - 1), min(24, y + 2)
                x0, x1 = max(0, x - 1), min(80, x + 2)
                nb = tc[i, y0:y1, x0:x1]
                if not MON[nb].any():
                    continue
                # local WxW window (padded)
                win = np.full((W, W), ord(' '), dtype=np.uint8)
                wy0, wx0 = y - HALF, x - HALF
                for iy in range(W):
                    fy = wy0 + iy
                    if 0 <= fy < 24:
                        for ix in range(W):
                            fx = wx0 + ix
                            if 0 <= fx < 80:
                                win[iy, ix] = tc[i, fy, fx]
                S.append(win.ravel()); H.append(hp_bucket(tc[i, 22], tc[i, 23])); A.append(int(ac[i]))
            print(f'ep {ki+1}/{len(keys)} pairs={len(A)}', flush=True)
            if (ki + 1) % 3 == 0 and A:
                save(S, H, A); print(f'  [checkpoint {len(A)}]', flush=True)
    save(S, H, A)
    Aa = np.array(A); uniq, cnts = np.unique(Aa, return_counts=True)
    top = sorted(zip(cnts.tolist(), uniq.tolist()), reverse=True)[:10]
    print(f'DONE combat_pairs={len(A)} | distinct_actions={len(uniq)} | top(count,action)={top}')
    print(f'saved {OUT}')

if __name__ == '__main__':
    main()

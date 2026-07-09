#!/usr/bin/env python3
"""NH-E46 combat-BC STEP 2: train a small torch policy to predict AutoAscend's
combat action from the local 9x9 ASCII window + hp-bucket. CPU-only.
Saves e46_bc.pt (weights + char-vocab + action-label map + config)."""
import numpy as np, os, sys, json
import torch, torch.nn as nn

HERE = os.path.dirname(os.path.abspath(__file__))
NPZ = os.path.join(HERE, 'e46_combat.npz')
OUT = os.path.join(HERE, 'e46_bc.pt')
W = 9

def main():
    d = np.load(NPZ)
    S, H, A = d['states'].astype(np.int64), d['hp'].astype(np.int64), d['actions'].astype(np.int64)
    N = len(A)
    print(f'loaded {N} combat (state,action) pairs | window {S.shape[1]} hp-buckets {H.max()+1}')

    # compact char vocab (present bytes only) and action labels (present actions only)
    chars = np.unique(S); char2idx = {int(c): i for i, c in enumerate(chars)}
    Sidx = np.vectorize(char2idx.get)(S).astype(np.int64)
    acts = np.unique(A); act2lab = {int(a): i for i, a in enumerate(acts)}
    Y = np.vectorize(act2lab.get)(A).astype(np.int64)
    V, C = len(chars), len(acts)
    print(f'vocab={V} chars | classes={C} actions | majority-class baseline={np.bincount(Y).max()/N:.3f}')

    # 90/10 split (shuffled, seeded)
    rng = np.random.RandomState(0); perm = rng.permutation(N); cut = int(N * 0.9)
    tr, va = perm[:cut], perm[cut:]
    Xs = torch.tensor(Sidx); Xh = torch.tensor(H); Yt = torch.tensor(Y)

    class BC(nn.Module):
        def __init__(self):
            super().__init__()
            self.emb = nn.Embedding(V, 24)
            self.hemb = nn.Embedding(int(H.max()) + 1, 8)
            self.net = nn.Sequential(
                nn.Linear(24 * W * W + 8, 256), nn.ReLU(),
                nn.Linear(256, 256), nn.ReLU(),
                nn.Linear(256, C))
        def forward(self, s, h):
            e = self.emb(s).flatten(1)
            return self.net(torch.cat([e, self.hemb(h)], 1))

    model = BC(); opt = torch.optim.Adam(model.parameters(), 1e-3)
    lossf = nn.CrossEntropyLoss(); bs = 512
    best = 0.0
    for ep in range(8):
        model.train(); rng.shuffle(tr)
        for i in range(0, len(tr), bs):
            b = tr[i:i + bs]
            opt.zero_grad()
            out = model(Xs[b], Xh[b]); loss = lossf(out, Yt[b])
            loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            pv = model(Xs[va], Xh[va]).argmax(1)
            acc = (pv == Yt[va]).float().mean().item()
        print(f'epoch {ep+1}: val_acc={acc:.3f}', flush=True)
        best = max(best, acc)
    torch.save({'state_dict': model.state_dict(), 'char2idx': char2idx,
                'act2lab': act2lab, 'lab2act': {v: k for k, v in act2lab.items()},
                'V': V, 'C': C, 'W': W, 'hmax': int(H.max())}, OUT)
    print(f'saved {OUT} | best val_acc={best:.3f} vs majority {np.bincount(Y).max()/N:.3f}')
    print('=> if val_acc >> majority baseline, the local window PREDICTS expert combat actions (BC learnable)')

if __name__ == '__main__':
    main()

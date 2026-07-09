# OpenWorld × BALROG — Experiments & Results Wiki

> **Purpose:** one findable place for what we tried, what worked, the best result per world,
> and where the code/data live. Fighting exponentials with logs. **Update this when a result
> or experiment lands** — the per-world page first, then the table/highlights here.

## 🏆 Highlights
- **ARC-AGI-3 — first PERFECT result**, source-free: 25/25 games, 183/183 levels, beats prior SOTA. → [worlds/arc-agi-3](worlds/arc-agi-3.md)
- **MiniHack 92.5%** (best 95%) vs 40 SOTA → **+52.5pp, >2×.** → [worlds/minihack](worlds/minihack.md)
- **TextWorld 90% clean / 100% privileged** vs 75.7 → **+14.3pp.** → [worlds/textworld](worlds/textworld.md)
- **Baba 100%** · **BabyAI 100%** (saturated/matched). → [worlds/others](worlds/others.md)
- **Crafter 47.3%** & **NetHack 6.09** — the stochastic-survival wall (death-bound). → [worlds/crafter](worlds/crafter.md) · [worlds/nethack](worlds/nethack.md)

## Results table (clean / leaderboard-comparable; SOTA from leaderboard_parse.json 2026-07-06)
| World | Ours (best) | #1 SOTA | #2 prev | Δ vs #1 | Status | Headroom |
|---|---|---|---|---|---|---|
| ARC-AGI-3 | 25/25 perfect | prior | — | beat | ✅ done | saturated |
| BabyAI | 100.0 | 100.0 | 98.0 | tie | ✅ matched | saturated |
| Baba Is AI | 100.0 | 90.0 | 88.3 | +10 | ✅ beat | saturated |
| TextWorld | 90.0 (100 priv) | 75.7 | 66.5 | +14.3 | ✅ beat | clean→~100 via memory ledger (small) |
| MiniHack | 92.5 (95 best) | 40.0 | 35.0 | +52.5 | ✅ beat | ~95–97 (some episodes hard-unsolvable) |
| Crafter | 47.3 (48.6 mem) | 57.3 | 55.0 | −10 | ⚠ below | **BIG — survival/death is the constraint** |
| NetHack | 6.09 | 6.8 | 4.0 | −0.7 | ⚠ tied | needs non-heuristic lever (LLM-in-loop) |

## The pattern (the thesis)
**Deterministic / code-representable worlds → we dominate** (BabyAI, Baba, TextWorld, MiniHack): the
verified-world-model + classical-search recipe saturates them. **Stochastic / survival worlds → we
struggle** (Crafter, NetHack): randomness + combinatorial scope, and *death is the binding
constraint* — the planner is competent but keeps dying. Improving survival is THE open problem, and
Crafter is its tractable cousin (a win there should transfer to NetHack).

## Where things live
- **Reports (source of truth):** each world's `FABLE_*_REPORT.md` (full protocol, per-task tables,
  ablations, honest caveats). Backed up in `collinquome/openworld` branch `balrog-results`.
- **ARC-AGI-3:** `quome-cloud/openworld` (fork `collinquome/openworld`).
- **NetHack:** `nethack-experiments` repo (push pending token) + 3 GB corpus at `gs://researchy-nethack-results`.
- **Other worlds' code/data:** `work/fable_*` on the VM — full migration to collinquome is the open infra task.

## How to use / update
1. A result or experiment lands → edit that world's `worlds/<world>.md` (append to its Experiments log + update Best).
2. Update the Results table + Highlights here if the best changed.
3. Keep the report `FABLE_*_REPORT.md` as the detailed source of truth; this wiki is the map.

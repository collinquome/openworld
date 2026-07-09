# MiniHack — worlds wiki

**Best:** 92.5% (official block 1000 + untouched robustness block 2000; 37/40 eps; 6/8 tasks 100%). Best pass B1 95.0%.
**SOTA:** 40.0 (#1 Gemini-3-Pro) · 35.0 (#2). **We beat by +52.5pp (>2×).**
**Report:** `work/fable_minihack/FABLE_MINIHACK_REPORT.md` · **Code:** `work/fable_minihack/`.

## How (per-task solvers)
World-model synthesis + classical search: Boxoban = full Sokoban A* (push-macros, deadlock pruning,
0 mispredictions in 20/20 eps); MazeWalk = frontier explore + lattice-parity wall inference; Corridor
= search-for-hidden-passages; Quest = acquisition puzzle + scripted crossing. Every step verified
against the model's predicted state; misprediction → replan.

## Headroom (~95–97%, partly capped)
Remaining failures: (a) hidden-passage Corridor levels where the required # of `search` successes
doesn't fit in the 100-step cap; (b) ~1/13 random Quest roles are **mechanically unsolvable** — the
BALROG action alphabet can't select the quest wand (letters land on d/f/g/i...). (c) the frozen-step
scoring trap (fast roles score 0.99) — already mitigated by a win-step guard. Net: small real
headroom; a chunk is a hard cap, not a bug. Memory doesn't help (planner already solves on attempt 1).

## Experiments log
| pass | score | notes |
|---|---|---|
| run1 | 87.5% | exposed 2 bugs (quest-wand shadow, over-broad never-melee-F) |
| run2 = Cond A | 92.5% | bugs fixed on dev seeds first |
| robustness (2000) | 92.5% | guards vs tuning-to-eval-seeds |
| B1 (best) | 95.0% | |

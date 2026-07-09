# Crafter — worlds wiki  ⚠ ACTIVE: beat SOTA

**Best:** 47.3% (Condition A, memoryless, clean) · 48.6% (Condition B, cross-episode memory).
**SOTA:** 57.3 (#1 Grok-4 / Gemini-3-Pro tie) · 55.0 (#2). We are **~10pp below** — the only
tractable world we haven't beaten.
**Report:** `work/fable_crafter/FABLE_CRAFTER_REPORT.md` · **Code:** `work/fable_crafter/`.

## Why we're below (the diagnosis — this is the whole game)
**Death, not tech-tree competence, is the binding constraint: 10/10 episodes end in death** in both
conditions. The planner saturates the crafting/tech logic; it just doesn't survive long enough to
rack up more achievements. The memory condition (B) helps **variance not mean** (SE 5.3→3.0, worst
episode 13.6%→36.4%) — it removes the catastrophic tail but doesn't raise the ceiling.

**This is the tractable cousin of the NetHack survival wall.** A survival win here should transfer.

## Headroom & plan (open experiments)
The gap to SOTA is ~10pp and it's all survival. Candidate levers (survival-first, A/B each):
1. **Threat avoidance** — zombies/skeletons at night are the likely killers; retreat/avoid vs fight; don't sleep exposed.
2. **Health/food management** — keep food & health buffers above a threshold before pursuing achievements; drink/eat proactively.
3. **Night behavior** — build/shelter or hole up at night rather than roam (night = most deaths in Crafter).
4. **Combat only when favorable** — engage only with a weapon + health margin; flee otherwise.
5. **Memory of death causes** (extend Condition B) — remember what killed you last episode; pre-empt it.

## First steps (do this)
1. Read `FABLE_CRAFTER_REPORT.md` §6 (death analysis) — get the exact death causes / timing.
2. Instrument: log cause-of-death + step + health-trajectory per episode.
3. Add the highest-frequency-death counter as a survival lever; A/B vs Condition A on the same seeds.
4. Track here: experiment → Δ score → keep/kill. Target: cross 57.3.

## Experiments log
| # | Lever | Result | Notes |
|---|---|---|---|
| A | memoryless planner (baseline) | 47.3% | 10/10 die |
| B | + cross-episode memory | 48.6% | variance↓ not mean; tail removed |
| — | *(survival levers — TBD)* | — | this page's active work |

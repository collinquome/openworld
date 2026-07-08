# HANDOFF_11 — Phase L session 11 → session 12

MODEL: claude-opus-4-8 (max thinking) wrote this — session 11, the EIGHTH opus
session. Runtime identity VERIFIED at open (system-prompt id = claude-opus-4-8,
max thinking; Fable at usage cap). All s11 artifacts stamped claude-opus-4-8[max].
Fork aleph/fable-nethack.

## HEADLINE: FOOD-ACQUISITION (NH_FOODACQ) is the FIRST progression-safe lever to
## REMOVE a death class — hunger-death 5/15→0/15 — but it is NOT a mean-mover
## (it converts hunger-deaths into COMBAT-deaths at the same depth).
The s10 redirect ("it's food ACQUISITION not eat-timing") was built and validated.
The win is real, progression-safe, and honestly bounded: a death CLASS moved, the
MEAN did not. Combat is the newly-unmasked next constraint.

## What was built (all stamped opus-4.8[max], flat work/fable_nethack)
- **nh_agent.py** — flag C2_FOODACQ=_flag("NH_FOODACQ"); added to C2_ANY. New
  [FOODACQ] block in _decide (just before the s9 ANTI-FAINT guard): eat a safe
  fresh corpse UNDERFOOT (`_fresh_corpse_here`), gated hunger!=Satiated + no
  adjacent hostile, rate-limited by FOODACQ_COOLDOWN (default 8). Corpse-only.
  Flag-off bit-identical (C2_ANY False verified).
- **FOODACQ_COOLDOWN** const (env NH_FOODACQ_COOLDOWN, default 8) — the reconciled
  banking rate (see below).
- **e35_antifaint_smoke.py** — added foodacq_fires count + print col.
- **run_foodacq_block.sh (NEW)** — paired block runner, REF vs REF+NH_FOODACQ,
  one-seed-per-process, SERIAL, resumable, NH_FOODACQ_COOLDOWN passthrough.
- Data: results/foodacq_cd8.jsonl (the settled n=15 block + regression seeds),
  results/foodacq_v3.jsonl (cd=25 null), results/foodacq_block.jsonl (v1 aggressive,
  the STALL confound). Docs: DOCTRINE_CARDS_s11.md (S11-1/2), PROGRAM_FINDINGS.md
  (THE FOOD-ACQUISITION LEVER section rewritten to the reconciled verdict), this
  handoff. GIF: see MILESTONE below.

## THE RESULT (settled config = cd=8; the raw numbers were CONFIG-CONFOUNDED)
Three configs bracket a rate-limit-vs-stall tension:
- v1 aggressive (routing + no cooldown, ~5258 fires): hunger 6/15→1/15 STRONG but
  descent STALLS (mean depth 5.20→4.00, dev seeds 15→1) — agent farms corpses
  instead of descending. Confounded; DROPPED.
- v3 cd=25 (~119 fires): progression-safe but hunger NULL (6/15→5/15, CI [−.27,+.13]).
- **cd=8 (146 fires, median 8): the reconciled config.** n=15 hunger-prone seeds,
  cap 2000, one-seed-per-process:
  - **death-while-fainting (hunger-death) 5/15 → 0/15 (Δ −0.333)**
  - **fainting-incidence 6/15 → 2/15 (Δ −0.267, 95% CI [−0.533, +0.000], 5 imp/1
    reg, McNemar p=0.22)** — directional, needs n≈30 for 95%.
  - **progression-NEUTRAL (mean depth 5.20→5.47, +0.27)** — no stall.
  - **zero new death classes** (all TEST deaths ordinary combat; safe-corpse +
    cannibal guards held).
"Effect scales with fires" (earlier draft) is FALSE — cd=8 wins with 36× fewer
fires than v1; heavy firing was the stall, not the win.

## HONEST READ — the 9th angle is a lever, not a wall, but the mean still binds
NH_FOODACQ is the first program lever to REMOVE a death class safely. But it
CONVERTS hunger-deaths into combat-deaths at the same depth → the ascension mean
does not move; removing hunger UNMASKS COMBAT as the next binding constraint. The
resource-reframe pipeline is validated end-to-end (demonstration aimed → anti-faint
null refined → doom-moment corroborated → acquisition delivers at the hunger class),
and capability-boundedness at the MEAN still holds one layer deeper (combat).

## Standing config UNCHANGED — NH_FOODACQ ships DEFAULT-OFF. No revert needed.
Bit-identical flag-off. Default cd=8 baked in for when it goes on.

## Session-12 queue (value order)
1. **n≈30 confirmatory FOODACQ(cd=8) block** — push fainting CI clear of 0 (mine
   ~15 more of the 76-seed fainting corpus; same pre-reg design).
2. **COMBAT-SURVIVAL lever = the new Tier-1** (FOODACQ unmasked it). PET UTILIZATION
   (zero prior use) / WIELD UPGRADE (zero wield actions ever) / safe early leveling.
   Pair with FOODACQ, measure the MEAN (progression), not just the death class.
3. Attach the s11 MILESTONE GIF to the paper's resource-reframe figure.
4. General doom-moment loop (real-env backward replay) on the combat corpus.
5. Deeper ttyrec: a past-D21 ascension to extend S9-1 world-model validation.

## Gotchas (still bite)
- NLE only via PYTHONPATH=pylib; NH_* knobs read at IMPORT time.
- Episodes SLOW (~90s/ep at cap 2000 under load): a 3-seed paired chunk (6 procs)
  ≈ 9 min — sits right at the 10-min foreground Bash cap. Size chunks to 3 seeds;
  if a chunk auto-backgrounds, wait for CHUNK_DONE before launching the next
  (single-heavy-job rule — VM contention causes wall-timeout losses).
- ONE seed per process for paired blocks (s8 cross-seed leakage).
- FOODACQ is NOT flag-off-only inert: when ON it changes behavior on ALL seeds
  (banks corpses) → ALWAYS regression-check a "win" on OFF-target (healthy) seeds
  for progression, not just the enriched target corpus (S11-2).
- Push to FORK; commit author "NetHack Phase-L s11 (claude-opus-4-8[max])
  <nethack@botxiv.org>". Edit flat work/fable_nethack, cp to worktree
  papers/balrog/{code,artifacts}/nethack/.
- Findings docs canonical at researchy/docs/PROGRAM_FINDINGS.md +
  DEATH_TO_CAPABILITY.md (mirror artifacts copy in worktree). Doctrine cards +
  handoffs live in flat work/fable_nethack root.

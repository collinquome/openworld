# HANDOFF_10 — Phase L session 9 → session 10

MODEL: claude-opus-4-8 (max thinking) wrote this — session 9, the SIXTH opus
session. Runtime identity VERIFIED at open (system-prompt id = claude-opus-4-8,
max thinking; Fable at usage cap). All s9 artifacts stamped claude-opus-4-8[max].
Fork aleph/fable-nethack.

## HEADLINE: DEMONSTRATION LEARNING opened — world model validated on expert
## play + the expert hunger law derived + the anti-faint guard built.
The session's mandate was NH-E35 (learning from public ttyrecs). It also caught
the operator's mid-session RESOURCE reframe (hunger = #1 killer, decision levers
were the wrong KIND). Both landed as clean, data-grounded results.

### 1. NH-E35a WORLD-MODEL VALIDATION (P1) — 0 / 56,407 on expert data. SOLID.
Replayed 4 public alt.org expert human ttyrecs (rschaff ×3, nnnet ×1 — 2
top-class players, ~15k turns) through our symbolic possibility-set model.
**V_TIME / V_HP / V_XP / V_DEPTH: 0 violations / 56,407 action-free checks.**
Extends the "0 / 233k self-play" number to data WE DID NOT GENERATE — the
world-model invariant layer does not drift on independent expert transitions.
Honest caveats (in CARD S9-1 + PROGRAM_FINDINGS): V_MOVE/V_NONMOVE_POS need
action labels that V1 human ttyrecs lack (cursor≠hero → V_MOVE's 19–23% is
recovery noise, excluded); games are shallow (max Dlvl 13 < our D21 — alt.org
prunes ascension archives) so NOT yet validated past our own depth.
Tooling note: NLE's C Converter emits ZERO frames for dgamelaunch human ttyrecs
(keyed to NLE frame markers absent in V1) → we hand-rolled a minimal ANSI
emulator. Cache: work/fable_nethack/ttyrecs/ (4 games, ~7MB). Result:
results/e35_validate.json.

### 2. NH-E35c EXPERT HUNGER LAW (arbiter) — "never below Hungry". SOLID.
Across the 4 games / ~35k turns, NO expert EVER dropped below the Hungry tier
(0 frames Weak/Fainting). Experts eat ONE TIER EARLIER than us and never enter
the faint cascade. This is the demonstration arbiter endorsing eat-at-Hungry.

### 3. ANTI-FAINT GUARD (Tier-1 immediate mass) — BUILT, flag-OFF, backtest PENDING.
Our own 741 trajectories: **62.1% reach Hungry, 35.0% Weak, 26.5% Fainting**
(more PEAK at Fainting than Weak → we blow through the WEAK-eat guard). Expert
Weak-incidence = 0%. Guard [ANTI_FAINT] / flag NH_ANTIFAINT fires the readily-
available-food eat (inventory / corpse-here / <=3-step safe corpse) at HUNGRY,
gated on no adjacent hostile; prayer+detours stay WEAK+. Strict superset of the
proven WEAK-eat, one tier earlier. See CARD S9-3.

## What landed (all stamped opus-4.8[max], flat work/fable_nethack)
- **e35_ttyrec.py (NEW)** — minimal ANSI/VT100 ttyrec emulator + blstats/status
  parser (why hand-rolled: NLE Converter is inert on human V1 ttyrecs).
- **e35_validate.py (NEW)** — replays ttyrecs through the possibility-set rules
  (ported from c2_violations); writes results/e35_validate.json.
- **e35_antifaint_smoke.py (NEW)** — per-arm foreground paired-smoke driver
  (reads results/trajectories/<arm>__ep<seed>.json for hunger max + notes).
- **nh_agent.py** — flag C2_ANTIFAINT=_flag("NH_ANTIFAINT"); added to C2_ANY;
  ANTI_FAINT block inserted before the WEAK-eat block in _decide. All guarded;
  flag-off structurally bit-identical (import verified, AST OK, runs clean).
- Docs: DOCTRINE_CARDS_s9.md (S9-1/2/3), PROGRAM_FINDINGS.md (2 updates:
  world-model-on-expert-data + the resource-reframe/demonstration-arbiter), this
  handoff. ttyrecs cached under ttyrecs/.

## Standing config UNCHANGED — NH_ANTIFAINT ships DEFAULT-OFF. No revert needed.

## Session-10 queue (value order)
1. **RUN the pre-registered anti-faint paired block** (the immediate-mass move,
   guard is built + waiting). REF = C2.1 frozen (NH_FOOD2 NH_PRAYFIX NH_LOS
   NH_TOPO NH_GUARD + NH_CAST NH_CASTHUNGER NH_E15) vs TEST = REF+NH_ANTIFAINT.
   n>=20 dev seeds, cap 6000, ONE seed per process (cross-seed leakage). Proxy
   KPI = **Fainting-incidence rate (26.5% now, n=741 → tight CI; target →0%)** —
   far higher-SNR than the terminal faint-death count. Drop-rule; green before
   'kept'. Command shape in e35_antifaint_smoke.py header.
2. **Safe-corpse audit** (coordinator piece 2): SAFE_CORPSES (nh_common:155) +
   _cannibal + freshness — is the table over-rejecting edible corpses vs what
   experts eat? (E35c corpse-eating behavior is the reference.)
3. **Rest of the operator's hunger toolkit**: nutrition as first-class importance-
   weighted dossier resource (turns-to-Weak projection, food-source map) → feeds
   strategist; NH-E12 death-retro replay on starved-93+fainted-52; isolated
   hunger self-play; wiki Comestible/Eating/Prayer KB (provenance:wiki). Then
   compile the food-economy doctrine (food-paced descent, gold→food, pray-timing).
4. **Tier-2 trash-attrition** (untried resource levers): PET UTILIZATION (zero
   prior use), WIELD UPGRADE (zero wield actions ever), safe early leveling.
5. **Deeper ttyrec**: fetch a fresh ASCENSION from a currently-active ascender to
   extend E35a past Dlvl 21 (the unmet depth ambition; alt.org prunes old ones).

## Gotchas (still bite)
- NLE only via PYTHONPATH=pylib; NH_* knobs read at IMPORT time.
- **NLE C ttyrec Converter is INERT on alt.org human V1 ttyrecs** — use
  e35_ttyrec.py, not nle.dataset.Converter, for human recordings.
- alt.org ttyrecs: dir listing works (userdata/<L>/<user>/ttyrec/, uncompressed
  .ttyrec); S3 bucket is now access-denied; only currently-active players' recent
  games remain (pruned); some users 403 (IanCurtis). Modest/timeout-guarded fetch.
- Episodes are SLOW (survivors ~60–130s at cap 6000) — a paired block is a
  multi-min foreground run; size the Bash tool timeout (max 600000ms) and use
  capblock's per-episode resumability. The naive 2-min default WILL kill it.
- ONE seed per capblock process for paired blocks (s8 cross-seed leakage).
- Push to FORK; commit author "NetHack Phase-L s9 (claude-opus-4-8[max])
  <nethack@botxiv.org>". Edit flat work/fable_nethack, cp to worktree
  papers/balrog/{code,artifacts}/nethack/.

## Honest read on demonstration learning as a capability lever
E35a is a genuine WIN on world-model quality (independent-data corroboration),
but it is a VALIDATION result, not yet a mean-mover. The mean-mover test is the
anti-faint guard (E35c-derived): the FIRST capability-injection lever aimed by
demonstration rather than intuition, and aimed at the #1 death class with a
high-SNR proxy. If it moves Fainting-incidence, demonstration learning is viable
where advisory-push was inert — that would be the qualitatively-different result
the program has been hunting. It is built and one paired block from an answer.
Demonstration's clearest value so far = it told us WHERE to aim (eat-at-Hungry),
cheaply and unambiguously, which the 7 intuition/decision levers never did.

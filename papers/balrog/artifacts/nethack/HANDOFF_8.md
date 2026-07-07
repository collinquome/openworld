# HANDOFF_8 — Phase L session 7 → session 8

MODEL: claude-opus-4-8[1m] (max thinking) wrote this — session 7, the FOURTH
opus session. Runtime identity VERIFIED at open (system-prompt id =
claude-opus-4-8, matches intended assignment; Fable at usage cap) — NO mismatch.
All s7 artifacts stamped claude-opus-4-8[1m]. Commit 93dc8ec on fork
(aleph/fable-nethack).

## HEADLINE: 2 mean-movers DROPPED (with numbers) + the rule-base ARCHITECTURE landed
Velocity mode. Delivered per-workstream verdicts, not new designs.

1. **DOOR_DIAGONAL_KITE — DROP at the self-play gate.** The most-promising
   untested trash-fight lever. Paired KITE-vs-DOOR_KITE over 16 (seed×backoff)
   TRASH branch states: the door term changed the chosen step 13/16 (mechanism
   fires) but survival 0/16 both, sum-max-distance-to-pursuer KITE 24 vs
   door-variants 24/23 (NO gap opened), turns-adjacent 83% vs 91-94% (WORSE —
   routing to the choke traps the agent). Two variants failed: door-seeking-
   primary AND door-as-free-tiebreaker. Straight-line flee already escapes 4/4;
   the door-diagonal exploit geometry (diagonal pursuer + straight door run)
   isn't present in this death class. Per the s6 MODEL-FIDELITY meta-card
   (in-model over-credits), a non-winner in-model is a clean DROP — does NOT
   graduate to a real-env block. **The gate saved the expensive block.**
   (door_kite_distance.py, door_kite_selfplay.py, self_play_doorkite_b120.json.)
2. **HEALER MIDDLE-HP-BAND — DROP.** n=20 role-strat, band 0.30-0.55 under
   threat. WIKI-attributable Healer delta **-0.63** CI95 [-1.76,-0.02] (CI
   excludes 0), survival@D5 **40%→20%**, 18 heal casts. The WHEN-band did NOT
   rescue it: seed 900 regresses IDENTICALLY to s6 (D10/12.56→D4/2.12). Third
   net-negative trigger (s6 crisis-late, s6 proactive-safe, s7 mid-band) — the
   heal-cast lever is net-negative for this agent independent of the band; the
   cast-turn opportunity cost dominates the HP restored. Ships flag-OFF.

## What landed (all stamped opus-4.8[1m], commit 93dc8ec)
- **RULE_BASE_ARCHITECTURE (s7 HEADLINE, operator's big ask).** nh_rulebase.py:
  declarative {condition matcher over served-obs state, reminder + action_tag,
  severity HARD-GUARD|ADVISORY, provenance×2}. FOUR guards migrated behavior-
  preserving — NEVER_MELEE (HARD), TOUCH_KILL_WEAPON (ADV), PRAYFIX_DEFER
  (HARD), HEAL_MIDBAND (ADV). nh_agent delegates the four decision sites behind
  NH_RULEBASE. TWO consumers proven: procedure `RB.check(rule_id,state)` +
  intuition `RB.reminders_text(state)`. Regression: rulebase_equiv.py 130/130
  unit-equiv; seed 706(Priest)+831(Healer) NH_RULEBASE 0-vs-1 BIT-IDENTICAL;
  flag-off bit-identical to s6 baseline; snapshot 19/19.
- **KICK_COST_GATE** (NH_KICK_GATE, flag-off): skip kick when HP<50% max or
  fragile role (Tourist/Wizard/Archeologist), defer-and-return. Unit-verified.
- **HEALER mid-band code** (nh_agent): NH_HEAL_HP_LO=0.30 band floor + under-
  threat trigger; s6 proactive no-threat top-up REMOVED. Mechanism fires (18
  casts) but lever dropped.
- Docs (batched at close): DOCTRINE_CARDS_s7.md (4 cards + verdict table),
  INSIGHT_LEDGER s7 section, RUN_LOG S7-1..4 + KPI-DASH + close.

## Standing config UNCHANGED
Both s7 levers ship DEFAULT-OFF (NH_ROLE_PROFILE, NH_KICK_GATE, NH_RULEBASE all
default 0). No revert needed. Flag-off == s6 baseline (seed 706 anchor).

## Session-8 queue (value order)
1. **ADVISORY-PUSH ablation (the rule-base payoff block).** The base + two
   consumers are built; the deferred question is: does pushing RB.reminders_text
   into the LLM/intuition (Arm-B) context IMPROVE decisions? Pre-register an
   Arm-B paired block (reminders-on vs -off) on a mixed-role seed set. This is
   the first block that tests the architecture's VALUE, not just its wiring.
2. **The trash-death class needs a NON-heal, NON-throw, NON-door lever.** Three
   trash-fight levers have now dropped (THROW s6, door-kite s7) or the death
   persists (heal s6/s7). TRASH is still 14/20 of Healer deaths. The clean
   finding: these deaths escape the LOCAL fight (4/4) but die DOWNSTREAM — the
   bottleneck is next-level survival, not the one-step disengage. Reframe the
   lever search toward post-escape survival (arrive-safer, not disengage-better).
3. **Migrate MORE knowledge into the rule base** (now that it's the compile
   target): the scattered CAST_NEVER, novelty-detector, FAST_THREATS, elbereth
   guards → declarative rules with provenance. Cheap, compounding, regression-
   safe (same equiv recipe).
4. **Kick-gate A-B** (quick): flip NH_KICK_GATE on for a small paired block to
   confirm the safety fix is non-regressive before making it default.
5. Deprioritized (unchanged from HANDOFF_7): ARMOR wear-rule (likely ~0),
   Tourist/Priest profiles (do NOT copy the Healer naive-trigger mistake),
   E35a ttyrec (flag coordinator before corpus download), E21b BLIND arm
   (needs a fresh-context instance — do NOT self-run).

## Gotchas (still bite)
- NLE only via PYTHONPATH=pylib; knobs read at IMPORT time; one condition/proc.
- capblock.py is resumable + checkpoints per-episode — run FOREGROUND/chunked
  (the parallel-background launch_*.sh die silently; ops rule). cap-6000
  survivors dominate wall-time (a 20-seat arm ~6min of quick-deaths + a few
  slow survivors).
- Lever-fire counts from the result dict (heal_fires/throw_fires) or traj evs —
  NEVER stdout. A fired lever DIVERGES the run; bit-identical pair = no fire.
- Rule-base regression recipe: rulebase_equiv.py (unit) + a seed 706/831
  NH_RULEBASE 0-vs-1 trajectory diff (in-vivo). Both green before 'kept'.
- Push to FORK (aleph/fable-nethack); commit author "NetHack Phase-L s8
  (claude-opus-4-8[1m]) <nethack@botxiv.org>". Edit flat work/fable_nethack,
  cp to worktree papers/balrog/{code,artifacts}/nethack/ (no mirror script).
- Renderer render_c2.py; times out under block contention. No honest positive
  GIF this session (both mean-movers dropped) — did not render one.

## Exit-criteria scoreboard (toward Phase E)
- Levers tested this session: 2 (both DROP, clean diagnoses). Cumulative shipped
  levers to standing config: unchanged (CAST/CASTHUNGER/E15/etc. from prior).
- Architecture: rule base BUILT — the compile target for external knowledge is
  now real; the advisory-push VALUE test is the s8 gate.
- Before Phase E: (a) find ONE trash-death lever that survives a paired block
  (the death class is unmoved across 4 attempts); (b) the advisory-push block
  must show the intuition layer USES the rule base to improve decisions;
  (c) migrate the remaining guards into the base. Phase E (the LLM/intuition-
  in-the-loop live arm) is gated on (b).

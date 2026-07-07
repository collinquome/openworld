# HANDOFF_7 — Phase L session 6 → session 7

MODEL: claude-opus-4-8[1m] (max thinking) wrote this — session 6, the THIRD
opus session. Runtime identity VERIFIED at open (system-prompt id =
claude-opus-4-8, matches intended assignment; Fable at usage cap) — NO
mismatch. All s6 artifacts stamped claude-opus-4-8[1m].

## HEADLINE: two pre-registered paired blocks RUN → BOTH DROP (informative negatives)
Velocity mode (operator directive): execute + verdict. Delivered 2 clean
verdicts with numbers + mechanistic diagnoses, not new designs.

1. **THROW_DISENGAGE — DROP.** n=12 paired, delta **-0.28** CI95[-0.68,0.00].
   17 live fires on 4 seeds; every seed where the throw MATERIALLY diverged the
   run REGRESSED (732 D4→D1 -2.12, 783 -0.89, 782 -0.37). The e6 REPLAY
   backtest OVER-CREDITED it: won at 4 pre-death branch-states drawn from
   baseline-policy episodes, but the live standing-config policy never reaches
   them (e6-winners 707/727 fired 0× live); hurling at a same-speed ADJACENT
   monster donates a turn without creating distance → worse than the incumbent.
   → the MODEL-FIDELITY-FOR-STRATEGY-TRAINING meta-card (DOCTRINE_CARDS_s6.md):
   backtest proposes, LIVE paired block disposes. Ships flag-OFF (default).
2. **HEALER cast-heal (NH-E13 wiki flagship) — DROP.** The controlled "does the
   strategy guide help?" number: WIKI-ATTRIBUTABLE Healer delta = **-0.62**
   CI95[-1.73,0.00] (mean 2.57→1.95), survival@D5 40%→25%. Heal MECHANISM works
   (18 casts, menu parse+select+HP-restore confirmed) but the DOCTRINE
   as-implemented is net-negative: crisis-trapped heal fires TOO LATE (~hp
   4/21; 16/20 test eps bit-identical to ref), proactive HP<55% top-up is
   HARMFUL (burns turns/Pw, perturbs good runs — seed 900 ref D10/12.56 → test
   D4/2.12, -10.44). The wiki gives the WHAT, not the WHEN. Ships flag-OFF.

## What landed this session (all stamped opus-4.8[1m])
- **Two paired-block verdicts** (RUN_LOG S6-5, S6-6) + KPI-DASH lines each.
- **Healer profile WIRED** behind NH_ROLE_PROFILE (nh_agent.py): heal-cast
  plumbing (self-target spell, additive heal-scan in _parse_cast_menu, menu
  handler, _cast_heal at 3 sites). MECHANISM is reusable; only the trigger was
  wrong. Flag-off bit-identical (seed 706).
- **MEASUREMENT-BUG fix** (S6-2): note()/_ev() append to lists, never print →
  any lever-fire count off stdout is a false 0. nh_runner result now carries
  throw_fires/heal_fires/cast_fires (additive); capblock reads them; historical
  recovery via traj `evs`. This bit the THROW block mid-flight (recovered).
- **STRATEGIC SELF-PLAY harness** (self_play.py) on the trash-fight, reusing
  e6 pol_kite/throw/stairs + pol_mc. In-model per-strategy survival number:
  results/self_play_trash.json (see RUN_LOG S6-7). FIDELITY GUARD stated: NLE
  replay = deterministic single-combat-sample; MC samples the AGENT policy, not
  game dice. The GAP vs the real-env THROW block (-0.28) is the reported
  finding — in-model over-credits.
- **Docs (batched at close):** DOCTRINE_CARDS_s6.md (THROW drop + model-
  fidelity meta-card + Healer drop + verdict-summary table, all two-axis
  provenance); INSIGHT_LEDGER.md s6 section (3 insights + replication recipes);
  NETHACK_PROGRAM.md E6 row updated; RUN_LOG S6-1..7; KPI-DASH.
- **GIFs** (results/animations/, flagged in RUN_LOG for the operator email):
  s6_healer831_D8_castheal (mechanism: Healer casting heal, dive to D8),
  s6_healer900_ref_D10 vs s6_healer900_test_D4 (before/after: the wiki doctrine
  BACKFIRED). NOTE: no honest THROW "we found the fix" shot exists — the lever
  was DROPPED; do not render one.

## Session-7 queue — COORDINATOR DIRECTIVES STACKED THIS SESSION (velocity-triaged, NOT executed)
The coordinator fired several new directives mid-session; per the velocity
directive (verdicts on mean-movers first, don't balloon) I landed the 2
flagship verdicts and TRIAGED these to s7. In rough value order:
1. **HEALER refinement block** (the obvious next verdict): heal at a MIDDLE HP
   band (fire earlier than the hp-4 crisis so it changes survival; DROP the
   proactive top-up that perturbs good runs). One knob (NH_HEAL_HP already
   exists; add a crisis-only gate). Pre-register + run — the mechanism is built.
2. **DECLARATIVE RULE BASE** (operator architectural directive, the big one):
   formalize "scenario qualifies → reminder" as a first-class rule base
   {condition matcher, reminder/action, provenance, severity HARD-GUARD|
   ADVISORY}. TWO consumers from ONE base: PROCEDURE layer (hard-guards fire as
   veto/forced-action — migrate NEVER_MELEE/TOUCH_KILL/PRAYFIX/HEAL etc. in,
   behavior-preserving, flag-off bit-identical) + INTUITION layer (advisory
   rules pushed into the LLM context as a REMINDERS section). Then the
   reminder-ablation number (does advisory-push improve Arm-B decisions?). This
   is a MAJOR build — scope it as s7's headline.
3. **Door-diagonal KITE sub-tactic** (wiki Standard_strategy): can't move
   diagonally into/out of a doorway → a same-speed pursuer eats an orthogonal
   penalty at a door → converts an un-winnable same-speed chase into a gap.
   VALIDATE in strategic self-play (perfect testbed: NLE enforces the door rule
   natively). Directly attacks the #1 death class (same-speed-adjacent trash) —
   and it's a POSITIONING fix, unlike the failed THROW (which donates turns).
   This is the most promising trash-fight lever left.
4. **Kick-cost doctrine gate** (CONFIRMED needed): nh_agent.py ~2472-2492 kicks
   locked doors up to 12× with NO HP/role gating — reckless (break-leg→slow→
   death, esp. Tourist/low-HP). Add an HP/role gate (defer unkickable doors as a
   re-firing curiosity objective when a key is later found). Low-priority, cheap.
5. **Tourist / Priest profiles** (registered): NOT wired. Given the Healer
   flagship DROP, do NOT copy the same naive-trigger mistake — Tourist's dart-
   bridge is throw-forward (and THROW just failed as a disengage; but Tourist
   throw is kill-before-contact, a different use — still, gate carefully).
6. **ARMOR wear-rule block** (registered): s5 headroom probe = 0/20 early-game
   (INERT early). A paired block would likely show ~0. Deprioritize unless a
   mid-game headroom scan finds candidates first.
7. **NH-E35a ttyrec world-model validation**: design/parser stub only; flag the
   coordinator before any heavy corpus download.
8. **E21b 4-arm BLIND arm** still needs a FRESH-CONTEXT instance — do NOT self-
   run (partially informed). Flag the coordinator.

## Standing / gotchas (still bite)
- NLE runs ONLY via vendored pylib/nle → PYTHONPATH=pylib for everything.
  Knobs read at IMPORT time; set env BEFORE import; one condition per process.
- Episodes slow; cap-6000 SURVIVORS dominate wall-time (a 12-seat block took
  ~35min; a 40-seat block ~50min). Use capblock.py (NH_STEPCAP) + parallel
  worker suffixes (disjoint JSONs, glob for analysis). Don't oversubscribe cores
  — the self-play branch-replay competes hard (kill it during a flagship block).
- Lever-fire counts: read from the result dict (throw_fires/heal_fires) or traj
  evs — NEVER from captured stdout (note/_ev don't print). A fired lever
  DIVERGES the run, so any bit-identical test==ref pair = the lever didn't fire.
- Push to FORK only (worktree wt-fable-nethack, branch aleph/fable-nethack;
  flat work/fable_nethack is the runnable mirror — edit there, cp to worktree
  papers/balrog/{code,artifacts}/nethack/, commit/push). No mirror script.
- Commit author = "NetHack Phase-L s7 (claude-opus-4-8[1m]) <nethack@botxiv.org>".
- Renderer standard = render_c2.py (v3; +14 pad, my0+28 legend clearance).
  Rendering TIMES OUT under heavy block contention — render when cores are free.
- Snapshot suite (snapshot_suite.py) must be green (19/19) before commit; run
  at open too.

## nh_agent.py md5 (post-s6): see RUN_LOG S6 close line. Flag-off (all NH_
## levers unset) is bit-identical to the s5 committed baseline (seed 706 anchor).

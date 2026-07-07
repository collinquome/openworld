# HANDOFF_3 — Phase L session 2 → session 3 (FINAL, written at forced wrap — Fable usage cap)

MODEL HANDOFF (provenance rule): sessions 1-2 = Fable 5 (max reasoning).
SUCCESSOR = claude-opus-4-8 (max thinking), the registered fallback. Log
the handoff line in PHASE_L_REPORT's roster (done) and stamp your own
artifacts from here on.

MODEL: Fable 5 (max reasoning) wrote this and everything stamped session 2.
Read order: (1) this; (2) PHASE_L_REPORT.md (repo — session-2 sections);
(3) docs/NETHACK_PROGRAM.md (repo canonical; ~10 NEW rows: NH-E25/E26/E27,
AUX-CONSTRUCT, RENEWABLE, CAST-HUNGER, SHEET, HISTORY, SAMPLE10, DEV-B1,
SUITE-V, E6-HARVEST, MATRIX, E21b-LIVE); (4) HANDOFF_2.md still valid for
substrate.

## Exit-criteria scoreboard after session 2

(i) coverage matrix: FORMALIZED, baseline 16.4% weighted fill
    (coverage_matrix.py; 28 open hypotheses; TRASH column = the prize;
    WIELD/ARMOR/KITE/REST/FLEE × TRASH are the 0.394-weight cells).
(ii) gym syllabus: LIBRARY LIVE — 794 branchable scenarios
    (e6_harvest.py); top-5: TRASH 313 / MELEE+ 161 / STARV 160 /
    SPIDANT 80 / RANGED 43. Solve loop NOT started.
(iii) avoidable-damage cadence: DEV-B1 done (6%; trend 10→8→6).
    DEV-B2 needed (same standing config unless a lever ships first —
    which restarts the 2-block clock; judge at s3 open).
(iv) snapshot suite: STILL NOT ASSEMBLED (the one criterion untouched
    this session — fixtures for the 6 fixed bugs + probe records).
(v) violations: c2_violations.py PORTED + criterion PASSES on DEV-B1
    (0/119,057 after 3 real scope discoveries: conf/stun random-walk,
    level-teleport, god-punishment xp). Run it on every block.

## Session-2 lever verdicts

- CAST_HUNGER: retro quantified (4/12 Wizards hit refusal; s839 2759-step
  retry loop, 24% of episode; 2 hunger deaths). V1 = latch + eat-early.
  CASTHUNGER-1 verdict: eat-early CLEARLY NEGATIVE (s918 -9.91 — diverts
  every caster run; resource-TIMING: early ration burn ⇒ empty inventory
  at Weak ⇒ 'while fainted' deaths). V1b DROPPED (sub-flag
  NH_CASTHUNGER_EAT for the E20 lab). CASTHUNGER-2 (latch-only, 4
  affected seeds vs cast2 ref) IN FLIGHT at wrap: 839 done (2.91 = ref
  exact; hunger death persists — the latch stops the retry loop, it does
  not mint food; the STRUCTURAL fix is the RENEWABLE verified food loop),
  912 done (5.08 = ref exact), 940/980 running. VERDICT LANDS IN
  results/nethack_results_casthunger2_wa.json — c2_ab.py vs cast2,
  criteria in the RUN_LOG 18:09 entry; expect ship if 940/980 not worse
  (pure guard), then ledger row + report + add NH_CASTHUNGER to the
  standing config for casters.
- REPEAT V2: root cause of REPEAT-1 inertness = _explore honors only
  frontier-set targets. V2 routes to frontier-nearest-to-prediction as a
  first-class goal (budget 150/level, refutation events). Smoke diverges.
  REPEAT-2 VERDICT (final): +0.39 [-0.23,+1.28], 12/20 divergent
  (V1: 0/20), routing 19/20, best +7.71 s818 — mechanism FIXED, effect
  UNCLEAR => default-off per drop rule; goal-market integration is the
  revisit path.
- E15 watchdog: E15-1 paired block LAUNCHED (overnight rider, 4 workers,
  seeds 700-739, test=standing+NH_E15 vs ref=DEV-B1; pre-registered
  RUN_LOG 18:11). VERDICT LANDS IN: results/nethack_results_e15b1_w*.json
  — c2_ab.py vs devb1; wd_fires evidence in trajectories.
- Ledger harness on DEV-B1: 1 fire — D1 loot-approach 50x no-pickup on
  seed 704 (Knight starved D2); the KNOWN bounded class the predecessor
  also flagged once. Watch, not blocker; candidate gym scenario.

## E21b — first live intuition results (the session's milestone)

live_arm.py (replay-interactive; intuition = Fable 5 max, consultations
verbatim in results/e21b_live/*.json): T1 s0 WIN 27 steps/6 consults;
T6 s0 WIN 30 steps/8 consults via an UNDESIGNED solution class
(never-pick-up beats the possession trap) + probe branch pinned 4/4
mechanics and demonstrated the designed give-up line. Engine
anti-contamination bug found LIVE and fixed (obs inventory served
item_class ground truth; display_name only now; 9/9 tests green).
Session 3: T5, multi-seed, the 4-arm ablation (incl. (d) no-override),
and consider a FRESH-context intuition instance for blind statistics
(this instance had read the design docs — disclosed in the consult logs).

## Session-3 priority queue (my read)

1. CHARACTER SHEET + counterfactual power (operator, spec at
   NH-E14-role-modules/CHARACTER_SHEET_SPEC.md) — top of queue by
   operator reweight; unlocks WIELD/ARMOR doctrine = the top matrix
   cells; readiness ratio makes P1 computable.
2. DEV-B2 (criterion iii block 2/2) — decide config first: if
   CASTHUNGER-2/REPEAT-2 shipped, clock restarts; else same config.
3. Gym solve loop on TRASH (313 scenarios, 118 seeds): branch-explore
   via nh_branch, ≥3-seed generalization, MISPLAYED/UNWINNABLE stamps.
4. Snapshot suite (criterion iv — the untouched one): fixtures for
   armor-under-@, corpse-on-victim-cell, shopkeeper-dpt, dwarven≠dwarf,
   pet-not-a-wall, stale-door + E16 probe records as replay fixtures.
5. E15 paired block (ref = devb1, same 40 seeds, +NH_E15).
6. Zap doctrine (kb ray/beam table ready; RAY_BOUNCE + CAST_NEVER guards;
   probe via nh_branch first) + rest-spot quality rating (RENEWABLE cheap
   win vs the 57/66 attrition class).
7. NH-E25(a) open-mode session + SAMPLE-10-PICK-1 adoption at every
   generative moment (log the rejected 9).

## Session-ops notes

- Standing config unchanged: NH_FOOD2,PRAYFIX,LOS,TOPO,GUARD + NH_CAST.
  NH_CASTHUNGER pending CASTHUNGER-2 verdict; NH_REPEAT pending REPEAT-2.
- history_render.py: HISTORY.md per episode + KNOWLEDGE_INDEX.md
  (regenerate at session open — it live-greps rule cards).
- c2_violations.py runs offline on any transitions dir; keep its scoping
  discipline (new violation ⇒ either a real bug or a world-model scope to
  model, never silently ignored).
- The work dir (fable_nethack) is the run workspace; wt-fable-nethack is
  the repo worktree (push fork aleph/fable-nethack). package_artifacts.sh
  + manual cp for new files (I synced nh_agent, c2_violations, e6_harvest,
  coverage_matrix, phasel_block, history_render).
- Registration hygiene held: EVERY operator directive of this session is
  in docs/NETHACK_PROGRAM.md rows + experiment READMEs/specs. Check there
  before creating anything.
- ARC-3 sibling 25/25 claim: WATCH ITEM only (unverified vs public repo).

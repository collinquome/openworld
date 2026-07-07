# HANDOFF_2 — Phase L session 1 → session 2 (written 2026-07-07 late)

MODEL: Fable 5 (max reasoning) wrote this and everything stamped today.
Read order for successor: (1) this file; (2) PHASE_L_REPORT.md (repo:
papers/balrog/artifacts/nethack/) — running log + verdicts; (3)
docs/NETHACK_PROGRAM.md — now carries ~15 NEW registered experiments/
directives from an operator directive burst (E16–E24 + GOALS/PLAYBOOKS/
RESOLUTION/RECALL/DECIDE rows); (4) HANDOFF.md (v1, still valid for
technical substrate).

## What landed today (all committed + pushed, fork collinquome/openworld aleph/fable-nethack)

1. **Harness-audit fixes 1–4,6 SHIPPED** (snap-error counting, transition
   flush+.complete+tolerant reader, RUNNER_TRUNCATED end-reason, ttyrank
   role fallback + role_source, blstats depth ground truth + same-obs
   assert). Flag-off regression byte-exact. The dev-block gate is
   satisfied.
2. **nh_branch.py (NH-E16 instrument)**: (seed,prefix) snapshot/branch on
   the verified-deterministic stack; forbidden-seed guard; probe records
   in results/e16_probes/. Session determinism gate: run
   `nh_branch.verify_determinism()` before trusting any probe batch.
3. **Verb grammars pinned** (7 probes, Wizard 940): cast→menu(Fail%)→
   letter(Pw deducted)→direction; zap/quaff/read/wield/puton mapped;
   getobj brackets list candidate letters (a served percept); 'more'
   dismisses menus free; esc exists. **RAY_BOUNCE danger card**: wall-
   adjacent lightning zap killed the caster turn 1 on a branch.
4. **CAST_ATTACK_V1.1 (NH_CAST)**: per-episode menu discovery, fail%≤20 +
   Pw≥5·level gates, adjacent-preferring-never-melee + clear-line
   fast-threat targets ≤6; CAST_NEVER peaceful-class guard (shopkeeper
   anger killed 3 dev Wizards in CAST-1 — cast skips "Really attack?").
   **CAST-1: guards exact-0 ×8; Wizard block 3.12→4.39, +1.27/seed paired
   (8+/3−/1=0).** CAST-2 (V1.1 revalidation, 12 Wizard seeds) was
   completing as this was written — check results/nethack_results_cast2_*
   vs cast1ref via c2_ab.py; criteria: shop deaths→0, delta not clearly
   negative. THEN update ledger row + report.
5. **NH-E18 memory substrate v0.1 (nh_store.py)**: events/items+prices/
   monster ledger(passive_adj!)/features/story + ctx_package
   (CONTEXT_SPEC v0.2 — REMINDERS section registered but not yet built).
   traj["store"] serialized. Reflection pass #1 (seed 990) produced R1–R3
   + 2 instrument fixes; artifact in NH-E18/results/e18_reflection_990.md.
6. **LAYOUT-REPEAT WORLD DISCOVERY**: NLE seeded gen repeats layouts
   (19/96 consecutive pairs >60% identical; some 1.0). NH_REPEAT lever
   built (≥85% match over ≥60 cells ⇒ predict stairs at prev level's
   cell, explore-target hint). Smoke 3/3 correct. **Paired block NOT yet
   run — next dev action** (ref = cast1ref results, same 20 seeds, test =
   frozen+NH_REPEAT).
7. **NH-E15 stall watchdog v1 (NH_E15)**: 150-turn no-progress window
   (rest-exempt) → L1 perturb / L2 disengage-80-steps; unit-verified;
   rides the next dev block. Full state machine + playbooks + resolution
   chain + option menus + decision pattern: REGISTERED, not built.
8. **NH-E12 backfill**: 163 retros; **59% ARRIVAL_CONSTRAINT** (per-role
   100%–29%) = the preparation thesis quantified. 44.2% below-half final
   stretch.
9. **NH-E13 KB**: 15 pages FTS5 + manifest + kb_prices.json (incl. wand
   ray/beam types — the NH_ZAP safety table). NH_ZAP NOT yet wired.
10. **NH-E21b engine DELIVERED** (engine/ in its folder): grammar, 6
    templates, tests 9/9, baseline ablation = pre-registered signature
    (T1/T5/T6 0%, T2-4 100%). LLM arms (a)(c)(d) are stubs — wiring the
    intuition layer in is the next E21b step.
11. **NH-E22 pass 1**: departure-explored vs next-level survival = NULL
    (Δ −5.1 [−31,+20]). Read with E12: preparation pays via xp/AC, not
    tiles.
12. **Role census** results/role_census.json (800–999): 12 Wizards etc.

## The directive burst (ALL registered in program doc + experiment READMEs; none should be re-registered)

NH-E16 search-as-teacher (+ mechanic discovery loop), NH-E17 clean-room
rebuild (at exit; keep artifacts reconstruction-complete), NH-E18
connecting-dots (+ curiosity objectives, question-driven retrieval,
curiosity reward formula DEMOTED to baseline — felt-sense is DEFAULT per
operator, reminder loops, recognition-primed decision + option menus),
NH-E19 principles (PRINCIPLES.md v0.1 P1–P6 seeded; defeasibility +
override protocol; algorithm catalog TBD), NH-E20 MiniHack lab (not yet
started — spellcast doctrine + D5-6 melee first), NH-E21/21b composition
worlds + THE GAME, NH-E22 exploration→model-quality (pre-registered),
NH-E23 bandits (scheduling + strategy posteriors), NH-E24 curiosity
framings (felt-sense default), four-layer naming
(PERCEPTION/MEMORY/INTUITION/PROCEDURE — tag everything), CONTEXT_SPEC
v0.2, model-provenance standing rule (stamp MODEL on every artifact),
goals-are-a-list, pursuit schedules/playbooks/boss strats, strategy
resolution order, standard decision pattern (playouts), exploration
metrics (3 estimators; wired into store), readiness backtrace +
trajectory avoidability (NOT yet implemented in c2_avoid — open),
capability map (0/34 cells resolved — fill via probes/lab).

## Late-session addenda (post-draft)

- **CAST-2 SHIPPED: +2.41 [+0.75, +4.41]** — first CI-low>0 lever ever;
  shop deaths 0; NH_CAST joins the Phase-L config for casters.
- **REPEAT-1 INERT: all 20 deltas exact 0.00** — hint fires but explore
  layer discards the target; rework = first-class goal injection.
- Healer heal Xp1-BLOCKED (pwmax 4 < 5 cost) — capability-map cell verdict.
- FIRSTS ledger live in store (kill/verb/depth); PARETO directive +
  option-frontier + tail-regime tagging registered; c22 GIFs rendered.

## Priority queue for session 2 (my read, честно)

1. CAST-2 verdict → ledger + report (if green: FIRST SHIPPED Phase-L
   capability lever).
2. REPEAT-1 paired block (cheap, potentially large; ref exists).
3. NH_ZAP v1 (wand types table ready; CAST_NEVER + RAY_BOUNCE guards;
   probe first via nh_branch).
4. WIELD/ARMOR doctrine (P2/P3) — weapon-value perceptor; E12 says
   readiness is the death driver.
5. E21b intuition-arm wiring (the ablation IS the paper's centerpiece).
6. E20 MiniHack lab bootstrap (des-file smoke + first boss-strat reps:
   soldier-ant pack).
7. Trajectory-avoidability counterfactual (E12 extension) — the
   moment-vs-trajectory gap number the operator wants.
8. Coverage matrix + avoidable-damage trend need their Phase-L dev-block
   cadence started (exit criterion iii needs 2 consecutive 40-ep blocks).

## Session-ops notes (beyond HANDOFF v1's)

- 4 parallel env workers saturate the box; episodes 30–100 steps/s.
- phasel_block.py <label> <suffix> <seeds...> reads NH_* env flags;
  results/nethack_results_<label>_<suffix>.json; c2_ab.py for paired
  reads; md5s + pre-registration line into results/RUN_LOG.txt BEFORE
  launch (did this for CAST-1/2).
- Monitor tool for waits (bare sleep is blocked); until-loops via
  run_in_background Bash.
- Registration hygiene: every operator directive of today is IN
  docs/NETHACK_PROGRAM.md — check the ledger table + experiment READMEs
  before creating anything new.
- The coordinator relays operator directives mid-session at high rate;
  budget ~30% of context for registration work.

# HANDOFF_6 — Phase L session 5 → session 6

MODEL: claude-opus-4-8[1m] (max thinking) wrote this — session 5, the SECOND
opus session (Fable 5 s1-3 then cap; opus s4-s5). Runtime identity VERIFIED at
session open: system-prompt id = claude-opus-4-8, matches the intended
assignment; NO label/runtime mismatch. All s5 artifacts stamped
claude-opus-4-8[1m]. Pushed to fork: commit 0d4addd on aleph/fable-nethack.

## ENVIRONMENT (unchanged, still bites)
NLE runs here ONLY via vendored `pylib/nle` — `PYTHONPATH=pylib` for
dev_run/pair_rest/e6_solve*/armor_headroom (nh_branch/nh_sheet self-path).
Episodes slow (~12-50 steps/s; survivors run to cap). Snapshot suite green
19/19 (~56s). Knobs read at IMPORT time — set env BEFORE importing nh_agent;
one condition per process. Push to FORK only (worktree wt-fable-nethack,
branch aleph/fable-nethack; flat work/fable_nethack is the runnable mirror —
edit there, mirror to worktree, commit/push). Worktree layout: code →
papers/balrog/code/nethack/; program doc → docs/NETHACK_PROGRAM.md; artifacts
(RUN_LOG, cards, result JSONs) → papers/balrog/artifacts/nethack/; KB →
experiments/NH-E13-wiki-strategy/; census → experiments/NH-E14-role-modules/
results/. Commit author = "NetHack Phase-L sN (claude-opus-4-8[1m])
<nethack@botxiv.org>".

## What landed this session (all stamped opus-4.8[1m])
- **★ E6 SOLVE LOOP v2 (e6_solve_v2.py)** — the REAL REST fix. Rich escape
  menu driven off the agent's perception (fresh C.Atlas on the branch obs):
  KITE (relaxed disengage — drops _flee's slower-only + full-disengage
  gates), THROW (back-and-throw ammo at nearest in-line hostile), STAIRS
  (BFS to stairs, leave the level), + REST/RETREAT (v1). Multi-backoff; in-
  model MONTE CARLO (K seeded rollouts) gates the UNWINNABLE stamp. Re-
  adjudicated the 9 s3-UNRESOLVED TRASH deaths: **ALL 9 → MISPLAYED, 0
  UNWINNABLE**; THROW won **4 distinct seeds** → **THROW_DISENGAGE class-solve
  rule GRADUATES**. MC proved its worth: 712 UNWINNABLE@mc8 → MISPLAYED@mc20.
  results/e6_solve_v2_trash.json.
- **THROW_DISENGAGE wired** (nh_agent._crisis_throw, behind NH_CRISIS_THROW
  default off) — fires in the crisis branch after _flee declines. FLAG-OFF
  REGRESSION PASS (seed 706 bit-identical to committed baseline md5 6cb03764).
  md5 nh_agent.py now 9074c6a903b78a9f0fd8d71236d66486.
- **ARMOR DEFENSE MODEL (nh_sheet.py)** — the s4 UNBUILT blocker cleared. AC
  now enters the readiness ratio: _p_hit_on_us(AC,mlev), defense_model()
  scales the empirical band dpt by P_hit(AC)/P_hit(AC_REF=7.1) → eff_hp,
  PI_def, RR_def. counterfactual_armor() + counterfactual_power WEAR now
  return REAL deltas. Monotone + correctly ranked. Snapshot green 19/19.
  Wear-headroom probe (armor_headroom.py): 0/20 early game (honest: inert
  early, value is mid-game armor drops).
- **FLOOR-ROLE UPLIFT launched** (operator flagship, wiki-fed NH-E13): KB
  expanded (Tourist + Cleric pages; Healer present) — provenance:wiki cards
  in DOCTRINE_CARDS_s5.md. role_seeds.py stratified harness on the merged
  census (Healer 83 / Tourist 65 / Priest 45 / Priestess 30).
- **NH-E34** (community/forum corpus) + **NH-E35** (ttyrec demonstration:
  35a world-model / 35b strategy / 35c discovery) REGISTERED (design folders
  with READMEs + ledger rows).

## Session-6 priority queue (ordered by expected mean-lift)
1. **FLOOR-ROLE UPLIFT execution (operator's flagship — where +0.4-0.6 lives).**
   HEALER FIRST (freq × headroom max). Build a role-profile selector (read
   role at episode start → apply the role's playbook: goal weights /
   aggression / cast-heal / item doctrine), behind a flag, per DOCTRINE_
   CARDS_s5.md. Wire the Healer wiki profile (cast-heal-to-survive + stethoscope
   + avoid-melee/pacifist). Flag-off regression. Then a ROLE-STRATIFIED dev
   block: `role_seeds.py Healer 20 --csv` → 20 Healer seeds, ref vs profile;
   proximal KPI = Healer mean + survival@D5; REPORT A PER-ROLE MEAN TABLE.
   Track WIKI-ATTRIBUTABLE Δ (Healer 2.15→? = the controlled "does the wiki
   help" number). Then Tourist (caution+dart+item), then Priest (BUC+#turn).
2. **THROW_DISENGAGE paired block** (pre-registered, RUN_LOG S5-4): ref=standing
   vs test=+NH_CRISIS_THROW; seeds = e6 v2 THROW-win (707,714,727,732) + fresh;
   proximal KPI = TRASH-death rate; criteria: throw fires>0, delta not clearly
   negative, TRASH-death class not worse; drop-if-unclear. The general survival
   lever that helps floor roles MOST — measure its floor-role-specific Δ.
3. **COVERAGE → 70%** (criterion i, long pole): the s5 evidence is ready to
   FILL cells — KITE/THROW/STAIRS × TRASH (all 9 residual resolved, 20/20
   TRASH avoidable) + ARMOR × TRASH/MELEE+ (defense model now first-class).
   Update coverage_matrix.py; mind PROVISIONAL=half discipline.
4. **NH-E35a WORLD-MODEL VALIDATION** (cheapest+highest-value of the ttyrec
   set; flag coordinator before heavy download): ttyrec parser → replay
   expert ascension games through the model → c2_violations on real deep-game
   transitions. Extends "0/233k" to millions across the full game.
5. **Gym class expansion**: run e6_solve_v2 on MELEE+/STARV/SPIDANT batches
   (the v2 menu generalizes; STARV wants EAT/corpse alternatives added).

## Standing / gotchas that bit this session
- **E21b 4-arm ablation BLIND arm** still needs a FRESH-CONTEXT instance — do
  NOT run it yourself (partially-informed); FLAG THE COORDINATOR to spawn a
  quarantined instance. Not reached this session (floor-role directive took
  priority).
- e6_solve v2 replays the whole prefix per line — cheap here (TRASH prefixes
  573-2757 steps, 4-80s/scenario) but MELEE+/deep scenarios will be slower;
  run big batches in background / on the VM.
- Coverage PROVISIONAL = role-scoped/below-bar counts half; don't inflate.
- The wiki cards are HYPOTHESES until role-stratified-validated (and NH-E35b
  audits them against winners) — don't ship a floor-role profile on the card
  alone; the paired block is the gate.
- Renderer standard = v3 (render_v3.py / render_c2.py; +14 panel pad, my0+28
  legend clearance). MILESTONE flags → coordinator emails operator.

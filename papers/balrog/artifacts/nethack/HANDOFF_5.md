# HANDOFF_5 — Phase L session 4 → session 5

MODEL: claude-opus-4-8[1m] (max thinking) wrote this — session 4, the FIRST
opus session (Fable 5 sessions 1-3, then cap). Runtime identity VERIFIED at
session open (system-prompt id = claude-opus-4-8[1m], self-report matches);
NO label/runtime mismatch (the s3 gotcha did not recur). All s4 artifacts
stamped claude-opus-4-8[1m].

## ENVIRONMENT NOTE (read first — cost me time, will cost you time)

NLE runs in this sandbox ONLY via the vendored `pylib/nle` (balrog_nle
0.9.0, compiled .so). A bare `import nle` FAILS — every run needs
`PYTHONPATH=pylib` (the scripts that add pylib to sys.path themselves —
nh_branch, nh_sheet — work either way; dev_run/pair_rest need the env var).
Snapshot suite + determinism gate are green here, so the FULL engine works.

Episodes are SLOW here (agent decision rate ~12-50 steps/s; perception/BFS
cost grows with explored-map size). Dying TRASH episodes are fast (<600
steps, ~10-20s); SURVIVING episodes run to the step cap and can take
minutes. Seed 701 is a pathological stall (>2min CPU at cap 1500 without
finishing) — put it LAST in any batch. Use a step cap for lever probes whose
proximal KPI is early deaths; a full 40-ep 50000-cap block is a multi-hour
run here — budget for it or run it on the VM.

## What landed this session (all stamped opus-4.8[1m])

- **★ ARMOR AC-COLUMN BUG FIXED** (nh_sheet.build_armor_table): read Cost/
  Weight not AC; **33/66 rows wrong** (leather jacket 10→1, cloak of
  protection 10→3, helmet 10→1; heavy armor right by luck). Verified vs
  frozen KB; parse col-4; table rebuilt. Weapon table checked CLEAN.
  Snapshot fixture **A7** added → suite 19/19 green. This was the
  prerequisite for any real ARMOR_DOCTRINE.
- **THE KPI TREE** (operator directive): KPI_TREE.md — DAG + per-node
  instrument/value/trend, backfilled from c2_cache (max-depth 6.0, survival@D8
  32.3%, descent 139 t/lvl, AC 7.1, die-at-35%HP) + ledger. New rule: every
  lever declares a PROXIMAL KPI at pre-registration; per-block KPI-DASH line.
- **WIELD_DOCTRINE** (PROVISIONAL, role-scoped): sheet offense headroom
  2/10 probes, BOTH Rangers under-firing (+40-50% dpt); melee roles inert.
  Coverage **23.2%→27.3%**. Cards in DOCTRINE_CARDS_s4.md.
- **REST/DISENGAGE lever** (first solve-loop-sourced lever): diagnosed as a
  threshold tune of the P3 crisis-flee (hardcoded 0.28/×2.0; agents die at
  ~35% HP, above the flee floor). Knobs NH_CRISIS_HP/NH_CRISIS_EXCH added,
  defaults = prior constants (flag-off regression PASS, seed 706 bit-identical).
  Paired block REF(0.28/2.0) vs TEST(0.40/1.5) — VERDICT in RUN_LOG (grep
  "REST-LEVER VERDICT"); results/rest_lever_{ref,test}.json.

## Open / session-5 queue

1. **REST lever** — if the s4 paired block was inconclusive/partial (slow
   env), rerun on the VM at full cap + more fresh controls; apply drop rule
   on the proximal KPI (TRASH-death rate) primarily. If it shipped, add
   NH_CRISIS_HP/EXCH to the standing config + DEV-B4/B5 clock.
2. **ARMOR_DOCTRINE (P3)** — prerequisite (AC table) now correct. BUILD:
   fold AC into RR via monster-hit prob (effective_incoming_dpt = band_dpt ×
   P(hit|AC); source to-hit from KB d20-vs-10+AC). Then counterfactual_power
   yields real armor delta_rr → fill ARMOR × TRASH/MELEE+ coverage cells.
3. **Coverage toward 70%** (criterion i, long pole): KITE/ZAP × TRASH next
   (top death-mass). KITE via e6_solve; ZAP probe-first (RAY_BOUNCE guard).
4. **Gym class expansion**: e6_solve on MELEE+/STARV/SPIDANT batches + the
   v2 alternatives menu (kite/throw/stairs-escape + in-model MC before any
   UNWINNABLE stamp).
5. **E21b multi-seed + 4-arm ablation** — the ablation's BLIND arm needs a
   FRESH-CONTEXT instance (flag the coordinator to spawn it; do NOT run it
   yourself — you are partially informed). E21b engine is separate from NLE
   (python tiles) — check its runnability early.
6. WIELD wire-in: make the agent actually switch to its best sheet option
   (Ranger launcher adoption) behind a flag; paired block; proximal KPI OFFENSE.

## Standing reminders that bit this session

- Knobs are read at IMPORT time (module-level env.get) — set env BEFORE
  importing nh_agent; run each condition as its own process.
- Same-seed rerun of the deterministic agent is bit-identical — flag-off
  regression uses same seeds (correct); paired blocks compare conditions on
  same seeds.
- Coverage-matrix PROVISIONAL = role-scoped/below-bar evidence, counts half.
  Don't inflate the % with weakly-grounded fills (WIELD was kept conservative).
- Push to FORK only (worktree work/wt-fable-nethack, branch aleph/fable-nethack,
  remote fork = collinquome/openworld). The flat work/fable_nethack/ is an
  UNTRACKED mirror; edits happen there (has results/), then mirror code+
  artifacts to the worktree and commit/push from it.

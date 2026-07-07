# HANDOFF_4 — Phase L session 3 → session 4 (clean close, not a cap-death)

MODEL: Fable 5 (max reasoning) wrote this; sessions 1-3 ALL Fable 5 —
the HANDOFF_3 opus-fallback line was corrected in PHASE_L_REPORT's
roster (cap reset before s3 launched; roster is single-model).

Read order: (1) this; (2) PHASE_L_REPORT.md session-3 sections (verdicts
+ scoreboard + session-4 queue — canonical); (3) docs/NETHACK_PROGRAM.md
(NEW s3 rows/updates: NH-E28, core-loop statement, DEV-B2/B3, SHEET,
SUITE-V, E21b-LIVE, MATRIX, E6-HARVEST, CAST-HUNGER shipped, NH-E15
shipped); (4) HANDOFF_2/3 for substrate.

## State you inherit (no in-flight verdicts this time — everything landed)

- STANDING CONFIG: NH_FOOD2,PRAYFIX,LOS,TOPO,GUARD,CAST + NH_CASTHUNGER
  + NH_E15 (both shipped s3 on pre-registered gates; E15's honest
  caveat: progression-unclear, shipped as robustness lever, partially
  inert — 7/22 fired-eps action-identical; rework path = goal-market).
- EXIT CRITERIA: (iii) MET (DEV-B2/B3 5%→5%), (iv) MET (snapshot_suite
  18/18 — RUN IT at session open, it is the regression gate now),
  (v) MET+holding (0/233k s3). OPEN: (i) 23.2%/70% — the long pole;
  (ii) TRASH 20/118 adjudicated, other 4 classes untouched.
- NEW INSTRUMENTS s3: nh_sheet.py (character sheet: PI/TI/RR +
  counterfactual_power; tables results/weapon_table.json,
  armor_table.json, depth_threat.json — damage-mass-weighted bands);
  e6_solve.py (deterministic branch backtesting of logged deaths —
  ORIG control must reproduce death; MISPLAYED/UNRESOLVED semantics,
  UNWINNABLE reserved for v2 menu + MC); snapshot_suite.py;
  render_live_v2.py (side-panel reel STANDARD — operator directive).
- E21b: T1/T5/T6 all live-won (s0). T5 result is a headline: the T5/T6
  charm pair is a DEFEASIBILITY test (never-pick-up as rule fails T5,
  as hypothesis passes both). Probe records in engine results/e21b_live/.
- GIF EMAIL FLAGS pending coordinator action: e21b_v2_T1/T5/T6 GIFs.
- DEV seeds burned this session: 740-779 (DEV-B3). 780-799 still fresh.
- Session-4 queue: PHASE_L_REPORT §Session-4 queue (REST-lever paired
  block first — it is the first solve-loop-sourced lever; then
  WIELD/ARMOR on sheet deltas + readiness wire-in w/ flag-off
  regression; solve-loop v2 menu; E21b multi-seed + ablation w/
  fresh-context blind instance; zap probe-first; E25a open-mode).

## Standing-rules reminders that bit or nearly bit this session

- Terminal transition frames ZERO blstats (R_TERMINAL_ZERO) — death
  time/hp must read the last NONZERO row (e6_solve bug, fixed).
- Transitions rows: first row is initial-obs (no "action" key).
- Branch.step returns a BRIEF; live blstats are on branch.obs.
- Ammo weapons carry their LAUNCHER's skill in the KB table (arrows →
  "bow") — classify ammo by name before launcher-by-skill (nh_sheet).
- Same-seed rerun of the deterministic agent is bit-identical: cadence
  block 2/2 MUST use fresh seeds; structural-identity adoption (DEV-B2
  pattern) is registered and legitimate when a flag is provably inert
  without a trigger event — cite gate line numbers in the RUN_LOG.
- Coverage-matrix statuses live IN coverage_matrix.py (edit + rerun;
  auto-generated numbers rule still applies to the printed table).

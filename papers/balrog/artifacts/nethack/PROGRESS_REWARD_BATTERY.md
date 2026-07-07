# NH-E29–E33 — Nested-KPI / Progress-Reward Battery (design doc)

MODEL: claude-opus-4-8[1m] (max thinking), Phase L session 4. Operator
directive 2026-07-07 (via coordinator). STATUS: DESIGN + REGISTRATION only —
execution scheduled, flag the coordinator before any heavy run.

## The guard (state prominently, everywhere)

Potential-based shaping and all dense/intermediate reward terms are a
**dev/training-time tool ONLY**. The FROZEN Phase-E evaluations (Arm A n=100
seeds 6000-6099; Arm B n=25 seeds 7000-7024) stay **pure terminal-metric**
(BALROG progression) — shaping never enters the scored objective. Potential-
based shaping is provably policy-invariant w.r.t. the true goal (Ng et al.
1999): reward' = reward + γΦ(s') − Φ(s) leaves the optimal policy unchanged,
so it adds signal without corrupting the objective. Every reward config is
BACKTESTED against the 275+ episode corpus before any live block (the
PROPOSE→COMPILE→BACKTEST→DEPLOY core loop). This is the anti-reward-hacking
discipline.

## NH-E29 — POTENTIAL-BASED PROGRESS REWARD

- Φ(s) = expected-progress-to-goal proxy. Candidates to compare:
  (a) max-depth-reached; (b) depth + readiness-ratio (char sheet RR);
  (c) a learned/coded distance-to-descent (steps-to-stairs from the dossier).
- Intermediate reward r_shape = γΦ(s') − Φ(s) (policy-invariant).
- EXPERIMENT: does shaped dense reward improve the LEARNING RATE of the
  bandit/strategy-selection layers (NH-E23) vs sparse terminal-only? Measure
  on dev: episodes-to-converge, regret curve, final dev mean.
- PRE-REG PREDICTION P1: (b) depth+RR shapes fastest (RR is the readiness
  signal deaths correlate with); (a) max-depth alone is too coarse; all three
  reach the SAME optimal policy (invariance check — if they don't, a bug).

## NH-E30 — GOOD-STUFF / BAD-STUFF LEDGER (the KPI tree's reward layer)

- GOOD events (signed +Δ on a KPI-tree node): depth gained, xp gained, AC
  improved, food secured, first-defeated (FIRSTS), socket/level closed,
  verified-loop found (RENEWABLE).
- BAD events (signed −Δ): avoidable damage, hunger tick toward Weak, stall
  turns, retreat / lost-depth, novel-threat contact.
- EXPERIMENT (FREE, historical): regress terminal progression on event
  counts over the 275+ corpus → which signals are PREDICTIVE of final score.
  Predictive ones become reward terms; non-predictive = vanity metrics,
  dropped. Report standardized coefficients + held-out R².
- PRE-REG PREDICTION P2: depth-gained + avoidable-damage (neg) dominate;
  xp and "first-defeated" are weakly predictive (correlated with depth);
  stall-turns predictive-negative. (Falsifiable against the regression.)

## NH-E31 — CLOSER-TO-GOAL ESTIMATOR V(s)

- V(s) ≈ P(reach depth D+k | s), fit by survival analysis over the logged
  transition corpus (Cox / discrete-time hazard on state features: depth,
  RR, hp-frac, hunger, xp, AC).
- Rendered LIVE in the HUD as a progress bar toward expected-depth (feeds
  NH-E33 / the v3 renderer HUD).
- EXPERIMENT: (i) calibration — predicted vs realized reach-rate on a
  held-out split (reliability diagram); (ii) does acting to maximize V beat
  the current planner on dev?
- PRE-REG PREDICTION P3: V(s) is calibrated within ±10% on held-out; greedy-V
  ties the planner on mean but reduces death variance (it is a smoothed
  readiness signal, not a new capability).

## NH-E32 — REWARD-TERM ABLATION (backtest-gated)

- With E30's candidate terms, run PROPOSE→COMPILE→BACKTEST: each reward
  configuration is backtested against the corpus BEFORE any live block —
  historical replay asks "would this reward have RANKED the good (high-final-
  score) episodes above the bad ones?" (rank correlation of Σreward vs final
  progression). Ship only configs that pass the backtest.
- PRE-REG PREDICTION P4: the minimal 2-term config (depth-gain + avoidable-
  dmg) backtests within noise of the full config → parsimony wins; extra
  terms add variance not rank-signal.

## NH-E33 — MULTI-HORIZON KPI DASHBOARD

- The KPI tree (KPI_TREE.md) rendered as a live 3-tier readout: GOAL
  (progression) / DRIVERS (depth, offense, defense, sustain, nav) /
  PERFORMANCE (avoidable-dmg, readiness, verb-use), trend arrows, appended
  to every block close (the KPI-DASH line, already live in RUN_LOG s4) AND
  shown in a corner of the reel HUD (v3 renderer).
- No experiment — instrumentation. Ties E29-E32's signals into one view.
- PRE-REG: the DRIVERS tier moves 1-2 blocks before the GOAL proxy on a
  working lever (the KPI-tree thesis; measurable once ≥3 levers ship).

## Sequencing

E30 first (free historical regression — tells us WHICH signals matter, gates
everything else) → E31 (V(s) from the same corpus) → E29 (shaping with the
validated Φ) → E32 (ablation, backtest-gated) → E33 (dashboard, continuous).
Design-only until the coordinator flags execution.

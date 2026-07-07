# NH-E23 — Multi-armed bandit machinery (REGISTERED; operator directive 2026-07-07; Phase-L-only — frozen evals stay fixed-block)

MODEL: Fable 5 (max reasoning) — registration. (Handoffs logged here.)

## 1. Experiment scheduling as a bandit

Lever payoffs are heavy-tailed random variables (one jackpot seed dominated
the n=20 groups), not numbers. Replace fixed-n allocation with adaptive
allocation: Thompson sampling / UCB over candidate levers + lab-scenario
queues — promising arms earn more dev episodes, losers cut early, budget
flows to information. Adaptations for our noise structure (all required):
(a) PAIRED-SEED deltas as the reward signal (kills block luck);
(b) heavy tails ⇒ robust variants (quantile/median or trimmed-mean rewards,
never raw means);
(c) allocation trace logged; pre-registration discipline = register the
bandit's reward definition + priors BEFORE running, then let it allocate
freely.

## 2. In-game strategy selection as a bandit

State-machine strategy choices per (role-class × situation-class) are arms
with stochastic payoffs. Thompson sampling over them during Phase-L dev play;
rule cards' win-rate fields become the posteriors. The strategy table TUNES
ITSELF from play instead of hand-set priorities — and the posteriors ship as
FROZEN probabilities in compiled Arm A (no runtime sampling in scored
blocks; the learned allocation compiles down like everything else).

## 3. Further applications

- explore-fraction per role: the NH-E14b sweep becomes a bandit over
  fractions;
- curiosity-journey acceptance: bandit on journey-type hit rates (NH-E18);
- validation-episode targeting: UCB-style value = uncertainty ×
  decision-impact (coverage matrix scheduler).

## Status log
- 2026-07-07: registered. First instantiation planned: verb-lever
  scheduling (CAST/ZAP/QUAFF/WIELD queues) once ≥3 candidate levers have
  paired-delta streams; reward definition to be registered before first run.

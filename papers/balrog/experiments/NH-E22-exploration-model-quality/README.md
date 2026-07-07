# NH-E22 — Exploration → model quality (pre-registered hypothesis; operator directive 2026-07-07)

MODEL: Fable 5 (max reasoning) — registration. (Handoffs logged here.)

**Pre-registered hypothesis: EXPLORATION PRODUCES A MEASURABLY BETTER WORLD
MODEL.** Plot model quality against exploration investment.

## 1. Model-quality metrics (evaluated on HELD-OUT play, never the exploration data itself)

(a) **violation rate** — predictions outside possibility sets per 1k steps;
(b) **SHARPNESS** — possibility-set tightness (a model predicting "anything"
is never violated but knows nothing; mean set size / predictive entropy;
quality = low violations AND tight sets);
(c) **pinned-mechanic coverage** — fraction of the world's mechanic
inventory pinned (discovery-loop output);
(d) **counterfactual reliability** — gym-replay agreement rate (model's
branch prediction vs real-env branch outcome).

## 2. The curve

Matched agents at different exploration budgets/policies (none / passive /
active hypothesis-driven discovery loop); plot model quality vs exploration
steps invested — in NH-E21b worlds (generator KNOWS ground-truth mechanics ⇒
EXACT model-vs-truth scoring — the cleanest version of this measurement in
the program) and in NetHack dev (approximated via held-out violation rate).

**Pre-registered predictions:** (i) active hypothesis-driven exploration
beats passive at equal budget (the discovery loop is worth its cost);
(ii) quality saturates — the diminishing-returns knee IS the optimal explore
budget, which then feeds the explore/exploit weights empirically (NH-E14b).

## 3. The mediation chain (the paper's causal diagram if it holds)

exploration → model quality → decision quality (avoidable damage) →
survival → score. Measure every link on the same runs; if the chain holds
statistically, exploration is upstream of everything.

## Status log
- 2026-07-07: registered, pre-registered predictions recorded. Runs after
  E21b engine + NetHack dev instrumentation both exist.

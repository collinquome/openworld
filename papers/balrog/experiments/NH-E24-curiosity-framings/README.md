# NH-E24 — Curiosity framings compared (REGISTERED; operator directives 2026-07-07 ×2)

MODEL: Fable 5 (max reasoning) — registration. (Handoffs logged here.)
ID note: the operator's directive said "register NH-E22"; NH-E22 was already
taken by exploration→model-quality (registered earlier the same day), so
this is filed as NH-E24, alias "curiosity-framings". Both experiments
cross-reference.

**Design principle (operator amendment, controls the defaults): DON'T FORCE
INTUITION THROUGH A FORMULA BOTTLENECK.** Intuition is hard to quantify by
nature; modeling it risks Goodhart (optimizing the proxy instead of the
judgment). Therefore FELT-SENSE is the DEFAULT curiosity/exploration engine
for the intuition layer, effective now; the formula is a BASELINE arm + an
explanation/logging layer — never a gate on intuition's choices. The
epistemics that make this safe: we never need to model intuition to
EVALUATE it — realized outcomes (info gain, sockets closed, score) are
measurable regardless of how the choice was made. Judge the layer by its
fruits; leave its internals unmodeled. The formula must EARN its way in by
beating felt-sense, not vice versa.

## Arms (same worlds/budgets)

- **ARM 1 — FORMULA (baseline):** curiosity_value = α·novelty +
  β·dot-completion, with the calibration loop (spec in NH-E18 §7).
- **ARM 2 — FELT-SENSE (default engine):** no formula — the intuition layer
  sees the full CONTEXT_SPEC package and picks "what feels like the right
  next thing to explore," with a one-line why. Choice + stated reason
  logged.
- **ARM 3 — BASELINES:** nearest-frontier (pure spatial), random-frontier.
- optional ARM 4 — HYBRID (felt-sense chooses, formula as tiebreak/veto) if
  arms 1–3 split.

## Metrics (per arm)

Realized information gain per exploration step (mechanics pinned, sockets
closed, sharpness delta); downstream model quality (NH-E22 metrics) + score.

## Pre-registered both ways (honest)

The formula may win (explicit socket-tracking beats vibes) OR felt-sense may
win (the LLM's implicit valuation over full context captures signal no
hand-built scalar does — in which case the formula was a lossy compilation
of intuition and becomes logging/explanation only). Whichever wins becomes
the goal market's curiosity engine — decided by data, not design taste.

**Write-up note:** this is a mini-instance of the program's deepest question
— compiled mechanism vs live intuition — and is reported as such.

## Status log
- 2026-07-07: registered; felt-sense set as default engine per operator
  amendment.

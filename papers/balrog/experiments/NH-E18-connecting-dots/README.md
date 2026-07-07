# NH-E18 — Connecting-dots memory (REGISTERED, Phase L; operator directive 2026-07-07 — LEADS the Phase-L priority order together with the perceptor backlog)

MODEL: Fable 5 (max reasoning) — design + registration. (Handoffs logged here if a successor model continues this experiment.)

**Core insight (operator):** memory serves TWO functions. (1) Avoiding death —
hazard ledgers, dossiers: we have this, it is code-shaped. (2) CONNECTING DOTS —
relational inference over remembered observations, where facts jointly imply
something neither implies alone: we DON'T have this, and it requires the LLM.

## 1. Memory substrate (code; ships into both arms)

Unify the episode's observations into ONE queryable store: level dossier +
item sightings WITH unidentified appearances + prices seen (shop offer/asking
events) + monster encounters with outcomes + events timeline. Code records
everything; the structure is designed for retrieval (by item appearance, by
species, by level, by event type). Within-episode only (BALROG protocol:
nothing persists into a scored episode from outside it); serialized into
trajectories for offline analysis and between-episode reflection.

## 2. LLM dot-connector (dev/gym + Arm B consultation points + between-episode reflection)

The LLM reads the memory store and proposes RELATIONAL HYPOTHESES. Canonical
NetHack targets:
- **PRICE-ID:** offered/asking price + item class → probable identity set
  (wiki documents the price tables — NH-E13 KB cross-reference makes each
  inference concrete and checkable).
- **Altar drop → BUC identification** (message grammar on drop).
- **"Monster X didn't attack while adjacent → peaceful/passive class"**.
- **Level features → branch recognition** (Mines/Sokoban signatures).
- **Key/lock-class bindings** where they exist.

Each proposed relation = a rule card (provenance: **inferred**) validated via
gym/branch-probe (NH-E16 component 2) before ANY policy trust. Validated
relations compile to code for Arm A; Arm B may also run them live.

## 3. The two-loop demonstration (write-up angle, operator's)

Code CANNOT do step 2 — pattern-matching across heterogeneous remembered facts
is the LLM's comparative advantage; executing a validated relation cheaply and
reliably every step is code's. NH-E18 is the cleanest demonstration in the
program that BOTH loops are necessary. The writeup treats this as its thesis.

## 4. Metrics

- relations proposed / validated / refuted per episode (and per reflection pass)
- score + survival impact of validated relations (price-ID alone should
  measurably improve item decisions — paired dev validation like any lever)
- dots-connected count surfaced in GIF banners
  (e.g. `INFERRED: 60gp potion ≈ healing [price-ID]`)

## 5. Hypothesis-driven exploration objectives (operator refinement, closes the E18↔E11 loop)

> **"The LLM decides WHERE to go; the procedures decide HOW to get there.
> Strategist chooses destinations, navigator drives."** — operator, 2026-07-07

- **REVALUATION TRIGGER:** whenever new capability or knowledge lands (item
  acquired: key/pick-axe/wand identified; relation validated; skill unlocked),
  the dot-connector RE-SCANS the level dossiers for revalued opportunities:
  "locked door on D1 + key now held → that room is reachable", "unreachable
  vault + pick-axe → diggable", "unidentified wand + now-known zap semantics →
  test target".
- **CURIOSITY OBJECTIVE contract:** {hypothesis ("I wonder if..."), target
  location, expected value (what might be there × prior), cost (risk-costed
  travel per the NH-E11 navigator), abort conditions} — priced in the goal
  market against descent value (the explore/exploit call is the LLM's;
  execution and per-step replanning over dossier hazards is the navigator's
  risk-costed A*).
- **LOGGING:** hypothesis→journey→outcome triples. Metric: **curiosity hit
  rate** (journey found something valuable vs wasted trip + its cost) — the
  empirical explore/exploit curve for backtracking; feeds the goal market's
  future pricing of curiosity.
- **RENDER:** curiosity journeys get their own GIF banner, e.g.
  `CURIOSITY: returning to D1 locked room [key acquired]`.

## Dependencies / siblings

Perceptor backlog feeds the substrate (operator reweight, same directive):
shop/altar/fountain/special-room detectors, monster-state perceptor
(peaceful/hostile/fleeing/asleep), item-appearance tracker (unidentified
appearance + observed prices + contexts), branch/level-feature recognition.
NH-E13 KB supplies the reference tables; NH-E16 supplies the validation
instrument; NH-E11 dossier is the substrate's spatial spine.

## Status log
- 2026-07-07: registered (operator directive), folder created.

## 6. Question-driven retrieval (operator addition, shared with NH-E21)

Goal-directed mode alongside passive dot-connecting: planning hits a
constraint → the intuition layer formulates an explicit QUESTION ("How can I
get below 20 health?") → runs it as a retrieval query against the memory
store (FTS5 over observations + dossiers + relations) → retrieved memory
answers the question → plan completes. Full chain logged (constraint →
question → hits → answer → plan) + rendered in GIF banners. Both modes
measured; chain rate is a core NH-E21 metric.

## 7. CURIOSITY REWARD, operationalized (operator spec 2026-07-07)

`curiosity_value(target) = α·NOVELTY + β·DOT_COMPLETION`, both from
existing ledgers:

- **NOVELTY** (what the model doesn't know): unpinned mechanics nearby,
  unseen entity/tile/verb-context classes, reachable coverage-matrix
  untested cells, high possibility-set-entropy regions (widest predictions
  = most to learn). Queryable from rule cards + matrix + the model itself.
- **DOT-COMPLETION** (connecting new dots): the memory store's OPEN
  SOCKETS — unanswered questions, half-completed relations (door-condition
  known but no matching capability; item seen but unpriced; monster
  encountered but untyped). Each open socket projects a VALUE FIELD over
  the world: any target that might complete it scores. Open questions
  literally price exploration targets — question-driven retrieval,
  inverted.
- **CALIBRATION LOOP:** after each curiosity journey, log REALIZED info
  gain (mechanics pinned, relations completed, sharpness delta, questions
  answered) vs predicted curiosity value; the predicted-vs-realized curve
  calibrates α/β over time, and NH-E23 bandits allocate among curiosity
  targets using these as rewards. A curiosity estimator that stays
  calibrated is the answer to "explore rewards are hard to model": model
  them, then check the model.
- **Report artifact:** curiosity calibration curve + top realized-gain
  journeys ("CURIOSITY: unexplored NE room [2 open sockets] → FOUND: wand
  → SOCKET CLOSED: ranged option acquired").

**AMENDMENT (operator, same day): §7's formula is DEMOTED to a baseline +
explanation/logging layer. FELT-SENSE (intuition picks over the full context
package, one-line why, choice logged) is the DEFAULT curiosity engine.
See NH-E24 (curiosity framings compared) — the formula must earn its way in.**

# NH-E28 — THE GOAL-INFERENCE BRIDGE

MODEL: Fable 5 (max reasoning), Phase L session 3 (registered on operator
directive, 2026-07-07 s3). STATUS: registered, DESIGN-ONLY — execution
post-Phase-E or as capacity allows; **coordinator flag REQUIRED before any
heavy execution** (operator gate, verbatim).

## The wall this is aimed at

Jim's E102–E104 trilogy (repo `experiments/e102_goal_search.py`,
`e103_hypothesis_solver.py`, `e104_bayesian_subworld.py`) documented the
one place the program's recipe has failed: on ARC-AGI-3, **perfect (or
near-perfect verified) world models plus three principled goal-discovery
attacks all failed** — 0/9, 0/3, 0/3 across the attacks. E103's diagnosis:
**wins are PROCEDURES, not reachable states.** A hypothesis space of
state-scored goal functions (goal-conditioned MPC through the world model,
score = predicate over the reached state) optimizes the wrong object when
the win condition is "do X then Y within Z", "visit in this order", or any
condition over the *path*, because every state-shaped hypothesis assigns
the same score to procedure-distinguished trajectories.

This experiment is the program's flagship follow-up after NetHack Phase E:
the same recipe (perception / memory / intuition / procedure + paired
validation + pre-registration), aimed at the wall.

## Three instruments Jim's attacks lacked

### 1. Procedure-native hypothesis space (INTUITION + PROCEDURE layers)

Our objective stacks and playbooks already ARE procedure representations.
Hypothesize goals as **procedure sketches** — ordered, typed steps with
holes:

    SKETCH := [step_1, ..., step_k] + constraints
    step   := DO(verb, object-hole) | REACH(zone-hole) | AVOID(class-hole)
              | WITHIN(n-steps-of, step_i) | ORDER(step_i < step_j)
              | NEVER(predicate) | HOLD(predicate, duration-hole)

Scoring a sketch = alignment between the executed trajectory's event
stream (the E18 store's events timeline is exactly this) and the sketch's
step sequence — a PATH object, not a state predicate. The intuition layer
proposes sketches narratively from the full context package (E103's
machinery was formula-scored, not narrative); the procedure layer compiles
sketches to trackable monitors.

### 2. The training ladder with ground truth (extends The Game / NH-E21b)

Extend the E21b grammar (`engine/templates.py`, `grammar.py`) to generate
**OPAQUE-WIN worlds**: win conditions that are procedures, where WE KNOW
the answer, graded by inference difficulty. The opacity ladder:

| grade | win condition class | example | why it's harder |
|---|---|---|---|
| O0 | visible state goal | reach the marked goal tile | control; state-shaped inference suffices |
| O1 | invisible state goal | stand on an unmarked tile / carry item X anywhere | reward-on-state still identifies it |
| O2 | ordered pair | interact(A) THEN enter(B); reversed order = no win | final state identical across orderings — first procedure-only grade |
| O3 | ordered k-visit | visit zones C→A→B (k=3–4), no state trace of order | hypothesis space explodes combinatorially with k |
| O4 | timing/window | do X within Z steps of Y; parity/holding conditions | requires counting, not just ordering |
| O5 | negative/conditional procedure | win requires NEVER picking up class-c (T6's trap as win rule); or IF hazard triggered THEN cleanup step required | absence-of-event evidence; conditionals double the sketch space |
| O6 | latent-counter procedure | procedure over hidden counters, only score/win events observable, plus distractor reward events | E103-hard by construction — the measured wall |

Each generated world ships with its ground-truth sketch (auto-graded, the
E21b pattern), ≥3 seeds per template, and a per-grade batch. Deliverable
metric: **inference success vs opacity grade** — the wall measured on a
dial for the first time. Then transfer the method to the real walled
ARC-3 games (harness in repo: `experiments/e102/e103` + `papers/arc-3`).

### 3. Cross-run induction + memory (MEMORY layer)

Goal hypotheses accumulate evidence ACROSS attempts (Jim's attacks were
largely within-run): which procedure fragments correlate with score/reward
events over the run history; the E18 dot-connector runs over near-win
patterns between episodes; sketch posteriors persist and re-rank the next
run's pursuit order. SAMPLE-10-PICK-1 applies at sketch-proposal moments
(log the rejected 9).

### E97 primitive (wired in)

Once any win IS found, induce the objective as **verified code**
(`experiments/e97_reward_induction.py` pattern): one win converts
inference into verification — the induced win-rule is then replay-checked
against every logged trajectory (wins score 1, losses 0) before it is
trusted.

## Pre-registered predictions (falsifiable, both directions)

P1 (wall replication): a state-predicate baseline arm (E102/E103
surrogate: state-scored hypotheses + MPC) solves O0–O1 and fails from O2
up — reproducing the ARC-3 wall inside the ladder. If it does NOT fail at
O2+, the diagnosis "wins are procedures" is wrong or the ladder is leaky.

P2 (instrument 1+3 effect): procedure-native sketches + cross-run
evidence extend solved grades through O3 and partially O4–O5 (order
inference from event streams is the designed sweet spot; counting and
absence-evidence are expected to be harder).

P3 (intuition delta): the narrative-proposal arm beats a
grammar-enumerated sketch arm at equal budget on O4–O6 specifically
(compositional/conditional sketches are where enumeration explodes) — the
E21b Arm-A/Arm-B claim transposed to goal inference.

P4 (E97 conversion): at any grade where a win is stumbled into at least
once, induced-and-verified win rules reach ~100% identification even when
prospective inference failed — inference and verification are different
problems and the ladder should show the gap explicitly.

P5 (transfer): ladder-trained method attempted on the real walled ARC-3
games; pre-registered honestly BOTH directions — transfer may fail (their
opacity may exceed O6 or be off-ladder), and a documented transfer failure
localizes the residual gap.

## Protocol notes

- Dev/gym discipline inherited: ladder worlds are generated (no scored
  NetHack seeds involved); ARC-3 transfer uses Jim's existing harness and
  respects its eval hygiene.
- Every arm pre-registers criteria in RUN_LOG before launch; drop-if-
  unclear applies to method components exactly as for NetHack levers.
- Model provenance stamped per artifact; consultations logged verbatim.
- Execution sequencing: post-Phase-E (or as capacity allows), and the
  operator/coordinator flag gate above is a hard precondition for any
  compute-heavy arm.

## The core loop this experiment instantiates (operator, s3)

NH-E28 is the sharpest instance of the program's architecture statement
(docs/NETHACK_PROGRAM.md §"The core loop"): **PROPOSE → COMPILE →
BACKTEST → DEPLOY.**

- PROPOSE: intuition emits goal hypotheses as procedure sketches (§instrument 1).
- COMPILE: every sketch gets a code twin immediately — an executable
  reward-checker over event streams (the hypothesis IS a candidate
  verifier; E97 goal-as-code, ARC-3 lesson 5).
- BACKTEST: the channel his attacks lacked — checkers run against
  CROSS-RUN history first (which procedure fragments correlate with
  already-logged score/reward/near-win events; nearly free), then model
  playouts, then ladder worlds. A hypothesis that cannot postdict the
  logged reward events never spends live compute.
- DEPLOY: survivors drive goal-directed MPC; a single live win converts
  the checker from hypothesis to verified objective (E97), after which
  it is replay-validated against the full trajectory corpus.

Pre-registered prediction P6 (added with this section): on the opacity
ladder, backtest-filtered sketch sets reach the same solved grade as
unfiltered sets at a fraction of the live-run budget (the filter's value
is efficiency and safety, not reachability); if filtered sets solve
LOWER grades, the backtest channel is over-pruning true hypotheses —
report either way.

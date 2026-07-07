# NH-E18 reflection pass #1 — dev seed 990 (Wizard, NH_CAST config, 8000-step cap)

MODEL: Fable 5 (max reasoning) — this IS the intuition layer running a
between-episode reflection over the CONTEXT_SPEC package (traj:
results/trajectories/dev__ep990.json, store serialized within; package
rendered by nh_store.ctx_package). Logged per the consultation contract.

## Relations proposed (provenance: inferred; NONE trusted until gym/probe-validated)

**R1 — REPEATED-LAYOUT SEED (validated within-episode, needs cross-seed
scoping).** Observations connected: belief maps of D2 and D3 are 17/21
rows identical; stair transit cells identical three descents in a row
([63,4] → [14,15] for D1→2, D2→3, D3→4); RAW tty confirms (not a belief
artifact). Joint implication neither observation carries alone: in this
seed the generator repeats level layouts, so LEVEL N's map PREDICTS level
N+1's stair location. Test the relation would have passed: it predicts
D3→D4 transit at [63,4]→[14,15] — which is exactly what happened at step
893. Value if general: on detecting high map-similarity with the previous
level, route straight to the predicted stair cell (large descent-time
saving). Validation plan: measure layout-repeat frequency across the
800–999 dev census seeds (cheap offline check over existing trajectories +
a few probe resets); scope the rule to detected-repeat episodes only.
STATUS: pending validation. NOTE: possible NLE seeding artifact — if
repeats are common, this is also a WORLD-MODEL fact about the eval
substrate worth disclosing in the report.

**R2 — QUESTION-DRIVEN RETRIEVAL DEMO (the mechanism working on real
data).** Constraint hit: status shows "Hungry" at T837 with no food in
inventory. Question formulated: "Where have I seen food?" Memory query
(items_seen): clove of garlic @ D2 (28,7) seen 6×; egg @ D1 (35,16) seen
2×. Answer: known food two levels up; risk-costed backtrack ≈ 40 turns via
the (repeated-layout!) known stairs. The mainline agent did NOT do this —
it has no backtrack-for-food capability. This is the motivating instance
for the curiosity/backtrack objective class: the memory already contains
the solution to the constraint the agent later died-adjacent to
(starvation class = 14/80 checkpoint deaths).
CHAIN LOG: constraint(hungry) → question(where food?) → hits(garlic@D2,
egg@D1) → plan(backtrack via known stairs) → [not executable yet — no
navigator hook]. Socket stays OPEN until the backtrack objective ships.

**R3 — PASSIVE-SPECIES SEPARATION (store evidence).** Monster ledger:
lichen passive_adj=7, hit_us=0 (25 sightings); newt hit_us=2; jackal
hit_us=0 but 36 sightings with 6 kills (we struck first). Implication:
passive_adj/hit_us ratios separate chase-and-bite species from
stand-still species using only served observations. CAUTION: lichen has a
sticky touch attack in the source — 7 passive turns without a hit may be
small-n luck. Validation: E16 branch-probe (stand adjacent to a lichen N
turns on a branch; observe attack rate) before any policy trust.
STATUS: pending probe.

## Data-quality catches from this pass (already fixed in code)

- "spell" logged as a monster with hit_us=16 — the store's hit-parser was
  counting OUR Force Bolt as an enemy. Fixed (NON_MONSTERS filter,
  committed). Lesson for the writeup: the reflection pass's first real
  yield was instrument calibration — the dot-connector audits its own
  memory substrate before it can trust it.
- Ghost-stairs "smear" hypothesis REFUTED (R1 explains the data): the
  dossier was correct; the world repeats. Niggle closed.

## Curiosity objectives emitted (felt-sense, one-line whys)

- C1: "Backtrack to D2 garlic when hunger < Hungry-threshold" — why: known
  food beats unknown frontier when starving is the #2 death class.
- C2: "On next level entry, check map-similarity vs previous level; if
  high, walk the predicted stair cell first" — why: R1 pays instantly if
  the repeat holds.
- C3: "Probe lichen adjacency on a branch" — why: if lichen is truly
  passive at our speed, it's free xp/food for fragile roles (and if not,
  R3 dies before it misleads anyone).

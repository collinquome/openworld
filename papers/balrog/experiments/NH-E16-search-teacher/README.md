# NH-E16 — Search-as-teacher (REGISTERED, Phase L; operator directive 2026-07-07, flagship writeup: "deterministic replay as an epistemic instrument")

MODEL: Fable 5 (max reasoning) — design + registration. (Handoffs logged here if a successor model continues this experiment.)

**Foundation (verified fact):** ref-vs-ref replay on this host/config is perfectly
deterministic — same seed + same action prefix ⇒ identical state (n=20 control,
all paired deltas exactly 0.00; NH-C2.1 report §E-NH2). A `(seed, action_prefix)`
pair therefore IS a state snapshot, and re-running a prefix then diverging is a
sound branch operator. No env internals, no state cloning: snapshot/branch is
`reset(seed)` + scripted replay through the same served interface. Clean-protocol
compatible by construction.

## Component 1 — SEARCH TEACHES POLICY (the AlphaGo loop, code-space)

Generalize the gym beyond deaths: at ANY high-uncertainty decision point in dev
play — flagged by (a) EV margins near zero, (b) novel monster (< NOVELTY_MIN_ROWS
evidence), (c) coverage-matrix untested cell, (d) stall watchdog fire — snapshot
`(seed, prefix)`, branch-explore alternative actions/policies in replay, measure
outcomes, and DISTILL the winning line into a rule card. Standard gates apply:
≥3-different-seed generalization before a distilled rule ships; drop-if-unclear.

Loop: play → search at hard spots → distill → play better → harder spots emerge.
Policy improvement through search, exactly AlphaGo's self-play distillation,
except the policy is legible code (rule cards + docstrings, per the code-as-bridge
standard — NH-E17 will test whether those artifacts alone reconstruct the system).

**Tracked metrics (the result figure):** rules-distilled-from-search per dev
block; their aggregate paired dev delta; avoidable-damage movement attributable
to distilled rules.

## Component 2 — BRANCH-PROBE MECHANICS EXPLORATION (epistemic save-scumming; dev/gym ONLY)

Before uncertain interactions — unknown potion, unidentified wand, novel monster
contact, ANY untested verb — snapshot and TRY IT on a branch: quaff the potion,
zap the wand, cast the spell, touch the thing. Observe the consequence, record
the mechanics knowledge (possibility sets, danger tables, verb grammar/effects),
then let the mainline decide informed. This is the standard harness for the
NH-E14 action-space frontier: every unexplored verb gets branch-probed
systematically (verb grammar mapped, effects observed, failure modes catalogued)
BEFORE it is wired into policy.

**HONEST SCOPE (pre-declared):**
- Item APPEARANCES shuffle per seed → branch-probing teaches GENERAL mechanics
  (what the potion-class can do, what zapping does, which monsters are
  touch-dangerous), feeding priors and possibility sets — NOT per-episode item
  identities. No per-seed identity knowledge may leak into any scored
  configuration.
- Scored runs get no snapshots (one life). What transfers to Phase E is the
  compiled knowledge only: rule cards, danger tables, verb state-machine
  grammars.
- Dev/gym seeds only, like every learning instrument in this program.

## Instrument

`papers/balrog/code/nethack/nh_branch.py` — replay/branch executor:
`replay(seed, prefix) → live env at the snapshot point`, `branch(seed, prefix,
probe_policy) → outcome record`. Determinism re-verified per session (replay
twice, compare tty + blstats hash) before any probe batch is trusted; drift ⇒
STOP, investigate (possibility: env version change), never probe on an unsound
snapshot. Probe records land in `results/e16_probes/` as JSON
{seed, prefix_len, probe, transcript(messages), observed_effects, knowledge}.

Both components log into the hypothesis coverage matrix (cells resolved by
branch evidence are marked as such — branch evidence counts as verification at
the same α as play evidence only when the probed mechanic is deterministic;
stochastic mechanics still need the distributional gate) and into the NH-E13 KB
(mechanics claims get provenance:probe, joining provenance:wiki and
provenance:source in the 3-way validation).

## Status log
- 2026-07-07: registered (operator directive), folder + instrument spec created.

## The MECHANIC DISCOVERY LOOP (operator directive 2026-07-07; protocol shared by E16 branch-probes, E20 lab, E21b The Game)

1. **HYPOTHESIS QUEUE per unknown mechanic** — on encountering unknown
   dynamics, enqueue explicit micro-hypotheses in question form: "How does
   the cat move? (toward player within 5 tiles?)", "What happens if I water
   the plant 3 times?", "Does the shrine effect stack?"
2. **MINIMAL ISOLATED TEST per hypothesis** — the SMALLEST scenario that
   answers it (unit-test scenario, not a full level); controlled initial
   conditions via the lab/authoring channel; branch-probe (snapshot+try)
   where the env supports it.
3. **PREDICT-BEFORE-TEST** — each test declares its predicted possibility
   set BEFORE running; observe, corroborate or revise, iterate until the
   mechanic's violation rate ~0 → mechanic PINNED → rule card written.
4. **THE KEY ARTIFACT: the successful micro-test IS the unit test.**
   Discovery leaves the snapshot suite behind as its residue; the world
   model and its test suite co-emerge; every pinned mechanic ships with the
   test that pinned it. Log the discovery transcript per mechanic
   (hypothesis → tests → revisions → pinned) — methods evidence + highlight
   material ("HYPOTHESIS: cat chases within 5 → TEST → REFUTED: chases
   within 3 → PINNED").
5. **Metrics:** hypotheses-per-mechanic-until-pinned (discovery efficiency);
   pinned-mechanic coverage before first serious world attempt (the
   "study before the exam" curve).

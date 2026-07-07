# NH-E21 — Composition Worlds (REGISTERED; operator directive 2026-07-07; benchmark-artifact candidate "Composition Worlds v1")

MODEL: Fable 5 (max reasoning) — design + registration. (Handoffs logged here.)

Purpose: isolated testbeds for the program's central claim — the INTUITION
layer (LLM over memory) is NECESSARY, not decorative. The controlled-
experiment version of the Arm A/B comparison; four-layer thesis in a petri
dish with a tiny confound surface.

## Scenario class (operator design)

1. **Procedurally generated** mini-environments where DYNAMICS MUST BE
   DISCOVERED through play: item effects, hazard magnitudes, passage
   conditions randomized per episode/world ("the lettuce deals 80 damage
   THIS world") — no fixed policy or memorized solution works.
2. **Long-range fact separation:** solution facts encountered far apart
   (different rooms/times): "lettuce costs 80 HP" ... later ... "this door
   passes only below 20 HP". Neither fact useful alone.
3. **Composition required:** the win combines remembered facts into a novel
   plan — with 100 max HP: survive discovering the lettuce (>80 HP), then
   deliberately EAT LETTUCE to drop under 20 for the door. Damage-as-key.
   Solution class: reinterpret a discovered dynamic as an instrument for a
   separately-discovered constraint.

## Implementation

Fastest substrate wins per template: MiniHack des-files where NetHack
mechanics permit (HP-threshold gates aren't native; traps/levers partially
work); else custom gridworlds via the minigrid stack (BabyAI arm infra) or
the openworld framework itself (its authoring surface exists for this —
doubles as our first contribution USING the framework; see openworld core +
Jim's world-authoring pattern). Procedural generator + 10–20 world templates
of escalating composition depth (2-fact, 3-fact, cross-episode-KB variants).

**Creative license (operator):** author additional templates freely —
resource-budget puzzles, multi-key dependency chains, information-asymmetry
worlds (fact learnable only via sacrifice), trade-off worlds (every gain
costs something remembered later), cross-episode KB worlds (dynamics stable
across episodes → does the KB accumulate?). Each with README + pre-registered
predictions. The world-suite itself becomes a benchmark artifact
("Composition Worlds v1") publishable alongside the paper.

## The ablation (the point) — pre-registered prediction

Run each world under: (a) full stack (perception+memory+intuition+procedure);
(b) no-intuition (code-only, same memory); (c) no-memory (LLM sees only
current obs). **Prediction, registered now: (b) and (c) fail composition
worlds systematically; (a) solves them.** Metrics: solve rate,
facts-connected count, question→hit→solve chain rate.

## Question-driven retrieval (operator addition — the mechanism, named; shared with NH-E18)

When planning hits a constraint, the intuition layer formulates an explicit
QUESTION — "How can I get below 20 health?" — and runs it against the memory
store as a retrieval query (FTS5 over observation store + dossiers +
relations; e.g. search 'damage','HP loss', ranked by controllability). The
retrieved memory ("lettuce: −80 HP, D2, repeatable") answers the question and
completes the plan. Log the full chain: constraint → question → memory hits →
answer selected → plan. This is GOAL-DIRECTED retrieval (question as key),
complementing passive dot-connecting (relations noticed unprompted) —
implement and measure BOTH modes. GIF banners render the chain:
`Q: how to get under 20HP? → MEMORY: lettuce −80 [D2] → PLAN: eat lettuce`.

## Highlight reel

Solve GIFs (fact-1 banner → fact-2 banner → "INFERRED: eat lettuce to pass
door" → win) are expected to be the program's best demonstration material.

## Status log
- 2026-07-07: registered (operator directive + 2 additions). Implementation
  queued behind the in-flight NH-E14 cast integration milestone.

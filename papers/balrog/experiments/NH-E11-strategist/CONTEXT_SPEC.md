# CONTEXT_SPEC v0.2 — the strategist context package (operator directive 2026-07-07)

MODEL: Fable 5 (max reasoning) — design + registration. (Handoffs logged here if a successor model continues this experiment.)

Every LLM consultation — Arm B triggers, reflection passes, NH-E18 dot-connector
scans — receives the FULL picture, not a summary of the current room. All
content is obs-derived (clean protocol: built exclusively from served
observations accumulated in the episode's belief state). The package is
versioned; **every consultation logs the exact package sent** (verbatim, into
the trajectory) — auditability now, context-size vs decision-quality analysis
later.

## Package sections (v0.1)

1. **FULL WORLD MAP** — every visited level rendered as annotated ASCII from
   the atlas/dossier: terrain + explored/unexplored boundaries, stairs (up/down
   + destination when known), hazards with evidence, items seen INCLUDING
   left-behind ones, shops/altars/fountains/features, monster last-known
   positions. Current level in full detail; older levels may compress to
   dossier annotations + notable-cells if token budget demands, but bias
   toward completeness — the map IS the reasoning substrate for where-to-go
   decisions.
2. **MEMORIES** — the NH-E18 unified observation store: item-appearance/price
   table, validated + pending inferred relations, open curiosity hypotheses,
   relevant rule cards (retrieved by current context via the KB/card index,
   not the full table), death lessons applicable to the current state.
3. **STORY SO FAR** — compact running narrative maintained by CODE (not raw
   logs): chronological event log — level transitions, fights (outcome + what
   fired), acquisitions, near-deaths, objectives completed/aborted and why,
   current objective stack. Style: "D3: killed-by-ranged a soldier ant pack at
   the choke; found + wore ring mail (AC 4→3); descended via SE stairs...".
4. **CURRENT STATE** — role/stats/HP/hunger/inventory/position + active
   strategy state (NH-E15 machine state + last transition).

## v0.2 addition (operator reminder-loop directive): section 5 — REMINDERS

5. **REMINDERS** — memories PUSHED by the cue→memory index for the current
   situation (adversary strats, applicable lessons, price hits, branch
   notes), each tagged with its cue and source artifact. The strategist
   doesn't have to know what to ask for. Every reminder fire is logged with
   whether it changed the decision.

## Versioning + logging contract

- Spec version string embedded in every package header
  (`CONTEXT_SPEC/v0.1`).
- Consultation record: {trigger, spec_version, package(verbatim), response
  (verbatim), objective-stack delta, retrievals made}.
- Changes to section content/format bump the version and are recorded here.

## Status
- v0.1 2026-07-07: registered. Builder lands with the NH-E18 substrate
  (`nh_memory` store + dossier renderer); first consumer = dot-connector
  reflection passes on dev episodes.

## GOALS ARE A LIST (operator directive 2026-07-07 — amends the objective-stack contract)

The agent holds MULTIPLE STANDING GOALS CONCURRENTLY — "get stronger" AND
"progress downward" AND "stay fed" AND "close open sockets" — not one
active objective with the rest queued.

1. The strategist maintains the GOAL LIST with weights (role- and
   situation-dependent; felt-sense sets/re-weights at consultations).
2. Goal-market candidates are scored by combined contribution across ALL
   standing goals — a detour fight scores on 'stronger' (xp) + 'sockets'
   (species evidence) even while pausing 'downward'; stairs score
   'downward' but may debit 'stronger' if under-ready (the readiness
   principle becomes a WEIGHT INTERACTION, not a gate).
3. The objective STACK remains the execution plan (the ordered how),
   derived from the goal LIST (the standing what) — list persists, stack
   turns over.
4. Per-action goal-contribution vectors are logged — death retrospectives
   then attribute deaths to goal overweighting ("died over-serving
   'downward': 0.8 vs 'stronger' 0.1 at xp2/D5"), turning weight-tuning
   into evidence.
GIF HUD: goal list + weights; flash multi-goal wins ("+stronger +sockets:
killed newt [xp, species pinned]").

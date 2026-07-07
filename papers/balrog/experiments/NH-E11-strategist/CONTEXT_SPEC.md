# CONTEXT_SPEC v0.1 — the strategist context package (operator directive 2026-07-07)

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

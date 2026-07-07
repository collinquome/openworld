# FABLE NETHACK — PHASE L (extended learning campaign)

MODEL ROSTER (methods line, per the model-provenance standing rule): Phase L
session 1 design/synthesis/analysis = Fable 5 (max reasoning); registered
fallback if capped = claude-opus-4-8 (max thinking) — any handoff will be
logged here at its phase boundary. Workers/subagents where used: Sonnet 5
(tagged per artifact).

Predecessor state: NH-C2.1 checkpoint 5.27 [4.22, 6.43] vs SOTA 6.8 — no beat;
avoidability audit says deaths are CAPABILITY-bound (5–8% of damage
decision-avoidable); action audit says 50/248 actions ever used
(cast/zap/quaff/read/fire/wield/puton = 0). Phase L builds capability on dev
seeds only until the pre-declared exit criteria are met, then stops for Phase E.
Full context: FABLE_NETHACK_C2_REPORT.md; registry: docs/NETHACK_PROGRAM.md.

## Exit criteria (pre-declared in the C2 report §Program — restated, not weakened)

(i) coverage matrix ≥70% of death-mass-weighted cells resolved; (ii) top-5 gym
syllabus classes solved-or-UNWINNABLE with ≥3-seed generalization; (iii)
avoidable-damage rate plateaued (<1-point change) over 2 consecutive 40-episode
dev blocks; (iv) snapshot suite green; (v) play-time violation rate < 1e-4 with
no unexplained novelty entries.

## The four-layer architecture (operator naming, 2026-07-07 — structures this whole report)

PERCEPTION (perceptors: obs → typed structure) · MEMORY (dossiers, observation
store, cards, lessons) · INTUITION (the LLM: dot-connecting, curiosity
hypotheses, objective selection over the full context package — slow, rare,
expensive, irreplaceable) · PROCEDURE (code: navigation, combat, state machine,
verified rules — fast, constant, free, exact). Program claim in these terms:
perception+memory+procedure alone plateau (Arm A ceiling); adding intuition
breaks it (Arm B delta). Every mechanism below carries its layer tag.

## Priority order (operator, 2026-07-07, incl. late reweight)

1. PERCEPTORS + MEMORY (NH-E18 substrate + dot-connector; perceptor backlog:
   shop/altar/fountain/special-room, monster-state, item-appearance+prices,
   branch recognition) — expected biggest wins.
2. ACTION-SPACE FRONTIER (NH-E14: cast/zap/quaff/read/wield/fire), every verb
   branch-probed via NH-E16 component 2 before wiring into policy.
3. NH-E15 strategy state machine + stall watchdog.
4. NH-E13 wiki KB (FTS5 + manifest, add-only) feeding everything.
5. Background loop: gym (E-NH6) + NH-E12 retrospectives + coverage matrix +
   NH-E14b loot-ROI + E-NH4b risk planner.
NH-E16 (search-as-teacher) is the shared instrument under 2/3/5;
NH-E17 (clean-room rebuild) runs at exit — every card written to pass it.

## Dev-metric trend table (primary: avoidable-damage rate; updated per dev block)

| block | config | n | mean prog | avoidable dmg % | gym solve | matrix fill | violation rate | notes |
|---|---|---|---|---|---|---|---|---|
| C2 ref (700–739) | v1.1 frozen | 40 | 4.27 | 10% | — | — | — | predecessor baseline |
| C2 navfood (700–739) | NH-C2.1 frozen | 40 | 5.30 | 8% | — | — | — | predecessor freeze candidate |

## Workstream verdicts (running)

*(rows appended as they land; milestones flagged for the coordinator)*

## Running log (UTC)

- 2026-07-07 ~17:3x Phase L session 1 opened. NH-E16 + NH-E17 + NH-E18
  registered (operator directives), folders + ledger rows created. Priority
  reweight (perceptors+memory lead) recorded in program doc + here.
- ~17:4x E18 refinement registered: hypothesis-driven exploration objectives
  (revaluation trigger → curiosity objectives; "LLM decides WHERE, procedures
  decide HOW"; curiosity hit rate metric; CURIOSITY GIF banners).
- ~17:5x Registered in one batch as directives arrived: CONTEXT_SPEC v0.1
  (strategist context package: full world map + memories + story-so-far +
  current state, versioned + logged verbatim per consultation); four-layer
  architecture naming (PERCEPTION/MEMORY/INTUITION/PROCEDURE); NH-E19
  principles distillation + algorithm catalog/meta-selection (+ ablation
  experiment); NH-E20 MiniHack scenario lab (des-file micro-scenarios,
  transfer gate, priority: spellcast doctrine + D5-6 melee); model-provenance
  standing rule (MODEL field stamped on all new artifacts).

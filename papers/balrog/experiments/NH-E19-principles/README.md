# NH-E19 — Principles distillation + algorithm selection (REGISTERED, Phase L; operator directive 2026-07-07)

MODEL: Fable 5 (max reasoning) — design + registration. (Handoffs logged here if a successor model continues this experiment.)

Play produces THREE knowledge artifacts, each in its consumer's representation:
**world model** (code, for the planner), **strategies** (rules, for the state
machine), and **PRINCIPLES** (language, for the intuition layer).

## 1. PRINCIPLES.md (versioned, provenance-cited, IN THE STRATEGIST PROMPT)

Distilled decision-making principles in plain language, each with evidence
citations — the prose twin of rule cards. Examples of the intended register:
- "Below half HP, never take a fight you can walk away from — 57/66 combat
  deaths were slow bleeds."
- "A fresh unknown monster deserves one thrown dagger before any melee."
- "Descend hungry only if the next meal is likelier below than here."

Sources: NH-E12 death retrospectives, gym verdicts, avoidability-audit
patterns, reflection passes. Principles guide the scenarios you CAN'T easily
write an algorithm for — the intuition layer's judgment substrate. Update
discipline = rule-card discipline: evidence in, revision logged; invalidated
principles struck through (~~like this~~) with the refuting data cited —
invalidations stay VISIBLE (operator requirement).

File: `papers/balrog/priors/PRINCIPLES.md` (lives with the priors/verdict
artifacts; version header; every principle numbered + cited).

## 2. Algorithm catalog + meta-selection

The strategist KNOWS its procedures: a catalog card per algorithm (risk-A*,
dig-dive routine, kite-to-choke, expectimax-fight, frontier-explore,
rest-cycle, ...) with what-it's-for / preconditions / failure modes
(`ALGORITHM_CATALOG.md`, same folder). At consultations the intuition layer
may SELECT which algorithm the navigator should run for the current situation
— meta-control: choosing the tool, not micro-managing it. Selections +
outcomes are logged; catalog cards accumulate their own win rates, so
algorithm-selection becomes evidence-driven over time.

## 3. Experiment — principles ablation

Arm-B-style dev blocks: strategist WITH full PRINCIPLES.md + catalog vs
WITHOUT (bare CONTEXT_SPEC package). Delta = the measured value of articulated
wisdom. Secondary metric: principle-citation logging — which principles the
LLM actually invokes in decisions; dead principles get pruned.

## 4. NH-E17 note

The clean-room rebuild now tests all THREE artifacts: world-model docs + rule
cards + PRINCIPLES.md should reconstruct the full system. Standing obligation:
keep all three complete enough to pass.

## Status log
- 2026-07-07: registered (operator directive), folder created.

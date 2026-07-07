# NH-E20 — MiniHack scenario lab (REGISTERED, Phase L; operator directive 2026-07-07; exploratory mode authorized — "play around, let's see what works")

MODEL: Fable 5 (max reasoning) — design + registration. (Handoffs logged here if a successor model continues this experiment.)

MiniHack runs the SAME NLE engine as NetHackChallenge and supports DES-FILE
AUTHORING → fabricate small, controlled, real-engine test scenarios for every
mechanism. Hypotheses that needed 40 noisy NetHack episodes resolve in 50
cheap controlled ones.

## 1. Authored micro-scenarios

des-files for exactly the situations we need to master:
- "Wizard vs 2 giant ants in a corridor, 60% HP" — spellcast doctrine
- "agent + jackal pack in open room" — kiting
- "unknown potion + shopkeeper" — price-ID
- "sessile F + trash mob" — target priority
- the D5–6 kill-zone composition
Controlled initial conditions, low variance, fast episodes, unlimited reps —
the falsification matrices (HP × terrain × count) become REAL-ENGINE test
suites instead of in-model approximations.

## 2. Learning mode

"I wonder what a good strat for X would be?" → author scenario X → run
candidate strategies head-to-head (ours + wiki's + principles-derived) at
n=50+ → winner becomes a rule card / principle with MiniHack-lab evidence.
The intuition layer designs the scenario AND the candidate set (tier-1 of the
NH-E10 pipeline, now with a real-engine instantiator).

## 3. TRANSFER GATE (honest, pre-declared)

MiniHack ≠ NetHackChallenge exactly (action-space config, options, level
context differ). Every lab-validated tactic gets a NetHack dev-block transfer
check before it ships to a role profile: lab evidence sets the prior, wild
evidence confirms. Log the lab→wild transfer rate — itself a finding (feeds
T387's cross-game transfer thesis).

## 4. Infra

Reuse the proven MiniHack arm env stack (`work/fable_minihack/`). Scenario
des-files live in this folder (`scenarios/`), versioned, each with a README
(what it tests, why, verdicts).

**Priority scenarios first: spellcasting doctrine + the D5–6 melee problem.**

## Status log
- 2026-07-07: registered (operator directive), folder created.

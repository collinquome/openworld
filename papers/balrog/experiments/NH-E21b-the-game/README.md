# NH-E21b — THE GAME: Composition Worlds as a designed 2D game (REGISTERED; operator directive 2026-07-07; flagship build)

MODEL: Fable 5 (max reasoning) — design + registration. (Handoffs logged here.)

**Operator's design pillars (verbatim):** world discovery = figuring out
unique mechanics; strategy = how to navigate; knowledge/memory log; choosing
novel/counterintuitive things for exploration or AHA moments;
curiosity/intuition seeking.

A 2D tile-based game whose CORE LOOP is the four-layer thesis: world
discovery = figuring out UNIQUE mechanics; strategy = navigating under them;
memory = the knowledge log; progress = curiosity, novelty-seeking, and AHA
moments (long-range dot-connecting), with some gates REQUIRING
counterintuitive plays (defeasibility by design).

## 1. Invented mechanics via a MECHANIC GRAMMAR (anti-contamination property — state prominently)

Mechanics are procedurally COMPOSED at world-generation from a grammar of
primitives (entities × triggers × effects × conditions): "touching the blue
shrine while carrying metal inverts gravity for 20 steps", "the lamp drains
3 HP/step but doubles loot visibility", "doors keyed to parity of steps
taken". Because mechanics are GENERATED, they exist NOWHERE in any training
corpus, wiki, or source the agent could have seen — **the purest possible
test of discovery + memory + intuition, closing the pretraining-prior
asterisk that every NetHack arm carries.**

## 2. World structure

Interconnected map (not isolated rooms): multiple zones; long-range fact
separation ACROSS zones; backtracking rewarded (curiosity journeys); some
mechanics only discoverable via deliberate experimentation (branch-probe);
AHA-gated progress (composition of 2–4 discovered facts); at least one gate
per world requiring a counterintuitive play (principle-override class).

## 3. Agent-facing (clean-protocol analog)

obs = tile grid + entity glyphs + event messages. The KNOWLEDGE LOG is a
first-class artifact (discovered mechanics, open hypotheses) — the game is
legible-by-design.

## 4. Instrumentation built in (the game IS the measurement instrument)

Per-run native metrics: mechanics discovered/total, AHA events
(fact-composition uses), overrides attempted/needed, curiosity journeys +
hit rate, question-driven retrievals.

## 5. Build plan

Python, simple: tiles + JSON world specs + deterministic seeds; gridworld
GIF rendering patterns reused from the BabyAI arm, with knowledge-banner
overlays. Ship: engine + mechanic grammar + 5–10 grammar-generated worlds of
escalating depth + the NH-E21 ablation harness (full stack / no-intuition /
no-memory / no-override). Writeup position: our benchmark contribution
("Composition Worlds"), built ON the openworld framework's world-authoring
thesis.

## Status log
- 2026-07-07: registered. Build queued this phase (flagship); NH-E21
  ablation arms and question-driven retrieval apply as specced in NH-E21.

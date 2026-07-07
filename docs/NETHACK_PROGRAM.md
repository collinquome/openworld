# NetHack arm — program conventions (Campaign 2 onward)

## The four-layer architecture (operator naming decision 2026-07-07 — use everywhere: reports, paper sections, mechanism tags, GIF banners)

1. **PERCEPTION** — perceptors: raw obs → typed structure (rooms, threats,
   items, prices, monster states, branch signatures).
2. **MEMORY** — dossiers, observation store, rule cards, lessons: what has
   been seen and learned.
3. **INTUITION** — the LLM: holistic judgment over map+memory+narrative;
   connects dots, generates hypotheses ("I wonder if..."), senses where to
   go, picks objectives. Slow, rare, expensive, irreplaceable.
4. **PROCEDURE** — code: navigation, combat mechanics, state machine,
   verified rules. Fast, constant, free, exact.

**The program's claim, in these terms:** perception+memory+procedure alone
plateau (Arm A ceiling); adding intuition is what breaks it (Arm B delta).
Every mechanism/rule/GIF-banner is tagged with its layer; the four-layer
diagram anchors the paper.

## Phase structure (TRAIN-THEN-EVALUATE, operator-ratified 2026-07-07)

1. **NH-C2.1 midpoint checkpoint** — frozen levers-so-far, n=80 seeds
   4000–4079. One block, reported honestly, no freeze-block iteration after.
2. **Phase L — extended learning.** No scored evaluations. All progress is
   dev-side: avoidable-damage rate (primary), gym solve rate, coverage-matrix
   fill, play-time violation rate, dev-block means on dev seeds (700–999).
   Exit criteria are pre-declared in FABLE_NETHACK_C2_REPORT.md §Program and
   may not be weakened retroactively.
3. **Phase E — TWO first-class final arms** (operator+CEO decision), each
   pre-registered, frozen, single-block:
   - **ARM A — PURE CODE:** Phase-L learnings compiled to code; n=100,
     seeds 6000–6099 (6000–6004 memory-pass-3 overlap disclosed).
     Primary: mean + canonical CI vs 6.8; decisive = CI-low > 6.8.
   - **ARM B — LLM-STRATEGIST:** live LLM at strategic triggers ONLY
     (level entry / impasse / novelty / objective completion) emitting
     NH-E11 objective stacks; code navigator executes all steps. n=25,
     seeds 7000–7024, own protocol category (LLM-in-loop; closer to
     leaderboard comparability). Metrics: score, consultations/episode,
     marginal value per consultation; strategist prompt+response logged
     verbatim into trajectories; obs-derived context only (dossier,
     never env internals). Where budget allows, run B on a subset of
     Arm A's seeds for paired comparison. **A-vs-B delta is a headline:**
     live strategic intelligence vs compiled intelligence.
     **Final form (operator): retrieval-augmented strategist** — at
     consultation triggers the LLM may retrieve (wiki lookup via NH-E13
     reactive mode, rule-card search, dossier review) before emitting the
     objective stack; retrievals logged like consultations (what was
     looked up, advice extracted, whether the stack changed). A-vs-B thus
     measures the full "intelligent lookup + code execution" package vs
     pure compiled code.

## Repo layout (operator directive)

Every experiment gets `papers/balrog/experiments/NH-<id>-<slug>/` with
README.md (experiment card mirroring its ledger row), experiment-specific
code or pointers (shared stack stays in `papers/balrog/code/nethack/`),
`results/`, and NOTES.md. Ledger rows link to folders. Pushes go to the
`fork` remote (collinquome/openworld); upstream PRs only at milestones.

## Phase-L workstreams (operator directives on file, 2026-07-07)

**Priority reweight (operator, 2026-07-07 late):** PERCEPTORS and MEMORY lead
Phase L as the expected biggest wins; the action-space frontier continues
behind them. Perceptor backlog beyond the built set: shop/altar/fountain/
special-room detectors, monster-state perceptor (peaceful/hostile/fleeing/
asleep), item-appearance tracker (unidentified appearance + observed prices +
contexts — feeds NH-E18), branch/level-feature recognition (Mines/Sokoban
signatures).

- **E-NH4b risk-constrained sampling planner:** death-probability-aware
  path costs; determinized K-future sampling for multi-monster fights;
  global `P(death) < ε per level` knob (unifies veto/rest/pacing), ε swept
  on dev metrics. Validate on avoidable-damage + the D5–6 hazard spike.
- **E-NH6 situation gym + DEATH LEARNING intake:** scenario library
  harvested from all logs (deaths, near-deaths, stalls) as
  (seed, action-prefix, class); branch-explore alternatives in the real
  env (dev seeds; deterministic best-line finder, not dice sampling);
  in-model Monte Carlo luck quantification → MISPLAYED / UNWINNABLE /
  MARGINAL; generalization gate (≥3 different-seed instances per class);
  solved scenarios become permanent regression fixtures. **Continuous
  intake:** every new Phase-L death auto-enqueues (replay fatal window →
  branch-explore → rule card or upstream arrival-constraint; recurring
  class post-fix = highest-priority regression alarm; dedupe by class).
  Report figure: death-class decay curve over Phase-L time.
- **NH-E12 death retrospective (tracked experiment):** per-death artifact
  {death_id, class, depth/role/turn, avoidability verdict, LESSON (typed:
  TACTICAL RULE | ARRIVAL CONSTRAINT | NO-LESSON-DICE), gym evidence,
  status}. NO-LESSON-DICE is mandatory where true — patching rules to
  explain variance is how models rot. Metrics: % deaths with lessons,
  lesson→rule conversion, class decay after lesson ships, repeat-death
  alarms. Backfill over the historical 66+ combat deaths.
  EXTENSION (operator 2026-07-07): READINESS BACKTRACE per capability-bound
  death (readiness deficit at death vs floor threat band + dossier-enumerated
  skipped prep opportunities → quantitative lesson) + TRAJECTORY AVOIDABILITY
  metric (was there a prep path through the same dungeon that survives?) —
  the moment-vs-trajectory gap = the quantified value of preparation
  ("capability-bound at the moment, preparation-bound at the trajectory");
  exploration weights raised by default for walker/fragile roles (digger
  exemption = live hypothesis; E14b + backtraces tune per-role).
- **NH-E11 strategist/navigator architecture:** level dossier (structured
  per-level record: rooms/exits/stairs, located hazards w/ evidence, item
  sightings, monster encounters w/ outcomes, frontiers, notes; persists
  across revisits within episode; serialized into trajectories;
  within-episode-only, disclosed); objective-stack JSON contract
  {id, goal(typed), target, why, preconditions, constraints, abort_if,
  priority} ingested by the goal market; strategist mode at low-frequency
  triggers; **compilation path**: mine Phase-L objective-stack decisions
  for recurring patterns → compile into strategist policy rules for Arm A;
  the live-LLM variant IS Arm B. Traversal upgrade: A* edge costs =
  distance + dossier-hazard + threat exposure; log route-chosen vs
  naive-shortest (safety-premium metric).
- **Hypothesis coverage matrix:** rule-card × scenario-class grid; scoped
  holds_in% per cell; untested-but-applicable cells auto-enumerated as
  open hypotheses, prioritized by death-mass × uncertainty; each cell run
  as a pre-registered micro-experiment {hypothesis, Y, Z, prediction,
  outcome, card update}. Rendered in the report (audit surface).
- **LLM-designed falsification matrices:** before a gym mechanism ships,
  the LLM designs the condition matrix meant to BREAK it (HP × terrain ×
  pack size × xp × hunger); instantiate via mined real-env instances +
  model-authored states; real-vs-model disagreement feeds the
  distributional gate.
- **Deliberate play:** LLM plays dev-seed envs directly at frontier
  scenarios, annotating reasoning; transcripts codified into carded rules.
  Never on scored seeds; no LLM calls in Arm A scored code.
- **Novelty protocol:** detector (shipped in NH-C2.1 as ledger +
  touch-kill guard) → Phase L adds caution-default contact gating for
  thin-evidence species (danger prior scaled by difficulty, contact gated
  on evidence; touch effects never appear in dpt stats) and
  explain-the-novel ledger discipline (unexplained novelty = report
  metric). Novelty is also the designed trigger hook for Arm B
  consultations.
- **Goal-market info-gain term:** exploration goals get a
  value-of-information bonus (map/hazard knowledge per step cost).
- **World-model test suite:** snapshot fixtures (every fixed bug included)
  + play-time possibility-set verification on all dev/gym episodes with
  per-episode violation-rate tracking; spike after a change = drift alert,
  blocks the change. Green suite required for any freeze.
- **Harness-audit fixes (post-checkpoint):** belief-snapshot exception
  counting; transition-log flush + .complete marker + tolerant reader;
  RUNNER_TRUNCATED end-reasons; tty-rank-title role-parse fallback;
  blstats-ground-truthed depth records + belief-vs-blstats assertion.

## Results ledger (keep current — one row per experiment as it closes)

| id | experiment | config/seeds | result | status |
|---|---|---|---|---|
| C1-v1 | v1 scored block | v1 frozen; 2000–2024 | 4.39 [2.97, 5.97] | closed |
| C1-v1.1 | v1.1 scored block | v1.1 frozen; 3000–3079 | 6.09 [4.46, 7.93] | closed |
| C1-mem | memory A/B (2 designs) | v1+ledger | no learning curve; paired −1.21 [−3.17, +0.47] → rejected | closed |
| C1-blind | source-blind arm frozen | blind v10; 5000–5024 | 2.56 [1.65, 3.89] | closed |
| C2-ENH1 | forensics + ceilings | 224 episodes | trash-melee ceiling +4.88; ranking table in report | closed |
| C2-ENH1b | avoidability audit | v1.1 block replay | 5% damage avoidable; 7/80 deaths avoidable-final | closed |
| C2-ENH2 | lever groups (5) | n=20 paired each | NAV +2.25; FOOD +1.12; ARMOR +0.67; PACE +0.14; COMBAT −0.11/−0.38 → dropped | closed |
| C2-ENH4 | expectimax combat | dev | built + verified substrate; dropped per drop-rule (flat score, better death mix) | closed |
| C2-ENH5 | Elbereth substitutes | probe + dev | reachable via weapon-engrave BUT multi-turn carving = death trap; panic use dropped; dust-write remains interface-blocked | closed |
| C2-settled | 6-lever settled stack | n=40 paired | +0.01 [−1.31, +1.22] → rejected for reduced config | closed |
| C2-navfood | reduced stack (freeze candidate) | n=40 paired | +1.03 [−0.58, +2.68] → FROZEN as NH-C2.1 | closed |
| NH-C2.1 | midpoint checkpoint block | frozen navfood+guard; 4000–4079 | **5.27 [4.22, 6.43]** — no beat; ties v1.1; levers-so-far don't move the needle | **closed** |
| NH-E12 | death retrospectives | Phase L + backfill | — | registered |
| NH-E13 | wiki-strategy arm (Mode A batch / Mode B reactive) + mechanics-claims 3-way validation (wiki vs source model vs experiment; verdicts CONFIRMED / WIKI-WRONG / OUR-MODEL-WRONG / UNTESTABLE-IN-BALROG, version-tagged) | dev/gym only; provenance:wiki, no trust exemption | — | registered |
| NH-E14-probe | CAST FLOW VERIFIED (dev seed 715 Wizard): cast -> spell menu -> letter -> direction prompt -> Pw 8->3, time advances; same queue machinery as dig. Spell verb family is interface-reachable — action-space frontier is GO | probe | flow works | closed |
| NH-E14 | per-role strategy modules (13 profiles: dig-dive / melee-forward / fast-dive / survival-first; wiki per-role pages feed profiles; per-role stratified dev validation) + spellcasting/action-repertoire expansion | dev | action audit: 50/248 actions ever used; cast/zap/quaff/read/fire/wield = 0 ever | registered (audit closed) |
| NH-E14b | exploration-vs-descent frontier: explore-fraction as policy parameter (0.3/0.6/0.9/adaptive-VOI), swept per role class + depth-dependence; deliverable = LOOT ROI CURVE per role class; pre-registered both directions (loot ROI vs depth-only metric + food clock); track pick-axe-find rate on D1-3 full-explore and its score delta | dev blocks | — | registered |
| NH-E15 | strategy state machine (DIVE/EXPLORE/LOOT/FIGHT/FLEE/RECOVER/ESCAPE-UP; carded transition rules; state+transition in ledger + GIF banner) + STALL WATCHDOG (windowed progress metrics: new tiles/depth/xp/hp/action-entropy; escalation: perturbation -> forced transition -> dev/Arm-B LLM consult). Motivating fixture: ~400-turn giant-bat dig standoff -> gym scenario + regression fixture. Phase L: LLM authors/revises the transition table (pre-registered, gym-validated); Arm B adds proactive review ticks (~500 game-turns or on oscillation, logged); Arm A ships the compiled table | always-on, both arms | — | registered |
| NH-E16 | search-as-teacher (operator directive 2026-07-07; flagship: "deterministic replay as an epistemic instrument"): (1) AlphaGo loop in code-space — snapshot (seed,prefix) at high-uncertainty decision points (EV-margin~0 / novel monster / untested matrix cell / stall), branch-explore in replay, distill winning lines into rule cards (≥3-seed gate); metrics: rules-distilled per dev block + their aggregate dev delta. (2) branch-probe mechanics exploration (epistemic save-scumming, dev/gym ONLY) — snapshot-and-try before uncertain interactions (unknown potion/wand/verb/monster contact); teaches GENERAL mechanics (appearances shuffle per seed — never per-episode identities); standard harness for the NH-E14 verb frontier; scored runs get no snapshots, only compiled knowledge transfers | dev/gym only; folder NH-E16-search-teacher | — | registered |
| NH-E17 | clean-room rebuild (operator directive 2026-07-07): at Phase-L exit a FRESH agent context rebuilds the agent from knowledge artifacts ONLY (rule cards, priors, lessons, READMEs, reports, KB — docs never source); both agents run the same fresh dev block; rebuild≈incumbent ⇒ docs contain the knowledge; gap ⇒ itemized tacit-knowledge misses. Standing obligation NOW: every card/lesson written to reconstruct the system without its author | runs at Phase L exit — flag operator when exit criteria met | — | registered |
| NH-E18 | connecting-dots memory (operator directive 2026-07-07; LEADS Phase-L priorities with the perceptor backlog): (1) memory substrate — one queryable per-episode store (dossier + item sightings w/ appearances + prices + monster encounters + events timeline); (2) LLM dot-connector at consultation points + between-episode reflection proposes RELATIONAL hypotheses (price-ID via KB price tables, altar-drop BUC, didn't-attack⇒peaceful, level-features⇒branch, key/lock bindings), each a rule card (provenance: inferred) validated via gym/branch-probe before policy trust; (3) two-loop thesis: relational pattern-matching is the LLM's advantage, cheap reliable execution is code's — cleanest both-loops-necessary demonstration in the program. Metrics: relations proposed/validated/refuted per episode; paired impact of validated relations; dots-connected in GIF banners. Refinement (operator): HYPOTHESIS-DRIVEN EXPLORATION — capability/knowledge lands ⇒ dot-connector re-scans dossiers for revalued opportunities ⇒ CURIOSITY OBJECTIVES {hypothesis, target, EV, risk-costed travel cost, abort} priced in the goal market; "LLM decides WHERE, procedures decide HOW"; metric: curiosity hit rate (hypothesis→journey→outcome triples); CURIOSITY GIF banners; QUESTION-DRIVEN RETRIEVAL added as the second retrieval mode (goal-directed: constraint → question → memory query → plan; see NH-E21) | folder NH-E18-connecting-dots | — | registered |
| PRIORS | versioned prior sets `papers/balrog/priors/` (GENERIC_VIDEOGAME v0.1, NETHACK_SPECIFIC v0.1) + PRIOR VERDICT TABLE (validated/invalidated/untested — invalidations recorded; already: Elbereth-panic INVALIDATED in-interface, XP-grind INVALIDATED for max-rung, loot-usually-good PARTIALLY INVALIDATED) ; feeds T388 K-ladder generic-vs-specific axis | cross-game | v0.1 committed | live |
| NH-E13-KB | local wiki knowledge base: `wiki_kb.sqlite` (FTS5, per T312) + sha256 manifest; experiments query the LOCAL KB only; live WebFetch only ADDS pages (logged) — frozen corpus makes guide-following a controlled experiment | NH-E13 folder | spec committed | registered |
| E-NH4b / E-NH6 / NH-E11 / matrix / suite | Phase-L workstreams | dev only | — | registered |
| CONTEXT | strategist context package (operator 2026-07-07): every LLM consultation gets FULL world map (all visited levels, annotated ASCII from dossiers) + MEMORIES (E18 store: appearances/prices, relations, curiosity hypotheses, context-relevant cards, applicable lessons) + STORY SO FAR (code-maintained narrative) + CURRENT STATE (stats/inventory/strategy state); versioned CONTEXT_SPEC.md; every consultation logs the exact package verbatim | NH-E11-strategist/CONTEXT_SPEC.md v0.1 | — | registered |
| NH-E19 | principles distillation + algorithm selection (operator 2026-07-07): three knowledge artifacts per representation — world model (code), strategies (rules), PRINCIPLES (language, in the strategist prompt): priors/PRINCIPLES.md versioned + evidence-cited, invalidations struck through visibly; ALGORITHM_CATALOG.md (per-procedure card: what-for/preconditions/failure modes) with intuition-layer meta-selection at consultations (selections+outcomes logged → evidence-driven win rates); ablation experiment: strategist WITH vs WITHOUT principles+catalog on Arm-B-style dev blocks = measured value of articulated wisdom; principle-citation logging prunes dead principles; E17 rebuild now tests all three artifacts; DEFEASIBILITY model (operator): principles = defeasible heuristics with intuition-layer override authority under the override protocol (explicit + justified + bounded + outcome-tracked), two-tier safety (hard vetoes non-overridable; memory-bound licenses the override — no bound, no override); E21 gains ablation arm (d) no-override (pre-registered: fails lettuce-class like code-only) | folder NH-E19-principles | — | registered |
| NH-E20 | MiniHack scenario lab (operator 2026-07-07, exploratory mode): des-file-authored micro-scenarios on the same NLE engine (spellcast doctrine, kiting, price-ID, target priority, D5-6 composition); falsification matrices become real-engine suites; learning mode = author scenario → run candidate strategies head-to-head n=50+ → winner becomes carded rule/principle; TRANSFER GATE: lab sets the prior, NetHack dev-block confirms before any role-profile ship; lab→wild transfer rate logged (feeds T387); reuse work/fable_minihack stack; priority: spellcasting + D5-6 melee | folder NH-E20-minihack-lab | — | registered |
| NH-E21 | composition worlds (operator 2026-07-07): procedurally-generated discovery worlds with long-range fact separation + composition-required solutions (damage-as-key class); substrates: MiniHack des / minigrid / openworld authoring surface; 10-20 escalating templates + creative-license extras; THE ABLATION (pre-registered prediction: no-intuition and no-memory fail systematically, full stack solves) = controlled Arm-A/B comparison; QUESTION-DRIVEN RETRIEVAL mechanism (constraint → explicit question → FTS5 memory query → answer → plan; chains logged + rendered; complements passive dot-connecting — both modes measured); suite = publishable benchmark artifact 'Composition Worlds v1' | folder NH-E21-composition-worlds | — | registered |
| NH-E21b | THE GAME (operator 2026-07-07, flagship build): Composition Worlds as a designed 2D tile game; MECHANIC GRAMMAR composes per-generation mechanics that exist in no training corpus (anti-contamination — closes the pretraining-prior asterisk); interconnected zones, long-range fact separation, branch-probe-only discoveries, AHA gates, ≥1 counterintuitive gate per world (override class); knowledge log first-class; native instrumentation (mechanics discovered, AHA events, overrides, curiosity hit rate, question-retrievals); python tiles + JSON specs + seeds + BabyAI-style GIFs; ships 5-10 worlds + 4-arm ablation harness; benchmark contribution 'Composition Worlds' on the openworld authoring thesis | folder NH-E21b-the-game | — | registered |
| ARM A final | pure-code exam | n=100; 6000–6099 | — | reserved |
| ARM B final | LLM-strategist exam | n=25; 7000–7024 | — | reserved |

## Seed registry

| range | status |
|---|---|
| 101–140, 500–547, 690–699, 700–799 | dev (Campaign 1 + 2) |
| 1000–1004 | official 5-ep protocol block (v1, spent) |
| 2000–2024 | v1 scored block (spent) |
| 3000–3079 | v1.1 scored block (spent) |
| 4000–4079 | NH-C2.1 checkpoint block (spent as of 2026-07-07) |
| 4000–4004 / 5000–5004 / 6000–6004 | touched once by v1 memory passes 1–3 (disclosed) |
| 5000–5024 | blind-arm frozen block (spent) |
| 6000–6099 | **RESERVED: Phase E confirmatory. Do not touch.** |
| gym harvest | any spent/dev seed via reset+action-prefix replay; NEVER scored ranges for score |

## Standing rules

- **Model provenance (operator standing rule, 2026-07-07):** track WHICH model
  did the work, per experiment and per artifact. Every experiment README +
  ledger row carries a MODEL field (model + reasoning effort that designed/
  synthesized/analyzed it); model handoffs mid-experiment are logged at the
  phase boundary ("phases 1-2: Fable 5 max; phase 3+: Opus 4.8 max thinking").
  Rule cards + principles carry model provenance (who inferred/authored).
  Arm B consultation logs add the model id per consultation (strategist model
  may differ from synthesis model). Reports state the model roster in their
  methods line. Rationale: synthesis-model tier is the program's own binding
  variable (Baba 65.8→100), and Opus-4.8-max is the registered fallback if
  Fable caps.

- **Clean protocol:** reset/step + served obs only in the scored loop;
  offline source-derived tables permitted and disclosed; no env internals.
- **Drop rule:** a lever ships only if it clearly pays on its validation
  (score primary at ≥20 paired dev episodes pre-Phase-L; avoidable-damage
  primary + score secondary during Phase L). Dev-noise selects seed luck —
  proven three times in this program.
- **Verification stack** (each layer catches what the others miss):
  snapshot unit fixtures (exact next-state for deterministic mechanics,
  support/frequency constraints for stochastic; every fixed bug becomes a
  fixture) → play-time possibility-set checks with violation-rate tracking
  (dev/gym episodes only) → distributional verification gate (α=0.01,
  train/holdout split) for any stochastic rule entering the decision layer
  → ledger regression harness (`c2_ledger_checks.py` D1–D5) after every
  dev block. Suite must be green before any freeze.
- **Rule cards:** every heuristic/constant in the decision layer carries
  {statement, mechanism class, evidence(n + source), holds_in% [CI], scope,
  status: verified/provisional/prior-only, provenance}. Code docstrings
  point at their card (code-as-bridge standard).
- **Gym guardrails:** operates on dev/harvested seeds only; scored blocks
  are never replayed-for-score; all gym learnings enter the policy as
  general code passing the ≥3-different-seed generalization gate.
- **Deliberate play:** LLM plays dev-seed envs directly for mechanism
  discovery; transcripts are development artifacts; the scored agent
  remains pure code (no LLM calls at test time).
- **CIs:** `bootstrap_ci.ci95()` (10k, seed 20260706) everywhere.
- **Runs ledger:** every scored/dev block appends config + md5s to
  results/RUN_LOG.txt before launch.

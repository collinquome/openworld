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

## The core loop: PROPOSE → COMPILE → BACKTEST → DEPLOY (operator directive 2026-07-07 s3 — the program's architecture statement; MODEL: Fable 5 max s3)

The pattern the whole program has been circling, stated once (this is the
precise answer to "how do you combine LLMs with backtestable code
strategies"; it deepens NH-E28 and incorporates the ARC-3 lessons):

1. **PROPOSE (INTUITION).** The LLM emits proposals in STRUCTURED form —
   goals as procedure sketches, strategies as objective stacks/playbook
   candidates, principles with scope conditions, hypotheses as claims
   with falsification handles. Free-form narrative is for the consult
   log; the proposal object is typed. (SAMPLE-10-PICK-1 applies at the
   proposal moment; the rejected 9 go on the idea shelf.)

2. **COMPILE (PROCEDURE).** Every proposal gets a CODE TWIN immediately:
   a goal becomes an executable checker (ARC-3 lesson 5 / E97
   goal-as-code — the hypothesis IS a candidate verifier); a strategy
   becomes a policy fragment behind a flag; a principle becomes a rule
   card with machine-readable scope; a world-model claim becomes a
   possibility-set rule (c2_violations pattern). Uncompilable proposal ⇒
   under-specified proposal — send it back to the intuition layer.

3. **BACKTEST (MEMORY × PROCEDURE) — the gap we are uniquely positioned
   to fill** (the ARC-3 attacks were within-run; we hold corpora).
   Three channels, cheapest first, each a no-risk filter:
   (i) **HISTORICAL REPLAY** — run the compiled artifact against the
   logged corpus (275+ episodes, 500k+ transitions): "would strategy X
   have changed outcomes?" Counterfactual evaluation against transition
   logs is nearly free and nobody does it. (Existing instances of the
   pattern, now recognized as such: c2_avoid's counterfactual audit,
   the CAST-HUNGER retro quantification, c2_violations offline, E12
   backfill. The E28 goal-checkers backtest against logged reward/
   near-win events the same way.)
   (ii) **MODEL PLAYOUTS** — K-future determinized simulation through
   the world model (E-NH4b sampling; the DECIDE playout machinery).
   (iii) **GYM/LAB** — real-env scenario batteries (E6 library, E20
   MiniHack, E21b synthetic worlds, E16 branch probes).
   A proposal that fails its backtests never risks a live run; a
   proposal that passes arrives at validation already evidence-carrying.

4. **DEPLOY.** Standard paired dev validation + pre-registered criteria
   + drop-if-unclear + per-block violation/regression gates. Ship ⇒
   standing config + ledger row; drop ⇒ documented verdict + idea shelf.

Instrument mapping: PROPOSE = consultations/reflections (E11/E18/E21b);
COMPILE = rule cards, NH_* flags, goal-checkers (E97-style), scenario
fingerprints; BACKTEST = c2_avoid/c2_violations/E12-style corpus replay +
E-NH4b playouts + E6/E20/E16 batteries; DEPLOY = phasel_block + c2_ab +
drop rule. For NH-E28 specifically: goal hypotheses compile to
reward-checker code, backtest against cross-run reward-event history
(which procedure fragments correlate with already-logged score events),
survivors drive goal-directed MPC — one win then converts inference to
verification (E97).

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
| NH-E15 | strategy state machine (DIVE/EXPLORE/LOOT/FIGHT/FLEE/RECOVER/ESCAPE-UP; carded transition rules; state+transition in ledger + GIF banner) + STALL WATCHDOG (windowed progress metrics: new tiles/depth/xp/hp/action-entropy; escalation: perturbation -> forced transition -> dev/Arm-B LLM consult). Motivating fixture: ~400-turn giant-bat dig standoff -> gym scenario + regression fixture. Phase L: LLM authors/revises the transition table (pre-registered, gym-validated); Arm B adds proactive review ticks (~500 game-turns or on oscillation, logged); Arm A ships the compiled table | always-on, both arms | E15-1 (s3, overnight 40 seeds 700-739 vs DEV-B1): **+0.13 [-0.44,+0.70]**, wd fired 22/40 eps (L1 perturb/L2 disengage, noted), 15/40 action-divergent, hunger deaths **10→5**, no death-class worsening, violations 0/81,125 — all 3 pre-registered criteria PASS; caveat: 7/22 fired-eps byte-identical to ref (disengage no-op without adjacent standoff; perturb can resolve to incumbent target — REPEAT-1 inertness class; rework = goal-market) | **watchdog v1 SHIPPED s3** (NH_E15 in standing config as ROBUSTNESS lever per its pre-registered gate — as progression lever UNCLEAR; DEV-B2 validates in-config); state machine + playbooks still registered |
| NH-E16 | search-as-teacher (operator directive 2026-07-07; flagship: "deterministic replay as an epistemic instrument"): (1) AlphaGo loop in code-space — snapshot (seed,prefix) at high-uncertainty decision points (EV-margin~0 / novel monster / untested matrix cell / stall), branch-explore in replay, distill winning lines into rule cards (≥3-seed gate); metrics: rules-distilled per dev block + their aggregate dev delta. (2) branch-probe mechanics exploration (epistemic save-scumming, dev/gym ONLY) — snapshot-and-try before uncertain interactions (unknown potion/wand/verb/monster contact); teaches GENERAL mechanics (appearances shuffle per seed — never per-episode identities); standard harness for the NH-E14 verb frontier; scored runs get no snapshots, only compiled knowledge transfers. + MECHANIC DISCOVERY LOOP (operator): hypothesis queue per unknown mechanic → minimal isolated test → predict-before-test → PINNED + the micro-test ships as the unit test (world model and test suite co-emerge); discovery transcripts logged; metrics: hypotheses-until-pinned + pinned-coverage-before-exam | dev/gym only; folder NH-E16-search-teacher | — | registered |
| NH-E17 | clean-room rebuild (operator directive 2026-07-07): at Phase-L exit a FRESH agent context rebuilds the agent from knowledge artifacts ONLY (rule cards, priors, lessons, READMEs, reports, KB — docs never source); both agents run the same fresh dev block; rebuild≈incumbent ⇒ docs contain the knowledge; gap ⇒ itemized tacit-knowledge misses. Standing obligation NOW: every card/lesson written to reconstruct the system without its author | runs at Phase L exit — flag operator when exit criteria met | — | registered |
| NH-E18 | connecting-dots memory (operator directive 2026-07-07; LEADS Phase-L priorities with the perceptor backlog): (1) memory substrate — one queryable per-episode store (dossier + item sightings w/ appearances + prices + monster encounters + events timeline); (2) LLM dot-connector at consultation points + between-episode reflection proposes RELATIONAL hypotheses (price-ID via KB price tables, altar-drop BUC, didn't-attack⇒peaceful, level-features⇒branch, key/lock bindings), each a rule card (provenance: inferred) validated via gym/branch-probe before policy trust; (3) two-loop thesis: relational pattern-matching is the LLM's advantage, cheap reliable execution is code's — cleanest both-loops-necessary demonstration in the program. Metrics: relations proposed/validated/refuted per episode; paired impact of validated relations; dots-connected in GIF banners. Refinement (operator): HYPOTHESIS-DRIVEN EXPLORATION — capability/knowledge lands ⇒ dot-connector re-scans dossiers for revalued opportunities ⇒ CURIOSITY OBJECTIVES {hypothesis, target, EV, risk-costed travel cost, abort} priced in the goal market; "LLM decides WHERE, procedures decide HOW"; metric: curiosity hit rate (hypothesis→journey→outcome triples); CURIOSITY GIF banners; QUESTION-DRIVEN RETRIEVAL added as the second retrieval mode (goal-directed: constraint → question → memory query → plan; see NH-E21); CURIOSITY REWARD operationalized: curiosity_value = α·NOVELTY + β·DOT-COMPLETION with calibration loop + E23-bandit allocation — DEMOTED to baseline/explanation layer by operator amendment (felt-sense is the default curiosity engine; see NH-E24) | folder NH-E18-connecting-dots | — | registered |
| PRIORS | versioned prior sets `papers/balrog/priors/` (GENERIC_VIDEOGAME v0.1, NETHACK_SPECIFIC v0.1) + PRIOR VERDICT TABLE (validated/invalidated/untested — invalidations recorded; already: Elbereth-panic INVALIDATED in-interface, XP-grind INVALIDATED for max-rung, loot-usually-good PARTIALLY INVALIDATED) ; feeds T388 K-ladder generic-vs-specific axis | cross-game | v0.1 committed | live |
| NH-E13-KB | local wiki knowledge base: `wiki_kb.sqlite` (FTS5, per T312) + sha256 manifest; experiments query the LOCAL KB only; live WebFetch only ADDS pages (logged) — frozen corpus makes guide-following a controlled experiment | NH-E13 folder | spec committed | registered |
| E-NH4b / E-NH6 / NH-E11 / matrix / suite | Phase-L workstreams | dev only | — | registered |
| STARS | self-set gold stars + give-up-too-hard (operator 2026-07-07, exploratory): intuition declares own session goals pre-play (logged, pursued, celebrated, period-end reviewed; earned-rate ~60-80% = calibrated self-model; ZPD learning-rate hypothesis measured vs fixed goals) + SHELVE as first-class move (condition-tagged deferred curiosity objective on the revaluation trigger; anti-stubbornness: N failed attempts ⇒ mandatory shelve — inverse stall watchdog; shelve→return→win conversion is the metric; give-ups logged with pride) | spec NH-E18 §11-12 | — | registered |
| FIRSTS | novelty awards / firsts ledger (operator 2026-07-07): first-per-{species kill, verb, depth, scenario solve, relation} = logged+celebrated award; store.first SHIPPED (kill/verb/depth live); "BEAT NEW THINGS" standing goal with bounded premium inside ε-ruin + caution gates; firsts-per-episode = exploration-health metric; coverage matrix gamified; trophy-case email material | spec NH-E18 §10 | — | code partly live |
| PARETO | Pareto both senses (operator 2026-07-07): (1) frontier over option menus — prune dominated options, choose on-frontier by goal weights + felt-sense; frontier rendered in playout previews (P(death) vs E[prog], dominated greyed); (2) tail-aware policy — heavy-tailed convex metric ⇒ robust estimators (the E23 rationale, stated), cheap-lottery-ticket portfolio (max tail capture s.t. P(death) bound = E-NH4b ε-constraint), outcome-distribution-shape tags in scenario fingerprints (mean-regime vs tail-regime strategies differ) | spec NH-E15 README | — | registered |
| DECIDE | standard decision pattern (operator 2026-07-07): suggest-don't-dictate (bidirectional authority, logged overrides) + play-it-out-first (K world-model playouts per menu option summarizing possibility-space regions per goal dimension; shares E-NH4b sampling) + goal-weighted choice (Arm A) / intuition-read choice (Arm B) + playout-vs-realized calibration as a world-model metric; playout preview panel in renders | spec NH-E15 README | — | registered |
| RECALL | reminder/recall loops + recognition-primed decision (operator 2026-07-07 ×2): push-mode memory (cue→memory index, REMINDERS section in CONTEXT_SPEC v0.2, fired→influenced hit-rate tunes index) + scenario fingerprints with continuous recognizer — "I've seen this before" = first-class event forcing strategy (re)selection via the resolution chain; gym library doubles as recognition corpus; PRACTICE-TRANSFER metric (recognition→correct-strat application) | spec NH-E18 §8-9 | — | registered |
| RESOLUTION | strategy resolution order (operator 2026-07-07): most-specific-first lookup chain (adversary+context → adversary → situation-class → playbook → principles), evidence gate (pinned specific beats generic; hypothesized specific loses + flags practice priority), fallbacks auto-enqueue lab reps, per-engagement resolution path logged (maturity metric) | spec in NH-E15 README | — | registered |
| PLAYBOOKS | pursuit schedules + activity-mode playbooks + BOSS STRATS (operator 2026-07-07): dynamic goal weights logged as per-role pursuit schedules; named playbooks (XP-FARMING/LOOT-SWEEP/DESCENT/BOSS-FIGHT/ESCAPE) selected by the state machine; per-adversary practiced counters via E20 reps until pinned; boss-strat library = first-class artifact; top-10 death-mass adversary coverage = Phase-L exit-relevant metric | spec in NH-E15 README | — | registered |
| GOALS | goals-are-a-list (operator 2026-07-07): concurrent standing goals with strategist-set weights; market scores candidates by combined contribution across ALL goals (readiness = weight interaction, not gate); objective stack = derived execution plan; per-action goal-contribution vectors logged → death retros attribute goal overweighting | amends NH-E11; spec in CONTEXT_SPEC.md | — | registered |
| CONTEXT | strategist context package (operator 2026-07-07): every LLM consultation gets FULL world map (all visited levels, annotated ASCII from dossiers) + MEMORIES (E18 store: appearances/prices, relations, curiosity hypotheses, context-relevant cards, applicable lessons) + STORY SO FAR (code-maintained narrative) + CURRENT STATE (stats/inventory/strategy state); versioned CONTEXT_SPEC.md; every consultation logs the exact package verbatim | NH-E11-strategist/CONTEXT_SPEC.md v0.1 | — | registered |
| NH-E19 | principles distillation + algorithm selection (operator 2026-07-07): three knowledge artifacts per representation — world model (code), strategies (rules), PRINCIPLES (language, in the strategist prompt): priors/PRINCIPLES.md versioned + evidence-cited, invalidations struck through visibly; ALGORITHM_CATALOG.md (per-procedure card: what-for/preconditions/failure modes) with intuition-layer meta-selection at consultations (selections+outcomes logged → evidence-driven win rates); ablation experiment: strategist WITH vs WITHOUT principles+catalog on Arm-B-style dev blocks = measured value of articulated wisdom; principle-citation logging prunes dead principles; E17 rebuild now tests all three artifacts; DEFEASIBILITY model (operator): principles = defeasible heuristics with intuition-layer override authority under the override protocol (explicit + justified + bounded + outcome-tracked), two-tier safety (hard vetoes non-overridable; memory-bound licenses the override — no bound, no override); E21 gains ablation arm (d) no-override (pre-registered: fails lettuce-class like code-only) | folder NH-E19-principles | — | registered |
| NH-E20 | MiniHack scenario lab (operator 2026-07-07, exploratory mode): des-file-authored micro-scenarios on the same NLE engine (spellcast doctrine, kiting, price-ID, target priority, D5-6 composition); falsification matrices become real-engine suites; learning mode = author scenario → run candidate strategies head-to-head n=50+ → winner becomes carded rule/principle; TRANSFER GATE: lab sets the prior, NetHack dev-block confirms before any role-profile ship; lab→wild transfer rate logged (feeds T387); reuse work/fable_minihack stack; priority: spellcasting + D5-6 melee | folder NH-E20-minihack-lab | — | registered |
| E16-PROBES | verb-grammar probe battery (Wizard 940): cast/zap/quaff/read/wield/puton/fire grammars mapped; RAY_BOUNCE danger card (wall-adjacent lightning zap = caster death, turn 1); cast menu carries Fail%; 'more' dismisses at zero cost; esc exists | 7 probe records in NH-E16/results | grammars pinned; 0 mainline deaths spent | closed 2026-07-07 |
| E16-BRANCH | paired-branch cast-vs-melee (same snapshot, seed 940): cast = 1-turn kill 0 dmg; melee = 3 misses −3 HP | nh_branch.py; determinism gate green | first search-as-teacher paired verdict | closed 2026-07-07 |
| NH-E14 CAST-1 | CAST_ATTACK_V1 paired dev block: 12 Wizard + 8 guard seeds | guards EXACT 0.00 ×8; Wizard 3.12→4.39 (+1.27/seed, 8+/3−/1=0); overall +0.76 [−0.07,+1.80]; ledger caught shop-death class 0→3 (cast skips Really-attack confirm) → CAST_NEVER guard (V1.1) | **CAST-2: ref 3.11→5.53, +2.41 [+0.75,+4.41], 9+/2−, shop deaths 3→0 — FIRST PAIRED CI-LOW > 0 IN PROGRAM HISTORY** | **SHIPPED (NH_CAST, casting roles)** |
| NH-E12 BACKFILL | 163 combat-death retros from cache corpus | ARRIVAL_CONSTRAINT 96/163 (59%) — preparation thesis quantified; per-role: Arch 100%, Priest 82% … Priestess 29%; below-half final stretch 44.2% | e12_retros.json | closed 2026-07-07 |
| NH-E13-KB BUILD | 15 pages fetched (FTS5 + sha256 manifest, add-only idempotent) + kb_prices.json (28 potions/18 scrolls/25 wands/28 rings by base cost + wand ray/beam types) | wiki_kb.sqlite 944KB | price-ID + zap-safety reference live | closed 2026-07-07 |
| NH-E18 v0.1 | memory substrate (nh_store.py: events/items+prices/monster ledger/features/story + ctx_package CONTEXT_SPEC renderer) + reflection pass #1 (seed 990): R1 repeated-layout relation (validated in-episode), R2 question-driven-retrieval demo (hungry→garlic@D2, socket open: no backtrack capability), R3 passive-species evidence; 2 instrument fixes from the pass | traj["store"] serialization live | substrate SHIPPED; dot-connector demonstrated | live |
| WORLD-MODEL | LAYOUT-REPEAT DISCOVERY: vendored NLE seeded gen repeats level layouts — 19/96 consecutive pairs >60% identical explored rows (several 1.0; seed 809 D6=D7=D8) | corpus scan over CAST-1 block | disclosed as eval-substrate fact; NH_REPEAT paired block (n=20): ALL DELTAS EXACT 0.00 — hint fires (logged in 5/5 early episodes) but never diverges an action: explore layer discards the injected target ⇒ MECHANISM INERT as wired (the ARMOR-bug pattern, caught by the fires-vs-effect read); rework = inject as first-class goal, session 2 | inert; **V2 shipped in code session 2** (root cause: _explore honors only frontier-set targets; V2 = first-class goal routing to nearest-to-prediction frontier, 150-step budget, refutation events; smoke diverges actions) — REPEAT-2 verdict: **+0.39 [-0.23,+1.28]**, 12/20 divergent (V1 was 0/20), routing 19/20 eps, best +7.71 s818; mechanism FIXED, effect UNCLEAR ⇒ default-off per drop rule; candidate for goal-market integration |
| NH-E21b ENGINE | composition-worlds engine: grammar + 6 templates + knowledge log + baseline + ablation harness; 9/9 tests | baseline: T1/T5/T6 = 0% (structurally), T2/T3/T4 = 100% | pre-registered design signature confirmed; LLM arms stubbed | engine closed; ablation arms open |
| NH-E22 PASS-1 | departure-explored vs next-level survival (386 events, c2block80) | NULL: Δ −5.1 [−31.3,+20.4], Spearman −0.02, flat quartiles | exploration pays via what it BUYS (xp/AC — see E12 59%), not tiles walked; confound caveats recorded | closed 2026-07-07 |
| NH-E21 | composition worlds (operator 2026-07-07): procedurally-generated discovery worlds with long-range fact separation + composition-required solutions (damage-as-key class); substrates: MiniHack des / minigrid / openworld authoring surface; 10-20 escalating templates + creative-license extras; THE ABLATION (pre-registered prediction: no-intuition and no-memory fail systematically, full stack solves) = controlled Arm-A/B comparison; QUESTION-DRIVEN RETRIEVAL mechanism (constraint → explicit question → FTS5 memory query → answer → plan; chains logged + rendered; complements passive dot-connecting — both modes measured); suite = publishable benchmark artifact 'Composition Worlds v1' | folder NH-E21-composition-worlds | — | registered |
| NH-E21b | THE GAME (operator 2026-07-07, flagship build): Composition Worlds as a designed 2D tile game; MECHANIC GRAMMAR composes per-generation mechanics that exist in no training corpus (anti-contamination — closes the pretraining-prior asterisk); interconnected zones, long-range fact separation, branch-probe-only discoveries, AHA gates, ≥1 counterintuitive gate per world (override class); knowledge log first-class; native instrumentation (mechanics discovered, AHA events, overrides, curiosity hit rate, question-retrievals); python tiles + JSON specs + seeds + BabyAI-style GIFs; ships 5-10 worlds + 4-arm ablation harness; benchmark contribution 'Composition Worlds' on the openworld authoring thesis | folder NH-E21b-the-game | — | registered |
| NH-E22 | exploration→model-quality (operator 2026-07-07, PRE-REGISTERED): held-out model-quality metrics (violation rate, sharpness/set-tightness, pinned coverage, counterfactual reliability) vs exploration budget under none/passive/active-discovery policies; E21b gives exact model-vs-truth scoring; predictions: active>passive at equal budget, quality saturates (knee = optimal explore budget → feeds E14b weights); mediation chain exploration→model→decisions→survival→score measured per-link | folder NH-E22-exploration-model-quality | — | registered |
| NH-E23 | bandit machinery (operator 2026-07-07, Phase-L only): (1) experiment scheduling — Thompson/UCB over lever + lab queues, PAIRED-SEED deltas as reward, robust (median/trimmed) estimators for heavy tails, allocation trace logged, reward+priors registered before running; (2) in-game strategy selection — Thompson over (role×situation) arms in dev play, card win-rates = posteriors, ships as frozen probabilities in Arm A; (3) E14b explore-fraction bandit, curiosity-acceptance bandit, UCB validation targeting | folder NH-E23-bandit-machinery | — | registered |
| NH-E24 | curiosity framings compared (operator 2026-07-07; operator said 'E22', filed as E24 — collision with exploration-model-quality): ARM1 formula (novelty+dot-completion, baseline), ARM2 FELT-SENSE (DEFAULT engine per operator design principle: don't force intuition through a formula bottleneck; judge by fruits, leave internals unmodeled), ARM3 nearest/random-frontier baselines, optional hybrid; same worlds/budgets; realized info gain + downstream model quality + score; formula must EARN its way in by beating felt-sense; mini-instance of compiled-vs-live-intuition | folder NH-E24-curiosity-framings | — | registered |
| NH-E25 | open-mode play (operator 2026-07-07 s2; Cleese 1991): (a) unstructured play sessions — no objectives/stars/scoring, intuition plays and notices; discovery yield (mechanics pinned, relations, hypotheses) vs equal-budget structured practice, PRE-REGISTERED BOTH DIRECTIONS; (b) SECOND-SOLUTION RULE in gym — search past first adequate line, log first-found vs best-found quality delta (measurable creativity dividend); (c) PONDERING PASSES — no-decision reflection consultations, log what pondering surfaces that decision-pressure doesn't | folder NH-E25-open-mode; dev/gym only | — | registered |
| NH-E26 | policy-function evolution (operator 2026-07-07 s2; FunSearch pattern): LLM as mutation operator over SINGLE small functions (readiness gate, threat-cost, descent pacing, kite heuristic); cheap fitness = E20 lab batteries; islands for diversity; survivors still pass paired dev + drop-rule before shipping; mutation tree logged w/ model provenance; never whole-agent evolution | folder NH-E26-policy-evolution; blocked on E20 bootstrap | — | registered |
| AUX-CONSTRUCT | auxiliary construction as strategist move-class (operator 2026-07-07 s2; AlphaGeometry): at impasse, CHANGE THE PROBLEM by adding an element (acquire tool, reposition to corridor, drop-to-lure, dig new route) — explicit option in impasse consultations ("what could you ADD?"); proposals→outcomes logged; E15 L2/consult = trigger site. AlphaGeometry synthetic-data lesson → E21b SYNTHETIC CURRICULUM (hundreds of auto-graded worlds as the intuition arms' gymnasium) | spec in NH-E11 README | — | registered |
| RENEWABLE | renewable-source ledger (operator 2026-07-07 s2, ×2 msgs): replenishment sources as first-class dossier entries {resource, location, mechanism, yield, cooldown, RISK, verified?}; LOOPS verified before planner trust (branch-probe/lab + wiki three-way; verified loop card = resource SOLVED-within-conditions — a food loop answers cast-hunger structurally); FIRSTS/revaluation/FARM-playbook/context-package integration; false-loop guard (depletion/cooldown/risk + breakage conditions). NH mapping: REST-SPOT QUALITY rating (passive regen ⇒ location = spot quality; RECOVER routes to best-rated spot — cheap immediate win vs 57/66 attrition class); features = GAMBLE TABLES (Fountain/Altar/Throne/Sink KB pages + odds extraction + safe-subset validation); scroll-of-charging refill; nurse-heal candidate loop | spec NH-E18 §13; dev/gym validation | — | registered |
| CAST-HUNGER | cast-nutrition economics (operator GIF observation 2026-07-07 s2 — "too hungry to cast" live failure): casting debits NUTRITION (hunger per cast scaling w/ spell level; KB Spellbook page rates; three-way validate); (a) per-cast nutrition debit in food-economy planner (stock thresholds scale w/ cast rate); (b) "too hungry to cast" = PRE-FAIL signal — casters eat at Hungry-tier not Weak-tier (failure arrives mid-fight when the bolt was the plan); (c) cast-blocked fallback doctrine (throw/retreat — option menu never assumes the bolt); retro over cast blocks + lesson card (provenance: operator-observed via GIF reel — the human-observer→hypothesis loop working as designed); general principle: EVERY NEW CAPABILITY IMPORTS NEW COSTS (full resource ledger ships with the verb; E20 batteries gain resource-exhaustion scenario class for zap/quaff/read) | retro DONE: 4/12 CAST-block Wizards hit refusal, 2 hunger deaths, seed 839 = 2759 refusal retries (24% of episode); CAST_HUNGER_V1 built (refusal latch + caster eat-early at Hungry), flag-off regression identical | CASTHUNGER-1: **-1.10 [-2.94,+0.06]** — eat-early V1b CLEARLY NEGATIVE (fires every run, early ration burn ⇒ 'while fainted' deaths; resource-TIMING lesson) ⇒ DROPPED to lab sub-flag; latch V1a retesting alone (CASTHUNGER-2, 4 affected seeds); CASTHUNGER-2 (s3): **+0.00 exact on all 4 affected seeds** — retry loops GONE ('too hungry' events 3169/115/268/465 → 1/1/2/1 = latch triggers only), hunger-death class identical, violations 0/17,319 ⇒ PURE GUARD | V1b dropped; **V1a SHIPPED s3** (NH_CASTHUNGER in standing config; hunger deaths persist — RENEWABLE is the structural fix) |
| NH-E27 | meta-discovery track (operator 2026-07-07 s2, ×3 msgs; long-arc — "where does agent doctrine come from?", meta-twin of the source-blind arm): ground-truth doctrine inventory (40 concepts, v0.1 in folder README) each annotated with its discovery mechanism — taxonomy (a) watching replays / (b) asking-why-on-failure / (c) game analogy / (d) field borrowing / (e) noticing absence / (f) inversion / (g) generalizing a fix / (h) questioning the frame; V1 novel-discovery arm (machinery + open meta-questions + the MECHANISM taxonomy, never the concepts — teach fishing, withhold fish; score concept-recall + time-to-discovery + operator-unseen novel concepts), V2 research arm (discovers doctrine from human knowledge: speedrun/roguelike/coaching/game-learning literature), V1-vs-V2-vs-operator Venn. Sequenced after Phase-L threads mature | folder NH-E27-meta-discovery | inventory v0.1 committed | registered |
| NH-E28 | THE GOAL-INFERENCE BRIDGE (operator 2026-07-07 s3; flagship follow-up post-Phase-E, aimed at the wall Jim's E102-E104 ARC-3 trilogy documented — perfect world models + 3 goal-discovery attacks 0/9, 0/3, 0/3; E103 diagnosis: wins are PROCEDURES not reachable states, state-scored hypothesis spaces optimize the wrong object): (1) procedure-native hypothesis space — goals as procedure SKETCHES (ordered typed steps with holes) proposed narratively by the intuition layer, scored against event-stream paths not end states; (2) TRAINING LADDER with ground truth — E21b grammar extended to OPAQUE-WIN worlds (win = do-X-then-Y / ordered visits / timing windows / negative-conditional / latent-counter), opacity grades O0-O6, we know the answers ⇒ inference-success-vs-opacity = the wall on a dial, then transfer to the real walled ARC-3 games (harness in repo); (3) cross-run induction + memory — sketch posteriors accumulate evidence across attempts via the E18 dot-connector over near-win patterns (his attacks were within-run); + E97 primitive wired in (one win ⇒ induce objective as verified code, inference→verification). 6 pre-registered predictions (incl. wall-replication P1, transfer-both-directions P5, backtest-efficiency P6) in folder README; E28 = sharpest instance of the PROPOSE→COMPILE→BACKTEST→DEPLOY core loop (§above, registered s3) | folder NH-E28-goal-inference-bridge; DESIGN-ONLY now, execution post-Phase-E; coordinator flag REQUIRED before heavy execution | design doc + opacity-ladder spec + P1-P5 committed s3 | registered |
| SAMPLE10 | sample-10-pick-1 ideation primitive (operator 2026-07-07 s2, program-wide standard): at every generative moment generate ~10 diverse candidates (diversity forced across E27 mechanism-classes), select 1 (felt-sense or cheap eval), LOG THE REJECTED 9 (counterfactual ideation record + revivable idea shelf — rejected idea + new evidence = reminder-loop fire) | spec NH-E27 §4; applies to reflection/hypotheses/scenarios/E26 mutations | — | registered |
| DEV-B1 | Phase-L measurement-cadence block 1 (criterion iii 1/2) | standing config frozen+NH_CAST; 700–739 n=40 | mean 5.32; avoidable dmg **6%** (trend 10→8→6); paired vs navfood 39/40 exact-0 (lone divergence = the 1 Wizard, CAST); violation rate 0/119,057 post-scoping | closed 2026-07-07 |
| DEV-B2 | Phase-L measurement-cadence block 1/2 of the POST-SHIP standing config (FOOD2,PRAYFIX,LOS,TOPO,GUARD,CAST,+CASTHUNGER,+E15; clock restarted by the s3 ships) | 700-739 n=40; CONSTRUCTED: 39 eps adopted bit-identical from e15b1 (structural-identity: CASTHUNGER inert w/o refusal events; 1/40 e15b1 eps had refusals) + s715 fresh | mean 5.45; avoidable dmg **5%**; s715 hunger death GONE under latch (died fighting, same prog); violations 0/80,155 | closed s3 |
| DEV-B3 | Phase-L measurement-cadence block 2/2, same config, FRESH seeds (same-seed rerun of a deterministic agent reads nothing) | 740-779 n=40 | mean 5.51; avoidable dmg **5%** (KITE 55/EAT 50/THROW 22/LOS 6); hunger deaths 3/40; violations 0/54,859; **CRITERION (iii) MET: |5-5|=0 < 1pt over 2 consecutive blocks**; trend 10->8->6->5->5 | closed s3 — criterion iii MET |
| SUITE-V | c2_violations.py — play-time possibility-set checker ported from blind arm (criterion v instrument); V_TIME/V_MOVE/V_NONMOVE_POS/V_DEPTH/V_HP_BOUND/V_XP_MONO; first outing found 3 real scope gaps (conf/stun random-walk, level-teleport, god-punishment xp) — all scoped ⇒ **0.00e0 on DEV-B1, criterion (v) PASSES on this block** | offline over any transitions dir | snapshot_suite.py GREEN 18/18 s3 (6 fixed-bug fixtures on REAL code paths — armor-under-@ via live agent + injected recorded messages, corpse-cell + phantom purge, shopkeeper-dpt floor incl. load-bearing regression-flip check, dwarven!=dwarf _cannibal, pet-not-a-wall BFS swap, stale-door correction; + 9 E16 probe integrity + 3 deterministic replays behind verify_determinism gate). Built by Sonnet 5 worker to Fable 5 spec; ~60s wallclock; results/snapshot_suite.log | **CRITERION (iv) MET s3** (suite green; runs per-session) |
| E6-HARVEST | gym scenario library (criterion ii start): 794 branchable death scenarios (55 retro-matched); syllabus TRASH 313 / MELEE+ 161 / STARV 160 / SPIDANT 80 / RANGED 43, all ≥14 distinct seeds | e6_harvest.py → results/e6_scenarios.json | library live; solve loop = session 3 ; SOLVE LOOP v1 live s3 (e6_solve.py): TRASH batch 20 distinct dev seeds -> 11 MISPLAYED / 9 UNRESOLVED (0 errors, 0 replay-divergences; winning backoffs 40:6/120:3/300:2 = shallow decision errors dominate); REST wins 10 seeds => CLASS SOLVE RULE FIRES, disengage-and-recover rule candidate graduates to paired dev block; UNRESOLVED deliberately != UNWINNABLE pending v2 menu (kite/throw/stairs + in-model MC). **SOLVE LOOP v2 s5 (e6_solve_v2.py — KITE/THROW/STAIRS perception-driven + REST/RETREAT + in-model MC gating UNWINNABLE): re-adjudicated all 9 s3-UNRESOLVED TRASH deaths → ALL 9 MISPLAYED, 0 UNWINNABLE; THROW won 4 distinct seeds → THROW_DISENGAGE class-solve rule GRADUATES (the same-speed-adjacent fix the s4 REST threshold tune could not reach — a NEW ACTION not a number). Wired behind NH_CRISIS_THROW (flag-off regression bit-identical, seed 706). MC caught its own value: 712 UNWINNABLE@mc8 → MISPLAYED@mc20. TRASH column: 20/20 adjudicated scenarios avoidable. results/e6_solve_v2_trash.json** | **s6: THROW paired block RUN → DROPPED (delta -0.28 CI95[-0.68,0.00]; 17 live fires on 4 seeds, every materially-divergent seed regressed). The e6 replay OVER-CREDITED THROW — it won at branch-states the live policy never reaches; hurling at a same-speed adjacent monster donates a turn without creating distance. Ships flag-OFF. → model-fidelity meta-card (DOCTRINE_CARDS_s6.md).** solve-loop live |
| MATRIX | coverage matrix formalized (criterion i): 16 cards × 6 classes, death-mass-weighted, N/A excluded, PROVISIONAL=half | coverage_matrix.py → results/coverage_matrix.json | baseline 16.4% s2 -> **23.2% s3** (REST_GATESxTRASH + FLEE_GATExTRASH provisional via e6_solve counterfactuals; STALL_WATCHDOGxSTARV provisional via E15-1 hunger-death halving); 25 open hypotheses; top mass now KITE/WIELD/ARMOR/ZAP x TRASH | live |
| E21b-LIVE | live intuition arm (live_arm.py, replay-interactive; intuition = Fable 5 max, consultations verbatim): **T1 s0 WIN 27 steps/6 consults (baseline 0% structurally); T6 s0 WIN 30 steps/8 consults via UNDESIGNED solution class (never-pick-up beats the possession trap) + probe branch pinned 4/4 mechanics and demonstrated the designed give-up line**; engine leak found+fixed live (obs inventory served ground-truth item_class; tests 9/9 post-fix) | results/e21b_live/ | first live intuition results; T5 + multi-seed + 4-arm ablation open ; s3: T5 s0 LIVE WIN 64 steps/8 consults/3-3 mechanics — solution = reveal-by-sacrifice (eat dark seed: -15 HP buys hidden-zone reveal) + charm-key gate; post-win probe DISAMBIGUATED the confound (wounded-no-charm HOLDS FIRM => charm-keyed) — T5 is the exact INVERSION of T6's possession trap: the pair is a defeasibility test ('never pick up' as RULE fails T5; as per-world HYPOTHESIS passes both — consult-3 verbatim shows the hypothesis discipline). T1+T5+T6 all live-won | T1/T5/T6 live-won s3; NEXT: multi-seed + 4-arm ablation (incl. fresh-context blind instance) |
| SHEET | character-sheet self-model + counterfactual power (operator 2026-07-07 s2, fixes the self-model asymmetry — monster dpt empirical from 160k rows, our dpt = 2 hardcoded constants at nh_percept.py:98): per-attack-option expected dpt+to-hit (source arithmetic + own logged fights) + defense + verb availability → POWER INDEX; power vs depth's empirical threat band = READINESS RATIO (P1 becomes computable: descend when ratio≥threshold, per-role swept); COUNTERFACTUAL POWER: power_index(hypothetical wield/wear of any seen/dossier item) → wield/wear/detour decisions become power-delta arithmetic, item-value perceptor upgrades to computed deltas, revaluation on big deltas, unknown-delta = curiosity value | spec NH-E14-role-modules/CHARACTER_SHEET_SPEC.md; build = TOP of session-3 queue (perceptors lead; closes WIELD/ARMOR matrix cells) | nh_sheet.py BUILT s3: PI = best_dpt x hp; TI(d) = band_dpt x band_hp (damage-mass-weighted bands from the 160k-row c2_cache corpus — coexistence-exposure weighting rejected, it diluted bands to absurdity); RR = PI/TI = (their turns-to-kill-us)/(our turns-to-kill-them), RR>1 = win the representative exchange; tables from FROZEN KB (Weapon 75 entries incl. multi-dice+bonus dice forms, Armor 66, force bolt 2d12 hit d20<AC+10) w/ sha256 provenance; attack options = wield-current/carried/throw/launcher+ammo/spell/unarmed; counterfactual_power = wield deltas live (armor slot economics v0.2); live probe green (dev 805 Ranger: crossbow+bolt 2.01 tops dagger 1.44 from served obs) | **BUILT s3** (logging wire-in + WIELD/ARMOR doctrine + RR-threshold sweep = next; armor CF v0.2) |
| HISTORY | history browser (operator 2026-07-07 s2): per-episode HISTORY.md render (story/firsts/event-ledger/notes channels) + cross-episode KNOWLEDGE_INDEX.md (live-grepped rule cards + principles + loops + syllabus + matrix snapshot) | history_render.py; examples committed (HISTORY_cast2_918, HISTORY_devb1_711, KNOWLEDGE_INDEX) | shipped session 2 | live |
| NH-E29 | potential-based progress reward (operator 2026-07-07 s4): Φ(s)=progress-to-goal proxy (max-depth / depth+RR / coded distance-to-descent), r_shape=γΦ(s')−Φ(s) (policy-invariant, Ng 1999); does dense shaping speed the bandit/strategy-selection LEARNING RATE vs sparse terminal? dev-only, shaping NEVER in scored objective | folder NH-E29; design doc PROGRESS_REWARD_BATTERY.md; MODEL opus-4.8[1m] | design + P1 registered | registered |
| NH-E30 | good-stuff/bad-stuff ledger = KPI-tree reward layer (operator 2026-07-07 s4): enumerate GOOD (depth/xp/AC/food/first/socket/loop) + BAD (avoidable-dmg/hunger-tick/stall/lost-depth/novel-contact) events as signed KPI-node deltas; regress terminal progression on event counts over the 275+ corpus (FREE, historical) → predictive signals become reward terms, vanity metrics dropped | folder NH-E30; design doc | design + P2 registered | registered |
| NH-E31 | closer-to-goal estimator V(s)≈P(reach depth D+k|s) via survival analysis over the transition corpus (operator 2026-07-07 s4); live HUD progress bar toward expected-depth; experiment = calibration (predicted vs realized) + does greedy-V beat the planner on dev | folder NH-E31; design doc | design + P3 registered | registered |
| NH-E32 | reward-term ablation, backtest-gated (operator 2026-07-07 s4): each reward config historical-replay-backtested (does Σreward rank good episodes above bad?) BEFORE any live block; ship only backtest-passers — the anti-reward-hacking loop | folder NH-E32; design doc | design + P4 registered | registered |
| NH-E33 | multi-horizon KPI dashboard (operator 2026-07-07 s4): KPI tree as live 3-tier readout GOAL/DRIVERS/PERFORMANCE + trend arrows, appended per block (KPI-DASH line LIVE s4) + reel HUD corner; instrumentation ties E29-E32 signals into one view | folder NH-E33; KPI_TREE.md | KPI-DASH live s4 | registered |
| NH-E13 FLOOR-ROLE | **wiki-fed floor-role uplift = NH-E13 flagship "does the strategy guide help?"** (operator 2026-07-07 s5): mean-leverage = frequency × headroom; floor roles win both (Healer ~2.15 @~12%, Tourist ~1.10 @~7%, Priest/Priestess ~2–3.4 vs near-capped Samurai 11.75/Barbarian 9.32). 1.10 = OUR combat-forward policy failing the Tourist (they ascend in real play), not the role ceiling → distinct per-role playbooks selected at episode start from the role census. Wiki-fed: extract each role's documented survival doctrine → provenance:wiki rule cards → role-stratified validation → track WIKI-ATTRIBUTABLE Δ (the controlled wiki-vs-none number NH-E13 has owed) | KB EXPANDED s5 (kb_build.py add-only): Tourist(18282c)+Cleric=Priest/Priestess(19969c) added, Healer(16388c) present — sha256/rev-id, FTS5 17 pages. Cards in DOCTRINE_CARDS_s5.md (HEALER pacifist+cast-heal+stethoscope; TOURIST extreme-caution+dart-bridge+item-reliant; PRIEST BUC-detect+#turn+AC-focus). Seed harness: role_census 800-999 + ext 1100-1899 (role_seeds.py); pools Healer 83/Tourist 65/Priest 45/Priestess 30 (n≥15 stratifiable) | **cards + KB + seed pools s5; profile wire-in + role-stratified blocks = HANDOFF_6 (proximal KPI = per-role mean + survival@D5; per-role mean table each block)** |
| NH-E34 | COMMUNITY CORPUS — forums beyond the wiki (operator 2026-07-07 s5): extend KB with r/nethack, rec.games.roguelike.nethack (rgrn), wiki Talk pages, known strategy guides. Different KNOWLEDGE TYPE: forums carry EXPERIENTIAL/tactical knowledge (how experts actually survive early, death post-mortems, situational judgment) that reference pages lack. provenance:forum (distinct tag), sha256 snapshots, FTS5; three-way validation (forum claim vs our data vs gym) — no trust exemption. Grows the "which KIND of external knowledge helps": wiki(reference) vs forum(experiential) vs none, by provenance tag | folder NH-E34; design-stage; sequence AFTER floor-role uplift | registered s5 |
| NH-E35 | LEARNING FROM DEMONSTRATION via ttyrecs (operator 2026-07-07 s5): KEY INSIGHT — NetHack ttyrecs are demonstrations IN OUR EXACT OBSERVATION SPACE (public servers alt.org/hardfought store millions of games incl. thousands of ascensions as ttyrec = the SAME tty_chars our agent consumes → NO video→world mapping needed). Mine for (a) per-role human strategies (see how experts play a Tourist), (b) action sequences at decision points → behavioral priors/boss-strat corpus, (c) the action-space gap (what experts DO that we never do). Design: ttyrec parser → (obs,action,next_obs) stream → THREE sub-experiments (one parser, sequence 35a first = cheapest+highest value): **35a WORLD-MODEL VALIDATION** — replay expert ascension ttyrecs through our symbolic model + run c2_violations on REAL human deep-game transitions (edge cases our shallow max-D21 play never reaches; extends "0/233k" to millions across the FULL game; each violation → fix + snapshot fixture); **35b STRATEGY VALIDATION** — audit our rule cards/principles (incl. the s5 floor-role wiki cards) against what WINNERS actually do, per-principle corpus-confirmation rate (experts-violate = red flag); **35c STRATEGY DISCOVERY** — mine the behavioral gap where WE DIE but experts SURVIVE (death-class decision points: same-speed-adjacent trash / low-HP crisis / D5-6 kill zone) → candidate rule cards via propose→compile→backtest(e6 battery)→deploy (imitation-INFORMED, extract-mechanism not blind-clone). provenance:demonstration; per-role sliced (expert Tourist games feed floor-role uplift). CLEAN-PROTOCOL: public human data OFFLINE (like reading source/wiki — disclosed); scored runs pure-code/clean; flag before heavy corpus download. General pixel-video→world mapping = T390 future-work note | folder NH-E35 (README: 35a/b/c + P1-P4); design-stage; sequence AFTER floor-role uplift | registered s5 |
| NH-ADVISORY | ADVISORY-PUSH / LLM-strategist on REAL NetHack (s8, opus-4.8[max]) — the never-run intuition-in-loop test on NetHack itself (prior intuition = composition worlds). Code hands a live LLM (headless `claude -p`, Max OAuth) the CONTEXT_SPEC package + rule-base pushed ADVISORY reminders (RB.reminders_text) at low-freq triggers; executes the structured strategy (DESCEND/EXPLORE/DISENGAGE/REST/FIGHT/PRESS_ON) via bias hooks. nh_strategist.py + NH_ADVISORY | paired off/on, one seed/process, cap 1800, n=5 mixed fragile | **paired Δ prog -0.0011 (3 bit-identical, 833 D5->D6, 812 D6->D4), maxD 5.80->5.60, 29 consults @5.8/ep 100% parsed; mechanism VERIFIED (HEAL_MIDBAND pushed+cited)** | **NULL — ships flag-OFF; s8 gate (b) USES-but-doesn't-improve** |
| NH-READY_GATE | role-conditioned readiness gate before descend (s8, opus-4.8[max]): fragile (digger-exempt) rest-to-buffer when nh_sheet RR(d+1)<thresh vs depth_threat.json. NOT the s4 XP-pace-gate (HP not XP). NH_READY_GATE | n=9 Tourist/Wizard/Rogue paired, cap 3000 | block Δ +0.0055 = ONE seed (847), A/A-proven cross-seed process artifact; heavy-fire seeds prog-identical; inert (existing rest gate already tops to 85-92% HP; deficit is RR~0.07-0.16) | **DROP — sixth converging local/arrival lever** |
| NH-E36 | SCENARIO STRATEGY SYNTHESIS (operator 2026-07-08, claude-opus-4-8[max] — the systematic large-search version of the 13 hand-designed single levers): for each recurring HARD SCENARIO, GENERATE many diverse candidate strategies (LLM, the tier-sensitive step — built Fable-ready, run on Opus now), SIMULATE/RANK them across many sampled instances, COMPILE the winner to a fast rule card, DEPLOY behind a flag. = search-as-teacher (E16) + best-of-N (SAMPLE10) + expert-seeding (hand levers seeded as incumbents). DECOUPLED architecture: STRATEGY (pol_*, no baked qualifier) / SCENARIO SIGNATURE (predicate classifier) / SELECTOR (the sim survival MATRIX → top strategy per scenario; qualifier is LEARNED not hand-coded). Files: e36_candidates.py (20-strategy pool, 12 SYNTHESIS + 8 DEMONSTRATION), e36_simulate.py (branch-replay matrix fill, fresh-env/candidate, dev seeds only), e36_compile.py (winner→rule card + crisis_predicate), e36_paired.py (E36Agent subclass injected via monkeypatch — ZERO edits to shared nh_agent.py) | TRASH first scenario, N=18 distinct-seed matrix, backoff 40 window 400; DEPLOY paired REF vs +NH_E36 cap 1500 | **RANKING: WINNER=CORRIDOR (SYNTHESIS, attacker-count mgmt) survival 0.50 vs KITE hand-lever 0.28 = Δ+0.22 — a synthesized strategy BEATS hand-design in robust replay. CAVEATS: FIGHT_NEAREST null-control TIES at 0.50 (finding = stand/funnel-and-fight > flee, not uniquely CORRIDOR); 3/18 seeds 0-survivors-across-all-20 = bootstrapping-UNWINNABLE for hardest instances; HYBRID composite UNDERperforms single-best (7th); ELBERETH interface-limited as logged. Flag-OFF bit-identical VERIFIED. Live-mean paired block = the model-fidelity gate (s6 THROW over-credit precedent).** | **mechanism + first proof SHIPPED; live-mean verdict pending block** |
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

# NH-E27 — The meta-discovery track (REGISTERED, long-arc; operator directive 2026-07-07 session 2, ×3 messages)

MODEL: Fable 5 (max reasoning) — registration + ground-truth inventory v0.1.

**Premise:** everything the operator injected as doctrine should ultimately be
DISCOVERABLE by agents. The paper section this feeds: **"Where does agent
doctrine come from?"** — the meta-level twin of the source-blind arm (there:
world knowledge; here: LEARNING-PROCESS knowledge).

## 1. Ground-truth doctrine set (the benchmark for doctrine discovery)

Inventory of operator-injected concepts, each annotated with its DISCOVERY
MECHANISM (taxonomy §2) — we have the actual history in the session logs.
This inventory doubles as the design documentation of the 2026-07-07
directive burst.

| # | concept | registry home | discovered via (§2) |
|---|---|---|---|
| 1 | readiness principles (level up before down; enter floors at max readiness) | P1–P4 | (b) asking why on failure (E12: 59% arrival-constraint) |
| 2 | wield/armor doctrine (use what you carry) | P2/P3 | (e) noticing absence (0 wields ever) |
| 3 | situation gym / replay-the-hard-stuff | E-NH6 | (d) borrowing (sports/speedrun practice culture) |
| 4 | death retrospectives + typed lessons | NH-E12 | (b) asking why on failure |
| 5 | avoidability audits (moment-level counterfactuals) | E-NH1b | (b) + (h) questioning the frame |
| 6 | trajectory avoidability (prep-path counterfactual) | NH-E12 ext | (f) inversion of the 5% moment-read |
| 7 | search-as-teacher (branch replay distills rules) | NH-E16 | (d) borrowing (AlphaGo) |
| 8 | mechanic discovery loop (predict-before-test, micro-tests become unit tests) | NH-E16 | (d) borrowing (experimental method) |
| 9 | clean-room rebuild (docs must reconstruct the agent) | NH-E17 | (h) questioning the frame (is knowledge IN the docs?) |
| 10 | connecting-dots memory + relational hypotheses | NH-E18 | (d) borrowing (human insight phenomenology) |
| 11 | curiosity objectives / hypothesis-driven exploration | NH-E18 | (c) analogy (scientist's field trip) |
| 12 | felt-sense curiosity as default engine (formula must earn its way in) | NH-E24 | (h) questioning the frame |
| 13 | question-driven retrieval (constraint → question → query → plan) | NH-E18/E21 | (d) borrowing (research practice) |
| 14 | reminder/recall loops (push-mode memory) | RECALL | (d) borrowing (spaced cueing / human memory) |
| 15 | recognition-primed decision + option menus | RECALL | (d) borrowing (Klein RPD) |
| 16 | strategy resolution order (most-specific-first + evidence gate) | RESOLUTION | (d) borrowing (dispatch/case law) |
| 17 | playbooks / pursuit schedules / boss strats | PLAYBOOKS | (c) analogy (sports playbooks, boss patterns) |
| 18 | goals-are-a-list (concurrent weighted goals) | GOALS | (h) questioning the single-objective frame |
| 19 | full-picture context package (map+memories+story+state+reminders) | CONTEXT | (b) (consultations failed on room-local summaries) |
| 20 | defeasible principles + override protocol | NH-E19 | (d) borrowing (defeasible logic / jurisprudence) |
| 21 | algorithm catalog + meta-selection | NH-E19 | (d) borrowing (design patterns) |
| 22 | composition worlds / anti-contamination game | NH-E21/21b | (c) analogy (Fez; escape rooms) |
| 23 | exploration→model-quality mediation chain | NH-E22 | (h) questioning "exploration is good" directly |
| 24 | bandit machinery for scheduling + strategy selection | NH-E23 | (d) borrowing (bandits) |
| 25 | firsts ledger / novelty awards | FIRSTS | (c) analogy (achievements/trophies) |
| 26 | self-set gold stars (ZPD curriculum) | STARS | (d) borrowing (pedagogy: zone of proximal development) |
| 27 | give-up-too-hard / shelve as first-class move | STARS | (f) inversion of stubbornness (anti-stall watchdog twin) |
| 28 | open-mode play / second-solution rule / pondering | NH-E25 | (d) borrowing (Cleese 1991) |
| 29 | policy-function evolution | NH-E26 | (d) borrowing (FunSearch) |
| 30 | auxiliary construction (change the problem at impasse) | AUX-CONSTRUCT | (d) borrowing (AlphaGeometry) |
| 31 | renewable-source ledger / verified loops / rest-spot quality | RENEWABLE | (c) analogy (Zelda rupee loops) |
| 32 | capability-imports-costs (verb ships with its resource ledger) | P7 / CAST-HUNGER | (a) watching replays (GIF reel) |
| 33 | coverage matrix (hypothesis × scenario, death-mass-weighted) | matrix | (e) noticing absence (untested cells) |
| 34 | world-model test suite / every-bug-a-fixture | suite | (g) generalizing a specific fix (armor-under-@) |
| 35 | Pareto option frontiers + tail-regime strategy tags | PARETO | (d) borrowing (multi-objective opt) |
| 36 | standard decision pattern (playout previews, suggest-don't-dictate) | DECIDE | (d) borrowing (MPC/planning) |
| 37 | four-layer architecture naming | program doc | (h) questioning the frame (what IS the agent?) |
| 38 | model provenance stamping | standing rule | (b) (synthesis-model tier moved Baba 65.8→100) |
| 39 | sample-10-pick-1 ideation primitive | §4 below | (d) borrowing (best-of-N + diversity forcing) |
| 40 | meta-discovery itself | NH-E27 | (h) questioning the frame, recursively |

## 2. Discovery-mechanism taxonomy (operator addendum — this is V1's SEED)

(a) WATCHING REPLAYS (cast-hunger spotted in a GIF; static-enemies challenge)
(b) ASKING WHY ON FAILURE (death retros ← "why are we dying")
(c) ANALOGY FROM OTHER GAMES (Zelda→resource ledger; Fez→composition worlds;
    boss patterns→practice reps)
(d) BORROWING FROM OTHER FIELDS (AlphaGo→search-as-teacher; Cleese→open mode;
    FunSearch→policy evolution; Shannon→the program; RPD→recognition)
(e) NOTICING ABSENCE (never sprints; never casts; 50/248 verbs)
(f) INVERSION (give-up-too-hard ← stubbornness; trajectory-avoidability ←
    the 5% moment-read)
(g) GENERALIZING A SPECIFIC FIX (armor-under-@ → silent-subsystem detectors)
(h) QUESTIONING THE FRAME ("is the curiosity formula right?" → E24)

**The honest benchmark: V1 gets the MECHANISMS (how to ideate), never the
CONCEPTS (what) — teaching fishing, withholding fish.**

## 3. Arms

- **V1 — NOVEL DISCOVERY:** fresh agent with the learning MACHINERY
  (reflection, gym, memory) but NONE of the doctrine concepts; prompted only
  with open meta-questions at reflection time ("what should I systematically
  track? what practice would make me better? what am I doing wrong
  repeatedly?") + the §2 taxonomy. Measures: concept-recall rate vs the
  ground-truth set, time-to-discovery per concept, and the exciting column —
  NOVEL concepts the operator didn't think of.
- **V2 — RESEARCH ARM:** agent discovers doctrine by studying human knowledge
  (speedrunning practice culture, roguelike strategy communities,
  game-learning literature Shannon onward, sports-coaching methodology) and
  adapts concepts. Same scoring + novelty column.
- **Comparison:** V1 vs V2 vs operator-set overlap Venn — which concepts come
  only from play, only from research, only from a human watching GIFs at
  midnight.

## 4. SAMPLE-10-PICK-1 (program-wide ideation primitive, operator directive)

At every generative moment — reflection ideas, hypothesis generation,
scenario design, felt-sense exploration targets, E26 mutations, doctrine
candidates — generate ~10 DIVERSE candidates cheaply (diversity requirement:
force different §2 mechanism-classes across the 10), then select 1
(felt-sense or cheap eval, whichever fits). **LOG THE REJECTED 9:** they are
the counterfactual ideation record (selection-quality measurement later:
did we pick the right ones?) and a shelf of pre-generated ideas that later
contexts can revive (rejected idea + new evidence = a reminder-loop fire).
Best-of-N with diversity forcing and a receipts drawer.

## Sequencing

After current Phase-L threads mature — the machinery must exist before an
agent can discover how to use it better. Registry row now; this inventory
maintained as directives land (every new operator concept gets a row + a
mechanism annotation at registration time).

Status: registered; inventory v0.1 (40 concepts). Not started.

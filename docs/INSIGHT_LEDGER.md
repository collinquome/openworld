# Insight Ledger — where each idea originally came from
Tracks INSIGHT provenance (origin of the IDEA) — distinct from KNOWLEDGE provenance (origin of the FACT, tagged on rule cards: wiki/source/mined/gym/demonstration/inferred).
Origin codes: OP=operator (Collin) · AG=agent-discovered-from-play · PAPER=borrowed from literature/other program · ANALOGY=cross-game/domain analogy · WIKI=strategy guide · DATA=fell out of our own results.
Discovery-mechanism taxonomy (from NH-E27): WATCH-REPLAY / ASK-WHY-ON-FAILURE / ANALOGY / BORROW-FIELD / NOTICE-ABSENCE / INVERSION / GENERALIZE-FIX / QUESTION-FRAME.
Honest note: a large share of the program's architecture originated with the operator across the 2026-07-07 design session. Attribution is graded; where an agent CO-developed, both are credited.

## Architecture & method
| Insight | Origin | Mechanism | Became |
|---|---|---|---|
| Four-layer architecture (perception/memory/intuition/procedure) | OP | QUESTION-FRAME | program's core frame |
| Intuition layer = LLM as felt-sense judge | OP | ANALOGY (human cognition) | E21b live arm, Arm B |
| Defeasible principles (override authority, bounded by memory) | OP | INVERSION | T5/T6 defeasibility result |
| propose→compile→backtest→deploy core loop | OP+AG | BORROW-FIELD (markets backtest + games verify) | program architecture statement |
| KPI tree (goal/drivers/performance) + potential-based reward | OP | QUESTION-FRAME | KPI_TREE.md, E29-E33 |
| Goals as a weighted concurrent LIST (not a stack) | OP | NOTICE-ABSENCE | goal-market design |
| Recognition-primed decisions → option menus (fight/run/sprint) | OP | ANALOGY (RPD, expert play) | strategy resolution |
| Strategy playouts ("do I like this region of possibility space?") | OP | ANALOGY (imagination/planning) | decision pattern |
| Curiosity: felt-sense default, not a formula (Goodhart risk) | OP | QUESTION-FRAME | NH-E22 |
| Multi-armed bandit allocation over levers/strategies | OP | BORROW-FIELD | Phase-L allocation |

## Experiments the operator seeded
| Insight | Origin | Mechanism | Became |
|---|---|---|---|
| Max-reasoning synthesis is the claim under test | OP | QUESTION-FRAME | the tier ablation (65.8→100) |
| Memory-across-attempts hypothesis | OP | ANALOGY (human learning) | the memory law (4 testbeds) |
| "Was this damage avoidable?" | OP | ASK-WHY-ON-FAILURE | avoidability audit (5% finding) |
| Situation gym / replay-the-hard-stuff | OP | ANALOGY (drill practice) | E-NH6 gym, THROW fix |
| Death retrospectives ("what's the lesson?") | OP | ASK-WHY-ON-FAILURE | NH-E12 |
| Composition worlds (Fez/Outer-Wilds-class) | OP | ANALOGY (knowledge-gated games) | NH-E21b The Game |
| Weight exploration higher / readiness before descent | OP | ASK-WHY-ON-FAILURE | trajectory-avoidability, floor-role |
| Resource/recharge loops (Zelda rupee farm) | OP | ANALOGY | renewable-source ledger |
| Character sheet / "how strong could I be with X" | OP | NOTICE-ABSENCE | nh_sheet, counterfactual power |
| Floor-role uplift (spend time on Tourists) | OP | DATA (per-role means) + QUESTION-FRAME | NH-E13 flagship, s6 Healer |
| Wiki strategy guides | OP | BORROW-FIELD | NH-E13, CAST doctrine |
| Forums (experiential knowledge) | OP | GENERALIZE-FIX (of the wiki idea) | NH-E34 |
| ttyrec demonstrations (watch expert games) + 3 uses | OP | ANALOGY (imitation) + QUESTION-FRAME | NH-E35a/b/c |
| Meta-discovery (agents rediscover the doctrine) | OP | QUESTION-FRAME | NH-E27 |
| Sample-10-pick-1 ideation + diversity | OP | BORROW-FIELD (best-of-N) | ideation primitive |
| Cast-hunger death mode | OP | WATCH-REPLAY (spotted in a GIF) | CASTHUNGER lever |

## Borrowed from the ARC-3 sibling / literature
| Insight | Origin | Became |
|---|---|---|
| Verification gates make synthesis trustworthy | PAPER (ARC-3 recipe) | clean-protocol + distributional gates |
| Goal-as-code / reward induction (E97) | PAPER (ARC-3) | death-recognizers; NH-E28 win-rule |
| Select-don't-vote (E95) | PAPER (ARC-3) | model-selection everywhere |
| Search-as-teacher (distill search into policy) | PAPER (AlphaGo) | NH-E16 |
| Policy-function evolution (LLM as mutation op) | PAPER (FunSearch) | NH-E26 |
| Auxiliary construction (add an element when stuck) | PAPER (AlphaGeometry) | strategist move-class |
| Open-mode play, second-solution rule | PAPER (Cleese 1991) | NH-E25 |
| The goal-inference wall (procedures not states) | PAPER (ARC-3 E102-104) | NH-E28 frontier target |

## Agent-discovered (from play) & data-driven
| Insight | Origin | Mechanism | Became |
|---|---|---|---|
| Capability-bound not decision-bound (5% avoidable) | AG+DATA | the avoidability audit ran | program redirect to verbs |
| 50/248 verbs ever used → spellcasting frontier | AG (action audit) | NOTICE-ABSENCE | CAST lever |
| Same-speed-adjacent → can't flee trash | AG | ASK-WHY-ON-FAILURE (REST drop) | THROW menu |
| Pet-is-a-door, dwarven≠dwarf, armor-under-@, shopkeeper-dpt | AG (debugging) | GENERALIZE-FIX | regression fixtures + detectors |
| NLE repeats level layouts across depths | AG | DATA | disclosed world finding |
| n=5 leaderboard rankings are seed noise | AG+DATA | the CI discipline | statistics-as-a-finding |
| Elbereth unreachable (missing minus key) | AG | DATA (action-space probe) | benchmark defect |

## Session-6 insights (full recipes — NH-E27 test corpus)
Format: {insight · knowledge-prov · insight-origin · mechanism · replication recipe}.

- **A replay-validated lever can be live-inert-or-negative** (the backtest over-credits it). knowledge: data(our e6+paired blocks). insight-origin: AG+DATA. mechanism: WATCH-REPLAY + NOTICE-ABSENCE + ASK-WHY-ON-FAILURE. recipe: "take a rule that WON on replayed historical death-states (e6_solve v2: THROW survives 4 trash pre-death branch states) → wire it live behind a flag → run a paired block on the SAME winning seeds + fresh → count LIVE fires from the ev_log (not stdout) → observe (a) it fires on DIFFERENT seeds than the replay-winners and (b) where it fires it regresses (s6 THROW delta -0.28, every divergent seed negative) → conclude the historical-replay channel evaluated the action from states the live policy never reaches, and its deterministic single-combat-sample hid the turn-donation cost." This is the model-fidelity-for-strategy-training result: backtest proposes, live paired block disposes.
- **Lever-fire counting off stdout is always 0 because note()/_ev() buffer to lists, not print.** knowledge: data(code). insight-origin: AG. mechanism: ASK-WHY-ON-FAILURE. recipe: "grep the run log for a lever's fire-note → find zero despite the subgoal ledger showing that lever's goal set as the final decision → open note()/_ev() → see they append to self.notes/self.ev_log, never call self.log → fix: surface counts in the result dict (nh_runner throw_fires/heal_fires) or recover from the traj evs." (Found while smoke-testing the Healer heal — the goal appeared but no note line did.)
- **Healers carry a never-used SUSTAIN capability (cast healing) = pure headroom.** knowledge: wiki(Healer page) + data(verb-frontier). insight-origin: WIKI + DATA. mechanism: BORROW-FIELD + NOTICE-ABSENCE. recipe: "read the Healer wiki page → note 'cast healing for survival, best pacifist role' → check our verb-utilization audit: cast_heal fires = 0 ever across the corpus → wire heal-casting (self-target spell, no direction) behind a role profile → measure Healer survival delta on a role-stratified block (role_seeds Healer pool)." Wired s6, mechanism confirmed (seed 828 heal_fires=2, menu parsed, cast at hp 9/21 & 4/21).

## How to maintain
Every new experiment README + rule card + principle records BOTH provenances: knowledge-source (existing tag) AND insight-origin (this ledger's codes) + discovery mechanism. Append here as insights land. This ledger IS the ground-truth for NH-E27 (can an autonomous agent rediscover these? tagged by who found them first).

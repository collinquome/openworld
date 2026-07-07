# NH-E15 — Strategy state machine + stall watchdog (REGISTERED, Phase L; always-on, both arms)

**Architecture (operator directive):** strategy becomes an explicit state machine — DIVE / EXPLORE / LOOT / FIGHT / FLEE / RECOVER / ESCAPE-UP — with if-this-then-that transition rules as provenance-tagged rule cards, e.g.:
- "HP<40% AND adjacent threat -> RECOVER"
- "no new tiles AND no depth change for 150 turns -> switch exploration mode / force frontier goal"
- "pick-axe acquired -> DIVE"
- "food < threshold -> prioritize EAT/LOOT"

Current state + last transition go in the subgoal ledger and the GIF strategy banner. Every transition rule is pre-registered and gym-validated like any mechanism.

**STALL WATCHDOG (mandatory component):** windowed progress metrics — new tiles, depth delta, xp delta, hp delta, action-repetition entropy. Stall triggers escalating responses: perturbation -> forced strategy transition -> (dev/Arm B only) LLM consult.
**Motivating fixture:** the ~400-turn giant-bat standoff in the dig-death episode (v1 condition-A Archeologist, `animations/clean_A__ep4_archeologist_digdeath.gif`) — that episode should have transitioned three times (FIGHT->FLEE->DIVE-elsewhere). Harvest as gym scenario + permanent regression fixture.

**LLM roles:** Phase L — the LLM authors and revises the transition table (each rule carded + validated). Arm B additionally runs PROACTIVE REVIEW TICKS: every ~N game-turns (N~500, tuned) or on transition-oscillation, the strategist reviews a state summary and may proactively override strategy/objective; all consultations logged verbatim. Arm A scored runs stay pure code — the compiled transition table IS the strategist.

## Operator consolidation (2026-07-07): pursuit schedules, playbooks, boss strats

1. **PURSUIT SHIFTS OVER TIME:** goal-list weights are DYNAMIC — re-set at
   consultations and by state-machine transitions; minute 5 (stronger/loot)
   ≠ minute 40 (descend/survive). Weight trajectories logged per episode;
   the weight-over-time curve per role is a learnable artifact (the
   "pursuit schedule").
2. **ACTIVITY-MODE PLAYBOOKS:** named strategies per activity — XP-FARMING
   (safe-species grinding at chokes), LOOT-SWEEP, DESCENT (risk-minimal
   stairs-seeking), BOSS-FIGHT, ESCAPE. Each playbook = parameter set +
   tactics + termination conditions; the state machine selects playbooks;
   felt-sense re-weights the goal list that drives selection.
3. **PER-ADVERSARY BOSS STRATS, OBTAINED WITH PRACTICE:** dangerous
   adversary classes ARE our bosses (soldier-ant packs, chickatrice,
   floating eye, shopkeepers; deeper: mind flayers, soldiers). Bosses have
   learnable patterns. For each high-death-mass adversary: dedicated
   PRACTICE REPS in the E20 lab (same boss, varied conditions) until a
   SPECIFIC counter is pinned — "vs soldier-ant pack: corridor choke +
   throw-first + never open-room" — speedrunner boss-drilling, except our
   muscle memory is a rule card + playbook entry. The BOSS-STRAT LIBRARY
   (adversary → practiced counter, evidence, reps-to-pin) is a first-class
   artifact; **coverage of the top-10 death-mass adversaries is a Phase-L
   exit-relevant metric.** GIF banner: "BOSS STRAT: soldier ants →
   choke+throw [pinned in 14 reps]".

## STRATEGY RESOLUTION ORDER (operator directive 2026-07-07)

Case-based dispatch with honest confidence — most-specific-wins, gated by
evidence:
1. **LOOKUP CHAIN:** (a) adversary+context ("soldier-ant pack in corridor")
   → (b) adversary ("soldier ants, any terrain") → (c) situation-class
   ("melee pack") → (d) activity playbook (BOSS-FIGHT generic) → (e)
   generic principles (throw-first, choke, EV). First PINNED entry wins.
2. **EVIDENCE GATE:** specific-but-hypothesized LOSES to
   generic-but-proven — and gets flagged as a practice-priority signal.
3. **EVERY FALLBACK GROWS THE LIBRARY:** generic resolution for a
   meaningful-death-mass adversary AUTO-ENQUEUES it for E20 practice reps.
   The library fills itself where the dungeon shows gaps.
4. **LOG the resolution path per engagement**; resolution-depth
   distribution over time = maturity metric (early: mostly generic; late:
   mostly specific). GIF banner shows it.

## THE STANDARD DECISION PATTERN (operator directive 2026-07-07; strategy AND action level)

1. **SUGGEST, DON'T DICTATE:** procedures produce a SUGGESTED action/
   strategy (resolution chain + option menus) — overridable by the
   intuition layer (Arm B) or by playout evidence (both arms).
   Bidirectional authority: intuition proposes objectives downward,
   procedures propose actions upward; either overrides with logged
   reasons.
2. **PLAY IT OUT FIRST** (planning in imagination — world-model playouts,
   zero env access, legitimate at test time): before committing to
   strategy X in a recognized scenario, roll K sampled futures (~20–50
   steps) through the symbolic+exchange model; summarize the POSSIBILITY-
   SPACE REGION per goal dimension: P(death), HP distribution,
   depth/loot/xp, time. Operator's question verbatim: "Do I like where we
   could be in possibility space if I try strategy X?" — per menu option.
   (Implementation shares E-NH4b's determinized K-future sampling
   machinery.)
3. **EVALUATE + CHOOSE:** Arm A = goal-weighted scoring over playout
   summaries; Arm B = intuition READS the playout summaries and
   picks/overrides ("sprint: 85% cross safely, worst case 40% HP — I like
   that region better than fight's bimodal outcome").
4. **THEN TRY IT** — per-step replanning + abort conditions; playouts
   inform, reality governs.
5. **CALIBRATION:** playout-predicted distribution vs realized outcome
   logged per decision — playout calibration at strategy scale = a
   world-model quality metric (extends the verification stack upward);
   poorly-calibrated playout classes = model gaps = curiosity targets.
Render: playout preview panel ("SIMULATED: fight → P(death) .18, sprint →
.05") before the chosen action — the agent visibly thinking ahead.

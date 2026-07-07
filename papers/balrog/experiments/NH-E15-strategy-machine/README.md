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

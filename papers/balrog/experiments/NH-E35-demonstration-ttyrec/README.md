# NH-E35 — Learning from Demonstration (ttyrecs)

MODEL: claude-opus-4-8[1m] (max thinking), Phase L session 5. Operator
directive via coordinator, 2026-07-07. DESIGN-STAGE (registration + pre-
registered predictions; execution sequenced AFTER the floor-role uplift
workstream; flag the coordinator before any heavy corpus download).

## The key insight (why this is near-term for NetHack)

**NetHack ttyrecs are demonstrations IN OUR EXACT OBSERVATION SPACE.** Public
servers (alt.org/nethack, hardfought.org) store millions of recorded games —
including thousands of **ascensions** — as `ttyrec` (timestamped terminal
recordings). A ttyrec replays into the SAME `tty_chars` representation our
agent already consumes. So "watching expert gameplay" needs **no
video→world-space mapping** for NetHack: the demonstrations are already text
in our format. (The general pixel-video→world mapping — for games with no
ttyrec equivalent — is the harder cousin, registered as a future-work note
under the perception/benchmark-scout track T390.)

## Architecture: one parser, three consumers

```
ttyrec files ──▶ parser ──▶ (obs, action, next_obs) stream ──┬─▶ 35a WORLD-MODEL check
  (public,                  (tty_chars + inferred keypress)   ├─▶ 35b STRATEGY validation
   offline)                  per-role sliced                  └─▶ 35c STRATEGY discovery
```

provenance:**demonstration** (distinct tag from wiki/forum). CLEAN-PROTOCOL:
public human data used OFFLINE to build priors/knowledge (like reading source
or the wiki — a disclosed offline artifact); scored runs stay pure-code /
clean-protocol; disclosed prominently. Per-role slicing throughout (expert
Tourist games feed the floor-role uplift directly — finally SEE how a Tourist
is won). Respect server data policies; public ttyrecs only; offline.

## Sub-experiments (sequence: 35a first — cheapest + highest value)

### NH-E35a — WORLD-MODEL VALIDATION (do first)
Replay expert ttyrecs through our symbolic model and run the possibility-set
violation checker (c2_violations.py: V_TIME/V_MOVE/V_NONMOVE_POS/V_DEPTH/
V_HP_BOUND/V_XP_MONO) against REAL human-game transitions. Why huge: ascension
games contain DEEP-GAME transitions, rare monsters, and item interactions our
own shallow play (max Dlvl 21) NEVER reaches — a massive INDEPENDENT
validation set covering exactly the edge cases we cannot self-generate.
- **P1:** low violation rate on expert deep-game data → strong model-quality
  evidence, extending "0 violations / 233k predictions" to millions of
  transitions across the FULL game (not just our shallow slice).
- **P2:** each violation = a model gap we would never find ourselves → a fix
  + a new snapshot fixture (the criterion-iv corpus grows from ground truth).

### NH-E35b — STRATEGY VALIDATION (audit our doctrine vs winners)
Test our derived rule cards / principles against what WINNERS actually do.
Each principle gets a corpus-confirmation rate.
- e.g. "Tourists avoid early combat" → measure expert Tourist ascensions'
  early combat rate. "Descend hungry only if food likelier below" → do experts?
- **P3:** principles experts FOLLOW get empirical backing; principles experts
  VIOLATE are a red flag (our doctrine may be wrong-for-winning). Honest audit
  of our strategy layer against ground-truth success. Directly checks the s5
  floor-role wiki cards (does the wiki doctrine match what winners do?).

### NH-E35c — STRATEGY DISCOVERY (imitation-INFORMED, not blind cloning)
Mine expert play for strategies we DON'T have — especially the behavioral gap
**where WE DIE but experts SURVIVE**. Cluster expert action-patterns at our
death-class decision points (same-speed-adjacent trash, low-HP crises, the
D5-6 kill zone from the KPI tree) → what do winners do there that our policy
doesn't?
- **P4:** surfaces whole strategy classes (prayer timing, altar/BUC use,
  escape techniques, item combos) as candidate rule cards.
- **discipline:** EXTRACT the mechanism experts use, then run it through
  PROPOSE→COMPILE→BACKTEST→DEPLOY in our loop — don't clone blindly. The
  e6_solve gym battery is the natural backtest channel (does the mined rule
  win the death-class scenarios?).

## Connection to the current program
- 35a extends criterion (v) validation to ground-truth deep-game data.
- 35b audits the s5 floor-role wiki cards + all principle cards against winners.
- 35c is a candidate-rule FACTORY feeding the same solve-loop pipeline that
  graduated THROW_DISENGAGE (s5) — the death-class gap is the target.
- The general video→world mapping for pixel games = T390 future-work note.

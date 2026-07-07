# NH-E18 — Connecting-dots memory (REGISTERED, Phase L; operator directive 2026-07-07 — LEADS the Phase-L priority order together with the perceptor backlog)

MODEL: Fable 5 (max reasoning) — design + registration. (Handoffs logged here if a successor model continues this experiment.)

**Core insight (operator):** memory serves TWO functions. (1) Avoiding death —
hazard ledgers, dossiers: we have this, it is code-shaped. (2) CONNECTING DOTS —
relational inference over remembered observations, where facts jointly imply
something neither implies alone: we DON'T have this, and it requires the LLM.

## 1. Memory substrate (code; ships into both arms)

Unify the episode's observations into ONE queryable store: level dossier +
item sightings WITH unidentified appearances + prices seen (shop offer/asking
events) + monster encounters with outcomes + events timeline. Code records
everything; the structure is designed for retrieval (by item appearance, by
species, by level, by event type). Within-episode only (BALROG protocol:
nothing persists into a scored episode from outside it); serialized into
trajectories for offline analysis and between-episode reflection.

## 2. LLM dot-connector (dev/gym + Arm B consultation points + between-episode reflection)

The LLM reads the memory store and proposes RELATIONAL HYPOTHESES. Canonical
NetHack targets:
- **PRICE-ID:** offered/asking price + item class → probable identity set
  (wiki documents the price tables — NH-E13 KB cross-reference makes each
  inference concrete and checkable).
- **Altar drop → BUC identification** (message grammar on drop).
- **"Monster X didn't attack while adjacent → peaceful/passive class"**.
- **Level features → branch recognition** (Mines/Sokoban signatures).
- **Key/lock-class bindings** where they exist.

Each proposed relation = a rule card (provenance: **inferred**) validated via
gym/branch-probe (NH-E16 component 2) before ANY policy trust. Validated
relations compile to code for Arm A; Arm B may also run them live.

## 3. The two-loop demonstration (write-up angle, operator's)

Code CANNOT do step 2 — pattern-matching across heterogeneous remembered facts
is the LLM's comparative advantage; executing a validated relation cheaply and
reliably every step is code's. NH-E18 is the cleanest demonstration in the
program that BOTH loops are necessary. The writeup treats this as its thesis.

## 4. Metrics

- relations proposed / validated / refuted per episode (and per reflection pass)
- score + survival impact of validated relations (price-ID alone should
  measurably improve item decisions — paired dev validation like any lever)
- dots-connected count surfaced in GIF banners
  (e.g. `INFERRED: 60gp potion ≈ healing [price-ID]`)

## 5. Hypothesis-driven exploration objectives (operator refinement, closes the E18↔E11 loop)

> **"The LLM decides WHERE to go; the procedures decide HOW to get there.
> Strategist chooses destinations, navigator drives."** — operator, 2026-07-07

- **REVALUATION TRIGGER:** whenever new capability or knowledge lands (item
  acquired: key/pick-axe/wand identified; relation validated; skill unlocked),
  the dot-connector RE-SCANS the level dossiers for revalued opportunities:
  "locked door on D1 + key now held → that room is reachable", "unreachable
  vault + pick-axe → diggable", "unidentified wand + now-known zap semantics →
  test target".
- **CURIOSITY OBJECTIVE contract:** {hypothesis ("I wonder if..."), target
  location, expected value (what might be there × prior), cost (risk-costed
  travel per the NH-E11 navigator), abort conditions} — priced in the goal
  market against descent value (the explore/exploit call is the LLM's;
  execution and per-step replanning over dossier hazards is the navigator's
  risk-costed A*).
- **LOGGING:** hypothesis→journey→outcome triples. Metric: **curiosity hit
  rate** (journey found something valuable vs wasted trip + its cost) — the
  empirical explore/exploit curve for backtracking; feeds the goal market's
  future pricing of curiosity.
- **RENDER:** curiosity journeys get their own GIF banner, e.g.
  `CURIOSITY: returning to D1 locked room [key acquired]`.

## Dependencies / siblings

Perceptor backlog feeds the substrate (operator reweight, same directive):
shop/altar/fountain/special-room detectors, monster-state perceptor
(peaceful/hostile/fleeing/asleep), item-appearance tracker (unidentified
appearance + observed prices + contexts), branch/level-feature recognition.
NH-E13 KB supplies the reference tables; NH-E16 supplies the validation
instrument; NH-E11 dossier is the substrate's spatial spine.

## Status log
- 2026-07-07: registered (operator directive), folder created.

## 6. Question-driven retrieval (operator addition, shared with NH-E21)

Goal-directed mode alongside passive dot-connecting: planning hits a
constraint → the intuition layer formulates an explicit QUESTION ("How can I
get below 20 health?") → runs it as a retrieval query against the memory
store (FTS5 over observations + dossiers + relations) → retrieved memory
answers the question → plan completes. Full chain logged (constraint →
question → hits → answer → plan) + rendered in GIF banners. Both modes
measured; chain rate is a core NH-E21 metric.

## 7. CURIOSITY REWARD, operationalized (operator spec 2026-07-07)

`curiosity_value(target) = α·NOVELTY + β·DOT_COMPLETION`, both from
existing ledgers:

- **NOVELTY** (what the model doesn't know): unpinned mechanics nearby,
  unseen entity/tile/verb-context classes, reachable coverage-matrix
  untested cells, high possibility-set-entropy regions (widest predictions
  = most to learn). Queryable from rule cards + matrix + the model itself.
- **DOT-COMPLETION** (connecting new dots): the memory store's OPEN
  SOCKETS — unanswered questions, half-completed relations (door-condition
  known but no matching capability; item seen but unpriced; monster
  encountered but untyped). Each open socket projects a VALUE FIELD over
  the world: any target that might complete it scores. Open questions
  literally price exploration targets — question-driven retrieval,
  inverted.
- **CALIBRATION LOOP:** after each curiosity journey, log REALIZED info
  gain (mechanics pinned, relations completed, sharpness delta, questions
  answered) vs predicted curiosity value; the predicted-vs-realized curve
  calibrates α/β over time, and NH-E23 bandits allocate among curiosity
  targets using these as rewards. A curiosity estimator that stays
  calibrated is the answer to "explore rewards are hard to model": model
  them, then check the model.
- **Report artifact:** curiosity calibration curve + top realized-gain
  journeys ("CURIOSITY: unexplored NE room [2 open sockets] → FOUND: wand
  → SOCKET CLOSED: ranged option acquired").

**AMENDMENT (operator, same day): §7's formula is DEMOTED to a baseline +
explanation/logging layer. FELT-SENSE (intuition picks over the full context
package, one-line why, choice logged) is the DEFAULT curiosity engine.
See NH-E24 (curiosity framings compared) — the formula must earn its way in.**

## 8. REMINDER/RECALL LOOPS — the push mode (operator directive 2026-07-07; completes the retrieval triad: PUSH reminders / PULL questions / OFFLINE dot-connecting)

1. **SCENARIO→REMINDER:** perceptual cues fire associative recall without
   being asked — adversary sighted → boss strat + lessons + exchange stats
   pushed; level type → branch dossier notes; item class → price table +
   past outcomes; state pattern (low HP + pack) → applicable death lessons.
   Implementation: cue→memory index (entity/situation/state-pattern tags on
   every memory artifact; FTS5 on cue fire), top-k surfaced.
2. **TWO CONSUMERS:** (a) procedures — implicit recall via rule matching,
   made explicit + logged; (b) INTUITION — pushed REMINDERS section in the
   context package (push finds what pull misses: you can't query for a
   lesson you forgot you learned). CONTEXT_SPEC bumps to v0.2 with the
   REMINDERS section.
3. **LOG every reminder fire + whether it changed a decision**; reminder
   hit-rate (fired→influenced) tunes the index; never-influencing reminders
   get demoted (relevance learning).
4. Banner: "REMEMBERED: last bat standoff wasted 400 turns [lesson #12] →
   forcing transition".

## 9. RECOGNITION AS A DECISION TRIGGER (operator sharpening — recognition-primed decision, not passive recall)

1. **SCENARIO FINGERPRINTS:** every gym/lab scenario, death retro, notable
   situation gets a situation signature (adversary set + terrain class +
   HP band + xp band + resources); a RECOGNIZER matches the current
   situation continuously (cheap feature match).
2. **"I'VE SEEN THIS BEFORE" is a first-class event** that PROMPTS an
   immediate strategy decision (state-machine interrupt + consultation
   trigger where warranted): surface the scenario's OUTCOME HISTORY
   ("seen 7×: choke+throw won 6, open-melee died 3") and force explicit
   (re)selection through the resolution chain — recognized+pinned → apply
   the practiced strat NOW; recognized+bad-history+no-answer → caution
   posture + intuition consult ("we've died here twice — what's
   different?"); recognized-mid-strategy → re-evaluate, don't just
   continue.
3. **The gym library doubles as the RECOGNITION CORPUS** — every practiced
   scenario is a tripwire in live play; practice without recognition is
   wasted. Metric: recognition→correct-strat application rate (the
   PRACTICE-TRANSFER number — arguably the single most important metric of
   the whole learning system).
4. Banner: "RECOGNIZED: ant-pack corridor [seen 7×, strat pinned] →
   engaging choke+throw".

## 9b. RECOGNITION YIELDS AN OPTION MENU (operator refinement)

A recognized scenario has MULTIPLE good options — FIGHT (practiced strat,
+xp +loot, risk), RUN (safe, forfeits), SPRINT-THROUGH ("book it": cross
without engaging — movement-through-danger as a first-class practiced
skill: door-to-door pathing, don't stop, eat the opportunity attacks),
FIGHT-AND-LOOT, SNEAK/WAIT.
1. Each fingerprint stores an OPTION SET with outcome history per GOAL
   DIMENSION (survival% / loot / xp / time / HP cost) from gym reps + wild
   outcomes.
2. Selection = goal-list weights × option outcome vectors; felt-sense
   breaks ties or overrides with a why ("weights say fight, but we're one
   hit from veto range — booking it").
3. SPRINT-THROUGH gets its own lab reps — probably the most under-used
   option in our history (we fight or flee; we never just run past).
4. Log menu + choice + outcome per recognition event; each scenario's menu
   ranks itself per goal profile over time.
Banner: "RECOGNIZED: ant pack [menu: fight .72 / sprint .85 / retreat .95]
→ goal weights favor sprint → booking it".

## 10. FIRSTS LEDGER / NOVELTY AWARDS (operator directive 2026-07-07)

First-time achievements (first kill per species, first verb use, first
depth, first scenario-class solve, first relation type) = NOVELTY AWARD
events: logged (store.first — SHIPPED: kill/verb/depth kinds live,
serialized as store["firsts"]), GIF-celebrated, counted. Goal-pursuit
wiring (registered): standing goal "BEAT NEW THINGS" — option-menu bonus
for engagements scoring a first, as a BOUNDED premium inside the ε-ruin
constraint + caution defaults (the award tempts, the veto governs).
Not-just-fun: each first = evidence begun + coverage cell + boss-strat
seed + sharpness gain — the coverage matrix gamified. Firsts-per-episode
rate = exploration-health metric (declining firsts ⇒ world seen ⇒
descend). Cumulative-firsts HUD + "new bosses beaten" milestone-email
list = trophy case.

## 11. SELF-SET GOLD STARS (operator directive 2026-07-07; exploratory — implement light, measure, keep what pays)

At play-period start (reflection pass) the intuition layer DECLARES its
own session goals — self-chosen, ability-calibrated ("pin the wolf strat",
"D8 with a fragile role", "close 3 price-ID sockets", "first
sprint-through"). Logged BEFORE play; pursued via the goal list;
celebrated on earn (HUD + reel); period-end review (earned / missed /
abandoned + why). MEASUREMENT: does self-set goal pursuit change learning
rate vs fixed goals (zone-of-proximal-development hypothesis)?
Self-calibration check: earned-rate should sit ~60–80% — persistently
higher = sandbagging, lower = frustration loop; the earned-rate curve is
itself the calibration read on the intuition layer's self-model.

## 12. GIVE UP — TOO HARD, as a first-class move (same directive)

Attempts beyond current capability end in a clean SHELVE, not a death
spiral: disengage → dossier note "too hard now — return when [condition:
xp≥X / ranged option / heal potions≥2]" → becomes a DEFERRED CURIOSITY
OBJECTIVE that re-fires on the existing revaluation trigger (§5).
ANTI-STUBBORNNESS GUARD: N failed attempts on the same target within a
period → mandatory shelve (the inverse of the stall watchdog — don't
grind what's beating you). Live-play twin of the gym's UNWINNABLE
verdict. Give-ups logged WITH PRIDE: "SHELVED: soldier pack at xp2 —
returning at xp5" is a smart agent talking. Metrics: shelve→return→win
conversion rate (the whole point), death-rate on shelved-class targets
before vs after.

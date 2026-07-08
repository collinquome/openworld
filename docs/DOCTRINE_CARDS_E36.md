# Doctrine Cards — NH-E36 SCENARIO STRATEGY SYNTHESIS
MODEL: claude-opus-4-8 (max thinking). Runtime identity VERIFIED at open
(system-prompt id = claude-opus-4-8; Fable at usage cap). All E36 artifacts
stamped claude-opus-4-8[max]. Fork aleph/fable-nethack.
insight-origin: OP (operator directive — scenario-strategy synthesis, the
systematic large-search version of the 13 hand-designed single levers).

Frame: 13 hand-designed single levers all nulled the mean (PROGRAM_FINDINGS:
capability-/acquisition-bound). E36 attacks the bootstrapping wall with a NEW
MECHANISM: for each recurring HARD SCENARIO, GENERATE MANY diverse candidate
strategies (LLM), SIMULATE/RANK them across many sampled instances, COMPILE the
winner to a fast rule card, DEPLOY behind a flag. = search-as-teacher (NH-E16)
+ best-of-N (SAMPLE10) + expert-seeding (the hand-designed levers are seeded
into the pool as incumbents to beat). This session = design + infrastructure +
a FIRST end-to-end proof on ONE scenario (TRASH, the #1-frequency hard class).

## CARD E36-1 — the pipeline (mine -> generate-20 -> simulate/rank -> compile)
BUILD (NEW files, no collision with the parallel stacked-arm block):
- `e36_candidates.py` — the CANDIDATE POOL: 20 diverse strategies as concrete
  action-policies over served obs (signature pol(A,obs,ps)). 12 SYNTHESIS +
  8 DEMONSTRATION (the hand-designed KITE/THROW/STAIRS/DOOR_KITE/RETREAT/REST
  incumbents seeded in). Tagged {priority (LLM pre-sim promise rank), tag,
  provenance}. Fable-ready: flat REGISTRY a stronger diverse-generation model
  regenerates without touching the harness (this pool authored by opus now).
  Strategy classes: COMPOSITE (HYBRID_BEST), ATTACKER-MGMT (CORRIDOR/CORNER —
  reduce simultaneous attackers, NEVER simulated as a ranked candidate before),
  ESCAPE-LEVEL (STAIRS/STAIRS_OR_KITE/AGGRO_DESCENT), DISENGAGE (KITE/DOOR_KITE/
  FAR_FLEE/RETREAT), RANGED (THROW/THROW_THEN_FIGHT/ZAP_WAND), RESOURCE-GAMBLE
  (PRAY/QUAFF_UNKNOWN), ATTRITION (FIGHT_WEAKEST), ALLY (WAIT_PET), WARD
  (ELBERETH), NULL-CONTROL (FIGHT_NEAREST/REST).
- `e36_simulate.py` — simulate+rank via deterministic branch replay (nh_branch,
  served obs only, dev seeds only, FRESH env/candidate — NLE can't be reused
  across a terminal death). Branch each death scenario at backoff=40 (crisis-
  proximal = the actual trash-melee-at-low-HP state), hand each candidate the
  agent's own information state, score SURVIVAL (alive at death_t+window OR
  level-escape) + depth-gain across MANY distinct seeds. Class-solve gate: same
  line survives >=3 instances on >=3 distinct seeds (the loot-lever 2-seed
  mirage is the cautionary tale). Head-to-head vs KITE (shipped hand lever).

## CARD E36-2 — TRASH strategy×scenario matrix (N=18 adjudicated seeds)
METHOD: 18 distinct dev-seed trash-melee death scenarios (roles Priest/Healer/
Samurai/Knight/Barbarian/Valkyrie/Ranger/Rogue/Archeologist/Caveman/Tourist),
branch at backoff 40 (crisis-proximal), each of 20 strategies runs from the
agent's own info-state, survival = alive at death_t+400 OR level-escape. The
matrix cell = strategy survival across the 18 sampled instances (robust; the
loot-lever 2-seed mirage is the cautionary tale).

RANKING (survival_rate, seeds_won/18):
  1  CORRIDOR        SYNTHESIS      0.50  (9)   <- WINNER (attacker-count mgmt)
  2  FIGHT_NEAREST   SYNTHESIS      0.50  (9)   <- null control TIES the winner
  3  CORNER          SYNTHESIS      0.44  (8)
  4  THROW           DEMONSTRATION  0.44  (8)
  5  THROW_THEN_FIGHT SYNTHESIS     0.44  (8)
  6  ZAP_WAND        SYNTHESIS      0.44  (8)
  7  HYBRID_BEST     SYNTHESIS      0.33  (6)   <- composite UNDERperforms
  ...
 13  KITE            DEMONSTRATION  0.28  (5)   <- shipped hand-designed lever
 14  DOOR_KITE       DEMONSTRATION  0.28  (5)
 20  STAIRS          DEMONSTRATION  0.11  (2)   <- but escape_rate 0.61

KEY READS:
- The WINNER is a SYNTHESIS strategy (CORRIDOR = funnel to a 1-wide corridor so
  <=1-2 trash attack at once, then fight the weakest) that BEATS the shipped
  hand-designed KITE lever 0.50 vs 0.28 = **Δ+0.22 survival**. Attacker-count
  management (CORRIDOR/CORNER) and standing to FIGHT beat KITE/DOOR_KITE/RETREAT
  fleeing — fleeing a SAME-SPEED pursuer donates turns (the s6 THROW lesson,
  re-found structurally). So in robust replay a synthesized strategy DOES beat
  hand-design → the mechanism discriminates and finds a NEW direction.
- CAVEAT 1 (dampens the win): FIGHT_NEAREST (the "just attack" null control)
  TIES CORRIDOR at 0.50. Much of the survival differential vs KITE is that
  FLEEING is actively bad here, not that CORRIDOR is uniquely clever. Honest:
  the finding is "stand-and-fight/funnel > flee in trash-melee", winner not
  uniquely CORRIDOR.
- CAVEAT 2: 3/18 seeds (712, 723, 732) = 0 survivors across ALL 20 strategies →
  those specific instances are BOOTSTRAPPING-UNWINNABLE (no strategy in a 20-
  wide seeded search survives an under-geared trash fight). The wall is real for
  the hardest instances; the win is on the winnable-but-misplayed remainder.
- HYBRID_BEST (the hand-composed "smart" policy) ranks 7th (0.33) — composing
  sub-strategies UNDERperforms the single best; the composite over-descends/over-
  prays into death. Best-of-N > hand-composition, as the mechanism predicts.
- ELBERETH ranked 19th (0.17): dust-engrave is interface-limited (no getlin
  commit token) exactly as the program logged — the pipeline REDISCOVERED this
  honestly rather than crediting a phantom ward.

## CARD E36-3 — compiled selector + deploy (paired-validate on the MEAN)
COMPILE (e36_compile.py): winner CORRIDOR -> rule card E36-TRASH-1 =
{signature: crisis_predicate (mobile hostile adjacent, hp_frac<=0.55, D2-7),
strategy: pol_corridor}, flag NH_E36, default-OFF. Decoupled architecture
(coordinator directive): STRATEGY (pol_*, no baked qualifier) / SIGNATURE
(crisis_predicate) / SELECTOR (the survival matrix -> top strategy). The
qualifier is LEARNED (matrix), not hand-coded.
DEPLOY (e36_paired.py): E36Agent subclass injected via monkeypatch — ZERO edits
to shared/parallel-owned nh_agent.py / nh_runner.py. Flag-OFF BIT-IDENTICAL
VERIFIED (base DiveAgent REF prog 0.021221378364235505 == subclass REF, exact,
seed 712). Paired block REF vs REF+NH_E36, one-seed-per-process, cap 1500.
RESULT: [FILLED AFTER BLOCK — prog mean Δ + 95% CI + fire counts]

## HONEST READ
[FILLED after block. Provisional from the replay matrix: the synthesis MECHANISM
works as a discriminator (found a NEW +0.22-survival direction hand-design
missed) BUT (a) a null control ties the winner and (b) the hardest instances are
strategy-invariantly unwinnable — the live-mean result decides whether the
replay edge survives the model-fidelity gap (the s6 THROW over-credit precedent).]

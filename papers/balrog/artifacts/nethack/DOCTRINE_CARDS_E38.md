# DOCTRINE CARDS — NH-E38 CONSUMABLE ECONOMY + ITEM IDENTIFICATION

MODEL: claude-opus-4-8 (max thinking). Runtime identity VERIFIED at open
(system-prompt id = claude-opus-4-8, CLAUDE_EFFORT=high; Fable = in-loop
synthesis model, at usage cap, N/A for this build — the DiveAgent is a symbolic
code policy, no per-step LLM). All E38 artifacts stamped claude-opus-4-8[max].

Provenance: knowledge=WIKI + NetHack 3.6.7 `src/engrave.c` WAND_CLASS switch
(engrave-test ID table), OFFLINE + disclosed, cross-checked vs local
`wiki_kb.sqlite`. insight-origin=OPERATOR (consumable-economy swing) +
coordinator steer (offensive-wand branch = spike-death counter; XP-throughput
target). Recipe = `run_consume_block.sh` (paired, one-seed/arm-per-process,
resumable) + `analyze_consume.py` (paired-bootstrap CI + fired-split +
leave-one-out + death-class regression + leveling-wall table).

## THE LEVER (flag NH_CONSUME, alias NH_IDGAME; default OFF => bit-identical)
Staged low-risk-first, all gated, all behind the flag:
1. ENGRAVE-ID (deterministic, zap-risk-free): engrave-test an unidentified wand
   (write in dust with the wand as tool -> the discharge message reveals the
   class). Message table verbatim from src/engrave.c. Digging/teleport are SAFE
   to engrave-test (they do NOT dig/teleport-you; only lightning self-blinds,
   fire burns floor-items). One test per wand.
2. OFFENSIVE/CONTROL-WAND ZAP (the spike-death counter, coordinator #1): zap a
   KNOWN striking/sleep/death/cold/fire/lightning/magic-missile/slow wand at a
   fast/same-speed/tough/adjacent hostile in a clear line. A sleep/striking/death
   wand ENDS the unfleeable one-exchange fight AND is a zero-exchange (safe) kill
   = free XP. Fires in P3 (crisis) and P4.85 (proactive at spike-threats).
3. KNOWN-CONSUMABLE USE: quaff KNOWN heal potion at HP<40% (secondary — can't
   outrun a spike); quaff/read KNOWN gain-level (direct safe XP, supply-limited);
   read KNOWN enchant-armor/weapon when safe.
4. ACQUISITION: underfoot pickup + bounded-detour (radius 10, 25-step/level
   budget — the FOODACQ/s13 no-stall discipline) to floor wands>scrolls>potions,
   so the offensive wand that ends the fight (which is on the FLOOR, not the
   starting kit for most roles) actually reaches the agent's hand.

Instrumentation (bit-identical, logging only; answers "are we leveling-walled?"):
per-episode xp/hp_max/ac/str AT DEATH + depth-conditioned XP (xp at each depth)
+ arrival-XP@D5. Added to nh_runner traj (ac/str) + e35_antifaint_smoke rows.

## LEVELING-WALL, QUANTIFIED (mined from 1183 existing trajectories, no new compute)
- depth_max at death: median 5, mean 5.19, p90 10 (death peaks SHALLOW).
- hpmax at end: median 22 (tiny HP pool).
- XP at end: median 2 (n=60 with xp logged) — DESCEND ~unleveled (seed 101
  Priest reached D9 at XP 2; Wizard 839 died D5 at XP 1, xp_by_depth all 1s).
- 45% of episodes end with >30% HP in the last logged frame -> SPIKE deaths
  (one big exchange), NOT attrition to zero. The only counter to an unfleeable
  spike is ENDING THE FIGHT IN ONE ACTION -> the offensive-wand branch.

## RESULT — NULL on the mean; the FIRED-SPLIT confirms the EXECUTION WALL (13th angle)
Pilot: n=8 paired dev seeds (4,16,21,37,104,111,115,700), cap 3000, TEST-only
(NH_CONSUME) vs the reused deterministic standing-config REF baseline
(e38_ref_baseline.jsonl); TEST timeout 720 so survivors complete (no survival-win
exclusion bias). + 3 fresh full-instrumentation Wizard pairs (consume_block2).

- **PRIMARY progression: REF 0.0365 -> TEST 0.0403, Δ +0.0038, 95% paired-
  bootstrap CI [-0.0149, +0.0209] — INCLUDES 0. NULL.** (The interim n=7 read
  a positive CI-excludes-0; adding one seed collapsed it to include 0 -> the
  drop-rule caught small-sample noise, as designed.) depth_max Δ +0.875 CI
  [-0.50, +2.375], includes 0.
- **FIRED-SPLIT (the finding):** on the 4 seeds where the ID/use machinery FIRED
  (4,37,104,700): progression **Δ -0.0123, CI [-0.0369, +0.000]** — null-to-
  NEGATIVE. The apparent positive aggregate comes ENTIRELY from NON-fired seeds
  (16,21,111) where only the acquisition DETOUR perturbed the exploration route
  -> deeper by luck (the s13 LOOT CONFOUND — the brief's "+0.72 one-seed noise"
  warning; leave-one-out: drop16 -> -0.0030, drop700 -> +0.0114 — a tug-of-war
  between detour-noise-positive and use-cost-negative netting to ~0).
- **THE MONEY DATUM (seed 4):** engrave-ID SOLVED a wand (sol=1), ZAPPED it 3x
  and KILLED 2 monsters — the win-item was acquired, identified, and used
  EFFECTIVELY in combat — yet the agent reached the SAME max depth (D8) as REF
  and died anyway. Progression Δ = 0. The capability was reachable and used; it
  still did not convert to the OUTCOME. Cleanest possible evidence that the wall
  is EXECUTION, not bootstrapping/acquisition.
- **REGRESSION (introduced death class):** seed 4 died "Killed by a bolt of
  lightning" — absent from REF, consistent with a SELF-INFLICTED reflected zap
  (wand of lightning ray bouncing off a corridor wall). Offensive-wand zap in
  enclosed early-dungeon geometry is self-dangerous -> a reflection / clear-
  line-of-fire guard is REQUIRED before any use-deployment.
- **QUAFF-HEAL inert (seed 104):** quaffed healing 3x, still died to a wererat
  at D4, Δ=0 — confirms "a heal can't outrun a spike."
- **Mechanism totals (n=8 TEST):** engrave-ID tests 5 (solved 1), zap 3 (kills
  2), quaff-heal 3, enchant 1, gain-level 0 (none found — supply-limited, as
  flagged), acquisitions ~2-4/episode via detour+autopickup. The USE layer
  UNDER-fires because acquired potions/scrolls stay UNIDENTIFIED (engrave-ID is
  WANDS-ONLY; read-identify/price-ID detected but not yet acted on) and offensive
  wands are floor-scarce.

**VERDICT:** the consumable economy does NOT move the mean. Where the use-layer
fires it is null-to-negative AND can self-harm (reflected zap); the only positive
signal is acquisition-DETOUR route-perturbation noise, not consumable capability.
Consumables were IN HAND early (acquired, some identified + used, some killed
monsters) and using them still didn't convert -> per the brief's discriminating
prediction, the strongest evidence yet for the EXECUTION WALL specifically. The
13th converging angle on capability/acquisition/EXECUTION-boundedness. Honest
caveat: pilot n=8 (4 fired, 1 real zap-seed); a fuller ID game (read-identify +
price-ID) would raise the fire rate — but seed 4 shows a fully-identified,
used, monster-killing offensive wand already fails to convert, so more fires
would deepen the execution-wall evidence, not overturn it.

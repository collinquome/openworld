# HANDOFF — NH-E38 CONSUMABLE ECONOMY + ITEM IDENTIFICATION

MODEL: claude-opus-4-8 (max thinking). Runtime identity VERIFIED at open
(system-prompt id=claude-opus-4-8, CLAUDE_EFFORT=high; Fable = in-loop synth
model at usage cap, N/A — DiveAgent is a symbolic code policy). All artifacts
stamped claude-opus-4-8[max]. Dev/gym seeds only; reserved exam seeds
(1000-1004/2000-2024/…/6000-6099/7000-7024) UNTOUCHED.

## WHAT SHIPPED (flag NH_CONSUME / NH_IDGAME, default OFF => bit-identical)
Verified bit-identical-OFF (seed 101 prog 0.09770935198701912 to 1e-12, twice)
and import-clean on/off. Files (flat dir work/fable_nethack; sync to worktree
papers/balrog/code/nethack via sync_to_worktree.sh, commit, push to FORK):
- **nh_agent.py**: C2_CONSUME flag + tables (ENGRAVE_ID_SIGS from NetHack 3.6.7
  src/engrave.c, OFFENSIVE_WANDS, HEAL/GAINLEVEL/ENCHANT name sets) + methods
  `_consume_inv` `_line_hostile` `_consume_zap` `_consume_heal` `_consume_safe`
  `_engrave_id` `_consume_acquire` + underfoot consumable pickup + P3-crisis /
  P4.85-proactive / P8.55-safe wiring + engrave-ID message capture in
  `_bookkeeping`.
- **nh_percept.py**: `consumable_targets` (floor wand/scroll/potion spotter by
  object class; separate from item_targets so no other lever changes).
- **nh_common.py / nh_runner.py**: STR + AC per-step logging (leveling-wall
  instrumentation, bit-identical).
- **e35_antifaint_smoke.py**: E38 result-row fields — xp/hp_max/ac/str AT DEATH,
  xp_by_depth, arrival_xp_d5, + mechanism counters (zap/engrave/gainlevel/heal/
  enchant/pickup/walk/acq/kill).
- **run_consume_block.sh** (fresh paired), **run_consume_testonly.sh** (TEST-only
  vs reused REF baseline), **analyze_consume.py** (paired-bootstrap CI +
  fired-split + leave-one-out + death-class regression + leveling-wall table).

## METHOD NOTES / GOTCHAS (carry forward)
- **VM ~3.65 steps/s**: a cap-3000 SURVIVOR ~= 820s. Run ONE arm per process.
  timeout 480 KILLS survivors (lost rows) and BIASES against a survival-improving
  lever (HANDOFF_14). Use timeout ~720 at cap 3000 so survivors complete, OR
  cap 1500/timeout 500 for fast clean pairs (early-game signal only).
- **OPS**: run blocking foreground (harness auto-backgrounds + tracks + notifies).
  A `nohup … &` detached launch DIED instantly / produced 0 rows — do NOT detach.
- **REF reuse**: REF is deterministic + E38 additions are bit-identical, so the
  cap-3000 standing-config REF rows from loot_block/pet_block (32 dev seeds) are
  reusable (results/e38_ref_baseline.jsonl, enriched with arrival_xp_d5 etc.
  recomputed from REF trajectories). Halves the run (TEST-only).
- Flags read at IMPORT: never edit nh_agent.py while a block is running (later
  episodes in the same chunk would pick up the edit -> mixed-code rows).

## EMERGING READ (to be confirmed at larger n — see RESULT below)
The mechanism FIRES as an acquisition DETOUR (`_consume_acquire` walks to a floor
consumable; autopickup grabs it — verified seed 860: "n - a black potion"). BUT
the USE-conversion (zap/quaff-heal/gainlevel) fired 0× on the first 3 Wizard
seeds because: (a) acquired POTIONS/SCROLLS stay UNIDENTIFIED — engrave-ID is
WANDS-ONLY; no price-ID (needs shop), no altar-BUC, and read-identify is detected
but NOT yet acted on; (b) offensive WANDS are scarce on shallow floors and
starting wands are utility/pre-ID'd (Wizard 839 = pre-ID digging). So the early
effect is route-PERTURBATION (860 D3->D6 by luck, the s13 loot confound), not
consumable USE -> shaping up as the acquisition/identification wall ONE LAYER
DEEPER. NEEDS the larger fired-split to confirm.

## NEXT (to make the offensive-wand hypothesis a FAIR test)
1. **Act on the KNOWN scroll of identify** (Wizards start with one) in
   `_consume_safe`: read-identify an acquired unknown potion/wand -> it becomes
   usable. Closes a real ID loop without engrave.
2. **Price-ID** (kb_prices.json is built) when a shop is on the level -> IDs
   potions/scrolls the engrave channel can't.
3. Scale the paired block to n>=20 at cap 3000 timeout 720 (TEST-only vs reused
   REF), fold fresh full-instrumentation pairs for arrival_xp@D5 / leveling Δ.
4. If still null: report which layer bit (never-acquired / acquired-but-unid /
   unid-but-unused / used-but-inert / new-deaths) — the diagnosis is the result.

## RESULT — NULL on the mean; fired-split = EXECUTION WALL (see DOCTRINE_CARDS_E38.md)
Pilot n=8 (cap 3000, TEST-only vs reused REF): progression Δ +0.0038, 95% CI
[-0.0149,+0.0209] (INCLUDES 0). Fired-pairs (4,37,104,700) Δ -0.0123 CI
[-0.0369,+0.000]; the positive aggregate is acquisition-DETOUR route-perturbation
on NON-fired seeds (16,21,111) — the s13 loot confound (LOO: drop16->-0.0030).
MONEY DATUM seed 4: engrave-ID solved a wand, zapped 3x, killed 2 monsters, SAME
D8 as REF, died anyway (Δ=0) to a self-reflected "bolt of lightning" (NEW death
class). Quaff-heal (seed 104, 3x) inert. gain-level never found (supply-limited).
Data: results/consume_testonly.jsonl + e38_ref_baseline.jsonl +
consume_block2.jsonl; recipe analyze_consume.py.

To SCALE/strengthen: (1) add read-identify + price-ID so the USE layer fires more
(currently under-fires: acquired potions/scrolls stay unidentified). (2) add a
zap reflection / clear-line-of-fire guard (seed-4 self-zap death). (3) n>=20 at
cap 3000 timeout 720. Prediction: more fires -> deeper execution-wall evidence,
not a mean-mover (seed 4 already shows used+identified+killing != converting).

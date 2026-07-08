# Doctrine Cards — Phase L session 14 (claude-opus-4-8[max])

## CARD S14-1 — Two perception bugs blocked the loot-then-wield pivot; both fixed
**Class:** load-bearing perception defect (same family as item-under-@,
corpse-on-victim-cell).
**Bug A [ITEM_ON_PERCEIVED_WALL]:** LevelMap.integrate()'s dark-adjacent
negative-inference guard marks unseen neighbours WALL; when a cell is later
revealed to hold a floor item, the object-glyph branch only corrected
UNKNOWN->FLOOR, so the stale WALL survived → passable() False → the item cell
was unwalkable-into. FIX: an object/boulder glyph proves passability → correct
WALL too (`terrain in (UNKNOWN, WALL)`).
**Bug B [ITEM_UNDER_@ / weapon]:** standing on the weapon hides its glyph under
@, so _best_floor_weapon goes blind and the cell==agent pickup branch can't
fire → oscillation (746: 11 walks, 0 pickups). FIX: complete pickup from the
"You see here <weapon>." message channel (`_weapon_upgrade_underfoot`).
**Evidence:** seed 746 now completes pickup(step176)+wield(step177, 1.15->2.59
dpt). Suite GREEN 21/21 (fixtures A8+A9). Default config bit-identical (733/772).
**Lesson:** "the loot policy paths toward the item" ≠ "pickup completes" — verify
END-TO-END, not just that the detour fires. Two independent perception layers
(terrain belief + glyph occlusion) each block on-cell acquisition.

## CARD S14-2 — FOODACQ anti-faint sub-win: EMERGING, not SOLID (n=28)
**Setup:** cd=8 food-acquisition paired block, hunger-prone seeds, KPI =
fainting-incidence (maxhunger>=4), paired bootstrap CI.
**Result:** n=28, REF 0.429 → TEST 0.214, **Δ−0.214, 95% CI [−0.429, +0.000]**
(touches 0). Hunger-death 0.179→0.071. Point estimate wandered −0.25→−0.167→
−0.214 as n grew 16→24→28 — never cleanly cleared 0.
**Verdict:** a real-direction, modest, marginally-non-significant fainting
reducer. Does NOT settle to SOLID. Honest label: EMERGING/suggestive.
**Lesson:** more n did not rescue a boundary result — a lever that halves an
event rate in-sample can still fail the 95% bar at n≈30 when base rates are ~0.4
and the pairing is noisy. Report the CI, don't over-claim the in-sample halving.
**Method gotcha:** the fainting KPI is NOT cap-insensitive (9/15 faints at
steps>1600) — cannot shorten the step cap to beat episode-timeouts. At the
current slow VM (~3.65 steps/s) slow survivors exceed any foreground-safe
timeout → some seeds are unavoidably excluded; document the exclusion direction.

## CARD S14-3 — Don't run a parallel heavy block someone else is already running
**Situation:** TASK 3 (NH_LOOT efficient-loot) was found already implemented AND
being executed by a concurrent agent (run_loot_block.sh, loot_block.jsonl live).
**Action:** did NOT launch a competing block; killed my own marginal contending
job to free the VM. SERIAL / no-parallel-sub-blocks is a throughput rule, not
just etiquette — two concurrent episode streams slow BOTH into timeouts.
**Lesson:** before running a heavy block, `ps`-check for an in-flight run and
inspect the target results file. The flat dev dir is SHARED and concurrently
edited — treat your in-context file view as potentially stale; re-Read before
editing, commit data-only to avoid capturing a neighbour's uncommitted code.

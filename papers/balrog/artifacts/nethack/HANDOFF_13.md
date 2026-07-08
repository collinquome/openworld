# HANDOFF_13 — Phase L session 13 -> session 14

MODEL: claude-opus-4-8 (max thinking) wrote this — session 13, the TENTH opus
session. Runtime identity VERIFIED at open (system-prompt id = claude-opus-4-8,
max thinking; Fable at usage cap). All s13 artifacts stamped claude-opus-4-8[max].
Fork aleph/fable-nethack.

## HEADLINE: WIELD UPGRADE (NH_WIELD) — the cleanest DIRECT combat-capability
## injection, zero wield actions ever — is a MECHANICAL NULL (progression Δ
## +0.0000, CI [0,0], 17/17 bit-identical, wield-fires=0). The counterfactual is
## PROVABLY EMPTY: 77/77 role-episodes across all 15 roles start weapon-optimal.
## The diagnosis resolves the whole resource-injection path into ONE meta-finding:
## the NetHack mean is ACQUISITION-BOUND — the agent has the mechanisms to USE
## capability (eat/wield/cast) but no behavior to ACQUIRE it (loot the floor).

## What this session settled
- **WIELD is the 11th converging angle on capability-boundedness**, and the FIRST
  that is mechanically (not just statistically) null: the lever CANNOT fire
  because roles start wielding their best in-inventory weapon. Refines the law:
  injection only injects capability that EXISTS and is UNUSED (the +2.41 Wizard-
  cast win had unused casting; wielding has none; gifting is contract-forbidden).
- **The zero-fire diagnosis -> ACQUISITION-BOUND meta-finding.** Read-only floor-
  weapon diag: (c) already-optimal/floor-junk 8/13; (a) acquisition-bound 3-5/13,
  DEMONSTRATED — 746 Healer walked past a mace (+1.44 dpt) 25 steps; 4054 Ranger
  past a flail 100 steps; 721 Knight past a two-handed sword. `item_targets` values
  only food/ammo/armor -> floor weapons are invisible to the loot policy. Same
  shape as the s10 anti-faint "empty larder" null: mechanism present, acquisition
  absent. Both #1-killer (hunger) and combat are gated by acquisition.
- **The pivot (NH_WIELDACQ) confirms it AND its cost.** Detour-to-weapon + pickup:
  the acquisition FIRES (11 walks toward the mace) but pickup never completes (the
  mace cell is marked a WALL in the terrain model -> unwalkable-into) AND the
  detour STALLS descent (DEATH@D5 -> TRUNCATED@2000, zero descent — the FOODACQ
  S11-2 trade-off recurs). Acquisition is not a free mean-mover.

## What was built (all stamped opus-4.8[max], flat work/fable_nethack)
- **nh_agent.py**: flags C2_WIELD=_flag("NH_WIELD") + C2_WIELDACQ=_flag("NH_WIELDACQ"),
  both added to C2_ANY. Consts WIELD_MARGIN(0.5), WIELDACQ_RADIUS(8),
  WIELD_DIAG(NH_WIELD_DIAG). Helpers `_wield_upgrade` (wield best carried melee
  weapon when +margin & safe; Monk/thrown excluded), `_wield_diag` (read-only
  floor-weapon pricer), `_best_floor_weapon`, `_weapon_acquire` (detour+pickup).
  Injections in `_decide` (after ANTIFAINT, before hunger crisis): diag, then
  WIELDACQ, then WIELD. Pickup menu handler extended with a "weapon" kind
  (targeted keyword). Flag-off bit-identical (C2_ANY False; block 17/17 identical).
- **e35_antifaint_smoke.py**: emits wield_fires, wieldacq_fires, wieldacq_walk,
  floor_wpn_dpt/name, floor_upgrade_steps (parsed from traj notes).
- **run_wield_block.sh (NEW)**: paired combat block, REF=FOODACQ+ANTIFAINT baseline
  vs TEST=+NH_WIELD+NH_WIELD_DIAG. Per-episode timeout 500s (s12 lesson), cap 2000,
  one-seed-per-process, SERIAL, resumable.
- **analyze_wield.py (NEW)**: paired-bootstrap progression-mean + CI + combat-death
  + wield-fires + bit-identical count + per-role.
- **run_foodacq_block.sh**: per-episode timeout parametrized (NH_EP_TIMEOUT, default
  500) — unblocks the CARD S12-2 n≈30 confirmatory.
- Data: results/wield_block.jsonl (n=17 paired). Docs: DOCTRINE_CARDS_s13.md
  (S13-1/2), PROGRAM_FINDINGS.md (11th angle + ACQUISITION-BOUND section), this
  handoff. Probes: scratchpad/probe_wield_broad.py (77-episode counterfactual),
  dbg746b.py (the perceived-wall pickup blocker).

## Standing config UNCHANGED — NH_WIELD + NH_WIELDACQ ship DEFAULT-OFF. No revert.
Bit-identical flag-off (C2_ANY False verified; block 17/17 identical). Snapshot
suite GREEN 19/19 with the new code (incl. wield_grammar fixture confirming the
wield letter-prompt). Defaults WIELD_MARGIN=0.5, WIELDACQ_RADIUS=8 baked in.

## Session-14 queue (value order)
1. **GENERAL ITEM-ACQUISITION policy** (the meta-finding's lever): teach the loot
   perceptor to see weapons (+keep armor/food); loot underfoot-FIRST (no detour,
   cd rate-limit, FOODACQ cd=8 model) so wield/wear/eat fire on acquisitions;
   REGRESSION-gate on descent depth (S11-2 confound). FIRST fix the item-on-
   perceived-wall pickup edge (terrain belief marks a real floor item as a wall).
2. **SAFE EARLY LEVELING** — XP/skill is the OTHER unused capability; arrive at the
   D5-6 kill-zone at xp>=5 (targeted safe kills, at range / with pet).
3. **FOODACQ n≈30 confirmatory** — CARD S12-2, now unblocked (timeout 500s). Fresh
   fainting seeds 715/716/717/722/726/728/731/733/734/745/752/772/774/778/825; fold
   with foodacq_cd8.jsonl; push fainting CI clear of 0 ([−0.533,0], p=0.22 at n=15).
4. If acquisition + safe-XP null -> DEMONSTRATION LEARNING (expert ttyrec capability
   injection) = the last qualitatively-different mean-lever.

## Gotchas (still bite — carried from s12, all held)
- OPS: run episodes as BLOCKING one-seed-per-process calls; per-episode timeout
  >=500s (the 280s cap SIGKILLed slow episodes). Foreground Bash caps ~10 min ->
  chunk seeds; the runner is RESUMABLE (skips done (arm,seed)). Do NOT start a
  detached waiter and yield the turn (dead pattern — the coordinator flagged it).
- NLE only via PYTHONPATH=pylib; NH_* knobs read at IMPORT time.
- ONE seed per process (s8 leakage); SERIAL only (VM contention -> wall-timeouts).
- Push to FORK; commit author "NetHack Phase-L s13 (claude-opus-4-8[max])
  <nethack@botxiv.org>". Edit flat work/fable_nethack, cp to worktree
  papers/balrog/{code,artifacts}/nethack/ via sync_to_worktree.sh.
- Findings canonical at researchy/docs/PROGRAM_FINDINGS.md + DEATH_TO_CAPABILITY.md
  (mirror in worktree). Doctrine cards + handoffs live in flat work/fable_nethack.

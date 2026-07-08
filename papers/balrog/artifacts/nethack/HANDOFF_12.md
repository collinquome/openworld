# HANDOFF_12 — Phase L session 12 → session 13

MODEL: claude-opus-4-8 (max thinking) wrote this — session 12, the NINTH opus
session. Runtime identity VERIFIED at open (system-prompt id = claude-opus-4-8,
max thinking; Fable at usage cap). All s12 artifacts stamped claude-opus-4-8[max].
Fork aleph/fable-nethack.

## HEADLINE: PET UTILIZATION (NH_PET, preserve-the-pet-on-descent) — the FIRST
## combat-survival resource lever — is DIRECTIONAL-but-NULL on the mean. It is a
## 10th converging angle on capability-boundedness, now at the COMBAT layer.
s11 unmasked COMBAT as the constraint binding once hunger was fixed. s12 built the
highest-value untried combat-side resource lever (PET, zero prior use) in its
cleanest zero-risk form and validated it ON TOP of the s11 hunger fix. The pet-
follow MECHANISM works but does NOT move combat survival — the binding constraint
is agent+pet combat CAPABILITY, not the pet's presence.

## What was built (all stamped opus-4.8[max], flat work/fable_nethack)
- **nh_agent.py** — flag C2_PET=_flag("NH_PET"), added to C2_ANY. New helpers
  `_live_pet` (nearest live pet) + `_pet_follow_wait` (bounded wait-at-stairs for
  the pet to become adjacent so it follows down). Single injection in `_descend`
  at the terminal `return "down"`. Consts PET_WAIT_MAX=8 (env NH_PET_WAIT_MAX),
  PET_WAIT_RADIUS=5 (env NH_PET_WAIT_RADIUS). Flag-off bit-identical (C2_ANY
  False verified; snapshot suite GREEN 19/19 incl. the pet-not-a-wall fixture).
- **e35_antifaint_smoke.py** — added pet_waits count + pet_start/pet_end/
  pet_maxdepth_present (pet-survival signal read off traj["monsters"] snapshots).
- **run_pet_block.sh (NEW)** — paired combat block runner. REF=C2.1+NH_FOODACQ+
  NH_ANTIFAINT (the s11 hunger fix carried in BOTH arms) vs TEST=REF+NH_PET.
  One-seed-per-process, SERIAL, resumable.
- Data: results/pet_block.jsonl (n=17 paired trash-melee-death seeds + 709 timeout).
  Docs: DOCTRINE_CARDS_s12.md (S12-1/2), PROGRAM_FINDINGS.md (10th angle + THE
  PET-UTILIZATION LEVER section), this handoff.

## THE RESULT (n=17 paired, cap 2000, one-seed-per-process; pet_block.jsonl)
- **Combat-death rate: REF 15/17=0.882 → TEST 14/17=0.824, Δ −0.059** (1 improved
  / 0 regressed — 1 discordant pair; directional only).
- **Progression mean: REF 0.0283 → TEST 0.0314, Δ +0.00305, 95% paired-bootstrap
  CI [−0.00157, +0.00998] — INCLUDES 0. NULL on the mean.**
- **Depth mean: REF 4.18 → TEST 4.35, Δ +0.18, CI [−0.53, +0.94] — includes 0.**
- **Mechanism CONFIRMED: pet-waits fired 8/17; pet preserved DEEPER 6/17** (seed 16
  Cavewoman depth 3→8; 706 Priest 3→5; 21 Priestess +1). But the agent still
  combat-died at the reached depth, AND the wait REGRESSES some seeds (746 Healer
  5→2). Gains and losses net to a wash. Zero new death classes.

## HONEST READ — peeling the pet-present sub-layer unmasks combat CAPABILITY
Preserve-the-pet-on-descent is inert because (1) pets already follow NATIVELY when
adjacent (NetHack's rule) → the lever's counterfactual is narrow (only fires when
the pet is 2-5 cells from the stairs; petw=0 on 9/17 = already adjacent, free
follow in both arms), and (2) where it fires, the pet loses the same attrition the
agent loses and dies to the same trash → presence ≠ survival. So combat did NOT
move; it unmasked combat CAPABILITY (win-the-fight-faster / take-fewer-hits) one
layer deeper. Stacked-death-classes law (s11) continues to hold: the mean moves
only when you address what is BINDING, and what binds combat is capability, not
the pet resource.

## Standing config UNCHANGED — NH_PET ships DEFAULT-OFF. No revert needed.
Bit-identical flag-off. Defaults PET_WAIT_MAX=8 / PET_WAIT_RADIUS=5 baked in.

## PRIORITY-2 FOODACQ n≈30 confirmatory — ATTEMPTED, BLOCKED (carry to s13)
Same pre-registered cd=8 design, 15 fresh fainting seeds mined (715 716 717 722
726 728 731 733 734 745 752 772 774 778 825; 43-seed fresh corpus available).
BLOCKED by episode wall-time: under s12 load, cap-2000 FAINTING-corpus episodes do
not terminate early (REF-no-FOODACQ survivors run the full 2000 steps) and exceed
the runner's 280s per-episode timeout → TIMEOUT_OR_FAIL, unusable. The trash-melee
combat corpus dies fast so the PET block completed; the hunger corpus is the
slowest episode class. Fix: raise per-episode timeout to ~500s (accept 4-5 min/ep)
in small off-peak chunks, OR cap ~1600 (fainting appears ~turn 1400, so >=1500
keeps the KPI). The s11 fainting result (Δ −0.267, CI [−0.533,+0.000], p=0.22)
therefore stands UNCONFIRMED at 95%. See CARD S12-2.

## Session-13 queue (value order)
1. **WIELD UPGRADE (NH_WIELD)** — the CAPABILITY-side combat lever the PET null
   points to. Zero wield actions EVER; wield the best available weapon (character
   sheet counterfactual_power ranks them) → win fights in fewer rounds → fewer
   incoming hits. Pair with FOODACQ baseline (as s12 did); measure combat-death +
   MEAN on the trash-melee corpus. This directly tests "combat is capability-bound."
2. **SAFE EARLY LEVELING** — arrive at the D5-6 kill-zone at xp 5+ (targeted safe
   kills, with pet help / at range), not the failed XP-pace-gate.
3. **FOODACQ n≈30 confirmatory** — unblock per CARD S12-2 (raise timeout or lower
   cap), fold with foodacq_cd8.jsonl, push the fainting CI clear of 0.
4. If BOTH capability-side combat levers (wield + safe-XP) also come back null →
   the combat layer is capability-bound like the decision layer (0-for-7), and
   DEMONSTRATION LEARNING (expert-ttyrec capability injection) is the only
   qualitatively-different remaining mean-lever (flagged since s11).
5. PET combat-POSITIONING form (position so pet tanks; don't outrun it in travel)
   — larger, pet-AI-coupled, high-regression build; deferred.
6. MILESTONE GIF: seed 16 (Cavewoman, pet preserved → depth 3→8) if it renders as
   a clean pet-changes-the-run reel.

## Gotchas (still bite)
- NLE only via PYTHONPATH=pylib; NH_* knobs read at IMPORT time.
- EPISODE WALL-TIME IS THE BINDING OPS CONSTRAINT under load: trash-melee combat
  seeds die fast (~150-400 steps, ~30-60s) so combat blocks complete; FAINTING /
  survivor seeds run the full cap (~280s at cap 2000) and blow the 280s timeout.
  Size hunger blocks with cap<=1600 or timeout>=500s. Chunks auto-background past
  the 10-min foreground Bash cap → block on CHUNK_DONE with an until-loop, don't
  detach-and-exit (that kills the job).
- ONE seed per process for paired blocks (s8 cross-seed leakage). SERIAL only —
  no parallel sub-blocks (VM contention → wall-timeout losses).
- petw=0 does NOT mean the pet was abandoned — it means the pet was already
  adjacent and followed for free. Use pet_maxdepth_present (deepest snapshot with
  a live pet) as the preservation signal, not the wait count.
- Push to FORK; commit author "NetHack Phase-L s12 (claude-opus-4-8[max])
  <nethack@botxiv.org>". Edit flat work/fable_nethack, cp to worktree
  papers/balrog/{code,artifacts}/nethack/.
- Findings docs canonical at researchy/docs/PROGRAM_FINDINGS.md +
  DEATH_TO_CAPABILITY.md (mirror artifacts copy in worktree). Doctrine cards +
  handoffs live in flat work/fable_nethack root.

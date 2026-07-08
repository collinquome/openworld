# HANDOFF_9 — Phase L session 8 → session 9

MODEL: claude-opus-4-8 (max thinking) wrote this — session 8, the FIFTH opus
session. Runtime identity VERIFIED at open (system-prompt id = claude-opus-4-8,
CLAUDE_EFFORT=high; Fable at usage cap) — NO mismatch. All s8 artifacts stamped
claude-opus-4-8[max]. Fork aleph/fable-nethack.

## HEADLINE: the ADVISORY-PUSH loop is BUILT + RUN on real NetHack — result NULL
The never-run test of the intuition thesis on NetHack itself (all prior
intuition results were composition-worlds). Both s8 workstreams are clean
NEGATIVE findings that CONVERGE on the capability-bound diagnosis.

1. **ADVISORY-PUSH (NH_ADVISORY) — NULL, ships flag-OFF.** At low-freq strategic
   triggers (level-entry/impasse/novelty/low-HP) the code hands a live LLM
   strategist the CONTEXT_SPEC package + the rule base's pushed ADVISORY
   reminders (RB.reminders_text) and executes its structured strategy choice.
   Paired (advisory off vs on, ONE seed/process, cap 1800), n=5 mixed-fragile:
   **paired Δ prog = −0.0011** (3 bit-identical, 833 Healer D5→D6, 812 Tourist
   D6→D4), maxD 5.80→5.60, 29 consults @5.8/ep, 100% parsed. The MECHANISM is
   verified working: at hp 6/12 the pushed HEAL_MIDBAND rule entered the LLM
   context and the strategist chose REST citing it verbatim. Consults logged
   verbatim in traj["advisory_consults"]. Read: the compiled agent is already at
   the intuition layer's ceiling for EARLY NetHack — the strategic
   explore/descend/rest choice is not where capability-bound deaths are decided.
   Caveat: n=5, cap-1800, COARSE 5-tag execution surface. See CARD S8-1.
2. **READINESS GATE (NH_READY_GATE) — DROP.** Role-conditioned rest-to-buffer
   before descending (nh_sheet RR(d+1) < thresh, digger-exempt, fragile roles).
   n=9 Tourist/Wizard/Rogue paired: block Δ +0.0055 but ENTIRELY one seed (847)
   proven by A/A test to be a cross-seed process-order artifact, NOT the gate;
   every heavy-fire seed is prog-identical. INERT because the existing rest gate
   already tops fragile roles to 85–92% HP before descending; the binding
   deficit is RR≈0.07–0.16 (under-leveled/geared), unfixable pre-descent
   (XP-grind INVALIDATED, HP maxed). SIXTH converging local/arrival drop. CARD
   S8-2.

## What landed (all stamped opus-4.8[max], flat work/fable_nethack)
- **nh_strategist.py (NEW)** — the advisory consult: builds prompt from context
  + pushed reminders, calls headless `claude -p` with ANTHROPIC_API_KEY UNSET
  (Max OAuth — the env key is DISABLED for runtime auth, broker keys are botXiv
  platform tokens not Anthropic keys), parses strict JSON strategy, tolerant +
  timeout-guarded, returns a verbatim record.
- **nh_agent.py** — NH_ADVISORY dispatcher (`_advisory` + `_advisory_trigger`,
  placed AFTER the safety cascade so the strategist never overrides a tactical
  emergency), bias hooks (DISENGAGE→E15 disengage window, REST→rest, DESCEND→
  skip loot detour, EXPLORE→defer descent), verbatim consult log. NH_READY_GATE
  (`_ready_gate` + `_readiness_ratio` via nh_sheet) at the descent site. Both
  flags default OFF; added to C2_ANY; flag-off bit-identical (all edits guarded;
  rulebase_equiv 130/130 green; A/A determinism confirmed).
- **nh_runner.py** — surfaces ready_gate_fires + advisory_consults in the result
  dict; traj["advisory_consults"] verbatim.
- Docs: docs/DOCTRINE_CARDS_s8.md (2 cards + method note), this handoff.

## Standing config UNCHANGED
Both s8 levers ship DEFAULT-OFF (NH_ADVISORY, NH_READY_GATE). No revert needed.

## METHOD NOTE (bites) — cross-seed leakage in capblock
A seed's result depends on which seeds ran before it in the same capblock
PROCESS (847 = D7 as 7th seed, = D9 alone; A/A within a process is bit-exact).
RUN PAIRED BLOCKS ONE SEED PER PROCESS (as s8 advisory did) or tear down the env
per episode. Prior 5-seed/process launch scripts carry this confound.

## Session-9 queue (value order)
1. **The mean-mover path is (near) exhausted at the LOCAL/ARRIVAL/STRATEGIC
   layers.** Six converging drops (REST/THROW/door-kite/heal×2/readiness) + the
   advisory-push NULL all say the same thing: deaths are capability-bound in the
   tactical EXCHANGE, not in objective selection or arrival HP. Before spending
   more on levers, DECIDE with the operator whether the deliverable is now the
   ARCHITECTURE + FINDINGS (the honest read) vs one more attack.
2. **If one more advisory attack:** the null used a COARSE 5-tag execution
   surface. The untested variant is a RICHER surface — the E11 objective-stack
   with TARGETS (not just a strategy tag), or consults sited at the tactical
   exchange (target-priority / kite-vs-fight), where the capability gap actually
   is. Also try a STRONGER strategist model / retrieval-augmented consult
   (NH-E13 KB lookup) per the Arm-B final spec. Bigger n (≥15) + role-strat.
3. **Migrate remaining guards into the rule base** (cheap, compounding): CAST_
   NEVER, FAST_THREATS, novelty-detector, elbereth → declarative rules (same
   rulebase_equiv recipe). Now that RB.reminders_text feeds the LLM, every
   migrated guard also becomes a pushable reminder.
4. Deprioritized (unchanged): ARMOR wear-rule (~0), Tourist/Priest profiles
   (do NOT copy the Healer naive-trigger mistake), E35 ttyrec (flag coordinator).

## Gotchas (still bite)
- NLE only via PYTHONPATH=pylib; NH_* knobs read at IMPORT time.
- capblock.py resumable + checkpoints per-episode — FOREGROUND/chunked. cap-3000
  Wizard SURVIVORS dominate wall-time (~90–130s each); a paired advisory block
  is slow (test arm = 6 consults × ~11s + sim). Budget it.
- Advisory consult = `claude -p` (Max OAuth). MUST unset ANTHROPIC_API_KEY (the
  env key 401s; broker BOTXIV_AGENT_A00X keys are 43-char botXiv platform tokens,
  NOT Anthropic keys). nh_strategist does this. anthropic SDK 0.109.2 present but
  UNUSABLE without a valid key.
- ONE seed per capblock process for paired blocks (cross-seed leakage).
- Lever fires from the result dict (ready_gate_fires / advisory_consults) or
  traj, NEVER stdout.
- Push to FORK; commit author "NetHack Phase-L s8 (claude-opus-4-8[max])
  <nethack@botxiv.org>". Edit flat work/fable_nethack, cp to worktree
  papers/balrog/{code,artifacts}/nethack/.

## Exit-criteria scoreboard (toward Phase E)
- Levers tested s8: 2 (advisory-push NULL, readiness DROP — both clean).
- **Architecture: the advisory-push loop (Arm-B on real NetHack) is BUILT, wired
  behind one flag, and DEMONSTRATED end-to-end (context + pushed reminders → LLM
  → structured strategy → execution, logged verbatim).** The s8 gate (b) "does
  the intuition layer USE the rule base to improve decisions?" — it USES it
  (verified: HEAL_MIDBAND citation) but does NOT improve the mean (null).
- Honest read: the mean-mover path has no remaining LOCAL/ARRIVAL/STRATEGIC
  lever (six drops + one null converge). Any remaining upside is a QUALITATIVELY
  different execution surface (richer objective-stack / tactical-layer consults /
  stronger+retrieval strategist) — or the value is now the architecture + the
  findings themselves (the capability-bound thesis, now triangulated from seven
  independent angles).

# DOCTRINE CARDS — Phase L session 8 (claude-opus-4-8[max])

MODEL: claude-opus-4-8 (max thinking), Phase L session 8 — the FIFTH opus
session. Runtime identity VERIFIED at open (system-prompt id = claude-opus-4-8,
CLAUDE_EFFORT=high; matches intended assignment; Fable at usage cap) — NO
mismatch. All s8 artifacts stamped claude-opus-4-8[max].

Two workstreams executed as PAIRED dev blocks (dev seeds only; fork
aleph/fable-nethack). Both are **findings that CONVERGE on the capability-bound
diagnosis** — neither shipped as a mean-mover; the value is the ARCHITECTURE
(the advisory-push loop is now BUILT and demonstrated on real NetHack) plus two
clean negative results.

---

## CARD S8-1 — ADVISORY-PUSH (LLM-strategist on REAL NetHack): NULL [HEADLINE]

**Layer:** INTUITION × PROCEDURE (the two-loop test). **Flag:** `NH_ADVISORY`
(default OFF). **Verdict:** NULL — does not beat compiled code; ships flag-OFF.
**This is the never-run test:** every prior intuition result in the program is
from COMPOSITION worlds (E21b-LIVE). This is the FIRST live-LLM-in-the-loop
result on NetHack itself — the Phase-E Arm-B gate, run in miniature.

**Statement.** At LOW-frequency strategic triggers (level-entry / impasse /
novelty / low-HP crisis) the code hands a live LLM strategist the CONTEXT_SPEC
package (map + memory + story, `nh_store.ctx_package`) PLUS the survival rule
base's pushed ADVISORY reminders (`nh_rulebase.RuleBase.reminders_text`), and
executes the returned structured strategy (one of DESCEND / EXPLORE / DISENGAGE
/ REST / FIGHT / PRESS_ON) by biasing the decision cascade. The question: does
live intuition + the rule base beat pure compiled code on real NetHack?

**Result (paired, advisory-off vs -on, one-seed-per-process, cap 1800):**
n=5 mixed-fragile pairs (831 Healer, 812 Tourist, 807 Rogue, 833 Healer, 839
Wizard). **paired Δ progression = −0.0011** (3 bit-identical, 833 Healer BETTER
D5→D6 +0.0089, 812 Tourist WORSE D6→D4 −0.0142). Mean maxD 5.80 → 5.60.
Consults: 29 total, **5.8/episode**, 100% parsed (0 errors). Strategy mix
dominated by EXPLORE + PRESS_ON, a wash (helped one seed, hurt another).
Marginal value per consult ≈ 0 (−0.0011 prog over 5.8 consults/ep).

**Mechanism VERIFIED working (the positive part).** The pushed rule-base
reminder demonstrably enters the LLM context and is USED: at hp 6/12 (seed 831)
the `HEAL_MIDBAND` ADVISORY was pushed and the strategist replied REST citing it
verbatim — *"as a Healer with 7 pw the HEAL_MIDBAND rule says to convert power
into HP now rather than press on under-prepared."* Consults are logged VERBATIM
into the trajectory (`traj["advisory_consults"]`: trigger, full prompt,
reminders, raw response, parsed strategy). The two consumers of ONE rule base
(s7) are both now live: procedure (`RB.check`) AND intuition (`RB.reminders_text`
→ LLM). The architecture pays its wiring debt.

**Read (honest, both directions were pre-registered).** The NULL says: for
early NetHack, the compiled agent is **already at the intuition layer's ceiling**
— the strategic explore/descend/rest choice at these triggers is NOT where the
capability-bound deaths are decided. The LLM picking "explore more" does not
change the downstream exchange the agent loses. This CONVERGES with the s8
readiness-gate DROP (S8-2) and the avoidability audit: deaths are in the
tactical exchange EXECUTION (capability), not in strategic objective SELECTION
(what both the rule base and the LLM operate on). A live strategist that only
re-ranks the same coarse objectives the code already sequences has no lever the
code lacks.

**Caveats (do not overclaim the null).** n=4, cap-1800 truncation, and a COARSE
5-tag execution surface (the strategist proposes among strategies the navigator
already supports — it cannot invent a new tactic). A richer execution surface
(objective-stack with targets, per-E11) or triggers sited at the tactical
exchange (not the strategic junction) are the untested variants. The null is
SUGGESTIVE, not decisive.

**DUAL provenance.** knowledge = program design (NH-E11 strategist/navigator +
CONTEXT context-package + s7 rule base `reminders_text` hook). insight =
AG (BUILD + first real-NetHack run); mechanism = BORROW-FIELD (backtest→deploy)
+ NOTICE-ABSENCE (the hook existed, unused, since s7).
**Replication recipe.** `NH_ADVISORY=1` with `NH_RULEBASE=1 NH_STORE=1` (context
+ reminders sources) + standing config; `NH_ADVISORY_MAX=6 NH_ADVISORY_GAP=25`;
paired vs `NH_ADVISORY=0`; ONE seed per capblock process (avoid cross-seed
leakage, see NOTE). Consult = headless `claude -p` with `ANTHROPIC_API_KEY`
unset (Max OAuth; the env key is disabled for runtime auth). Verify in
`traj["advisory_consults"]`.

---

## CARD S8-2 — ROLE-CONDITIONED READINESS GATE: DROP (subsumed / inert)

**Layer:** PROCEDURE. **Flag:** `NH_READY_GATE` (default OFF). **Verdict:** DROP
— no reliable survival signal; structurally subsumed by the existing rest gate.

**Statement.** Targeting the downstream death (NH-E12: 59% ARRIVAL_CONSTRAINT;
death-shape = descend at ~35% HP): before a FRAGILE (digger-exempt) role takes
the '>', if `readiness_ratio(d+1)` (nh_sheet, vs `depth_threat.json`) < a
per-role threshold, rest to fuller HP than the default gate — buy arrival buffer
only for dangerous descents. Explicitly NOT the failed s4 XP-pace-gate (rests
HP, never grinds XP; role-conditional; digger-exempt).

**Result (paired, gate-off vs -on, n=9 Tourist/Wizard/Rogue, cap 3000):**
block Δ prog = +0.0055, but **entirely one seed (847 Wizard)**, which an A/A
determinism test proved is a **cross-seed process-order artifact**, NOT the
gate (gate-off-alone reproduces the "improved" 847). Every HEAVY-fire seed
(Tourist 812/880 = 48/69 gate-fires, Rogue 807 = 56) is prog-IDENTICAL between
arms. reach@D8 0%→11% is the same single artifact seed.

**Why inert.** Instrumentation (`NH_READY_DEBUG`) shows the agent **already
arrives at the stairs HP-topped**: the standing config's existing rest gate
(`_should_rest`, lo 0.6/hi 0.85 deep, 0.75/0.92 shallow) already rests fragile
roles to 85–92% before descending. The readiness gate's true divergence window
is a thin 85–92% HP band; below it BOTH arms rest, so actions coincide. Healers
self-heal to FULL (100%) — fully inert. The binding deficit at descent is
`readiness_ratio ≈ 0.07–0.16` (wildly under the threat band = under-LEVELED /
under-GEARED), which NO realizable pre-descent action fixes: XP-grind is
INVALIDATED (PRIORS), HP is already maxed. **Arrival-HP is not the lever — the
capability is.**

**DUAL provenance.** knowledge = NH-E12 backfill (59% ARRIVAL_CONSTRAINT) +
KPI death-shape + nh_sheet RR + depth_threat.json. insight = AG (BUILD +
instrument); mechanism = ASK-WHY-ON-FAILURE (why 0 fires on a D8 Healer? →
already full HP) + NOTICE-ABSENCE (no divergence surface). This is the SIXTH
converging local/arrival lever to drop (REST s4, THROW s6, door-kite s7, heal
s6/s7, and now readiness) — all confirm capability-bound.
**Replication recipe.** `NH_READY_GATE=1` (+`NH_READY_RR`/`NH_READY_HP`/
`NH_READY_ROLES`) vs off; fragile non-digger roles; `NH_READY_DEBUG=1` prints
the arrival-HP/RR at each descent to show the (non-)divergence surface.

---

## METHOD NOTE (bites future blocks) — cross-seed state leakage in capblock

An A/A test (seed 847, gate-off, two suffixes) is bit-identical WITHIN a fresh
process, but a seed's result **depends on which seeds ran before it in the same
capblock process** (847 = D7 as the 7th seed of a 9-seed process, = D9 run
alone). Some process-global state (module cache / NLE env reuse) leaks across
episodes. **Consequence:** paired blocks that run many seeds per process can
attribute a leaked delta to the lever. **Fix used s8:** ONE SEED PER PROCESS for
the advisory block. Recommend the same for all future paired blocks, or a
per-episode env teardown. (The prior launch scripts run 5 seeds/process — their
deltas carry this confound at some magnitude.)

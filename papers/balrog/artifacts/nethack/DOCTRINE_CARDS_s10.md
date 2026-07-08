# Doctrine Cards — Phase L session 10 (claude-opus-4-8 [max thinking])

Runtime identity VERIFIED at open: system-prompt model id = claude-opus-4-8,
max thinking; Fable at usage cap. All s10 artifacts stamped claude-opus-4-8[max].
Fork aleph/fable-nethack. Session = SHIP the anti-faint guard (first demonstration-
aimed capability lever at the #1 death class) + formalize the DOOM-MOMENT LOOP.

---

## CARD S10-1 — ANTI-FAINT PAIRED BLOCK (rule [ANTI_FAINT], flag NH_ANTIFAINT)  [VERDICT: __FILL__]
provenance: knowledge=DEMONSTRATION (S9-2 expert hunger law, alt.org ttyrecs) +
insight-origin=OP (DEATH_TO_CAPABILITY Tier-1) + precedent CAST_HUNGER. layer:
LOGISTICS. model: claude-opus-4-8[max].

**Pre-registered design (from CARD S9-3).** REF = C2.1 frozen (NH_FOOD2 NH_PRAYFIX
NH_LOS NH_TOPO NH_GUARD NH_CAST NH_CASTHUNGER NH_E15) vs TEST = REF + NH_ANTIFAINT.
ONE seed per process (s8 cross-seed leakage). cap 6000. Proximal KPI =
**Fainting-incidence** (fraction of episodes with peak hunger tier >= Fainting).

**Seed design honesty.** Dev seeds 101-140 NEVER faint (those roles die to combat
first — verified: 0/40 fainting in the corpus), so they give no power on the
fainting KPI (they are the NO-REGRESSION check: guard inert, REF==TEST bit-identical
when hunger never reaches Hungry — confirmed seeds 101/102). The fainting-prone
seeds live in the 700s/4000s gym blocks (NOT the untouchable 6000-6099/7000-7024).
So the power block is HUNGER-ENRICHED: seeds selected for reaching Fainting in the
prior corpus. Selection inflates the shared baseline, but the PAIRED REF-vs-TEST
delta at the same seeds is an unbiased treatment-effect estimate (both arms equally
selected) — the pre-registered "does the guard prevent faints" test.

**Result (n=__FILL__ paired seeds, hunger-enriched):**
- Fainting-incidence: REF __FILL__ -> TEST __FILL__ ; DELTA __FILL__ [95% CI __FILL__]
- Hunger-death rate (starved+fainted end): REF __FILL__ -> TEST __FILL__
- Guard fired in __FILL__/n episodes; PREVENTED (REF faint -> TEST no-faint) __FILL__.
- Per-role table + per-seed detail in results/antifaint_enriched.jsonl.

**Verdict: __FILL__.** Mechanism: __FILL__ (does the guard fire and hold hunger
at/above Hungry?).

**Replication recipe:** `./run_antifaint_block.sh results/antifaint_enriched.jsonl
<seeds...>` (PYTHONPATH=pylib, one-seed-per-process, resumable) then
`python3 analyze_antifaint.py results/antifaint_enriched.jsonl`.

---

## CARD S10-2 — THE DOOM-MOMENT LOOP, applied to hunger  [SOLID offline attribution]
provenance: insight-origin=OP (2026-07-08 doom-moment-loop directive: search
BACKWARD for the point of no return, not fixed-offset replay) + knowledge=our own
196-episode fainting corpus. layer: METHOD. model: claude-opus-4-8[max].

**The loop (formalized).** Per death: (1) DOOM-MOMENT SEARCH — backward from death,
the last step where a surviving line still existed = the fatal decision; (2)
RECOVERABLE-WINDOW = steps from doom-moment to death = how much warning (long =
foreseeable/high-value; 1-step = dice/no-lesson); (3) COUNTERFACTUAL corrected
decision; (4) SELF-PLAY VALIDATION across >=3 seeds of the doom-state CLASS; (5)
deploy via paired block.

**Hunger application (offline, tier-analytic — no env replay needed because hunger
dynamics are near-deterministic: nutrition depletes ~1/turn, eating resets it).**
Over the 196 corpus episodes that reached Fainting:
- **100% (196/196) passed through Hungry BEFORE Fainting** — the guard's actionable
  tier is on the path to every single hunger death.
- **Recoverable window Hungry->Fainting: median ~1399 steps, mean ~2045** (p10=230,
  p90=3992, max=10510). **Every episode had >=50 steps of warning.**
- Weak->Fainting window (the OLD guard's tier): median ~902 steps — even the
  existing WEAK-eat had huge warning but still failed (at Weak there is often no
  accessible food left; S9-3 finding).
- Fainting->episode-end cascade: median ~1866 steps — the agent lingers at Fainting
  a long time before dying (repeated faints), more warning still.

**Reading.** Hunger deaths are SLOW-MOTION, foreseeable failures — not dice. The
doom moment lands at the Hungry->Weak boundary; the corrected decision is
eat-at-Hungry — INDEPENDENTLY REDISCOVERING the expert hunger law (S9-2) from our
own death corpus, by a completely different method (offline backward window vs
forward demonstration replay). The anti-faint paired block (S10-1) IS the self-play
validation step (4) of this corrected strategy. Composition confirmed.

**Scope caveat.** This is the tier-analytic doom-moment (justified by hunger's
near-determinism). The heavier general version — real-env deterministic replay +
in-model MC backward search for the exact survivable/unsurvivable boundary — is
future work for the stochastic death classes (trash-attrition, mid-tier) where
the point of no return is not analytically obvious. Recipe: replay the action
prefix to step k (same seed), branch, test survivability; binary-search k.

**Replication recipe:** offline scan of results/trajectories/*.json hunger[] tiers
(first-Hungry / first-Weak / first-Fainting / end step per episode); see the s10
doom-window analysis block.

---

## CARD S10-3 — SAFE-CORPSE TABLE AUDIT (P3, preliminary)  [TENTATIVE]
provenance: insight-origin=OP (DEATH_TO_CAPABILITY Tier-1 corpse-aggressiveness) +
knowledge=source/wiki.

SAFE_CORPSES (nh_common:155) = 56-species whitelist; correctly includes the safe
high-value ones (floating-eye CORPSE = telepathy and safe to EAT though deadly to
MELEE; lizard = never rots; the full trash-mob set). Whitelist is conservative by
construction (rejects anything unlisted) but is NOT obviously over-rejecting on
species — the trash mobs the agent actually kills are nearly all present. The more
probable corpse lever is the FRESHNESS/REACHABILITY window (eat the corpse while
fresh at Hungry, S9-3), not the species list. Recommend: instrument passed-up
fresh safe corpses per episode before expanding the table. Not shipped.

---

## Session queue for s11
1. If S10-1 shipped: watch for the terminal hunger-death-rate move on a fresh
   eval block; consider the next Tier-1 hunger piece (food-paced descent / nutrition
   as first-class dossier resource).
2. PET UTILIZATION (Tier-2, zero prior use) — the untried trash-attrition lever.
3. General doom-moment loop with real-env backward replay on the trash-attrition
   corpus (the stochastic death classes S10-2 deferred).
4. Deeper ttyrec: a past-D21 ascension game to extend S9-1 world-model validation.

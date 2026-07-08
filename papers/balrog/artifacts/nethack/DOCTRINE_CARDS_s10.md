# Doctrine Cards — Phase L session 10 (claude-opus-4-8 [max thinking])

Runtime identity VERIFIED at open: system-prompt model id = claude-opus-4-8,
max thinking; Fable at usage cap. All s10 artifacts stamped claude-opus-4-8[max].
Fork aleph/fable-nethack. Session = SHIP the anti-faint guard (first demonstration-
aimed capability lever at the #1 death class) + formalize the DOOM-MOMENT LOOP.

---

## CARD S10-1 — ANTI-FAINT PAIRED BLOCK (rule [ANTI_FAINT], flag NH_ANTIFAINT)  [VERDICT: NULL on fainting-incidence — capability-bound. Do NOT ship default-ON; keep flag-OFF.]
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

**Result (n=7 paired seeds, hunger-enriched fast-fainting corpus seeds, cap 2000,
serial one-seed-per-process; results/antifaint_faint.jsonl):**
- **Fainting-incidence: REF 0.571 (4/7) -> TEST 0.571 (4/7). DELTA = +0.000,
  95% paired-bootstrap CI [+0.000, +0.000]** (zero discordant pairs — every seed
  has identical faint-status across arms).
- Hunger-death rate: REF 0.143 (1/7) -> TEST 0.286 (2/7) (the one difference is
  seed 912, where TEST died within the 2000-step horizon while REF truncated at
  2000 — both reached Fainting; noise, not a real regression).
- **Guard fired in 4/7 TEST episodes, 29 fires total; PREVENTED 0 faints.**
- Per-role: Wizard REF 2/3 TEST 2/3 (29 fires); Rogue 1/1=1/1 (0 fires); Caveman
  1/1=1/1 (0 fires); Cavewoman 0/1=0/1; Samurai 712 Weak=Weak (6 fires, no faint
  either arm).

**Verdict: NULL on the KPI, and the MECHANISM says why — the lever is CAPABILITY-
bound, not decision-bound.** The guard fires exactly as designed at Hungry, but:
- On 2 of 4 REF-faint seeds (737 Rogue, 754 Caveman) it fired **0 times** despite
  reaching Hungry — because there was **NO readily-available food to bank** (these
  roles carry none; no fresh corpse in reach). "Eat now" is a no-op with an empty
  larder.
- On 769/912 (Wizards) it fired 1-4x (banked what little was there) but the agent
  **still fainted** — insufficient food.
- On the food-carriers (712 Samurai 6 fires, 980 Wizard 18 fires) it fired a LOT
  but **neither arm fainted anyway** — active but non-differentiating.
The expert "never below Hungry" law (S9-2) holds for experts because they have
ACQUIRED food; our hunger-prone roles reach Hungry with nothing to eat. **The
binding constraint is food ACQUISITION, not eat-timing.** Demonstration correctly
AIMED the lever (which the 7 intuition levers never did) but the aimed lever is
itself capability-bound — an 8th converging angle on capability-boundedness, now
at the RESOURCE layer. Redirects Tier-1 to the food-ACQUISITION levers
(corpse-eating aggressiveness / food pickup+hunting / gold->food), NOT eat-timing.

**Honest caveats.** n=7 is modest: fainting seeds are inherently deep survivors
(slow episodes), the shared VM was overloaded (load ~5-6/4cores) causing wall-
timeout losses (728/918 both arms, 781 TEST), and cap was lowered to 2000 (from
the pre-reg 6000, applied equally to both arms so the paired delta stays valid) to
fit compute. Seeds are hunger-enriched (selected for prior Fainting), so the PAIRED
delta is the valid estimand, not the absolute rate. Zero discordant pairs gives a
tight [0,0] CI but low power to detect a *small* effect — however the mechanism
(guard fires 0x when no food; fires a lot but doesn't prevent when food is scarce)
is a stronger read than n: it is not seed luck, it is food-unavailability.

**Regression/ship:** flag-off is bit-identical (confirmed: seed 782 + dev 101/102
REF==TEST when hunger stays below Hungry). Drop-rule => do NOT ship default-ON.
NH_ANTIFAINT stays default-OFF (unchanged). The guard is a correct, bit-identical
scaffold that only becomes a mean-mover once food-acquisition capability lands.

**Replication recipe:** `./run_antifaint_block.sh results/antifaint_faint.jsonl
<seeds...>` (PYTHONPATH=pylib, one-seed-per-process, SERIAL to avoid VM-contention
timeouts, cap via NH_STEPCAP) then `python3 analyze_antifaint.py
results/antifaint_faint.jsonl`. Fast-fainting seeds via the corpus scan in the s10
log (trajectories with peak hunger>=4, ranked by first-Fainting step).

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
1. **FOOD ACQUISITION is the real Tier-1 lever** (S10-1 redirect — eat-timing is
   solved-but-inert; the gap is having food to eat). Build + paired-test, in order:
   (a) AGGRESSIVE SAFE-CORPSE EATING — eat every safe fresh corpse the agent walks
   over/kills (bank nutrition proactively, not just at Hungry); instrument how often
   a safe corpse is passed up. (b) FOOD PICKUP — pick up floor food/rations always.
   (c) gold→food shopping (Tourists). KPI: does the agent ARRIVE at Hungry with food
   in inventory? (the precondition the anti-faint guard needs). Then re-run S10-1 with
   acquisition ON — the guard should go live.
2. Bigger, faster anti-faint block when the VM is not overloaded: n>=20 paired,
   SERIAL, cap>=3500 (this session got n=7 due to load + timeout losses).
3. PET UTILIZATION (Tier-2, zero prior use) — the untried trash-attrition lever.
4. General doom-moment loop with real-env backward replay on the trash-attrition
   corpus (the stochastic death classes S10-2 deferred).
5. Deeper ttyrec: a past-D21 ascension game to extend S9-1 world-model validation.

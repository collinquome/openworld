# Doctrine Cards — Phase L session 11 (claude-opus-4-8 [max thinking])

Runtime identity VERIFIED at open: system-prompt model id = claude-opus-4-8,
max thinking; Fable at usage cap. All s11 artifacts stamped claude-opus-4-8[max].
Fork aleph/fable-nethack. Session = BUILD + VALIDATE the food-ACQUISITION lever
(the s10 redirect) and RECONCILE the config-sensitive raw numbers into one honest
verdict.

---

## CARD S11-1 — FOOD-ACQUISITION: OPPORTUNISTIC SAFE-CORPSE BANKING (rule [FOODACQ], flag NH_FOODACQ)  [VERDICT: progression-safe HUNGER-DEATH win at cd=8; NOT a mean-mover. Ship flag-OFF scaffold.]
provenance: insight-origin=OP (DEATH_TO_CAPABILITY Tier-1 food-acquisition /
corpse-aggressiveness) + knowledge=our own S10-1 death mechanism (guard-fired-
empty-larder) + demonstration arbiter (S9-2: experts have ACQUIRED food).
layer: LOGISTICS. model: claude-opus-4-8[max].

**What was built.** NH_FOODACQ = eat a safe fresh corpse we ALREADY stand on
(typically after a kill we won), gated on hunger != Satiated (choke-safe) + no
adjacent hostile, rate-limited to once / FOODACQ_COOLDOWN turns. Corpse-only
(inventory food + prayer stay in the ANTIFAINT/WEAK crisis blocks). Placed just
before the s9 ANTI-FAINT guard in _decide. Verified: food PICKUP was ALREADY live
under NH_FOOD2 in the REF (perceptor FOOD_NAMES table covers rations/fruit/etc.) →
pickup is NOT the treatment; banking is. Flag-off is bit-identical (C2_ANY False).

**Design honesty — two dead ends found by regression, then the reconciled config.**
1. v1 AGGRESSIVE (active <=2-step walk-to-corpse routing + no cooldown): on the
   hunger corpus, fainting 6/15→~1/15 STRONG (~5258 fires) — but a REGRESSION
   check on healthy dev seeds exposed a catastrophic descent STALL: depth 15→1
   (Archeologist 110), 9→1 (Valkyrie 700); mean descent depth REF 5.20 → TEST
   4.00 (**−1.2**). The agent avoids fainting by FARMING corpses in place instead
   of descending. The "win" was the agent not playing the game. DROPPED.
2. v3 OVER-CONSERVATIVE (underfoot-only + cooldown=25, ~119 fires): progression-
   safe but hunger effect NULL — fainting 6/15→5/15, 95% CI [−0.27,+0.13].
3. **cd=8 RECONCILED (underfoot-only + cooldown=8):** threads the needle.

**Result — cd=8, n=15 hunger-prone/fainting seeds, cap 2000, one-seed-per-process,
REF=C2.1 frozen (NH_FOOD2 NH_PRAYFIX NH_LOS NH_TOPO NH_GUARD NH_CAST NH_CASTHUNGER
NH_E15) vs TEST=REF+NH_FOODACQ; results/foodacq_cd8.jsonl:**
- **Death-while-fainting (hunger-death proxy): REF 5/15=0.333 → TEST 0/15=0.000,
  Δ −0.333.** All five hunger-linked deaths eliminated.
- **Fainting-incidence: REF 6/15=0.400 → TEST 2/15=0.133, Δ −0.267, 95% paired-
  bootstrap CI [−0.533, +0.000]** (5 improved / 1 regressed; McNemar exact
  p=0.22 — directional, not yet 95%-significant at n=15; needs n≈30 to settle).
- **Progression-NEUTRAL: mean descent depth REF 5.20 → TEST 5.47 (+0.27); 4 seeds
  deeper, 3 shallower.** No stall (contrast v1's −1.2).
- **acq_fires: median 8, total 146** — MODERATE (36× fewer than v1's ~5258). The
  hunger effect does NOT scale with fire count; heavy firing was the STALL, not
  the win.
- **Zero new death classes.** All TEST deaths are ordinary combat (orcish arrow,
  gnome, coyote, gas spore, wand, werejackal, horse). SAFE_CORPSES whitelist +
  cannibal guard held; no over-eat choke, no unsafe-corpse poisoning.

**Verdict: a real, progression-safe SUB-WIN at the #1 death class — but NOT a
mean-mover.** NH_FOODACQ(cd=8) is the first lever in the program to REMOVE a death
class safely (hunger-death 5/15→0/15, descent unharmed) — the 9th converging angle
is a lever, not a wall. BUT the overall progression/ascension mean does not move:
the lever CONVERTS hunger-deaths into combat-deaths at the SAME depth. Removing
hunger unmasks COMBAT as the next binding constraint. So: the resource layer had a
genuine aimable progression-safe lever (unlike the 8 decision-levers), acquisition
capability injects successfully AT THE HUNGER CLASS, and the mean stays capability-
bound because combat now binds. Capability came from ACQUIRING what the agent
needed, not reasoning harder — and the next capability to inject is combat survival.

**Regression/ship.** flag-off bit-identical (confirmed: C2_ANY False; dev seeds
102/110 REF==TEST, facq=0). Default cd=8 baked into FOODACQ_COOLDOWN. Ships
DEFAULT-OFF (matching the s9 ANTIFAINT scaffold precedent) — a validated,
progression-safe scaffold that becomes a default-ON candidate once (a) the n≈30
confirmatory block pushes the fainting CI clear of 0 and (b) it is paired with a
combat-survival lever so the death-class it clears isn't just handed to combat.

**Replication recipe:** `NH_STEPCAP=2000 NH_FOODACQ_COOLDOWN=8 ./run_foodacq_block.sh
results/foodacq_cd8.jsonl <seeds...>` (PYTHONPATH=pylib, one-seed-per-process,
SERIAL; REF vs REF+NH_FOODACQ). Analyze with the paired-bootstrap block in the s11
log. Hunger-prone seeds via the corpus scan (results/trajectories/*.json peak
hunger>=4): the 76-seed fainting corpus; block used 700-712/737/754/769/781/782/
912/980/4003/4009. Regression-check on healthy dev seeds (101/102/110).

---

## CARD S11-2 — CONFIG-SENSITIVITY IS A REAL METHODOLOGY TRAP (rate-limit vs stall)  [SOLID method note]
provenance: insight-origin=self (s11 reconciliation). layer: METHOD.

A resource-acquisition lever has a knob (banking rate) that trades the target KPI
against a DIFFERENT KPI (progression). The raw headline (6→1 fainting) was real in
direction but produced by a config that STALLED descent — a confound invisible
unless you run the regression check on non-target seeds. Two lessons:
1. **Always regression-check a "win" on OFF-target seeds** (here: healthy dev seeds
   for progression), not just the enriched target corpus. The target-KPI win and
   the off-target regression live at opposite ends of the same knob.
2. **"Effect scales with how hard it fires" is a seductive false read.** Here more
   fires = more stall, not more win; the reconciled config fires 36× less and
   keeps the win. When a lever's activity correlates with its KPI, check whether
   the activity is CAUSING the KPI or is a proxy for the confound (staying-in-place
   = both more banking AND more fed AND less descent).

---

## Session queue for s12
1. **n≈30 confirmatory FOODACQ(cd=8) block** to push the fainting-incidence CI
   clear of 0 (currently [−0.533, +0.000], McNemar p=0.22). Same pre-registered
   design; mine ~15 more seeds from the 76-seed fainting corpus.
2. **COMBAT-SURVIVAL lever** — the newly-unmasked binding constraint. FOODACQ
   converts hunger-deaths into combat-deaths at the same depth; the mean won't move
   until combat survival improves. This is the real Tier-1 now. (Candidates from
   the untried set: PET UTILIZATION for tanking, WIELD UPGRADE — zero wield actions
   ever, safe early leveling before descent.) Pair it with FOODACQ and re-measure
   the MEAN (progression), not just the death class.
3. **MILESTONE GIF** rendered s11 (Priestess 781 / Wizard 769: REF starves→dies vs
   TEST banks-corpse→survives); attach to the paper's resource-reframe figure.
4. General doom-moment loop with real-env backward replay on the combat/trash-
   attrition corpus (the stochastic death classes S10-2 deferred).
5. Deeper ttyrec: a past-D21 ascension game to extend S9-1 world-model validation.

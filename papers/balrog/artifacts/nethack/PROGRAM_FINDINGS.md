# Program Findings — living synthesis
Owner: A001 (Origin Aleph). Updated as findings mature. Confidence graded SOLID / EMERGING / TENTATIVE.
Frame: the four capture themes — LEARNING, STRATEGIES, WORLD MODELS, OBJECTIVE GOALS/KPIs.

## LEARNING
- **The memory law [SOLID — 4 testbeds].** Memory is transformative exactly where information is missing within an episode but persists across episodes (TextWorld trap-chest 64→100%, information-theoretically guaranteed); null-to-harmful where dice or search-budget bind (MiniHack 95/95/82.5, NetHack paired −1.21, Crafter variance-only). Characterized law + mechanism, not a slogan.
- **Avoidability finding [SOLID — program-redirecting].** ~5% of damage is decision-avoidable; ~60% model-endorsed dice → deaths are CAPABILITY-bound, not decision-bound. Explains why decision-layer levers came back flat; redirected the program to the verb/capability frontier.
- **Price of source-blindness [SOLID].** Interaction-only induction = 58% of source-reading sibling; gap is starvation-dominated (knowledge gap, not reasoning gap). Meta-twin: NH-E27 asks the same of learning-process knowledge.
- **Death-learning shape [EMERGING].** 55% of trash deaths escapable ~40 steps out (shallow errors) — but the naive REST fix FAILED (same-speed hostile adjacent → can't flee/rest). Honest negative that located the real lever (kite/stairs menu).

## STRATEGIES
- **Tier ablation [SOLID — foundational].** Synthesis-model reasoning tier is THE binding variable: same recipe 65.8% (Sonnet) → 100% (Fable) on Baba. Everything rests on this.
- **Defeasibility [SOLID — clean experiment].** T5/T6 pair: "never pick up" as compiled RULE fails T5; as per-world HYPOTHESIS wins both. Intuition must stay overridable; overrides bounded by memory (the bound licenses the risk).
- **Capability > tuning [EMERGING].** 50/248 verbs ever used; the one CI-positive lever = teach the Wizard to cast (+2.41 [+0.75,+4.41]). Points live in unused capability, not decision polish.
- **Discipline results [SOLID].** Drop-rule caught seed-luck ≥3× (Crafter v2 inversion, shallow-hunting sign-flip, NetHack n=5 mirage); select-don't-vote (ARC-3 E95, adopted); pre-registration + auto-generated numbers prevent framing drift.

## WORLD MODELS
- **Verified code doesn't drift [SOLID — now corroborated on INDEPENDENT expert data].** 0 violations / 233k+ predictions on our own play; distributional gates generalize exact-match to stochastic domains (16/23 species pass chi-square). NH-E35a (s9) extends this to data we did NOT generate: **0 violations / 56,407 action-free possibility-set checks (V_TIME/V_HP/V_XP/V_DEPTH) replaying 4 public alt.org expert human ttyrecs** (2 top-class players, ~15k turns) through our symbolic model. Honest caveats: action-labelled rules (V_MOVE/V_NONMOVE_POS) aren't cleanly testable from V1 human ttyrecs (no keypresses; tty cursor≠hero → 19–23% V_MOVE "rate" is position-recovery noise, excluded), and the fetched games are shallow (max Dlvl 13 < our D21 — alt.org prunes ascension archives), so the invariant layer is validated on independent play but not yet past our own depth. NLE's own C ttyrec Converter emits nothing for dgamelaunch human recordings; we hand-rolled a minimal ANSI emulator (e35_ttyrec.py). The thesis in one stat, now on foreign data.
- **Recipe saturates deterministic, walls on stochastic [SOLID].** Baba 100 / BabyAI 100 / TextWorld 90 / MiniHack 92.5 (beaten/ceiling); Crafter 56 / NetHack ~6 (dice+capability bound). Boundary = wherever verification runs out.
- **World models need audits [SOLID pattern].** Load-bearing bugs found by our own tooling: armor AC 50% wrong, item-under-@ invisible, corpse-on-victim-cell, shopkeeper-dpt≈0. Every fixed bug → permanent snapshot fixture.

## OBJECTIVE GOALS / KPIs
- **The goal-inference wall [SOLID — ARC-3 sibling].** Perfect world models + 3 principled goal-discovery attacks fail (0/9, 0/3, 0/3); wins are PROCEDURES not reachable states (E103). Named frontier; NH-E28 targets it with procedure-native hypotheses + cross-run induction + opacity ladder.
- **avoidable-damage as high-SNR proxy KPI [SOLID].** Moves before the noisy terminal score → lets levers validate in ~20 episodes. The KPI tree (goal/drivers/performance) + potential-based-shaping guard (E29-E33) formalizes this.
- **Composition worlds: intuition necessary [SOLID — 4-arm ablation, 4/4 predictions confirmed].** 48-episode blind ablation: code-only & no-memory solve 0 composition/counterintuitive worlds; no-memory solves only co-located control; no-override solves SAFE composition but 0 counterintuitive; ONLY full-stack (memory×override) solves counterintuitive worlds. SMOKING GUN: no-override *identified* the self-damaging opener (C=1.00 pre-veto) but the hard avoid_damage constraint vetoed it every time → override AUTHORITY, not reasoning, is the blocker. Perception+memory+procedure plateau; the defeasible-override intuition layer is what breaks counterintuitive composition. (Blind arm on fresh grammar + haiku in-loop; complements the T1/T5/T6 full-stack wins on registered worlds.)
- **Metric shape sets risk appetite [SOLID].** Max-rung progression is convex → optimal policy is tail-seeking (buy cheap depth lottery tickets) under a ruin (ε-death) constraint, NOT expected-value.

## THE CAPABILITY-BOUNDEDNESS RESULT [SOLID — 8 converging angles + a 9th progression-safe SUB-WIN + a 10th at the COMBAT layer + an 11th (WIELD) that resolves to the ACQUISITION-BOUND meta-finding]
(8th angle, s10: the anti-faint guard — a DEMONSTRATION-aimed resource lever — is NULL on fainting-incidence because the agent reaches Hungry with no food to eat; capability-boundedness holds even for correctly-aimed levers, now at the resource layer. See the RESOURCE REFRAME section.)
(9th angle, s11: food-ACQUISITION (NH_FOODACQ, corpse-banking) DOES remove the hunger death-class safely — death-while-fainting 5/15→0/15, progression-neutral — the first lever that isn't a wall. But the MEAN stays capability-bound: it converts hunger-deaths into combat-deaths at the same depth, unmasking COMBAT as the next binding constraint. A death-class was moved; the mean was not. See THE FOOD-ACQUISITION LEVER section.)
(10th angle, s12: PET UTILIZATION in its cleanest zero-risk form (NH_PET, preserve-the-pet-on-descent — wait a bounded number of turns for the pet to be adjacent so it follows down the stairs) tested ON TOP of the s11 hunger fix (FOODACQ baseline) on the trash-melee death corpus is DIRECTIONAL-but-NULL on combat survival — combat-death 15/17→14/17 (1 discordant), progression Δ +0.003 with 95% CI [−0.0016, +0.0100] straddling 0. The mechanism is confirmed (pet preserved deeper on 6/17, waits fire on 8/17; seed 16 Cavewoman depth 3→8) but does NOT propagate to survival, because pets follow NATIVELY when adjacent so the lever's counterfactual is narrow, and where it fires the pet loses the same attrition the agent loses (it dies to the same trash). Preserving a capability-bound resource is inert; the wait itself regresses some seeds (746 depth 5→2). Peeling the "pet-present" sub-layer off combat unmasks combat CAPABILITY (win-the-fight / take-fewer-hits) as the true binding constraint — the stacked-death-classes law continues one layer deeper. See THE PET-UTILIZATION LEVER section.)
(11th angle, s13: WIELD UPGRADE (NH_WIELD, wield the best in-inventory weapon when it beats the current melee dpt by a margin, safe) — the CAPABILITY-side combat lever the s12 PET null pointed to, the cleanest DIRECT combat-capability injection (zero wield actions ever in program history) — is a MECHANICAL null: n=17 paired, progression Δ +0.0000 CI [0,0], 17/17 bit-identical, wield-fires=0. The counterfactual is PROVABLY EMPTY: a 77-role-episode probe across all 15 roles found ZERO in-inventory wield-upgrades — every NetHack role starts wielding its best in-inventory weapon. This REFINES the law: capability injection can only inject capability that EXISTS and is UNUSED (the +2.41 Wizard-cast win had unused casting; wielding has none). The read-only diagnosis (NH_WIELD_DIAG) then resolved WHY wield never fires into the ACQUISITION-BOUND meta-finding below: for weak-weapon roles a real upgrade sits ON THE FLOOR unlooted. See THE WIELD LEVER + ACQUISITION-BOUND META-FINDING section.)
NetHack mean is CAPABILITY-bound, not decision-bound. 0-for-7 mean-mover attempts triangulate it: 6 local/arrival/strategic lever drops (REST, THROW, door-diagonal-kite, heal×2, readiness-gate) + the ADVISORY-PUSH NULL (Δ −0.0011, marginal value/consult ≈0 — the first live-LLM-in-loop test on real NetHack; mechanism verified, LLM cited pushed rules verbatim, but no mean effect). The clean pair that defines the boundary: **intuition is NECESSARY where the bottleneck is JUDGMENT** (composition-world ablation, 4/4) and **adds NOTHING where the bottleneck is CAPABILITY** (advisory-push null). LLM-in-the-loop advising a competent code agent on the strategic layer of a capability-bound task is inert. The only qualitatively-different remaining mean-lever = DEMONSTRATION LEARNING (ttyrec expert corpus → inject the missing capability). Method note found en route: cross-seed state leakage in multi-seed processes → run paired blocks one-seed-per-process.

## THE RESOURCE REFRAME + DEMONSTRATION ARBITER [EMERGING — s9]
The 0-for-7 drops were all DECISION/positioning/advice levers; the observed death mass is dominated by RESOURCE failures (hunger ~145 = #1 killer, trash-attrition ~287) that we had barely touched. So "capability-bound" ≠ "no lever" — we were pulling the wrong KIND of lever. The demonstration corpus (NH-E35c, s9) is the honest arbiter of which resource levers experts actually use. **First arbiter result — the expert hunger law: across 4 alt.org games / ~35k turns, no expert EVER dropped below the "Hungry" tier** (0 frames at Weak/Fainting). Our own play: **62.1% of episodes reach Hungry, 35.0% Weak, 26.5% Fainting** (n=741 trajectories); more episodes PEAK at Fainting than Weak → once past Hungry we blow straight through the WEAK-eat guard to the faint cascade. Demonstration thus endorses **eat-at-Hungry** (one tier earlier than our WEAK trigger) → the ANTI-FAINT GUARD (rule [ANTI_FAINT], flag NH_ANTIFAINT): shipped flag-OFF, high-SNR proxy KPI = Fainting-incidence 26.5%→(expert 0%). This was the first capability-injection lever aimed by demonstration rather than intuition — the test of whether demonstration learning is a viable mean-mover where advisory-push was inert.

**s10 VERDICT — the anti-faint guard is NULL on fainting-incidence, and the mechanism reveals WHY: even a demonstration-aimed lever is capability-bound.** Pre-registered paired block (n=7 hunger-enriched fast-fainting seeds, REF=C2.1 vs REF+NH_ANTIFAINT, one-seed-per-process, cap 2000): **Fainting-incidence REF 0.571 (4/7) → TEST 0.571 (4/7), DELTA +0.000, 95% paired-bootstrap CI [0,0]** (zero discordant pairs). The guard FIRES as designed (29 fires across 4/7 TEST episodes) but PREVENTS 0 faints. Mechanism: on 2 of 4 REF-faint seeds it fired **0 times** despite reaching Hungry — **no food available to bank** (roles carry none; no fresh corpse in reach); where it did fire (Wizards, 1-4 fires) the agent still fainted (insufficient food); the food-carriers that fired heavily (Samurai 6, Wizard 18) never fainted in EITHER arm. Experts obey "never below Hungry" because they have ACQUIRED food; our hunger-prone roles reach Hungry with an empty larder, so eat-at-Hungry is a no-op. **The binding constraint is food ACQUISITION, not eat-timing.** So: demonstration correctly AIMED the lever (which the 7 intuition levers never managed — a genuine value of demonstration), but the aimed lever is ITSELF capability-bound → this is an **8th converging angle on capability-boundedness, now at the resource layer**, and it redirects Tier-1 from eat-timing to the food-ACQUISITION levers (aggressive safe-corpse eating / food pickup + hunting / gold→food). Honest read on demonstration as a mean-mover: its clearest, repeatedly-confirmed value is telling us WHERE to aim cheaply and unambiguously; it has not yet MOVED the mean, because where it aims (resource management) the deeper bottleneck is the missing acquisition capability, not the missing decision. Independent corroboration from the s10 DOOM-MOMENT LOOP: 100% of 196 corpus fainting deaths pass through Hungry with a median ~1399-step warning window — foreseeable slow deaths that rediscover the eat-at-Hungry law from our own corpus, confirming the lever is aimed right and the failure is capability (no food to act on), not timing. NH_ANTIFAINT stays default-OFF: a correct, bit-identical scaffold that becomes live only once food-acquisition lands.

## THE FOOD-ACQUISITION LEVER [SOLID after config-reconciliation — s11: a progression-safe hunger-death win, but NOT a mean-mover]
The s10 null ("it's food ACQUISITION not eat-timing") pointed the fix: build active food-securing (NH_FOODACQ) so the anti-faint guard has something to eat. Built as opportunistic safe-corpse BANKING — eat a safe fresh corpse we already stand on (typically after a kill), gated on not-Satiated + no adjacent hostile. (Food PICKUP was already live under NH_FOOD2 in the REF — verified against the item-value perceptor FOOD_NAMES table — so it is not the treatment; corpse-banking is.)

**The reconciliation (this is the whole finding — the raw numbers are CONFIG-CONFOUNDED).** Three configs bracket a hard tension:
- **Aggressive (routing + no rate-limit, ~5258 fires/block):** hunger-death 6/15→1/15 — but CONFOUNDED: mean descent depth REF 5.20 → TEST 4.00 (**−1.2 depth**), and on dev/regression seeds depth collapses 15→1 (Archeologist), 9→1 (Valkyrie). The agent avoids fainting by FARMING corpses in place instead of descending. The "win" is the agent not playing the game. Not shippable, not real capability.
- **Over-conservative (cooldown=25, ~119 fires):** progression-safe but hunger effect null — fainting-incidence 6/15→5/15, 95% CI [−0.27,+0.13] includes 0.
- **Reconciled (cooldown=8, moderate banking, 146 fires total / median 8 per ep):** the config that threads the needle. n=15 hunger-prone seeds, cap-2000, one-seed-per-process, REF vs REF+NH_FOODACQ: **death-while-fainting (hunger-death proxy) 5/15 → 0/15 (Δ −0.333)**; **fainting-incidence 6/15 → 2/15 (Δ −0.267, 95% paired-bootstrap CI [−0.533, +0.000], 5 improved / 1 regressed, McNemar p=0.22)**; **progression-NEUTRAL (mean depth REF 5.20 → TEST 5.47, +0.27; 4 seeds deeper, 3 shallower)**; **zero new death classes** (all TEST deaths are ordinary combat — arrow/gnome/coyote/gas-spore/wand; SAFE_CORPSES + cannibal guards held; no over-eat choke, no unsafe-corpse poisoning).

**Corrects the earlier draft's "effect scales with fires."** It does NOT: cd8 removes the same hunger death-class (5→0) with 36× FEWER fires than the aggressive config. The heavy firing was the STALL artifact, not the win mechanism — moderate banking is both sufficient for the hunger effect and necessary to preserve descent.

**Honest verdict — a real sub-win, but capability-boundedness still holds at the mean.** NH_FOODACQ (cd=8) is the FIRST progression-safe lever to remove a death CLASS at the #1 killer (hunger-death 5/15→0/15). But (a) the fainting-incidence CI just touches 0 at n=15 (directional, McNemar p=0.22 — needs n≈30 to reach 95%), and (b) crucially it does NOT move the overall progression/ascension mean: it CONVERTS hunger-deaths into combat-deaths at the same depth (mean depth unchanged). Removing hunger unmasks COMBAT as the next binding constraint. So this is the 9th converging angle refined: the resource layer had a genuine, aimable, progression-safe lever (unlike the 8 decision-levers), and injecting acquisition capability works AT THE HUNGER CLASS — but the mean stays capability-bound because a deeper capability (combat survival) now binds. Validates the resource-reframe pipeline end-to-end: demonstration aimed it (eat-at-Hungry) → anti-faint null refined it (bottleneck = acquisition) → doom-moment corroborated (foreseeable 1399-step window) → food-acquisition delivers at the hunger class, safely. Capability came from ACQUIRING what the agent needed; the mean did not move because the next wall is combat. NH_FOODACQ ships flag-OFF (bit-identical when off, verified) as a validated scaffold pending the n≈30 confirmatory + combat-lever pairing.

## THE PET-UTILIZATION LEVER [EMERGING — s12: the first combat-survival resource lever; DIRECTIONAL-but-NULL, mechanism confirmed]
s11 unmasked COMBAT (trash-melee ~287, the biggest death class) as the constraint binding once hunger is fixed, so s12 built the highest-value untried combat-side resource lever: PET UTILIZATION, in its cleanest zero-risk form — **preserve-the-pet-on-descent** (NH_PET): before taking the down-stairs, wait a bounded number of turns (cap 8/stair, radius-gated to 5) for the starting pet to reach an adjacent cell so it follows down (a pet descends only if adjacent when '>' is taken), keeping it alive across the descent to tank/kill trash on the D2-6 kill-zone. Tested ON TOP of the s11 hunger fix (both arms carry NH_FOODACQ+NH_ANTIFAINT) so this is combat isolated from hunger.

**Result (n=17 paired trash-melee-death seeds, cap 2000, one-seed-per-process; REF=C2.1+FOODACQ+ANTIFAINT vs TEST=+NH_PET; results/pet_block.jsonl):** combat-death rate REF 15/17 (0.882) → TEST 14/17 (0.824), Δ −0.059 (1 improved / 0 regressed — 1 discordant pair, directional only); **progression mean REF 0.0283 → TEST 0.0314, Δ +0.00305, 95% paired-bootstrap CI [−0.00157, +0.00998] — includes 0, NULL on the mean**; depth mean +0.18 (CI [−0.53,+0.94], includes 0); zero new death classes; flag-off bit-identical.

**Why it's null (the mechanism, which is the finding).** (1) Pets follow NATIVELY when adjacent — NetHack's own rule — so the lever's counterfactual is NARROW: it only acts when the pet is 2-5 cells away at the stairs (petw=0 on 9/17 = pet already adjacent, followed for free in both arms). (2) Where it DID fire (8/17 seeds, preserving the pet deeper on 6/17 — seed 16 Cavewoman depth 3→8, seed 706 Priest 3→5) the agent still combat-died at the reached depth, because the pet loses the same attrition the agent loses and dies to the same trash. (3) The wait itself REGRESSES some seeds (746 Healer depth 5→2) — the identical banking-rate-vs-progression knob tension as FOODACQ (config-sensitivity, s11 method note). Gains and losses net to a wash.

**Verdict — a 10th converging angle on capability-boundedness, now at the COMBAT layer.** Preserving a pet (a resource) is inert on combat survival because the binding constraint is not the pet's PRESENCE (native follow handles that) but the agent+pet COMBAT CAPABILITY against the trash. Peeling s11's hunger layer exposed combat; peeling combat's "pet-present" sub-layer exposes combat CAPABILITY (win-the-fight-faster / take-fewer-hits) as the true binding constraint — the mean did not move, it unmasked yet another constraint one layer deeper (the stacked-death-classes law, s11, continuing). The next combat levers to test are the CAPABILITY side, not the presence side: WIELD UPGRADE (zero wield actions ever) and SAFE EARLY LEVELING (arrive at the D5-6 kill-zone at xp 5+). NH_PET ships flag-OFF (bit-identical) as a validated scaffold; its remaining untried headroom is the combat-POSITIONING form (position so the pet tanks, don't outrun it in travel) — a larger, pet-AI-coupled, high-regression build deferred to s13+.

## THE WIELD LEVER + ACQUISITION-BOUND META-FINDING [SOLID — s13: the 11th angle resolves the resource/capability-injection path]
s12's PET null pointed from the presence side to the CAPABILITY side of combat, naming WIELD UPGRADE (zero wield actions ever) as the cleanest direct combat-capability injection and the decisive test of whether ANY resource/capability lever moves the mean. It does not — and the WAY it fails is the finding.

**WIELD is a mechanical null (11th angle).** NH_WIELD (wield the best carried weapon when it beats current melee dpt by >=0.5, safe, non-Monk, non-thrown) on the s12 trash-melee corpus (n=17 paired, cap 2000, one-seed-per-process, REF=C2.1+FOODACQ+ANTIFAINT vs TEST=+NH_WIELD): **progression mean 2.8305 -> 2.8305, Δ +0.0000, 95% CI [0,0], 17/17 bit-identical, wield-fires=0.** The counterfactual is PROVABLY EMPTY: a broad probe (77 role-episodes, all 15 roles) found ZERO in-inventory wield-upgrades — NetHack roles start weapon-optimal (Knight long sword, Barbarian two-handed sword, Wizard quarterstaff, Healer scalpel, ...; Monk/Tourist best unarmed, carry only throwing darts). This refines capability-boundedness: injection can only inject capability that EXISTS and is UNUSED. The program's one CI-positive lever (teach the Wizard to cast, +2.41) worked because casting was unused; wielding has no unused capability, so it is inert — and gifting a weapon is forbidden by the honest-observation contract. The mechanism is nonetheless correct (fires on a synthetic scalpel+long-sword inventory, dpt 1.25->2.81); the 0-fire is a WORLD property.

**The zero-fire diagnosis -> the mean is ACQUISITION-BOUND (the meta-finding).** A read-only floor-weapon diagnostic (NH_WIELD_DIAG: price every WEAPON_CLASS glyph on the floor vs current wield) distinguishes (a) acquisition-bound / (b) threshold / (c) already-optimal. Result over 13 seeds: NOT (b) — upgrades where they exist are far above margin. (c) already-optimal-or-junk in 8/13 (well-armed roles: no floor weapon, or floor weapon WORSE than the start — orcish/elven daggers 1.45-1.80 < starting). **(a) ACQUISITION-BOUND in 3-5/13, demonstrated: a genuine upgrade lies on the floor, in view for many steps, and the agent never takes it — seed 746 Healer walked past a MACE (scalpel 1.15 -> 2.59, +1.44) for 25 steps; seed 4054 Ranger past a FLAIL (1.44 -> 2.93) for 100 steps; seed 721 Knight past a two-handed sword (3.04 -> 4.39).** Root cause: the loot perceptor (`item_targets`) values only food/ammo/armor — **floor weapons are invisible to the agent's pickup policy.** The agent has the mechanism to USE the weapon (wield) but no behavior to ACQUIRE it — the EXACT parallel to the s10 anti-faint null ("reaches Hungry with an empty larder, no food to eat"). So BOTH the #1 killer (hunger) and the newly-unmasked binding constraint (combat) are gated by the SAME missing behavior: **acquisition.** The agent doesn't LOOT.

**The pivot confirms the meta-finding AND its cost.** NH_WIELDACQ (detour <=8 to a floor weapon that upgrades melee, pick it up, then wield) tested on seed 746: the acquisition FIRES (11 walk-toward-mace steps) but the pickup never completes (the terrain model marks the mace cell as a wall -> the item-on-perceived-wall cell is unwalkable-into) AND the detour STALLS descent (DEATH@D5 -> RUNNER_TRUNCATED@2000, zero descent — the identical banking-rate-vs-progression trade-off as FOODACQ, S11-2). So adding loot behavior is not a free mean-mover: it recurses into perception edges + the descent-stall confound. **Honest resolution of the resource/capability-injection path: it has NO clean mean-mover.** WIELD (in-inventory) is a mechanical zero; ACQUISITION (the behavior that would let capability be injected) is the true missing piece but re-hits the progression trade-off when built. The mean is not merely capability-bound but ACQUISITION-bound — and the value of this program is the FINDINGS (this characterized law), not a NetHack number. The next honest levers are a GENERAL progression-safe item-acquisition policy (underfoot-first looting on the FOODACQ cd=8 discipline, with a descent-depth regression gate) and SAFE EARLY LEVELING (XP/skill = the other unused capability), with DEMONSTRATION LEARNING as the last qualitatively-different mean-lever if those also come back null.

## THE PER-CLASS EXPERT OPENING (NH-E37) [EMERGING — the 12th angle: DEMONSTRATION learning, executed, fires-live, null-to-negative on the mean]
DEMONSTRATION LEARNING — flagged in the 11th angle as "the last qualitatively-different mean-lever" — was executed. We mined WHAT EXPERTS ACTUALLY DO in the early game (D1-6, where we die) from 6 public alt.org expert ttyrecs spanning 5 classes (Wizard/Samurai/Caveman/Priest/Knight, strong→fragile), via a message-line + status extractor (e37_extract.py, reuses the e35 emulator; DEMONSTRATION provenance, OFFLINE+disclosed). **The decisive finding is structural: the per-class expert early-game routine, decomposed, is ENTIRELY a subset of levers the program has ALREADY built** — opportunistic safe-corpse eating before Hungry (NH_FOODACQ+NH_ANTIFAINT; no expert ever dropped below Hungry, Priest ate 13× in-window), heavy pet-tanking (NH_PET; 20-103 interactions/game every class), proactive ranged softening (NH_RANGED; 14-68 throws/game — experts throw *before* contact where our THROW is crisis-only), Elbereth panic-break (NH_ELBERETH; ~5×/game), early prayer (NH_PRAYFIX), cast economy (NH_CAST), class-tuned dive tempo (NH_PACE — Samurai D5@T859 fast vs Wizard D5@T1505 cautious). There is **no un-built "secret opener."** Also an independent DEMONSTRATION confirmation of the s13 WIELD null: 0 in-inventory wield-upgrades across the corpus (every expert weapon-optimal from turn 1). The experts' edge is a PREVENTIVE buffer (never ENTER the 0-survivor crisis band — corroborates the E36 bootstrapping-unwinnable reframe: reliability = not entering, not out-fighting), built from behaviors we already have.

So E37 tested the one un-tested COMPOSITION: per-class SUBSET stacking (each rolled class gets ONLY its experts' small lever-subset, class-tuned — NH_OPENING, a bit-identical harness-level composer over the frozen C2.1 baseline; agent code untouched, verified git-clean). This is distinct from "test each lever globally" (done, null) and "stack everything" (done, negative). Result, WIZARD first tranche (n=5 role-stratified paired, cap 2000, one-seed-per-process): **progression Δ −0.008, depth_max Δ −1.0, survival@D5 Δ −0.20 (100%→80%), crisis-entry Δ 0, min_hpfrac Δ +0.018** (a tiny preventive HP buffer). Critically, **behavioral divergence 5/5 pairs** (cast 0→5-14 every seed, corpse-bank active) — the card FIRES LIVE and changes behavior massively, so this is NOT the E36 mechanical-null / signature-fidelity trap; it fires and STILL doesn't move the mean, and the heavier stack (NH_PACE-defer + cast-risk) REGRESSES depth on 2/5 seeds (860 D7→D3, 847 D6→D5), helps 0/5. This reproduces the NH-E13 Healer wiki-playbook result (−0.62) and the stacked-arm-negative law: **class-tailoring did NOT rescue the stack.** (Samurai, lighter card with no pace-defer/cast, first-tranche in progress — the only candidate for mean-neutral-with-a-buffer; a genuine per-seed win on seed 801 D2→D4 via foodacq firing; confirmatory n≥15 pending, box-saturation-deferred, see HANDOFF.)

**The honest read (the operator's "RELIABLE" ask, answered):** even human-optimal, demonstration-derived, class-tailored early play does not reliably move our mean — it fires, changes behavior, buys a little survival-time/HP buffer, but does not deepen progression, and multi-lever stacks regress depth. The gap to experts is not a missing OPENING ROUTINE (we have every piece) but the CAPABILITY to execute those pieces well under the benchmark's action-space/budget — the 12th converging angle on capability/acquisition-boundedness, now closing the DEMONSTRATION-learning path the 11th angle named. Demonstration's repeatedly-confirmed value remains AIMING (it told us exactly which behaviors matter, cheaply and unambiguously, and confirmed the WIELD null on foreign data); it has still not MOVED the mean, because where it aims the deeper bottleneck is execution-capability, not the decision. NH_OPENING ships flag-OFF (bit-identical, agent untouched) as a validated scaffold + the per-class playbook (E37_PLAYBOOK.md).

## THE CONSUMABLE ECONOMY (NH-E38) [EMERGING — the 13th angle: win-items acquired + identified + USED, mean still null -> EXECUTION-bound]
The largest untouched capability frontier — potions/scrolls/wands, the game's
actual game-changers — was built behind NH_CONSUME (default-OFF, bit-identical):
low-risk engrave-ID (NetHack 3.6.7 src/engrave.c table, disclosed) + zap a KNOWN
offensive/control wand at a spike-threat (the coordinator's #1: the mechanistic
counter to the unfleeable one-exchange death) + quaff KNOWN heal + gain-level/
enchant when safe + bounded-detour floor-consumable acquisition. Plus leveling-
wall instrumentation (xp/hp_max/ac/str-at-death). **Leveling wall, quantified
(1183 trajectories):** death peaks SHALLOW (depth_max median 5), hpmax median 22,
XP-at-end median 2, and 45% of episodes end with >30% HP -> SPIKE deaths (one
exchange), NOT attrition. The only counter to an unfleeable spike is ending the
fight in ONE action -> the offensive-wand branch.

**Pilot (n=8 paired dev seeds, cap 3000, TEST-only vs reused deterministic REF):
progression Δ +0.0038, 95% CI [-0.0149,+0.0209] — NULL.** The FIRED-SPLIT is the
finding: on the 4 seeds where the ID/use machinery FIRED, Δ **-0.0123** CI
[-0.0369,+0.000] (null-to-negative); the apparent positive aggregate is entirely
acquisition-DETOUR route-perturbation on NON-fired seeds (the s13 loot confound —
leave-one-out collapses it, drop16->-0.0030). **MONEY DATUM (seed 4):** the agent
engrave-IDENTIFIED a wand, ZAPPED it 3x and KILLED 2 monsters — the win-item was
acquired, identified, and used effectively in combat — yet reached the SAME max
depth (D8) as REF and died anyway (Δ=0), to a self-reflected "bolt of lightning"
(a NEW death class — offensive-wand zap in corridor geometry self-harms). Quaff-
heal (3x, seed 104) inert — "a heal can't outrun a spike." So consumables were IN
HAND early, acquired + identified + used + killing monsters, and using them STILL
did not move the mean — per the pre-registered discriminating prediction, the
strongest evidence yet that the wall is EXECUTION, not bootstrapping/acquisition.
The 13th converging angle. Honest caveats: pilot n=8 (4 fired, 1 real zap-seed);
the USE layer under-fires because acquired potions/scrolls stay UNIDENTIFIED
(engrave-ID is wands-only; read-identify/price-ID not yet acted on) — a fuller ID
game would raise the fire rate, but seed 4 shows a fully-identified, used, monster-
killing wand already fails to convert, so more fires deepen the execution-wall
evidence rather than overturn it. NH_CONSUME ships flag-OFF (bit-identical) as a
validated scaffold + the leveling-wall instrumentation; a zap reflection/line-of-
fire guard is required before any use-deployment (DOCTRINE_CARDS_E38.md, HANDOFF_E38.md).

## THE DIVE-RUSH METRIC-EXPLOIT (NH-E40) [SOLID — the 14th angle: the FIRST mean-MOVER, and it moves the mean DOWN; the metric-shape tail-seeking prediction put to a paired test and REFUTED]
All 13 prior levers were COMBAT/CAPABILITY/RESOURCE and nulled on the mean. E40
tests the OPPOSITE lever class — PACING/AVOIDANCE — the strategy the Metric-shape
finding predicted (progression rewards MAX DEPTH not survival ⇒ optimal policy is
TAIL-SEEKING: buy cheap depth lottery tickets). NH_DIVERUSH (default-OFF, bit-
identical, snapshot GREEN 21/21) biases the decision cascade HARD toward
descend/find-stairs and AWAY from combat/loot/explore/rest: route to a known
downstairs AROUND monsters and descend (skip the fight/loot/rest dawdles), explore
toward FINDING stairs when unknown, fight ONLY when a hostile blocks the sole
route; the P3 emergency-survival guards (crisis-flee/pray, hunger-crisis eat) stay
above it — speed-over-safety, not suicide. The hypothesis: rush PAST the D3-6 kill-
zone to reach D7-8 before dying, scoring higher than a careful death at D5.

**Result (n=18 paired dev seeds 101-118, cap 2000, one-seed-per-process, REF=C2.1
vs TEST=+NH_DIVERUSH; results/e40_diverush.jsonl):** progression mean REF 0.0644 →
TEST 0.0270, **Δ −0.0374, 95% paired-bootstrap CI [−0.0737, −0.0086] — EXCLUDES 0,
a ROBUST NEGATIVE** (3 TEST-better / 8 worse / 7 tie). depth_max REF 5.78 → TEST
3.94 (**Δ −1.83**); TEST reached DEEPER on only 2/18, equal 9, SHALLOWER 7 — never
robustly deeper, the whole hypothesis inverted. Leave-one-out is sign-stable (every
drop keeps Δ ∈ [−0.040, −0.024]); dropping the single biggest loser (seed 110,
Archeologist REF D15→TEST D7) still leaves Δ −0.024. Death-rate ≈ unchanged (REF
14/18 → TEST 15/18). Fired-split: the lever is LIVE (dive-rush drove behavior on
16/18 seeds, changed steps/level on 7/18) — not a mechanical/signature null; it
FIRES, descends, and STILL loses.

**The mechanism (the finding).** (1) **Avoiding combat ≠ avoiding damage** — same-
speed/faster monsters land free hits as the agent slips past toward the stairs (the
exact s4 REST-failure mode: you can't outrun what matches your speed), so
under-leveled dive-rushers die to the FIRST kill-zone monster EARLIER and SHALLOWER
(seed 101 Priest D9→D3, killed by a large kobold it tried to route around). (2)
**Steps/level went UP, not down** (Δ +60.3): on the seeds that reach deep, REF is
ALREADY the fast descender (Archeologists 102/108/110 reach D10/D11/D15 at ~9
steps/level by FIGHTING THROUGH the kill-zone in seconds), and forcing "descent-
first" on them made them die shallow after MORE wandering (110: 9.3→171 steps/lvl).
This **paired-experimentally PROVES the correlational fast-descender signal (fast<150
steps/lvl mean prog 7.36 vs slow 2.82) was REVERSE CAUSATION** — good runs descend
fast; making a run descend fast does not make it good, it inverts the outcome. (3)
You **cannot buy cheap depth lottery tickets because TRAVERSAL ITSELF requires the
combat capability dive-rush skips** — reaching D_{n+1} means surviving the monsters
of D_n, which is the same bind every prior lever hit.

**Verdict — the 14th converging angle on capability-boundedness, from the OPPOSITE
(pacing) lever class, and the strongest yet.** DIVE-RUSH is the program's FIRST
mean-MOVER (13 nulls, now a robust non-zero) — decisive precisely because it moves
the mean the WRONG way with a CI that excludes 0. The metric IS depth-shaped and
the tail-seeking analysis was correct in the abstract, but the paired test refutes
its policy corollary: **metric-aligned dive-rushing does not exploit the depth-
reward — the shallow kill-zone gets you regardless of pace, in fact EARLIER, because
the wall is survive-the-traversal CAPABILITY, not pacing.** Honest read on the
operator's "improve avg score" ask: the fastest way DOWN is not the deepest — the
deep runs are the ones that win the D3-6 fights, so the lever that would move the
mean is still combat/leveling capability (or demonstration of it), not speed. No
MILESTONE/GIF: no dive-rush run reached deep where baseline died shallow — the
reverse happened on every deep seed. NH_DIVERUSH ships flag-OFF (bit-identical) as a
validated scaffold + the paired block + analyzer (e40_block.py / e40_analyze.py).

## THE CORRIDOR-FUNNEL ANTI-PACK LEVER (NH-E41) [SOLID — the 15th angle: a mechanistically-sound anti-BURST lever that FIRES live (unlike E36) but nulls, because the multi-attacker-pack death mode it targets barely OCCURS under the current config]
E36's offline synthesis crowned CORRIDOR (funnel-and-fight) over the shipped KITE
lever in robust replay (survival 0.50 vs 0.28) but deployed as a MECHANICAL NULL:
its signature (adjacency AT low HP) never fired live (the signature-fidelity gap).
E41 re-attacks the SAME mechanism PROACTIVELY: NH_FUNNEL (default-OFF, bit-identical,
snapshot GREEN 21/21) fires ABOVE normal open-combat when a PACK (≥2 mobile hostiles
within radius 3) threatens and a 1-tile choke (corridor cell / doorway, from
nh_common Topology.chokes) is reachable within a few steps — retreat to the choke so
the pack QUEUES and only one attacks per turn (burst → single-attacker). The trigger
is BURST-scaled (funnel iff the pack's simultaneous-attacker dpt ≥ frac·HP), and for
the validation block it was calibrated MAX-FIRE (burst_frac 0.0, HP_HI off) to give
the mechanism every chance to fire — the E36 anti-null mandate. P3 emergency
pray/flee stay above it.

**Result (n=16 paired dev seeds 101-116, cap 2000, one-seed-per-process, REF=C2.1 vs
TEST=+NH_FUNNEL max-fire; results/e41_funnel.jsonl):** progression mean REF 0.0695 →
TEST 0.0641, **Δ −0.0054, 95% paired-bootstrap CI [−0.0234, +0.0065] — INCLUDES 0, a
NULL** (2 TEST-better / 2 worse / 12 tie). depth_max REF 6.06 → TEST 5.81 (Δ −0.25);
death-rate identical 13/16 both. **Signature-fidelity: it FIRES — 7/16 seeds, 18
total fires** (unlike E36's 0), so this is NOT a mechanical/signature null. But
leave-one-out shows the slight negative is ONE-SEED: dropping seed 108 (Archeologist
REF D11 → TEST D6, Δ −0.1258) FLIPS Δ positive — the +2.64/+7.36 on-fire mirage
lesson, caught by LOO. Fired-split (endogenous): {108 −0.126, 103 −0.003, 106/115/116
0.0, 111 +0.006, 112 +0.036} = mean −0.011, dominated by one catastrophe; non-fired
seeds Δ EXACTLY 0.0 (bit-identical when it doesn't fire, 4-way verified).

**Why a sound mechanism nulls (the finding — three quantified factors).** (1) **The
addressable scenario is RARE.** Facing a pack (≥2 non-pet hostiles within radius 3)
occurs on just **3.3% of snapshots (269/8232)**, and ≥2 ADJACENT is rarer still
(0–8 moments/episode). Under the current strong config (NH_LOS line-of-fire avoid +
NH_TOPO + corridor pathing + weakest-single-target combat) monsters are engaged
ONE AT A TIME — they approach single-file and the agent does not wade into groups.
The lethal spikes are **SINGLE strong/fast monsters** (giant spider, giant ant while
praying, large kobold), not multi-attacker packs — the E41 premise is contradicted
for this config. (2) **Even the one pack-heavy seed couldn't fire:** seed 113 (Wizard)
had 19.7% faced-2 (184/936) yet funnel_fires=0 — no choke reachable in time (the
"choke rarely reachable" factor). (3) **When it DOES fire it does NOT reduce
simultaneous attackers — it INCREASES them:** multi-attacker rate REF 0.0091 → TEST
0.0294 (Δ **+0.020**, wrong sign); seed 116 (Valkyrie) fired once and its
multi-attacker rate EXPLODED 4.7% → 30.4% — the retreat backed it into a dead-end
where the pack CONVERGED. Choke-retreat perturbs the trajectory into different
(sometimes worse) RNG deaths (108: D11→D6) rather than cleanly collapsing burst to
1-on-1.

**Verdict — the 15th converging angle on capability-boundedness, at the tactical-
positioning layer.** The classic choke-point-vs-pack doctrine is sound in vanilla
NetHack, and NH_FUNNEL fires live (beating E36's signature-fidelity gap), yet it is
INERT-to-slightly-harmful here for a structural reason the paired block + addressable-
rate instrumentation make precise: **the multi-attacker-BURST death mode barely
occurs under the current config (3.3% pack rate; single-file engagement already
prevents surrounds), so a lever that only helps in that state cannot move the mean —
and forcing choke retreats mostly perturbs trajectories, occasionally into worse
swarms.** Honest read on the "improve avg score" ask: we do not die to packs, we die
to the FIRST kill-zone monster an under-leveled character cannot out-trade — the same
survive-the-traversal CAPABILITY wall E40 hit from the pacing side. No MILESTONE/GIF:
no funnel-fight saved a run baseline lost (the reverse — 108, 116). NH_FUNNEL ships
flag-OFF (bit-identical, snapshot GREEN) as a validated scaffold + the paired block +
analyzer + firing diagnostic (e41_block.py / e41_analyze.py / diag_funnel.py).

## THE META-FINDING (both programs)
The synthesis-model + verified-code + planning recipe is twice-proven across two programs on 6+ environments. Its BOUNDARY is exactly where VERIFICATION stops: opaque procedural goals (ARC-3) and irreducible stochasticity/missing-capability (NetHack). That boundary is the research frontier — and the intuition layer + memory + goal-inference-bridge are the instruments aimed at it.

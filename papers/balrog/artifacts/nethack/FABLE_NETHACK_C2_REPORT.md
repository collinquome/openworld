# FABLE NETHACK — CAMPAIGN 2 (forensics-ranked levers, avoidability audit, midpoint checkpoint)

**Baseline (v1.1, PR #215):** n=80 untouched block (seeds 3000–3079), mean 6.09, 95% CI [4.46, 7.93].
**Leaderboard SOTA:** 6.8 ± 3.2 (Gemini-3-Pro; raw-HTML verified). **Original campaign goal:** frozen untouched block (n=80, seeds 4000–4079) with bootstrap CI **lower bound > 6.8**.
**Phase restructure (operator, mid-campaign):** the n=80 block on 4000–4079 is the **NH-C2.1 midpoint checkpoint** (levers-so-far), not the campaign verdict. It is followed by **Phase L** — an extended learning phase with no scored evaluations (situation gym, coverage matrix, deliberate play, risk-constrained planner, novelty protocol, verification suite, wiki-strategy arm) — and then **Phase E**, two pre-registered final arms (pure-code n=100 seeds 6000–6099; LLM-strategist n=25 seeds 7000–7024). Program structure, ledger and Phase-L exit criteria: `NETHACK_PROGRAM.md` + §Program below.

## ★ NH-C2.1 CHECKPOINT RESULT (frozen block, n=80, seeds 4000–4079)

**Mean 5.27, canonical bootstrap 95% CI [4.22, 6.43]. No beat: the CI excludes SOTA 6.8 from below (P(mean>6.8) = 0.005). Statistically indistinguishable from v1.1's 6.09 [4.46, 7.93] (overlapping CIs; cross-block comparison is seed-confounded — the 3000-block drew a Dlvl:21 Archeologist jackpot this block didn't; the paired-dev estimate of the config delta, +1.03 [−0.58, +2.68], remains the causal read). Plainly: the levers-so-far do not move the needle. The D5–6 capability problem is untouched, exactly as the avoidability audit predicted.**

| statistic | NH-C2.1 (this block) | v1.1 (3000-block) |
|---|---|---|
| mean [95% CI] | **5.27 [4.22, 6.43]** | 6.09 [4.46, 7.93] |
| depth ≥ 9 | 16/80 | 16/80 |
| zero-progression | **1/80** | 6/80 |
| starvation-class deaths | 14/80 | 14/80 |
| deepest | Dlvl:13 (25.66, Archeologist ×3 at 12–13) | Dlvl:21 (39.29) |
| churn/abort | 0 | 0 |

Per-role (top/bottom): Archeologist 14.45 (n=7), Monk 8.80 (n=7), Ranger 7.05 (n=3) … Samurai 2.24 (n=7), Wizard 2.09 (n=3), Healer 1.51 (n=3). **Variance decomposition: role lottery 45% / within-role 55%.** Death classes: TRASH 32, STARV 14, MELEE+ 14, SPIDER/ANT 8, RANGED 7, PRAY 5. Subgoal at death (new attribution channel): explore 30, survive 18, eat 10, find-stairs 8, rest 5, dig 4, loot 3, descend 2. Avoidability audit on the block itself: 8% of damage avoidable (KITE 320 of 495 avoidable points — pack-kiting remains the largest recoverable mass), 8/80 deaths with an avoidable final event; 60% of damage is model-endorsed dice. Regression harness: 0 detector fires in 80 episodes. Novelty/guard ledger: 214 entries logged for Phase-L triage.

What the checkpoint buys even without a score move: the floor lifted (1 zero-prog vs 6), the failure catalog shrank (no churn, no shop deaths, no petrification: dev seed 705's chickatrice death is gone under the frozen config — before/after animation pair committed), and every episode now carries subgoal attribution + plan logs + predicted-damage calibration for Phase L.

**Action-space usage audit (operator question, answered from all 552 logged episodes): the agent has ever used 50 of the 248 available actions. `cast`, `zap`, `quaff`, `read`, `fire`, `wield`, `puton`: zero uses, ever.** A Wizard has never cast Force Bolt at the giant ant killing it; a Healer has never cast a heal. Combined with E-NH1b (deaths are capability-bound, not decision-bound), the untouched action-space regions — in-combat spellcasting, wands, potions, wielding — are the concrete capability frontier Phase L's per-role strategy modules target.
**Protocol:** clean loop (reset/step + served obs only), offline source-derived world model disclosed, dev on dev-labeled seeds only (Campaign-2 dev range: 700–799 + extensions, disjoint from every prior block), ≥20-dev-episode validation per lever with drop-if-unclear discipline, code freeze + md5s before the scored block, per-episode JSON + full transition logs, source-leak audit section.

**Block-seed disclosure (pre-registered):** the operator-designated scored range 4000–4079 overlaps the 5 seeds 4000–4004 played once by the *v1 + memory-ledger* agent (condition B pass 1, different agent configuration). No Campaign-2 development touches these seeds and no per-seed information from that run informs any lever; disclosed rather than swapped because the range was fixed by directive before dev started.

## E-NH1 — Forensics (all 224 logged episodes, both arms; ceilings on the v1.1 n=80 block)

Corpus: 150 main-arm episodes (v1 baseline25 + robustness + run1 + cleanA + memory 3×5 + memory-paired 15 + v1.1 n=80) + 74 source-blind-arm episodes; 216/217 transition logs mined (one gz truncated by a killed worker; its episode-level record survives). Extraction: `nh_mine.py` → `results/c2_cache/`; analysis: `nh_forensics.py` → `results/c2_forensics.json`.

### Death-cause taxonomy (all arms pooled)

| class | n | note |
|---|---|---|
| MELEE_TRASH (difficulty ≤ 4 species) | 84 | jackal 16, goblin 9, newt 7, hobbit 6, giant bat 6, dogs/cats/ponies/rats… |
| STARVATION (incl. fainted-from-hunger kills) | 58 | mostly blind arm + v1; v1.1 reduced but not solved (14/80) |
| MELEE_OTHER (difficulty ≥ 5) | 34 | jaguar, guard, dingo, dwarf king, Elvenking… |
| SPIDER_ANT (spider/ant/bee class) | 19 | giant spider 8, giant ant 7 |
| RANGED (wand/bolt/missile/thrown) | 12 | includes 2 "killed by a wand" off-screen zaps |
| PRAY_DEATH (killed while praying, non-hunger) | 6 | trash mob finishing a low-HP prayer |
| ABORT / SLEEP / EXPLODE / TRAP | 11 | |

### v1.1 hazard structure (n=80 block — the Campaign-2 baseline agent)

- Hazard by depth h(d) = P(die with max depth d | reached d): 0.11 at D1, dips 0.06 at D2, then **0.15/0.12/0.30/0.31/0.21** across D3–D7 (the kill zone), 0.16–0.25 D8–D10, 0.60 at D12 (n=10 reaching).
- The D5–D6 spike is **MELEE_TRASH (7+7 deaths)**: xp1–3 characters, part health, killed by speed-15+ trash (pony 16, little dog 18, kitten 18, giant bat 22) that the flee gate correctly refuses to outrun.
- **57/66 combat deaths spent their final stretch below 50% max HP** — deaths are attritional, entered at part health, not ambushes. There is signal for an imminent-death recognizer.
- Deaths above own max depth (retreat deaths): 2/80 — max-depth ≈ death-depth, validating the hazard model's approximation.
- Starvation deaths (14/80) cluster at depth 1–5, turns 2k–9.7k: descent-stalled episodes that starve while exploring, not deep runs running dry.
- Per-role (n=80): Archeologist 16.52 (n=9, dig-dive), Valkyrie 9.49, Ranger 6.89, Monk 6.61 … Tourist 1.81, Priestess 1.50. Role lottery is the variance backbone.

### Counterfactual ceilings (censored competing-risk elimination; bootstrap CI on the delta)

Expected n=80 block mean if death-class X were eliminated (hazard h_X(d) subtracted, survivors re-walked down the empirical depth-score curve; conservative truncation at the observed frontier). Model baseline reproduces the actual mean (6.09).

| eliminate | ceiling | delta | boot 95% CI | deaths (n) |
|---|---|---|---|---|
| **MELEE_TRASH** | **10.97** | **+4.88** | [+2.84, +7.46] | 31 |
| MELEE_OTHER | 8.17 | +2.09 | [+0.71, +3.71] | 13 |
| SPIDER_ANT | 8.00 | +1.92 | [+0.60, +3.45] | 10 |
| STARVATION | 7.49 | +1.40 | [+0.68, +2.39] | 14 |
| PRAY_DEATH | 6.60 | +0.51 | [+0.10, +1.09] | 5 |
| RANGED | 6.49 | +0.40 | [+0.06, +0.93] | 4 |
| EXPLODE / SLEEP / TRAP | ≤6.20 | +0.11 ea | — | 1 ea |

**Reading:** the pre-campaign hypothesis ("starvation #1") described the pooled 275-episode corpus, not the current agent: v1.1's dominant recoverable loss is **winnable melee fights lost from part health against low-difficulty species** (ceiling +4.9), with deep-melee and spider/ant next. Combat capability (expectimax fight/flee/throw + armor + earlier disengagement), not food, is where the points are. Food economy remains worth +1.4.

### Lever ranking implied (build order)

1. **E-NH4 expectimax combat + death-recognizer veto** (attacks MELEE_TRASH +4.88, MELEE_OTHER +2.09, SPIDER_ANT +1.92)
2. **E-NH2d armor economy** (multiplies all melee classes: fewer incoming hits)
3. **E-NH2b ranged-first combat** (spider/ant class + softening packs before contact)
4. **E-NH2a food economy v2** (+1.40)
5. **E-NH2e/E-NH3 role-conditional pacing** (the xp1–3-at-depth-5–8 pattern says fragile roles dive past their HP curve; v1's "pace gate hurts" finding was measured on a dig-diver, not walkers)
6. **Prayer-under-threat discipline** (+0.51; 3/5 pray-deaths at depth 1–2 with a trash mob adjacent mid-prayer)
7. **E-NH2c LOS discipline** (+0.40)

Perceptor audit (E-NH2.5) and per-lever dev verdicts follow as they land.

## E-NH5 — Elbereth: reachable, but NOT a panic button (two-sided finding)

**Side 1 (interface, reverses v1's "engraving disabled"):** the engrave flow IS completable without the `-` key. The getobj prompt accepts a **weapon letter**, the getlin accepts typed letters (a–zA–Z are all actions), and `more` (= carriage return in NLE) submits it. Deterministic probe (dev seed 690): `engrave, a, E,l,b,e,r,e,t,h, more` → `look` reads back *"Elbereth"*. Every BALROG agent has this available.

**Side 2 (behavioral, from the ≥20-episode validation — the lever KILLED):** weapon engraving is *carving in the ground*, not fingertip dust-writing: it is a **multi-turn helpless occupation** (plus enchantment loss on the stylus). Wired as an emergency panic layer, it produced three dev deaths *mid-engraving* — "killed by a giant bat/giant rat/rothe, **while helpless**", each with the death screen literally frozen at `What do you want to engrave in the ground here? Elbereth` (seeds 703/705/711, combat-group v1). **Dropped from the emergency chain per the drop-if-it-doesn't-pay rule.** The v1 conclusion survives in amended form: without `-` (1-turn dust writing), Elbereth-as-panic remains effectively unreachable in BALROG's action space; scroll-of-scare-monster is also unusable (scroll appearances are shuffled and unidentified reads are -EV). The remaining niche — pre-emptive carving before a planned rest, several turns ahead of any threat — is left unexploited and documented.

## E-NH4 substrate — exchange model + verification gate (Jim-ports f/g/h)

- **Exchange model** (`nh_exchange.py` → `results/c2_exchange.json`): per-species per-adjacent-game-turn damage distributions + our kill rates, mined from 160,583 combat rows across 216 episode logs. Single-adjacent rows only for attribution; multi-turn actions spread over their game-time delta (disclosed approximation).
- **Distributional verification gate** (pre-registered α=0.01, even/odd-seed split): 23 species had ≥40 turns in both folds; **16 verified** (chi-square on binned damage histogram + binomial on kill rate), **7 failed** → their decision-layer dpt uses the conservative max-of-folds estimate. Small-n species shrink toward a difficulty regression prior (dpt ≈ 0.61 + 0.080·difficulty, fit over species with ≥30 turns).
- **Death-recognizer veto (h)**: rule "hp ≤ 3·Σdpt(adjacent)" validated on held-out odd-seed episodes: **precision 0.70, recall 0.19** for death-within-12-steps under the old always-fight policy. Wired as the expectimax emergency veto (fires → upstairs escape / last-resort prayer / Elbereth), where a false positive costs one defensive turn.
- **Select-don't-vote (g)**: one model per mechanic, selected by held-out verification; no averaging anywhere in the stack.

## E-NH2.5 — perceptors (`nh_percept.py`)

Audit: v1.1 perceived blstats + glyph classes + messages, but left **room structure, branch identity, line-of-fire, per-monster lethality, and item value** as raw glyphs. Death-classes tracing to perception gaps: secret-door stalls (topology), wand deaths (LOS), walked-past-a-pony deaths (threat field), floor armor never worn (item value: v1.1 AC trajectory shows armor essentially never upgraded after start).
Built: **Topology** (rooms/corridors/doors segmentation, room graph with exits, dead ends, choke cells = kite spots, room-perimeter secret-door hosts), **ThreatField** (per-cell dpt exposure + travel halos), **LOSField** (clear-ray cells from potentially-ranged monster classes), **ItemValue** (food > ammo > armor ranking via object-glyph → objclass). Goal-set enumeration: the policy now runs an explicit subgoal ledger (descend / dig / explore / fight / flee / hold-choke / kite-choke / ranged / loot / wear / eat / rest / grind / find-stairs / survive) with per-step reasons, planned A*-path logging, and EV annotations — feeding both forensics attribution and the planner-visible renderer (`render_c2.py`: belief mini-map + route overlay + threat tints + subgoal/EV panels).

## E-NH2 — Lever-group verdicts (n=20 paired dev seeds 700–719 vs frozen v1.1; ref-vs-ref control = exact 0.00 on all 20)

| lever group | flags | paired delta | 95% CI | pos/neg | class shifts (ref→test) | verdict |
|---|---|---|---|---|---|---|
| NAV (LOS + topology secret-search) | LOS, TOPO | **+2.25** | [−0.07, +5.29] | 8/5 | STARV 5→2 | **ship** |
| FOOD (economy v2 + prayer-under-threat fix) | FOOD2, PRAYFIX | **+1.12** | [−1.55, +4.10] | 8/4 | STARV 5→3 | **ship** |
| PACE (fragile-role descent gate) | PACE | +0.14 | [+0.00, +0.42] | 1/0 | ~inert (gate rarely binds) | ship (harmless) |
| COMBAT (expectimax + ranged + threat halo) | EXPMAX, RANGED, THREAT | −0.11 | [−2.35, +1.80] | 7/7 | STARV 5→2, deaths pushed deeper (TRASH→MELEE+) | revalidated below |
| ARMOR (pickup + wear) | ARMOR | (+0.85 but **0 wears** — mechanism inert, see bug #5) | — | — | — | revalidated below |

Bug #5 (found via the ledger's `wear`-fires=0): **an item under the agent is invisible in the served glyphs** (the @ covers it), so glyph-based on-cell pickup can never complete — the agent oscillated on/off armor cells. The `You see here …` message is the only on-cell item sensor; pickup switched to message-driven (mirroring the v1.1 floor-food path), with a shop-price guard ("for sale"/"zorkmids" ⇒ never grab). ARMOR and COMBAT(+ranged ammo economy) re-validated post-fix:

| revalidation | paired delta | 95% CI | mechanism |
|---|---|---|---|
| ARMOR (post-fix) | +0.67 | [−2.00, +4.25] | wear fired 7×/20 eps, no adverse signature → **ship** |
| COMBAT (post-fix) | −0.38 | [−2.42, +1.20] | ranged fired 30×; death mix better but score flat-negative twice independently (−0.11, −0.38) → **DROP** per the drop-rule |

### E-NH4 verdict (honest)

The expectimax combat layer is **built, distributionally grounded, and dropped**: two independent n=20 paired readouts came back mildly negative on score despite mechanically sensible interventions (fewer starvation deaths, deaths pushed deeper, 0.70-precision death-veto). The E-NH1 ceiling (+4.9 on trash melee) is real, but this implementation buys depth with time and XP in a way that nets ~zero; the frozen agent keeps v1.1's threshold combat. The exchange model itself ships (it powers PACE's prey selection), as does its verification-gate methodology. What survives of E-NH2b/c: nothing in the frozen loop (ranged-first and LOS-halo travel rode with the dropped groups — LOS ships via NAV's `NH_LOS` flag, halo does not).

### E-NH3 disposition

With the noise floor measured (single-seed flips of ±7–16 from any decision change), a rest-threshold × depth-gate grid at feasible n would select seed luck — the exact failure this program hit twice before. E-NH3 was bounded and then superseded: the checkpoint keeps v1.1's rest defaults; the risk knob returns in Phase L as E-NH4b's principled `P(death) < ε per level` constraint (one parameter unifying veto, rest gates, and descent pacing), swept on dev-side metrics.

## E-NH1b — AVOIDABILITY AUDIT ("was this damage avoidable?")

Offline counterfactual replay (`c2_avoid.py`): every damage event in a logged episode is re-examined on the agent's **own belief state at the decision step** (Atlas replayed from step 0 — exact, since ref-vs-ref replay is deterministic) against the alternative set {throw-first, kite-to-choke, rest-before-descend, non-LOS route, eat-earlier}. Movement counterfactuals are exact in the model; combat counterfactuals inherit the exchange model's distributional epistemics.

**v1.1 n=80 block (5,020 damage points, 80 deaths):**

| verdict | damage mass | share |
|---|---|---|
| AVOIDABLE | 270 | **5%** — KITE 122, THROW 93, EAT 45, LOS 10 |
| UNAVOIDABLE (dice in model-endorsed fights / no better option) | 2,975 | 59% |
| UNCERTAIN (losing-1v1-no-alternative, off-screen ranged, no-adjacency) | 1,775 | 35% |

Death-stretch (final damage event per death): 7/80 AVOIDABLE (THROW 3, KITE 2, EAT 2), 26 UNAVOIDABLE, 47 UNCERTAIN.

**The reconciliation the operator asked for — and the campaign's central finding:** E-NH1's counterfactual ceilings said eliminating trash-melee deaths is worth +4.9; E-NH1b says only ~5% of damage (and ~9% of deaths) were avoidable by any *in-model, in-interface* alternative at the decision point. Both are true: the death **classes** are worth a lot, but v1.1 already plays its own model near-optimally — the remaining deaths are dice in fights the model endorses, or states with no better local action. Closing the classes needs **capability the interface mostly denies** (1-turn Elbereth: blocked; real ranged kit: marginal ammo economy; AC: slow to accumulate), not better decisions over the same repertoire. This is exactly why the E-NH2/E-NH4 levers audited flat on score while visibly improving death *composition*. Unforced-error rate is the right dev metric going forward (dozens of events/episode vs one score) and is adopted as Phase L's primary signal; per-config audit: v1.1-dev 10% avoidable, settled 8% (KITE remains the largest avoidable mass in both).

## Harness audit (operator-requested, received mid-block)

Six defects acknowledged; the frozen block was already running on the declared md5s, so fixes are split by scope. **Analysis-side, applied immediately:** (5) `bootstrap_ci.py` is now the canonical CI module (exported `ci95()`, fixed seed 20260706) and `c2_block_analysis.py` imports it — the blind arm's independently-implemented bootstrap ([2.97,6.01] vs canonical [2.97,5.97] on identical data) is the motivating discrepancy; blind-report numbers will be recomputed on next touch. (4-backfill) the two v1 "(unparsed)" roles recovered from their transition logs via tty rank titles: seed 2015 = Healer ("Rhizotomist"), seed 2016 = Wizard ("Evoker"). **Harness-side, queued post-block as snapshot-suite fixtures** (none affect block validity: scoring is `env.get_stats()`, no worker kills during the block, `MAX_LOOP` cannot fire below the env's own 100k cap): (1) belief-snapshot bare-except → counted + noted, (2) transition-log periodic flush + `.complete` marker + tolerant reader, (3) explicit `RUNNER_TRUNCATED@steps` end-reason, (4) tty-rank-title role-parse fallback with parse-source recorded, (6) blstats-ground-truthed `depth_max` + belief-vs-blstats play-time assertion.

## Program structure (operator restructure: TRAIN-THEN-EVALUATE)

- **NH-C2.1 (this report's block): midpoint checkpoint.** Frozen levers-so-far on n=80 seeds 4000–4079. Reported below, then no further freeze-block iteration.
- **Phase L — extended learning (no scored evaluations).** The machinery, all queued with operator directives on file: E-NH4b risk-constrained sampling planner (death-probability path costs, determinized K-future sampling for pack fights, global `P(death)<ε per level` knob swept on dev); E-NH6 situation gym (harvest scenario library from all logs — every death/near-death/stall as `(seed, action-prefix, class)`; branch-explore alternatives in the real env on dev seeds; in-model Monte Carlo luck quantification: MISPLAYED / UNWINNABLE / MARGINAL; generalization gate: a mechanism ships only if it wins ≥3 instances of its class from different seeds); LLM-designed falsification matrices per mechanism (HP × terrain × pack × xp × hunger); hypothesis coverage matrix (rule-card × scenario-class, scoped confidence, untested cells = enumerated open hypotheses prioritized by death-mass × uncertainty); LLM deliberate-play on frontier scenarios (dev/gym only, transcripts codified into rules; no LLM calls in scored code); novelty protocol (detector shipped in the checkpoint as logging + touch-kill guard; caution-default contact gating in Phase L); goal-market info-gain term; world-model test suite (snapshot fixtures incl. every fixed bug: armor-under-@, corpse-on-victim-cell, shopkeeper-dpt, dwarven≠dwarf, pet-not-a-wall, stale-door; play-time possibility-set verification with per-episode violation rate, ported from the blind arm); permanent ledger regression harness (`c2_ledger_checks.py`, shipped — detectors D1–D5 formalizing today's bug taxonomy, already flagging one bounded loot-approach case).
- **Phase L exit criteria (pre-declared):** (i) coverage matrix ≥70% of death-mass-weighted cells resolved (verified or refuted); (ii) top-5 gym syllabus classes each solved-or-stamped-UNWINNABLE with ≥3-seed generalization; (iii) avoidable-damage rate plateaued (<1-point change) over 2 consecutive 40-episode dev blocks; (iv) snapshot suite green; (v) play-time violation rate < 1e-4 with no unexplained novelty entries.
- **Phase E — one confirmatory evaluation, pre-registered:** freeze (md5s), single n=100 untouched block, seeds 6000–6099. Primary criterion: mean + canonical 95% CI vs 6.8; decisive = CI-low > 6.8. No peeking, no unregistered extensions, no post-hoc seed exclusion. Disclosure now, at registration time: seeds 6000–6004 were played once by the v1+memory-ledger agent (condition B pass 3); no development touches them.

## Progress log (UTC)

- 2026-07-07 ~09:0x E-NH1 complete: 217 transition logs mined once into per-episode extracts (depth arrivals, hp-drop events with adjacency attribution, per-step combat log, prayers/eats/hunger/AC trajectories); taxonomy + hazard + ceilings above. v1.1 reference code snapshot md5-verified against the RUN_LOG freeze (`v11_ref/`).
- ~12:12 dev reference block launched: v1.1 frozen code, fresh dev seeds 700–739 (n=40) → **mean 4.27** (starvation-heavy draw; no Archeologist). This is the paired baseline for every lever verdict.
- ~12:3x Campaign-2 stack built behind default-off env flags (NH_EXPMAX / NH_RANGED / NH_ARMOR / NH_FOOD2 / NH_PRAYFIX / NH_LOS / NH_THREAT / NH_TOPO / NH_PACE / NH_ELBERETH). v1.1 behavior byte-preserved when flags off.
- ~13:0x Elbereth probe: reachable (section above). Exchange model + verification gate + death-recognizer holdout validation done.
- ~13:2x First full-stack dev pass surfaced a new failure mode: shop-item pickup → killed by shopkeeper (seed 716). Shop guard added (no pickups with a peaceful @ visible). Full-stack block running for the paired A/B.
- ~13:0x Full-stack pass 1 (pre-fix): delta −0.03 [−1.54, +1.42] vs ref — flat, with diagnosable bugs (below), not a clean lever readout.
- ~13:1x **Dev-forensics on the ledger caught four real defects:** (1) *flee-a-winnable-fight*: when melee was geometry-blocked (diagonal-through-door), the win branch fell through to flee — a Barbarian spent 1,300 steps fleeing a goblin it out-EV'd 10×; fixed to fall through to other layers (v1.1 semantics). (2) *peaceful-biased dpt*: shopkeeper/guard exchange stats mined from peaceful coexistence read dpt≈0 → EV treated them as free kills; dpt now floors at the difficulty prior for that class. (3) *Elbereth emergency kills* (E-NH5 above); dropped. (4) *object-glyph table silently empty* (`oc_class` is a char, `int()` threw inside try/except) → every item/armor/floor-food layer was inert in the first passes; fixed and all affected groups re-queued. The subgoal ledger + EV annotations found all four in minutes — the operator's legibility investment paying for itself.
- ~13:1x Role-conditioned kill-rate hypothesis **rejected by data** (fitted multiplier reversed under confounding — strong roles fight deeper monsters). Replaced with a source-arithmetic prior (monster HP ≈ 4.5·mlevel vs role-class damage/turn) blended with the pooled empirical rate (select-don't-vote).
- ~13:15 Clean lever-group isolation relaunched (n=20 paired each, sequential): COMBAT (expectimax+ranged+threat-halo), FOOD (food-v2+prayfix), ARMOR, NAV (LOS+topology-search), PACE.
- 14:56 **NH-C2.1 CODE FREEZE** (md5s in RUN_LOG): config `NH_FOOD2 NH_PRAYFIX NH_LOS NH_TOPO NH_GUARD` after NAVFOOD n=40 (+1.03) beat the 6-lever settled stack (+0.01). Block n=80 seeds 4000–4079 launched 14:56:31, complete ~15:30.
- 15:3x **Checkpoint result: 5.27 [4.22, 6.43]** — section above. Avoidability audit on the block: 8% avoidable (KITE-dominated). Regression harness clean. Animations rendered with the provenance-annotated planner view (belief map + route overlay + knowledge banners + model ticker).
- Post-block program registered per operator directives: Phase L (E-NH4b risk planner, E-NH6 gym + death-learning intake, NH-E11 strategist/navigator + dossier, NH-E12 retrospectives, NH-E13 wiki arm ×2 modes + mechanics-claims 3-way validation, NH-E14 per-role modules + spell/wand/potion repertoire, coverage matrix, verification suite, harness-audit fixes) → Phase E two final arms (pure-code n=100 @ 6000–6099; LLM-strategist n=25 @ 7000–7024). Full detail: `NETHACK_PROGRAM.md`.

## Source-leak audit (Campaign 2 delta)

No new env touchpoints. The scored loop remains `reset(seed)`/`step(action_string)`/`get_stats()` through the vendored BALROG stack; the agent consumes only served observations. New offline components and their provenance: `nh_percept.py` (topology/threat/LOS/item perceptors — pure functions over the belief state built from served glyphs; object-glyph→name tables from the NLE python API, offline, disclosed), `c2_exchange.json` (mined exclusively from our own logged served observations), `c2_avoid.py`/`nh_mine.py`/`nh_forensics.py` (offline log analysis; no env interaction), TOUCH_KILL/ELBERETH_IGNORES/PEACEFUL_BIASED constants (source-derived, disclosed, rule-carded). The Elbereth probes ran reset/step on dev seeds through the same served interface. No wiki content has been consumed yet (NH-E13 is registered but not started; when it runs, wiki provenance will be tagged per claim). Mechanical grep re-run: no `unwrapped`, no `.nethack`, no state cloning in any scored-loop module.

- ~13:5x Second ledger catch: item market thrashed on items parked under peaceful monsters (660 consecutive `loot: shuriken d1` targetings — path detour returns, goal refires, game time burns → starvation uptick + depth collapse in that pass). Near-target give-up counter added. All groups restarted once more; **ref-vs-ref control launched** (same seeds, same frozen v1.1 code, fresh process) to measure the same-seed chaos-divergence noise floor that the v1 report documented (disp-RNG) — the paired-delta CI is only meaningful relative to it.
- Decision framework pre-declared for lever verdicts under this noise: a lever ships only if (1) paired delta not clearly negative, (2) ledger-level mechanism evidence is sound (interventions fire where intended, no thrash signatures), (3) targeted death-class does not worsen. The settled full stack then gets its own n=40 paired validation before freeze.
- ~13:5x **Control result: ref-vs-ref (n=20, same seeds, same frozen v1.1 code, fresh process) is perfectly deterministic — all 20 paired deltas exactly 0.00.** The v1 disp-RNG divergence caveat does not manifest on this host/config. Consequence: every nonzero paired delta in the lever runs is *caused* by the lever's first divergent decision (then chaotically amplified) — paired deltas are causal but heavy-tailed; seed 700–719 contains one jackpot seed (716 = 16.13 in ref) whose flip dominates any group's mean.
- ~13:50 **Group verdicts (n=20 paired each):** FOOD (food-v2 + prayfix) **+1.12 [−1.55, +4.10]**, 8 pos / 4 neg, starvation 5→3 — mechanism sound, SHIPS. COMBAT v3 (expectimax + ranged + threat-halo, after fixes) **−0.11 [−2.35, +1.80]**, 7/7, death mix improved (starvation 5→2; deaths moved deeper: trash→MELEE+ conversion, e.g. 719 depth 4→9) — flat on score, mechanically positive; provisional ship pending settled-stack readout.

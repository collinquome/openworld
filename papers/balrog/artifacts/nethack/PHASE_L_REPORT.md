# FABLE NETHACK — PHASE L (extended learning campaign)

MODEL ROSTER (methods line, per the model-provenance standing rule): Phase L
session 1 design/synthesis/analysis = Fable 5 (max reasoning); registered
fallback if capped = claude-opus-4-8 (max thinking) — any handoff will be
logged here at its phase boundary. Workers/subagents where used: Sonnet 5
(tagged per artifact). PHASE BOUNDARY (logged per the provenance rule):
sessions 1-2 = Fable 5 (max reasoning); session 3+ = claude-opus-4-8
(max thinking) — forced handoff at Fable usage cap, 2026-07-07 evening.
CORRECTION at session-3 open: the cap reset before session 3 launched —
session 3 = Fable 5 (max reasoning). The opus fallback was NOT used;
the roster remains single-model (Fable 5) through session 3.

Predecessor state: NH-C2.1 checkpoint 5.27 [4.22, 6.43] vs SOTA 6.8 — no beat;
avoidability audit says deaths are CAPABILITY-bound (5–8% of damage
decision-avoidable); action audit says 50/248 actions ever used
(cast/zap/quaff/read/fire/wield/puton = 0). Phase L builds capability on dev
seeds only until the pre-declared exit criteria are met, then stops for Phase E.
Full context: FABLE_NETHACK_C2_REPORT.md; registry: docs/NETHACK_PROGRAM.md.

## Exit criteria (pre-declared in the C2 report §Program — restated, not weakened)

(i) coverage matrix ≥70% of death-mass-weighted cells resolved; (ii) top-5 gym
syllabus classes solved-or-UNWINNABLE with ≥3-seed generalization; (iii)
avoidable-damage rate plateaued (<1-point change) over 2 consecutive 40-episode
dev blocks; (iv) snapshot suite green; (v) play-time violation rate < 1e-4 with
no unexplained novelty entries.

## The four-layer architecture (operator naming, 2026-07-07 — structures this whole report)

PERCEPTION (perceptors: obs → typed structure) · MEMORY (dossiers, observation
store, cards, lessons) · INTUITION (the LLM: dot-connecting, curiosity
hypotheses, objective selection over the full context package — slow, rare,
expensive, irreplaceable) · PROCEDURE (code: navigation, combat, state machine,
verified rules — fast, constant, free, exact). Program claim in these terms:
perception+memory+procedure alone plateau (Arm A ceiling); adding intuition
breaks it (Arm B delta). Every mechanism below carries its layer tag.

## Priority order (operator, 2026-07-07, incl. late reweight)

1. PERCEPTORS + MEMORY (NH-E18 substrate + dot-connector; perceptor backlog:
   shop/altar/fountain/special-room, monster-state, item-appearance+prices,
   branch recognition) — expected biggest wins.
2. ACTION-SPACE FRONTIER (NH-E14: cast/zap/quaff/read/wield/fire), every verb
   branch-probed via NH-E16 component 2 before wiring into policy.
3. NH-E15 strategy state machine + stall watchdog.
4. NH-E13 wiki KB (FTS5 + manifest, add-only) feeding everything.
5. Background loop: gym (E-NH6) + NH-E12 retrospectives + coverage matrix +
   NH-E14b loot-ROI + E-NH4b risk planner.
NH-E16 (search-as-teacher) is the shared instrument under 2/3/5;
NH-E17 (clean-room rebuild) runs at exit — every card written to pass it.

## Dev-metric trend table (primary: avoidable-damage rate; updated per dev block)

| block | config | n | mean prog | avoidable dmg % | gym solve | matrix fill | violation rate | notes |
|---|---|---|---|---|---|---|---|---|
| C2 ref (700–739) | v1.1 frozen | 40 | 4.27 | 10% | — | — | — | predecessor baseline |
| C2 navfood (700–739) | NH-C2.1 frozen | 40 | 5.30 | 8% | — | — | — | predecessor freeze candidate |

## Workstream verdicts (running)

*(rows appended as they land; milestones flagged for the coordinator)*

## Running log (UTC)

- 2026-07-07 ~17:3x Phase L session 1 opened. NH-E16 + NH-E17 + NH-E18
  registered (operator directives), folders + ledger rows created. Priority
  reweight (perceptors+memory lead) recorded in program doc + here.
- ~17:4x E18 refinement registered: hypothesis-driven exploration objectives
  (revaluation trigger → curiosity objectives; "LLM decides WHERE, procedures
  decide HOW"; curiosity hit rate metric; CURIOSITY GIF banners).
- ~17:5x Registered in one batch as directives arrived: CONTEXT_SPEC v0.1
  (strategist context package: full world map + memories + story-so-far +
  current state, versioned + logged verbatim per consultation); four-layer
  architecture naming (PERCEPTION/MEMORY/INTUITION/PROCEDURE); NH-E19
  principles distillation + algorithm catalog/meta-selection (+ ablation
  experiment); NH-E20 MiniHack scenario lab (des-file micro-scenarios,
  transfer gate, priority: spellcast doctrine + D5-6 melee); model-provenance
  standing rule (MODEL field stamped on all new artifacts).

## Harness-audit fixes (items 1–4, 6) — SHIPPED (gate for all Phase-L dev blocks)

All five queued defects fixed + smoke-verified on dev seed 801 (determinism
preserved: identical progression across pre/post runs of the same seed):
(1) belief-snapshot exceptions counted + first-occurrence noted
(`belief_snap_errors`; step-0 empty-atlas case excluded by design — the
counter's first outing caught exactly that and nothing else);
(2) transition logs flush every 100 steps + `.complete` sidecar marker +
tolerant reader (truncated tails yield every complete step);
(3) `RUNNER_TRUNCATED@steps` end-reason whenever OUR loop, not the env,
ends the episode;
(4) role-parse fallback via status-line rank titles (`RANK_TO_ROLE`, 137
titles, source role.c, offline+disclosed) with `role_source` recorded;
(6) `depth_max_blstats` ground truth + same-obs belief-vs-blstats assert
(`belief_depth_mismatch`; 0 on smoke).

## NH-E16 instrument + first probe battery (SHIPPED)

`nh_branch.py`: (seed, action-prefix) snapshot/replay/branch executor on the
verified-deterministic env stack (session gate: verify_determinism() —
green, sig-identical replay at step 300). Probe records in
results/e16_probes/. Forbidden-seed guard hard-blocks all scored ranges.

**Verb-grammar battery (Wizard dev seed 940, 7 probes, all saved):**
cast → menu(with Fail% column) → letter(Pw deducted here) → direction;
zap/quaff/read/wield/puton grammar mapped (getobj bracket lists candidate
letters — a served percept); `more` dismisses the cast menu at ZERO cost;
`esc` EXISTS in the action space (v1's engraving note said '-' missing —
correct — but esc is available for menu bails). fire without quiver
degrades to a throw prompt.

**DANGER CARD from probe (RAY_BOUNCE):** zapping the starting wand of
lightning at an adjacent wall BOUNCED the ray back and killed the caster
on turn 1 (hp 11→0, tombstone; probe record
zap_lightning_bounce_DEATH.json). Rule: never zap a ray wand without a
clear line ≥2 cells; wall-adjacent ray zaps are suicide. This is the
branch-probe instrument doing exactly its job — that lesson cost zero
mainline deaths.

**Paired-branch cast-vs-melee (same snapshot, seed 940 step 6, grid bug
adjacent):** cast = 1-turn kill, 0 damage, 5 Pw; melee = 3 consecutive
misses, −3 HP, target alive. First search-as-teacher paired verdict.

## NH-E14 CAST_ATTACK_V1 (layer: PROCEDURE) — BUILT, dev block RUNNING

NH_CAST flag (default off, v1.1-preserving; flag-off regression: seed-801
progression byte-identical). Mechanism: per-episode menu discovery (parse
letter/level/category/fail%), attack-spell selection gated on fail% ≤ 20 and
Pw ≥ 5·level; targets = adjacent hostiles (never-melee species PREFERRED —
spells bypass touch/passive effects) else straight-line fast/never-melee
threats ≤6 cells with clear ray path. Live smoke (seed 940): 5 casts, 5
one-shot kills incl. a two-rat line pierce. Rule card CAST_ATTACK_V1 in
nh_agent.py with probe+KB provenance.

**CAST-1 paired dev block pre-registered + launched** (RUN_LOG 
md5s): ref=frozen NH-C2.1 config vs test=+NH_CAST; seeds = 12 Wizards
(839 845 847 850 860 912 918 940 957 980 982 990, from the 800–999 role
census — new artifact results/role_census.json) + 8 non-caster guards
(801–822 subset, expected exact-0 delta). Wizard block is primary
(role-targeted lever); drop-if-unclear applies.

## NH-E18 memory substrate (layer: MEMORY) — SHIPPED (v0.1)

`nh_store.py`: per-episode observation store — events timeline, item
sightings w/ appearances + prices (RE-parsed from served messages), monster
encounter ledger (seen/killed/hit_us/passive_adj — the didn't-attack ⇒
peaceful-class evidence), per-level feature dossier (altar/fountain/throne/
sink/grave/stairs from belief terrain), STORY-SO-FAR narrative, and
`ctx_package()` — the CONTEXT_SPEC/v0.1 renderer (full multi-level ASCII
world map + memories + story + current state; 9.5KB on a depth-10 dev
episode). Wired into the agent as a pure logger (NH_STORE default-on, no
decision reads); serialized into trajectories as traj["store"]. Smoke:
green mold passive_adj=2/hit_us=0 vs jackal hit_us=2 — the peaceful/passive
separation is already visible in data.
Niggle logged: possible stair-coord coincidences across level dossiers —
verify before the dossier feeds routing.

## NH-E15 stall watchdog v1 (layer: PROCEDURE) — BUILT (flag NH_E15)

Windowed progress metrics (new tiles + depth + xp over WD_WINDOW=150 game
turns); healing-rest exempted (deliberate rest is progress). Escalation:
L1 perturb (drop explore target → different frontier), L2 disengage
(WD_DISENGAGE=80 env steps: standoff combat skipped, descent/exploration
take over; P3 emergencies unaffected). All fires ledgered (wd_fires +
notes + subgoal). Unit-verified fire→escalate→disengage; flag-off
regression byte-exact (seed 801 progression identical). Rule card
STALL_WATCHDOG_V1 in nh_agent.py. Rides the next 40-ep dev block for
fire-rate + no-regression evidence; the giant-bat fixture becomes a gym
regression scenario when the E6 harvest lands. Full E15 state-machine
formalization (explicit DIVE/EXPLORE/... states + carded transition table)
remains open — v1 delivers the watchdog component.

## NH-E13 wiki KB — BUILT (Mode A batch, 15 pages)

wiki_kb.sqlite (FTS5, 944KB) + sha256 manifest, built via MediaWiki API by a
Sonnet subagent (spec: Fable 5); 15 pages incl. Standard strategy, Spellbook
of force bolt, Wizard/Healer, Wand/Potion/Scroll/Ring, Price identification,
Shopkeeper. Add-only + idempotent (verified re-run: 0 fetches). Sanity
queries rank correctly. Committed in NH-E13-wiki-strategy/.

**kb_prices.json (MEMORY-layer reference, provenance: wiki rev-tagged):**
base-cost tables parsed from KB wikitext — 28 potions / 18 scrolls / 25
wands / 28 rings by price point, PLUS the wand ray/beam/non-directional type
table (ray = {digging, magic missile, cold, fire, lightning, sleep, death})
— the exact table the RAY_BOUNCE safety gate needs before NH_ZAP ships.
This is the price-ID cross-reference the E18 dot-connector consumes.

## NH-E12 backfill — DONE (163 combat deaths retro'd)

Subagent backfill (spec + review: Fable 5) over the full cache corpus:
**by class** MELEE_TRASH 88 / MELEE_OTHER 35 / SPIDER_ANT 21 / RANGED 10 /
PRAY_DEATH 9; **by lesson type** ARRIVAL_CONSTRAINT 96 / NEEDS_REVIEW 52 /
NO_LESSON_DICE 10 / TACTICAL_RULE 5 (avoidability verdicts only exist for
the 63 v11block40 deaths — TACTICAL/DICE counts bounded by that subset).
**59% of combat deaths carry an under-leveled-arrival deficit (xp < depth/2)
— the strongest quantitative support yet for the operator's preparation
thesis (P1/P4); per-role: Archeologist 100%, Priest 82%, Ranger 75%, Healer
69% ... Priestess 29%.** 44.2% of deaths spent the final stretch below half
HP. Artifacts: NH-E12-death-retro/results/{e12_retros,e12_summary}.json.
Trajectory-avoidability counterfactual (operator's moment-vs-trajectory gap)
remains open — the readiness numbers above are its motivation.

## ★ CAST-1 PAIRED VERDICT (milestone — flag for coordinator)

n=20 paired (12 Wizard + 8 non-caster guards), ref = frozen NH-C2.1 config:
- **Guard block: all 8 non-casters EXACT 0.00** — the lever is perfectly
  role-scoped (first divergent decision only ever happens for casters).
- **Wizard block: ref 3.12 → test 4.39 (paired +1.27/seed, 8+/3−/1=0;
  best +7.65 seed 982 D4→D9, +4.54 seed 918 D3→D8).** Overall n=20 delta
  +0.76 [−0.07, +1.80].
- **Ledger caught an adverse class shift: shopkeeper deaths 0(ref) → 3
  (test)** — directional casts SKIP the "Really attack?" confirm that
  protects melee, so the line-cast's fast-mover gate (shopkeeper speed 18)
  angered shopkeepers. Blocks shipping per the no-worse-death-class rule.
- Fix: CAST_NEVER_PEACEFUL_CLASS static guard (rule card, verified-by-death
  evidence, both target branches). **CAST-2 revalidation running** (12
  Wizard seeds paired vs same ref; criteria pre-registered: shop deaths
  → 0, Wizard delta not clearly negative).
Wizard headroom context: Wizard block mean was 2.09–2.77 in every prior
scored block; a +1.27 role-targeted lift on the worst role is exactly the
capability-frontier thesis paying out — pending CAST-2 confirmation.

## NH-E21b engine — DELIVERED (Sonnet build, Fable 5 spec + review)

engine/ in the E21b folder: mechanic grammar (triggers × effects ×
conditions, bindings sampled per seed, magnitudes discoverable only by
experience), 6 templates of escalating composition depth, knowledge log,
no-intuition baseline, ablation harness, 9/9 tests green (determinism;
reference solver 120/120 template×seed solves; baseline STRUCTURALLY fails
the counterintuitive worlds). Baseline ablation (10 seeds): T1
lettuce-door 0%, T5 sacrifice-info 0%, T6 double-override 0% vs T2/T3/T4
100% — the pre-registered design signature exactly: systematic exploration
solves explore-worlds; only override-capable intuition can solve
damage-as-key. LLM arms (a)/(c)/(d) stubs ready.

## NH_REPEAT — repeated-layout stair predictor (BUILT; awaiting paired block)

World-model discovery (E18 reflection R1 → corpus scan): the vendored NLE
seeded generator repeats level layouts — 19/96 consecutive-level pairs in
CAST-1 share >60% identical explored rows, many pixel-identical (seed 809
D6=D7=D8). Disclosed as an eval-substrate fact (same for all BALROG
agents). Lever: NH_REPEAT — ≥85% terrain match over ≥60 comparable cells
⇒ predict down-stairs at the previous level's stair cell, bias exploration
there (hint-only; normal give-up applies). Smoke on seed 990: 3 detections,
all correctly predicting (63,4). Rule card REPEAT_LAYOUT_STAIRS. Paired
dev block queued behind CAST-2.

## Phase-L status vs exit criteria (end of session 1, 2026-07-07)

(i) coverage matrix ≥70% death-mass-weighted: **NOT STARTED as a formal
grid** — capability map built (0/34 cells resolved; verb grammars pinned
count toward the cast column's evidence base); matrix scheduler (E23 UCB)
registered. (ii) top-5 gym classes solved/UNWINNABLE: **gym harvest not
yet run**; instrument (nh_branch) + retro corpus (163 deaths typed) ready;
bat-standoff fixture pending harvest. (iii) avoidable-damage plateau over
2 consecutive 40-ep dev blocks: **cadence not started** (session ran
targeted 20-seed lever blocks; first full 40-ep block with c2_avoid due
session 2). (iv) snapshot suite green: **suite not yet assembled** (probe
records + E21b tests exist; NetHack-side fixtures pending). (v) violation
rate <1e-4: **play-time possibility-set checker not yet ported** from the
blind arm.

Honest summary: session 1 built the INSTRUMENTS (branch executor, store,
KB, engine, watchdog, catalogs) and landed the first capability lever
(CAST) + a world-model discovery (layout repeats); the exit-criteria
MEASUREMENT loops (matrix fill, gym syllabus, avoidability cadence, suite,
violation tracking) are session 2+'s backbone. No criterion is met yet;
none is blocked.

## ★★ CAST-2 VERDICT: SHIPPED (milestone — email-worthy)

CAST_ATTACK_V1.1 revalidation, 12 Wizard seeds paired vs frozen ref:
**ref 3.11 → test 5.53, paired delta +2.41, CI95 [+0.75, +4.41], 9+/2−/1=0.
CI-low > 0 — the first lever in this program's history to clear zero on a
paired CI.** Shopkeeper deaths 3 → 0 (the CAST_NEVER guard didn't just
stop the bleeding: seed 957 flipped −3.09 → +4.92 (D9), seed 918 +10.14
(D3 → D10)). Death mix moved deeper across the block. All pre-registered
CAST-2 criteria met ⇒ NH_CAST ships into the Phase-L config for casting
roles. Scope note: effect is role-conditional (Wizards ≈ 1.5/20 of random
roles; naive block-level contribution ≈ +0.2 — role-coverage expansion
(Priest/Monk attack spells, Healer at Xp2+) is the multiplier to chase).

## REPEAT-1 VERDICT: INERT (honest negative)

n=20 paired vs cast1ref: ALL deltas EXACT 0.00. Detections fire (5/5 early
episodes logged REPEAT hits with correct stair predictions) but zero
action divergence — the explore layer discards the injected explore_target
(same fires≠effect signature as C2's ARMOR bug #5; the paired-exact-zero
read is what caught it). NH_REPEAT stays default-off; rework (inject the
predicted cell as a first-class goal-market goal, not a target hint) queued
for session 2. The world-model discovery (layout repeats) stands
regardless.

## FIRSTS ledger (operator novelty-awards directive) — code partly SHIPPED

store.first(): first kill per species / first verb use / first depth,
logged as award events into story (GIF banner material) + serialized
(store["firsts"]). Smoke (seed 940): ['depth:1','verb:cast','kill:grid
bug',...]. Goal-pursuit bonus (bounded premium inside ε-ruin) registered
for session 2.

## c22 highlight GIFs rendered (coordinator email request)

results/animations/: c22_cast2__seed918_wizard_dlvl10.gif (25 force-bolt
kills, D3ref→D10, +10.14), c22_ref_contrast__seed918_meleeonly_dlvl3.gif,
c22_first_forcebolt__seed839.gif (kill at range, step 6),
c22_cast1block__seed822_barb_dlvl14.gif (29.25 block-best).

## Session 2 open (2026-07-07, MODEL: Fable 5 max reasoning — same roster, no handoff)

- DEV-B1 pre-registered + LAUNCHED at open: first 40-ep measurement-cadence
  block, STANDING CONFIG = frozen(FOOD2,PRAYFIX,LOS,TOPO,GUARD)+NH_CAST,
  seeds 700–739 (trend-table comparable). Primary read: c2_avoid
  avoidable-damage rate (exit criterion iii, block 1/2). NH_E15 deliberately
  OFF — the cadence block is the clean shipping config; it doubles as the
  paired REF for both the E15 watchdog validation and the CAST-HUNGER fix.
- Directive burst registered (ledger rows + folders/specs): **NH-E25**
  open-mode play (Cleese: unstructured-play discovery yield vs structured
  control, both directions pre-registered; second-solution rule in gym;
  pondering passes), **NH-E26** policy-function evolution (FunSearch: LLM
  mutations over single hot functions, E20 lab fitness, islands, drop-rule
  still gates shipping), **AUX-CONSTRUCT** strategist move-class
  (AlphaGeometry: at impasse, ADD an element — change the problem, don't
  search harder; + synthetic-curriculum lesson onto E21b), **RENEWABLE**
  renewable-source ledger (sources as dossier entries; VERIFIED loops as the
  prize — a verified food loop = cast freely; NH mapping: rest-spot quality
  rating = cheap immediate win vs the 57/66 attrition class; features are
  gamble tables — KB pages + safe-subset validation first), **CAST-HUNGER**
  cast-nutrition economics (operator saw "too hungry to cast" in the c22
  GIFs — the reel's human-observer→hypothesis loop paying out; P7 added:
  EVERY NEW CAPABILITY IMPORTS NEW COSTS).
- WATCH ITEM (coordinator relay): claim that the ARC-3 sibling program hit
  25/25 public games source-blind — UNVERIFIED against the public repo
  (whose log still shows the goal-inference wall). No action unless
  artifacts surface; if they do, cross-study their method vs our blind arm
  immediately.

## Dev-metric trend table update (session 2)

| block | config | n | mean prog | avoidable dmg % | violation rate | notes |
|---|---|---|---|---|---|---|
| DEV-B1 (700–739) | frozen+NH_CAST (standing) | 40 | 5.32 | **6%** | **0.00e0 (0/119,057)** | criterion-iii block 1/2; paired vs navfood ref: 39/40 EXACT 0.00, the single divergence = the block's one Wizard (+0.01 [+0.00,+0.04] overall) — session-1 code churn verified behavior-preserving |

Avoidable-damage trend: 10% (v1.1) → 8% (settled/navfood) → **6% (DEV-B1)**.
Plateau read needs DEV-B2 within 1 point (session 3, same config unless a
lever ships paired-green first — then the new standing config restarts the
2-block clock).

## Criterion v instrument SHIPPED: c2_violations.py (play-time possibility-set checker)

Ported from the blind arm's world_model predict/verify pair; runs OFFLINE
over any transitions dir (every dev/gym block gets a violation read free).
Rules V_TIME / V_MOVE / V_NONMOVE_POS / V_DEPTH / V_HP_BOUND / V_XP_MONO.
First outing on DEV-B1 found rate 2.44e-4, ALL EXPLAINED: (1) confusion/
stun random-walk movement (V_MOVE cluster inside a centipede fight), (2)
level-teleport trap depth jump 7→3, (3) god-punishment xp loss on prayer
(also seen on cast2 ep940). Each became a SCOPE on its rule (condition-mask
gating for conf/stun; teleport/drain/god-voice message signatures) — the
checker's first day did exactly what the criterion intends: it found three
world-model scope gaps and they are now modeled. Post-scoping: **0/119,057
— criterion (v) PASSES on DEV-B1.**

## E-NH6 GYM HARVEST — scenario library LIVE (criterion ii start)

e6_harvest.py over the full corpus: **794 death scenarios, 794 branchable**
(transitions on disk ⇒ (seed,prefix) branch-explorable via nh_branch), 55
retro-matched to E12 lessons. **Top-5 syllabus (death mass):** TRASH 313
(118 distinct seeds) / MELEE+ 161 / STARV 160 / SPIDANT 80 / RANGED 43.
PRAY 37 next. Every class has ≥14 distinct seeds — the ≥3-seed
generalization gate has abundant material. Solve-or-UNWINNABLE work begins
session 3 with TRASH (the 39% mass class).

## COVERAGE MATRIX formalized (criterion i baseline)

coverage_matrix.py: 16 rule-cards/mechanisms × 6 death classes,
death-mass-weighted by the live syllabus; N/A cells excluded, PROVISIONAL
counts half. **Baseline weighted fill: 16.4%** (VERIFIED: CAST_NEVER,
TOUCH_KILL, FOOD2×STARV, PRAYFIX×PRAY). **28 open hypotheses
auto-enumerated, top by mass: KITE_TO_CHOKE×TRASH, REST_GATES×TRASH,
FLEE_GATE×TRASH, WIELD×TRASH, ARMOR×TRASH (0.394 each)** — the TRASH
column is where criterion i will be won, and wield/armor doctrine (P2/P3)
plus kite formalization are its levers. Artifact:
results/coverage_matrix.json (renders the audit surface).

## CAST-HUNGER retro (operator GIF observation) — LESSON CARD + fix BUILT

Retro over the cast blocks: **4/12 Wizard seeds hit "too hungry to cast"
(839/912/940/980); 2 of the 4 died of hunger** (839 starved, 980 fainted →
iguana). Worse: the cast layer RETRIED the refused cast every step — seed
839 logged **2,759 refusals = 24% of its episode** burned on a no-op loop
while starving. Doctrine CAST_HUNGER_V1 (flag NH_CASTHUNGER, default off):
(a) refusal message latches cast-blocked until fed to NotHungry (kills the
retry loop, melee/throw doctrine takes the fight); (b) casters eat at
HUNGRY tier, not Weak (the failure arrives mid-fight, when the bolt was
the plan). Rule card provenance: OPERATOR-OBSERVED (GIF reel — the
human-observer→hypothesis loop working as designed). P7 added to
PRINCIPLES.md: EVERY NEW CAPABILITY IMPORTS NEW COSTS. Flag-off
regression: seed 801 old-vs-new code result-identical (7346 steps,
bit-identical progression). CASTHUNGER-1 paired block RUNNING (12 Wizard
seeds vs cast2 ref; criteria pre-registered in RUN_LOG).

## NH_REPEAT V2 — fires≠effect FIXED, paired block RUNNING

Root cause found in code: _explore only honors explore_target if it is
already a frontier cell; a cross-map stair prediction never is, so V1's
hint was discarded every time (exact-0 ×20). V2 routes to the frontier
cell NEAREST the predicted stair cell as a first-class goal (150-step
per-level budget, refutation event if the cell explores to non-stairs).
Smoke (seed 990): 2 routing engagements with real action divergence +
budget-exhaust fallbacks logged. REPEAT-2 paired block RUNNING (same 20
seeds vs cast1ref; criteria pre-registered).

## ★★ NH-E21b LIVE INTUITION ARM — first live results (milestone — flag for coordinator)

live_arm.py shipped (replay-based interactive protocol on the
deterministic engine — nh_branch pattern; the live intuition layer for
these runs IS Fable 5 max; every consultation logged VERBATIM in the state
files, results/e21b_live/).

- **T1 lettuce-door seed 0: WIN, 27 steps, 6 consultations, 2/2 mechanics**
  — the canonical damage-as-key world the scripted baseline fails 0/10
  structurally. Chain logged: probe gate at full HP → observe refusal →
  eat mottled fruit (−68) → gate yields at hp 32 → win. The override
  (deliberate self-harm under a bounded, justified read) is exactly the
  NH-E19 defeasibility protocol in action.
- **T6 double-override seed 0: WIN, 30 steps, 8 consultations** — via a
  solution class the DESIGNER didn't script: the charm trap was defeated
  by NEVER PICKING IT UP ("the cheapest counter to a possession trap is
  non-possession"), so mechanics read 3/4 on the win line. A second
  branch (probe, 4 consultations) then pinned mechanic 4 and demonstrated
  the DESIGNED line end-to-end: charm heals in room B (+15/+5), G2
  refuses the carrier, drop → pass (give-up-a-proven-good-item, the
  second-solution rule honored).
- **Engine integrity bug found live and FIXED: obs inventory leaked
  item_class ("hazard_fruit") — ground-truth mechanic labels served to
  the agent.** Caught in T1 consult 4, disclosed in that run's log,
  fixed (display_name only), tests 9/9 green. T6 ran post-fix.
- Baseline contrast stands: T1/T5/T6 = 0% scripted vs live-intuition
  2/2 wins on first attempts. T5 + multi-seed statistics + the four-arm
  ablation (incl. (d) no-override) are session 3's E21b block.

## CASTHUNGER-1 VERDICT: eat-early component DROPPED (honest negative, fast)

Full read (12 Wizard seeds vs cast2 ref): **-1.10 [-2.94, +0.06], 1+/4−.**
The eat-early-at-Hungry component fired on EVERY caster run (vs the rare
refusal event it was meant to prevent), diverted mid-run trajectories
(s918 -9.91, D10→D5), and — the real lesson — BURNED RATIONS EARLIER
against a fixed stock, so Weak-tier eating found an empty inventory:
"while fainted" deaths appeared (s912, s940-class). **Resource-TIMING
lesson: eating earlier is not more food.** V1b demoted to lab sub-flag
NH_CASTHUNGER_EAT; the refusal LATCH (V1a — kills the 2759-step retry
loop) retests alone as CASTHUNGER-2 (4 affected seeds; others are
structurally exact-0). This pairs with P7: the fix for an imported cost
must itself be costed.

## REPEAT-2 VERDICT: mechanism FIXED, effect UNCLEAR → stays default-off

n=20 paired vs cast1ref: **+0.39 [-0.23, +1.28], 12/20 divergent
(V1: 0/20), 6+/6−, best +7.71 (s818 D7→D10).** Routing engaged in 19/20
episodes (layout repeats are ubiquitous at these depths). V2 did exactly
what the rework intended — real action divergence via first-class goal
routing — but the score effect does not clear the drop bar. Per the drop
rule NH_REPEAT stays default-off; the world-model discovery stands, and
the lever remains a candidate for a bigger block or for integration into
the goal market proper (where stair-prediction competes with loot/xp
goals instead of preempting them).

## NH-E18 reflection pass #2 (devb1 s711) — R4–R6 proposed

Verbatim consultation in NH-E18-connecting-dots/results/e18_reflection_711.md:
R4 firsts-stream imbalance (depth-awards outrunning kill-awards in the
first 400 turns) as a cheap arrival-constraint predictor — validate over
the 794-scenario library; R5 passive-species evidence (acid blob
passive_adj=4/hit_us=0) accumulates but is unconsumed — and counterattack
damage is INVISIBLE to the store (add passive_counter when the
monster-state perceptor lands); R6 the episode's lone novelty event
(plains centaur, diff 6, xp1, D8, step 554) sits adjacent to the death —
P6 + readiness ratio are its exact missing procedures. Instrument note:
items_seen empty on a D8 run ⇒ floor-item sighting RE under-fires outside
shops (filed for the item-appearance perceptor).

## Registered this session (late batch): SHEET + HISTORY

CHARACTER SHEET self-model + counterfactual power (operator; spec
NH-E14-role-modules/CHARACTER_SHEET_SPEC.md — power index, readiness
ratio makes P1 computable, item deltas upgrade the value perceptor;
BUILD = top of session-3 queue). HISTORY BROWSER shipped
(history_render.py): per-episode HISTORY.md + KNOWLEDGE_INDEX.md
(committed examples: cast2 s918, devb1 s711).


## Session 2 close (forced wrap at Fable usage cap)

In flight at close: CASTHUNGER-2 (2/4 done: 839 + 912 both EXACT ref —
latch kills the retry loop without behavior cost; 940/980 finishing;
verdict lands in nethack_results_casthunger2_wa.json) and E15-1 paired
overnight rider (40 eps vs DEV-B1 ref). Ledger harness on DEV-B1: one D1
fire (loot-approach x50, seed 704 Knight) — known bounded class.
HANDOFF_3.md carries the full state. Model handoff logged above.


## Session 3 open (2026-07-07 evening, MODEL: Fable 5 max reasoning — cap reset, no model handoff; roster correction logged in the header)

### In-flight verdicts collected (all three finished writing after session-2 wrap)

**CASTHUNGER-2 SHIPPED (pure guard).** All 4 affected Wizard seeds
ref-EXACT (+0.00 CI [+0.00,+0.00]: 839 2.91 / 912 5.08 / 940 1.85 /
980 3.54). Retry loops GONE: 'too hungry to cast' events test-vs-ref
1/3169 (s839 — the 24%-of-episode loop), 1/115, 2/268, 1/465; the
residual 1-2 events are the latch triggers themselves. Hunger-death
class unchanged (the latch stops the loop, it does not mint food —
RENEWABLE stays the structural fix). Violations 0/17,319. NH_CASTHUNGER
(V1a latch-only) joins the standing config for casters; V1b eat-early
stays dropped (lab sub-flag NH_CASTHUNGER_EAT).

**E15-1 SHIPPED (robustness lever, on its own pre-registered gate).**
40 seeds 700-739 vs DEV-B1: +0.13 [-0.44,+0.70]; watchdog fired in
22/40 episodes (L1 perturb / L2 disengage, all noted in trajectories);
15/40 action-divergent, 6/40 score-divergent (best +7.35 s700 D4→D9;
worst -7.71 s710). Death classes: HUNGER DEATHS HALVED 10→5 — s700/702/
704/727/728 all escaped stall-starve loops (s704 starved → rotted-corpse
poisoning: lateral move within the food-crisis class, no novel class).
All 3 pre-registered criteria pass (fire-rate>0, delta not clearly
negative, no death-class worsening). Violations 0/81,125. HONEST CAVEAT:
as a progression lever the effect is UNCLEAR by drop-rule standards (CI
spans 0), and the mechanism is partially inert — 7/22 fired-episodes are
byte-identical to ref (s715: 37 fires, s733: 61 fires, zero divergence;
L2 disengage is a no-op without adjacent standoff combat and the L1
perturb goal can resolve back to the incumbent explore target — the
REPEAT-1 inertness class again; rework = goal-market integration).
Shipped because its pre-registered criteria define the gate; DEV-B2
validates it inside the standing config and a regression there reverts it.

**REPEAT-2 (verdict landed 18:22 session 2, collected unchanged):**
+0.39 [-0.23,+1.28], 12/20 divergent (V1: 0/20), routing fired 19/20,
best +7.71 s818 — mechanism FIXED, effect UNCLEAR ⇒ NH_REPEAT stays
default-off per the drop rule; goal-market integration is the revisit
path (same rework as the E15 inertness caveat — one integration serves
both).

**STANDING CONFIG after session-3 open:** NH_FOOD2, NH_PRAYFIX, NH_LOS,
NH_TOPO, NH_GUARD, NH_CAST + NH_CASTHUNGER + NH_E15. Two levers shipped
⇒ the criterion-iii 2-block clock RESTARTS: DEV-B2 = block 1/2 of the
new config.

### Session 3 mid: two exit criteria closed + the self-model shipped

**CRITERION (iii) MET.** DEV-B2 (700-739; 39 eps adopted bit-identical
from e15b1 by the registered structural-identity argument + s715 fresh
under the full config — the latch removed s715's hunger death: died
fighting a goblin at the same progression instead of fainting behind
579 cast refusals) → avoidable damage **5%**, mean 5.45. DEV-B3
(740-779, FRESH seeds, same config) → avoidable damage **5%**, mean
5.51, hunger deaths 3/40. Plateau |5−5| = 0 < 1 point over two
consecutive 40-episode blocks. Trend across configs: 10→8→6→5→5.

**CRITERION (iv) MET.** snapshot_suite.py green 18/18 (Sonnet 5 worker,
Fable 5 spec): the six fixed bugs each pinned by a fixture exercising
the REAL code path (armor-under-@ driven through a live agent with
recorded messages injected; shopkeeper-dpt floor proven load-bearing by
a simulated-regression flip; corpse-on-victim-cell + phantom purge;
dwarven≠dwarf; pet-not-a-wall BFS swap; stale-door correction) + E16
probe records as integrity + replay fixtures behind the
verify_determinism gate.

**CRITERION (v) holding:** 0 violations across all four session-3
blocks (233,458 transitions cumulative).

**CHARACTER SHEET BUILT (nh_sheet.py, operator top-of-queue).**
PI = best_dpt × hp; TI(d) = band_dpt × band_hp from damage-mass-weighted
per-depth threat bands (the v0 exposure weighting was rejected when it
diluted D5's p75 to 0.007 dpt — coexistence turns are not threat);
RR = PI/TI = exact exchange semantics (their turns-to-kill-us over our
turns-to-kill-them). Weapon (75) + armor (66) tables parsed from the
frozen KB with sha256 provenance; force bolt 2d12 / d20<AC+10 from the
KB page. counterfactual_power() renders wield decisions as power-delta
arithmetic (Valkyrie D3 example: two-handed sword = +6.98 RR). Live
probe on dev 805 (served-obs path): Ranger sheet correctly ranks
crossbow+bolt over wielded dagger. Next: readiness logging wire-in
(flag-off regression first), WIELD/ARMOR doctrine on the deltas,
RR-threshold sweep.

**E6 SOLVE LOOP LIVE (e6_solve.py).** Exact logged-action replay to
branch points (death−40/−120/−300), ORIG control must reproduce the
death, v1 alternatives REST/RETREAT, MISPLAYED iff an alternative
survives death+600 turns; UNRESOLVED deliberately ≠ UNWINNABLE (that
stamp waits for the v2 menu + in-model MC). First TRASH batch (≤20
distinct dev seeds) running; smoke: jackal-death MISPLAYED via REST,
poison-corpse death correctly unsolvable by repositioning.

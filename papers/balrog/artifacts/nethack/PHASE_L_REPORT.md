# FABLE NETHACK — PHASE L (extended learning campaign)

MODEL ROSTER (methods line, per the model-provenance standing rule): Phase L
session 1 design/synthesis/analysis = Fable 5 (max reasoning); registered
fallback if capped = claude-opus-4-8 (max thinking) — any handoff will be
logged here at its phase boundary. Workers/subagents where used: Sonnet 5
(tagged per artifact).

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

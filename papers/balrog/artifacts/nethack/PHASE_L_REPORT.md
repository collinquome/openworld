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

# Doctrine rule cards — Phase L session 5

MODEL: claude-opus-4-8[1m] (max thinking), 2026-07-07. Cards follow the
program standard {statement, mechanism class, evidence, holds_in%, scope,
status, provenance}. Runtime identity verified at session open (system-prompt
id = claude-opus-4-8, matches intended assignment; Fable at usage cap) — no
mismatch.

---

## THROW_DISENGAGE (NH-E6 v2 class-solve rule) — status: GRADUATED → paired block

- **statement:** in the crisis branch, when `_flee` declines to disengage
  (the adjacent threat is SAME-SPEED or faster, so its slower-only +
  full-disengage gates refuse), hurl carried ammo (dagger/dart/arrow/spear/
  shuriken/rock/aklys) at the nearest MOBILE hostile on a clear straight ray
  (dist ≤ 7) instead of falling through to a stand-and-trade death.
- **mechanism class:** SURVIVAL (P3 per-exchange ranged disengage; PROCEDURE
  layer). Proximal KPI = survival-to-depth via TRASH-death rate (KPI_TREE.md).
- **evidence:** e6_solve **v2** re-adjudicated the 9 s3-UNRESOLVED TRASH
  deaths (backoffs 40/120/300, window 600, in-model MC 20×250). ALL 9 →
  MISPLAYED, **0 UNWINNABLE**. THROW won **4 distinct seeds** (727 wererat,
  707 giant-bat, 714 hobbit, 732 kitten) → class-solve rule fires (criterion
  ii: ≥3 wins on ≥3 seeds). Diagnostic: 707 giant-bat (speed-22, un-outrunnable)
  escaped by BOTH THROW and STAIRS — the exact same-speed/faster-adjacent mode
  the s4 REST threshold tune could not reach. results/e6_solve_v2_trash.json.
- **holds_in%:** 4/9 of the residual TRASH set by THROW specifically; the full
  residual set is 100% avoidable (THROW 4 / KITE 1 / STAIRS 1 / MC 4).
- **scope / caveat:** requires carried throwable ammo + an in-line target;
  ammo-poor roles fall back to KITE/STAIRS (also validated wins). Survival
  linkage across full episodes PENDING the paired block (proximal KPI proven
  at the pre-death states via the deterministic branch; per-episode fire-rate
  measured in the block).
- **lever:** env flag NH_CRISIS_THROW (default OFF). Flag-off == prior code
  (seed 706 bit-identical to committed baseline md5 6cb03764: 248 steps /
  prog 0.017539535798967013 / D3 / Priest / jackal). nh_agent._crisis_throw.
- **status:** PROPOSE→COMPILE(NH_CRISIS_THROW)→BACKTEST(e6_solve v2, 4-seed
  class win)→DEPLOY(paired block, pre-registered s5). THE real REST fix the
  s4 diagnosis called for: a NEW ACTION, not a new number.
- **provenance:** claude-opus-4-8[1m] s5 (rule from the v2 solve loop).

---

## ARMOR_DOCTRINE (P3) — status: MODEL BUILT (v0.2); WEAR-rule PROVISIONAL

- **statement (target):** wear the AC-maximizing item per slot; revalue a
  loot detour on a large effective-HP delta.
- **mechanism class:** DEFENSE (AC → effective HP). Proximal KPI = DEFENSE.
- **model (BUILT s5, the s4 UNBUILT blocker cleared):** AC now enters the
  readiness ratio. `_p_hit_on_us(AC,mlev)=clamp((AC+mlev+BASE)/20)` (KB
  d20-vs-AC family; mlev proxy = depth; BASE=5, v0.2 uncalibrated, documented
  like the offense to-hit). The empirical band `dpt_p75` was measured at the
  corpus MEAN AC (AC_REF=7.1), so the sound counterfactual scales incoming dpt
  by the RATIO P_hit(AC)/P_hit(AC_REF): reproduces the band at AC_REF, monotone
  in AC. eff_hp = hp/ratio; PI_def = best_dpt×eff_hp; RR_def = PI_def/TI.
  `counterfactual_armor()` → real (Δac, Δeff_hp, Δrr); `counterfactual_power`
  WEAR now returns real deltas (was 0.0/0.0). nh_sheet.defense_model.
- **evidence:** monotone + correctly ranked — AC 10→−3 gives eff_hp
  16.8→60.4 / survivable turns 26→94; wear ranking mithril-coat (+8.4 eff_hp)
  > ring mail/cloak-of-prot (+3.3) > leather (+2.1) > small shield (+1.0).
  Snapshot suite GREEN 19/19 (additive; A7 armor-table fixture unaffected).
- **WEAR-rule headroom (proximal probe, armor_headroom.py):** **0/20** dev
  seeds (700–719) carry an unworn armor piece with positive Δrr at 150 steps
  — early game the starting armor is already worn and loot armor has not
  accumulated (Tourist starts naked AC 10, Wizard AC 0, Barbarian/Caveman
  AC 8). Honest read: the WEAR-rule is INERT early (same "provably inert
  in-scope" class as WIELD's melee roles); its value is mid-game armor drops.
- **scope / next:** MODEL is the shipped instrument; the WEAR-rule needs a
  deeper/corpus-scan headroom probe (mid-game) before a lever + paired block.
  Feeds the ARMOR × TRASH/MELEE+ coverage cells (defense now first-class).
- **provenance:** inferred (sheet arithmetic on frozen KB tables + bands),
  claude-opus-4-8[1m] s5.

---

## FLOOR-ROLE PLAYBOOKS (NH-E13 wiki flagship) — status: WIKI CARDS + PRE-REGISTERED

Operator directive (s5): mean-leverage = frequency × headroom; floor roles
win both. Wiki-fed (the human-solved doctrine already exists). Each card is
**provenance:wiki** (nethackwiki, sha256/rev-id in wiki_kb.sqlite), extracted
verbatim-sourced. Selected at episode start from the role census.

### HEALER (highest value — freq ~12% × largest headroom, ~2.15) — provenance:wiki
- **statement:** play cautious + CAST-TO-SURVIVE, not combat-forward. Healers
  are "the role best suited for PACIFIST conduct by far" (wiki). Cast healing
  for survival (wisdom stat, special spell = healing); apply the starting
  STETHOSCOPE (free monster HP read → know when to break contact); avoid melee.
- **mechanism:** SUSTAIN + SURVIVAL. We have NEVER cast healing spells for
  survival — pure headroom. Proximal KPI = Healer mean + survival@D5.

### TOURIST (freq ~7% × huge headroom, ~1.10 = OUR policy failing it) — provenance:wiki
- **statement:** "The Tourist's early game must be played with EXTREME
  CAUTION, and they will need to rely a lot on their extra healing potions and
  found items" (wiki). Darts are a BRIDGE weapon (21–40 +2 darts ≈ 84–160
  throws) — throw, do not melee. Use starting items / Magic Marker; avoid
  early combat; careful dive. Combat-forward play is ACTIVELY WRONG here.
- **mechanism:** SURVIVAL + item-reliance. THROW_DISENGAGE + KITE/STAIRS help
  Tourists MOST (their whole problem is dying to trash). Proximal KPI =
  Tourist mean + survival@D5.

### PRIEST / PRIESTESS (Cleric page; freq + headroom, ~2–3.4) — provenance:wiki
- **statement:** use inherent BUC-DETECTION (item beatitude is known for free
  → never wear/wield cursed, safely bless) + `#turn` undead. "Quite fragile
  early" → focus on improving AC, keep the robe intact, prefer lighter
  non-metallic armor (spellcasting-safe). Moderate aggression.
- **mechanism:** DEFENSE (BUC-safe gear + AC) + SURVIVAL. Proximal KPI =
  Priest/Priestess mean + survival@D5.

**Validation (pre-registered, HANDOFF_6 execution):** role-stratified dev
blocks, n≥15 of the target role (seed pools ready: Healer 83 / Tourist 65 /
Priest 45 / Priestess 30 from role_census 800-999 + 1100-1899). Report a
PER-ROLE MEAN TABLE each block. Track WIKI-ATTRIBUTABLE Δ explicitly (e.g.
Healer 2.15→? on wiki doctrine = the controlled "does the strategy guide
help?" number — NH-E13's owed three-way, made concrete per-role). The general
survival levers (THROW_DISENGAGE / escape menu / AC model) are built in
parallel and their floor-role-specific Δ measured.
- **provenance:** wiki (nethackwiki role pages) + claude-opus-4-8[1m] s5.

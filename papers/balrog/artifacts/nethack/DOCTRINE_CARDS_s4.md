# Doctrine rule cards — Phase L session 4

MODEL: claude-opus-4-8[1m] (max thinking), 2026-07-07. Cards follow the
program standard {statement, mechanism class, evidence, holds_in%, scope,
status, provenance}. Written for E17 clean-room rebuild.

---

## WIELD_DOCTRINE (P2, launcher-scope) — status: PROVISIONAL (role-scoped)

- **statement:** when a carried weapon or launcher+ammo pair has higher
  expected dpt (character-sheet best option) than the current wield, switch
  to it before engaging.
- **mechanism class:** OFFENSE (character sheet; PERCEPTION layer). Proximal
  KPI = OFFENSE (PI / best-dpt), per KPI_TREE.md.
- **evidence:** sheet-measured offense headroom = 2/10 dev probes, BOTH
  Rangers under-firing (seed 723 orcish bow+arrow 1.72 vs wielded dagger
  1.15; seed 805 crossbow+bolt 2.01 vs dagger 1.44; +40-50% dpt). Every
  melee role probed (Knight/Priest/Healer/Wizard/Priestess) already wields
  its best option → zero headroom. n=10 probes; source nh_sheet s4.
- **holds_in%:** role-scoped — applies to launcher/ranged-capable roles;
  provably inert for pure-melee roles (0/8 melee-role probes had headroom).
- **scope / caveat:** proximal KPI (offense) validated by construction;
  death-class resolution (survival linkage) PENDING a paired block on
  Ranger-heavy seeds. Do not claim broad TRASH/MELEE+ resolution.
- **provenance:** inferred (sheet arithmetic), claude-opus-4-8[1m] s4.

---

## ARMOR_DOCTRINE (P3) — status: UNBUILT (prerequisite now MET)

- **statement (target):** wear the AC-maximizing item per slot; on a large
  effective-HP delta, revalue the loot detour (curiosity value for unknowns).
- **mechanism class:** DEFENSE (AC → effective HP). Proximal KPI = DEFENSE.
- **blocker:** nh_sheet.counterfactual_power returns delta 0.0 for armor —
  AC does not enter the readiness ratio yet ("slot economics v0.2"). The
  power index is offense×hp only; AC is unused on the defense side.
- **prerequisite (MET s4):** the armor AC table was corrupt — build_armor_table
  grabbed Cost/Weight not AC (33/66 rows wrong). FIXED s4 (parse column 4;
  snapshot fixture A7). A defense model built on the old table would have
  been meaningless; it is now correct.
- **next (spec):** fold AC into RR via monster-hit probability —
  effective_incoming_dpt = band_dpt × P(hit | our AC); source the to-hit
  rule from the KB (d20 vs 10+AC family); then counterfactual wear yields a
  real delta_rr and the doctrine is validatable. Deferred to session 5.
- **provenance:** spec + prerequisite fix, claude-opus-4-8[1m] s4.

---

## REST/DISENGAGE lever (NH-E6 solve-loop) — status: paired block s4

- **statement:** break contact from a losing exchange earlier — flee when
  hp < CRISIS_HP × hpmax, or when a recent max hit × CRISIS_EXCH ≥ current hp.
- **mechanism class:** SURVIVAL (P3 crisis-disengage; PROCEDURE layer).
  Proximal KPI = survival-to-depth via TRASH-death rate.
- **backtest (done):** e6_solve TRASH — REST/disengage survives 10/20 TRASH
  deaths on 10 distinct dev seeds, winning at 40-step backoffs (shallow
  decision errors dominate). CLASS SOLVE RULE fired s3.
- **diagnosis (s4):** the P3 crisis-flee thresholds were hardcoded 0.28 /
  ×2.0. The DEV death-shape KPI shows agents die at ~35% HP — i.e. ABOVE the
  0.28 flee floor, lost in the 35→28% window while still trading blows. So
  the fatal hit lands before the flee reliably engages.
- **interaction:** complements NH_E15 L2 disengage (watchdog-triggered, i.e.
  reactive to a persistent standoff). This lever is the PROACTIVE per-exchange
  version — it is a threshold tune of an existing trigger, not new machinery
  (handoff prediction confirmed).
- **lever:** env knobs NH_CRISIS_HP (default 0.28) / NH_CRISIS_EXCH (default
  2.0). Defaults reproduce prior behavior exactly → flag-off regression PASS
  (seed 706 bit-identical: 267 steps / prog 0.026482449457437766 / D5 /
  kitten). Test condition = 0.40 / 1.5.
- **status:** PROPOSE→COMPILE→BACKTEST(e6_solve)→DEPLOY(paired block, s4).
  Verdict in RUN_LOG (see rest_lever_ref/test.json).
- **provenance:** claude-opus-4-8[1m] s4.

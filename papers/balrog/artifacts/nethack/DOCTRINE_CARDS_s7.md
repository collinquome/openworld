# Doctrine rule cards — Phase L session 7

MODEL: claude-opus-4-8[1m] (max thinking), 2026-07-07. Runtime identity VERIFIED
at session open (system-prompt id = claude-opus-4-8, matches intended
assignment; Fable at usage cap) — NO mismatch. All s7 artifacts stamped
claude-opus-4-8[1m]. Cards carry TWO provenance axes: KNOWLEDGE provenance
(origin of the FACT) AND INSIGHT provenance (origin of the IDEA: origin-code +
discovery-mechanism + one-line replication recipe).

---

## DOOR_DIAGONAL_KITE (s7 mean-mover bet) — status: DROPPED at the self-play gate

- **statement (tested):** route the crisis flee toward / through a known doorway
  so a same-speed pursuer, unable to move diagonally into/out of a doorway,
  eats an orthogonal penalty and loses ground (wiki Standard_strategy).
- **mechanism class:** SURVIVAL / POSITIONING. Proximal KPI (a positioning
  lever) = distance-gain on the pursuer (turns-adjacent ↓, max-min-distance ↑),
  NOT downstream survival.
- **testbed:** the in-model strategic self-play gate (self_play.py + the
  paired KITE-vs-DOOR_KITE distance harness) on the 4 residual TRASH-death
  seeds {707 Rogue, 714 Tourist, 727 Valkyrie, 732 Ranger}. NLE natively
  enforces the door-diagonal rule for BOTH player and monsters
  (nh_common.neighbors lines 366-370), so the geometry is captured exactly —
  the perfect deterministic testbed the directive named. Doors are present and
  reachable (nearest open door 1-6 cells) in all 4 scenarios.
- **evidence (VERDICT):** across 16 (seed × backoff∈{15,30,50,80}) branch
  states, TWO door-kite variants were paired against straight-line KITE:
  variant A (door-seeking above distance-max) and variant B (door-proximity as
  a FREE TIEBREAKER, distance-max primary == KITE). The door term genuinely
  changed the chosen step in **13/16** branch states (mechanism fires), but:
    - survival to death_t+600: KITE **0/16**, DOOR_KITE **0/16** (no gain);
    - sum-of-max-distance-to-pursuer: KITE **24**, variant-A **24**,
      variant-B **23** (NO larger gap opened);
    - turns-adjacent: KITE 83%, variant-A 94%, variant-B 91% (door-routing kept
      the agent adjacent LONGER, not shorter — routing to the choke pulled it
      into the bottleneck).
  At backoff 120 (self_play_doorkite_b120.json) DOOR_KITE ≡ KITE exactly
  (0/4 survive, 4/4 escape).
- **why it failed (the finding):** on the sampled TRASH deaths, straight-line
  distance-maximizing flee ALREADY escapes the level 4/4; the door-diagonal
  exploit needs (a) a same-speed pursuer on the DIAGONAL of the door transition
  and (b) a clean straight run through — a geometry these open-room fights don't
  present. Biasing the flee toward the door costs tempo and can trap the agent
  at the choke. Door-diagonal kiting is real NetHack geometry but is NOT the
  operative lever for this death class as sampled.
- **disposition:** the pre-registered self-play GATE ("does it beat straight-
  line flee IN-MODEL?") returned NO. Per the s6 MODEL-FIDELITY meta-card
  (in-model OVER-credits levers), a lever that does not even win in-model has ~no
  chance in the real env — so DOOR_KITE does **not** graduate to a real-env
  paired block. Caught cheaply at the gate; the expensive block is SAVED. Code
  retained flag-off behind the self-play NAMED_SP menu for the lab.
- **provenance (knowledge):** wiki (nethackwiki Standard_strategy — doorway
  diagonal restriction) + data (our self-play distance harness).
- **provenance (insight):** OP via READ-WIKI (directive named the tactic);
  mechanism BORROW-FIELD + NOTICE-ABSENCE; recipe = "wire door-attraction into
  the kite pathing behind a variant flag → paired KITE-vs-DOOR_KITE self-play
  across backoffs → measure distance-gain (turns-adjacent, max-dist), NOT just
  survival → see the step change but no gap open → the exploit's geometry isn't
  present in this death class."

---

## RULE_BASE_ARCHITECTURE (s7 HEADLINE, operator's big ask) — status: BUILT + migrated, regression-safe

- **statement:** the scattered hardcoded survival if-thens are formalized as a
  first-class DECLARATIVE rule base (nh_rulebase.py): each rule =
  {condition matcher over a served-obs STATE VIEW, reminder (LLM-facing) +
  action_tag (procedure-facing), severity HARD-GUARD|ADVISORY, provenance×2}.
  ONE base, TWO consumers: the PROCEDURE layer calls `RB.check(rule_id, state)`
  for the hard-guard boolean its decision sites act on; the INTUITION layer
  calls `RB.reminders_text(state)` to push fired rules into LLM context as a
  REMINDERS section (advisory-push ABLATION deferred to a later block).
- **migrated (behavior-preserving):** four guards ported to declarative rules,
  each condition an EXACT port of the predicate it replaced —
  NEVER_MELEE (HARD-GUARD), TOUCH_KILL_WEAPON (ADVISORY), PRAYFIX_DEFER
  (HARD-GUARD), HEAL_MIDBAND (ADVISORY). The four decision sites in nh_agent.py
  delegate to the base when NH_RULEBASE is ON; flag OFF → base never consulted.
- **evidence (regression contract MET):**
    - unit equivalence (rulebase_equiv.py): **130/130** checks — every rule
      condition == its migrated predicate across the sampled state space;
    - end-to-end trajectory equivalence: seed 706 (Priest — exercises
      NEVER_MELEE/PRAYFIX) and 831 (Healer — exercises HEAL band, heal_fires=2)
      run under the full flag config with NH_RULEBASE=0 vs =1 are
      **BIT-IDENTICAL**;
    - flag-off vs s6 baseline (seed 706, no NH_ flags): bit-identical (only
      wallclock differs);
    - snapshot suite **19/19** green.
- **scope / next:** this base is the COMPILE TARGET for all external knowledge
  (wiki/forum/ttyrec) — new facts land as provenanced rules, not fresh
  if-thens. The advisory-push ablation ("does pushing REMINDERS to the LLM
  improve Arm-B decisions?") is the queued follow-on block.
- **provenance (knowledge):** architecture (operator design session 2026-07-07)
  + source/mined/wiki per each migrated rule (see nh_rulebase.build_default_base
  provenance fields).
- **provenance (insight):** OP (declarative rule-base directive); mechanism
  QUESTION-FRAME + GENERALIZE-FIX; recipe = "enumerate the scattered survival
  if-thens → give each a {condition,severity,reminder,provenance} rule →
  delegate the procedure predicates to the base behind a flag → prove
  unit-equivalence + bit-identical trajectory → expose reminders_text for the
  intuition layer."

---

## KICK_COST_GATE (s7 quick safety fix) — status: BUILT flag-off, mechanism verified

- **statement (tested):** kicking a locked door risks a broken leg (→ slowed →
  death), a cost the s6 audit found UNGATED (kicks fired up to 12× with no
  HP/role check). Gate the kick: skip when HP < KICK_MIN_HP (0.5) of max or the
  role is fragile/low-HD (Tourist/Wizard/Archeologist); DEFER the door instead
  (re-approachable with a key later).
- **mechanism class:** SURVIVAL (guard-class). Behind flag NH_KICK_GATE.
- **evidence:** unit table — Valkyrie 20/20 kick_ok=True; Valkyrie 6/20=False
  (below 50%); Tourist/Wizard any-HP=False (fragile); Barbarian 15/20=True,
  11/20=True (55%, above floor). Flag-off (default) bit-identical (seed 706).
- **status:** ships flag-OFF (regression-safe); ready to enable / A-B after a
  block. A full "re-fire when a key is found" curiosity requeue is deferred.
- **provenance (knowledge):** inferred (break-leg death mode; kick.c leg-break
  on failed kick).
- **provenance (insight):** DATA (s6 kick audit: 12× ungated) + AG; mechanism
  NOTICE-ABSENCE; recipe = "audit kick fire-count → find no HP/role gate → add
  the gate + defer-and-return, flag-gated."

---

## HEALER_MIDDLE_HP_BAND (NH-E13 WHEN-refinement) — status: DROPPED (net-negative, third trigger)

- **statement (tested):** heal in a MIDDLE HP band [HEAL_HP_LO=0.30,
  HEAL_HP_FRAC=0.55] of max UNDER THREAT (adjacent hostile), earlier than the
  s6 near-death crisis and without the s6 proactive no-threat top-up. The s6
  diagnosis said the WHEN was mis-set in both directions; this block set it to
  the middle.
- **mechanism class:** SUSTAIN + SURVIVAL. Proximal KPI = Healer mean +
  survival@D5.
- **evidence (VERDICT):** s7 role-stratified paired block, n=20 Healer seeds,
  cap 6000, ref=standing vs test=+NH_ROLE_PROFILE (band 0.30-0.55). WIKI-
  ATTRIBUTABLE Healer delta = **-0.63** CI95 [-1.76, **-0.02**] (mean
  2.57→1.93; CI EXCLUDES 0 → clearly negative). survival@D5 **40%→20%**
  (worse). Mechanism MET: 18 heal casts. 15/20 bit-identical. Death-class
  distribution unchanged (TRASH 14/14 both).
- **why it failed (the finding — the WHEN-band did NOT rescue it):** the
  middle-band under-threat heal STILL donates the cast-turn mid-fight and STILL
  perturbs otherwise-good runs — seed 900 regresses IDENTICALLY to s6
  (ref D10/12.56 → test D4/2.12, -10.44, the single biggest loss both
  sessions). Regressions {828 -0.53, 879 -0.53, 900 -10.44, 935 -1.42} vs a
  single +0.21 (932). Across all THREE triggers tested (s6 crisis-late, s6
  proactive-safe, s7 middle-band-under-threat) the heal-cast lever is
  net-negative for this agent: the turn-donation opportunity cost of casting
  dominates the HP restored, and the wiki's "cast healing for survival" does
  not transfer to this policy's play.
- **holds_in%:** 1/20 improved; 4/20 regressed; 15/20 outcome-neutral.
- **status:** DROP. Ship flag-OFF (NH_ROLE_PROFILE default 0; no revert
  needed). Heal-cast plumbing + the rule (HEAL_MIDBAND, ADVISORY) retained for
  the intuition layer, but the HARD procedure trigger stays off.
- **provenance (knowledge):** wiki (nethackwiki Healer) + data (s6+s7 blocks).
- **provenance (insight):** WIKI + DATA; mechanism ASK-WHY-ON-FAILURE; recipe =
  "s6 found both naive triggers net-negative → set the WHEN to a middle HP band
  under threat → n=20 role-strat block → still -0.63, seed 900 identical
  regression → the heal-cast lever is net-negative independent of the band."

---

## Session-7 verdict summary
| workstream | verdict | number |
|---|---|---|
| DOOR_DIAGONAL_KITE | DROP at self-play gate | 13/16 fires, 0/16 surv, no distance-gain (24 vs 24/23) — real-env block saved |
| HEALER middle-band | DROP | delta -0.63 CI95 [-1.76,-0.02]; surv@D5 40→20% |
| RULE_BASE_ARCHITECTURE | BUILT (headline) | 4 guards migrated; 130/130 equiv; bit-identical; 19/19 snapshot |
| KICK_COST_GATE | BUILT flag-off | HP/role gate + defer; unit-verified; bit-identical |

Two mean-movers dropped with clean mechanistic diagnoses (door-kite: exploit
geometry absent in the death class; healer: heal-cast net-negative across all
three triggers). The headline architecture landed regression-safe. Flag-off
bit-identical (seed 706); snapshot 19/19.

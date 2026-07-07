# Doctrine rule cards — Phase L session 6

MODEL: claude-opus-4-8[1m] (max thinking), 2026-07-07. Runtime identity
verified at session open (system-prompt id = claude-opus-4-8, matches intended
assignment; Fable at usage cap) — NO mismatch. Cards carry TWO provenance axes
(operator directive s6): KNOWLEDGE provenance (origin of the FACT) AND INSIGHT
provenance (origin of the IDEA: origin-code + discovery-mechanism + one-line
replication recipe). Standard fields: {statement, mechanism class, evidence,
holds_in%, scope, status, provenance×2}.

---

## THROW_DISENGAGE (NH-E6) — status: DROPPED (live paired block, drop-rule fired)

- **statement (tested):** in the crisis branch, when `_flee` declines to
  disengage (adjacent threat same-speed/faster), hurl carried ammo at the
  nearest in-line mobile hostile instead of trading melee.
- **mechanism class:** SURVIVAL (P3 ranged disengage). Proximal KPI = TRASH-
  death rate.
- **evidence (VERDICT):** s6 pre-registered paired block, n=12 (4 e6-THROW-win
  {707,714,727,732} + 8 fresh {780-787}), cap 6000, ref=standing vs
  test=+NH_CRISIS_THROW. delta **-0.28** CI95 [-0.68,+0.00]. 17 real throw
  fires (recovered from traj evs) on 4 seeds. Every seed where the throw
  MATERIALLY diverged the trajectory REGRESSED: 732 D4->D1 (-2.12), 783 D6->D5
  (-0.89), 782 D4->D3 (-0.37); 714 fired 2x but died identically (Tourist D1).
  Criterion 2 (delta not clearly negative) FAILED. survival@D5 33.3%->33.3%.
- **holds_in%:** 0/3 of the materially-divergent seeds improved (all regressed).
- **why it failed (the finding):** hurling ammo at a SAME-SPEED ADJACENT monster
  donates a turn without creating distance — the monster keeps hitting and the
  throw whiffs/does little; strictly worse than the incumbent fight/partial-flee.
  The e6 replay backtest over-credited it: it won at 4 pre-death BRANCH STATES
  drawn from baseline-policy episodes, but the live policy under the standing
  config never reaches those states (the e6-winners 707/727 fired 0x live; the
  seeds that DID fire were different and worse).
- **status:** DROP per pre-registered drop-rule. Ship remains flag-OFF
  (NH_CRISIS_THROW default 0; no revert needed). Code retained behind the flag
  for the lab / self-play comparison.
- **provenance (knowledge):** data (e6 replay + s6 live block).
- **provenance (insight):** AG+DATA; mechanism WATCH-REPLAY + ASK-WHY-ON-FAILURE;
  recipe = "wire the replay-winning rule live behind a flag → paired block on
  the winning seeds + fresh → count LIVE fires from ev_log → see fires land on
  different seeds and regress → backtest over-credited it."

---

## MODEL-FIDELITY-FOR-STRATEGY-TRAINING (meta-card) — status: ESTABLISHED

- **statement:** a strategy validated in a MODEL / on REPLAYED historical
  states can be inert-or-negative in live self-play, because (a) the live
  policy may never reach the states where the model scored the strategy, and
  (b) a deterministic single-sample combat model hides costs (turn-donation)
  that a distributional model would surface. Therefore EVERY model/replay-
  derived strategy is disposed by a real-env PAIRED BLOCK before belief; the
  GAP between in-model win and real-env delta is the reported fidelity number.
- **evidence:** THROW graduated in-model (e6 v2: won 4 trash pre-death branch
  states) but the s6 real-env paired block returned delta -0.28 (negative). The
  gap = +win (in-model) vs -0.28 (real-env). Companion in-model self-play
  quantification: self_play.py per-strategy survival on the trash-fight (lean
  re-run pending; the e6 v2 winners table IS the first-order in-model result).
- **scope:** governs the whole propose→compile→BACKTEST→deploy loop and the
  operator's strategic-self-play directive (self-play proposes, real env
  disposes; report both numbers + the gap).
- **provenance (knowledge):** data (our own e6 vs s6 blocks).
- **provenance (insight):** OP (self-play directive named the guard) + AG (we
  hit it empirically); mechanism NOTICE-ABSENCE + GENERALIZE-FIX.

---

## HEALER_CAST_HEAL (NH-E13 wiki flagship) — status: DROPPED (net-negative as-implemented)

- **statement (tested):** role==Healer + HP<HEAL_HP_FRAC(0.55) → cast the
  book's cheapest HP-restoring spell (self-target, no direction), in three
  sites: crisis-trapped (after _flee declines), and proactive top-up when no
  threat adjacent + not starving.
- **mechanism class:** SUSTAIN + SURVIVAL. Proximal KPI = Healer mean +
  survival@D5.
- **evidence (VERDICT):** s6 role-stratified paired block, n=20 Healer seeds,
  cap 6000, ref=standing vs test=+NH_ROLE_PROFILE. WIKI-ATTRIBUTABLE Healer
  delta = **-0.62** CI95 [-1.73,+0.00] (mean 2.57→1.95). survival@D5
  40%→25% (worse). Mechanism MET: 18 heal casts, menu parse+select+restore
  confirmed. DROP: both proximal-KPI components negative; survival@D5 clearly
  worse.
- **why it failed (the finding — the wiki says WHAT not WHEN):** the two
  triggers bracket the right answer on both sides. Crisis-trapped heal fires
  TOO LATE (~hp 4/21, near death → 16/20 test episodes bit-identical to ref:
  healed a sliver, died the same way). Proactive HP<55% top-up is HARMFUL:
  burns turns/Pw standing still and perturbs otherwise-good runs (seed 900:
  ref D10/12.56 → test D4/2.12, −10.44, the biggest single loss). No positive
  surface.
- **holds_in%:** 0/20 improved; 4/20 regressed; 16/20 outcome-neutral.
- **scope / next (refinement hypothesis, HANDOFF_7):** heal at a MIDDLE HP band
  (earlier than the hp-4 crisis so it can actually change survival, but not
  proactively when it costs exploration turns). The WHEN-to-heal threshold is
  the true lever; this first cut mis-set it in both directions. Mechanism is
  reusable (heal-cast plumbing works); the trigger is what needs a new block.
- **status:** DROP; ship flag-OFF (NH_ROLE_PROFILE default 0; regression
  confirmed bit-identical seed 706). Code retained behind the flag.
- **provenance (knowledge):** wiki (nethackwiki Healer page — "cast healing
  for survival, best pacifist role") + data (verb-frontier: cast_heal never
  fired before).
- **provenance (insight):** WIKI + DATA (NOTICE-ABSENCE the never-used verb);
  mechanism BORROW-FIELD + NOTICE-ABSENCE. recipe = "wiki says cast-heal →
  verb audit shows cast_heal fires=0 ever → wire heal-casting → role-stratified
  block → the guide gives the WHAT, the WHEN is an open lever (this block
  found both naive triggers net-negative)."

---

## Session-6 verdict summary (2 pre-registered blocks RUN → both DROP)
| lever | block | proximal KPI | verdict | number |
|---|---|---|---|---|
| THROW_DISENGAGE | n=12 paired | TRASH-death rate | DROP | delta −0.28 [−0.68,0]; regresses where it fires |
| HEALER cast-heal | n=20 role-strat | Healer mean + surv@D5 | DROP | delta −0.62 [−1.73,0]; surv@D5 40→25% |

Both DROPs are informative negatives with mechanistic explanations: THROW =
model-fidelity gap (replay over-credited a lever the live policy under-reaches
and that donates turns); HEALER = the wiki gives the WHAT not the WHEN, and both
naive heal-triggers are net-negative. Flag-off regression bit-identical (seed
706). Snapshot suite green 19/19 at open.

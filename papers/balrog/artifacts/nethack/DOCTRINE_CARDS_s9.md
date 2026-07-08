# Doctrine Cards — Phase L session 9 (claude-opus-4-8 [max thinking])

Runtime identity VERIFIED at open: system-prompt model id = claude-opus-4-8,
max thinking; Fable at usage cap. All s9 artifacts stamped claude-opus-4-8[max].
Fork aleph/fable-nethack. Session = DEMONSTRATION LEARNING (NH-E35) + the
operator's hunger reframe (Tier-1 anti-faint guard).

---

## CARD S9-1 — NH-E35a WORLD-MODEL VALIDATION ON EXPERT PLAY  [SOLID]
provenance: knowledge=DEMONSTRATION (public alt.org human ttyrecs, OFFLINE, like
reading the wiki/source — disclosed) + insight-origin=OP (2026-07-07 s5 NH-E35
design) + replication recipe below.

**Result: 0 violations / 56,407 action-free possibility-set checks on independent
expert human play.** 4 alt.org games (2 top-class players: rschaff x3, nnnet x1),
~15k game-turns. Per-rule (V_TIME / V_HP / V_XP / V_DEPTH) each 0 / ~12–15k.
This extends our "0 / 233k shallow self-play" number to data WE DID NOT GENERATE
— the world model's invariant layer does not drift on real expert transitions.

**Method (why hand-rolled).** NLE's C `Converter` (_pyconverter) emits ZERO
frames for alt.org dgamelaunch human ttyrecs — it is keyed to NLE-injected frame
markers that public V1 recordings lack (verified: remaining==SEQ, chars.sum()==0
across all dims/versions). So we render the ttyrec ourselves: `e35_ttyrec.py` is a
minimal ANSI/VT100 emulator (clear / cursor-position / erase-line / CR-LF-BS +
printable writes) that recovers the two STATUS lines + cursor + message. From
those we parse blstats (hp/hpmax, Dlvl, T, Xp, condition words) and run the
possibility rules ported from `c2_violations.py`.

**Scope / honesty caveats (load-bearing):**
1. V1 human ttyrecs carry NO action labels (keypresses exist only in NLE V2/V3
   recordings), so we ran the ACTION-FREE subset = exactly the world-model
   INVARIANT layer (V_TIME/V_HP/V_XP/V_DEPTH). V_NONMOVE_POS needs the action
   and is omitted. V_MOVE was attempted via cursor-position + chebyshev but is
   NOT cleanly testable here: the tty cursor frequently rests at line-end
   (col 79), not on the hero, so its 19–23% "violation" rate is
   position-recovery NOISE, not model violations (confirmed from samples) —
   EXCLUDED from the quality claim.
2. DEPTH: the games reached max Dlvl 5 / 13 / 6 / 12 — SHALLOWER than our own
   max Dlvl 21. Live alt.org prunes ttyrecs; only currently-active mid-level
   players remain (ascension/streak archives aged out), and they die shallow.
   So this corroborates the invariants on INDEPENDENT play but does NOT (yet)
   extend past our own depth. Getting a past-D21 ascension ttyrec is future work
   (needs a live ascender's fresh game, or the big NLD-AA S3 dataset which is now
   access-denied). Honest read: strong world-model-quality evidence on
   independent data; the "deep edge cases" ambition is unmet this session.

**Replication recipe:** list `https://www.alt.org/nethack/userdata/<L>/<user>/ttyrec/`
(Apache index), fetch a handful of completed `.ttyrec` (timeout-guarded, modest)
to `work/fable_nethack/ttyrecs/`, then `python3 e35_validate.py` (foreground, no
net; emulator = `e35_ttyrec.py`). Result cached at `results/e35_validate.json`.
Clean-protocol: OFFLINE analysis only; scored agent runs stay pure-code.

---

## CARD S9-2 — NH-E35c EXPERT HUNGER LAW: "never below Hungry"  [SOLID arbiter]
provenance: knowledge=DEMONSTRATION (same 4 alt.org games) + insight-origin=OP.

**Across 4 expert games / ~35k turns, NO expert EVER dropped below the "Hungry"
tier — 0 frames at Weak / Fainting / Fainted.** Experts sit at Normal/Satiated
and resolve brief "Hungry" excursions (68 / 58 / 301 frames) promptly by eating.
They eat ONE TIER EARLIER than our policy and never enter the faint cascade.

This is the honest arbiter the operator asked for: of the Tier-1 food-economy
levers, the demonstration data most strongly endorses **eat-at-Hungry (buffer
maintenance)** — precisely the anti-faint guard.

---

## CARD S9-3 — ANTI-FAINT GUARD (rule [ANTI_FAINT], flag NH_ANTIFAINT)  [SHIPPED flag-OFF, backtest PENDING]
provenance: knowledge=DEMONSTRATION (S9-2 expert hunger law) + insight-origin=OP
(DEATH_TO_CAPABILITY Tier-1) + precedent rule CAST_HUNGER ("casters eat at HUNGRY
not Weak"). layer: LOGISTICS.

**Addressable mass (from OUR OWN 741 logged trajectories):**
- reach Hungry(>=2): 62.1%   reach Weak(>=3): 35.0%   reach Fainting(>=4): 26.5%
- Peak-tier histogram: Normal 37.9% / Hungry 27.1% / Weak 8.5% / **Fainting 26.5%**.
  More episodes PEAK at Fainting than at Weak => once past Hungry our agent
  usually blows straight through Weak to Fainting. The existing WEAK-eat guard
  (nh_agent line ~1352, fires at hunger>=WEAK) is firing TOO LATE — at Weak
  there is often no food left to eat; the fresh corpse should have been eaten at
  Hungry. Expert incidence of Weak = 0%. This gap is the lever.

**Design.** New block in `_decide` (nh_agent.py), guarded `if C2_ANTIFAINT and
A.hunger == C.HUNGRY and not self._adjacent_hostiles():` placed immediately
before the existing `if A.hunger >= C.WEAK:` block. At Hungry, if READILY-
available food exists it eats NOW: inventory food (`_food_letter`) → fresh corpse
here (`_fresh_corpse_here`) → a <=3-step safe corpse (`fresh_kills` ∩ SAFE_CORPSES).
Elective, so gated on NO adjacent hostile (don't donate a free attack for a
non-crisis eat). Prayer + longer detours stay in the WEAK+ block. Reuses the
exact helpers/queue mechanism the proven WEAK-eat uses — strict superset firing
one tier earlier. Flag default OFF; added to C2_ANY; flag-off is structurally
bit-identical (single `if C2_ANTIFAINT` guard). Imports clean; runs on real
episodes without crash/regression (seeds 101/102 combat deaths, guard correctly
inactive — maxHunger=Normal).

**PRE-REGISTERED paired block (next session, the honest exit criterion):**
REF = C2.1 frozen (`NH_FOOD2 NH_PRAYFIX NH_LOS NH_TOPO NH_GUARD` + `NH_CAST
NH_CASTHUNGER NH_E15`) vs TEST = REF + `NH_ANTIFAINT=1`. n>=20 dev seeds, cap
6000, ONE seed per process (s8 cross-seed-leakage note). Proximal KPI = faint+
starve death rate. **High-SNR proxy KPI = Fainting-incidence rate (currently
26.5%, n=741 => tight CI); target = drop toward the expert 0%.** Drop-rule
applies (guard against seed luck). Do NOT ship 'kept' until the block is green.

---

## Session queue for s10
1. RUN the S9-3 pre-registered anti-faint paired block (proxy KPI = Fainting-
   incidence). This is the immediate-mass deliverable; the guard is built and
   waiting behind one flag.
2. Verify the safe-corpse table isn't over-rejecting (coordinator piece 2): the
   SAFE_CORPSES set (nh_common.py:155) looks reasonable but audit `_cannibal` +
   freshness rejection against the E35c expert corpse-eating behavior.
3. Operator's remaining hunger pieces: resource-tracker (nutrition as first-class
   importance-weighted dossier state), death-retro replay (NH-E12) on the
   starved-93 + fainted-52 corpus, isolated hunger self-play, wiki Comestible KB.
4. Deeper ttyrec: grab a fresh ASCENSION game from a currently-active ascender to
   extend S9-1 past Dlvl 21 (the unmet depth ambition).

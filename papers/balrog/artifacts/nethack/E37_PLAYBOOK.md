# NH-E37 — Per-Class Expert Early-Game Playbook (D1-6)

MODEL: claude-opus-4-8 (max thinking), Phase L NH-E37. Runtime identity verified
at session open (system-prompt id = claude-opus-4-8, matches intended assignment;
Fable at usage cap) — no mismatch. Tier-sensitive extraction done carefully.

Operator directive: "analyze expert play and bake the strategies for early
levels for all classes — we've got to find something RELIABLE."

provenance: DUAL. knowledge = DEMONSTRATION (public alt.org expert human
ttyrecs, used OFFLINE for research; disclosed — same class as reading the
wiki/source). insight-origin = OP (NH-E37 directive). Extractor: e37_extract.py
(reuses the e35_ttyrec.py ANSI emulator). Corpus: artifacts/nethack/ttyrecs/.
Clean-protocol: OFFLINE analysis only; scored agent runs stay pure code.

---

## THE CORPUS (6 expert games, 5 classes, all top alt.org players)

| player   | class    | span (align/race)     | ttyrec |
|----------|----------|-----------------------|--------|
| nnnet    | Wizard   | neutral gnomish female | nnnet__2026-07-08.00_18_03 |
| rschaff  | Samurai  | lawful human male ×2   | rschaff__2026-07-06.02_42_54, rschaff__2026-07-07.23_22_57 |
| Zapwai   | Caveman  | neutral human          | Zapwai__2026-07-08.00_12_26 |
| DaveT    | Priest   | lawful human           | DaveT__2026-07-08.00_11_28 |
| Langmuir | Knight   | lawful human male      | Langmuir__2026-07-08.00_50_17 |

Classes span the strength ladder: strong (Samurai, Caveman, Knight) →
fragile (Wizard, Priest).

**[GAP]** No expert ttyrec acquired this session for **Valkyrie, Barbarian,
Tourist, Healer** (also Ranger/Monk/Rogue/Archeologist). alt.org's early-game
archives are class-varied and the fetch recipe generalizes (dumplog role →
plr.php ttyrec index → fetch); these 4 are the priority acquisitions for the
next session. Proceeded with the 5 acquired classes as directed.

---

## THE EXTRACTED EARLY-GAME ROUTINE (what experts DO, T ≤ 2000)

Signal recoverable from a V1 human ttyrec = the rendered tty message-line +
status only (NO action labels). We mine eat events + the hunger tier at each,
wield/wear, prayer, altar/BUC, dive pacing (turn to first reach each depth),
and combat-message intensity. Numbers below are per-game counts in the
first ~2000 game-turns.

### CROSS-CLASS UNIVERSALS (high confidence — every class does these)

1. **Opportunistic safe-corpse eating, BEFORE Hungry.** Every expert eats
   fresh safe corpses (newt / jackal / lichen / giant-rat / cave-spider) the
   moment they are made, while still "not hungry" — banking nutrition ahead of
   need. **No expert ever dropped below the "Hungry" tier** (worst hunger in
   window = Hungry for Priest/Samurai/Caveman; never Weak/Fainting). Priest
   ate 13× in-window; Samurai-2 ate 8×. This is the PREVENTIVE hunger buffer —
   the exact eat-at-Hungry / corpse-bank law E35/E11 already found. → maps to
   **NH_FOODACQ + NH_ANTIFAINT**.
2. **Heavy PET utilization.** 20-103 pet interactions per game (swap-places /
   displace) across ALL classes (Wizard 103, Caveman 76, Priest 57, Samurai
   49/20, Knight-pony 40). Experts keep the pet adjacent and let it tank/kill
   trash — a preventive positioning buffer. → maps to **NH_PET**.
3. **Proactive ranged softening.** 14-68 throw/shoot events (Samurai 68,
   Caveman 63 rocks, Wizard 54, throws before contact). Experts soften/kill at
   range so they never take the melee exchange — the purest "don't ENTER the
   0-survivor melee" behavior. → maps to **NH_RANGED** (our THROW is crisis-only;
   experts throw preventively).
4. **Elbereth engraving for survival.** Samurai / Wizard / Caveman each engrave
   Elbereth ~5× in-window — scare-monster panic buffer to break contact.
   → maps to **NH_ELBERETH** (weapon-engraved; fingertip-Elbereth is UNREACHABLE
   in BALROG's NLE action space — documented constraint).
5. **Prayer when in trouble, early.** Priest prays T1549, Samurai T769, Wizard
   T1522 — early prayer is safe (< ~1000-turn timeout). → maps to **NH_PRAYFIX**.
6. **Wear all armor immediately** ("dressing maneuver" T182-204 for Priest/
   Knight). Note: our WEAR-rule probe found this INERT early (roles start with
   armor already worn) — experts wearing armor at T180 is just starting armor.

### PER-CLASS TEMPO + OPENER (the differentiator)

- **Samurai (strong martial)** — FAST dive: D5@T859, D6@T1134. Ranged-first
  (68 throws, bow/shuriken), early corpse-eat, Elbereth, prays early. Does NOT
  defer descent. Opener = soften-at-range → dive on tempo.
  *cite: rschaff ×2.*
- **Caveman (strong bruiser)** — rock/sling ranged (63 throws), pet-forward
  (76), corpse-bank; moderate dive D5@T1494. *cite: Zapwai.*
- **Knight (strong pet-forward)** — pony pet (40), ranged, corpse-bank;
  moderate dive D4@T567. *cite: Langmuir.*
- **Wizard (fragile caster)** — CAUTIOUS dive (D5@T1505, slowest). Force-bolt
  economy, Elbereth 5×, altar-BUC 4×, corpse-bank, pick-axe for escape-dig.
  Opener = cast/kite from range, level up before diving. *cite: nnnet.*
- **Priest (fragile prayer-forward)** — heavy corpse-eat (13×), prays freely
  (short timeout), cautious dive D5@T1109; BUC-detect is innate (no altar).
  *cite: DaveT.*

### WIELD is confirmed a non-event (corroborates the s13 WIELD null)
0 in-inventory wield-upgrades across the corpus — every expert stayed
weapon-optimal from turn 1 (Wizard's only "wield" was a found pick-axe for
digging, not combat). Independent demonstration confirmation of the s13
finding that roles start weapon-optimal.

---

## THE HONEST FINDING (the reason this matters)

**The per-class expert early-game routine, decomposed, is ENTIRELY a subset of
levers the program has ALREADY built and tested** — NH_FOODACQ, NH_PET,
NH_RANGED, NH_ELBERETH, NH_CAST, NH_PACE, NH_ANTIFAINT, prayer. There is no
un-built "secret opener." Each of these was individually null-to-directional;
the FULLY-STACKED arm is NEGATIVE (levers interact badly combined).

So E37 tests the one remaining un-tested composition: give each rolled class
ONLY the small lever-subset ITS experts use, class-tuned (NH_OPENING, the
per-class OPENING CARDS in e37_opening.py). This is a genuinely different
hypothesis from "test each lever globally" (done, null) and "stack everything"
(done, negative): does CLASS-TAILORED stacking escape the negative interaction?

### Validation (role-stratified paired blocks; REF = frozen C2.1, TEST = REF +
class card; one seed per process; PRIMARY KPIs = progression, survival@D5, and
CRISIS-ENTRY RATE — the preventive "did we avoid the 0-survivor band" KPI).

**WIZARD (n=5, FIRST TRANCHE — underpowered):**
- progression Δ **−0.008**; depth_max Δ **−1.0**; surv@D5 Δ **−0.20** (100%→80%);
  crisis_entries Δ 0.0; min_hpfrac Δ **+0.018** (a tiny preventive HP buffer).
- **Behavioral divergence 5/5 pairs** (cast 0→5-14 every seed, corpse-bank
  active): the card FIRES LIVE and changes behavior massively — it is NOT a
  mechanical null (the E36 signature-fidelity trap is avoided). Yet it does not
  move the mean; the multi-lever stack (esp. NH_PACE cautious-descent + cast
  risk) REGRESSES depth on 2/5 seeds (860 D7→D3, 847 D6→D5) and helps 0/5.
- Reads exactly like the NH-E13 Healer wiki playbook (−0.62) and the
  "stacked-arm-negative" law: class-tailoring did NOT rescue the Wizard stack.

**SAMURAI (n=5, FIRST TRANCHE — lighter card, no pace-defer/cast):** in progress
— early seeds show the lighter subset is less depth-costly (seed 801 D2→D4,
foodacq firing) — see PROGRAM_FINDINGS / HANDOFF for the completed block.

### THE READ (honest, per the operator's "RELIABLE" ask)
- The reliable buffer experts build is PREVENTIVE (never enter the crisis:
  corpse-bank nutrition, throw before contact, pet-tank, Elbereth-break,
  cautious tempo). Our agent HAS every one of these behaviors, and NH_OPENING
  makes them fire live per class — but on the mean they are null-to-negative
  at our action-space/budget: firing the expert routine changes behavior
  dramatically and buys a little survival-time / HP buffer, WITHOUT moving
  progression, and the heavier stacks regress depth.
- The evidence is converging on the deepest honest conclusion: **even human-
  optimal, demonstration-derived, class-tailored early play does not move our
  mean** — the gap to experts is not a missing OPENING (we have the pieces) but
  the CAPABILITY to execute them well under the benchmark's constraints
  (acquisition/capability-bound, PROGRAM_FINDINGS 11 angles). Where a lighter,
  depth-neutral subset exists (Samurai), it is the only candidate that could be
  mean-neutral-with-a-buffer; the confirmatory n≥15 block decides it.

BAKED classes (compiled cards, default-OFF, bit-identical): **Wizard, Samurai,
Priest** (`baked: True`). Exploratory cards: Caveman, Knight, Priestess.

---

## HANDOFF — confirmatory blocks (box-saturation-deferred)

This session ran first tranches only (Wizard n=5 DONE = clear negative; Samurai
n=5 partial — box saturated by the parallel E36 agent, ~240s/episode). The
mechanism is proven (cards fire live, 5/5 behavioral divergence). To confirm:

RECIPE (run on an UNSATURATED box; SERIAL, one-seed-per-process, the VM-contention law):
```
cd /data/doh/teams/researchy/work/fable_nethack   # PYTHONPATH=pylib
# per baked class, n>=15 role-stratified paired (REF=C2.1, TEST=+class card):
PYTHONPATH=pylib python3 e37_run_opening.py --class Wizard  --n 15 --cap 2000 --out results/e37_wizard.jsonl
PYTHONPATH=pylib python3 e37_run_opening.py --class Samurai --n 15 --cap 2000 --out results/e37_samurai.jsonl
PYTHONPATH=pylib python3 e37_run_opening.py --class Priest  --n 15 --cap 2000 --out results/e37_priest.jsonl
# analysis (progression / surv@D5 / crisis-entry deltas + behavioral divergence + sign split):
PYTHONPATH=pylib python3 e37_run_opening.py --analyze results/e37_wizard.jsonl
```
Blocks are RESUMABLE (skip (seed,arm) already in the JSONL). Priest census is
thin (n=3 Priest + 11 Priestess) — pool Priest+Priestess for n>=15, or lean on
Priestess (same card).

OPEN QUESTIONS for the confirmatory:
1. Does the LIGHTER Samurai card (ranged+foodacq+elbereth, no pace-defer/cast)
   stay depth-NEUTRAL where the heavier Wizard card regressed −1.0 depth? Seed
   801 (D2→D4) is the one encouraging signal. If Samurai is mean-neutral with a
   min-HP buffer, that is the closest thing to "reliable" E37 found — and it
   would say: drop NH_PACE-defer and cast-risk from cards, keep only the
   depth-free preventive buffers (foodacq + elbereth).
2. Is NH_RANGED actually firing for Samurai? (seed 801 fp_throw=0 in both arms —
   the ranged component may be a partial null; verify ammo availability / that
   the throw path triggers, else drop it from the card.)

[GAP] ACQUISITIONS (priority next session): Valkyrie, Barbarian, Tourist, Healer.
FETCH RECIPE (verified this session): gamesday.php dumplog → role → plr.php
ttyrec index → curl the largest recent .ttyrec into ttyrecs/; then
`python3 e37_extract.py --json results/e37_extract.json`. Valkyrie especially
(the canonical strong-class rush — the "reliable" strong opener to demonstrate).

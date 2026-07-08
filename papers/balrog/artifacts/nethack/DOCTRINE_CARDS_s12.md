# Doctrine Cards — Phase L session 12 (claude-opus-4-8 [max thinking])

Runtime identity VERIFIED at open: system-prompt model id = claude-opus-4-8,
max thinking; Fable at usage cap. All s12 artifacts stamped claude-opus-4-8[max].
Fork aleph/fable-nethack. Session = build + validate the FIRST COMBAT-SURVIVAL
resource lever (the s11-unmasked binding constraint), tested ON TOP of the s11
hunger fix, plus the FOODACQ n≈30 confirmatory.

---

## CARD S12-1 — PET UTILIZATION: PRESERVE-THE-PET-ON-DESCENT (rule [PET_FOLLOW], flag NH_PET)  [VERDICT: DIRECTIONAL-but-NULL on combat survival; mechanism confirmed but narrow. Ship flag-OFF scaffold.]
provenance: insight-origin=OP (DEATH_TO_CAPABILITY Tier-2 PET UTILIZATION, zero
prior use) + knowledge=our own s11 STACKED-DEATH-CLASSES finding (combat is the
binding layer once hunger is fixed). layer: LOGISTICS/COMBAT. model: claude-opus-4-8[max].

**What was built.** NH_PET = before taking the down-stairs, if a live pet is on
the level but NOT adjacent, and it's safe (no adjacent hostile), and the pet is
within PET_WAIT_RADIUS (default 5), WAIT (search) a BOUNDED number of turns
(PET_WAIT_MAX, default 8, tracked per stair cell) for the pet to reach an adjacent
cell so it FOLLOWS us down (a pet descends only if adjacent when '>' is taken).
Preserves the starting pet across the descent so it keeps tanking/killing the
D2-6 trash that is the newly-unmasked combat death-class. Single injection point
in `_descend` at the terminal `return "down"`; helpers `_live_pet` /
`_pet_follow_wait`. Flag-off bit-identical (C2_ANY False when NH_PET unset;
`_pet_follow_wait` returns None immediately). Bounded per-stair + radius-gated so
a far/stuck pet cannot stall descent (the FOODACQ-stall lesson, CARD S11-2).

**THE MECHANISM SURPRISE (defines the result).** Pets already follow NATIVELY
when adjacent — NetHack's own rule, independent of our code. So the lever's
counterfactual is NARROW: it only adds value when the pet is 2-5 cells away at the
stairs (REF abandons it; TEST waits). On the majority of seeds the pet is already
adjacent at the '>' → petw=0 → the pet follows for free in BOTH arms → REF≡TEST.
petw=0 does NOT mean the pet was abandoned; it means the wait was unnecessary.

**Result — cd=8 FOODACQ baseline carried in BOTH arms (testing combat ON TOP of
the hunger fix), n=17 paired trash-melee-death seeds, cap 2000, one-seed-per-
process. REF=C2.1+NH_FOODACQ+NH_ANTIFAINT vs TEST=REF+NH_PET; results/pet_block.jsonl:**
- **Combat-death rate: REF 15/17=0.882 → TEST 14/17=0.824, Δ −0.059** (1 improved
  / 0 regressed; McNemar 1 discordant pair — directional, not significant).
- **Progression mean: REF 0.0283 → TEST 0.0314, Δ +0.00305, 95% paired-bootstrap
  CI [−0.00157, +0.00998] — INCLUDES 0. NULL on the mean.**
- **Depth mean: REF 4.18 → TEST 4.35, Δ +0.18, CI [−0.53, +0.94] — includes 0.**
- **Mechanism CONFIRMED but doesn't propagate: pet-waits fired on 8/17 seeds; pet
  preserved DEEPER (pdmax TEST>REF) on 6/17.** Where it fired big it helped
  (seed 16 Cavewoman depth 3→8 +5; seed 706 Priest 3→5 +2; seed 21 Priestess
  +1) — but the agent still combat-died at the reached depth.
- **HIGH VARIANCE / the wait REGRESSES some seeds:** seed 746 Healer depth 5→2
  (−3, 8 waits); 115/739 −1 each. Waiting near the stairs for the pet trades
  against progression exactly as FOODACQ's banking-rate did (S11-2, same knob
  shape). The gains (16:+5, 706:+2) and the losses (746:−3) net to a wash.
- **Zero new death classes.** All TEST deaths ordinary trash/combat; flag-off
  bit-identical.

**Verdict: the cleanest, zero-risk pet lever (preserve-on-descent) is INERT on
combat survival — a 10th converging angle on capability-boundedness, now at the
COMBAT layer.** The pet-follow MECHANISM works (preserves the pet deeper on 6/17)
but does NOT move combat survival, because the binding constraint is not the pet's
PRESENCE (pets follow natively when adjacent) but the agent+pet COMBAT CAPABILITY
against the same trash: the pet loses the same attrition the agent loses, and dies
to the same monsters. Preserving a capability-bound resource is inert. Peeling s11's
hunger layer off exposed combat; peeling combat's "pet-present" sub-layer exposes
combat CAPABILITY (win-the-fight / take-fewer-hits) as the true binding constraint —
the mean did not move, it unmasked yet another constraint one layer deeper, exactly
the stacked-death-classes law (s11) continuing to hold.

**Regression/ship.** flag-off bit-identical (C2_ANY False verified). Defaults
PET_WAIT_MAX=8, PET_WAIT_RADIUS=5 baked in. Ships DEFAULT-OFF (matching the
ANTIFAINT/FOODACQ scaffold precedent). The next combat lever to try is the
CAPABILITY side, not the presence side: WIELD UPGRADE (zero wield actions ever —
win fights in fewer rounds = fewer incoming hits) and SAFE EARLY LEVELING (arrive
at the D5-6 kill-zone at xp 5+ instead of xp 1-3). PET UTILIZATION's remaining
untried headroom is the COMBAT-positioning form (position so the pet tanks; don't
outrun it in travel) — but that is a large, pet-AI-coupled, high-regression build,
not the clean preserve-on-descent form tested here.

**Replication recipe:** `NH_STEPCAP=2000 ./run_pet_block.sh results/pet_block.jsonl
<seeds...>` (PYTHONPATH=pylib, one-seed-per-process, SERIAL; REF=C2.1+FOODACQ+
ANTIFAINT vs TEST=+NH_PET). Trash-melee death seeds mined from the corpus via the
final-frame "Killed by <trash>" scan (144 candidates); block used 4/16/21/37/104/
111/115/702/706/720/721/739/746/761/766/4031/4054 (709 timed out, excluded).
Analyze with the paired-bootstrap block in the s12 log.

**KPI-DASH — per-role (PET block, TEST=+NH_PET vs REF, n=17):**
```
role        n  Δdepth_mean  petw_tot  pet_preserved_deeper
Cavewoman   1     +5.00         4          0/1     <- big gain (deepest run)
Priest      1     +2.00        12          1/1
Priestess   1     +1.00        12          1/1
Wizard      2     -0.50         4          2/2
Barbarian   1     -1.00         3          1/1
Healer      2     -1.50        11          1/2     <- the 746 regression (5->2)
Knight      3     +0.00         0          0/3     <- pet paces natively (petw=0)
Monk        1     +0.00         0          0/1     <- "
Ranger      1     +0.00         0          0/1     <- "
Rogue       2     +0.00         0          0/2     <- "
Tourist     2     +0.00         0          0/2     <- "
```
The lever ONLY touches the 6 roles whose pets LAG at the stairs (fire petw>0);
the 5 roles whose pets keep pace natively (Knight/Monk/Ranger/Rogue/Tourist) are
bit-identical (petw=0, Δ0). Among the affected roles the sign is MIXED (Cavewoman
+5, Priest +2 vs Healer −1.5, Barbarian −1) — the gains net against the losses to
the null. This is the mechanism made role-legible: the counterfactual is narrow AND
capability-bound.

---

## CARD S12-2 — FOODACQ(cd=8) n≈30 CONFIRMATORY  [ATTEMPTED, BLOCKED by episode wall-time this session — carry to s13]
provenance: s11 CARD S11-1 follow-up (push the fainting-incidence CI clear of 0;
s11 was Δ −0.267, 95% CI [−0.533, +0.000], McNemar p=0.22 at n=15). Same pre-
registered design; 15 fresh fainting seeds mined (peak hunger tier >= Fainting,
not in the original block): 715 716 717 722 726 728 731 733 734 745 752 772 774
778 825 (43-seed fresh corpus available — see s12 log mining scan).
**BLOCKED: under s12 VM load, cap-2000 FAINTING-corpus episodes do NOT terminate
early — the REF arm (no FOODACQ) frequently reaches ~step 2000 WITHOUT dying and
truncates, and each such episode exceeds the runner's 280s per-episode timeout →
recorded TIMEOUT_OR_FAIL, unusable.** (715 timed out both arms; 716 REF truncated
at 2000 having only reached Hungry.) The hunger corpus is the SLOWEST episode
class (survivors run the full cap); the trash-melee combat corpus used for the PET
block dies fast (~150-400 steps) so those blocks completed. Fix for s13: raise the
per-episode timeout to ~500s in run_foodacq_block.sh (accept ~4-5 min/episode) and
run in small chunks off-peak, OR lower cap to ~1600 (fainting first appears ~turn
1400 so >=1500 preserves the KPI). Replication once unblocked:
`NH_STEPCAP=2000 NH_FOODACQ_COOLDOWN=8 ./run_foodacq_block.sh
results/foodacq_cd8_confirm.jsonl <fresh seeds...>`; combine with foodacq_cd8.jsonl.
The s11 result (Δ −0.267, CI [−0.533,+0.000]) therefore stands UNCONFIRMED at 95%.

---

## Session queue for s13
1. **WIELD UPGRADE (NH_WIELD)** — the CAPABILITY-side combat lever (PET tested the
   presence side, inert). Zero wield actions ever; wield the best available weapon
   (character sheet counterfactual_power ranks them) → win fights in fewer rounds →
   fewer incoming hits. Pair with FOODACQ baseline; measure combat-death + mean.
2. **SAFE EARLY LEVELING** — arrive at the D5-6 kill-zone at xp 5+ (targeted safe
   kills with pet help / at range), not the failed XP-pace-gate.
3. If both capability-side combat levers also come back null → the combat layer is
   capability-bound like the decision layer (0-for-7), and DEMONSTRATION LEARNING
   (expert ttyrec capability injection) becomes the only qualitatively-different
   remaining mean-lever, as flagged in s11.
4. PET COMBAT-positioning form (tank/don't-outrun) — larger build, deferred.
5. MILESTONE GIF for a seed where the preserved pet visibly changes the run (seed
   16: depth 3→8 with the pet) — only if it reads as a clean pet-saves-run reel.

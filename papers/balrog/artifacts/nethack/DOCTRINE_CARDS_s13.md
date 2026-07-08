# Doctrine Cards — Phase L session 13 (claude-opus-4-8 [max thinking])

Runtime identity VERIFIED at open: system-prompt model id = claude-opus-4-8,
max thinking; Fable at usage cap. All s13 artifacts stamped claude-opus-4-8[max].
Fork aleph/fable-nethack. Session = build + validate the WIELD UPGRADE lever
(direct combat-CAPABILITY injection, the s12 PET-null redirect), diagnose WHY it
never fires, and resolve whether capability-injection can move the mean.

---

## CARD S13-1 — WIELD UPGRADE (rule [WIELD_BEST], flag NH_WIELD)  [VERDICT: MECHANICAL NULL — the in-inventory counterfactual is PROVABLY EMPTY; roles start optimally wielded. Ship flag-OFF scaffold.]
provenance: insight-origin=OP (DEATH_TO_CAPABILITY, "combat power at our depth" =
the binding constraint; zero wield actions EVER in program history) + our own s12
PET null (presence side inert -> try the CAPABILITY side). layer: COMBAT/CAPABILITY.
model: claude-opus-4-8[max].

**What was built.** NH_WIELD = before a non-crisis turn, if a CARRIED (not-wielded)
NON-thrown weapon's melee dpt beats the current wielded (or unarmed) dpt by
WIELD_MARGIN (default 0.5) and it is safe (no adjacent hostile -> never caught
mid-swap weaponless), wield it. dpt from the nh_sheet character sheet
(attack_options / counterfactual_power). Monk excluded (martial arts > early
weapons); thrown-primary weapons (darts/daggers) excluded so we don't disarm the
ranged game. Single injection in `_decide` (helper `_wield_upgrade`); the wield
grammar (`What do you want to wield? [- a or ?*]`) is a direct letter prompt, so
`queue=[letter]` answers it (snapshot fixture `wield_grammar.json`). Flag-off
bit-identical (C2_ANY False when unset).

**THE MECHANISM SURPRISE (defines the result): the counterfactual is EMPTY.**
A broad probe (77 role-episodes, ALL 15 roles, low dev seeds + the fainting
corpus) found **ZERO in-inventory wield-upgrades** (margin >=0.5): every NetHack
role starts wielding its best in-inventory melee weapon (Knight long sword 3.04,
Barbarian two-handed sword 4.39, Valkyrie long sword, Samurai katana 3.71, Wizard
quarterstaff 2.01, Healer scalpel 1.15, ...); Monk/Tourist are best unarmed and
carry only throwing darts (worse in melee than unarmed). So "wield the best
weapon" injects NOTHING from inventory — there is no starting-vs-available gap.

**Result — n=17 paired trash-melee-death seeds, cap 2000, one-seed-per-process,
per-episode timeout 500s; REF=C2.1+FOODACQ+ANTIFAINT vs TEST=REF+NH_WIELD
(+read-only NH_WIELD_DIAG); results/wield_block.jsonl:**
- **PROGRESSION MEAN: REF 2.8305 -> TEST 2.8305, Δ +0.0000, 95% paired-bootstrap
  CI [+0.0000, +0.0000] — a MECHANICAL null.**
- **wield-fires total: 0. bit-identical pairs: 17/17.** Cleaner than the s12 PET
  null (which had a discordant pair): the lever cannot fire, so TEST ≡ REF exactly.
- combat-death 15/17 -> 15/17 (Δ 0); depth mean 4.18 -> 4.18 (Δ 0).

**Verdict: direct combat-capability injection via wielding is NOT CONSTRUCTIBLE
in-inventory — the 11th converging angle on capability-boundedness.** The lever
the findings said SHOULD move the mean (address combat power directly) has a
provably empty counterfactual because roles start weapon-optimal. This REFINES the
law: capability injection can only inject capability that EXISTS and is UNUSED. The
one CI-positive lever in the program (teach the Wizard to cast, +2.41) worked
because casting was unused capability; wielding has NO unused capability to inject.
The only honest ways to add combat power are (i) ACQUIRE a better weapon
(resource-logistics -> see S13-2) or (ii) gift one (forbidden by the honest-
observation contract). NH_WIELD ships DEFAULT-OFF as a validated, mechanism-correct
scaffold (fires on a synthetic scalpel+long-sword inventory: dpt 1.25->2.81).

**Replication:** `NH_STEPCAP=2000 NH_EP_TIMEOUT=500 ./run_wield_block.sh
results/wield_block.jsonl <seeds...>` (PYTHONPATH=pylib, one-seed-per-process,
SERIAL; TEST=+NH_WIELD+NH_WIELD_DIAG). Analyze: `python3 analyze_wield.py
results/wield_block.jsonl`. Corpus = the s12 trash-melee-death seeds 4/16/21/37/
104/111/115/702/706/720/721/739/746/761/766/4031/4054. Broad counterfactual probe:
scratchpad/probe_wield_broad.py (77 role-episodes, 0 upgrades).

---

## CARD S13-2 — THE ZERO-FIRE DIAGNOSIS + WEAPON ACQUISITION (flag NH_WIELDACQ)  [VERDICT: the mean is ACQUISITION-BOUND. Adding loot behavior fails to complete AND re-triggers the FOODACQ descent-stall. Ship flag-OFF.]
provenance: coordinator redirect (distinguish why wield_fires=0: (a) acquisition-
bound / (b) threshold / (c) already-optimal) + our own S11-2 stall lesson.
layer: RESOURCE-LOGISTICS / ACQUISITION. model: claude-opus-4-8[max].

**The read-only diagnosis (NH_WIELD_DIAG).** Each cycle, scan the served glyphs
for WEAPON_CLASS objects on the floor, price each via the sheet, and track the best
floor-weapon dpt seen vs current wielded dpt. Pure observation -> arms stay
bit-identical. Per-episode outputs: best_floor_weapon (name, dpt), and
floor_upgrade_steps (steps a floor weapon beat current by the margin).

**Result (13 seeds with DIAG data):**
- **NOT (b) threshold.** Where an upgrade exists it is FAR above margin (mace +1.44,
  flail +1.49, two-handed sword +1.35) — tuning the margin changes nothing.
- **(c) already-optimal / floor-junk — 8/13.** Well-armed roles: either no floor
  weapon in view (5) or the floor weapon is WORSE than the starting weapon (3:
  elven dagger 1.80, orcish dagger 1.45, knife 1.45 — all < the role's start).
- **(a) ACQUISITION-BOUND — 3-5/13, DEMONSTRATED.** A genuine upgrade lies on the
  floor, in view for many steps, and the agent NEVER takes it:
  - **seed 746 Healer: a MACE (scalpel 1.15 -> 2.59, +1.44) in view 25+ steps.**
  - **seed 4054 Ranger: a FLAIL (dagger 1.44 -> 2.93) in view 100 steps.**
  - **seed 721 Knight: a two-handed sword (3.04 -> 4.39) in view 5 steps.**
  Root cause: `item_targets` values only food/ammo/armor — **floor weapons are
  literally invisible to the agent's loot policy.** The agent has the wield
  mechanism but no weapon-ACQUISITION behavior — the EXACT parallel to the s10
  anti-faint null ("reaches Hungry with an empty larder — no food to eat").

**The pivot (NH_WIELDACQ): build the missing loot behavior.** Detour up to
WIELDACQ_RADIUS (8) to a floor weapon that upgrades melee, pick it up (then NH_WIELD
wields it). Melee-only (ammo/thrown excluded), bounded detour + loot_tries cap =
the S11-2 no-stall discipline. **Tested on seed 746 (the mace):**
- **The acquisition FIRES (11 walk-toward-mace steps) but the pickup NEVER
  COMPLETES (wieldacq_fires=0).** The agent reaches (8,6), adjacent to the mace at
  (7,6), and bumps "west" repeatedly without moving — its terrain model marks the
  mace cell as a WALL (terrain=2), so the item-on-perceived-wall cell is
  unwalkable-into; after the loot cap it abandons the mace.
- **The detour STALLS descent: end_reason DEATH@D5 (REF) -> RUNNER_TRUNCATED@2000
  (TEST), depth 5, zero descent.** The identical banking-rate-vs-progression knob
  tension as FOODACQ (S11-2): the acquisition detour trades against descent.

**Verdict — THE UNIFYING META-FINDING: the NetHack mean is ACQUISITION-BOUND.**
Both the #1 killer (hunger, s10-11) and the newly-unmasked binding constraint
(combat, s12-13) are gated by the SAME missing behavior: the agent has the
mechanisms to USE capability (eat / wield / cast) but not the behavior to reliably
ACQUIRE it (loot food / weapons / gear off the floor). And when acquisition IS
bolted on, it (i) hits perception edges (item-on-perceived-wall) and (ii)
re-triggers the descent-stall trade-off — so acquisition is NOT a free mean-mover;
the constraint recurses. This subsumes the capability-boundedness law: capability
injection requires acquisition, acquisition is the missing behavior, and acquisition
costs progression. NH_WIELDACQ ships DEFAULT-OFF (bit-identical). The real Tier-1
lever is now a GENERAL, progression-safe item-acquisition policy (a floor-weapon/
armor/food perceptor + underfoot-first, no-detour looting on the FOODACQ cd=8
model) so that wield/wear/eat fire on what is acquired — with a regression gate on
descent depth (the S11-2 confound).

**Replication:** DIAG in every TEST arm of run_wield_block.sh (NH_WIELD_DIAG=1);
pivot test `NH_WIELDACQ=1 NH_WIELD=1 ... python3 e35_antifaint_smoke.py TEST 746`.
Blocker trace: scratchpad/dbg746b.py (glyph@(7,6)=mace, terrain=2, "west" bumps).

---

## Session queue for s14
1. **GENERAL ITEM-ACQUISITION policy** (the meta-finding's lever): extend the floor
   perceptor to weapons (+ keep armor/food), loot underfoot-first (no detour, cd
   rate-limit) so wield/wear/eat fire on acquisitions; REGRESSION-gate on descent
   depth (S11-2). Fix the item-on-perceived-wall pickup edge (terrain belief vs a
   real floor item) first — it blocked the s13 pivot.
2. **SAFE EARLY LEVELING** (the OTHER unused-capability lever wield pointed to): XP/
   skill IS unused capability the agent can gain; arrive at the D5-6 kill-zone at
   xp>=5 via targeted safe kills (at range / with pet), not the failed XP-pace-gate.
3. **FOODACQ n≈30 confirmatory** — still open from s11/s12 (fainting CI [−0.533,0],
   p=0.22); now unblocked (run_foodacq_block.sh timeout raised to 500s / cap<=1600).
4. If acquisition + safe-XP also come back null -> DEMONSTRATION LEARNING (expert
   ttyrec capability injection) is the last qualitatively-different mean-lever.

# CAPABILITY MAP — death classes × untouched capability families (operator directive 2026-07-07)

MODEL: Fable 5 (max reasoning) — initial construction. Cell verdicts stamped with their producing model as they land.

**This map IS the Phase L battle plan.** Rows = death classes with their
counterfactual ceiling deltas (E-NH1, v1.1 n=80 block). Columns = capability
families the action audit showed as never used (50/248 actions ever;
cast/zap/quaff/read/fire/wield/puton = 0). Cell = expected relevance +
lab-scenario status (NH-E20) + evidence. Fill % (resolved relevant cells /
relevant cells) is a Phase-L progress metric tracked in PHASE_L_REPORT.md.

Cell states: `—` not plausibly relevant · `HYP` hypothesized relevant (basis
noted) · `AUTH` lab scenario authored · `RUN` lab run, verdict pending ·
`WIN/LOSE` lab verdict · `XFER` NetHack dev transfer-check passed · `SHIP`
in a role profile.

| death class (ceiling Δ) | cast (Force Bolt / heal) | zap (wands) | quaff (potions) | read (scrolls) | fire/throw doctrine | wield upgrades | armor economy | Elbereth-alternatives |
|---|---|---|---|---|---|---|---|---|
| MELEE_TRASH (+4.88, 31 d) | HYP — kill speed-15+ trash before contact; Wizard block mean 2.09 is the headroom case | HYP — striking/sleep wands as burst | HYP — healing potions vs the 57/66 attrition deaths | HYP — teleport = escape from pack corners | HYP — soften packs pre-contact (dropped C2 impl was flat; retry with doctrine) | HYP — starting dagger at D8 is the audit's indictment | HYP — AC never upgraded in v1.1 trajectories | HYP — pre-emptive carve before rest (multi-turn cost carded) |
| MELEE_OTHER (+2.09, 13 d) | HYP — Force Bolt d6+ per cast, fail%-gated | HYP | HYP — !oGL/healing mid-fight | HYP — remove curse rarely; teleport escape | HYP | HYP — best-found weapon vs dwarf king etc. | HYP | — |
| SPIDER_ANT (+1.92, 10 d) | HYP — kill-before-contact is THE answer to speed-18 poison | HYP — sleep/striking | HYP — cure sickness class | — | HYP — primary historical counter, needs ammo economy | HYP | HYP | — |
| STARVATION (+1.40, 14 d) | — (Pw is not food) | — | HYP — fruit juice marginal | — | — | — | — | — |
| PRAY_DEATH (+0.51, 5 d) | HYP — Healer heal-self replaces desperation prayer | HYP | HYP — healing potion before prayer window | — | — | — | — | HYP |
| RANGED (+0.40, 4 d) | HYP — outrange the wand-zapper | HYP — return fire | — | — | HYP | — | HYP — AC vs bolts | — |
| EXPLODE/SLEEP/TRAP (+0.33) | — | — | — | HYP — magic mapping vs traps marginal | — | — | — | — |

**Reading the expected structure (operator):** Force Bolt → MELEE_TRASH +
SPIDER_ANT (kill before contact); healing/quaff → the 57/66 attrition deaths;
wand zaps → RANGED standoffs + emergencies; scrolls (teleport, remove curse) →
escape class; wield/armor → all melee rows multiplicatively.

**Fill protocol:** each HYP cell resolves via (1) NH-E16 branch-probe (verb
grammar + effect observed in real env), (2) NH-E20 lab tournament (n=50+
controlled), (3) NetHack dev transfer check (paired block) — then WIN cells
ship into role profiles (NH-E14) and the row's remaining ceiling is
re-estimated. Verdicts recorded here + ledger + report.

**Status 2026-07-07:** 0/34 relevant cells resolved (map just built).
Priority per operator: spellcast doctrine column + D5-6 melee rows first.

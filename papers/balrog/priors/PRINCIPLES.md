# PRINCIPLES.md — v0.1 (NH-E19; the intuition layer's judgment substrate)

MODEL: Fable 5 (max reasoning) — file created; per-principle provenance below.
Discipline: prose twin of rule cards. Evidence in → revision logged.
Invalidated principles are struck through (~~like this~~) with the refuting
data cited — invalidations stay visible. This file ships IN the strategist
prompt (Arm B / reflection passes) and is a first-class NH-E17 rebuild input.

DEFEASIBILITY (operator 2026-07-07): every principle here is a defeasible
heuristic — "generally true", suspendable by the intuition layer under the
override protocol (explicit, justified, bounded by a retrieved memory's bound,
logged + outcome-tracked). Hard vetoes are a separate non-overridable tier.
See NH-E19 §5.

Format per principle: statement · rationale+evidence · status
(hypothesized / validated / invalidated) · provenance (who authored) ·
validation plan.

---

**P1 — LEVEL SELF UP BEFORE GOING DOWN.** Don't descend while under-leveled
for the next floor's threat band.
Evidence context: the D5–6 kill zone is xp1–3 characters meeting speed-15+
mobs; the ceiling table's +4.88 lives exactly there (C2 report §E-NH1).
TENSION to resolve honestly: the earlier XP-pace-gate HURT the dig-diver —
expect a role-split verdict (diggers exempt: their strategy IS skipping the
fight; walkers/fragile roles likely benefit).
Status: hypothesized. Provenance: operator-prior (2026-07-07), Fable 5
transcription. Validation: per-role threat-band thresholds (xp/HP floor per
depth) swept in the E20 lab + per-role dev blocks.

**P2 — WIELD THE MOST POWERFUL WEAPON AVAILABLE.** The action audit shows
ZERO wield actions ever; we fight D8 monsters with starting daggers.
Status: hypothesized (mechanism near-certain, magnitude unknown).
Provenance: operator-prior. Validation: weapon-value perceptor + wield-upgrade
rule; E20 lab test: same fights, starting weapon vs best-found.

**P3 — WEAR THE MOST POWERFUL ARMOR AVAILABLE.** Armor economy, unblocked
post armor-under-@ fix (C2 bug #5); v1.1 AC trajectories show armor
essentially never upgraded after start.
Status: hypothesized (ARMOR lever shipped +0.67 weak-positive with 7/20 wear
fires; doctrine version untested). Provenance: operator-prior. Validation:
AC-delta per episode + paired dev.

**P4 — ENTER EACH FLOOR AT MAXIMUM AVAILABLE READINESS.** HP rested to
threshold, best gear equipped, food stocked, escape option known.
(Generalization of P1–P3.) Becomes a PREP state in the NH-E15 state machine:
the descend transition checks a role-conditioned readiness gate.
Status: hypothesized. Provenance: operator-prior. Validation: readiness gate
in E15 + readiness-deficit metric at death (NH-E12 backtrace) trending down
without descent-rate collapse (starvation guard: descent-stall is the known
failure mode of over-prep — 14/80 checkpoint deaths were starvation).

**P5 — BELOW HALF HP, NEVER TAKE A FIGHT YOU CAN WALK AWAY FROM.** 57/66
combat deaths spent their final stretch below 50% max HP — deaths are
attritional, entered at part health, not ambushes (C2 report §E-NH1).
Status: hypothesized (the flee gate exists; this extends it from
speed-feasibility to HP-policy). Provenance: Fable 5 from C2 forensics.
Validation: E20 lab (part-health fight-vs-walk tournaments) + avoidable-KITE
mass movement.

**P6 — A FRESH UNKNOWN MONSTER DESERVES ONE THROWN DAGGER BEFORE ANY MELEE.**
Probe-at-range converts novelty risk into information at one-item cost;
touch-effects are invisible in dpt stats until too late (chickatrice lesson,
dev seed 705).
Status: hypothesized. Provenance: Fable 5 from novelty-protocol design +
NH-E6. Validation: E20 novel-monster scenarios; metric = novel-species death
rate + info gained per probe.

**P7 — EVERY NEW CAPABILITY IMPORTS NEW COSTS.** When a verb ships, its full
resource ledger ships with it: Pw, NUTRITION, time, item consumption,
noise/aggro. The lab battery for any new verb must include a
resource-exhaustion scenario ("win the fight, then check what it cost").
Evidence: NH_CAST shipped on score alone; the operator spotted "too hungry to
cast" in the c22 GIFs within a day — casting Wizards run the hunger clock
faster than any historical agent while starvation was killer #1.
Status: validated-by-incident (the cost side; the doctrine fix is open work).
Provenance: operator (2026-07-07, GIF-reel observation), Fable 5 transcription.
Validation: CAST-HUNGER retro + paired dev of the eat-early doctrine; E20
resource-exhaustion scenarios for zap/quaff/read before those levers ship.

---

Change log:
- v0.1 2026-07-07: created with operator seeds P1–P4 + forensics-derived
  P5–P6. No validations yet; nothing in the strategist prompt is marked
  validated — the intuition layer must treat all as priors with cited
  evidence, not laws.
- v0.2 2026-07-07 (session 2): P7 added (capability-imports-costs; operator
  GIF observation of "too hungry to cast" in the c22 reel).

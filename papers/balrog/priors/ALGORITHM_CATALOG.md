# ALGORITHM_CATALOG.md — v0.1 (NH-E19 §2: the strategist knows its procedures)

MODEL: Fable 5 (max reasoning). Card format: what-for / preconditions /
failure modes / evidence. Selection logging + win-rate accumulation start
when the consultation loop consumes this file. Every card names its code
home so the NH-E17 rebuild can check completeness WITHOUT reading source.

**A1 — FRONTIER-EXPLORE (P9).** What-for: map acquisition, stairs/item
discovery. Mass-biased frontier targeting with persistence. Preconditions:
unexplored frontier reachable. Failure modes: far-loot thrash (fixed:
give-up counters), secret-door stalls (fixed: TOPO search rotation).
Evidence: core of every run since v1.

**A2 — DIG-DIVE (P7).** What-for: fastest depth when a digger is held
(score = depth). Preconditions: pick-axe/mattock; not held in shop.
Failure modes: digging into shops/water; bat-standoff interruptions
(NH-E15 fixture). Evidence: Archeologist role-lottery wins (per-role mean
14–16 in blocks).

**A3 — STAIRS-DESCEND with rest gate (P6/P7).** What-for: standard
descent. Preconditions: known '>' or holes. Failure modes: descending
under-ready (E12: 59% arrival-constraint deaths — P1/P4 open work).

**A4 — THRESHOLD-COMBAT (P5, v1.1 semantics).** What-for: melee when
threat-budget allows. Preconditions: attackable adjacent, not never-melee.
Failure modes: attrition entry at part-HP (57/66 deaths below-half final
stretch); pack fights in the open. Evidence: kept over expectimax (two
flat readouts dropped EXPMAX).

**A5 — CAST_ATTACK (P4.9, NH_CAST, V1.1).** What-for: no-miss kills for
casters; safe removal of never-melee blockers (floating eye). Preconds:
attack spell fail%≤20, Pw≥5·level, non-peaceful-class target
(CAST_NEVER). Failure modes: shopkeeper anger (guarded), Pw exhaustion.
Evidence: CAST-1 Wizard block +1.27/seed paired; guards exact-0.

**A6 — FLEE/DISENGAGE (P3 crisis + E15 L2).** What-for: survival when
losing. Preconditions: flee-feasibility (speed), escape route. Failure
modes: fleeing faster monsters (speed gate exists); corner traps.

**A7 — KITE-TO-CHOKE (topology perceptor; partially wired).** What-for:
pack fights — fight 1-wide. Preconditions: known choke cell reachable.
Failure modes: kiting through unexplored (ambush). Evidence: KITE = the
largest avoidable-damage mass in every audit (322/495 pts).

**A8 — REST-TO-HEAL (P6 gate + budget).** What-for: HP recovery before
descent/fights. Preconditions: no visible hunters, hunger ok, budget
left. Failure modes: resting into starvation clock; watchdog-exempted.

**A9 — PRAYER (emergency).** What-for: HP/starvation last resort.
Preconditions: pray_ok discipline (T>300, gaps≥1500, ≤3). Failure modes:
praying with hostile adjacent (PRAYFIX guards hunger prayers).

**A10 — THROW-AT-BLOCKER (P5.5).** What-for: removing never-melee
blockers at range. Preconditions: ammo, clear line. Failure modes: ammo
economy waste (throws_at counters).

**A11 — REPEAT-LAYOUT-STAIRS (P8.9, NH_REPEAT).** What-for: skip
exploration on repeated-layout levels (~20% of consecutive pairs).
Preconditions: ≥85% terrain match over ≥60 comparable cells with previous
level; prev stairs known. Failure modes: false-positive match (give-up
logic bounds cost). Evidence: REPEAT-1 block pending.

**A12 — FOOD-ECONOMY (FOOD2).** What-for: starvation-class reduction
(+1.12 shipped). Preconditions: floor food / safe corpses. Failure modes:
detour cost; shop food (guarded).

Not yet built (registered): SPRINT-THROUGH (option menus), BACKTRACK-FOR-
FOOD (R2 socket), ZAP (table ready), WIELD/ARMOR doctrine (P2/P3),
K-playout previews (DECIDE pattern), boss strats (E20 reps).

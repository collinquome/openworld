# THE KPI TREE — NetHack arm directional scoreboard

MODEL: claude-opus-4-8[1m] (max thinking), Phase L session 4. Operator
directive 2026-07-07 (via coordinator). Values backfilled from existing
instruments (c2_cache n=216, DEV label n=65; ledger DEV-B1/B2/B3; character
sheet live). Every value here is measured or cited — none asserted.

## The DAG

```
                     ┌─────────────────────────────────────────┐
   GOAL / NORTH STAR │ ASCENSION  (progression = 1.0)           │
                     │ proxy: block-mean progression / max-rung │
                     └──────────────────┬──────────────────────┘
                                        │
                 ┌──────────────────────┴───────────────────────┐
   UPSTREAM      │ DEPTH  (max-depth/episode; depth-over-time)   │
   DIRECTIONAL   └───────┬───────────────────────────┬──────────┘
                         │                            │
             ┌───────────┴──────────┐    ┌────────────┴───────────┐
             │ SURVIVAL-TO-DEPTH    │  × │ DESCENT RATE           │
             │ (hazard curve,       │    │ (turns/level)          │
             │  survival@D8)        │    └────────────┬───────────┘
             └───────────┬──────────┘                 │
                         │        the capability quartet (drivers)
       ┌─────────┬───────┴────────┬─────────────┬──────────────┐
       │ OFFENSE │ DEFENSE        │ SUSTAIN     │ NAVIGATION    │
       │ PI/DPS  │ AC + eff-HP    │ food/hunger │ stall/steps   │
       └─────────┴────────────────┴─────────────┴──────────────┘
                         ▲
   PERFORMANCE (strategy-testing layer — high-SNR, MOVES FIRST):
   avoidable-damage % · readiness-ratio@descent · verb-utilization ·
   retry/loop counts · recognition→correct-strat · firsts/episode
```

Read direction: a lever changes a PERFORMANCE or capability-quartet node
first (high SNR); DEPTH and the GOAL proxy move last and noisiest.

## Node table — instrument · current value · trend

| node | instrument | current value | trend |
|---|---|---|---|
| **GOAL proxy** | block-mean progression (dev) | **5.51** (DEV-B3 n=40) | 5.32→5.45→5.51 ↗ (ref beat-bar 6.8) |
| DEPTH | max-depth/episode (c2_cache DEV n=65) | mean **6.00**, median 5, max 15 | flat |
| SURVIVAL-TO-DEPTH | survival@Dk rate | **@D6 44.6% · @D8 32.3%** | flat (REST lever targets this) |
| DESCENT RATE | turns/level (depth_arrivals) | mean **139**, median 105 | flat |
| OFFENSE | power index / best-dpt (char sheet, live) | live per-ep (e.g. Ranger d2 PI 28.1, best-dpt 2.01) | new instrument (SHEET s3) |
| DEFENSE | final AC + eff-HP-frac (c2_cache) | AC mean **7.1** · dies at **35% HP** | AC flat; armor-table AC fixed s4 |
| SUSTAIN | hunger-death rate; food stock-turns | **3/40 = 7.5%** (DEV-B3) | 10→5→3 ↘ (CASTHUNGER+E15) |
| NAVIGATION | stall-watchdog fire rate; steps-to-stairs | wd **22/40 = 55%** (E15-1) | new (E15 s3) |
| avoidable-damage % | c2_avoid (PRIMARY dev metric) | **5%** (DEV-B2/B3) | 10→8→6→5→5 ↘ criterion-iii MET |
| readiness-ratio@descent | char sheet RR at stair-descent | live per-ep (RR>1 = win exchange) | new (SHEET s3) |
| verb-utilization | action audit | 50/248 baseline; cast/zap now >0 | ↗ (CAST shipped) |
| firsts/episode | store.first (kill/verb/depth) | live | new (E18 s3) |

Death-shape read (DEV n=65): agents die at ~35% HP having descended to a
median D5 — i.e. killed *in* an exchange, not ground down to 0 over time.
This is why SURVIVAL-TO-DEPTH (not SUSTAIN) is the REST-lever's proximal
node: the win is disengaging the losing exchange, not out-healing it.

## The rule: every lever declares its PROXIMAL KPI at pre-registration

Validation reads the **proximal KPI primarily**, block mean secondarily.
The proximal node is the ONE node the lever should move first; the terminal
mean is the last, noisiest thing to move. Pre-registration must name it.

| lever | proximal KPI (moves first) | secondary | terminal (last) |
|---|---|---|---|
| REST / disengage | SURVIVAL-TO-DEPTH via **TRASH-death rate** | avoidable-dmg % | block mean prog |
| WIELD doctrine | **OFFENSE (PI / best-dpt)** | MELEE+ survival | block mean prog |
| ARMOR doctrine | **DEFENSE (effective HP via AC)** | survival@Dk | block mean prog |
| ZAP doctrine | OFFENSE (ranged dpt) + RAY_BOUNCE safety | RANGED survival | block mean prog |
| KITE-to-choke | avoidable-dmg % (KITE mass) | SPIDANT/TRASH survival | block mean prog |

## Per-block dashboard (directive req 3)

Each dev/scored block close appends a one-line KPI snapshot to RUN_LOG.txt
and the report, with trend arrows vs the prior block. Template:

```
KPI-DASH <block>: prog <mean> | maxD <mean> | surv@D8 <%> | descent <t/lvl>
  | avoid <%> | hunger <n/N> | AC <mean> | wd <n/N> | <proximal-KPI of the
  block's lever, if any>
```

Backfill anchor (DEV-B3 close, standing config): prog 5.51 | maxD ~6.0 |
surv@D8 32.3% | descent 139 t/lvl | avoid 5% | hunger 3/40 | AC 7.1 | wd 22/40.

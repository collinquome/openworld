# NH-E12 — Death retrospectives (REGISTERED, Phase L + backfill)

Per-death artifact: {class, depth/role/turn, avoidability verdict, LESSON typed as TACTICAL RULE | ARRIVAL CONSTRAINT | NO-LESSON-DICE, gym evidence, status}. NO-LESSON-DICE is mandatory where true (variance-patching is how models rot). Metrics: lesson rate, lesson->rule conversion, death-class decay after lesson ships, repeat-death alarms.

## Extension (operator refinement 2026-07-07): READINESS BACKTRACE + TRAJECTORY AVOIDABILITY

MODEL: Fable 5 (max reasoning) — registration; per-retro artifacts stamped as produced.

1. **READINESS BACKTRACE** in every capability-bound death retro: "enemy too
   strong" is not a root cause. Compute the READINESS DEFICIT at death
   (xp/HP/AC/weapon vs the floor's empirical threat band) and backtrace it:
   enumerate from the dossiers the SKIPPED PREP OPPORTUNITIES earlier in the
   trajectory — unexplored rooms with loot on D1-3, easy xp left unfought,
   armor walked past, rest opportunities declined. Lesson output becomes
   quantitative: "died at D5 with xp2/AC8; full D1-3 exploration would have
   plausibly yielded xp4-5 + ring mail (dossier: 3 unexplored rooms, 2
   skipped easy monsters) → exploration weight too low for this role."
2. **TRAJECTORY AVOIDABILITY** as a metric ALONGSIDE moment-avoidability:
   the 5-8% figure audited the final decision window; re-run the
   counterfactual at trajectory scale — was there a prep path through the
   SAME dungeon that survives this encounter? Expected: much higher. The gap
   between moment-5% and trajectory-X% IS the value of preparation,
   quantified. Honest correction to the C2 central finding's framing:
   capability-bound at the moment, PREPARATION-bound at the trajectory.
3. **WEIGHT EXPLORATION HIGHER (operator directive):** raise goal-market
   exploration weights now as the default for walker/fragile roles (digger
   exemption stays a live hypothesis); NH-E14b ROI sweep + readiness
   backtraces then tune per-role empirically. E15 PREP/EXPLORE states get
   first-class priority before descend transitions. (Implementation goes
   through the normal paired-dev gate on dev seeds — Phase L has no scored
   runs to contaminate.)

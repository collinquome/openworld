# NetHack — worlds wiki

**Best:** 6.09 progression (v1.1, 80 eps, seed block 3000–3079, CI [4.46, 7.93]); v1 4.39; deepest run Dlvl:21 = 39.29.
**SOTA:** 6.8 (#1 Gemini-3-Pro) · 4.0 (#2). We are **statistically tied**, not dominant.
**Report:** `wt-fable-nethack/papers/balrog/artifacts/nethack/FABLE_NETHACK_REPORT.md` · **Code:** `nethack-experiments` repo · **Corpus:** `gs://researchy-nethack-results` (3 GB).
**Lessons PDF:** `NetHack_Lessons_Report.pdf` (ARC-AGI-3 → NetHack).

## The wall (mechanism)
Die to a single **faster monster** in a 1-on-1 we lose because under-levelled. Deaths peak Dlvl 5,
72% "spike" (healthy→dead fast). Every hand-coded fix hits a **benefit/cost coupling**: what rescues
a weak run sinks a strong one. Metric = max achievement rung (depth OR xp), so depth-diving is +EV.

## Experiments log (all A/B'd with paired CI + leave-one-out)
| # | Lever | Result | Lesson |
|---|---|---|---|
| E36–42 | combat/positioning/config levers | null (0-for-N) | deaths capability-bound, not tactical |
| E38 | use in-hand consumables | null | used a win-item, died same depth — execution wall |
| E40 | dive-rush (metric exploit) | negative | rushing dies shallower |
| E41 | corridor funnel vs packs | null | we don't die to packs |
| E43–45 | farm XP before diving | null | can't farm without dying |
| E46 | clone AutoAscend combat (BC) | flat | combat learnable (val .34) but local-only can't lift mean |
| E48 | forensic pray-earlier | negative | fires on survivors, burns limited prayer |
| E50 | strength-first descent gate (NH_XPGATE) | wash | floor-up/ceiling-down; one Valkyrie seed (700) D4→13 didn't generalize |
| dig→str | dig deep then level to survive | invalidated | can't level at depth; 11/12 identical to dig-rush |

**23 arms, mean unmoved.** The coupling is the wall.

## Specialization (re-roll — legitimate, speedrunners do it)
- re-roll → **Valkyrie**: mean 0.066 (~2× random), buys combat capability.
- re-roll → **Archeologist + dig**: **mean 0.130** (best D20/0.379) — digs PAST monsters. **Local optimum:** dies deep, under-levelled. Beats the metric, not the game. ~50–78× action-efficient.
- Per-role mastery would lift the random-role mean 0.054 (current per-role means) → 0.20 (per-role records) — Goal 1 and Goal 3 are the same per-role survival problem.

## Promising / open (strategy_bandit says spend here)
- **LLM-in-the-loop** (`llm_crisis`): on deep-death scenarios the LLM picked a survival move **92% (11/12)** where the fixed rule died (reads HP/speed/prayer-cooldown → Elbereth). Reasoning scales where enumeration can't. **Next:** wire live at crisis point, A/B on Valkyrie/Arch cohorts w/ consistency@Dk + explore-at-depth (steps/level at depth≥8).
- **arch_escape**: dig + escape items (teleport/seal) to break contact on a bad arrival.
- Tooling built: possibility tensor (`e47`), deductive item-ID (Sudoku CSP, `deductive_id.py`), death-replay test set (1,150), visualizer, run_metrics (consistency@Dk), strategy_bandit (win-conjunction; binding FALSE conjunct = "survive at depth").

## Three goals
1. beat raw random-role mean (>6.8) · 2. re-roll benchmark + per-role records · 3. **beat the game once** (ascend). Blocker for 1&3 = survive at depth.

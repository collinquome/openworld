# BALROG + ARC-AGI-3 Results — master index & highlight sheet

> A parent-level log so we never lose or forget these. TL;DR at the top, full table +
> "what was done" below. (Fighting exponentials with logs.) Update this whenever a result lands.

## 🏆 HIGHLIGHTS (the headline wins)
- **ARC-AGI-3 — first PERFECT result**, source-free: 25/25 games, 183/183 levels, beats prior SOTA.
- **MiniHack — 92.5%** (best 95%) vs 40% SOTA → **+52.5pp, more than 2× the leaderboard.**
- **TextWorld — 90% clean / 100% privileged** vs 75.7% SOTA → **+14.3pp.**
- **Baba Is AI — 100%** (saturated) · **BabyAI — 100%** (matched SOTA).
- **NetHack — 6.09**, statistically *tied* with 6.8 SOTA — the one world the approach can't dominate (the lessons report is about why).
- **Pattern:** we DOMINATE deterministic/puzzle worlds; we STRUGGLE on stochastic/survival worlds (Crafter 47%, NetHack) where *death is the binding constraint*.

**Do not lose these.** Our verified-world-model + classical-search recipe (the OpenWorld
approach) applied across the BALROG benchmark suite + ARC-AGI-3. Numbers are the clean /
leaderboard-comparable protocol unless noted. SOTA = balrogai.com leaderboard (parsed 2026-07-06).

| World | Ours | SOTA | Verdict | Report (source of truth) |
|---|---|---|---|---|
| **ARC-AGI-3** | **25/25 games · 183/183 levels** (perfect, source-free) | prior SOTA | **beat — first perfect** | `openworld/README.md` (#arc3); repo quome-cloud/openworld |
| **BabyAI** | **100.0%** (priv 50/50, clean 50/50) | 100.0% | **matched SOTA** | `work/fable_babyai/FABLE_BABYAI_REPORT.md` |
| **Baba Is AI** | **100.0%** (priv + clean, 0 disagreements) | ~90 | **beat / saturated** | `work/fable_t372_synthesis/FABLE_REPORT.md` |
| **TextWorld** | **90.0% clean** / 100.0% privileged (robustness 88%) | 75.7% | **beat +14.3pp (clean)** | `work/fable_textworld/FABLE_TEXTWORLD_REPORT.md` |
| **MiniHack** | **92.5%** official+robustness (best pass 95%) | 40.0% | **beat +52.5pp (>2×)** | `work/fable_minihack/FABLE_MINIHACK_REPORT.md` |
| **Crafter** | 47.3% (48.6% w/ memory) | 57.3% | below ~10pp — *death-bound* | `work/fable_crafter/FABLE_CRAFTER_REPORT.md` |
| **NetHack** | **6.09** v1.1 (CI [4.46, 7.93]); v1 4.39; best run Dlvl:21 = 39.29 | 6.8 | tied SOTA (not dominated) — the wall | `work/fable_nethack/` + `work/wt-fable-nethack/papers/balrog/artifacts/nethack/FABLE_NETHACK_REPORT.md` |

## The pattern
- **Deterministic / puzzle worlds → we dominate:** BabyAI 100, Baba 100, TextWorld 90/100, MiniHack 92.5. Fully code-representable → verified world model + search saturates them.
- **Stochastic / survival worlds → we struggle:** Crafter 47.3 (below SOTA, death-bound), NetHack 6.09 (tied SOTA). Randomness + combinatorial scope + death-as-binding-constraint defeat the deterministic-planner approach. This is the subject of the NetHack lessons report.

## Where the code/data lives (git state — 2026-07-09)
- **ARC-AGI-3:** committed — `quome-cloud/openworld` (fork `collinquome/openworld`). SAFE.
- **BabyAI / Baba / TextWorld / MiniHack / Crafter:** in `work/fable_*`, tracked ONLY by the
  remote-less `/data/doh/teams/researchy` repo → **NOT BACKED UP TO ANY REMOTE.** Migration to
  collinquome pending (this index is step 1).
- **NetHack:** `work/fable_nethack` = the `nethack-experiments` repo (committed locally, push
  pending a fine-grained token); full 3 GB trajectory corpus archived at
  `gs://researchy-nethack-results`. Paper: `wt-fable-nethack/papers/balrog/`.

## Deep-dive TODO (operator wants to go through each)
Each `FABLE_*_REPORT.md` has the full protocol, per-task tables, ablations, and honest caveats.
Priority migration order: MiniHack + TextWorld (biggest SOTA deltas), Baba/BabyAI (saturated),
Crafter (the survival-wall cousin of NetHack), then confirm NetHack push.

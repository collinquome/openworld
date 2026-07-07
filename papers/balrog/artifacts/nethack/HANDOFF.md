# HANDOFF — NetHack Campaign 2 → Phase L (written 2026-07-07, end of checkpoint session)

## Where things stand (all committed + pushed: fork collinquome/openworld, branch aleph/fable-nethack, HEAD 382bcc0)

- **NH-C2.1 checkpoint CLOSED:** n=80 seeds 4000–4079, frozen config `NH_FOOD2 NH_PRAYFIX NH_LOS NH_TOPO NH_GUARD` (md5s in results/RUN_LOG.txt @ 14:56:09): **mean 5.27, CI [4.22, 6.43]** — no beat, ties v1.1. PR #215 updated (comment 4905710502). Operator emailed by coordinator with the c21 GIFs.
- **Central finding:** E-NH1b avoidability audit — only 5–8% of damage is avoidable in-model; deaths are capability-bound. Action audit: **50/248 actions ever used; cast/zap/quaff/read/fire/wield = 0 ever.**
- **Program state:** docs/NETHACK_PROGRAM.md (in repo) = authoritative ledger + phase structure + seed registry. Report: papers/balrog/artifacts/nethack/FABLE_NETHACK_C2_REPORT.md. Experiment folders: papers/balrog/experiments/NH-*/.

## FRESH RESULT for the successor (not yet in repo docs): CAST FLOW WORKS

Probe (dev seed 715, Wizard): `cast` → xwaitingforspace spell menu ("a - force bolt … 0% fail") → `a` → in_yn "In what direction?" → `west` → **Pw 8→3, T advanced**. Same queue machinery as the dig flow (`self.queue=[letter, direction]; return "cast"`). Spellcasting is INTERFACE-REACHABLE. This was the go/no-go for Phase-L priority 1 — it's GO.

## Phase L priority order (coordinator-set, 2026-07-07)

1. **ACTION-SPACE FRONTIER** (NH-E14 folder): per verb family {cast, zap, quaff, read, wield/fire}: KB mechanics claims + source model + gym experiments → rule cards → per-role integration. First target: Wizard Force Bolt in combat (menu letter discovered per-episode from the cast menu tty, direction at adjacent/ray target, gate on Pw ≥ 5 and fail% parsed from menu). Dev-validate on Wizard-heavy seed sets (Wizard block mean is 2.09–2.77 everywhere — huge headroom). Then Healer healing spell at low HP. Wands: zap flow probe next (expect same pattern; wand letters from inventory, unidentified wands = engrave-test or gamble — carded decision needed).
2. **NH-E15 state machine + stall watchdog** — spec in experiments/NH-E15-strategy-machine/README.md. Wire states into subgoal ledger (labels already exist: descend/explore/loot/fight/flee/rest/survive map ~1:1). Watchdog metrics from existing traj arrays. Fixture: giant-bat standoff (clean_A ep4 gif; v1 seed 1004).
3. **NH-E13 KB build:** wiki_kb.sqlite (FTS5) + manifest per experiments/NH-E13-wiki-strategy/KB.md. WebFetch adds pages only. First pages: Force bolt, Wizard strategy, Wand, Potion, Scroll, Standard strategy.
4. Background loop: gym harvest + NH-E12 retrospectives (backfill the 66+ combat deaths from results/c2_cache — cache has everything needed), coverage matrix, NH-E14b loot-ROI sweep.

## Live technical state

- Work dir: /data/doh/teams/researchy/work/fable_nethack (code = frozen NH-C2.1 state, byte-identical to repo papers/balrog/code/nethack/).
- v1.1 reference snapshot: v11_ref/ (md5-verified; own results/ + transitions for dev seeds 700–739 ref + ref2 control).
- Flags (all default-off, v1.1-preserving): NH_FOOD2 NH_PRAYFIX NH_LOS NH_TOPO NH_GUARD (frozen set) + built-but-dropped NH_EXPMAX NH_RANGED NH_THREAT NH_ARMOR NH_PACE NH_ELBERETH; rest-param env knobs NH_REST_*.
- Key modules: nh_percept.py (topology/threat/LOS/item + exchange model accessors, species_dpt/species_ttk), c2_avoid.py (avoidability auditor), c2_ledger_checks.py (regression harness D1–D5 — run after every dev block), c2_ab.py (paired A/B), bootstrap_ci.ci95 (canonical CI), render_c2.py (planner-view GIFs; provenance banners).
- Mined caches: results/c2_cache/ (per-episode extracts, 216 episodes), results/c2_exchange.json (verification-gated), results/c2_forensics.json, results/c2_avoid_*.json.
- Dev seed etiquette: 700–799 used; fresh dev from 800–999. NEVER touch 6000–6099 (Arm A) / 7000–7024 (Arm B).
- Known open niggles: (a) harness-audit items 1–4,6 (belief-snapshot except counting, transition flush+.complete, RUNNER_TRUNCATED end-reason, tty-rank role fallback, depth ground-truth assert) are queued — implement before the next dev block and add md5s at next freeze; (b) D1 detector flagged one bounded far-loot-approach case (navfood ep704) — tighten give-up to count no-progress targetings; (c) blind-arm report CIs should be recomputed with canonical ci95 on next touch.
- Session-ops gotchas: pkill with literal script names kills your own shell (use bracket patterns); background `sleep` calls return instantly — use run_in_background waiters/Monitor; episodes run ~30–100 steps/s, a 40-ep dev block ≈ 20–40 min on 3 workers; py-spy is at /home/doh/.local/bin/py-spy.

## Pre-declared discipline (do not weaken)

Drop-rule (≥20 paired dev episodes, clearly pays or dies); avoidable-damage as primary Phase-L dev metric; every stochastic rule through the α=0.01 distributional gate; rule cards with provenance everywhere (priors/ verdict table maintained — record invalidations); Phase-L exit criteria in the report §Program; Phase E = single pre-registered blocks per arm, no peeking.

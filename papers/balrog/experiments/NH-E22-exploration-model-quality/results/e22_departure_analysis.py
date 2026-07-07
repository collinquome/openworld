#!/usr/bin/env python3
"""NH-E22 departure-exploration vs next-level-survival analysis.

MODEL: Sonnet subagent, spec by Fable 5

Pre-registered question (operator, 2026-07-06/07): does the explored
fraction of a level AT DEPARTURE predict survival on the NEXT level?
First empirical read on the "explore before descending" hypothesis
(NH-E22, exploration -> model quality -> decision quality -> survival
mediation chain).

DATA SOURCE NOTE (read this before trusting the numbers): the spec asked
for results/trajectories/v11block40__ep*.json (80 episodes) PLUS
c2block80__ep*.json "if present". Checked: v11block40 trajectories carry
"frames" (raw tty renders) but have NO "beliefs" field at all (0/80
episodes) -- the sparse belief-snapshot format this analysis needs
(agent's own explored/terrain grid, [step, rows, suspects]) only exists
for the Campaign-2 belief-logging runs. Of those, c2block80 is the file
set actually named in the spec, so ALL events in this analysis come from
c2block80 (80 episodes, condition A, NH-C2.1 NAVFOOD+GUARD checkpoint).
v11block40 is scanned too (for future-proofing / in case beliefs get
backfilled) but contributes 0 events today. This is flagged again in the
caveats block of the output JSON.

Method:
  1. Departure event = step i where depth[i] > depth[i-1] (descend only,
     up-moves ignored). Departure depth d = depth[i-1]; departure step
     s = i-1 (last step still recorded at depth d). All observed descents
     in c2block80 are single-level (depth[i] == d+1); events are restricted
     to that case so "next level" unambiguously means d+1.
  2. explored_cells: count of non-"." chars in the nearest belief snapshot
     at or before step s (staleness guard: snapshot must be within 400
     steps of s, else the event is dropped and counted). This is the raw,
     wall-inclusive count -- "estimator (a)-adjacent" proxy, reported for
     completeness.
     nonwall_explored: same snapshot, excluding WALL cells ("B" =
     chr(65+1)), i.e. the codebase's own retrospective/offline exploration
     metric (see nh_store.py:level_explore_stats, estimator (b)). THIS is
     the primary metric used for the headline stats below -- estimator
     (b)-flavored RAW COUNTS, not a percentage of final-explored or of
     total map area.
  3. Outcome: final_depth = depth[-1] (last step of the episode).
     died_at_next = (final_depth == d + 1) and the episode's end_reason
     starts with "DEATH" (all 80 c2block80 episodes are deaths, so this
     reduces to final_depth == d + 1 here).
     survived_next = not died_at_next.
     Caveat: this is a GLOBAL per-episode death label applied to every
     departure event from that episode, not a causal trace of which
     specific descent led to death. If an episode revisits depth d more
     than once, all its departure-from-d events share the same
     died_at_next label. Flagged again below.

Outputs: results/e22_departure_survival.json (all numbers + full
per-event table), and a copy under
papers/balrog/experiments/NH-E22-exploration-model-quality/results/.
"""

import glob
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TRAJ_DIR = os.path.join(HERE, "results", "trajectories")
OUT_PATH = os.path.join(HERE, "results", "e22_departure_survival.json")
DEST_DIR = ("/data/doh/teams/researchy/work/wt-fable-nethack/papers/balrog/"
            "experiments/NH-E22-exploration-model-quality/results")

ROWS, COLS = 21, 79  # matches nh_common.ROWS, COLS
STALENESS_LIMIT = 400
BOOT_N = 10_000
BOOT_SEED = 20260706

PATTERNS = ["v11block40__ep*.json", "c2block80__ep*.json"]

# end_reason lookup: episode id -> (end_reason, role) from the frozen
# results summary (per-episode outcome ground truth; trajectories
# themselves don't carry an explicit death flag).
RESULTS_SUMMARY = os.path.join(HERE, "results", "nethack_results_c2block80.json")


def load_end_reasons():
    out = {}
    if not os.path.exists(RESULTS_SUMMARY):
        return out
    d = json.load(open(RESULTS_SUMMARY))
    for e in d.get("episodes", []):
        out[e["episode"]] = {
            "end_reason": e.get("end_reason", ""),
            "role": e.get("role", "?"),
            "depth_max": e.get("depth_max"),
        }
    return out


def explored_counts(rows):
    """(explored_cells_with_walls, nonwall_explored) for one belief
    snapshot's rows list."""
    explored = 0
    nonwall = 0
    for r in rows:
        for ch in r:
            if ch == ".":
                continue
            explored += 1
            if ch != "B":  # B = chr(65+1) = WALL
                nonwall += 1
    return explored, nonwall


def nearest_snapshot(beliefs, s):
    """Latest [step, rows, suspects] with step <= s, or None."""
    best = None
    for snap in beliefs:
        st = snap[0]
        if st <= s:
            if best is None or st > best[0]:
                best = snap
        else:
            # beliefs are step-ordered; once we pass s we can stop early
            # only if we've already found a candidate <= s AND steps are
            # monotonic (verified true in this dataset's writer, but stay
            # defensive and just continue the scan instead of breaking).
            continue
    return best


def spearman(x, y):
    """Spearman rank correlation, average-rank ties, no scipy dependency."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    def ranks(a):
        order = np.argsort(a, kind="mergesort")
        r = np.empty(len(a), dtype=float)
        sorted_a = a[order]
        i = 0
        n = len(a)
        while i < n:
            j = i
            while j + 1 < n and sorted_a[j + 1] == sorted_a[i]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg_rank
            i = j + 1
        return r

    rx = ranks(x)
    ry = ranks(y)
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def bootstrap_diff(explored_survived, explored_died, n_boot, seed):
    rng = np.random.default_rng(seed)
    es = np.asarray(explored_survived, dtype=float)
    ed = np.asarray(explored_died, dtype=float)
    if len(es) == 0 or len(ed) == 0:
        return None
    obs_diff = float(es.mean() - ed.mean())
    diffs = np.empty(n_boot, dtype=float)
    ns, nd = len(es), len(ed)
    for b in range(n_boot):
        bs = es[rng.integers(0, ns, ns)]
        bd = ed[rng.integers(0, nd, nd)]
        diffs[b] = bs.mean() - bd.mean()
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {
        "observed_diff_survived_minus_died": obs_diff,
        "ci_95_lo": float(lo),
        "ci_95_hi": float(hi),
        "n_boot": n_boot,
        "seed": seed,
    }


def band_for_depth(d):
    if d <= 3:
        return "d1-3"
    if d <= 6:
        return "d4-6"
    return "d7+"


def quartile_bins(values):
    qs = np.percentile(values, [25, 50, 75])
    return qs


def assign_quartile(v, qs):
    if v <= qs[0]:
        return "Q1"
    if v <= qs[1]:
        return "Q2"
    if v <= qs[2]:
        return "Q3"
    return "Q4"


def main():
    end_reasons = load_end_reasons()

    files_by_pattern = {}
    for pat in PATTERNS:
        fs = sorted(glob.glob(os.path.join(TRAJ_DIR, pat)))
        files_by_pattern[pat] = fs

    events = []
    drop_counts = {
        "no_snapshot_before_departure": 0,
        "stale_snapshot_gt_400": 0,
        "non_adjacent_descent_skipped": 0,  # depth jump > 1 (none observed,
                                             # kept for robustness)
    }
    files_scanned = 0
    files_with_beliefs = 0
    files_with_no_beliefs_field = []

    for pat, fs in files_by_pattern.items():
        for f in fs:
            files_scanned += 1
            d = json.load(open(f))
            beliefs = d.get("beliefs")
            if not beliefs:
                files_with_no_beliefs_field.append(os.path.basename(f))
                continue
            files_with_beliefs += 1
            depth = d["depth"]
            ep_id = d["episode"]
            meta = end_reasons.get(ep_id, {})
            end_reason = meta.get("end_reason", "")
            role = meta.get("role", "?")
            final_depth = depth[-1]
            is_death = end_reason.startswith("DEATH")

            for i in range(1, len(depth)):
                if depth[i] <= depth[i - 1]:
                    continue  # ignore up-moves / flat
                jump = depth[i] - depth[i - 1]
                dep_depth = depth[i - 1]
                if jump != 1:
                    drop_counts["non_adjacent_descent_skipped"] += 1
                    continue
                s = i - 1  # last step still at dep_depth

                snap = nearest_snapshot(beliefs, s)
                if snap is None:
                    drop_counts["no_snapshot_before_departure"] += 1
                    continue
                snap_step, rows, suspects = snap
                gap = s - snap_step
                if gap > STALENESS_LIMIT:
                    drop_counts["stale_snapshot_gt_400"] += 1
                    continue

                explored_cells, nonwall_explored = explored_counts(rows)
                died_at_next = (final_depth == dep_depth + 1) and is_death
                survived_next = not died_at_next

                events.append({
                    "file": os.path.basename(f),
                    "episode": ep_id,
                    "seed": d.get("seed"),
                    "role": role,
                    "departure_step": s,
                    "departure_depth": dep_depth,
                    "arrival_depth": dep_depth + 1,
                    "snapshot_step": snap_step,
                    "snapshot_gap": gap,
                    "explored_cells": explored_cells,
                    "nonwall_explored": nonwall_explored,
                    "total_map_cells": ROWS * COLS,
                    "n_suspects": len(suspects) if suspects else 0,
                    "final_depth": final_depth,
                    "end_reason": end_reason,
                    "is_death": is_death,
                    "died_at_next": died_at_next,
                    "survived_next": survived_next,
                    "depth_band": band_for_depth(dep_depth),
                })

    n_events = len(events)
    metric = "nonwall_explored"  # primary metric per spec step 4

    survived = [e for e in events if e["survived_next"]]
    died = [e for e in events if e["died_at_next"]]

    def mean_metric(evs, key=metric):
        return float(np.mean([e[key] for e in evs])) if evs else None

    headline = {
        "n_events": n_events,
        "n_survived": len(survived),
        "n_died": len(died),
        "survival_rate": (len(survived) / n_events) if n_events else None,
        "mean_nonwall_explored_survived": mean_metric(survived),
        "mean_nonwall_explored_died": mean_metric(died),
        "mean_explored_with_walls_survived": mean_metric(survived, "explored_cells"),
        "mean_explored_with_walls_died": mean_metric(died, "explored_cells"),
    }

    # per-depth-band breakdown
    bands = {}
    for band in ("d1-3", "d4-6", "d7+"):
        b_evs = [e for e in events if e["depth_band"] == band]
        b_surv = [e for e in b_evs if e["survived_next"]]
        b_died = [e for e in b_evs if e["died_at_next"]]
        bands[band] = {
            "n": len(b_evs),
            "n_survived": len(b_surv),
            "n_died": len(b_died),
            "survival_rate": (len(b_surv) / len(b_evs)) if b_evs else None,
            "mean_nonwall_explored_survived": mean_metric(b_surv),
            "mean_nonwall_explored_died": mean_metric(b_died),
        }

    # pooled quartile analysis (quartiles of nonwall_explored across ALL
    # retained events, pooled across depth bands)
    quartile_analysis = None
    if n_events >= 4:
        vals = [e[metric] for e in events]
        qs = quartile_bins(vals)
        qgroups = {"Q1": [], "Q2": [], "Q3": [], "Q4": []}
        for e in events:
            qgroups[assign_quartile(e[metric], qs)].append(e)
        quartile_analysis = {
            "quartile_edges_25_50_75": [float(x) for x in qs],
            "groups": {
                q: {
                    "n": len(evs),
                    "survival_rate": (
                        sum(1 for e in evs if e["survived_next"]) / len(evs)
                        if evs else None
                    ),
                    "mean_nonwall_explored": mean_metric(evs),
                }
                for q, evs in qgroups.items()
            },
        }

    # Spearman correlation, pooled
    spearman_r = None
    if n_events >= 2:
        x = [e[metric] for e in events]
        y = [1 if e["survived_next"] else 0 for e in events]
        spearman_r = spearman(x, y)

    # bootstrap CI on survived-vs-died mean difference (primary metric)
    boot = None
    if survived and died:
        boot = bootstrap_diff(
            [e[metric] for e in survived],
            [e[metric] for e in died],
            BOOT_N, BOOT_SEED,
        )

    out = {
        "question": ("Does the explored fraction of a level AT DEPARTURE "
                     "predict survival on the NEXT level?"),
        "estimator_tag": ("estimator (b)-flavored RAW COUNTS (offline/"
                           "retrospective nonwall-explored cell count at "
                           "departure snapshot; NOT a percentage of "
                           "final-explored or of total map area). Secondary "
                           "wall-inclusive raw count also reported."),
        "primary_metric": metric,
        "data_provenance": {
            "patterns_scanned": PATTERNS,
            "files_scanned": files_scanned,
            "files_with_beliefs_field": files_with_beliefs,
            "files_with_no_beliefs_field_count": len(files_with_no_beliefs_field),
            "note": ("v11block40__ep*.json (80 files) carry NO 'beliefs' "
                     "field at all -- checked programmatically, 0/80 have "
                     "a non-empty beliefs list. Every event in this "
                     "analysis therefore comes from c2block80__ep*.json "
                     "(80 episodes). This deviates from the spec's stated "
                     "expectation that v11block40 would also contribute "
                     "events; flagged here rather than silently dropped."),
        },
        "departure_event_counts": {
            "total_descent_events_seen": (
                n_events + sum(drop_counts.values())
            ),
            "retained_events": n_events,
            "dropped": drop_counts,
        },
        "headline": headline,
        "by_departure_depth_band": bands,
        "pooled_quartile_analysis": quartile_analysis,
        "spearman_explored_vs_survived": spearman_r,
        "bootstrap_survived_minus_died_mean_diff": boot,
        "caveats": [
            "N is small (this dataset yields on the order of a few hundred "
            "departure events from 80 episodes on one checkpoint, one "
            "condition) -- treat point estimates as directional, not "
            "conclusive; CIs below are the honest read on precision.",
            "Confound: better-playing episodes (better role/luck/policy) "
            "may BOTH explore more before descending AND survive more, for "
            "reasons unrelated to exploration itself (e.g. surviving "
            "longer per level mechanically allows more exploration time). "
            "This analysis is observational/correlational, not causal.",
            "Depth truncation: deeper bands (d7+) have fewer episodes "
            "reaching them at all (survivorship into deep levels is "
            "itself gated by earlier survival), so d7+ n is small and "
            "its estimates are noisier and conditioned on having already "
            "survived to that depth.",
            "Role differences: c2block80 mixes roles (Valkyrie, Monk, "
            "Archeologist, etc. -- see per-event 'role' field); different "
            "roles have very different survival curves and exploration "
            "styles (e.g. stealthy vs. tanky), and role is not controlled "
            "for in the pooled numbers above.",
            "Outcome label is per-EPISODE (final_depth == departure_depth+1 "
            "and death), applied to every departure-from-that-depth event "
            "in the episode -- not a causal trace of which specific "
            "descent produced the death. Episodes with more than one "
            "departure from the same depth (backtracking) share one label "
            "across those events.",
            "All 80 c2block80 episodes end in death (end_reason startswith "
            "'DEATH' for 80/80) -- there is no censoring-by-survival-to-"
            "game-end in this sample, which simplifies died_at_next but "
            "means 'survived_next' means 'survived that one level', not "
            "'won the game'.",
            "Belief snapshots are sparse; the staleness guard (max 400-"
            "step gap) drops some departure events outright -- see "
            "departure_event_counts.dropped for exact counts. Dropped "
            "events are not included in any statistic above.",
            "v11block40 contributes zero events (see data_provenance) -- "
            "this is a single-checkpoint (NH-C2.1 NAVFOOD+GUARD), single-"
            "condition (A) read, not yet a cross-checkpoint replication.",
        ],
        "events": events,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as fh:
        json.dump(out, fh, indent=2)

    os.makedirs(DEST_DIR, exist_ok=True)
    dest_json = os.path.join(DEST_DIR, "e22_departure_survival.json")
    with open(dest_json, "w") as fh:
        json.dump(out, fh, indent=2)
    dest_script = os.path.join(DEST_DIR, "e22_departure_analysis.py")
    with open(__file__) as fh:
        script_src = fh.read()
    with open(dest_script, "w") as fh:
        fh.write(script_src)

    print(json.dumps(headline, indent=2))
    print("bands:", json.dumps(bands, indent=2))
    print("spearman:", spearman_r)
    print("bootstrap:", json.dumps(boot, indent=2))
    print("dropped:", drop_counts)
    print(f"wrote {OUT_PATH}")
    print(f"copied to {dest_json} and {dest_script}")


if __name__ == "__main__":
    main()

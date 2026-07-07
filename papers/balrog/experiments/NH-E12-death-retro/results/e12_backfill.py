# MODEL: Sonnet subagent, spec by Fable 5
"""NH-E12 death-retrospective backfill.

Builds a per-death retrospective artifact for every COMBAT-class death
(MELEE_TRASH, MELEE_OTHER, SPIDER_ANT, RANGED, PRAY_DEATH) found in
results/c2_cache/ (216 mined episode extracts). Pure offline log
processing: no env interaction, read-only on all inputs.

Classification source of truth
-------------------------------
For episodes whose transitions_file appears in one of the canonical
results/nethack_results*.json (or memory_paired.json / memory_experiment.json)
files, we use the harness's own `end_reason` string + nh_forensics.classify()
(imported directly -- same function that produced results/c2_forensics.json's
taxonomy) so classification/killer/role match the project's canonical numbers
exactly. This covers v11block40 (the primary n=80 corpus), baseline25,
clean_A, memory_paired, memory_pass1-3, robustness (139/216 episodes).

For the "dev" and "exploration" cache labels (77/216 episodes) no canonical
results json exists (their transitions_file prefixes -- transitions/dev/,
transitions/exploration/ -- do not appear in ANY nethack_results*.json in
this workdir). The mined cache's own `last_msgs` field truncates each
message to 200 chars, which frequently cuts off the "Killed by ..." clause
before it appears (only 85/216 cache episodes have "Killed by" fully intact
within last_msgs). For those 77 episodes we fall back to reading the raw,
untruncated final message straight from results/transitions/<label>/*.jsonl.gz
(read-only) and run it through the exact same classify()/species_of()
functions. Role is recovered from the death screen's
"Agent-<role3>-<race3>-<gender3>-<align3>" string using NetHack's standard
3-letter role abbreviations (offline/disclosed constant table, same
provenance class as nh_common.py's RANK_TO_ROLE). Episodes in this fallback
group that show no death evidence at all (no "top ten list" / "Killed by" /
"starved" / "quit" marker in the raw final message -- i.e. runs that ended
by step-limit truncation, not death) are excluded and counted in
e12_summary.json's notes.

Avoidability join
------------------
results/c2_avoid_*.json verdicts are per-episode but keyed only by seed,
and seeds are REUSED across unrelated runs (e.g. seed 4000 appears both in
c2_avoid_block80.json, steps=1117, and in the memory_pass1 cache episode,
steps=1593 -- those are two different playthroughs of the same dungeon
seed under different agent configs, NOT the same episode). To avoid
misattributing an avoidability verdict to the wrong trajectory, we match
on the pair (seed, steps) across all 4 avoid files. Only c2_avoid_v11block.json
actually shares (seed, steps) with any cache episode (all 80 of
v11block40) -- confirmed by direct check. Every other episode gets
avoidability="UNKNOWN".
"""

import glob
import gzip
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "pylib"))

RESULTS = os.path.join(HERE, "results")
CACHE = os.path.join(RESULTS, "c2_cache")

import nh_forensics as NF  # reuses classify()/species_of()/DIFF -- canonical logic

COMBAT_CLASSES = {"MELEE_TRASH", "MELEE_OTHER", "SPIDER_ANT", "RANGED",
                   "PRAY_DEATH"}

# NetHack standard 3-letter role abbreviations used in the death/top-ten
# screen's "Agent-<role>-<race>-<gender>-<align>" string. Offline/disclosed
# game constant, same provenance class as nh_common.py's RANK_TO_ROLE table.
ROLE3 = {
    "Arc": "Archeologist", "Bar": "Barbarian", "Cav": "Caveman",
    "Hea": "Healer", "Kni": "Knight", "Mon": "Monk", "Pri": "Priest",
    "Rog": "Rogue", "Ran": "Ranger", "Sam": "Samurai", "Tou": "Tourist",
    "Val": "Valkyrie", "Wiz": "Wizard",
}
RE_AGENT_TAG = re.compile(r"Agent-([A-Za-z]{3})-")

# Mechanism -> one-sentence lesson template, transcribed from c2_avoid.py's
# own mechanism definitions (its module docstring), not invented.
MECH_LESSON = {
    "THROW": ("First contact with {killer} (fast/never-outrun or "
              "spider/ant-class) while carrying ammo and a clear ray -- "
              "should have thrown before it closed to melee."),
    "KITE": ("Pack fight ({killer}) in the open near a reachable choke "
             "point -- retreating to the choke would have traded a 1-at-a-"
             "time loss for the pack loss actually taken."),
    "REST": ("Descended below 60% HP with no visible hostile, then took "
             "damage from {killer} on the new level while still hurt -- "
             "should have rested/healed before diving."),
    "LOS": ("Took ranged damage from {killer} with no adjacent hostile "
            "while an adjacent non-ray cell was available -- should have "
            "broken line of sight."),
    "EAT": ("Fought {killer} while Weak+ from hunger with a fresh safe "
            "corpse available -- should have eaten first."),
}


def load_canonical_index():
    """transitions_file -> dict(end_reason, role, race) from every
    canonical results json in this workdir, preferring merged/plain
    filenames over per-worker shard duplicates when the same
    transitions_file appears more than once."""
    files = glob.glob(os.path.join(RESULTS, "nethack_results*.json"))
    files.append(os.path.join(RESULTS, "memory_paired.json"))
    # plain (non worker-shard) files first so they win ties
    files.sort(key=lambda p: (bool(re.search(r"_w\d+\.json$|_v\d+\.json$",
                                              p)), p))
    idx = {}

    def add(eps):
        for e in eps:
            tf = e.get("transitions_file")
            if not tf or tf in idx:
                continue
            idx[tf] = dict(end_reason=e.get("end_reason"),
                            role=e.get("role"), race=e.get("race"))

    for fn in files:
        if not os.path.exists(fn):
            continue
        try:
            d = json.load(open(fn))
        except Exception:
            continue
        eps = d.get("episodes", d if isinstance(d, list) else [])
        add(eps)

    me = os.path.join(RESULTS, "memory_experiment.json")
    if os.path.exists(me):
        d = json.load(open(me))
        for p in d.get("passes", []):
            add(p.get("episodes", []))

    return idx


def load_avoid_index():
    """(seed, steps) -> final_event dict, across all c2_avoid_*.json."""
    idx = {}
    for fn in glob.glob(os.path.join(RESULTS, "c2_avoid_*.json")):
        try:
            rows = json.load(open(fn))
        except Exception:
            continue
        for e in rows:
            key = (e.get("seed"), e.get("steps"))
            fe = e.get("final_event")
            if fe:
                idx.setdefault(key, fe)
    return idx


def raw_final_message(transitions_file):
    """Read the untruncated message of the LAST record in a raw
    transitions log (read-only). Returns "" if unreadable."""
    path = os.path.join(RESULTS, transitions_file)
    if not os.path.exists(path):
        return ""
    try:
        with gzip.open(path, "rt") as f:
            last_line = None
            for line in f:
                last_line = line
        if not last_line:
            return ""
        rec = json.loads(last_line)
        return (rec.get("obs") or {}).get("message", "") or ""
    except Exception:
        return ""


DEATH_MARKERS = ("top ten list", "Killed by", "starved to death",
                  "choked", "You die")


def looks_like_death(msg):
    return any(k in msg for k in DEATH_MARKERS)


def role_from_message(msg):
    m = RE_AGENT_TAG.search(msg)
    if not m:
        return None
    return ROLE3.get(m.group(1))


def hp_trajectory(cache):
    """Last ~10 (hp, hpmax) pairs approaching death: combat-log hp values
    plus the terminal live frame."""
    combat = cache.get("combat") or []
    final = cache.get("final") or {}
    pairs = [(c[3], c[4]) for c in combat[-9:]]
    if final and "hp" in final and "hpmax" in final:
        pairs.append((final["hp"], final["hpmax"]))
    return pairs[-10:]


def build_record(cache, cls, end_reason, role, avoid_fe, source,
                  end_reason_display=None):
    header = cache["header"]
    final = cache.get("final") or {}
    seed = header.get("seed")
    label = cache["label"]
    death_id = f"{label}_{seed}"
    killer = NF.species_of(end_reason) if end_reason else None

    pairs = hp_trajectory(cache)
    hp_traj_final = [p[0] for p in pairs] if pairs else None
    if pairs:
        below = sum(1 for hp, hpmax in pairs if hpmax and hp / hpmax < 0.5)
        final_stretch_below_half = below >= max(1, len(pairs)) * 0.5
    else:
        final_stretch_below_half = None

    depth = final.get("depth")
    xp = final.get("xp")
    hpmax = final.get("hpmax")
    ac = final.get("ac")
    turn = final.get("t")

    if avoid_fe:
        verdict = avoid_fe.get("verdict")
        mech = avoid_fe.get("mech")
        avoidability = f"{verdict}({mech})" if mech else str(verdict)
    else:
        verdict, mech = None, None
        avoidability = "UNKNOWN"

    # ---- mechanical lesson typing (see LESSON TYPING RULES in the task) --
    lesson_type = "NEEDS_REVIEW"
    lesson = ""
    if verdict == "AVOIDABLE":
        lesson_type = "TACTICAL_RULE"
        tmpl = MECH_LESSON.get(mech)
        if tmpl:
            lesson = tmpl.format(killer=killer or "the killer")
        else:
            lesson = f"AVOIDABLE({mech}): mechanism not in template table."
    elif depth is not None and xp is not None and depth > 0 and \
            xp < depth / 2.0:
        lesson_type = "ARRIVAL_CONSTRAINT"
        lesson = f"arrived at D{depth} with xp{xp} (readiness deficit)"
    elif verdict == "UNAVOIDABLE":
        lesson_type = "NO_LESSON_DICE"
        lesson = ""
    # else: NEEDS_REVIEW (UNCERTAIN avoidability, or UNKNOWN with no
    # arrival-constraint trigger) -- ambiguous, left for human review.

    return {
        "death_id": death_id,
        "class": cls,
        "role": role,
        "depth": depth,
        "turn": turn,
        "killer": killer,
        "hp_trajectory_final": hp_traj_final,
        "final_stretch_below_half": final_stretch_below_half,
        "readiness": {"xp": xp, "ac": ac, "hpmax": hpmax},
        "avoidability": avoidability,
        "lesson_type": lesson_type,
        "lesson": lesson,
        "_source": source,          # provenance, not part of the required
        # schema but kept for auditability -- raw (pre-normalization) text
        # when available, so a human can see the actual death-screen wrap
        "_end_reason": end_reason_display if end_reason_display is not None
        else end_reason,
    }


def main():
    canon_idx = load_canonical_index()
    avoid_idx = load_avoid_index()

    records = []
    n_seen = 0
    n_excluded_nondeath = 0
    n_canonical = 0
    n_fallback = 0
    n_fallback_no_role = 0
    class_counts_all = {}

    for fn in sorted(glob.glob(os.path.join(CACHE, "*.json.gz"))):
        n_seen += 1
        cache = json.load(gzip.open(fn, "rt"))
        tf = cache.get("file")
        final = cache.get("final") or {}
        meta = canon_idx.get(tf)

        if meta and meta.get("end_reason"):
            end_reason_raw = meta["end_reason"]
            role = meta.get("role")
            source = "canonical"
            n_canonical += 1
        else:
            msg = raw_final_message(tf)
            if not looks_like_death(msg):
                n_excluded_nondeath += 1
                continue
            end_reason_raw = msg
            role = role_from_message(msg)
            if role is None:
                n_fallback_no_role += 1
            source = "cache_fallback_raw_msg"
            n_fallback += 1

        # The raw NetHack death screen hard-wraps at 80 columns, which can
        # split a keyword phrase (e.g. "while praying" -> "while\npraying")
        # across the line break at an unpredictable offset. Collapse
        # whitespace before running it through classify()/species_of() so
        # those substring/regex checks aren't fooled by wrap position; the
        # untouched raw text is still kept in _end_reason for audit.
        end_reason = re.sub(r"\s+", " ", end_reason_raw)

        cls = NF.classify(end_reason, final)
        class_counts_all[cls] = class_counts_all.get(cls, 0) + 1
        if cls not in COMBAT_CLASSES:
            continue

        header = cache["header"]
        seed = header.get("seed")
        steps = cache.get("steps")
        avoid_fe = avoid_idx.get((seed, steps))

        rec = build_record(cache, cls, end_reason, role, avoid_fe, source,
                            end_reason_display=end_reason_raw)
        records.append(rec)

    records.sort(key=lambda r: r["death_id"])

    # ---- summary --------------------------------------------------------
    by_class = {}
    by_lesson = {}
    below_half_known = 0
    below_half_true = 0
    role_depth_pairs = {}   # role -> [n_arrival_constraint, n_total]
    for r in records:
        by_class[r["class"]] = by_class.get(r["class"], 0) + 1
        by_lesson[r["lesson_type"]] = by_lesson.get(r["lesson_type"], 0) + 1
        if r["final_stretch_below_half"] is not None:
            below_half_known += 1
            if r["final_stretch_below_half"]:
                below_half_true += 1
        role = r["role"] or "UNKNOWN"
        role_depth_pairs.setdefault(role, [0, 0])
        role_depth_pairs[role][1] += 1
        if r["lesson_type"] == "ARRIVAL_CONSTRAINT":
            role_depth_pairs[role][0] += 1

    arrival_rate_by_role = {
        role: (n_ac / n_tot if n_tot else None)
        for role, (n_ac, n_tot) in role_depth_pairs.items()
    }

    pct_below_half = (100.0 * below_half_true / below_half_known
                       if below_half_known else None)

    n_avoid_matched = sum(1 for r in records if r["avoidability"] != "UNKNOWN")
    n_role_unknown = sum(1 for r in records if r["role"] is None)

    notes = [
        f"{n_seen} total cache episodes scanned; {n_canonical} classified "
        "via canonical results*.json end_reason (exact harness ground "
        f"truth), {n_fallback} via raw untruncated final message from "
        "results/transitions/<label>/ (dev + exploration labels have no "
        "canonical results json in this workdir).",
        f"{n_excluded_nondeath} fallback-group episodes excluded as "
        "non-death endings (no death marker in final message -- likely "
        "step-limit truncation, not a death).",
        f"death-cause taxonomy over ALL {n_seen - n_excluded_nondeath} "
        f"classified episodes (combat + non-combat): {class_counts_all}",
        f"{n_role_unknown} of {len(records)} combat-death records have "
        "role=null (fallback group where the 'Agent-<role3>-...' tag "
        "could not be parsed from the death screen message).",
        f"avoidability verdicts matched for {n_avoid_matched}/{len(records)} "
        "combat deaths, all from c2_avoid_v11block.json (the only avoid "
        "file whose (seed, steps) pairs actually match any cache episode -- "
        "c2_avoid_block80/devref/settled correspond to different, "
        "unlogged-in-this-cache playthroughs of reused dungeon seeds; "
        "matched strictly on (seed, steps) to avoid misattributing a "
        "verdict from the wrong trajectory).",
        "final_stretch_below_half is computed from hp_trajectory_final "
        "(cache 'combat' log hp values + the terminal live frame): true "
        "if >=50% of the last ~10 trajectory points were below 50% of "
        "hpmax at that point.",
        "readiness.ac is populated from the cache's final-frame AC "
        "(available for all episodes, contrary to the task's 'if "
        "available' hedge).",
    ]

    summary = {
        "n_deaths": len(records),
        "by_class": by_class,
        "by_lesson_type": by_lesson,
        "pct_below_half_final_stretch": pct_below_half,
        "arrival_constraint_rate_by_role": arrival_rate_by_role,
        "notes": notes,
    }

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "e12_retros.json"), "w") as f:
        json.dump(records, f, indent=1)
    with open(os.path.join(RESULTS, "e12_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)

    print(f"scanned {n_seen} cache episodes")
    print(f"  canonical-sourced: {n_canonical}  fallback-sourced: "
          f"{n_fallback} (no role: {n_fallback_no_role})  "
          f"excluded non-death: {n_excluded_nondeath}")
    print(f"combat deaths kept: {len(records)}")
    print("by_class:", by_class)
    print("by_lesson_type:", by_lesson)
    print(f"pct_below_half_final_stretch: {pct_below_half}")
    print("arrival_constraint_rate_by_role:", arrival_rate_by_role)
    print("wrote results/e12_retros.json, results/e12_summary.json")


if __name__ == "__main__":
    main()

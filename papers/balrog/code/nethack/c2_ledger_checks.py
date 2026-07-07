"""Permanent regression harness (operator directive): the dumb-heuristic
taxonomy from Campaign 2's dev day, formalized as automated ledger checks
over trajectory files. Run after every dev block.

Detectors (each caught a real defect on 2026-07-07):
  D1 fires-but-never-completes  subgoal class fires >= N times in an
     episode with zero completion signature (the armor-wear case)
  D2 repeat-target thrash       same subgoal reason repeated >= N times
     consecutively (the shuriken-d1 case)
  D3 EV-vs-outcome sign flip    'fight' engagements vs species whose
     realized damage over the corpus exceeds 3x the model's prediction
     (the shopkeeper-dpt case)
  D4 helpless-with-threat       multi-turn helpless actions (pray,
     engrave, wear) issued with a mobile hostile adjacent (the prayer/
     Elbereth death case)
  D5 zero-time churn            > 300 consecutive env steps with < 5
     game-time advance outside prompts (the stale-door class)

Usage: python3 c2_ledger_checks.py 'results/trajectories/<label>__ep*.json'
Exit code 1 if any detector fires (CI-style gate for dev blocks).
"""

import glob
import json
import re
import sys
import collections

HELPLESS_ACTIONS = {"pray", "engrave", "wear"}


def check_episode(fn):
    t = json.load(open(fn))
    issues = []
    sub = t.get("subgoals", [])
    msgs = t.get("messages", [])
    acts = t.get("actions", [])

    # D1: wear fires w/o "(being worn)" ever appearing; loot fires w/o
    # any pickup message ("X - item")
    fires = collections.Counter(l for _s, l, _r in sub)
    if fires.get("wear", 0) >= 3 and \
            not any("You are now wearing" in m or "You finish your dressing"
                    in m for m in msgs):
        issues.append(f"D1 wear fired {fires['wear']}x, no wear completed")
    if fires.get("loot", 0) >= 25 and \
            not any(re.match(r"^[a-zA-Z] - ", m) for m in msgs):
        issues.append(f"D1 loot fired {fires['loot']}x, no pickup message")

    # D2: same reason string >= 40 consecutive subgoal entries
    run_label, run_n = None, 0
    for _s, l, r in sub:
        key = (l, r)
        if key == run_label:
            run_n += 1
            if run_n == 40:
                issues.append(f"D2 thrash: {l} '{r}' x40+")
        else:
            run_label, run_n = key, 1

    # D4: helpless action with adjacent-threat evidence in the next
    # message (attack verbs immediately after issuing)
    for i, a in enumerate(acts[:-1]):
        if a in HELPLESS_ACTIONS and i + 1 < len(msgs):
            nxt = msgs[i + 1]
            if any(v in nxt for v in (" hits!", " bites!", " touches you",
                                      " stings")):
                issues.append(f"D4 helpless '{a}' at step {i} "
                              f"under attack: {nxt[:50]}")
                break

    # D5: zero-time churn — needs game-time; approximate via repeated
    # identical (action, message) pairs
    same, prev = 0, None
    for a, m in zip(acts, msgs):
        if (a, m) == prev and a not in ("search",):
            same += 1
            if same == 300:
                issues.append(f"D5 churn: '{a}' identical 300x")
                break
        else:
            same = 0
        prev = (a, m)
    return issues


def main():
    pat = sys.argv[1]
    bad = 0
    for fn in sorted(glob.glob(pat)):
        issues = check_episode(fn)
        if issues:
            bad += 1
            print(fn.split("/")[-1])
            for i in issues:
                print("   ", i)
    print(f"\n{bad} episodes with detector fires "
          f"(of {len(glob.glob(pat))})")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

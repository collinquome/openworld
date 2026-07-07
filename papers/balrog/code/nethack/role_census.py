"""Dev-seed role census (Phase L): reset each seed, parse role, no play.

Purpose: per-role stratified dev sets (NH-E14) — e.g. Wizard-heavy seed lists
for Force Bolt validation. Census-only touch (reset + a handful of no-op
steps to read the welcome message / status line); these remain DEV seeds.
Range: 800-999 by default (fresh dev range per HANDOFF etiquette).

Usage: python3 role_census.py [start] [end] [out.json]
"""

import json
import re
import sys

import nh_harness as H
import nh_common as C


def censor_seed(env, seed):
    obs, info = env.reset(seed=seed)
    role = race = None
    # welcome message first
    for _ in range(3):
        msg = obs["obs"].get("text_message", "") or ""
        m = re.search(r"You are an? ([a-z ]+) (\w+) (\w+)\.", msg)
        if m:
            role, race = m.group(3), m.group(2)
            break
        obs, r, t, tr, i2 = env.step("wait")
    if role is None:
        # ttyrank fallback (same table as the agent's item-4 fallback)
        tty = obs["obs"]["tty_chars"]
        for row in (tty[22], tty[23], tty[21]):
            line = "".join(chr(c) for c in row)
            m = re.search(r"the ([A-Z][a-zA-Z -]+?)(?:  |\s*$)", line)
            if m and m.group(1).strip() in C.RANK_TO_ROLE:
                role = C.RANK_TO_ROLE[m.group(1).strip()]
                break
    return role, race


def main():
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 800
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 999
    out = sys.argv[3] if len(sys.argv) > 3 else "results/role_census.json"
    res = {}
    env = H.make_env()
    for seed in range(lo, hi + 1):
        role, race = censor_seed(env, seed)
        res[seed] = {"role": role, "race": race}
        if seed % 20 == 0:
            print(f"  {seed}: {role}", flush=True)
    env.close()
    with open(out, "w") as f:
        json.dump(res, f, indent=0)
    from collections import Counter
    print(Counter(v["role"] for v in res.values()))


if __name__ == "__main__":
    main()

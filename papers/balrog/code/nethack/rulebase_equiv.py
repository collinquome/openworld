"""Behavior-preserving EQUIVALENCE test for the s7 rule-base migration.

MODEL: claude-opus-4-8[1m] (max thinking), Phase L session 7.

Asserts that each declarative rule's condition returns EXACTLY the boolean of the
hardcoded predicate it replaced, across a sampled state space. If this passes,
the NH_RULEBASE-on procedure-layer delegations are bit-identical to flag-off by
construction (the delegated checks are the only difference). Run at open + before
any 'kept'. End-to-end trajectory equivalence is covered separately by running a
dev seed with NH_RULEBASE=0 vs =1 under a full flag config.

Usage: PYTHONPATH=pylib python3 rulebase_equiv.py
"""
import sys
import os

for _p in (os.path.join(os.path.dirname(os.path.abspath(__file__)), "pylib"),
           os.path.dirname(os.path.abspath(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import nh_rulebase as RB          # noqa: E402
import nh_common as C            # noqa: E402
import nh_agent as A             # noqa: E402

base = RB.build_default_base()
fails = []


def eq(rule_id, state, want, tag):
    got = base.check(rule_id, state)
    if bool(got) != bool(want):
        fails.append(f"{rule_id} [{tag}]: rule={got} predicate={want} state={state}")


# --- NEVER_MELEE: rule == (name in C.NEVER_MELEE) --------------------------
sample_names = sorted(C.NEVER_MELEE)[:8] + list(A.TOUCH_KILL) + \
    ["jackal", "newt", "giant spider", "shopkeeper", "grid bug", None]
for nm in sample_names:
    eq("NEVER_MELEE", RB.state_view(monster_name=nm), nm in C.NEVER_MELEE, f"nm={nm}")

# --- TOUCH_KILL_WEAPON: rule == (name in TOUCH_KILL) -----------------------
for nm in sample_names:
    eq("TOUCH_KILL_WEAPON", RB.state_view(monster_name=nm), nm in A.TOUCH_KILL, f"nm={nm}")

# --- PRAYFIX_DEFER: rule == (adj_mobile truthy) ----------------------------
for am in (True, False, None):
    eq("PRAYFIX_DEFER", RB.state_view(adj_mobile=am), bool(am), f"adj_mobile={am}")

# --- HEAL_MIDBAND: rule == (LO*max <= hp <= HI*max) ------------------------
LO, HI = A.HEAL_HP_LO, A.HEAL_HP_FRAC
for hpmax in (10, 16, 21, 40):
    for hp in range(0, hpmax + 1):
        want = (LO * hpmax <= hp <= HI * hpmax)
        eq("HEAL_MIDBAND", RB.state_view(hp=hp, hpmax=hpmax), want, f"hp={hp}/{hpmax}")
# degenerate: zero/None max -> no spurious guard
eq("HEAL_MIDBAND", RB.state_view(hp=5, hpmax=0), False, "hpmax=0")
eq("HEAL_MIDBAND", RB.state_view(hp=None, hpmax=None), False, "none")

n_checks = len(sample_names) * 2 + 3 + sum(m + 1 for m in (10, 16, 21, 40)) + 2
if fails:
    print(f"RULEBASE-EQUIV FAIL ({len(fails)} of {n_checks} checks):")
    for f in fails[:20]:
        print("  " + f)
    sys.exit(1)
print(f"RULEBASE-EQUIV GREEN: {n_checks} checks, rule conditions == migrated "
      f"predicates (NEVER_MELEE / TOUCH_KILL_WEAPON / PRAYFIX_DEFER / HEAL_MIDBAND)")
print(f"  bands: HEAL_HP_LO={LO} HEAL_HP_FRAC={HI}  NEVER_MELEE|{len(C.NEVER_MELEE)} "
      f"TOUCH_KILL|{len(A.TOUCH_KILL)}")

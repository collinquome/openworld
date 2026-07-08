"""Adjudicate the anti-faint paired block.
Proximal KPI = Fainting-incidence (fraction of episodes with maxhunger>=4).
Paired over seed: delta = P(faint|TEST) - P(faint|REF). Paired bootstrap CI over
seeds. Also hunger-death rate (starved+fainted end_reason) + per-role table +
mechanism (guard fires; seeds where REF faints and TEST does not).
Usage: python3 analyze_antifaint.py <block.jsonl>
"""
import json, sys, random

FAINT = 4  # maxhunger tier >= 4 == Fainting/Fainted


def load(fn):
    by = {}
    for l in open(fn):
        l = l.strip()
        if not l:
            continue
        d = json.loads(l)
        by.setdefault(d["seed"], {})[d["arm"]] = d
    # keep only seeds with BOTH arms and no failure
    pairs = {}
    for s, arms in by.items():
        if "REF" in arms and "TEST" in arms and \
           arms["REF"].get("maxhunger", -1) >= 0 and \
           arms["TEST"].get("maxhunger", -1) >= 0:
            pairs[s] = arms
    return pairs


def hunger_death(d):
    er = (d.get("end_reason") or "").lower()
    return ("starv" in er) or ("faint" in er) or (d.get("maxhunger", 0) >= 5)


def faint(d):
    return 1 if d.get("maxhunger", 0) >= FAINT else 0


def main():
    fn = sys.argv[1]
    pairs = load(fn)
    seeds = sorted(pairs)
    n = len(seeds)
    ref_f = [faint(pairs[s]["REF"]) for s in seeds]
    test_f = [faint(pairs[s]["TEST"]) for s in seeds]
    ref_hd = [1 if hunger_death(pairs[s]["REF"]) else 0 for s in seeds]
    test_hd = [1 if hunger_death(pairs[s]["TEST"]) else 0 for s in seeds]
    fires = [pairs[s]["TEST"].get("antifaint_fires", 0) for s in seeds]

    def rate(x):
        return sum(x) / len(x) if x else 0.0
    dpaired = [t - r for t, r in zip(test_f, ref_f)]
    delta = rate(test_f) - rate(ref_f)
    # paired bootstrap over seeds
    random.seed(12345)
    B = 20000
    boot = []
    for _ in range(B):
        samp = [dpaired[random.randrange(n)] for _ in range(n)]
        boot.append(sum(samp) / n)
    boot.sort()
    lo, hi = boot[int(0.025 * B)], boot[int(0.975 * B)]

    print(f"=== ANTI-FAINT PAIRED BLOCK: {fn} ===")
    print(f"paired seeds (both arms, valid): n={n}")
    print(f"Fainting-incidence  REF = {rate(ref_f):.3f} ({sum(ref_f)}/{n})   "
          f"TEST = {rate(test_f):.3f} ({sum(test_f)}/{n})")
    print(f"  DELTA (TEST-REF) = {delta:+.3f}  95% paired-bootstrap CI "
          f"[{lo:+.3f}, {hi:+.3f}]")
    print(f"Hunger-death rate   REF = {rate(ref_hd):.3f} ({sum(ref_hd)}/{n})   "
          f"TEST = {rate(test_hd):.3f} ({sum(test_hd)}/{n})   "
          f"delta = {rate(test_hd)-rate(ref_hd):+.3f}")
    print(f"Guard fired (TEST): {sum(1 for f in fires if f>0)}/{n} episodes, "
          f"total fires={sum(fires)}")
    # mechanism: REF faints & TEST does not (prevented) vs regressions
    prevented = [s for s in seeds if faint(pairs[s]['REF']) and not faint(pairs[s]['TEST'])]
    regressed = [s for s in seeds if not faint(pairs[s]['REF']) and faint(pairs[s]['TEST'])]
    both = [s for s in seeds if faint(pairs[s]['REF']) and faint(pairs[s]['TEST'])]
    print(f"PREVENTED (REF faint -> TEST no-faint): {len(prevented)}  seeds={prevented}")
    print(f"REGRESSED (REF no-faint -> TEST faint): {len(regressed)}  seeds={regressed}")
    print(f"BOTH faint (guard insufficient):        {len(both)}   seeds={both}")
    # per-role
    print("\n=== PER-ROLE (REF faint / TEST faint / n / TESTfires) ===")
    roles = {}
    for s in seeds:
        role = pairs[s]["REF"].get("role") or "?"
        roles.setdefault(role, []).append(s)
    for role, ss in sorted(roles.items()):
        rf = sum(faint(pairs[s]['REF']) for s in ss)
        tf = sum(faint(pairs[s]['TEST']) for s in ss)
        fr = sum(pairs[s]['TEST'].get('antifaint_fires',0) for s in ss)
        print(f"  {role:14s} REF {rf}/{len(ss)}  TEST {tf}/{len(ss)}  fires={fr}")
    # per-seed detail on prevented/both
    print("\n=== PER-SEED (maxHunger REF->TEST, fires, ends) ===")
    for s in seeds:
        R, T = pairs[s]['REF'], pairs[s]['TEST']
        flag = ""
        if s in prevented: flag = "  <== PREVENTED"
        elif s in regressed: flag = "  <== REGRESSED"
        elif s in both: flag = "  (both faint)"
        print(f"  seed {s} {R.get('role','?')[:10]:10s} "
              f"{R.get('maxhunger_name'):8s}->{T.get('maxhunger_name'):8s} "
              f"fires={T.get('antifaint_fires',0)}"
              f" | REF:{(R.get('end_reason') or '')[:26]:26s} TEST:{(T.get('end_reason') or '')[:26]}{flag}")


if __name__ == "__main__":
    main()

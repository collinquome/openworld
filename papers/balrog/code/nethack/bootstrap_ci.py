"""CANONICAL bootstrap 95% CI (10k resamples, fixed seed 20260706).

This module is the single source of truth for every CI in the NetHack
arms (harness-audit item 5: the blind arm's independently-implemented
bootstrap produced [2.97,6.01] vs this module's [2.97,5.97] on the same
data — one implementation, one seed, everywhere). Import ci95(xs) or run
as a script.

Usage: python3 bootstrap_ci.py results/nethack_results_baseline25.json [SOTA]
"""

import json
import random
import sys

SOTA = float(sys.argv[2]) if len(sys.argv) > 2 else 6.8


def ci95(xs, nboot=10_000, seed=20260706):
    """Canonical percentile bootstrap CI of the mean."""
    n = len(xs)
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(xs, k=n)) / n for _ in range(nboot))
    return means[int(0.025 * nboot) - 1], means[int(0.975 * nboot) - 1]


def main():
    doc = json.load(open(sys.argv[1]))
    xs = [e["progression"] * 100 for e in doc["episodes"]]
    n = len(xs)
    mean = sum(xs) / n
    lo, hi = ci95(xs)
    print(f"n={n} mean={mean:.2f}  bootstrap 95% CI [{lo:.2f}, {hi:.2f}]")
    if lo > SOTA:
        verdict = f"CI excludes SOTA {SOTA} from above: decisively above SOTA"
    elif hi < SOTA:
        verdict = f"CI excludes SOTA {SOTA} from below: below SOTA"
    else:
        verdict = f"CI straddles SOTA {SOTA}: at SOTA level"
    print(verdict)
    return {"n": n, "mean": mean, "ci95": [lo, hi], "verdict": verdict}


if __name__ == "__main__":
    out = main()
    doc = json.load(open(sys.argv[1]))
    doc["bootstrap"] = out
    json.dump(doc, open(sys.argv[1], "w"), indent=1)

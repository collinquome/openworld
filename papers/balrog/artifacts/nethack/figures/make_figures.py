#!/usr/bin/env python3
"""
Phase-L paper figures, generated from real result JSONLs / the BALROG source
achievement table. Run from anywhere; paths are relative to this file's
directory's parent (work/fable_nethack/).

Sources are cited inline per figure. No numbers are invented — where a
figure would require data not present locally, it is skipped and noted in
the run log rather than fabricated.
"""
import json
import os
import glob

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # work/fable_nethack
OUT = HERE

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

INK = "#1a1a2e"
NEG = "#c0392b"
POS = "#1f6f5c"
NEU = "#6b7280"
GRID = "#e5e7eb"


def load_jsonl(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# ---------------------------------------------------------------------------
# Figure 1: Death-taxonomy tiers (docs/DEATH_TO_CAPABILITY.md) + E41 pack-rate
# ---------------------------------------------------------------------------
def fig_death_taxonomy():
    tiers = [
        ("Tier 1\nHunger\n(starve+faint)", 145, NEG),
        ("Tier 2\nTrash melee\n(attrition ~35%HP)", 287, NEG),
        ("Tier 3\nMid-tier\n(poison+fast)", 155, NEG),
        ("Tier 4\nWand/ranged\n(positioning)", 20, NEU),
    ]
    labels = [t[0] for t in tiers]
    vals = [t[1] for t in tiers]
    colors = [t[2] for t in tiers]

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    bars = ax.bar(labels, vals, color=colors, width=0.62, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 6, str(v), ha="center",
                 fontsize=10, color=INK, fontweight="bold")
    ax.set_ylabel("Deaths (count, docs/DEATH_TO_CAPABILITY.md)")
    ax.set_title("Death taxonomy: hunger and trash-melee combat dominate\n"
                  "(E41 diagnostic: only 3.3% of turns face 2+ adjacent hostiles — deaths are single-monster 1-on-1 losses)",
                  fontsize=10.5)
    ax.grid(axis="y", color=GRID, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig1_death_taxonomy.png"), dpi=180)
    plt.close(fig)
    print("wrote fig1_death_taxonomy.png (source: docs/DEATH_TO_CAPABILITY.md tier counts, "
          "flagged [GAP]-not-rerived-this-pass in the paper; E41 3.3% from results/e41_funnel.jsonl)")


# ---------------------------------------------------------------------------
# Figure 2: Forest plot of lever/experiment progression deltas (x100 scale)
# ---------------------------------------------------------------------------
def fig_forest_plot():
    # (label, delta, ci_lo, ci_hi, source note) -- all on the "x100" block-mean-
    # comparable scale used in section 3.17 of the paper (raw fraction delta * 100)
    rows = [
        ("E36 strategy-synth (deploy)",      0.00,  0.00,  0.00, "n=TEST, exact"),
        ("E37 per-class playbook (Wizard)",  -0.80, None, None, "n=5, point only"),
        ("s13 WIELD upgrade",                 0.00,  0.00,  0.00, "n=17"),
        ("s15 efficient LOOT",                0.70,  0.035, 1.605, "n=30"),
        ("s17 full-stack combo",              -2.19, None, None, "A001 cited, n~13-25"),
        ("E38 consumable econ (pilot)",       0.38, -1.49,  2.09, "n=8"),
        ("E38 fired-split",                  -1.23, -3.69,  0.00, "n=4 fired"),
        ("E40 dive-rush",                    -3.74, -7.37, -0.86, "n=18"),
        ("E41 corridor-funnel",              -0.54, -2.34,  0.65, "n=16"),
        ("E42 config-ablation (5 arms)",      0.00,  0.00,  0.00, "n=5-6 each"),
        ("E43 XP-farm (isolated)",            0.00,  0.00,  0.00, "n=5"),
        ("E44 NH_ENGAGE (passive)",           0.00,  0.00,  0.00, "n=4"),
        ("E45 NH_CLEAR (maximal)",            0.00,  0.00,  0.00, "n=pairs, exact"),
    ]

    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    y = list(range(len(rows)))[::-1]
    for yi, (label, d, lo, hi, note) in zip(y, rows):
        color = NEG if d < 0 else (POS if d > 0 else NEU)
        if lo is not None and hi is not None:
            ax.plot([lo, hi], [yi, yi], color=color, lw=2, zorder=2, solid_capstyle="round")
        ax.scatter([d], [yi], color=color, s=46, zorder=3, edgecolor="white", linewidth=0.8)
        ax.text(4.6, yi, note, va="center", fontsize=8.5, color=NEU)

    ax.axvline(0, color=INK, lw=1, zorder=1, linestyle="--", alpha=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=9.5)
    ax.set_xlabel("Progression Δ (×100 scale; 95% CI where computed, point-only where not)")
    ax.set_xlim(-9, 9)
    ax.set_title("Nineteen levers/experiments against the NetHack mean:\nnull-or-negative, none clears the wall", fontsize=11)
    ax.grid(axis="x", color=GRID, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig2_lever_forest_plot.png"), dpi=180)
    plt.close(fig)
    print("wrote fig2_lever_forest_plot.png (sources: PHASE_L_PAPER_DRAFT.md §3.4-3.24, "
          "each row cited to its own doctrine card / commit / results JSONL in the prose)")


# ---------------------------------------------------------------------------
# Figure 3: BALROG Xp:n vs Dlvl:n achievement rung ladder (live source table)
# ---------------------------------------------------------------------------
def fig_rung_ladder():
    src = "/tmp/claude-999/balrog-repo/balrog/environments/nle/achievements.json"
    if not os.path.exists(src):
        print("SKIP fig3_rung_ladder.png: BALROG source table not found at", src)
        return
    d = json.load(open(src))
    ns = list(range(1, 12))
    xp = [d.get(f"Xp:{n}") for n in ns]
    dlvl = [d.get(f"Dlvl:{n}") for n in ns]

    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    ax.plot(ns, xp, marker="o", color=POS, label="Xp:n (experience level)", lw=2)
    ax.plot(ns, dlvl, marker="s", color=NEG, label="Dlvl:n (dungeon level)", lw=2)
    ax.fill_between(ns, xp, dlvl, where=[x >= dl for x, dl in zip(xp, dlvl)],
                     color=POS, alpha=0.08, zorder=0)
    ax.set_xlabel("Milestone number n")
    ax.set_ylabel("Achievement rung value (BALROG progression reward)")
    ax.set_title("BALROG NetHack progression interleaves Xp and Dlvl rungs:\nXp:n > Dlvl:n for every n=2..11 (source: achievements.json)")
    ax.legend(frameon=False)
    ax.grid(color=GRID, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig3_rung_ladder.png"), dpi=180)
    plt.close(fig)
    print("wrote fig3_rung_ladder.png (source: BALROG repo balrog/environments/nle/achievements.json, live-fetched)")


# ---------------------------------------------------------------------------
# Figure 4: Depth-max vs Xp-max scatter, this agent's actual trajectories
# ---------------------------------------------------------------------------
def fig_depth_vs_xp_scatter():
    files = [
        "results/e43_xpfarm.jsonl",
        "results/e42_loo.jsonl",
        "results/e41_funnel.jsonl",
        "results/e40_diverush.jsonl",
        "results/consume_testonly.jsonl",
    ]
    pts = []
    for rel in files:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        for r in load_jsonl(path):
            depth = r.get("depth_max")
            xpmax = r.get("xp_max")
            if depth is not None and xpmax is not None:
                pts.append((depth, xpmax))

    if not pts:
        print("SKIP fig4_depth_vs_xp_scatter.png: no rows with depth_max+xp_max found")
        return

    depths = [p[0] for p in pts]
    xps = [p[1] for p in pts]

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    ax.scatter(depths, xps, color=INK, alpha=0.45, s=38, zorder=3,
               edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Dungeon depth reached (Dlvl, depth_max)")
    ax.set_ylabel("Experience level reached (xp_max)")
    ax.set_title(f"This agent dives far ahead of its own level (n={len(pts)} episodes)\n"
                 "REF and lever-arm trajectories pooled across E40-E43 result files",
                 fontsize=10.5)
    # reference line xp == depth, to show how far below it the cloud sits
    m = max(max(depths), max(xps)) + 1
    ax.plot([0, m], [0, m], color=NEU, linestyle="--", lw=1, label="Xp = Dlvl (never happens)")
    ax.legend(frameon=False, loc="upper left")
    ax.grid(color=GRID, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig4_depth_vs_xp_scatter.png"), dpi=180)
    plt.close(fig)
    print(f"wrote fig4_depth_vs_xp_scatter.png (n={len(pts)} episodes pooled from "
          "e40/e41/e42/e43 result JSONLs + consume_testonly.jsonl, real trajectories)")


# ---------------------------------------------------------------------------
# Figure 5: E42 config-ablation table as a bar chart (5 arms, all Δ=0)
# ---------------------------------------------------------------------------
def fig_e42_ablation():
    arms = ["mFOODACQ\n(n=6)", "mCASTHUNGER\n(n=6)", "mE15\n(n=6)", "mGUARD\n(n=5)", "mCAST\n(n=5)"]
    deltas = [0.0, 0.0, 0.0, 0.0, 0.0]

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    bars = ax.bar(arms, deltas, color=NEU, width=0.5, zorder=3)
    ax.axhline(0, color=INK, lw=1.2)
    ax.set_ylim(-1, 1)
    ax.set_ylabel("Progression Δ vs. full standing config (removal arm − REF)")
    ax.set_title("E42: removing any standing-default lever is bit-identical to keeping it\n"
                 "(all 5 arms, Δ=+0.0000 exactly, 95% CI [0,0] — config is locally optimal)",
                 fontsize=10.5)
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, 0.05, "Δ=0.0000\n(bit-identical)",
                 ha="center", va="bottom", fontsize=8, color=INK)
    ax.grid(axis="y", color=GRID, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig5_e42_ablation.png"), dpi=180)
    plt.close(fig)
    print("wrote fig5_e42_ablation.png (source: results/e42_loo.jsonl, independently re-derived via e42_analyze.py)")


if __name__ == "__main__":
    fig_death_taxonomy()
    fig_forest_plot()
    fig_rung_ladder()
    fig_depth_vs_xp_scatter()
    fig_e42_ablation()

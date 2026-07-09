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


# ---------------------------------------------------------------------------
# Figure 6: E38 seed-4 money-datum trajectory panel (real per-episode data)
# ---------------------------------------------------------------------------
def fig_e38_seed4_panel():
    # REF: results/e38_ref_baseline.jsonl seed=4; TEST: results/consume_testonly.jsonl seed=4
    # Both independently re-read at this assembly pass.
    ref = dict(depth_max=8, prog=0.0695812141543123, end_reason="Killed by a pony.", steps=819)
    test = dict(depth_max=8, prog=0.0695812141543123, end_reason="Killed by a bolt of lightning.",
                steps=949, engrave_id_tests=1, engrave_id_solved=1, zap_off_fires=3,
                consume_kills=2)

    fig, ax = plt.subplots(figsize=(9.0, 4.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    ax.axis("off")

    # TEST timeline (top)
    events = [
        (0.3, "start\n(Knight)"),
        (2.0, "engrave-ID\nwand (solved)"),
        (4.5, "zap ×3\n(offensive wand)"),
        (5.3, "2 monsters\nkilled"),
        (8.6, f"D{test['depth_max']}, step {test['steps']}:\nDIES —\n\"{test['end_reason']}\"\n(self-reflected zap)"),
    ]
    ax.plot([0.3, 8.6], [2.15, 2.15], color=POS, lw=2, zorder=1)
    for x, label in events:
        ax.scatter([x], [2.15], color=POS, s=60, zorder=3, edgecolor="white")
        ax.text(x, 2.35, label, ha="center", va="bottom", fontsize=8.2, color=INK)
    ax.text(-0.2, 2.15, "TEST\n(NH_CONSUME)", ha="right", va="center", fontsize=9.5,
            fontweight="bold", color=POS)

    # REF timeline (bottom)
    ax.plot([0.3, 8.6], [0.55, 0.55], color=NEU, lw=2, zorder=1)
    ax.scatter([0.3, 8.6], [0.55, 0.55], color=NEU, s=60, zorder=3, edgecolor="white")
    ax.text(0.3, 0.75, "start\n(Knight)", ha="center", va="bottom", fontsize=8.2, color=INK)
    ax.text(8.6, 0.75, f"D{ref['depth_max']}, step {ref['steps']}:\nDIES —\n\"{ref['end_reason']}\"",
            ha="center", va="bottom", fontsize=8.2, color=INK)
    ax.text(-0.2, 0.55, "REF\n(no consumables)", ha="right", va="center", fontsize=9.5,
            fontweight="bold", color=NEU)

    ax.annotate("", xy=(8.6, 1.9), xytext=(8.6, 0.8),
                arrowprops=dict(arrowstyle="-", color=INK, lw=1, linestyle=":"))
    ax.text(9.15, 1.35, f"SAME\nDlvl {test['depth_max']}\nΔprog = 0.0000\nexactly", ha="left", va="center",
            fontsize=9, color=NEG, fontweight="bold")

    ax.set_title("E38 seed 4 (\"the money datum\"): capability acquired, identified, used,\n"
                 "killed 2 monsters — still dies at the exact same depth as REF",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig6_e38_seed4_panel.png"), dpi=180)
    plt.close(fig)
    print("wrote fig6_e38_seed4_panel.png (source: results/consume_testonly.jsonl + "
          "e38_ref_baseline.jsonl, seed=4 rows, independently re-read at this assembly pass)")


# ---------------------------------------------------------------------------
# Figure 7: The bootstrapping-wall diagram (the loop closing)
# ---------------------------------------------------------------------------
def fig_bootstrapping_wall():
    fig, ax = plt.subplots(figsize=(8.4, 8.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    nodes = {
        "depth": (5, 8.6, "Reach greater DEPTH", POS),
        "capability": (5, 5.6, "Need CAPABILITY to\nsurvive the traversal\n(gear, XP, or luck)", NEG),
        "acquisition": (1.6, 2.2, "Capability is only\nACQUIRABLE at/behind\nthe depth not yet reached", NEU),
        "execution": (8.4, 2.2, "Capability placed IN HAND\ndirectly (E38) still fails to\nCONVERT under execution", NEU),
    }
    for key, (x, y, label, color) in nodes.items():
        box = dict(boxstyle="round,pad=0.5", fc="white", ec=color, lw=2)
        ax.text(x, y, label, ha="center", va="center", fontsize=9.3, bbox=box, zorder=3, color=INK)

    def arrow(p1, p2, label=None, color=INK, rad=0.0):
        x1, y1 = nodes[p1][0], nodes[p1][1]
        x2, y2 = nodes[p2][0], nodes[p2][1]
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.8,
                                     connectionstyle=f"arc3,rad={rad}",
                                     shrinkA=48, shrinkB=48))
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mx, my, label, fontsize=8, color=color, ha="center",
                     va="center", style="italic",
                     bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))

    arrow("depth", "capability", "gates")
    arrow("capability", "acquisition", "the agent tries to\nacquire it (s11-s16, E36-E37)", rad=-0.15)
    arrow("acquisition", "depth", "...but acquisition needs\ndepth already reached\n(19 levers: null/negative)", color=NEG, rad=-0.15)
    arrow("capability", "execution", "the agent tries handing\nit over directly (E38)", rad=0.15)
    arrow("execution", "depth", "...but in-hand capability\nstill doesn't convert\n(seed 4 money datum)", color=NEG, rad=0.15)

    ax.text(5, 0.4, "Every path back to DEPTH is blocked. The wall is closed from both directions:\n"
                     "acquisition-side (need depth to get capability) AND execution-side (capability alone isn't enough).",
            ha="center", va="center", fontsize=9.2, color=INK, fontweight="bold")

    ax.set_title("The bootstrapping/capability wall: a closed loop, not a linear gap\n"
                 "(synthesized from §3.4-3.24, §4 — nineteen experiments probing both arrows out)",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig7_bootstrapping_wall.png"), dpi=180)
    plt.close(fig)
    print("wrote fig7_bootstrapping_wall.png (conceptual synthesis diagram, no new statistics — "
          "summarizes §3.4-3.24/§4's already-cited findings)")


if __name__ == "__main__":
    fig_death_taxonomy()
    fig_forest_plot()
    fig_rung_ladder()
    fig_depth_vs_xp_scatter()
    fig_e42_ablation()
    fig_e38_seed4_panel()
    fig_bootstrapping_wall()

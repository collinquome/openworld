"""HISTORY BROWSER (operator directive 2026-07-07 s2): render the
already-logged channels into human-browsable pages.

MODEL: Fable 5 (max reasoning), session 2.

1. Per-episode HISTORY.md from a trajectory JSON: timeline of
   decisions-with-reasons (subgoal/goal ledger), knowledge acquired
   (firsts, store events), fights + notable events (ev log), strategy
   notes, death line.
2. Cross-episode KNOWLEDGE INDEX: rule cards (grepped live from
   nh_agent.py), principles + algorithm catalog pointers, verified
   loops — the agent's one-page "what I know" snapshot, regenerated
   each session.

Usage:
  python3 history_render.py episode <traj.json> [--out HISTORY_<tag>.md]
  python3 history_render.py index [--out KNOWLEDGE_INDEX.md]
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def render_episode(fn, out=None):
    t = json.load(open(fn))
    st = t.get("store") or {}
    lines = [f"# HISTORY — {t.get('task')} seed {t.get('seed')} "
             f"({t.get('condition')})", ""]
    lines.append(f"MODEL provenance: render by history_render.py "
                 f"(Fable 5 max); data = logged trajectory channels.")
    lines.append("")
    # story-so-far (code-maintained narrative, NH-E18)
    story = st.get("story") or []
    if story:
        lines.append("## Story so far (code-maintained)")
        for s in story:
            lines.append(f"- {s if isinstance(s, str) else json.dumps(s)}")
        lines.append("")
    # firsts / awards
    firsts = st.get("firsts") or []
    if firsts:
        lines.append("## Firsts (awards)")
        for f0 in firsts:
            lines.append(f"- {json.dumps(f0)}")
        lines.append("")
    # notable events (ev ledger)
    evs = t.get("evs") or []
    if evs:
        lines.append("## Event ledger (decisions with reasons)")
        for step, txt in evs:
            lines.append(f"- step {step}: {txt}")
        lines.append("")
    # notes channel (percept/goal notes)
    notes = t.get("notes") or []
    if notes:
        lines.append("## Notes channel (last 80)")
        for n in notes[-80:]:
            lines.append(f"- {n}")
        lines.append("")
    txt = "\n".join(lines) + "\n"
    if out:
        open(out, "w").write(txt)
        print("wrote", out)
    return txt


def render_index(out=None):
    lines = ["# KNOWLEDGE INDEX — what the agent knows (regenerated "
             "per session)", ""]
    src = open(os.path.join(HERE, "nh_agent.py")).read()
    cards = re.findall(r"# (RULE CARD \[[^\]]+\][^\n]*(?:\n    #[^\n]*)*)",
                       src)
    lines.append(f"## Rule cards in the decision layer ({len(cards)})")
    for c in cards:
        head = c.split("\n")[0].replace("RULE CARD ", "")
        lines.append(f"- {head}")
    lines.append("")
    lines.append("## Principles: papers/balrog/priors/PRINCIPLES.md "
                 "(P1–P7; P7 validated-by-incident)")
    lines.append("## Algorithms: papers/balrog/priors/ALGORITHM_CATALOG.md "
                 "(A1–A12 + registered unbuilt)")
    lines.append("## Verified loops (RENEWABLE ledger): none verified yet "
                 "— candidates: prayer-at-Weak food cycle, nurse-heal")
    lines.append("## KB: wiki_kb.sqlite 15 pages + kb_prices.json "
                 "(price-ID + wand ray/beam table)")
    lines.append("## Gym syllabus: TRASH 313 / MELEE+ 161 / STARV 160 / "
                 "SPIDANT 80 / RANGED 43 (794 branchable scenarios)")
    lines.append("## Coverage matrix: 16.4% weighted fill, 28 open "
                 "hypotheses (results/coverage_matrix.json)")
    txt = "\n".join(lines) + "\n"
    if out:
        open(out, "w").write(txt)
        print("wrote", out)
    return txt


if __name__ == "__main__":
    mode = sys.argv[1]
    out = None
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    if mode == "episode":
        render_episode(sys.argv[2], out)
    else:
        render_index(out)

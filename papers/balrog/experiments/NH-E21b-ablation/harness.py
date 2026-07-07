"""E21b-ablation harness: 4 arms over the fresh composition worlds.

The tested skill is a single KEY DECISION at the gate. Room traversal is
scripted (navigation is not what the ablation studies), so each episode makes at
most one LLM call. The arms differ ONLY structurally:

  1. CODE-ONLY   : no LLM. A fixed procedural "explore + greedy-goal" policy with
                   a baked-in avoid_damage rule and no fact-composition.
  2. NO-MEMORY   : LLM sees ONLY the gate room's own text (no accumulated store).
  3. NO-OVERRIDE : LLM + full observation store (openworld.MemoryStore), but
                   avoid_damage is a HARD constraint: any damaging choice is
                   vetoed and replaced by a safe fallback.
  4. FULL        : LLM + memory + override authority (may suspend avoid_damage
                   when reasoning concludes the damage is the key).

Memory is grounded in the real framework: arms 3 and 4 load every observed fact
into `openworld.MemoryStore` and recall against the gate prompt.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))  # repo root -> openworld
from openworld.memory import MemoryStore  # real framework memory

from worldgen import World, KeyAction

MODEL = os.environ.get("E21B_MODEL", "haiku")


# ----------------------------- LLM adapter --------------------------------
def llm_decide(prompt: str, model: str = MODEL, timeout: int = 150, retries: int = 2) -> Dict:
    """One gate decision via the Claude CLI (OAuth). Returns parsed JSON or {}.

    The stale ANTHROPIC_API_KEY is stripped so the CLI uses subscription auth.
    Retries on timeout/unparseable output so transient CLI slowness does not
    corrupt a cell (each attempt is an independent, fresh call).
    """
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)
    sys_preamble = (
        "You are an agent solving a one-room gate puzzle. Read the observations, "
        "reason briefly, then choose exactly one action from the legal list that "
        "will OPEN the gate. Reply with ONLY a JSON object: "
        '{"action": "<verb:arg exactly as listed>", "reason": "<one sentence>"}.'
    )
    full = sys_preamble + "\n\n" + prompt
    last = {"action": None, "reason": "no-attempt", "raw": ""}
    for attempt in range(retries + 1):
        try:
            out = subprocess.run(
                ["claude", "-p", "--model", model, full],
                capture_output=True, text=True, timeout=timeout, env=env,
            ).stdout
            last = _parse(out)
            if last.get("action"):
                return last
        except subprocess.TimeoutExpired:
            last = {"action": None, "reason": f"timeout(attempt{attempt})", "raw": ""}
    return last


def _parse(text: str) -> Dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {"action": None, "reason": "unparseable", "raw": text[:200]}
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        # tolerate trailing prose / fences
        try:
            obj = json.loads(m.group(0).split("}\n")[0] + "}")
        except Exception:
            return {"action": None, "reason": "badjson", "raw": text[:200]}
    obj.setdefault("reason", "")
    obj["raw"] = text[:200]
    return obj


# ----------------------------- prompt builder -----------------------------
def gate_prompt(world: World, facts: List[str]) -> str:
    legal = [a.token() for a in world.gate_actions]
    fact_block = "\n".join(f"- {f}" for f in facts) if facts else "- (you recall nothing else)"
    return (
        "GOAL: open the sealed gate and reach the treasure beyond it.\n\n"
        "OBSERVATIONS YOU HAVE:\n" + fact_block + "\n\n"
        f"LEGAL ACTIONS (choose one, copy the string exactly): {legal}\n\n"
        "Notes: 'present:<relic>' offers a relic; 'brave:<hazard>' means you step "
        "into a hazard and take 1 damage. Some gates open only to a specific relic; "
        "some wards open only to a specific self-inflicted pain. Decide which single "
        "action opens THIS gate."
    )


# ----------------------------- arms ---------------------------------------
@dataclass
class Episode:
    arm: str
    world: World
    chosen: Optional[str] = None
    solved: bool = False
    vetoed: bool = False            # NO-OVERRIDE: correct-but-damaging was blocked
    identified_correct: bool = False  # LLM picked the opening action (pre-veto)
    reason: str = ""
    facts_seen: List[str] = field(default_factory=list)


def _action_by_token(world: World, token: Optional[str]) -> Optional[KeyAction]:
    for a in world.gate_actions:
        if a.token() == token:
            return a
    return None


def run_code_only(world: World) -> Episode:
    """Procedural explore + greedy-goal. No composition, hard avoid_damage."""
    ep = Episode(arm="code_only", world=world)
    facts = world.facts_before_gate() + [world.gate_room().fact]
    ep.facts_seen = facts
    blob = " ".join(facts).lower()
    safe_actions = [a for a in world.gate_actions if not a.damaging]
    # Rule 1: direct instruction "present the <item>" (handles class A).
    m = re.search(r"present the ([a-z\-]+)", blob)
    chosen = None
    if m:
        want = f"present:{m.group(1)}"
        if _action_by_token(world, want):
            chosen = want
    # Rule 2: greedy single-token heuristic — the last relic name mentioned.
    if chosen is None and safe_actions:
        names = re.findall(r"(chalice|lantern|sigil-stone|reed-flute|iron-comb)", blob)
        if names:
            last = names[-1]
            cand = _action_by_token(world, f"present:{last}")
            chosen = cand.token() if cand else safe_actions[0].token()
        else:
            chosen = safe_actions[0].token()
    # avoid_damage is HARD in the procedure: brave:* is never selectable.
    ep.chosen = chosen
    act = _action_by_token(world, chosen)
    ep.solved = bool(act and act.opens)
    ep.reason = "procedural: string-trigger + greedy relic, avoid_damage hard-coded"
    return ep


def run_llm_arm(world: World, arm: str, model: str = MODEL, trial: int = 0) -> Episode:
    ep = Episode(arm=arm, world=world)
    if arm == "no_memory":
        facts = [world.gate_room().fact]          # only current-room obs
    else:
        # full accumulated store, grounded in the real MemoryStore
        store = MemoryStore()
        for i, f in enumerate(world.facts_before_gate() + [world.gate_room().fact]):
            store.add(f"obs{i}", f)
        # recall everything (small store) against the gate goal
        facts = [val for _c, val, _s in store.recall("open the sealed gate", k=len(store))]
    ep.facts_seen = facts
    decision = llm_decide(gate_prompt(world, facts), model=model)
    token = decision.get("action")
    ep.reason = decision.get("reason", "")[:200]
    act = _action_by_token(world, token)
    ep.identified_correct = bool(act and act.opens)
    if arm == "no_override" and act and act.damaging:
        # HARD constraint: veto damage, fall back to a safe action.
        ep.vetoed = True
        safe = next((a for a in world.gate_actions if not a.damaging), None)
        act = safe
        ep.chosen = safe.token() if safe else None
    else:
        ep.chosen = token
    ep.solved = bool(act and act.opens)
    return ep

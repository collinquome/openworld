"""LLM-STRATEGIST advisory consult — the ADVISORY-PUSH arm (Arm B) on REAL
NetHack. Phase L session 8, claude-opus-4-8[max].

WHY: every intuition result in the program so far is from COMPOSITION worlds
(E21b). This module is the never-run test of the thesis on NetHack itself: at
LOW-frequency strategic triggers the code hands a live LLM strategist the
CONTEXT_SPEC package (map + memory + story, nh_store.ctx_package) PLUS the
survival rule base's pushed ADVISORY reminders (nh_rulebase.RuleBase
.reminders_text) and gets back a STRUCTURED strategy the code executes. The
paired block (code-only vs +advisory) answers the Phase-E gate: does live
intuition + the rule base beat pure compiled code on real NetHack?

AUTH: the env ANTHROPIC_API_KEY is disabled for runtime auth (operator moved
agents to Max OAuth). We therefore call the headless `claude -p` CLI with
ANTHROPIC_API_KEY UNSET so it falls back to the subscription login. No key in
the batch. Every consult (prompt + raw response) is logged VERBATIM.

STRATEGY MENU (each is code-executable at the strategic layer; tactics/safety
stay with the procedure layer — strategist proposes, code disposes):
  DESCEND   head for the down-stairs now; skip loot/explore detours
  EXPLORE   keep exploring this level before descending
  DISENGAGE break contact from threats (opens the E15 disengage window)
  REST      recover HP where safe before continuing
  FIGHT     no strategic redirect; let the combat layer run
  PRESS_ON  no override; continue the compiled policy
"""
from __future__ import annotations

import json
import os
import subprocess

STRATEGIES = {"DESCEND", "EXPLORE", "DISENGAGE", "REST", "FIGHT", "PRESS_ON"}

_PROMPT = """You are an expert NetHack strategist advising a code-driven agent \
that plays the early dungeon. The code handles all tactics (pathfinding, \
combat, prompts); YOU pick the high-level strategy for the next stretch. The \
north star is DESCENT SURVIVAL: reach greater depth without dying to an \
avoidable exchange. Deaths in this agent are dominated by arriving at a new \
floor under-prepared and being killed in an early exchange.

{context}

{reminders}

TRIGGER: {trigger}

Pick ONE strategy for the next stretch of play. Prefer PRESS_ON unless the \
situation clearly calls for a redirect. Reply with ONLY a JSON object, no \
prose and no code fence:
{{"strategy": "<DESCEND|EXPLORE|DISENGAGE|REST|FIGHT|PRESS_ON>", \
"objective": "<short goal>", "rationale": "<one sentence>"}}
"""


def _extract_json(s):
    """Tolerant: grab the first {...} block and parse it."""
    i = s.find("{")
    j = s.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        return json.loads(s[i:j + 1])
    except Exception:            # noqa: BLE001
        return None


def consult(context, reminders, trigger, model="", timeout=60):
    """One strategist consult. Returns a verbatim record dict:
    {trigger, prompt, raw, strategy|None, objective, rationale, error}."""
    prompt = _PROMPT.format(
        context=context[:12000],
        reminders=(reminders or "REMINDERS: (no rule-base reminders fired)"),
        trigger=trigger)
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)     # fall back to Max OAuth login
    cmd = ["claude", "-p"]
    if model:
        cmd += ["--model", model]
    cmd += [prompt]
    rec = {"trigger": trigger, "prompt": prompt, "raw": "", "strategy": None,
           "objective": "", "rationale": "", "error": None}
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout, env=env)
        rec["raw"] = (out.stdout or "").strip()
        obj = _extract_json(rec["raw"])
        if obj and obj.get("strategy") in STRATEGIES:
            rec["strategy"] = obj["strategy"]
            rec["objective"] = str(obj.get("objective", ""))[:200]
            rec["rationale"] = str(obj.get("rationale", ""))[:400]
        else:
            rec["error"] = "unparsable-or-bad-strategy"
    except Exception as e:       # noqa: BLE001
        rec["error"] = f"{type(e).__name__}:{str(e)[:160]}"
    return rec

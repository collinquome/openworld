"""
NH-E21b engine — MODEL: Sonnet subagent, spec by Fable 5 (max), Phase L session 1.

knowledge.py — the agent-facing KNOWLEDGE LOG.

This is the game's MEMORY substrate: an append-only, harness-maintained
store of facts distilled from event messages the agent has actually
experienced (obs["messages"]), plus a slot for open hypotheses the agent
(or a harness heuristic) hasn't yet confirmed. It is deliberately dumb
about *game* semantics — it only classifies message text into coarse
tags — because the point is to give an LLM arm (or the baseline) a clean,
serializable, growing record of "what have I learned so far" without
requiring it to re-derive that from raw transcript scrollback each turn.
"""

from __future__ import annotations

from typing import List, Optional


class KnowledgeLog:
    def __init__(self):
        self.facts: List[dict] = []           # [{step, text, tag}]
        self.hypotheses: List[dict] = []       # [{text, status}]
        self._seen_fact_keys = set()

    # -- ingestion -------------------------------------------------

    def ingest(self, step_no: int, messages: List[str], state: Optional[dict] = None) -> List[dict]:
        """Feed this step's event messages in. Returns the NEW facts added
        (empty list if nothing new/classifiable)."""
        added = []
        for m in messages:
            key = self._normalize(m)
            if key in self._seen_fact_keys:
                continue
            tag = self._classify(m)
            if tag is None:
                continue
            self._seen_fact_keys.add(key)
            fact = {"step": step_no, "text": m, "tag": tag}
            self.facts.append(fact)
            added.append(fact)
        return added

    # -- open hypotheses ---------------------------------------------

    def add_hypothesis(self, text: str) -> None:
        if not any(h["text"] == text for h in self.hypotheses):
            self.hypotheses.append({"text": text, "status": "open"})

    def resolve_hypothesis(self, text: str, status: str = "confirmed") -> None:
        for h in self.hypotheses:
            if h["text"] == text:
                h["status"] = status

    # -- queries -------------------------------------------------------

    def facts_by_tag(self, tag: str) -> List[dict]:
        return [f for f in self.facts if f["tag"] == tag]

    def summary_lines(self) -> List[str]:
        return [f"[{f['tag']}] {f['text']}" for f in self.facts]

    # -- serialization -------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "facts": list(self.facts),
            "hypotheses": list(self.hypotheses),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "KnowledgeLog":
        log = cls()
        log.facts = list(d.get("facts", []))
        log.hypotheses = list(d.get("hypotheses", []))
        log._seen_fact_keys = {cls._normalize(f["text"]) for f in log.facts}
        return log

    # -- classification heuristics -------------------------------------

    @staticmethod
    def _normalize(m: str) -> str:
        return m.strip().lower()

    @staticmethod
    def _classify(m: str) -> Optional[str]:
        low = m.lower()
        if "hp" in low and ("drain away" in low or "invigorat" in low or "tingle" in low):
            return "effect_hp"
        if "gate" in low and ("yields" in low or "holds firm" in low):
            return "gate"
        if "lurches sideways" in low:
            return "teleport"
        if "unlock" in low:
            return "toggle"
        if "comes into view" in low or ("revealed" in low and "nothing new" not in low):
            return "reveal"
        if "senses sharpen" in low or "senses fade" in low:
            return "visibility"
        if "drains your strength" in low or "draining sensation fades" in low:
            return "drain"
        if "flips inside out" in low or "snaps back to normal" in low:
            return "invert"
        if "notice a" in low or "you see a" in low:
            return "sighting"
        if "sign reads" in low:
            return "hint"
        if "materializes" in low:
            return "spawn"
        if "collapse" in low or "reached the goal" in low or "run out of time" in low:
            return "outcome"
        if "eat the" in low or "pick up the" in low or "drop the" in low:
            return "action"
        return None

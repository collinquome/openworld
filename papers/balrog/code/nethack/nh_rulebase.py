"""DECLARATIVE SURVIVAL RULE BASE — Phase L session 7 HEADLINE architecture.

MODEL: claude-opus-4-8[1m] (max thinking), Phase L session 7. Runtime identity
verified at open (system-prompt id = claude-opus-4-8, matches intended
assignment; Fable at usage cap) — NO mismatch.

WHY (operator's big ask, s7): the survival knowledge was SCATTERED as hardcoded
if-thens across nh_agent.py (NEVER_MELEE membership, TOUCH_KILL weapon-melee
exception, the Healer heal band, PRAYFIX prayer-defer). That is un-auditable,
un-provenanced, and gives the intuition/LLM layer nothing to read. This module
makes "scenario qualifies -> reminder/action" a FIRST-CLASS declarative object:

    Rule = {condition matcher over a served-obs STATE VIEW,
            reminder (LLM-facing) + action_tag (procedure-facing),
            severity: HARD_GUARD | ADVISORY,
            provenance x2 (knowledge = origin of the FACT,
                           insight  = origin of the IDEA + mechanism + recipe)}

TWO CONSUMERS FROM ONE BASE (operator directive):
  * PROCEDURE layer   -> RB.check(rule_id, state) returns the HARD_GUARD boolean
                         the existing decision sites act on (veto / forced line).
  * INTUITION layer   -> RB.reminders_text(state) renders the fired ADVISORY (and
                         hard-guard) rules as a REMINDERS section for LLM context
                         (the advisory-push ablation is a LATER block).

BEHAVIOR-PRESERVING MIGRATION (regression contract): each rule's condition is an
EXACT port of the predicate it replaces, so with NH_RULEBASE ON the procedure
layer's delegated checks return bit-identical booleans; with NH_RULEBASE OFF the
base is never consulted (flag-off == s6 baseline, seed-706 anchor). The
equivalence is asserted by rulebase_equiv.py over a dev-seed corpus.

STATE VIEW: a plain dict served from the agent's Atlas + inventory at the call
site (no env internals) — the same served-obs discipline as the perception
layer. Keys used by the current rules:
    role, hp, hpmax, hunger, wields_weapon, monster_name, adj_mobile
Rules read defensively via .get(); a missing key -> condition False (fail-safe,
never a spurious guard).

This base is the COMPILE TARGET for all external knowledge (wiki / forum /
ttyrec). New facts land here as rules with provenance, not as fresh if-thens.
"""
from __future__ import annotations

HARD_GUARD = "HARD-GUARD"
ADVISORY = "ADVISORY"


class Rule:
    """One declarative survival rule. `condition(state)->bool` is a pure matcher
    over the served-obs state dict; keep it a faithful port of the predicate it
    replaces so the migration is behavior-preserving."""

    __slots__ = ("id", "severity", "condition", "reminder", "action_tag",
                 "knowledge_prov", "insight_prov", "scope")

    def __init__(self, id, severity, condition, reminder, action_tag="",
                 knowledge_prov="", insight_prov="", scope=""):
        self.id = id
        self.severity = severity
        self.condition = condition
        self.reminder = reminder
        self.action_tag = action_tag
        self.knowledge_prov = knowledge_prov
        self.insight_prov = insight_prov
        self.scope = scope


class RuleBase:
    def __init__(self, rules):
        self.rules = list(rules)
        self._by_id = {r.id: r for r in self.rules}

    def get(self, rule_id):
        return self._by_id[rule_id]

    def check(self, rule_id, state):
        """PROCEDURE consumer: does this single rule fire on this state? Missing
        keys / matcher errors -> False (fail-safe: never a spurious hard guard)."""
        r = self._by_id.get(rule_id)
        if r is None:
            return False
        try:
            return bool(r.condition(state))
        except Exception:          # noqa: BLE001 — fail-safe, never spurious
            return False

    def fired(self, state):
        """All rules that fire on this state, split by severity."""
        hg, adv = [], []
        for r in self.rules:
            try:
                ok = bool(r.condition(state))
            except Exception:      # noqa: BLE001
                ok = False
            if ok:
                (hg if r.severity == HARD_GUARD else adv).append(r)
        return hg, adv

    def reminders_text(self, state):
        """INTUITION consumer: fired rules -> a REMINDERS section for LLM
        context. Hard-guards first (they bind), then advisories. Empty string
        when nothing fires (nothing to push)."""
        hg, adv = self.fired(state)
        if not (hg or adv):
            return ""
        lines = [f"- [{r.severity}] {r.id}: {r.reminder}" for r in hg + adv]
        return "REMINDERS (served from the survival rule base):\n" + \
            "\n".join(lines)


# --------------------------------------------------------------------- rules
# Sets are imported lazily inside the matchers so this module has no import-time
# dependency on nh_common (keeps the equivalence test and any doc tooling cheap).
def _never_melee_cond(s):
    from nh_common import NEVER_MELEE
    return s.get("monster_name") in NEVER_MELEE


def _touch_kill_cond(s):
    # membership port of the site check `m.name in TOUCH_KILL`; the surrounding
    # cornered / wielded / non-Monk context stays at the decision site.
    from nh_agent import TOUCH_KILL
    return s.get("monster_name") in TOUCH_KILL


def _prayfix_cond(s):
    # port of `any(m.name not in C.IMMOBILE for m in adj)` — a MOBILE hostile is
    # adjacent, so a hunger-prayer (many free turns) must be deferred.
    return bool(s.get("adj_mobile"))


def _heal_midband_cond(s):
    from nh_agent import HEAL_HP_LO, HEAL_HP_FRAC
    hp, hpmax = s.get("hp"), s.get("hpmax")
    if not hp or not hpmax:
        return False
    return HEAL_HP_LO * hpmax <= hp <= HEAL_HP_FRAC * hpmax


def build_default_base():
    """The four migrated survival guards. Extend HERE (with provenance) as the
    compile target for new wiki/forum/ttyrec knowledge."""
    return RuleBase([
        Rule(
            id="NEVER_MELEE",
            severity=HARD_GUARD,
            condition=_never_melee_cond,
            action_tag="no_bare_melee",
            reminder="Do NOT bare-hand melee this species (passive/petrifying/"
                     "engulfing/acidic touch). Disengage, or strike from range "
                     "/ with a wielded weapon per the TOUCH_KILL exception.",
            knowledge_prov="mined+source (nh_common.NEVER_MELEE; monst.c "
                           "passive/touch attack flags)",
            insight_prov="AG (verb-frontier death audit) + source read; "
                         "mechanism NOTICE-ABSENCE; recipe = 'deaths to passive "
                         "attackers -> enumerate the species set -> guard melee'."),
        Rule(
            id="TOUCH_KILL_WEAPON",
            severity=ADVISORY,
            condition=_touch_kill_cond,
            action_tag="weapon_melee_ok_touchkill",
            reminder="Cockatrice-class: petrification is a FLESH touch. When "
                     "cornered with a WIELDED weapon (non-Monk), weapon-melee is "
                     "source-safe — better than standing still to be touched.",
            knowledge_prov="source (uhitm.c: touch checks apply to "
                           "unarmed/martial hits & grabs, not wielded weapons)",
            insight_prov="AG (1 observed chickatrice corner-death, dev seed 705) "
                         "+ source read; mechanism ASK-WHY-ON-FAILURE; recipe = "
                         "'blanket never-melee froze a cornered wielder -> read "
                         "uhitm.c -> carve the wielded-weapon exception'."),
        Rule(
            id="PRAYFIX_DEFER",
            severity=HARD_GUARD,
            condition=_prayfix_cond,
            action_tag="defer_hunger_prayer",
            reminder="A MOBILE hostile is adjacent: DEFER the hunger prayer "
                     "(praying donates ~10+ free attacks). Kill or escape first; "
                     "pray only when it is truly fainting-or-die.",
            knowledge_prov="source (pray.c: prayer is a multi-turn action; the "
                           "adjacent monster gets free hits)",
            insight_prov="AG (PRAY_DEATH: hunger-prayers next to a hostile "
                         "killed the agent) ; mechanism ASK-WHY-ON-FAILURE; "
                         "recipe = 'prayer deaths carried an adjacent mobile -> "
                         "gate the prayer on adjacency below FAINTING'."),
        Rule(
            id="HEAL_MIDBAND",
            severity=ADVISORY,
            condition=_heal_midband_cond,
            action_tag="cast_heal",
            reminder="HP in the middle band [LO,HI] of max: a Healer should "
                     "cast-heal NOW (under threat) — earlier than the near-death "
                     "crisis (heals a sliver and dies) and not proactively when "
                     "safe (perturbs good runs).",
            knowledge_prov="wiki (nethackwiki Healer: cast healing for survival) "
                           "+ data (s6/s7 WHEN-refinement blocks)",
            insight_prov="WIKI + DATA; mechanism BORROW-FIELD + NOTICE-ABSENCE; "
                         "recipe = 'wiki says cast-heal -> s6 found the naive "
                         "triggers net-negative -> the WHEN is a middle HP band "
                         "under threat'."),
    ])


def state_view(role=None, hp=None, hpmax=None, hunger=None,
               wields_weapon=None, monster_name=None, adj_mobile=None):
    """Build the served-obs state dict for a rule check (helper for callers /
    tests). All fields optional; matchers read defensively."""
    return {"role": role, "hp": hp, "hpmax": hpmax, "hunger": hunger,
            "wields_weapon": wields_weapon, "monster_name": monster_name,
            "adj_mobile": adj_mobile}

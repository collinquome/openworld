"""
NH-E21b engine — MODEL: Sonnet subagent, spec by Fable 5 (max), Phase L session 1.

grammar.py — the MECHANIC GRAMMAR. This is the heart of NH-E21b.

Mechanics are composed from three kinds of primitives:

    TRIGGERS   — what event fires the mechanic
    CONDITIONS — what must hold for the effect(s) to actually apply
    EFFECTS    — what happens to the world/agent when it fires

A Mechanic = trigger + conditions[] + effects[] + flavor. World generation
(templates.py) SAMPLES mechanics from this grammar and instantiates them
with randomized bindings (colors, names, magnitudes, zone targets) drawn
from random.Random(seed) — never observable statically. The engine (game.py)
knows the ground truth; the agent-facing obs only ever sees generic,
in-world descriptions. A mechanic is "discovered" only once its trigger has
fired (conditions permitting) and the agent has experienced the resulting
event message — see Mechanic.fire().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional


# =====================================================================
# TRIGGERS
# =====================================================================
# Triggers are lightweight tags describing WHEN a mechanic is eligible to
# fire. game.py dispatches on `.kind` and matching identifying fields; the
# trigger objects carry no behavior of their own (behavior lives in the
# Effects, below).

@dataclass
class Trigger:
    kind: str


def on_touch(entity_id: str) -> "Trigger":
    """Fires when the agent steps onto the tile of `entity_id` (an item,
    interactable, gate, or hazard tile)."""
    return _Trigger("on_touch", entity_id=entity_id)


def on_carry_enter(item_class: str, zone_id: str) -> "Trigger":
    """Fires when the agent, while carrying an item of `item_class`, enters
    `zone_id`."""
    return _Trigger("on_carry_enter", item_class=item_class, zone_id=zone_id)


def on_eat(item_class: str) -> "Trigger":
    """Fires when the agent eats an item of `item_class`."""
    return _Trigger("on_eat", item_class=item_class)


def on_step_parity(k: int) -> "Trigger":
    """Fires on every step where step_count % 2 == k."""
    return _Trigger("on_step_parity", k=k)


def on_interact(entity_id: str) -> "Trigger":
    """Fires when the agent uses the 'interact' action on `entity_id`."""
    return _Trigger("on_interact", entity_id=entity_id)


def on_hp_below(x: int) -> "Trigger":
    """Fires (edge-triggered) the step the agent's HP first drops below x."""
    return _Trigger("on_hp_below", x=x)


class _Trigger(Trigger):
    """Trigger subclass that also stashes arbitrary kwargs as attributes,
    so callers can do `trig.entity_id`, `trig.zone_id`, etc."""

    def __init__(self, kind: str, **kwargs):
        super().__init__(kind)
        for k, v in kwargs.items():
            setattr(self, k, v)


# =====================================================================
# CONDITIONS
# =====================================================================

class Condition:
    def check(self, agent_state, world) -> bool:
        raise NotImplementedError

    def describe_gt(self) -> str:
        """Ground-truth human-readable description, for tests/solvers only."""
        return self.__class__.__name__


@dataclass
class Always(Condition):
    def check(self, agent_state, world) -> bool:
        return True

    def describe_gt(self) -> str:
        return "always"


@dataclass
class Carrying(Condition):
    item_class: str
    negate: bool = False

    def check(self, agent_state, world) -> bool:
        has_it = any(it.item_class == self.item_class for it in agent_state.inventory)
        return (not has_it) if self.negate else has_it

    def describe_gt(self) -> str:
        return f"{'not ' if self.negate else ''}carrying({self.item_class})"


@dataclass
class HpAbove(Condition):
    x: int

    def check(self, agent_state, world) -> bool:
        return agent_state.hp > self.x

    def describe_gt(self) -> str:
        return f"hp_above({self.x})"


@dataclass
class HpBelow(Condition):
    x: int

    def check(self, agent_state, world) -> bool:
        return agent_state.hp < self.x

    def describe_gt(self) -> str:
        return f"hp_below({self.x})"


@dataclass
class ZoneIs(Condition):
    zone_id: str

    def check(self, agent_state, world) -> bool:
        return agent_state.zone_id(world) == self.zone_id

    def describe_gt(self) -> str:
        return f"zone_is({self.zone_id})"


@dataclass
class StepCountParity(Condition):
    k: int

    def check(self, agent_state, world) -> bool:
        return agent_state.steps % 2 == self.k

    def describe_gt(self) -> str:
        return f"step_count_parity({self.k})"


@dataclass
class And(Condition):
    conditions: List[Condition]

    def check(self, agent_state, world) -> bool:
        return all(c.check(agent_state, world) for c in self.conditions)

    def describe_gt(self) -> str:
        return " and ".join(c.describe_gt() for c in self.conditions)


# =====================================================================
# EFFECTS
# =====================================================================

class Effect:
    def apply(self, agent_state, world) -> str:
        """Mutate state/world in place; return an experienced-event message."""
        raise NotImplementedError

    def describe_gt(self) -> str:
        return self.__class__.__name__


@dataclass
class HpDelta(Effect):
    n: int   # signed; negative = damage, positive = heal

    def apply(self, agent_state, world) -> str:
        before = agent_state.hp
        agent_state.hp = max(0, min(agent_state.max_hp, agent_state.hp + self.n))
        delta = agent_state.hp - before
        if delta < 0:
            return f"You feel life drain away! [{delta} HP]"
        elif delta > 0:
            return f"You feel invigorated. [+{delta} HP]"
        return "You feel a brief tingle, but nothing changes. [+0 HP]"

    def describe_gt(self) -> str:
        return f"hp_delta({self.n})"


@dataclass
class Teleport(Effect):
    zone_id: str
    dest: Optional[tuple] = None   # (x, y); if None, template must set via callback

    def apply(self, agent_state, world) -> str:
        if self.dest is None:
            z = world.zones[self.zone_id]
            self.dest = (z.x0 + z.w // 2, z.y0 + z.h // 2)
        agent_state.x, agent_state.y = self.dest
        world.reveal_zone(self.zone_id)
        return "The world lurches sideways — you are somewhere else now."

    def describe_gt(self) -> str:
        return f"teleport({self.zone_id})"


@dataclass
class ToggleGate(Effect):
    gate_id: str

    def apply(self, agent_state, world) -> str:
        world.gate_flags[self.gate_id] = True
        world.gates_by_id[self.gate_id].toggled_open = True
        return "You hear a distant mechanism unlock."

    def describe_gt(self) -> str:
        return f"toggle_gate({self.gate_id})"


@dataclass
class RevealZone(Effect):
    zone_id: str

    def apply(self, agent_state, world) -> str:
        newly = world.reveal_zone(self.zone_id)
        if self.zone_id in world.fog_locked_zones:
            # fog_locked zones are movement-blocked until known; revealing
            # both shows AND unlocks them.
            pass
        if newly:
            return "Something shifts — a part of the map you hadn't noticed comes into view."
        return "Nothing new is revealed."

    def describe_gt(self) -> str:
        return f"reveal_zone({self.zone_id})"


@dataclass
class SpawnItem(Effect):
    item_class: str
    display_name: str
    x: int
    y: int

    def apply(self, agent_state, world) -> str:
        world.add_item(self.item_class, self.display_name, self.x, self.y)
        return f"A {self.display_name} materializes nearby."

    def describe_gt(self) -> str:
        return f"spawn_item({self.item_class}@{self.x},{self.y})"


@dataclass
class InvertMovement(Effect):
    duration: int

    def apply(self, agent_state, world) -> str:
        agent_state.active_effects["invert_movement"] = self.duration
        return f"Your sense of direction flips inside out! (lasts {self.duration} steps)"

    def describe_gt(self) -> str:
        return f"invert_movement({self.duration})"


@dataclass
class DrainPerStep(Effect):
    n: int
    duration: int

    def apply(self, agent_state, world) -> str:
        agent_state.active_effects["drain_per_step"] = self.duration
        agent_state.active_effects["drain_per_step_n"] = self.n
        return f"A steady ache sets in — something is draining your strength. (lasts {self.duration} steps)"

    def describe_gt(self) -> str:
        return f"drain_per_step({self.n},{self.duration})"


@dataclass
class DoubleVisibility(Effect):
    duration: int

    def apply(self, agent_state, world) -> str:
        agent_state.active_effects["double_visibility"] = self.duration
        return f"Your senses sharpen — you can see further. (lasts {self.duration} steps)"

    def describe_gt(self) -> str:
        return f"double_visibility({self.duration})"


# =====================================================================
# MECHANIC — a bound trigger + conditions + effects, plus the hidden
# ground-truth card the engine (and only the engine / cheating solver)
# knows about.
# =====================================================================

@dataclass
class Mechanic:
    mechanic_id: str
    trigger: Trigger
    conditions: List[Condition]
    effects: List[Effect]
    info_message: Optional[str] = None   # extra flavor text always shown when triggered (any condition outcome)
    discovered: bool = False

    def conditions_met(self, agent_state, world) -> bool:
        return all(c.check(agent_state, world) for c in self.conditions)

    def fire(self, agent_state, world) -> List[str]:
        """Attempt to fire this mechanic's effects (trigger match is the
        caller's responsibility — game.py decides WHEN to call fire()).
        Returns the list of experienced-event messages, if any. Marks the
        mechanic discovered iff at least one effect actually applied OR an
        info_message was surfaced (i.e. the agent *experienced* something)."""
        messages: List[str] = []
        if not self.conditions_met(agent_state, world):
            return messages
        for eff in self.effects:
            messages.append(eff.apply(agent_state, world))
        if self.info_message:
            messages.append(self.info_message)
        if self.effects or self.info_message:
            self.discovered = True
        return messages

    def ground_truth_card(self) -> str:
        cond_desc = " & ".join(c.describe_gt() for c in self.conditions) or "always"
        eff_desc = "; ".join(e.describe_gt() for e in self.effects) or "(info only)"
        return f"[{self.mechanic_id}] {self.trigger.kind}({getattr(self.trigger, 'entity_id', getattr(self.trigger, 'item_class', ''))}) if {cond_desc} => {eff_desc}"

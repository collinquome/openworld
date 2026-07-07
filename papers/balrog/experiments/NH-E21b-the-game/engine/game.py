"""
NH-E21b engine — MODEL: Sonnet subagent, spec by Fable 5 (max), Phase L session 1.

game.py — the gym-style environment API.

    obs = env.reset(template_id, seed)
    obs, done, info = env.step(action)

Actions: "up" | "down" | "left" | "right" | "interact" | "pickup" |
         "wait" | "eat <letter>" | "drop <letter>"

obs = {
    "grid": [str, ...],           # ascii rows, visible zones only
    "messages": [str, ...],       # event strings experienced THIS step
    "state": {"hp", "pos", "zone", "inventory", "steps"},
}

info = {"mechanics_discovered", "mechanics_total", "win", "loss", "done", "steps"}

Event messages report EFFECTS as experienced — this is the discovery
channel the knowledge log (knowledge.py) is built from. The agent never
sees magnitudes, bindings, or conditions directly; it only ever sees what
happened.
"""

from __future__ import annotations

import string
from typing import Dict, List, Optional, Tuple

import world as world_mod
import templates

DELTAS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}


class Game:
    def __init__(self, max_steps: int = 200):
        self.max_steps = max_steps
        self.world: Optional[world_mod.World] = None
        self.agent: Optional[world_mod.AgentState] = None
        self.done = False
        self.win = False
        self._seen_entities = set()

    # -----------------------------------------------------------------
    def reset(self, template_id: str, seed: int) -> dict:
        self.world = templates.build(template_id, seed)
        sx, sy = self.world.start_pos
        self.agent = world_mod.AgentState(sx, sy)
        start_zone = self.world.zone_of(sx, sy)
        self.world.known_zones = {start_zone} if start_zone else set()
        self.done = False
        self.win = False
        self._seen_entities = set()
        msgs = [f"You awaken in {self._zone_name(start_zone)}."]
        msgs += self._new_sightings()
        return self._make_obs(msgs)

    # -----------------------------------------------------------------
    def step(self, action: str) -> Tuple[dict, bool, dict]:
        if self.done:
            return self._make_obs([]), True, self._make_info()

        action = (action or "").strip()
        hp_before = self.agent.hp
        self.agent.steps += 1
        msgs: List[str] = []

        if action in DELTAS:
            msgs += self._try_move(action)
        elif action == "interact":
            msgs += self._try_interact()
        elif action == "pickup":
            msgs += self._try_pickup()
        elif action == "wait":
            msgs.append("You wait.")
        elif action.startswith("eat "):
            msgs += self._try_eat(action.split(" ", 1)[1].strip())
        elif action.startswith("drop "):
            msgs += self._try_drop(action.split(" ", 1)[1].strip())
        else:
            msgs.append(f"You don't know how to '{action}'.")

        msgs += self._tick_step_mechanics(hp_before)
        msgs += self._tick_active_effects()
        msgs += self._new_sightings()

        if self.agent.hp <= 0:
            self.done = True
            self.win = False
            msgs.append("You collapse. GAME OVER.")
        elif self.agent.zone_id(self.world) == self.world.goal_zone_id:
            self.done = True
            self.win = True
            msgs.append("You have reached the goal! You win.")
        elif self.agent.steps >= self.max_steps:
            self.done = True
            self.win = False
            msgs.append("You have run out of time. GAME OVER.")

        obs = self._make_obs(msgs)
        info = self._make_info()
        return obs, self.done, info

    # -----------------------------------------------------------------
    # action handlers
    # -----------------------------------------------------------------

    def _try_move(self, action: str) -> List[str]:
        w = self.world
        a = self.agent
        dx, dy = DELTAS[action]
        if a.active_effects.get("invert_movement", 0) > 0:
            dx, dy = -dx, -dy
        nx, ny = a.x + dx, a.y + dy

        if not w.in_bounds(nx, ny):
            return ["You can't go that way."]

        target_zone = w.zone_of(nx, ny)
        if w.is_zone_fog_blocked(target_zone):
            return ["You can't find a way through here."]

        tile = w.tile(nx, ny)
        msgs: List[str] = []

        if tile == world_mod.WALL:
            return ["You bump into a wall."]

        if tile == world_mod.GATE:
            gate = w.gate_at(nx, ny)
            gm = w.mechanics.get(f"gate:{gate.gate_id}")
            is_open = gate.is_open(a, w)
            if gm is not None:
                gm.discovered = True
            if not is_open:
                return [f"The gate ({gate.gate_id}) holds firm; something about your "
                        f"situation doesn't satisfy it yet."]
            msgs.append(f"The gate ({gate.gate_id}) yields and lets you through.")

        # move
        a.x, a.y = nx, ny
        if target_zone and target_zone not in w.known_zones:
            w.known_zones.add(target_zone)
            msgs.append(f"You enter {self._zone_name(target_zone)}.")

        haz = w.hazard_at(nx, ny)
        if haz is not None:
            fired = self._fire_touch(f"hazard:{nx}:{ny}")
            if fired:
                haz.discovered = True
            msgs += fired

        ia = w.interactable_at(nx, ny)
        if ia is not None:
            msgs += self._fire_touch(ia.entity_id)

        if target_zone:
            msgs += self._fire_carry_enter(target_zone)

        return msgs

    def _try_interact(self) -> List[str]:
        w, a = self.world, self.agent
        ia = w.interactable_at(a.x, a.y)
        if ia is None:
            return ["There is nothing here to interact with."]
        fired = self._fire_interact(ia.entity_id)
        if fired:
            return fired
        return [f"You interact with the {ia.display_name}, but nothing happens."]

    def _try_pickup(self) -> List[str]:
        w, a = self.world, self.agent
        it = w.item_at(a.x, a.y)
        if it is None:
            return ["There is nothing here to pick up."]
        letter = string.ascii_lowercase[len(a.inventory) % 26]
        it.carried = True
        it.inventory_letter = letter
        it.x = it.y = None
        a.inventory.append(it)
        return [f"You pick up the {it.display_name}. (now carrying it as '{letter}')"]

    def _try_drop(self, letter: str) -> List[str]:
        w, a = self.world, self.agent
        for it in a.inventory:
            if it.inventory_letter == letter:
                a.inventory.remove(it)
                it.carried = False
                it.x, it.y = a.x, a.y
                it.inventory_letter = None
                return [f"You drop the {it.display_name}."]
        return ["You aren't carrying anything like that."]

    def _try_eat(self, letter: str) -> List[str]:
        w, a = self.world, self.agent
        target = None
        for it in a.inventory:
            if it.inventory_letter == letter:
                target = it
                break
        if target is None:
            return ["You aren't carrying anything like that to eat."]
        a.inventory.remove(target)
        msgs = [f"You eat the {target.display_name}."]
        fired = self._fire_eat(target.item_class)
        if fired:
            msgs += fired
        else:
            msgs.append("Nothing seems to happen.")
        return msgs

    # -----------------------------------------------------------------
    # mechanic dispatch
    # -----------------------------------------------------------------

    def _fire_touch(self, entity_id: str) -> List[str]:
        msgs: List[str] = []
        for m in self.world.mechanics.values():
            trig = m.trigger
            if trig.kind == "on_touch" and getattr(trig, "entity_id", None) == entity_id:
                msgs += m.fire(self.agent, self.world)
        return msgs

    def _fire_interact(self, entity_id: str) -> List[str]:
        msgs: List[str] = []
        for m in self.world.mechanics.values():
            trig = m.trigger
            if trig.kind == "on_interact" and getattr(trig, "entity_id", None) == entity_id:
                msgs += m.fire(self.agent, self.world)
        return msgs

    def _fire_eat(self, item_class: str) -> List[str]:
        msgs: List[str] = []
        for m in self.world.mechanics.values():
            trig = m.trigger
            if trig.kind == "on_eat" and getattr(trig, "item_class", None) == item_class:
                msgs += m.fire(self.agent, self.world)
        return msgs

    def _fire_carry_enter(self, zone_id: str) -> List[str]:
        msgs: List[str] = []
        for m in self.world.mechanics.values():
            trig = m.trigger
            if trig.kind == "on_carry_enter" and getattr(trig, "zone_id", None) == zone_id:
                item_class = getattr(trig, "item_class", None)
                if any(it.item_class == item_class for it in self.agent.inventory):
                    msgs += m.fire(self.agent, self.world)
        return msgs

    def _tick_step_mechanics(self, hp_before: int) -> List[str]:
        msgs: List[str] = []
        a, w = self.agent, self.world
        for m in w.mechanics.values():
            trig = m.trigger
            if trig.kind == "on_step_parity" and a.steps % 2 == getattr(trig, "k", -1):
                msgs += m.fire(a, w)
            elif trig.kind == "on_hp_below":
                x = getattr(trig, "x", None)
                if x is not None and hp_before >= x and a.hp < x:
                    msgs += m.fire(a, w)
        return msgs

    def _tick_active_effects(self) -> List[str]:
        msgs: List[str] = []
        a = self.agent
        if a.active_effects.get("drain_per_step", 0) > 0:
            n = a.active_effects.get("drain_per_step_n", 0)
            before = a.hp
            a.hp = max(0, a.hp - n)
            msgs.append(f"The drain saps your strength. [{a.hp - before} HP]")
            a.active_effects["drain_per_step"] -= 1
            if a.active_effects["drain_per_step"] <= 0:
                a.active_effects.pop("drain_per_step", None)
                a.active_effects.pop("drain_per_step_n", None)
                msgs.append("The draining sensation fades.")
        for name, fade_msg in (
            ("invert_movement", "Your sense of direction snaps back to normal."),
            ("double_visibility", "Your heightened senses fade."),
        ):
            if a.active_effects.get(name, 0) > 0:
                a.active_effects[name] -= 1
                if a.active_effects[name] <= 0:
                    a.active_effects.pop(name, None)
                    msgs.append(fade_msg)
        return msgs

    # -----------------------------------------------------------------
    # observation / rendering
    # -----------------------------------------------------------------

    def _zone_name(self, zone_id: Optional[str]) -> str:
        if zone_id is None:
            return "a corridor"
        return self.world.zones[zone_id].name

    def _tile_visible(self, x: int, y: int) -> bool:
        w, a = self.world, self.agent
        zone = w.zone_of(x, y)
        if zone is not None and zone in w.fog_locked_zones and zone not in w.known_zones:
            return False
        if zone is None or zone in w.known_zones:
            return True
        # local "doorway peek" radius so an unvisited (non-fog-locked) zone's
        # threshold tile is visible from just outside it
        return max(abs(x - a.x), abs(y - a.y)) <= 1

    def _new_sightings(self) -> List[str]:
        w = self.world
        msgs: List[str] = []
        for it in w.items:
            if it.carried or it.x is None:
                continue
            key = ("item", it.item_id)
            if key in self._seen_entities:
                continue
            if self._tile_visible(it.x, it.y):
                self._seen_entities.add(key)
                msgs.append(f"You notice a {it.display_name} here.")
        for ia in w.interactables:
            key = ("ia", ia.entity_id)
            if key in self._seen_entities:
                continue
            if self._tile_visible(ia.x, ia.y):
                self._seen_entities.add(key)
                msgs.append(f"You see a {ia.display_name} ({ia.entity_id}).")
        return msgs

    def _render_grid(self) -> List[str]:
        w, a = self.world, self.agent
        rows = []
        for y in range(w.height):
            chars = []
            for x in range(w.width):
                if not self._tile_visible(x, y):
                    chars.append(" ")
                    continue
                if (x, y) == (a.x, a.y):
                    chars.append("@")
                    continue
                it = w.item_at(x, y)
                if it is not None:
                    chars.append(str(it.item_id % 10))
                    continue
                ia = w.interactable_at(x, y)
                if ia is not None:
                    chars.append(ia.entity_id)
                    continue
                haz = w.hazard_at(x, y)
                if haz is not None and haz.discovered:
                    chars.append("^")
                    continue
                chars.append(w.tile(x, y))
            rows.append("".join(chars))
        return rows

    def _make_obs(self, messages: List[str]) -> dict:
        a = self.agent
        state = {
            "hp": a.hp,
            "pos": [a.x, a.y],
            "zone": a.zone_id(self.world),
            # ANTI-CONTAMINATION FIX (Fable 5 max, session 2, found live in
            # T1_s0 consult 4): item_class is a GROUND-TRUTH mechanic label
            # ("hazard_fruit") — serving it in obs leaks exactly what the
            # game exists to make discoverable. Obs carries display_name
            # only; internals keep item_class via agent.inventory directly.
            "inventory": [
                {"letter": it.inventory_letter,
                 "display_name": it.display_name}
                for it in a.inventory
            ],
            "steps": a.steps,
        }
        return {"grid": self._render_grid(), "messages": messages, "state": state}

    def _make_info(self) -> dict:
        w = self.world
        total = len(w.mechanics)
        discovered = sum(1 for m in w.mechanics.values() if m.discovered)
        return {
            "mechanics_discovered": discovered,
            "mechanics_total": total,
            "win": self.win,
            "loss": (self.done and not self.win),
            "done": self.done,
            "steps": self.agent.steps,
        }

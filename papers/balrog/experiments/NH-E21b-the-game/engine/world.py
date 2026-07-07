"""
NH-E21b engine — MODEL: Sonnet subagent, spec by Fable 5 (max), Phase L session 1.

world.py — tile world primitives.

A World is a single global grid subdivided into rectangular ZONES connected
by corridors (with optional typed GATEs). Entities (items, interactables,
hazard tiles) live at fixed (x, y) coordinates on the grid. Everything is
built deterministically from (template_id, seed) via random.Random(seed) —
see templates.py for the actual generators; this module only supplies the
data structures + small carving/placement utilities they share.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# --- tile chars -------------------------------------------------------

WALL = "#"
FLOOR = "."
GATE = "+"

Coord = Tuple[int, int]


# --- grid carving utilities --------------------------------------------

def new_grid(width: int, height: int) -> List[List[str]]:
    """An all-wall grid of the given size."""
    return [[WALL for _ in range(width)] for _ in range(height)]


def carve_room(grid: List[List[str]], x0: int, y0: int, w: int, h: int) -> None:
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            grid[y][x] = FLOOR


def carve_corridor(grid: List[List[str]], p0: Coord, p1: Coord) -> None:
    """Carve a straight (horizontal or vertical) 1-wide corridor between
    two points, inclusive. Only axis-aligned corridors are supported —
    templates are hand-laid-out, so this is all we need."""
    x0, y0 = p0
    x1, y1 = p1
    if y0 == y1:
        for x in range(min(x0, x1), max(x0, x1) + 1):
            grid[y0][x] = FLOOR
    elif x0 == x1:
        for y in range(min(y0, y1), max(y0, y1) + 1):
            grid[y][x0] = FLOOR
    else:
        raise ValueError("carve_corridor only supports axis-aligned segments")


def place_gate_tile(grid: List[List[str]], pos: Coord) -> None:
    x, y = pos
    grid[y][x] = GATE


# --- entities -----------------------------------------------------------

@dataclass
class Zone:
    zone_id: str
    name: str
    x0: int
    y0: int
    w: int
    h: int

    def contains(self, x: int, y: int) -> bool:
        return self.x0 <= x < self.x0 + self.w and self.y0 <= y < self.y0 + self.h


@dataclass
class Item:
    item_id: int
    item_class: str          # visible flavor category, e.g. "fruit"
    display_name: str        # visible flavor name, e.g. "waxy fruit"
    x: Optional[int]
    y: Optional[int]
    carried: bool = False
    inventory_letter: Optional[str] = None


@dataclass
class Interactable:
    entity_id: str            # e.g. "A", "B" — map glyph
    kind: str                 # "shrine" | "lever" | "lamp" | "sign"
    display_name: str
    x: int
    y: int


@dataclass
class HazardTile:
    x: int
    y: int
    mechanic_id: str
    discovered: bool = False


@dataclass
class Gate:
    gate_id: str
    x: int
    y: int
    zone_from: str
    zone_to: str
    # A gate is open if EITHER its condition (if any) evaluates True OR its
    # toggle flag has been set True by a toggle_gate effect. If both a
    # condition and requires_toggle are set, BOTH must hold (composition).
    open_condition: Optional[object] = None   # grammar.Condition or None
    requires_toggle: bool = False
    toggled_open: bool = False
    mechanic_id: Optional[str] = None         # the "you tried the gate" mechanic

    def is_open(self, agent_state, world) -> bool:
        ok = True
        if self.open_condition is not None:
            ok = ok and self.open_condition.check(agent_state, world)
        if self.requires_toggle:
            ok = ok and self.toggled_open
        return ok


@dataclass
class AgentState:
    x: int
    y: int
    hp: int = 100
    max_hp: int = 100
    inventory: List[Item] = field(default_factory=list)
    steps: int = 0
    active_effects: Dict[str, int] = field(default_factory=dict)  # name -> remaining duration

    def zone_id(self, world: "World") -> Optional[str]:
        return world.zone_of(self.x, self.y)


class World:
    def __init__(self, template_id: str, seed: int, width: int, height: int):
        self.template_id = template_id
        self.seed = seed
        self.width = width
        self.height = height
        self.grid = new_grid(width, height)
        self.zones: Dict[str, Zone] = {}
        self.gates: Dict[Coord, Gate] = {}
        self.gates_by_id: Dict[str, Gate] = {}
        self.items: List[Item] = []
        self.interactables: List[Interactable] = []
        self.hazards: Dict[Coord, HazardTile] = {}
        self.mechanics: Dict[str, "object"] = {}   # id -> grammar.Mechanic
        self.goal_zone_id: Optional[str] = None
        self.start_pos: Coord = (0, 0)
        self.fog_locked_zones: set = set()
        self.known_zones: set = set()
        self.gate_flags: Dict[str, bool] = {}
        self.ground_truth: Dict[str, object] = {}   # human-readable, solver/test only
        self._next_item_id = 1
        self._next_interactable_ord = 0

    # -- construction helpers ---------------------------------------

    def add_zone(self, zone_id: str, name: str, x0: int, y0: int, w: int, h: int,
                 fog_locked: bool = False) -> Zone:
        z = Zone(zone_id, name, x0, y0, w, h)
        self.zones[zone_id] = z
        if fog_locked:
            self.fog_locked_zones.add(zone_id)
        return z

    def add_gate(self, gate_id: str, x: int, y: int, zone_from: str, zone_to: str,
                 open_condition=None, requires_toggle: bool = False) -> Gate:
        g = Gate(gate_id, x, y, zone_from, zone_to, open_condition, requires_toggle)
        place_gate_tile(self.grid, (x, y))
        self.gates[(x, y)] = g
        self.gates_by_id[gate_id] = g
        self.gate_flags[gate_id] = False
        return g

    def add_item(self, item_class: str, display_name: str, x: int, y: int) -> Item:
        it = Item(self._next_item_id, item_class, display_name, x, y)
        self._next_item_id += 1
        self.items.append(it)
        return it

    def add_interactable(self, kind: str, display_name: str, x: int, y: int) -> Interactable:
        letter = chr(ord("A") + self._next_interactable_ord)
        self._next_interactable_ord += 1
        ia = Interactable(letter, kind, display_name, x, y)
        self.interactables.append(ia)
        return ia

    def add_hazard(self, x: int, y: int, mechanic_id: str) -> HazardTile:
        h = HazardTile(x, y, mechanic_id)
        self.hazards[(x, y)] = h
        return h

    def register_mechanic(self, mechanic) -> None:
        self.mechanics[mechanic.mechanic_id] = mechanic

    # -- queries -------------------------------------------------------

    def zone_of(self, x: int, y: int) -> Optional[str]:
        for z in self.zones.values():
            if z.contains(x, y):
                return z.zone_id
        return None

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def tile(self, x: int, y: int) -> str:
        return self.grid[y][x]

    def item_at(self, x: int, y: int) -> Optional[Item]:
        for it in self.items:
            if not it.carried and it.x == x and it.y == y:
                return it
        return None

    def interactable_at(self, x: int, y: int) -> Optional[Interactable]:
        for ia in self.interactables:
            if ia.x == x and ia.y == y:
                return ia
        return None

    def gate_at(self, x: int, y: int) -> Optional[Gate]:
        return self.gates.get((x, y))

    def hazard_at(self, x: int, y: int) -> Optional[HazardTile]:
        return self.hazards.get((x, y))

    def is_zone_fog_blocked(self, zone_id: Optional[str]) -> bool:
        return zone_id is not None and zone_id in self.fog_locked_zones and zone_id not in self.known_zones

    def reveal_zone(self, zone_id: str) -> bool:
        """Returns True if this newly revealed a previously-unknown zone."""
        if zone_id in self.known_zones:
            return False
        self.known_zones.add(zone_id)
        return True

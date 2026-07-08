"""Campaign-2 E-NH2.5: perception layer.

Structured perceptors over the Atlas belief state + served obs (no new
env touchpoints):

  Topology   — rooms/corridors/doors segmentation, room graph with exits,
               dead ends, choke cells (kite spots), room-perimeter wall
               cells (secret-door hosts)
  ThreatField— per-cell danger from the verified exchange model
               (results/c2_exchange.json), halo cells to avoid in travel
  LOSField   — cells on a clear straight ray from potentially-ranged
               monsters (line-of-fire discipline)
  ItemValue  — floor objects ranked food > ammo > armor > other, via
               object-glyph -> objclass (offline table, disclosed)

All pure functions/classes over (LevelMap, monsters, glyphs); consumed by
the policy and by the renderer.
"""

import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(_HERE, "pylib"), _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import nh_common as C
from nle import nethack as nh

ROWS, COLS = C.ROWS, C.COLS

# ---------------------------------------------------------------- exchange
_EXC = None


def exchange():
    global _EXC
    if _EXC is None:
        fn = os.path.join(_HERE, "results", "c2_exchange.json")
        _EXC = json.load(open(fn)) if os.path.exists(fn) else \
            dict(species={}, fallback=dict(slope=0.08, intercept=0.61))
    return _EXC


_PRIOR_K = 25.0


# species whose logged adjacency was mostly PEACEFUL coexistence: their
# empirical dpt is ~0 but they hit like trucks once hostile (guard killed
# 3 characters). Their dpt floors at the difficulty prior.
PEACEFUL_BIASED = {"shopkeeper", "guard", "watchman", "watch captain",
                   "vault guard", "gnome", "gnome lord", "gnomish wizard",
                   "dwarf", "dwarf lord", "dwarf king"}


def species_dpt(name, difficulty=None):
    """Expected damage to us per adjacent game turn (empirical, shrunk
    toward the difficulty prior for small n; conservative dpt for
    verification-failed species is baked into the table)."""
    ex = exchange()
    v = ex["species"].get(name)
    fb = ex["fallback"]
    if difficulty is None:
        difficulty = (v or {}).get("difficulty") or 5
    prior = fb["intercept"] + fb["slope"] * difficulty
    if v is None:
        return prior
    n = v["n_turns"]
    blend = (n * v["dpt"] + _PRIOR_K * prior) / (n + _PRIOR_K)
    if name in PEACEFUL_BIASED:
        return max(blend, prior)
    return blend


# Role conditioning: a fitted role-class kill-rate multiplier REVERSED
# under confounding (strong roles fight deeper monsters, so their pooled
# rate is lower) — hypothesis rejected by the data and dropped (select-
# don't-vote). Instead: a source-arithmetic prior (disclosed offline
# world model): monster HP ~= 4.5 * mlevel; our melee damage/turn by
# role class; blended with the pooled empirical kill rate.
STRONG_ROLES = {"Barbarian", "Valkyrie", "Samurai", "Knight", "Caveman",
                "Cavewoman", "Monk"}

_SP_LVL = {name: lvl for (name, lvl, diff, spd, cls) in
           [C._SPECIES[i] for i in range(len(C._SPECIES))]}


def species_ttk(name, difficulty=None, role=None, xplvl=1):
    """Expected adjacent turns for us to kill it (pooled empirical rate
    blended with a per-role source-arithmetic prior)."""
    ex = exchange()
    v = ex["species"].get(name)
    lvl = _SP_LVL.get(name, 3)
    our_dpt = 5.5 if role in STRONG_ROLES else 3.0
    if xplvl >= 5:
        our_dpt *= 1.3
    src_rate = min(0.5, our_dpt / max(3.0, 4.5 * lvl))
    if v is None or not v.get("kill_rate"):
        rate = src_rate
    else:
        n = v["n_turns"]
        rate = (n * v["kill_rate"] + _PRIOR_K * src_rate) / (n + _PRIOR_K)
        rate = max(rate, 0.5 * src_rate)   # pooled floor for strong roles
    return 1.0 / max(1e-4, rate)


# ---------------------------------------------------------------- topology
ROOMY = {C.FLOOR, C.FOUNTAIN, C.ALTAR, C.THRONE, C.SINK, C.ICE, C.GRAVE}
DOORS = {C.DOORWAY, C.DOOR_OPEN, C.DOOR_CLOSED}


class Topology:
    """Rooms/corridors segmentation of a LevelMap (recomputed lazily when
    the explored-cell count changes)."""

    def __init__(self):
        self._stamp = None
        self.room_id = None        # int grid, -1 none
        self.rooms = []            # dict(cells, exits, perimeter, frontier)
        self.chokes = set()        # door/narrow-corridor cells
        self.dead_ends = set()

    def refresh(self, L):
        stamp = (int(L.explored.sum()), int((L.terrain > 0).sum()))
        if stamp == self._stamp:
            return self
        self._stamp = stamp
        t = L.terrain
        self.room_id = np.full((ROWS, COLS), -1, dtype=np.int16)
        self.rooms = []
        seen = np.zeros((ROWS, COLS), dtype=bool)
        for y in range(ROWS):
            for x in range(COLS):
                if seen[y][x] or int(t[y][x]) not in ROOMY:
                    continue
                # BFS a room component (4-conn over ROOMY)
                comp = []
                stack = [(x, y)]
                seen[y][x] = True
                while stack:
                    cx, cy = stack.pop()
                    comp.append((cx, cy))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < COLS and 0 <= ny < ROWS and \
                                not seen[ny][nx] and int(t[ny][nx]) in ROOMY:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
                rid = len(self.rooms)
                exits, perim, frontier = set(), set(), set()
                for (cx, cy) in comp:
                    self.room_id[cy][cx] = rid
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if not (0 <= nx < COLS and 0 <= ny < ROWS):
                            continue
                        tt = int(t[ny][nx])
                        if tt in DOORS or tt == C.CORRIDOR:
                            exits.add((nx, ny))
                        elif tt == C.WALL and not L.inferred_wall[ny][nx]:
                            perim.add((cx, cy))
                        if not L.explored[ny][nx]:
                            frontier.add((cx, cy))
                self.rooms.append(dict(id=rid, cells=comp, exits=exits,
                                       perimeter=perim, frontier=frontier))
        # chokes + dead ends
        self.chokes, self.dead_ends = set(), set()
        for y in range(ROWS):
            for x in range(COLS):
                tt = int(t[y][x])
                if tt in DOORS:
                    self.chokes.add((x, y))
                    continue
                if tt == C.CORRIDOR:
                    deg = sum(1 for _ in L.neighbors(x, y))
                    if deg <= 2:
                        self.chokes.add((x, y))
                    if deg <= 1:
                        self.dead_ends.add((x, y))
        return self

    def search_hosts(self, L):
        """Cells worth 'search'ing: room perimeters + dead ends."""
        out = set(self.dead_ends)
        for r in self.rooms:
            out |= r["perimeter"]
        return out


# ------------------------------------------------------------- threat field
def threat_field(L, our_speed=12):
    """(danger grid, halo set). danger[y][x] = expected dpt exposure if we
    stood there now; halo = cells adjacent to a hostile with meaningful
    dpt (travel should route around them)."""
    danger = np.zeros((ROWS, COLS), dtype=np.float32)
    halo = set()
    for m in L.monsters:
        if m.pet or m.name in C.IMMOBILE:
            continue
        dpt = species_dpt(m.name, m.difficulty)
        speed_ratio = max(0.5, m.speed / our_speed)
        for y in range(max(0, m.y - 4), min(ROWS, m.y + 5)):
            for x in range(max(0, m.x - 4), min(COLS, m.x + 5)):
                d = max(abs(x - m.x), abs(y - m.y))
                if d <= 1:
                    danger[y][x] += dpt
                else:
                    danger[y][x] += dpt * min(1.0, speed_ratio) / (d * d)
        if dpt >= 0.8:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = m.x + dx, m.y + dy
                    if 0 <= nx < COLS and 0 <= ny < ROWS:
                        halo.add((nx, ny))
    return danger, halo


# --------------------------------------------------------------- LOS field
# species classes that plausibly carry/use ranged attacks (wands, thrown,
# spells): humanoid letters + soldiers/liches/nymphs etc. Source-derived
# coarse class, disclosed.
RANGED_CLASSES = set("@AKLNOTUVWYZcghiknoq")


def los_cells(L, agent):
    """Cells (within the level) lying on a clear straight 8-ray from any
    potentially-ranged non-adjacent hostile. Standing on these while it
    watches invites a zap."""
    out = set()
    ax, ay = agent
    for m in L.monsters:
        if m.pet or m.cls not in RANGED_CLASSES:
            continue
        if max(abs(m.x - ax), abs(m.y - ay)) <= 1:
            continue
        for sx in (-1, 0, 1):
            for sy in (-1, 0, 1):
                if sx == 0 and sy == 0:
                    continue
                cx, cy = m.x + sx, m.y + sy
                k = 0
                while 0 <= cx < COLS and 0 <= cy < ROWS and k < 12:
                    if not L.passable(cx, cy, doors_ok=True,
                                      bad_traps_ok=True):
                        break
                    out.add((cx, cy))
                    cx, cy = cx + sx, cy + sy
                    k += 1
    return out


# --------------------------------------------------------------- item value
AMMO_NAMES = ("dagger", "elven dagger", "orcish dagger", "silver dagger",
              "dart", "arrow", "elven arrow", "orcish arrow",
              "silver arrow", "ya", "crossbow bolt", "shuriken", "rock",
              "aklys", "spear", "elven spear", "orcish spear",
              "dwarvish spear", "javelin", "knife", "stiletto")
BODY_ARMOR = ("leather jacket", "leather armor", "orcish ring mail",
              "studded leather armor", "ring mail", "scale mail",
              "orcish chain mail", "chain mail", "banded mail",
              "splint mail", "plate mail", "crystal plate mail",
              "bronze plate mail", "elven mithril-coat",
              "dwarvish mithril-coat")
HELMETS = ("orcish helm", "dwarvish iron helm", "dented pot", "helmet",
           "helm of brilliance", "helm of opposite alignment",
           "helm of telepathy")
SHIELDS = ("small shield", "elven shield", "Uruk-hai shield",
           "orcish shield", "large shield", "dwarvish roundshield",
           "shield of reflection")
BOOTS_GLOVES = ("low boots", "iron shoes", "high boots",
                "leather gloves")
FOOD_NAMES = ("food ration", "cram ration", "lembas wafer", "K-ration",
              "C-ration", "pancake", "candy bar", "fortune cookie",
              "apple", "orange", "pear", "banana", "melon", "carrot",
              "meatball", "meat stick", "huge chunk of meat", "kelp frond",
              "slime mold", "lump of royal jelly", "cream pie",
              "sprig of wolfsbane", "clove of garlic", "egg", "tripe ration")

_OBJ_NAME = {}
for _g in range(C.GLYPH_OBJ_OFF, C.GLYPH_CMAP_OFF):
    try:
        oc = nh.objclass(_g - C.GLYPH_OBJ_OFF)
        _cls = oc.oc_class
        _cls = ord(_cls) if isinstance(_cls, str) else int(_cls)
        _OBJ_NAME[_g] = (nh.OBJ_NAME(oc) or "", _cls)
    except Exception:
        pass

FOOD_CLASS = nh.FOOD_CLASS
WEAPON_CLASS = nh.WEAPON_CLASS
ARMOR_CLASS = nh.ARMOR_CLASS
GEM_CLASS = nh.GEM_CLASS


# vectorized glyph -> (value, kind, name) lookup tables
_KINDS = ("food", "ammo", "armor", "armor2")
_GVAL = np.zeros(C.MAX_GLYPH + 2, dtype=np.float32)
_GKIND = np.full(C.MAX_GLYPH + 2, -1, dtype=np.int8)
_GNAME = {}
for _g, (_nm, _ocls) in _OBJ_NAME.items():
    if _ocls == FOOD_CLASS and _nm in FOOD_NAMES:
        _GVAL[_g], _GKIND[_g], _GNAME[_g] = 3.0, 0, _nm
    elif _nm in AMMO_NAMES:
        _GVAL[_g], _GKIND[_g], _GNAME[_g] = 2.0, 1, _nm
    elif _nm in BODY_ARMOR:
        _GVAL[_g], _GKIND[_g], _GNAME[_g] = 1.8, 2, _nm
    elif _nm in HELMETS + SHIELDS + BOOTS_GLOVES:
        _GVAL[_g], _GKIND[_g], _GNAME[_g] = 1.2, 3, _nm


# NH-E38: floor consumable spotter. Wand/potion/scroll appearances are
# shuffled but every appearance glyph still resolves to its true CLASS via
# objclass, so we can locate "a wand/potion/scroll is on the floor here" (not
# which one — that needs the ID game). Separate from item_targets so no other
# lever's valuation changes. Kind priority: wand(3) > scroll(2) > potion(1).
WAND_CLASS = nh.WAND_CLASS
POTION_CLASS = nh.POTION_CLASS
SCROLL_CLASS = nh.SCROLL_CLASS
_CONS_KIND = np.zeros(C.MAX_GLYPH + 2, dtype=np.int8)   # 3 wand,2 scroll,1 potion
for _g, (_nm, _ocls) in _OBJ_NAME.items():
    if _ocls == WAND_CLASS:
        _CONS_KIND[_g] = 3
    elif _ocls == SCROLL_CLASS:
        _CONS_KIND[_g] = 2
    elif _ocls == POTION_CLASS:
        _CONS_KIND[_g] = 1


def consumable_targets(glyphs, agent, radius=14):
    """[(prio, (x,y), kind)] floor wands/scrolls/potions within radius, ranked
    wand>scroll>potion then nearest. kind in {'wand','scroll','potion'}."""
    ax, ay = agent
    ga = np.asarray(glyphs)
    k = _CONS_KIND[ga]
    ys, xs = np.nonzero(k)
    names = {3: "wand", 2: "scroll", 1: "potion"}
    out = []
    for y, x in zip(ys.tolist(), xs.tolist()):
        d = max(abs(x - ax), abs(y - ay))
        if d > radius:
            continue
        pr = int(k[y][x])
        out.append((pr, (x, y), names[pr]))
    out.sort(key=lambda t: (-t[0], max(abs(t[1][0] - ax), abs(t[1][1] - ay))))
    return out


def item_targets(glyphs, agent, radius=14):
    """[(value, (x,y), kind, name)] floor items worth a detour, ranked.
    value: food 3.0, ammo 2.0, body armor 1.8, other armor 1.2."""
    ax, ay = agent
    ga = np.asarray(glyphs)
    vals = _GVAL[ga]
    ys, xs = np.nonzero(vals)
    out = []
    for y, x in zip(ys.tolist(), xs.tolist()):
        d = max(abs(x - ax), abs(y - ay))
        if d > radius:
            continue
        g = int(ga[y][x])
        out.append((float(_GVAL[g]), (x, y), _KINDS[_GKIND[g]], _GNAME[g]))
    out.sort(key=lambda t: (-t[0], max(abs(t[1][0] - ax),
                                       abs(t[1][1] - ay))))
    return out

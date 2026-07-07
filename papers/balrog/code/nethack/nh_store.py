"""NH-E18 memory substrate: the unified per-episode observation store.

MODEL provenance: Fable 5 (max reasoning), Phase L session 1.
Layer: MEMORY (four-layer architecture; feeds INTUITION via ctx_package).

One queryable store per episode unifying what the agent has observed:
  - events timeline (level transitions, fights, acquisitions, near-deaths,
    prayers, casts, feature discoveries) -> the STORY SO FAR
  - item sightings WITH unidentified appearances + prices seen (price-ID
    substrate for the NH-E18 dot-connector; wiki KB price tables are the
    cross-reference)
  - monster encounter ledger (per species: seen/killed/hit-us/passive-
    adjacent) -> "didn't attack => peaceful class" inference substrate
  - per-level feature dossier (stairs, altars/fountains via cmap glyphs,
    shops via price messages, dead ends, notable cells)

Clean protocol: built EXCLUSIVELY from served observations (messages,
glyphs, blstats via the Atlas belief state). Within-episode only; nothing
persists into any scored episode from outside. Serialized into trajectories
for offline reflection passes (dev/gym only).

Write-only at runtime in Arm A (no decision code reads it in scored
configs); the intuition layer reads it at consultation/reflection points.
NH_STORE=0 disables entirely (default on: pure logger, like the subgoal
ledger).

CONTEXT_SPEC v0.1 (papers/balrog/experiments/NH-E11-strategist/
CONTEXT_SPEC.md): ctx_package() renders section 1 (world map, all visited
levels), 2 (memories), 3 (story so far), 4 (current state) as text; every
consumer must log the package verbatim.
"""

import json
import re

RE_PRICE = re.compile(r"(?:for sale|costs?)[,;]? +(\d+) +zorkmids?")
RE_SEE = re.compile(r"You see here (?:an? |the )?([^.(]*?)(?:\s*\(([^)]*)\))?\.")
RE_KILL = re.compile(r"You (?:kill|destroy) the ([a-zA-Z' -]+?)!")
RE_HIT_US = re.compile(r"The ([a-z' -]+?) (?:bites|hits|kicks|butts|stings|touches|misses)")
# our own attack effects + trap projectiles are not monsters (found by the
# first reflection pass: "spell" logged as a species with hit_us=16 — that
# was our Force Bolt)
NON_MONSTERS = {"spell", "bolt", "force bolt", "bolt of lightning",
                "bolt of fire", "bolt of cold", "death ray",
                "magic missile", "arrow", "dart", "rock", "boulder",
                "poison dart"}

# unidentified appearance adjectives (potions/scrolls/wands/rings classes);
# used to flag sightings worth remembering for price-ID. Source: object
# appearance word lists are shuffled per game; these are the APPEARANCE
# grammar markers, not identities (offline-derived, disclosed).
APPEARANCE_HINTS = ("potion", "scroll labeled", "wand", "ring", "amulet",
                    "spellbook", "gem", "stone")


class Store:
    def __init__(self):
        self.events = []            # (step, t, kind, text)
        self.items_seen = []        # {step,t,level,cell,desc,price}
        self.prices = []            # {step,t,level,desc,price}
        self.monsters = {}          # species -> counters dict
        self.features = {}          # level key -> {kind: [cells]}
        self.story = []             # compact narrative lines
        self.n_events = 0

    # ---- recording -------------------------------------------------
    def event(self, step, t, kind, text, story=False):
        self.events.append((step, t, kind, text[:160]))
        self.n_events += 1
        if story:
            self.story.append(f"T{t}: {text[:120]}")

    def mon(self, name):
        return self.monsters.setdefault(
            name, {"seen": 0, "killed": 0, "hit_us": 0, "passive_adj": 0})

    def feature(self, key, kind, cell):
        cells = self.features.setdefault(str(key), {}).setdefault(kind, [])
        if list(cell) not in cells:
            cells.append(list(cell))

    # ---- update from one step (called from agent bookkeeping) -------
    def observe(self, agent, msg):
        A = agent.atlas
        step, t = agent.steps, A.time
        if msg:
            m = RE_KILL.search(msg)
            if m:
                self.mon(m.group(1).strip())["killed"] += 1
                self.event(step, t, "kill", m.group(0), story=True)
            m = RE_HIT_US.search(msg)
            if m and "misses" not in m.group(0) and \
                    m.group(1).strip() not in NON_MONSTERS:
                self.mon(m.group(1).strip())["hit_us"] += 1
            m = RE_SEE.search(msg)
            if m:
                desc = m.group(1).strip()
                paren = m.group(2) or ""
                pm = RE_PRICE.search(paren) or RE_PRICE.search(msg)
                price = int(pm.group(1)) if pm else None
                rec = {"step": step, "t": t, "level": str(A.key),
                       "cell": list(A.agent), "desc": desc, "price": price}
                self.items_seen.append(rec)
                if price is not None:
                    self.prices.append(rec)
                    self.event(step, t, "price",
                               f"{desc} @ {price}zm", story=True)
                elif any(h in desc for h in APPEARANCE_HINTS):
                    self.event(step, t, "item", desc)
            elif RE_PRICE.search(msg):
                pm = RE_PRICE.search(msg)
                self.prices.append({"step": step, "t": t,
                                    "level": str(A.key),
                                    "cell": list(A.agent),
                                    "desc": msg[:80],
                                    "price": int(pm.group(1))})
                self.event(step, t, "price", msg[:100], story=True)
        # passive-adjacency evidence: hostile-classed monster adjacent that
        # did not attack this turn (peaceful-class inference substrate)
        ax, ay = A.agent
        for mn in A.level.monsters:
            if mn.pet:
                continue
            if max(abs(mn.x - ax), abs(mn.y - ay)) == 1 and \
                    (not msg or mn.name not in msg):
                self.mon(mn.name)["passive_adj"] += 1
        for mn in A.level.monsters:
            if not mn.pet:
                self.mon(mn.name)["seen"] += 1

    def level_event(self, agent, kind, text):
        A = agent.atlas
        self.event(agent.steps, A.time, kind, text, story=True)

    # ---- serialization ----------------------------------------------
    def to_dict(self):
        return {"events": self.events[-4000:],
                "items_seen": self.items_seen,
                "prices": self.prices,
                "monsters": self.monsters,
                "features": self.features,
                "story": self.story[-300:]}


# -------------------------------------------------- exploration metrics
# Operator directive 2026-07-07: spatial exploration as first-class
# instrumentation. Estimators (report which one each analysis uses):
#   (a) ONLINE PROXY: reachable frontier count; fully-explored == 0
#       frontiers (crisp endpoint, no total-area guess);
#   (b) RETROSPECTIVE: explored/final-explored per level (offline);
#   (c) PRIOR-BASED: explored/expected-fill for cross-level comparability.
# Dark-but-inferred (suspect walls etc.) is known-unknown, NOT explored.

def level_explore_stats(level):
    """(explored_nonwall_cells, frontier_count) for one belief level.
    Frontier = explored passable cell with >=1 unexplored neighbor."""
    import nh_common as C
    explored = 0
    frontiers = 0
    for y in range(C.ROWS):
        for x in range(C.COLS):
            if not level.explored[y][x]:
                continue
            t = int(level.terrain[y][x])
            if t == C.WALL:
                continue
            explored += 1
            if t in (C.FLOOR, C.CORRIDOR, C.DOORWAY, C.DOOR_OPEN,
                     C.STAIRS_UP, C.STAIRS_DOWN):
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < C.COLS and 0 <= ny < C.ROWS and \
                                not level.explored[ny][nx]:
                            frontiers += 1
                            break
                    else:
                        continue
                    break
    return explored, frontiers


def snapshot_exploration(store, agent):
    """Record (explored, frontiers) for every visited level — called at
    level transitions; departure-% analyses read consecutive snapshots."""
    A = agent.atlas
    snap = {}
    for key, lvl in A.levels.items():
        snap[str(key)] = list(level_explore_stats(lvl))
    store.event(agent.steps, A.time, "explore_stats", json.dumps(snap))
    return snap


# ---------------------------------------------------------------- package

# PERCEPTION: feature cells worth remembering per level (shop detection is
# message-based via prices; these are terrain-glyph-based).
FEATURE_KINDS = None  # set lazily (needs nh_common)


def scan_features(store, agent):
    """Scan the current level's belief terrain for notable feature cells
    (altar/fountain/throne/sink/grave/stairs) into the store dossier."""
    import nh_common as C
    A = agent.atlas
    L = A.level
    kinds = {C.ALTAR: "altar", C.FOUNTAIN: "fountain", C.THRONE: "throne",
             C.SINK: "sink", C.GRAVE: "grave",
             C.STAIRS_UP: "stairs_up", C.STAIRS_DOWN: "stairs_down"}
    for y in range(C.ROWS):
        for x in range(C.COLS):
            if not L.explored[y][x]:
                continue
            k = kinds.get(int(L.terrain[y][x]))
            if k:
                store.feature(A.key, k, (x, y))


def render_level_ascii(level):
    """Annotated ASCII of one level from the belief state (CONTEXT_SPEC
    section 1). ' ' = unexplored."""
    import nh_common as C
    cmap = {C.FLOOR: ".", C.WALL: "#", C.DOORWAY: "+", C.DOOR_OPEN: "+",
            C.DOOR_CLOSED: "+", C.CORRIDOR: ",", C.STAIRS_UP: "<",
            C.STAIRS_DOWN: ">", C.ALTAR: "_", C.FOUNTAIN: "{",
            C.THRONE: "\\", C.SINK: "k", C.GRAVE: "|", C.TRAP: "^",
            C.BAD_TRAP: "^", C.SLOW_TRAP: "^", C.WATER: "~", C.LAVA: "~",
            C.ICE: "~", C.HOLE_DOWN: ">", C.IRONBARS: "=", C.TREE: "T",
            C.UNKNOWN: "?"}
    rows = []
    for y in range(C.ROWS):
        chars = []
        for x in range(C.COLS):
            if not level.explored[y][x]:
                chars.append(" ")
                continue
            chars.append(cmap.get(int(level.terrain[y][x]), "?"))
        rows.append("".join(chars).rstrip())
    return "\n".join(rows)


def ctx_package(agent, store):
    """CONTEXT_SPEC/v0.1 package (text). Log verbatim wherever consumed."""
    A = agent.atlas
    out = ["CONTEXT_SPEC/v0.1"]
    out.append("== 1. WORLD MAP (visited levels, belief-derived) ==")
    for key, lvl in sorted(A.levels.items(), key=lambda kv: str(kv[0])):
        out.append(f"-- level {key}"
                   f"{'  <== CURRENT' if key == A.key else ''}")
        out.append(render_level_ascii(lvl))
        feats = store.features.get(str(key), {})
        if feats:
            out.append(f"   features: {json.dumps(feats)}")
    out.append("== 2. MEMORIES ==")
    out.append(f"prices seen: {json.dumps(store.prices)}")
    out.append(f"item sightings: {json.dumps(store.items_seen[-40:])}")
    out.append(f"monster ledger: {json.dumps(store.monsters)}")
    out.append("== 3. STORY SO FAR ==")
    out.extend(store.story[-60:])
    out.append("== 4. CURRENT STATE ==")
    out.append(f"role={agent.role} depth={A.depth} hp={A.hp}/{A.hpmax} "
               f"pw={A.pw}/{A.pwmax} ac={A.ac} hunger={A.hunger} "
               f"xp={A.xplvl} t={A.time} pos={A.agent} "
               f"subgoal={agent.subgoal}")
    return "\n".join(out)

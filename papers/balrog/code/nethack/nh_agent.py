"""DiveAgent: layered belief-state policy for BALROG NetHackChallenge.

Objective model (from balrog/environments/nle/progress.py, offline read):
progression = max over achieved milestones Dlvl:n / Xp:n; depth dominates
(Dlvl:10 = 0.126, Dlvl:13 = 0.257). Survival per se scores nothing — the
optimal policy is depth-before-death maximization with cheap survival
maintenance (rest, pray, food) that buys more descent.

Layers (checked in order every step):
  P0 prompt/menu state machine (misc flags + message grammar)
  P1 scripted-sequence queue (dig / engrave / eat / pray / kick / pickup)
  P2 swallowed -> attack engulfer
  P3 emergency survival (pray, Elbereth, retreat)
  P4 food clock (eat inventory food / fresh safe corpse)
  P5 combat tactician (threat-budgeted melee, never-melee species)
  P6 rest-to-heal gate before descending
  P7 descent: dig down if digger held; else stairs/holes
  P8 pick-axe acquisition detour (object-glyph spotting)
  P9 frontier exploration (mass-biased, target persistence)
  P10 closed/locked doors (open, kick)
  P11 hidden-passage search rotation
  P12 anti-no-progress fallback (search/wait)

All decisions replan per step from the Atlas belief state.
"""

import re

import nh_common as C
from nh_common import DIRS, DIR_OF, CARDINALS

from nle import nethack as nh

# object glyphs for diggers (tool appearances are not shuffled)
DIGGER_GLYPHS = set()
for _g in range(C.GLYPH_OBJ_OFF, C.GLYPH_CMAP_OFF):
    try:
        _name = nh.OBJ_NAME(nh.objclass(_g - C.GLYPH_OBJ_OFF))
    except Exception:
        continue
    if _name in ("pick-axe", "dwarvish mattock"):
        DIGGER_GLYPHS.add(_g)

# NOTE: fingertip-Elbereth is UNREACHABLE in BALROG's NLE action space:
# the "What do you want to write with?" getobj prompt needs the '-' key
# (fingers), but BALROG's NLE action list has no "minus"/'-' action
# (TextCharacters are stripped from USEFUL_ACTIONS; only letters/digits/
# space are added back). Engraving is therefore disabled.
OUR_SPEED = 12          # all starting roles move at speed 12

# V1.1 L2 — shallow opportunistic hunting. DROPPED from v1.1 after dev
# validation (coordinator rule: drop levers that don't clearly pay):
# isolated effect +0.63 [-0.42,+1.82] on 24 paired dev seeds, and the
# 12-seed extension block regressed to -0.34 — the initial gains were
# dev-noise seed luck (the Crafter v2 lesson). Kept as an off-by-default
# toggle for future work.
import os as _os
HUNT_SHALLOW = _os.environ.get("NH_HUNT", "0") == "1"

# ---------------------------------------------------------------- Campaign 2
# Feature flags (all default OFF -> byte-identical v1.1 behavior). Each
# lever is dev-validated on >=20 paired seeds and dropped if it doesn't
# clearly pay (program rule).
def _flag(name):
    return _os.environ.get(name, "0") == "1"

C2_EXPMAX = _flag("NH_EXPMAX")    # expectimax combat + death-veto
C2_RANGED = _flag("NH_RANGED")    # ranged-first vs fast/pack threats
C2_ARMOR = _flag("NH_ARMOR")      # armor pickup + wear economy
C2_FOOD2 = _flag("NH_FOOD2")      # food economy v2 (floor detours, corpse@hungry)
C2_PRAYFIX = _flag("NH_PRAYFIX")  # no hunger-prayer with hostile adjacent
C2_LOS = _flag("NH_LOS")          # line-of-fire avoidance in travel
C2_THREAT = _flag("NH_THREAT")    # threat-halo avoidance in travel
C2_TOPO = _flag("NH_TOPO")        # topology-driven hidden-passage search
C2_PACE = _flag("NH_PACE")        # role-conditional descent pacing
C2_ELBERETH = _flag("NH_ELBERETH")  # E-NH5: weapon-engraved Elbereth panic
C2_GUARD = _flag("NH_GUARD")      # touch-kill weapon-melee + novelty ledger
C2_CAST = _flag("NH_CAST")        # Phase L: attack-spell combat casting
C2_E15 = _flag("NH_E15")          # Phase L: stall watchdog (NH-E15)
C2_REPEAT = _flag("NH_REPEAT")    # Phase L: repeated-layout stair predictor
C2_CASTHUNGER = _flag("NH_CASTHUNGER")  # Phase L: cast-nutrition doctrine
#   (guard-class only; lets the guards ride even on an otherwise-v1.1
#    configuration)
PACE_DEPTH = int(_os.environ.get("NH_PACE_DEPTH", "3"))
PACE_XP_STEP = float(_os.environ.get("NH_PACE_XPSTEP", "2"))
PACE_BUDGET = int(_os.environ.get("NH_PACE_BUDGET", "900"))
C2_ANY = any((C2_EXPMAX, C2_RANGED, C2_ARMOR, C2_FOOD2, C2_PRAYFIX, C2_LOS,
              C2_THREAT, C2_TOPO, C2_PACE, C2_ELBERETH, C2_GUARD, C2_CAST,
              C2_E15, C2_REPEAT, C2_CASTHUNGER))
WD_WINDOW = int(_os.environ.get("NH_WD_WINDOW", "150"))   # game turns
WD_DISENGAGE = int(_os.environ.get("NH_WD_DISENGAGE", "80"))  # env steps
CAST_FAIL_MAX = int(_os.environ.get("NH_CAST_FAILMAX", "20"))  # % gate
CAST_LINE_RANGE = int(_os.environ.get("NH_CAST_RANGE", "6"))
REPEAT_BUDGET = int(_os.environ.get("NH_REPEAT_BUDGET", "150"))  # env steps/level

# Elbereth is ignored by these (offline source facts, disclosed):
ELBERETH_IGNORES = {"minotaur", "shopkeeper", "watchman", "watch captain",
                    "guard", "vault guard"}

# RULE CARD [CAST_NEVER_PEACEFUL_CLASS] (layer: PROCEDURE; model: Fable 5
# max): statement: never cast attack spells at civil @-classes that
# generate peaceful (shopkeeper/watch/guards/temple priests/Oracle).
# mechanism: a directional cast SKIPS the "Really attack?" confirm that
# protects melee — CAST-1 dev block angered 3 shopkeepers (0 shop deaths
# in ref -> 3 in test: seeds 940/957/990), each fatal. The peaceful-decline
# machinery (no_attack cells) only learns from melee prompts, so spells
# need a static class guard. evidence: CAST-1 paired block ledger.
# status: verified-by-death, shipped with CAST_ATTACK_V1.1.
CAST_NEVER = {"shopkeeper", "watchman", "watch captain", "guard",
              "vault guard", "aligned priest", "high priest", "Oracle"}

# RULE CARD [TOUCH_KILL_WEAPON_MELEE]: petrification is a FLESH-touch
# effect — attacking cockatrice-class species with a WIELDED WEAPON is
# safe in the source (uhitm.c: touch checks apply to unarmed/martial
# hits and grabs). v1's blanket never-melee is right for bare hands but
# left a cornered Barbarian standing still while a chickatrice touched
# it to death (settled dev seed 705, 100+ step-away attempts while boxed
# in by a peaceful). Scope: fires only when (a) a C2 flag is on, (b) a
# weapon is wielded, (c) role is not Monk (martial arts = flesh), and
# (d) step-away has already failed (cornered). Status: source-derived
# prior, guard-class; evidence: 1 observed death + source read.
TOUCH_KILL = {"cockatrice", "chickatrice", "Medusa"}

# RULE CARD [NOVELTY_DETECTOR]: species adjacent to us with < 12
# exchange-model rows are flagged to the ledger (logging only in this
# campaign; caution-default behavior is the queued E-NH4b/novelty
# protocol work). Unexplained-novelty count is a report metric.
NOVELTY_MIN_ROWS = 12

if C2_ANY:
    import nh_percept as P
else:
    P = None

FRAGILE_ROLES = {"Tourist", "Healer", "Wizard", "Priest", "Priestess",
                 "Rogue", "Archeologist"}
# (Archeologist only counts as fragile when it has no digger; dig-dive
# behavior is never pace-gated.)

FAST_THREATS = {"giant spider", "soldier ant", "giant ant", "fire ant",
                "killer bee", "pony", "horse", "little dog", "dog",
                "large dog", "kitten", "housecat", "large cat", "jaguar",
                "panther", "tiger", "wolf", "warg", "dingo", "coyote",
                "jackal", "fox", "giant bat", "bat", "raven"}

RE_KILLED = re.compile(r"You (?:kill|destroy) the ([a-zA-Z' -]+?)!")
RE_SEE_HERE = re.compile(r"You see here (?:an? |the )?([^.]*)\.")

TRAP_HOLD_MSGS = ("pit", "bear trap", "web", "You are stuck")


class DiveAgent:
    def __init__(self, log=print, memory=None):
        self.atlas = C.Atlas()
        self.log = log
        self.memory = memory                    # NetHackMemory or None
        self.queue = []                         # scripted action sequence
        self.queue_tag = None
        self.last_action = None
        self.last_pos = None
        self.last_time = -1
        self.last_hp = None
        self.suspect_walls = {}                 # key -> set of cells
        self.explore_target = None
        self.no_time_steps = 0                  # env steps w/o game time
        self.last_prompt_sig = None
        self.prompt_repeats = 0
        self.prayed_at = None
        self.pray_count = 0
        self.engraved_at = {}                   # cell -> time
        self.kick_dir = None
        self.kick_count = 0
        self.door_giveup = set()
        self.door_target = None                 # cell of last open/kick attempt
        self.hunt_turns = {}                    # level key -> game turns spent hunting
        self.fresh_kills = []                   # (cell, species, time)
        self.role = None
        self.race = None
        self.role_source = None                 # "welcome" | "ttyrank"
        # ---- Phase L NH-E18 memory substrate (pure logger, like the
        # subgoal ledger: no decision code reads it in Arm A; the intuition
        # layer reads it at consultation/reflection points). NH_STORE=0
        # disables.
        self.store = None
        if _os.environ.get("NH_STORE", "1") == "1":
            import nh_store
            self.store = nh_store.Store()
        self.repeat_budget = {}     # level key -> REPEAT2 routing steps used
        # ---- Phase L NH_REPEAT state (inert unless C2_REPEAT) ----
        self.prev_level_key = None
        self._cur_level_key = None
        self.repeat_pred = None       # predicted stairs cell or False
        self.repeat_checked_exp = 0   # explored count at last check
        self.repeat_fires = 0
        # ---- Phase L NH-E15 stall watchdog (inert unless C2_E15) ----
        self.wd_hist = []           # (game_time, explored, depth, xp)
        self.wd_level = 0           # escalation level
        self.wd_last_fire_t = -999
        self.wd_disengage_until = -1   # env-step deadline for disengage
        self.wd_fires = []          # (step, t, level, action_taken)
        # ---- Phase L NH_CAST state (all inert unless C2_CAST) ----
        self.cast_spells = None     # letter -> (name, lvl, cat, fail%) per ep
        self.cast_choice = None     # (letter, name, pw_cost) selected spell
        self.cast_dir = None        # pending direction for in-flight cast
        self.cast_step = -99        # step the cast was issued (staleness)
        self.cast_unavailable = False
        self.cast_fires = 0
        # Phase L NH_CASTHUNGER state (tracking always on; behavior gated)
        self.cast_hunger_blocked = False
        self.cast_hunger_events = 0
        self.rest_budget = {}                   # level key -> turns rested
        self.dig_attempts = {}                  # level key -> attempts
        self.no_dig_cells = set()               # (key, cell)
        self.pickup_wanted = None               # letter to verify after pickup
        self.digger_letter = None
        self.digging = False
        self.need_look = True
        self.retreat_ups = 0
        self.grind_start = {}                   # level key -> game time
        self.grind_note = set()
        self.descended_from = None              # (key, cell) of last '>' taken
        self.mines_entrances = {}               # level key -> {cells}
        self.mines_avoid_since = {}             # level key -> game time
        self.commit_mines = False               # ban expired: stop retreating
        self.throws_at = {}                     # (key, cell) -> throw count
        self.steps = 0
        self.recent_max_hit = 0                 # worst single-step hp loss, decayed
        self.notes = []                         # sparse decision log
        self.mem_fired = []                     # memory-driven decisions
        # ---- Campaign 2: subgoal ledger + planner visibility (log-only)
        self.subgoal = None                     # (label, reason)
        self.subgoal_log = []                   # (step, label, reason) on change
        self.plan_cells = []                    # current planned path cells
        self.plan_log = []                      # (step, [[x,y],...]) on change
        self.ev_log = []                        # (step, text) expectimax fires
        self.pred_log = []                      # (step, predicted dmg/turn)
        self._novelty_seen = set()
        self._wields_weapon = False
        # ---- Campaign 2: lever state
        self.topos = {}                         # level key -> P.Topology
        self.ammo_letters = []
        self.wear_pending = None                # letter being worn
        self.worn_slots = set()                 # 'body','helmet','shield','boots','gloves'
        self.burdened = False
        self.item_target = None                 # (cell, kind, name)
        self.pickup_kind = None                 # what P0 menu should select
        self.wearable = []
        self.wear_tried = {}                    # letter -> attempts
        self.loot_tries = {}                    # (key, cell) -> attempts
        self.grind_kills = 0
        self.pace_grind_until = {}              # level key -> game time budget end
        self.emergency_fired = 0
        self.elbereth_cell = None               # (key, cell) of live engraving
        self.elbereth_time = 0
        self.elbereth_uses = 0
        self.elbereth_hits = 0                  # dmg taken while standing on it
        self._mem_avoid = set()
        self._mem_danger_depth = None
        if memory is not None:
            self._mem_avoid = set(memory.avoid_species())
            self._mem_danger_depth = memory.danger_depth()
            if self._mem_avoid:
                self._fire(f"M1 loaded avoid-species {sorted(self._mem_avoid)}")
            if self._mem_danger_depth is not None:
                self._fire(f"M2 loaded danger depth {self._mem_danger_depth}")

    # ------------------------------------------------------------------ api
    def set_actions(self, names):
        self.actions = set(names)

    def note(self, s):
        self.notes.append((self.steps, s))

    def _goal(self, label, reason=""):
        """Subgoal ledger: record the active subgoal (logged on change)."""
        if self.subgoal is None or self.subgoal[0] != label or \
                self.subgoal[1] != reason:
            self.subgoal = (label, reason)
            self.subgoal_log.append((self.steps, label, reason))

    def _ev(self, text):
        self.ev_log.append((self.steps, text))

    def _log_pred(self):
        """Online twin (E-NH1b.4): the model's expected damage THIS turn
        from currently-adjacent hostiles. Logged sparsely (adjacency
        only); post-hoc calibration = predicted vs realized hp drop."""
        if P is None:
            return
        adj = self._adjacent_hostiles()
        if not adj:
            return
        pred = sum(P.species_dpt(m.name, m.difficulty) for m in adj
                   if m.name not in C.IMMOBILE)
        if pred > 0:
            self.pred_log.append((self.steps, round(pred, 2)))
        # novelty detector (RULE CARD [NOVELTY_DETECTOR]): logging only
        for m in adj:
            if m.name in self._novelty_seen:
                continue
            v = P.exchange()["species"].get(m.name)
            if v is None or v.get("n_rows", 0) < NOVELTY_MIN_ROWS:
                self._novelty_seen.add(m.name)
                self._ev(f"NOVEL species adjacent: {m.name} "
                         f"(rows {0 if v is None else v.get('n_rows', 0)}, "
                         f"diff {m.difficulty})")

    def _fire(self, s):
        self.mem_fired.append((self.steps, s))
        if self.memory is not None:
            self.memory.record_fired(s)

    def act(self, obs):
        A = self.atlas
        A.update(obs)
        msg = A.message
        self._bookkeeping(obs, msg)
        if C2_ANY:
            self._log_pred()
        a = self._decide(obs, msg)
        self.last_action = a
        self.last_pos = A.agent
        self.last_time = A.time
        self.last_hp = A.hp
        self.steps += 1
        return a

    # --------------------------------------------------- planner visibility
    def _log_plan(self, path):
        """Record the currently-planned route (cells) when it changes."""
        cells = []
        x, y = self.atlas.agent
        for stp in path:
            dx, dy = DIRS[stp]
            x, y = x + dx, y + dy
            cells.append([x, y])
        if cells != self.plan_cells:
            self.plan_cells = cells
            self.plan_log.append((self.steps, cells))

    # ---------------------------------------------------------- bookkeeping
    def _bookkeeping(self, obs, msg):
        A = self.atlas
        if self.role is None and "welcome to NetHack" in msg:
            m = re.search(r"You are an? ([a-z ]+) (\w+) (\w+)\.", msg)
            if m:
                self.role = m.group(3)
                self.race = m.group(2)
                self.role_source = "welcome"
                self.note(f"role={self.role} race={self.race}")
        # Phase L NH_REPEAT: previous-level tracking + per-level reset
        if A.level_changed or self._cur_level_key is None:
            if self._cur_level_key is not None and \
                    self._cur_level_key != A.key:
                self.prev_level_key = self._cur_level_key
            self._cur_level_key = A.key
            self.repeat_pred = None
            self.repeat_checked_exp = 0
        # Phase L NH-E18: feed the observation store (MEMORY layer)
        if self.store is not None:
            import nh_store
            self.store.observe(self, msg)
            if A.level_changed:
                self.store.level_event(
                    self, "level",
                    f"entered {A.key} depth {A.depth} "
                    f"(hp {A.hp}/{A.hpmax} xp {A.xplvl})")
                # exploration snapshot at every transition: consecutive
                # snapshots give departure explored/frontier per level
                nh_store.snapshot_exploration(self.store, self)
                self.store.first(self.steps, A.time, "depth", str(A.depth))
            if self.steps % 200 == 0 or A.level_changed:
                nh_store.scan_features(self.store, self)
        # Phase L NH_CAST: roles with no spells say so once; remember it
        if C2_CAST and "You don't know any spells" in msg:
            self.cast_unavailable = True
            self.cast_dir = None
        # RULE CARD [CAST_HUNGER_V1] (layer: PROCEDURE; model: Fable 5 max;
        # provenance: OPERATOR-OBSERVED — spotted "too hungry to cast" live
        # in the c22 GIF reel, 2026-07-07; the human-observer→hypothesis
        # loop the reel exists for): casting debits NUTRITION as well as Pw,
        # and the env refuses casts when too hungry. Ungated, the cast layer
        # retried the refused cast EVERY step: seed 839 logged 2759 refusals
        # (24% of the episode) and starved; 2 of 4 affected CAST-block
        # Wizards died of hunger. Doctrine: (a) the refusal message is a
        # PRE-FAIL signal — latch cast_hunger_blocked until fed back to
        # NotHungry, letting melee/throw doctrine take over mid-fight;
        # (b) casters eat at HUNGRY tier, not Weak (see _decide eat-early
        # branch). Status: provisional pending paired dev (ref=cast2).
        # Evidence: 4/12 CAST-block Wizard seeds affected (839/912/940/980).
        if C2_CAST and "too hungry to cast" in msg:
            if not self.cast_hunger_blocked:
                self.cast_hunger_blocked = True
                self.cast_hunger_events += 1
                self.cast_dir = None
                self._ev(f"CAST_HUNGER: refusal at hunger {A.hunger} "
                         f"(event {self.cast_hunger_events})")
        elif self.cast_hunger_blocked and A.hunger <= 1:
            self.cast_hunger_blocked = False
            self._ev("CAST_HUNGER: unblocked (fed to NotHungry)")
        # harness-audit item 4: welcome-message parse can miss (message
        # scrolled past under skip_more). Fallback: the status line always
        # carries "<Name> the <RankTitle>" — map via C.RANK_TO_ROLE
        # (source role.c table, offline+disclosed). Two v1 "(unparsed)"
        # episodes (seeds 2015/2016) were recovered exactly this way.
        if self.role is None and self.steps > 10 and self.steps % 25 == 0:
            try:
                tty = obs["obs"]["tty_chars"]
                for row in (tty[22], tty[23], tty[21]):
                    line = "".join(chr(c) for c in row)
                    m = re.search(r"the ([A-Z][a-zA-Z -]+?)(?:  |\s*$)", line)
                    if m and m.group(1).strip() in C.RANK_TO_ROLE:
                        self.role = C.RANK_TO_ROLE[m.group(1).strip()]
                        self.role_source = "ttyrank"
                        self.note(f"role={self.role} (ttyrank fallback: "
                                  f"'{m.group(1).strip()}')")
                        break
            except Exception:
                pass

        if A.level_changed:
            # mines-entrance learning: if taking that '>' put us in the
            # Gnomish Mines (dnum 2), remember the fork-level cell
            if self.descended_from and A.dnum == 2 and \
                    self.descended_from[0][0] == 0:
                fkey, fcell = self.descended_from
                self.mines_entrances.setdefault(fkey, set()).add(fcell)
                self.note(f"learned Mines entrance at {fkey}:{fcell}")
            self.descended_from = None
            self.explore_target = None
            self.queue = []
            self.queue_tag = None
            self.kick_dir = None
            self.digging = False
            self.need_look = True      # terrain under agent is invisible
            self.retreat_ups = 0
            self.note(f"level -> {A.key} depth={A.depth}")

        # message-driven terrain-under-agent knowledge (from 'look')
        low = msg.lower()
        if "staircase down here" in low or "ladder down here" in low:
            A.level.stairs_down.add(A.agent)
            A.level.terrain[A.agent[1]][A.agent[0]] = C.STAIRS_DOWN
        elif "staircase up here" in low or "ladder up here" in low:
            A.level.stairs_up.add(A.agent)
            A.level.terrain[A.agent[1]][A.agent[0]] = C.STAIRS_UP

        # no-game-time counter (env aborts at 150)
        if A.time == self.last_time:
            self.no_time_steps += 1
        else:
            self.no_time_steps = 0

        # suspect-wall aging: stale entries (monster-blocked cells, opened
        # doors) otherwise wall off corridors forever; re-verifying costs
        # one bump each
        if self.steps % 250 == 249:
            self.suspect_walls.pop(A.key, None)

        # damage tracking (crisis detection + memory ledger)
        if self.last_hp is not None:
            dmg = self.last_hp - A.hp
            if dmg > 0 and self.elbereth_cell == (A.key, A.agent):
                self.elbereth_hits += 1     # engraving smudged/ignored
            if dmg > 0:
                self.recent_max_hit = max(self.recent_max_hit, dmg)
                if self.memory is not None:
                    adj = [m for m in A.level.monsters
                           if not m.pet and max(abs(m.x - A.agent[0]),
                                                abs(m.y - A.agent[1])) <= 1]
                    for m in adj:
                        self.memory.record_exchange(m.name, dmg / len(adj))
            elif self.steps % 12 == 0 and self.recent_max_hit > 0:
                self.recent_max_hit -= 1        # decay when not being hit

        # kill log (fresh corpses for the food layer); the corpse drops on
        # the victim's cell = the cell we attacked into, not our own
        for mname in RE_KILLED.findall(msg):
            cell = A.agent
            if self.last_action in DIRS:
                dx, dy = DIRS[self.last_action]
                cell = (A.agent[0] + dx, A.agent[1] + dy)
            self.fresh_kills.append((cell, mname.strip(), A.time))
            if self.memory is not None:
                self.memory.record_kill(mname.strip())
        self.fresh_kills = [k for k in self.fresh_kills
                            if A.time - k[2] < 40][-20:]

        # stuck detection -> suspect walls (not while held by a trap)
        if self.last_action in DIRS and self.last_pos == A.agent and \
                A.time == self.last_time and \
                not any(t in msg for t in TRAP_HOLD_MSGS):
            dx, dy = DIRS[self.last_action]
            tgt = (A.agent[0] + dx, A.agent[1] + dy)
            if not any(m.pos == tgt for m in A.level.monsters):
                self.suspect_walls.setdefault(A.key, set()).add(tgt)

        # boulder push failure
        if "but in vain" in msg and self.last_action in DIRS:
            dx, dy = DIRS[self.last_action]
            tgt = (A.agent[0] + dx, A.agent[1] + dy)
            A.level.boulder_blocked.add((A.agent, self.last_action))
            self.suspect_walls.setdefault(A.key, set()).add(tgt)

        # dig outcome tracking (self.digging set when a dig queue is issued)
        if getattr(self, "digging", False):
            low2 = msg.lower()
            if "stairs are too hard to dig" in low2:
                # we are standing on invisible stairs: identify them
                self.digging = False
                self.queue = []
                self.queue_tag = None
                self.need_look = True
                self.no_dig_cells.add((A.key, A.agent))
            elif "too hard to dig" in low2 or "can't dig" in low2 or \
                    "cannot dig" in low2 or "you don't have anything" in low2:
                self.no_dig_cells.add((A.key, A.agent))
                self.digging = False
                self.queue = []
                self.queue_tag = None

        # a queue answer that missed its prompt: abort the script
        if self.queue and ("You don't have that object" in msg or
                           "Never mind" in msg or "never mind" in msg):
            self.queue = []
            self.queue_tag = None
            self.digging = False

        # phantom corpse: kill was logged but no corpse dropped (drop is
        # probabilistic) -> "eat" refuses in zero time, which would freeze
        # the fresh-kill clock forever (dev seed 103 abort)
        if "don't have anything to eat" in msg:
            self.fresh_kills = [k for k in self.fresh_kills
                                if k[0] != A.agent]

        # locked door outcomes
        if "This door is locked" in msg and self.kick_dir:
            pass  # kick sequence continues in _decide
        if "crashes open" in msg or "The door opens" in msg or \
                "You succeed" in msg:
            self.kick_dir = None
            self.kick_count = 0

        # V1.1 L1 — stale-door terrain correction (v1 failure catalog #8:
        # an item glyph covering an opened door left remembered terrain
        # "closed"; the open/direction loop then churned 100k-step episodes
        # at ~zero game time). The message channel is authoritative:
        if self.door_target is not None:
            tx, ty = self.door_target
            if "This door is already open" in msg or "The door opens" in msg:
                A.level.terrain[ty][tx] = C.DOOR_OPEN
                self.door_target = None
            elif "You see no door there" in msg or "no door" in msg.lower():
                A.level.terrain[ty][tx] = C.DOORWAY
                self.door_target = None
            elif "This door is broken" in msg:
                A.level.terrain[ty][tx] = C.DOORWAY
                self.door_target = None

    # -------------------------------------------------------------- helpers
    def _suspects(self):
        return self.suspect_walls.get(self.atlas.key, set())

    def _mcells(self, hostile_only=True):
        """Monster cells to treat as path obstacles. Pets are NOT obstacles
        (moving into a pet swaps places) — treating them as walls let a
        following kitten box the agent into corridor dead-ends forever
        (dev seeds 106/103: thousands of stationary searches)."""
        L = self.atlas.level
        return {m.pos for m in L.monsters if not (hostile_only and m.pet)}

    def _inv(self, obs):
        return C.inventory(obs)

    def _find_digger(self, obs):
        for letter, desc, oc in self._inv(obs):
            d = desc.lower()
            if "pick-axe" in d or "mattock" in d:
                return letter
        return None

    def _food_letter(self, obs):
        best = None
        for letter, desc, oc in self._inv(obs):
            if oc != C.FOOD_CLASS:
                continue
            d = desc.lower()
            if "corpse" in d:
                # exact species match: substring matching accepted
                # "dwarf zombie corpse" via "dwarf" (wrath epidemic root #2)
                m = re.search(r"([a-z' -]+?) corpses?", d)
                species = m.group(1).strip() if m else ""
                if species in C.SAFE_CORPSES and not self._cannibal(species):
                    best = best or letter
                continue
            if "tin " in d or d.endswith("tin") or "tins" in d:
                continue
            return letter                       # prepared food: take first
        return best

    _RACE_ROOT = {"dwarven": "dwarf", "gnomish": "gnome", "elven": "elf",
                  "orcish": None,  # orcs may eat orcs
                  "human": "human"}

    def _cannibal(self, desc):
        d = desc.lower()
        if not self.race:
            # race unknown (welcome message missed): refuse any corpse that
            # could be own-race — cannibalism angers the god (wrath deaths)
            return any(r in d for r in ("dwarf", "gnome", "elf"))
        root = self._RACE_ROOT.get(self.race.lower(), self.race.lower())
        return bool(root) and root in d

    def _pray_ok(self, last_resort=False):
        # prayer discipline (dev seed 104: Healer smote by Hermes for
        # praying early+often): first prayer after turn 300, >=1500-turn
        # gaps, at most 3 per game. last_resort (imminent death) waives the
        # turn gates: an angry god is no worse than the ant eating you.
        A = self.atlas
        if self.pray_count >= 3:
            return False
        if last_resort:
            # one gamble per crisis, not a wrath-farming loop (dev seed 105)
            return self.prayed_at is None or A.time - self.prayed_at > 500
        if self.prayed_at is None:
            # NetHack's initial prayer timeout is rnz(350) (long-tailed):
            # T>700 clears most of the distribution
            return A.time > 700
        return A.time - self.prayed_at > 1500

    def _adjacent_hostiles(self):
        A = self.atlas
        ax, ay = A.agent
        out = []
        for m in A.level.monsters:
            if m.pet or m.pos in A.level.no_attack:
                continue
            if max(abs(m.x - ax), abs(m.y - ay)) == 1:
                out.append(m)
        return out

    def _mobile_hostiles(self):
        return [m for m in self.atlas.level.monsters
                if not m.pet and m.name not in C.IMMOBILE and
                m.pos not in self.atlas.level.no_attack]

    def _never_melee(self, m):
        if m.name in C.NEVER_MELEE:
            return True
        if m.name in self._mem_avoid and self.atlas.xplvl <= 6:
            return True
        return False

    def _dir_to(self, tgt):
        ax, ay = self.atlas.agent
        d = (tgt[0] - ax, tgt[1] - ay)
        return DIR_OF.get(d)

    # ------------------------------------------------- Campaign 2 helpers
    def _topo(self):
        t = self.topos.get(self.atlas.key)
        if t is None:
            t = self.topos[self.atlas.key] = P.Topology()
        return t.refresh(self.atlas.level)

    def _travel_avoid(self, goals=frozenset()):
        """First-pass travel avoid set: suspects + hostiles + (flagged)
        threat halos and line-of-fire cells. Callers keep their existing
        relaxed fallbacks, so this only re-routes when a route exists.
        Perceptor fields are cached per env step (pure wall-clock)."""
        avoid = set(self._suspects()) | (self._mcells() - set(goals))
        A = self.atlas
        if C2_THREAT:
            if getattr(self, "_tf_step", -1) != self.steps:
                self._tf_step = self.steps
                _, self._tf_halo = P.threat_field(A.level)
            avoid |= (self._tf_halo - set(goals)) - {A.agent}
        if C2_LOS:
            if getattr(self, "_los_step", -1) != self.steps:
                self._los_step = self.steps
                if any((not m.pet) and m.cls in P.RANGED_CLASSES and
                       max(abs(m.x - A.agent[0]),
                           abs(m.y - A.agent[1])) > 1
                       for m in A.level.monsters):
                    self._los_cells = P.los_cells(A.level, A.agent)
                else:
                    self._los_cells = set()
            if self._los_cells:
                avoid |= (self._los_cells - set(goals)) - {A.agent}
        return avoid

    def _c2_scan_inv(self, obs):
        """Track ammo letters and worn armor slots from inventory."""
        ammo, worn = [], set()
        self.wearable = []           # (letter, slot, name)
        for letter, desc, oc in self._inv(obs):
            d = desc.lower()
            being_worn = "(being worn)" in d
            slot = None
            if any(n in d for n in P.BODY_ARMOR):
                slot = "body"
            elif any(n in d for n in P.HELMETS):
                slot = "helmet"
            elif any(n in d for n in P.SHIELDS):
                slot = "shield"
            elif "boots" in d or "iron shoes" in d:
                slot = "boots"
            elif "gloves" in d or "gauntlets" in d:
                slot = "gloves"
            if slot:
                if being_worn:
                    worn.add(slot)
                else:
                    self.wearable.append((letter, slot, d))
                continue
            if "weapon in hand" in d or "weapons in hands" in d:
                continue
            if any(k in d for k in P.AMMO_NAMES) and oc == 2:  # WEAPON_CLASS
                ammo.append(letter)
        self.ammo_letters = ammo
        self.worn_slots = worn

    def _melee_step(self, m):
        """Legal melee move into m's cell, or None (door-diagonal rule)."""
        A = self.atlas
        L = A.level
        ax, ay = A.agent
        d = (m.x - ax, m.y - ay)
        if d not in DIR_OF:
            return None
        t_here = L.terrain[ay][ax]
        t_there = L.terrain[m.y][m.x]
        if d[0] and d[1] and (
                t_here in (C.DOORWAY, C.DOOR_OPEN, C.DOOR_CLOSED) or
                t_there in (C.DOORWAY, C.DOOR_OPEN, C.DOOR_CLOSED)):
            return None
        return DIR_OF[d]

    def _c2_engrave_tool(self, obs):
        """Letter of a weapon to engrave with (prefer non-wielded)."""
        wielded = None
        for letter, desc, oc in self._inv(obs):
            if oc != 2:
                continue
            if "weapon in hand" in desc.lower() or \
                    "weapons in hands" in desc.lower():
                wielded = letter
                continue
            return letter
        return wielded

    _ELBERETH_OK_TERRAIN = None   # set lazily from C

    def _c2_elbereth(self, obs, adj, reason):
        """E-NH5: engrave Elbereth with a weapon (fingers are unreachable
        in BALROG's action space, but getobj accepts a weapon letter and
        'more' (= CR) submits the getlin). One game turn; typing is
        zero-time. Scares most melee attackers off the square."""
        if not C2_ELBERETH or self.elbereth_uses >= 5:
            return None
        A = self.atlas
        t = A.level.terrain[A.agent[1]][A.agent[0]]
        if t not in (C.FLOOR, C.CORRIDOR, C.DOORWAY):
            return None
        # someone must actually be scareable
        scareable = [m for m in adj
                     if m.cls != "@" and m.name not in ELBERETH_IGNORES]
        if not scareable:
            return None
        tool = self._c2_engrave_tool(obs)
        if tool is None:
            return None
        self.elbereth_uses += 1
        self.elbereth_cell = (A.key, A.agent)
        self.elbereth_time = A.time
        self.elbereth_hits = 0
        self._goal("survive", f"Elbereth ({reason})")
        self._ev(f"ELBERETH: {reason} (hp {A.hp}/{A.hpmax}, "
                 f"{[m.name for m in adj]})")
        self.note(f"engraving Elbereth: {reason}")
        self.queue = [tool] + list("Elbereth") + ["more"]
        self.queue_tag = "engrave"
        return "engrave"

    def _on_elbereth(self):
        A = self.atlas
        return (self.elbereth_cell == (A.key, A.agent) and
                A.time - self.elbereth_time < 200 and
                self.elbereth_hits < 3)

    def _c2_emergency(self):
        """Death-recognizer veto action: escape upstairs or gamble a
        last-resort prayer. None if no emergency line exists."""
        A = self.atlas
        if A.agent in A.level.stairs_up and self.retreat_ups < 3:
            self.retreat_ups += 1
            self.emergency_fired += 1
            self._ev(f"VETO: upstairs escape (hp {A.hp}/{A.hpmax})")
            return "up"
        if A.hp <= 6 and self._pray_ok(last_resort=True):
            self.prayed_at = A.time
            self.pray_count += 1
            self.emergency_fired += 1
            self._ev(f"VETO: last-resort prayer (hp {A.hp}/{A.hpmax})")
            self.queue = ["y"]
            self.queue_tag = "pray"
            return "pray"
        return None

    def _c2_combat(self, obs, adj):
        """E-NH4 expectimax fight/flee/hold/throw over exchange EVs.
        Returns an action or None (nothing attackable adjacent)."""
        A = self.atlas
        L = A.level
        mobile = [m for m in adj if m.name not in C.IMMOBILE and
                  not self._never_melee(m) and m.pos not in L.no_attack]
        if not mobile:
            return None
        stats = sorted(((m, P.species_dpt(m.name, m.difficulty),
                         P.species_ttk(m.name, m.difficulty,
                                       role=self.role, xplvl=A.xplvl))
                        for m in mobile), key=lambda t: t[2])
        total_dpt = sum(d for _, d, _ in stats)
        # expected HP cost of fighting the pack out, weakest-ttk first
        loss, alive = 0.0, total_dpt
        for m, d, ttk in stats:
            loss += alive * ttk
            alive -= d
        loss *= 1.35
        floor = max(4.0, 0.12 * A.hpmax)
        target = stats[0][0]
        win = A.hp - loss >= floor
        # ---- death veto: ~3 turns from death and the fight is losing
        if not win and A.hp <= 3.0 * total_dpt:
            act = self._c2_emergency()
            if act:
                return act
        if win:
            step = self._melee_step(target)
            if step:
                self._goal("fight", f"{target.name} EVloss {loss:.0f}")
                if len(mobile) > 1 or loss > 0.3 * A.hp:
                    self._ev(f"EV fight: loss {loss:.1f} hp {A.hp} "
                             f"targets {[m.name for m, _, _ in stats]}")
                return step
            # diagonal-door block: try any legal melee on another target
            for m, _, _ in stats[1:]:
                step = self._melee_step(m)
                if step:
                    return step
            # winnable but no legal attack THIS turn (door geometry):
            # fall through to the other layers exactly like v1.1 — do NOT
            # flee a fight we are winning (dev seed 739: a Barbarian spent
            # 1300 steps fleeing a goblin it out-EV'd 10x)
            return None
        # ---- losing line: full disengage if speed allows
        act = self._flee(adj)
        if act:
            self._goal("flee", f"loss {loss:.0f} > hp {A.hp}")
            self._ev(f"EV flee: loss {loss:.1f} >= hp {A.hp}-floor")
            return act
        # (E-NH5 verdict: weapon-engraved Elbereth is CARVING — multi-turn,
        # helpless — and got three dev characters beaten to death mid-
        # engraving. Removed from the emergency chain; see report.)
        # ---- hold a choke: on a choke cell, packs engage one at a time
        topo = self._topo()
        if len(mobile) >= 2 and A.agent in topo.chokes:
            step = self._melee_step(target)
            if step:
                self._goal("hold-choke", f"{len(mobile)} attackers")
                self._ev(f"EV hold-choke: {len(mobile)} attackers, "
                         f"loss(pack) {loss:.1f}")
                return step
        # ---- retreat to a nearby choke when it clearly pays
        if len(mobile) >= 2:
            max_dpt = max(d for _, d, _ in stats)
            sum_ttk = sum(t for _, _, t in stats)
            loss_choke = 1.35 * max_dpt * sum_ttk
            if loss_choke < 0.75 * loss:
                best = None
                for cell in topo.chokes:
                    dist = max(abs(cell[0] - A.agent[0]),
                               abs(cell[1] - A.agent[1]))
                    if 0 < dist <= 3:
                        p = L.bfs(A.agent, [cell],
                                  avoid=self._suspects() | self._mcells())
                        if p and (best is None or len(p) < best[1]):
                            best = (p, len(p))
                if best:
                    self._goal("kite-choke", f"{len(mobile)} attackers")
                    self._ev(f"EV kite: choke loss {loss_choke:.1f} < "
                             f"open loss {loss:.1f}")
                    return self._step_path(best[0])
        # ---- nothing better than fighting
        step = self._melee_step(target)
        if step:
            self._goal("fight", f"cornered vs {target.name}")
            return step
        return None

    def _c2_prethrow(self, obs):
        """Ranged-first: soften fast/pack threats before contact."""
        if not self.ammo_letters:
            return None
        A = self.atlas
        L = A.level
        ax, ay = A.agent
        hostiles = [m for m in L.monsters
                    if not m.pet and m.name not in C.IMMOBILE and
                    m.pos not in L.no_attack]
        n_close = sum(1 for m in hostiles
                      if max(abs(m.x - ax), abs(m.y - ay)) <= 5)
        for m in hostiles:
            dx, dy = m.x - ax, m.y - ay
            dist = max(abs(dx), abs(dy))
            if dist < 2 or dist > 5:
                continue
            if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
                continue
            fast = m.speed > OUR_SPEED or m.name in FAST_THREATS
            if not fast and n_close < 2:
                continue
            key = (A.key, m.pos)
            if self.throws_at.get(key, 0) >= 6:
                continue
            sx = (dx > 0) - (dx < 0)
            sy = (dy > 0) - (dy < 0)
            cx, cy = ax + sx, ay + sy
            clear = True
            while (cx, cy) != m.pos:
                if not L.passable(cx, cy, bad_traps_ok=True) or \
                        any(mm.pos == (cx, cy) for mm in L.monsters):
                    clear = False
                    break
                cx, cy = cx + sx, cy + sy
            if not clear:
                continue
            letter = self.ammo_letters[0]
            self.throws_at[key] = self.throws_at.get(key, 0) + 1
            self._goal("ranged", f"{m.name} d{dist}")
            self._ev(f"EV throw: {m.name} at d{dist} (speed {m.speed})")
            self.queue = [letter, DIR_OF[(sx, sy)]]
            self.queue_tag = "throw"
            return "throw"
        return None

    def _c2_items(self, obs, pre_descent):
        """Item goal market: wear owned armor when safe; detour to floor
        food/ammo/armor. pre_descent=True limits to urgent/cheap grabs."""
        A = self.atlas
        L = A.level
        # wear what we carry (multi-turn: only when safe)
        if C2_ARMOR and self.wearable:
            danger_near = any(
                (not m.pet) and m.name not in C.IMMOBILE and
                max(abs(m.x - A.agent[0]), abs(m.y - A.agent[1])) <= 4
                for m in L.monsters)
            if not danger_near and A.hp >= 0.5 * A.hpmax and \
                    A.hunger < C.WEAK:
                for letter, slot, dsc in self.wearable:
                    if slot in self.worn_slots or \
                            self.wear_tried.get(letter, 0) >= 2:
                        continue
                    self.wear_tried[letter] = \
                        self.wear_tried.get(letter, 0) + 1
                    self._goal("wear", f"{slot}: {dsc[:30]}")
                    self.note(f"wearing {dsc[:40]} ({slot})")
                    self.queue = [letter]
                    self.queue_tag = "wear"
                    return "wear"
        # floor items
        if self.burdened:
            wanted_kinds = {"food"}
        else:
            wanted_kinds = {"food"}
            if C2_RANGED and len(self.ammo_letters) < 10:
                wanted_kinds.add("ammo")
            if C2_ARMOR:
                wanted_kinds.add("armor")
                wanted_kinds.add("armor2")
        if not (C2_FOOD2 or C2_ARMOR or C2_RANGED):
            return None
        # shop guard: picking up merchandise gets us killed by the
        # shopkeeper (dev seed 716). Any peaceful '@' on the level ->
        # no floor pickups except cells we've killed on (corpse drops).
        if any(m.cls == "@" and not m.pet for m in L.monsters) or \
                "unpaid" in A.message or "will cost you" in A.message:
            return None
        glyphs = obs["obs"]["glyphs"]
        radius = 14 if not pre_descent else (
            10 if A.hunger >= C.HUNGRY else 3)
        targets = P.item_targets(glyphs, A.agent, radius=radius)
        for val, cell, kind, name in targets:
            if kind not in wanted_kinds:
                continue
            if kind == "food" and not C2_FOOD2:
                continue
            tk = (A.key, cell)
            if self.loot_tries.get(tk, 0) >= 8:
                continue          # unreachable/refused item: stop thrashing
            if cell == A.agent:
                self.loot_tries[tk] = self.loot_tries.get(tk, 0) + 1
                self.pickup_kind = kind
                self._goal("loot", f"{kind}: {name}")
                self.queue_tag = "pickup"
                return "pickup"
            path = L.bfs(A.agent, [cell], avoid=self._travel_avoid({cell}))
            if path and len(path) <= radius:
                # only near-target attempts count toward give-up (a long
                # legitimate walk must not exhaust the budget)
                if len(path) <= 2:
                    self.loot_tries[tk] = self.loot_tries.get(tk, 0) + 1
                self._goal("loot", f"{kind}: {name} d{len(path)}")
                return self._step_path(path)
        return None

    def _c2_pace(self, obs, digger):
        """Role-conditional descent pacing: fragile roles defer descent
        while beatable prey is visible and xp lags depth."""
        A = self.atlas
        if digger or self.role not in FRAGILE_ROLES:
            return None
        allowed = PACE_DEPTH + PACE_XP_STEP * (A.xplvl - 1)
        if A.depth < allowed or A.hunger >= C.WEAK:
            return None
        until = self.pace_grind_until.setdefault(A.key,
                                                 A.time + PACE_BUDGET)
        if A.time >= until:
            return None
        prey = []
        for m in self._mobile_hostiles():
            if self._never_melee(m) or m.speed > OUR_SPEED:
                continue
            dpt = P.species_dpt(m.name, m.difficulty)
            ttk = P.species_ttk(m.name, m.difficulty, role=self.role,
                                xplvl=A.xplvl)
            if 1.35 * dpt * ttk < 0.35 * A.hp and m.difficulty <= A.xplvl + 1:
                d = max(abs(m.x - A.agent[0]), abs(m.y - A.agent[1]))
                if d <= 10:
                    prey.append((d, m))
        if not prey:
            return None
        prey.sort(key=lambda t: t[0])
        m = prey[0][1]
        path = A.level.bfs(A.agent, [m.pos],
                           avoid=self._suspects() |
                           (self._mcells() - {m.pos}))
        if path:
            self._goal("grind", f"{m.name} (xp{A.xplvl} d{A.depth})")
            return self._step_path(path)
        return None

    # ------------------------------------------------------------- decision
    def _decide(self, obs, msg):
        A = self.atlas
        L = A.level
        if C2_RANGED or C2_ARMOR:
            self._c2_scan_inv(obs)
            if "burdened" in msg.lower():
                self.burdened = True
        if C2_ANY:
            self._wields_weapon = any(
                oc == 2 and ("weapon in hand" in d.lower() or
                             "weapons in hands" in d.lower())
                for _l, d, oc in self._inv(obs))

        # ---- P0: prompts ------------------------------------------------
        in_yn, in_getlin, waitspace = C.misc_of(obs)
        prompt_open = in_yn or in_getlin or waitspace
        if prompt_open:
            if self.queue:
                self.last_prompt_sig = None
                return self._pop_queue()
            sig = (in_yn, in_getlin, waitspace, msg[-60:])
            if sig == self.last_prompt_sig:
                self.prompt_repeats += 1
            else:
                self.prompt_repeats = 0
            self.last_prompt_sig = sig
            if self.prompt_repeats >= 4:
                # cycle escapes for prompts that refuse our default
                return ["esc", "space", "more", "n"][self.prompt_repeats % 4]
            return self._answer_prompt(obs, msg, in_yn, in_getlin, waitspace)
        else:
            self.last_prompt_sig = None
            self.prompt_repeats = 0
            if not self.queue:
                self.queue_tag = None   # tags only live into their prompt

        # zero-time livelock breaker: the env aborts after 150 env steps
        # without game-time advance; search always consumes a turn
        if self.no_time_steps > 60:
            self.queue = []
            self.queue_tag = None
            return "search"

        # ---- P1: scripted queue ------------------------------------------
        if self.queue:
            # prompt-answer entries are only valid inside a prompt
            if self.queue_tag in ("pray", "eat", "eat_corpse"):
                self.queue = []
                self.queue_tag = None
            else:
                return self._pop_queue()

        # ---- P1.5: Phase L stall watchdog (NH-E15) ------------------------
        if C2_E15:
            self._watchdog()

        # ---- P2: swallowed ------------------------------------------------
        if A.swallowed:
            self.note("swallowed: attacking engulfer")
            return "west"

        # ---- P2.5: identify the (invisible) terrain under our feet -------
        if self.need_look and not self._adjacent_hostiles():
            self.need_look = False
            return "look"

        # ---- P2.7: protected rest on a live Elbereth engraving -----------
        if C2_ELBERETH and self._on_elbereth() and A.hp < 0.85 * A.hpmax:
            hostiles_near = any(
                (not m.pet) and m.name not in C.IMMOBILE and
                max(abs(m.x - A.agent[0]), abs(m.y - A.agent[1])) <= 3
                for m in A.level.monsters)
            if hostiles_near and A.hunger < C.WEAK:
                self._goal("rest", "on Elbereth")
                return "search"

        # ---- P3: emergency survival --------------------------------------
        adj = self._adjacent_hostiles()
        # prayer heals only in "major trouble" (hp < hpmax/7): fire it there
        if A.hp <= max(A.hpmax // 7, 5) and \
                self._pray_ok(last_resort=bool(adj) and A.hp <= 4):
            self.prayed_at = A.time
            self.pray_count += 1
            self.note(f"pray (hp {A.hp}/{A.hpmax})")
            self._goal("survive", f"pray hp {A.hp}/{A.hpmax}")
            self.queue = ["y"]
            self.queue_tag = "pray"
            return "pray"
        if C2_EXPMAX:
            if adj:
                act = self._c2_combat(obs, adj)
                if act:
                    return act
        else:
            # crisis zone: below ~28% max HP, or worst recent hit could
            # kill us within two more exchanges -> disengage from slower
            crisis = A.hp <= max(A.hpmax * 0.28, 6) or \
                (self.recent_max_hit * 2 >= A.hp and self.recent_max_hit > 0)
            if crisis and adj:
                act = self._flee(adj)
                if act:
                    return act

        # hunger crisis handled with priority right below emergencies
        if A.hunger >= C.WEAK:
            self._goal("eat", f"hunger {A.hunger}")
            fl = self._food_letter(obs)
            if fl:
                self.note(f"eat inventory food {fl} (hunger {A.hunger})")
                self.queue = [fl]
                self.queue_tag = "eat"
                return "eat"
            corpse = self._fresh_corpse_here()
            if corpse:
                self.note(f"eat fresh corpse here ({corpse})")
                self.queue = ["y"]
                self.queue_tag = "eat_corpse"
                return "eat"
            # walk to a fresh safe corpse nearby
            cells = [k[0] for k in self.fresh_kills
                     if k[1] in C.SAFE_CORPSES and not self._cannibal(k[1])
                     and k[0] != A.agent]
            if cells:
                path = A.level.bfs(A.agent, cells,
                                   avoid=self._suspects() | self._mcells())
                if path and len(path) <= 12:
                    return self._step_path(path)
            fainting_ok = (A.hunger >= C.FAINTING and self.pray_count < 5 and
                           (self.prayed_at is None or
                            A.time - self.prayed_at > 400))
            # PRAY_DEATH lever: praying with a mobile hostile adjacent
            # donates ~10+ free attacks; kill/escape first unless fainting
            pray_now = self._pray_ok() or fainting_ok
            if C2_PRAYFIX and pray_now and A.hunger < C.FAINTING and \
                    any(m.name not in C.IMMOBILE for m in adj):
                pray_now = False
                self._ev(f"PRAYFIX: deferring hunger prayer, "
                         f"{[m.name for m in adj]} adjacent")
            if pray_now:
                self.prayed_at = A.time
                self.pray_count += 1
                self.note(f"pray (hunger {A.hunger})")
                self.queue = ["y"]
                self.queue_tag = "pray"
                return "pray"
        elif A.hunger == C.HUNGRY:
            fl = self._food_letter(obs)
            if fl:
                self._goal("eat", "hungry: inventory")
                self.queue = [fl]
                self.queue_tag = "eat"
                return "eat"
            if C2_FOOD2:
                # eat a fresh safe corpse underfoot already at Hungry:
                # waiting for Weak wastes the freshness window
                corpse = self._fresh_corpse_here()
                if corpse:
                    self._goal("eat", f"hungry: fresh {corpse}")
                    self.note(f"eat fresh corpse at Hungry ({corpse})")
                    self.queue = ["y"]
                    self.queue_tag = "eat_corpse"
                    return "eat"
            if C2_CASTHUNGER and self._caster_active():
                # CAST_HUNGER_V1(b): casters treat HUNGRY as the eat
                # trigger, not Weak — the "too hungry to cast" failure
                # arrives mid-fight, precisely when the bolt was the plan.
                # Same walk-to-corpse search as the Weak branch.
                cells = [k[0] for k in self.fresh_kills
                         if k[1] in C.SAFE_CORPSES and not
                         self._cannibal(k[1]) and k[0] != A.agent]
                if cells:
                    path = A.level.bfs(A.agent, cells,
                                       avoid=self._suspects() |
                                       self._mcells())
                    if path and len(path) <= 12:
                        self._goal("eat", "caster eat-early at Hungry")
                        return self._step_path(path)

        # held by a sticky monster: kill it, fleeing is impossible
        if "cannot escape from" in msg:
            m2 = re.search(r"cannot escape from (?:the |an? )?([a-z' -]+?)!", msg)
            if m2:
                for m in self._adjacent_hostiles():
                    if m.name == m2.group(1).strip() and \
                            m.name not in C.NEVER_MELEE:
                        d = (m.x - A.agent[0], m.y - A.agent[1])
                        if d in DIR_OF:
                            return DIR_OF[d]

        # ---- P4.9: Phase L attack-spell casting (CAST_ATTACK_V1) ----------
        if C2_CAST:
            # stale in-flight cast (prompt never arrived): clear + learn
            if self.cast_dir and self.steps - self.cast_step > 3:
                self.cast_dir = None
            act = self._cast_attack(adj)
            if act:
                return act

        # ---- P5: combat ---------------------------------------------------
        # NH-E15 disengage: during a watchdog L2 window, standoff combat is
        # skipped (descent/exploration layers take over); crisis handling
        # at P3 still runs first, so this never suppresses emergencies.
        wd_disengaged = C2_E15 and self.steps < self.wd_disengage_until
        if adj and not C2_EXPMAX and not wd_disengaged:
            act = self._combat(adj)
            if act:
                return act
        if adj and C2_EXPMAX:
            # expectimax already ran at P3; handle remaining never-melee
            # mobile threats with the legacy step-away logic
            act = self._combat([m for m in adj if self._never_melee(m)])
            if act:
                return act

        # ---- P5.2: ranged-first softening (Campaign 2) ---------------------
        if C2_RANGED:
            act = self._c2_prethrow(obs)
            if act:
                return act

        # ---- P5.5: ranged removal of never-melee blockers ------------------
        # (dev seed 116: a sleeping floating eye parked in a 1-wide corridor
        # walled off the only route to the '>' for 4,000 turns)
        act = self._throw_at_blocker(obs)
        if act:
            return act

        # blind: sit tight until it clears (map can't be trusted)
        if A.blind:
            return "search"

        # global rest gate: badly hurt, nothing visible hunting us -> heal
        if A.hp < 0.35 * A.hpmax and self._rest_here_ok() and \
                self.rest_budget.get(A.key, 0) < 900:
            self.rest_budget[A.key] = self.rest_budget.get(A.key, 0) + 1
            self._goal("rest", f"hp {A.hp}/{A.hpmax}")
            return "search"

        # ---- P5.7: shallow opportunistic hunting (V1.1 L2) -----------------
        if HUNT_SHALLOW and A.depth <= 4 and A.hp >= 0.6 * A.hpmax and \
                not self.digger_letter and \
                self.hunt_turns.get(A.key, 0) < 250:
            prey = [m for m in self._mobile_hostiles()
                    if m.difficulty <= A.xplvl + 1 and m.speed <= OUR_SPEED
                    and not self._never_melee(m)
                    and max(abs(m.x - A.agent[0]),
                            abs(m.y - A.agent[1])) <= 6]
            if prey:
                tgt = min(prey, key=lambda m: max(abs(m.x - A.agent[0]),
                                                  abs(m.y - A.agent[1])))
                path = A.level.bfs(A.agent, [tgt.pos],
                                   avoid=self._suspects() |
                                   (self._mcells() - {tgt.pos}))
                if path:
                    t0 = self.hunt_turns.setdefault(A.key, 0)
                    self.hunt_turns[A.key] = t0 + 1
                    return self._step_path(path)

        # ---- P6.5: urgent/cheap item grabs before committing to descent ----
        if C2_ANY:
            act = self._c2_items(obs, pre_descent=True)
            if act:
                return act

        # ---- P6/P7: descent (dig > stairs), with rest gate -----------------
        act = self._descend(obs)
        if act:
            return act

        # ---- P8: digger acquisition detour ---------------------------------
        act = self._acquire_digger(obs)
        if act:
            return act

        # ---- P8.5: item goal market (Campaign 2) ----------------------------
        if C2_ANY:
            act = self._c2_items(obs, pre_descent=False)
            if act:
                return act

        # opportunistic floor pickup via the message channel (an item under
        # the agent is INVISIBLE in glyphs — the @ covers it; "You see
        # here" is the only on-cell item sensor)
        m3 = RE_SEE_HERE.search(msg)
        if m3 and C2_ANY and ("for sale" in msg or "zorkmids" in msg):
            m3 = None            # shop merchandise: taking it = death
        if m3 and self.queue_tag != "pickup":
            it = m3.group(1)
            if any(k in it for k in ("food ration", "cram ration", "lembas",
                                     "K-ration", "C-ration", "pancake",
                                     "candy bar", "fortune cookie", "apple",
                                     "orange", "pear", "banana", "melon",
                                     "carrot", "meatball", "meat stick")):
                self.note(f"picking up food: {it}")
                self.queue_tag = "pickup"
                return "pickup"
            if C2_ARMOR and any(k in it for k in
                                P.BODY_ARMOR + P.HELMETS + P.SHIELDS +
                                P.BOOTS_GLOVES):
                self.note(f"picking up armor: {it}")
                self._goal("loot", f"armor here: {it[:30]}")
                self.pickup_kind = "armor"
                self.queue_tag = "pickup"
                return "pickup"
            if C2_RANGED and len(self.ammo_letters) < 10 and \
                    any(k in it for k in P.AMMO_NAMES):
                self.note(f"picking up ammo: {it}")
                self._goal("loot", f"ammo here: {it[:30]}")
                self.pickup_kind = "ammo"
                self.queue_tag = "pickup"
                return "pickup"

        # ---- P8.9: repeated-layout stair goal (REPEAT_LAYOUT_STAIRS V2) ----
        # V1 (explore_target hint) was INERT: _explore only honors a target
        # already in the frontier set, and a cross-map stair prediction
        # never is — REPEAT-1 paired block read exact-0.00 on all 20 seeds
        # while detections fired 5/5 (fires≠effect, the ARMOR-bug pattern).
        # V2 makes the prediction a FIRST-CLASS GOAL: route to the frontier
        # cell nearest the predicted stair cell under a bounded per-level
        # budget; refute the prediction if the cell explores to non-stairs.
        if C2_REPEAT:
            hint = self._repeat_hint()
            if hint is not None:
                hx, hy = hint
                if A.level.explored[hy][hx]:
                    if hint not in (A.level.stairs_down | A.level.holes):
                        self._ev(f"REPEAT2: prediction {hint} refuted "
                                 f"(explored, no stairs)")
                        self.repeat_pred = False
                    # else: stairs known — descent layer takes over
                else:
                    used = self.repeat_budget.get(A.key, 0)
                    if used >= REPEAT_BUDGET:
                        if used == REPEAT_BUDGET:
                            self._ev("REPEAT2: budget exhausted, "
                                     "normal explore resumes")
                            self.repeat_budget[A.key] = used + 1
                    else:
                        frontier = A.level.frontier_cells()
                        if frontier:
                            tgt = min(frontier,
                                      key=lambda c: max(abs(c[0] - hx),
                                                        abs(c[1] - hy)))
                            path = A.level.bfs(A.agent, [tgt],
                                               avoid=self._travel_avoid())
                            if path:
                                if used == 0:
                                    self._ev(f"REPEAT2: routing to "
                                             f"predicted stairs {hint} "
                                             f"via frontier {tgt}")
                                self._goal("find-stairs",
                                           f"repeat-layout goal {hint}")
                                self.repeat_budget[A.key] = used + 1
                                return self._step_path(path)

        # ---- P9: explore ----------------------------------------------------
        act = self._explore(obs)
        if act:
            return act

        # ---- P10: doors ------------------------------------------------------
        act = self._doors(obs)
        if act:
            return act

        # ---- P11: hidden passages -------------------------------------------
        act = self._hidden_search(obs)
        if act:
            return act

        # ---- P12: fallback ----------------------------------------------------
        return "search"

    # --------------------------------------------------------------- queue
    def _pop_queue(self):
        a = self.queue.pop(0)
        if not self.queue:
            self.queue_tag = None
        return a

    # ------------------------------------------------------------- prompts
    # ------------------------------------- Phase L: repeated-layout predictor
    # RULE CARD [REPEAT_LAYOUT_STAIRS] (layer: PROCEDURE + MEMORY; model:
    # Fable 5 max): statement: when the current level's explored terrain
    # matches the previous level's terrain at >=85% over >=60 comparable
    # cells, predict the down-stairs at the previous level's down-stairs
    # cell and bias exploration there (explore_target hint only — normal
    # give-up logic applies if wrong/unreachable).
    # mechanism: the vendored NLE seeded generator REPEATS level layouts:
    # 19/96 consecutive-level pairs in the CAST-1 block share >60%
    # identical explored rows, many pixel-identical (seed 809 D6=D7=D8;
    # seed 990 D1-D3 with stair transits [63,4]->[14,15] three descents
    # running — E18 reflection R1, validated within-episode). Score = depth
    # before death; descent time is the currency; starvation deaths are
    # descent-stalled episodes.
    # evidence: offline corpus scan (96 pairs) + within-episode prediction
    # hit. status: provisional until its paired dev block. scope: belief-
    # derived, works on any level whose predecessor was partially mapped.
    def _repeat_hint(self):
        A = self.atlas
        if self.repeat_pred is False or self.prev_level_key is None:
            return None
        if self.repeat_pred is not None:
            return self.repeat_pred
        L = A.level
        P_ = A.levels.get(self.prev_level_key)
        if P_ is None:
            return None
        explored = sum(1 for y in range(C.ROWS) for x in range(C.COLS)
                       if L.explored[y][x])
        if explored - self.repeat_checked_exp < 25:
            return None                 # re-check every ~25 new cells
        self.repeat_checked_exp = explored
        comparable = match = 0
        for y in range(C.ROWS):
            for x in range(C.COLS):
                if L.explored[y][x] and P_.explored[y][x]:
                    comparable += 1
                    if int(L.terrain[y][x]) == int(P_.terrain[y][x]):
                        match += 1
        if comparable < 60:
            return None
        if match / comparable < 0.85:
            if comparable > 200:        # decisively different: stop checking
                self.repeat_pred = False
            return None
        # find previous level's down-stairs
        for y in range(C.ROWS):
            for x in range(C.COLS):
                if P_.explored[y][x] and \
                        int(P_.terrain[y][x]) == C.STAIRS_DOWN:
                    self.repeat_pred = (x, y)
                    self.repeat_fires += 1
                    self.note(f"REPEAT layout detected "
                              f"({match}/{comparable}): predicting stairs "
                              f"at {self.repeat_pred}")
                    return self.repeat_pred
        self.repeat_pred = False
        return None

    # ---------------------------------------------- Phase L: stall watchdog
    # RULE CARD [STALL_WATCHDOG_V1] (layer: PROCEDURE; NH-E15; model:
    # Fable 5 max): statement: if over the last WD_WINDOW(150) game turns
    # NO new tiles were explored AND depth AND xp are unchanged, the
    # episode is stalled; escalate: L1 perturbation (drop the current
    # explore target so a different frontier is chosen), L2 disengage
    # (for WD_DISENGAGE env steps, prefer movement/descent over repeated
    # standoff combat; if a digger is held, force the dig-down line).
    # mechanism evidence: the v1 ~400-turn giant-bat dig standoff
    # (clean_A ep4 archeologist digdeath) — three strategy transitions
    # overdue; stall classes cost score at zero risk compensation.
    # status: provisional (rides the next dev block; fires + no-regression
    # = keep). scope: dev/all arms once validated; all fires logged to
    # wd_fires + notes.
    def _watchdog(self):
        A = self.atlas
        explored = sum(row.count(True) if isinstance(row, list) else
                       int(row.sum()) for row in A.level.explored)
        self.wd_hist.append((A.time, explored, A.depth, A.xplvl))
        if len(self.wd_hist) > 4000:
            del self.wd_hist[:2000]
        # find the newest record at least WD_WINDOW game turns old
        cutoff = A.time - WD_WINDOW
        old = None
        for rec in reversed(self.wd_hist):
            if rec[0] <= cutoff:
                old = rec
                break
        if old is None:
            return
        if A.time - self.wd_last_fire_t < WD_WINDOW:
            return                     # cooldown: one fire per window
        _, oexp, odep, oxp = old
        if explored > oexp or A.depth != odep or A.xplvl > oxp:
            self.wd_level = 0          # progress: relax
            return
        # healing during a deliberate rest/eat IS progress, not a stall
        if self.subgoal and self.subgoal[0] in ("rest", "eat") and \
                A.hp < A.hpmax:
            return
        # stalled
        self.wd_level = min(self.wd_level + 1, 2)
        self.wd_last_fire_t = A.time
        if self.wd_level == 1:
            self.explore_target = None
            act = "perturb-explore"
        else:
            self.wd_disengage_until = self.steps + WD_DISENGAGE
            act = "disengage"
        self.wd_fires.append((self.steps, A.time, self.wd_level, act))
        self.note(f"WATCHDOG L{self.wd_level}: stalled {WD_WINDOW}t "
                  f"(tiles {oexp}=={explored}, depth {A.depth}) -> {act}")
        self._goal("survive", f"watchdog {act}")

    # ------------------------------------------------- Phase L: spellcasting
    # RULE CARD [CAST_ATTACK_V1] (layer: PROCEDURE; model: Fable 5 max):
    # statement: with a known attack spell at fail% <= CAST_FAIL_MAX and
    #   Pw >= 5*level, cast at (a) any adjacent hostile, preferring
    #   never-melee species (spells bypass touch/passive effects: floating
    #   eye, cockatrice class), else (b) a straight-line hostile within
    #   CAST_LINE_RANGE if it is fast/never-melee (kill-before-contact) and
    #   the ray path is clear of walls/other monsters/pets.
    # mechanism: force bolt never misses (probe: 3/3 quarterstaff misses vs
    #   1-cast kill on the same branch); menu grammar cast->letter->direction
    #   (probe records e16_probes/cast_forcebolt*.json, dev seeds 715/940);
    #   Pw deducted at letter selection; menu carries Fail% column; 'more'
    #   dismisses the menu at zero cost (probe); Xp1 Wizard force bolt =
    #   5 Pw, 0% fail.
    # evidence: NH-E16 branch probes (deterministic replay) + KB
    #   provenance:wiki (Spellbook of force bolt; Wizard) + paired-branch
    #   cast-vs-melee comparison. status: provisional until the paired dev
    #   block lands. scope: any role whose cast menu yields an attack spell
    #   passing the gates; discovery cast only attempted for Wizard until
    #   other roles are probed.
    def _parse_cast_menu(self, obs, msg):
        """Parse 'Choose which spell to cast' menu into cast_spells and
        select the best usable attack spell (min fail, then min level)."""
        text = msg if "force bolt" in msg or " - " in msg else ""
        rows = re.findall(
            r"([a-zA-Z]) - ([a-z' -]+?)\s{2,}(\d+)\s+([a-z]+)\s+(\d+)%",
            text)
        if not rows:        # fall back to tty lines (menu may overflow msg)
            tty = obs["obs"]["tty_chars"]
            text = "\n".join("".join(chr(int(c)) for c in row)
                             for row in tty)
            rows = re.findall(
                r"([a-zA-Z]) - ([a-z' -]+?)\s{2,}(\d+)\s+([a-z]+)\s+(\d+)%",
                text)
        self.cast_spells = {l: (n.strip(), int(lv), cat, int(f))
                            for l, n, lv, cat, f in rows}
        best = None
        for l, (n, lv, cat, f) in self.cast_spells.items():
            if cat == "attack" and f <= CAST_FAIL_MAX:
                k = (f, lv)
                if best is None or k < best[0]:
                    best = (k, l, n, 5 * lv)
        if best:
            self.cast_choice = (best[1], best[2], best[3])
            self.note(f"cast menu: {self.cast_spells} -> choice "
                      f"{self.cast_choice}")
        else:
            self.cast_choice = None
            self.cast_unavailable = True
            self.note(f"cast menu: no usable attack spell "
                      f"{self.cast_spells}")

    def _caster_active(self):
        """True when this episode is actually using the cast repertoire
        (CAST_HUNGER_V1 scope guard: doctrine must not touch non-casters)."""
        return C2_CAST and not self.cast_unavailable and \
            (self.cast_choice is not None or self.cast_fires > 0 or
             self.role == "Wizard")

    def _cast_ready(self):
        if not C2_CAST or self.cast_unavailable:
            return False
        # CAST_HUNGER_V1(a): a hunger-refused cast stays blocked until fed
        # — stops the refusal-retry loop (2759 wasted steps, seed 839) and
        # lets melee/throw doctrine take the fight over.
        if C2_CASTHUNGER and self.cast_hunger_blocked:
            return False
        if self.cast_spells is None and self.role != "Wizard":
            return False        # discovery restricted to Wizard (carded)
        cost = self.cast_choice[2] if self.cast_choice else 5
        return self.atlas.pw >= cost

    def _cast_attack(self, adj):
        """Attack-spell layer: adjacent first (never-melee preferred),
        then kill-before-contact line targets. Returns 'cast' or None."""
        if not self._cast_ready():
            return None
        A = self.atlas
        ax, ay = A.agent
        target = None
        # (a) adjacent hostiles: never-melee species first, else weakest
        # (CAST_NEVER_PEACEFUL_CLASS guard on both branches)
        if adj:
            pool = [m for m in adj if m.name not in CAST_NEVER]
            nm = [m for m in pool if self._never_melee(m)]
            pool = nm or pool
            target = min(pool, key=lambda m: m.difficulty) if pool else None
        else:
            # (b) straight-line fast/never-melee threats within range
            for m in self._mobile_hostiles():
                if m.name in CAST_NEVER:
                    continue
                dx, dy = m.x - ax, m.y - ay
                dist = max(abs(dx), abs(dy))
                if not (2 <= dist <= CAST_LINE_RANGE):
                    continue
                if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
                    continue
                if not (m.name in FAST_THREATS or self._never_melee(m)
                        or m.speed > OUR_SPEED):
                    continue
                sx = (dx > 0) - (dx < 0)
                sy = (dy > 0) - (dy < 0)
                clear = True
                cx, cy = ax + sx, ay + sy
                occupied = {(mm.x, mm.y) for mm in A.level.monsters}
                while (cx, cy) != (m.x, m.y):
                    if not A.level.passable(cx, cy, doors_ok=False) or \
                            (cx, cy) in occupied:
                        clear = False
                        break
                    cx, cy = cx + sx, cy + sy
                if clear:
                    target = m
                    break
        if target is None:
            return None
        d = (((target.x > ax) - (target.x < ax)),
             ((target.y > ay) - (target.y < ay)))
        if d not in DIR_OF:
            return None
        self.cast_dir = DIR_OF[d]
        self.cast_step = self.steps
        self._goal("fight", f"cast at {target.name}")
        self.note(f"cast at {target.name} dir {self.cast_dir} "
                  f"(pw {A.pw})")
        return "cast"

    def _answer_prompt(self, obs, msg, in_yn, in_getlin, waitspace):
        A = self.atlas
        if in_getlin:
            return "esc"
        if in_yn:
            # Phase L NH_CAST: the cast flow's direction prompt. Must come
            # before the generic "In what direction" -> esc fallback.
            if C2_CAST and self.cast_dir and "In what direction" in msg:
                d = self.cast_dir
                self.cast_dir = None
                self.cast_fires += 1
                if self.store is not None:
                    self.store.first(self.steps, A.time, "verb", "cast")
                return d
            if "Really attack" in msg:
                # peaceful: mark the intended cell and decline
                if self.last_action in DIRS:
                    dx, dy = DIRS[self.last_action]
                    cell = (A.agent[0] + dx, A.agent[1] + dy)
                    A.level.no_attack.add(cell)
                    self.note(f"peaceful at {cell}: declining attack")
                return "n"
            if "eat it?" in msg or "eat one?" in msg:
                m = re.search(r"There (?:is|are) (?:an? )?([a-z' -]+?) corpse", msg)
                if m and m.group(1) in C.SAFE_CORPSES and \
                        not self._cannibal(m.group(1)):
                    return "y"
                return "n"
            if "Are you sure you want to pray" in msg:
                return "y" if self.queue_tag == "pray" else "n"
            if "In what direction" in msg:
                return "esc"
            if "Do you want to add to the current engraving" in msg:
                return "n"
            if "lock it?" in msg or "Force its lock" in msg:
                return "esc"
            if "Shall I remove" in msg or "loot it?" in msg:
                return "n"
            if "Continue?" in msg:
                return "y" if self.queue_tag == "dig" else "n"
            if "What do you want" in msg:
                return "esc"
            return "esc"
        # xwaitingforspace: menus / overview screens
        # Phase L NH_CAST: spell-selection menu. Parse once per episode,
        # pick the best attack spell (fail% gate), answer with its letter
        # if a cast is in flight, else dismiss.
        if C2_CAST and ("Choose which spell to cast" in msg or
                        self._tty_has(obs, "Choose which spell")):
            self._parse_cast_menu(obs, msg)
            if self.cast_choice and self.cast_dir:
                return self.cast_choice[0]
            self.cast_dir = None
            return "more"           # verified zero-cost dismissal (probe)
        if "Pick up what" in msg or self._tty_has(obs, "Pick up what"):
            kws = ("pick-axe", "mattock")
            if self.pickup_kind == "food":
                kws = kws + P.FOOD_NAMES if P else kws
            elif self.pickup_kind == "ammo":
                kws = kws + P.AMMO_NAMES if P else kws
            elif self.pickup_kind in ("armor", "armor2"):
                kws = kws + P.BODY_ARMOR + P.HELMETS + P.SHIELDS + \
                    P.BOOTS_GLOVES if P else kws
            letter = self._menu_letter_for(obs, kws)
            if letter and self.queue_tag == "pickup":
                self.pickup_kind = None
                self.queue = ["more"]
                return letter
            return "esc"
        return "esc"

    def _tty_has(self, obs, text):
        tty = obs["obs"]["tty_chars"]
        for row in tty:
            if text in "".join(chr(c) for c in row):
                return True
        return False

    def _menu_letter_for(self, obs, keywords):
        tty = obs["obs"]["tty_chars"]
        for row in tty:
            line = "".join(chr(c) for c in row)
            m = re.search(r"([a-zA-Z]) - (.*)", line)
            if m and any(k in m.group(2) for k in keywords):
                return m.group(1)
        return None

    def _fresh_corpse_here(self):
        A = self.atlas
        for (cell, species, t) in reversed(self.fresh_kills):
            if cell == A.agent and species in C.SAFE_CORPSES and \
                    not self._cannibal(species):
                return species
        return None

    # -------------------------------------------------------------- combat
    def _combat(self, adj):
        A = self.atlas
        L = A.level
        ax, ay = A.agent
        threats = [m for m in adj if not self._never_melee(m)]
        nm_threats = [m for m in adj if self._never_melee(m) and
                      m.name not in C.IMMOBILE]

        # threat budget: flee/hold when outmatched
        danger = sum(m.difficulty for m in adj if m.name not in C.IMMOBILE)
        if (A.hp < 0.3 * A.hpmax and len([m for m in adj
                                          if m.name not in C.IMMOBILE]) >= 2):
            # retreat to the neighbor cell with fewest adjacent threats
            best = None
            for name, (nx, ny) in L.neighbors(ax, ay, avoid=self._suspects()):
                if any(m.x == nx and m.y == ny for m in L.monsters):
                    continue
                dgr = sum(1 for m in adj
                          if max(abs(m.x - nx), abs(m.y - ny)) <= 1)
                if best is None or dgr < best[0]:
                    best = (dgr, name)
            if best and best[0] < len(adj):
                self.note(f"retreat (hp {A.hp}, danger {danger})")
                return best[1]

        # attack the weakest attackable adjacent hostile (cardinal-legal)
        threats.sort(key=lambda m: m.difficulty)
        for m in threats:
            if m.name in C.IMMOBILE and not self._blocks_path(m):
                continue
            d = (m.x - ax, m.y - ay)
            t_here = L.terrain[ay][ax]
            t_there = L.terrain[m.y][m.x]
            if d[0] and d[1] and (
                    t_here in (C.DOORWAY, C.DOOR_OPEN, C.DOOR_CLOSED) or
                    t_there in (C.DOORWAY, C.DOOR_OPEN, C.DOOR_CLOSED)):
                continue
            return DIR_OF[d]

        # only never-melee mobile threats adjacent: step away if possible
        if nm_threats:
            for name, (nx, ny) in L.neighbors(ax, ay, avoid=self._suspects()):
                if all(max(abs(m.x - nx), abs(m.y - ny)) > 1
                       for m in nm_threats) and \
                        not any(m.x == nx and m.y == ny for m in L.monsters):
                    self.note(f"stepping away from {nm_threats[0].name}")
                    return name
            # cornered vs a touch-killer: weapon melee is source-safe
            # (see RULE CARD [TOUCH_KILL_WEAPON_MELEE])
            if C2_ANY and self.role != "Monk" and self._wields_weapon:
                for m in nm_threats:
                    if m.name in TOUCH_KILL:
                        step = self._melee_step(m)
                        if step:
                            self.note(f"cornered: weapon melee vs "
                                      f"{m.name} (touch-kill, wielded)")
                            self._ev(f"TOUCHKILL guard: weapon melee "
                                     f"{m.name}")
                            return step
            return "search"     # nowhere better: pass time, don't touch it
        return None

    def _flee(self, adj):
        """Crisis disengage: NetHack speed system makes running away work
        against slower species (dwarf 6, zombie 6, mold 0) and suicide
        against faster ones -- flee only when every adjacent mobile threat
        is slower than us; otherwise keep fighting (E2 lesson from the
        MiniHack arm: dashing while surrounded by fast monsters is worse
        than trading blows)."""
        A = self.atlas
        L = A.level
        mobile = [m for m in adj if m.name not in C.IMMOBILE]
        if not mobile:
            return None
        # outrunning needs a real speed margin: a speed-9 monster still
        # attacks on ~3 of 4 turns while "outrun" at speed 12
        if any(m.speed > (OUR_SPEED * 2) // 3 for m in mobile):
            return None
        if "cannot escape" in A.message or "still in a pit" in A.message or \
                "You fall into a pit" in A.message:
            return None                # held: fleeing burns turns for nothing
        ax, ay = A.agent
        # on known up stairs: escape the level entirely
        if A.agent in L.stairs_up and self.retreat_ups < 3:
            self.retreat_ups += 1
            self.note(f"crisis: escaping upstairs (hp {A.hp})")
            return "up"
        # move to the neighbor that maximizes distance from threats;
        # sticky direction (dev seed 109: direction flip-flop vs a speed-9
        # crocodile gained zero distance and donated bites)
        best = None
        prev = self.last_action if self.last_action in DIRS else None
        for name, (nx, ny) in L.neighbors(ax, ay, avoid=self._suspects()):
            if any(m.x == nx and m.y == ny for m in L.monsters):
                continue
            score = min(max(abs(m.x - nx), abs(m.y - ny)) for m in mobile)
            adjcnt = sum(1 for m in mobile
                         if max(abs(m.x - nx), abs(m.y - ny)) <= 1)
            sticky = 0 if name == prev else 1
            if best is None or (adjcnt, -score, sticky) < best[0]:
                best = ((adjcnt, -score, sticky), name)
        # flee only when the move fully disengages (0 adjacent threats after
        # it); partial retreats just donate free attacks (dev seed 103)
        if best and best[0][0] == 0:
            self.note(f"crisis: fleeing {mobile[0].name} (hp {A.hp})")
            return best[1]
        return None

    def _throwable_letter(self, obs):
        for letter, desc, oc in self._inv(obs):
            d = desc.lower()
            # "not wielded" contains "wielded" — only skip actual wields
            if "weapon in hand" in d or "weapons in hands" in d or \
                    ("wielded" in d and "not wielded" not in d):
                continue
            if any(k in d for k in ("dagger", "dart", "arrow", "spear",
                                    "shuriken", "rock", "aklys")):
                return letter
        return None

    def _throw_at_blocker(self, obs):
        A = self.atlas
        L = A.level
        ax, ay = A.agent
        letter = self._throwable_letter(obs)
        if not letter:
            return None
        for m in L.monsters:
            if m.pet or not self._never_melee(m):
                continue
            dx, dy = m.x - ax, m.y - ay
            dist = max(abs(dx), abs(dy))
            if dist < 1 or dist > 8:
                continue
            if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
                continue
            key = (A.key, m.pos)
            if self.throws_at.get(key, 0) >= 8:
                continue
            # ray must be clear (passable, no other monster) up to the target
            sx = (dx > 0) - (dx < 0)
            sy = (dy > 0) - (dy < 0)
            cx, cy = ax + sx, ay + sy
            clear = True
            while (cx, cy) != m.pos:
                if not L.passable(cx, cy, bad_traps_ok=True) or \
                        any(mm.pos == (cx, cy) for mm in L.monsters):
                    clear = False
                    break
                cx, cy = cx + sx, cy + sy
            if not clear:
                continue
            # only spend ammo when it actually blocks us (goal or frontier
            # unreachable without its cell) or it is adjacent
            if dist > 1 and not self._blocks_route(m):
                continue
            self.throws_at[key] = self.throws_at.get(key, 0) + 1
            self.note(f"throwing {letter} at {m.name} at {m.pos} "
                      f"(dist {dist})")
            self.queue = [letter, DIR_OF[(sx, sy)]]
            self.queue_tag = "throw"
            return "throw"
        return None

    def _blocks_route(self, m):
        A = self.atlas
        L = A.level
        goals = set(L.stairs_down) | set(L.holes)
        if not goals:
            cells = L.frontier_cells()
            if not cells:
                return True     # fully explored + never-melee around: clear it
            goals = set(cells)
        path_avoiding = L.bfs(A.agent, goals,
                              avoid=self._suspects() | {m.pos})
        return path_avoiding is None    # no route without its cell = blocker

    def _blocks_path(self, m):
        # immobile monster attacked only if it sits on our next planned cell
        tgt = self._current_goal_cell()
        if tgt is None:
            return False
        L = self.atlas.level
        path = L.bfs(self.atlas.agent, [tgt],
                     avoid=self._suspects() | {mm.pos for mm in L.monsters
                                               if mm.pos != m.pos})
        if not path:
            return True
        dx, dy = DIRS[path[0]]
        nxt = (self.atlas.agent[0] + dx, self.atlas.agent[1] + dy)
        return nxt == m.pos

    def _current_goal_cell(self):
        L = self.atlas.level
        goals = list(L.stairs_down | L.holes)
        if goals:
            return goals[0]
        if self.explore_target:
            return self.explore_target
        return None

    # ------------------------------------------------------------- descent
    _REST_LO = float(_os.environ.get("NH_REST_LO", "0.6"))
    _REST_HI = float(_os.environ.get("NH_REST_HI", "0.85"))
    _REST_SLO = float(_os.environ.get("NH_REST_SLO", "0.75"))
    _REST_SHI = float(_os.environ.get("NH_REST_SHI", "0.92"))
    _REST_SDEPTH = int(_os.environ.get("NH_REST_SDEPTH", "3"))

    def _rest_threshold(self):
        A = self.atlas
        lo, hi = self._REST_LO, self._REST_HI
        # V1.1 L4 — shallow rest discipline: the 2000-block's early deaths
        # (13/25 episodes at depth 2-6, xp 1-2) went in at part health;
        # shallow floors are the cheapest place to buy HP
        if A.depth <= self._REST_SDEPTH:
            lo, hi = self._REST_SLO, self._REST_SHI
        if self._mem_danger_depth is not None and \
                A.depth >= self._mem_danger_depth - 1:
            if (lo, hi) != (0.9, 0.95) and A.hp < 0.9 * A.hpmax:
                self._fire(f"M2 rest gate tightened at depth {A.depth} "
                           f"(remembered danger depth {self._mem_danger_depth})")
            lo, hi = 0.9, 0.95
        return lo, hi

    def _should_rest(self):
        A = self.atlas
        lo, hi = self._rest_threshold()
        key = A.key
        used = self.rest_budget.get(key, 0)
        cap = 800 if (self._mem_danger_depth is not None and
                      A.depth >= self._mem_danger_depth - 1) else 400
        if used >= cap:
            return False
        if A.hp >= hi * A.hpmax:
            return False
        if A.hp > lo * A.hpmax and used > 0:
            return True    # continue an ongoing rest up to hi
        return A.hp <= lo * A.hpmax

    def _rest_here_ok(self):
        # rest only when no mobile hostile is visible
        return not self._mobile_hostiles() and self.atlas.hunger < C.WEAK

    def _pace_gate(self):
        """XP pacing experiment — DISABLED after dev A/B: seed 102's
        Archeologist died grinding at depth 7 (0.048) where the ungated
        dig-dive reached depth 10 (0.126); observed non-digger deaths all
        happened at depth < xplvl+6, so the gate never fires for them.
        Depth-before-death favors continuous descent; kept for the record
        and for the memory condition to re-enable selectively (M2)."""
        return None
        A = self.atlas
        if A.depth < A.xplvl + 6:
            return None
        if A.hunger >= C.HUNGRY:
            return None
        start = self.grind_start.setdefault(A.key, A.time)
        if A.time - start > 700:
            return None
        if A.key not in self.grind_note:
            self.grind_note.add(A.key)
            self.note(f"pace gate: grinding at depth {A.depth} "
                      f"(xplvl {A.xplvl})")
        L = A.level
        # hunt the nearest beatable mobile hostile
        prey = [m for m in self._mobile_hostiles()
                if m.difficulty <= A.xplvl + 1 and not self._never_melee(m)]
        if prey and A.hp > 0.55 * A.hpmax:
            tgt = min(prey, key=lambda m: max(abs(m.x - A.agent[0]),
                                              abs(m.y - A.agent[1])))
            path = L.bfs(A.agent, [tgt.pos],
                         avoid=self._suspects() | (self._mcells() - {tgt.pos}))
            if path:
                return self._step_path(path)
        # otherwise rest/wait for spawns (search also reveals hidden ways)
        return "search"

    def _descend(self, obs):
        A = self.atlas
        L = A.level

        act = self._pace_gate()
        if act:
            return act

        # dig straight down if we hold a digger and the spot allows it
        digger = self._find_digger(obs)
        self.digger_letter = digger
        # digging with a mobile hostile nearby donates free attacks: clear
        # the area first (hunt it down), then dig. Only CATCHABLE threats
        # are worth hunting — chasing a speed-22 bat around the level got
        # the condition-A run-1 digger killed; fast flitters are left to
        # the adjacency combat layer while digging continues.
        near_threats = [
            m for m in self._mobile_hostiles()
            if max(abs(m.x - A.agent[0]), abs(m.y - A.agent[1])) <= 3
            and 6 <= m.speed <= OUR_SPEED and not self._never_melee(m)]
        threat_near = bool(near_threats)
        if digger and not threat_near and not L.undiggable and \
                (A.key, A.agent) not in self.no_dig_cells and \
                L.terrain[A.agent[1]][A.agent[0]] not in (
                    C.STAIRS_DOWN, C.STAIRS_UP, C.ALTAR, C.FOUNTAIN,
                    C.THRONE, C.SINK):
            if self._should_rest() and self._rest_here_ok():
                self.rest_budget[A.key] = self.rest_budget.get(A.key, 0) + 1
                return "search"
            att = self.dig_attempts.get(A.key, 0)
            if att < 40:
                self.dig_attempts[A.key] = att + 1
                self.queue = [digger, "down"]
                self.queue_tag = "dig"
                self.digging = True
                if att == 0:
                    self.note(f"digging down at {A.agent} depth {A.depth}")
                self._goal("dig", f"depth {A.depth}")
                return "apply"
        elif digger and threat_near and not L.undiggable:
            # close and kill the interloper so the dig can proceed
            tgt = min(near_threats,
                      key=lambda m: max(abs(m.x - A.agent[0]),
                                        abs(m.y - A.agent[1])))
            path = L.bfs(A.agent, [tgt.pos],
                         avoid=self._suspects() |
                         (self._mcells() - {tgt.pos}))
            if path:
                return self._step_path(path)
            return "search"            # unreachable: let it come, pass time
        elif digger and (A.key, A.agent) in self.no_dig_cells:
            # try a nearby diggable floor cell
            tries = sum(1 for (k, c) in self.no_dig_cells if k == A.key)
            if tries < 4:
                for name, (nx, ny) in L.neighbors(*A.agent,
                                                  avoid=self._suspects()):
                    if L.terrain[ny][nx] in (C.FLOOR, C.CORRIDOR) and \
                            (A.key, (nx, ny)) not in self.no_dig_cells:
                        return name
            else:
                L.undiggable = True
                self.note(f"level {A.key} marked undiggable")

        # role-conditional pacing (Campaign 2): fragile roles clear the
        # local prey before diving deeper than their xp supports
        if C2_PACE:
            act = self._c2_pace(obs, digger)
            if act:
                return act

        # Mines policy (condition A run 1: 3/5 episodes erased by early-
        # Mines dwarves at xplvl 1-2): while weak, back out of the Mines'
        # top levels and use the main-branch '>' on the fork level instead;
        # give up avoiding after 800 fruitless turns (starving is worse).
        if A.dnum == 2 and A.xplvl <= 3 and A.dlevel <= 2 and not digger \
                and not self.commit_mines:
            up = set(L.stairs_up)
            if A.agent in up:
                self.note(f"Mines retreat: going up (xplvl {A.xplvl})")
                return "up"
            if up:
                p = L.bfs(A.agent, up,
                          avoid=self._suspects() | (self._mcells() - up))
                if p is None:
                    p = L.bfs(A.agent, up, avoid=self._suspects())
                if p:
                    return self._step_path(p)

        goals = set(L.stairs_down) | set(L.holes)
        banned = self.mines_entrances.get(A.key, set())
        if banned and A.xplvl <= 3:
            since = self.mines_avoid_since.setdefault(A.key, A.time)
            if A.time - since < 800:
                if goals - banned:
                    goals = goals - banned
                elif goals:
                    # only the Mines '>' is known: keep exploring for the
                    # main-branch one instead of re-entering
                    goals = set()
            else:
                if not self.commit_mines:
                    self.commit_mines = True
                    self.note("Mines avoidance timed out: committing to Mines")
        if not goals:
            return None
        avoid = self._travel_avoid(goals)
        path = L.bfs(A.agent, goals, avoid=avoid)
        if path is None:
            path = L.bfs(A.agent, goals, avoid=self._suspects())
        if path is None:
            path = L.bfs(A.agent, goals, avoid=self._suspects(),
                         bad_traps_ok=True)
        if path == []:
            # standing on the goal
            if self._should_rest() and self._rest_here_ok():
                self.rest_budget[A.key] = self.rest_budget.get(A.key, 0) + 1
                self._goal("rest", f"hp {A.hp}/{A.hpmax} on stairs")
                return "search"
            self.descended_from = (A.key, A.agent)
            self._goal("descend", f"take > at depth {A.depth}")
            return "down"
        if path:
            self._goal("descend", f"to > at depth {A.depth}")
            return self._step_path(path)
        return None

    # ------------------------------------------------- digger acquisition
    def _acquire_digger(self, obs):
        A = self.atlas
        if self.digger_letter:
            return None
        msg = A.message
        m = RE_SEE_HERE.search(msg)
        if m and ("pick-axe" in m.group(1) or "mattock" in m.group(1)):
            self.note(f"picking up digger: {m.group(1)}")
            self.queue_tag = "pickup"
            return "pickup"
        # spot digger object glyphs on the map and detour if close
        glyphs = obs["obs"]["glyphs"]
        best = None
        ax, ay = A.agent
        import numpy as _np
        ga = _np.asarray(glyphs)
        for g in DIGGER_GLYPHS:
            ys, xs = _np.nonzero(ga == g)
            for y, x in zip(ys.tolist(), xs.tolist()):
                d = max(abs(x - ax), abs(y - ay))
                if d <= 20 and (best is None or d < best[0]):
                    best = (d, (x, y))
        if best:
            if best[1] == A.agent:
                self.queue_tag = "pickup"
                return "pickup"
            path = A.level.bfs(A.agent, [best[1]],
                               avoid=self._suspects() | self._mcells())
            if path:
                if len(path) == 1:
                    self.note(f"digger spotted at {best[1]}: stepping on")
                return self._step_path(path)
        return None

    # ------------------------------------------------------------- explore
    def _explore(self, obs):
        A = self.atlas
        L = A.level
        frontier = L.frontier_cells()
        if not frontier:
            return None
        self._goal("explore", f"{len(frontier)} frontier cells")
        fset = set(frontier)
        mcells = self._mcells()
        avoid = self._travel_avoid()
        path = None
        if self.explore_target in fset:
            path = L.bfs(A.agent, [self.explore_target], avoid=avoid)
        if not path:
            tgt = self._pick_frontier(L, fset, avoid)
            if tgt is not None:
                path = L.bfs(A.agent, [tgt], avoid=avoid)
                self.explore_target = tgt
            if not path:
                path = L.bfs(A.agent, frontier, avoid=avoid)
        if path is None:
            path = L.bfs(A.agent, frontier, avoid=self._suspects())
        if path:
            return self._step_path(path)
        if path == []:
            # on a frontier cell: any passable step into the unknown
            for name, (dx, dy) in DIRS.items():
                nx, ny = A.agent[0] + dx, A.agent[1] + dy
                if not (0 <= nx < C.COLS and 0 <= ny < C.ROWS):
                    continue
                if (nx, ny) in self._suspects() or (nx, ny) in mcells:
                    continue
                if not L.explored[ny][nx]:
                    if name in CARDINALS:
                        return name
            for name, (dx, dy) in DIRS.items():
                nx, ny = A.agent[0] + dx, A.agent[1] + dy
                if 0 <= nx < C.COLS and 0 <= ny < C.ROWS and \
                        not L.explored[ny][nx] and \
                        (nx, ny) not in self._suspects():
                    return name
        return None

    def _pick_frontier(self, L, fset, avoid):
        from collections import deque
        dist = {self.atlas.agent: 0}
        q = deque([self.atlas.agent])
        while q:
            cur = q.popleft()
            for _n, nxt in L.neighbors(*cur, avoid=avoid):
                if nxt not in dist:
                    dist[nxt] = dist[cur] + 1
                    q.append(nxt)
        best = None
        for cell in fset:
            if cell not in dist:
                continue
            x, y = cell
            mass = 0
            for yy in range(max(0, y - 3), min(C.ROWS, y + 4)):
                for xx in range(max(0, x - 3), min(C.COLS, x + 4)):
                    if not L.explored[yy][xx]:
                        mass += 1
            score = dist[cell] - 0.55 * mass
            if best is None or score < best[0]:
                best = (score, cell)
        return best[1] if best else None

    # --------------------------------------------------------------- doors
    def _doors(self, obs):
        A = self.atlas
        L = A.level
        doors = [d for d in L.find_terrain(C.DOOR_CLOSED)
                 if d not in self.door_giveup]
        if not doors:
            return None
        mcells = self._mcells()
        # adjacent (cardinal) closed door? open / kick it
        for door in doors:
            ddx, ddy = door[0] - A.agent[0], door[1] - A.agent[1]
            if (ddx, ddy) in DIR_OF and (ddx == 0 or ddy == 0):
                dname = DIR_OF[(ddx, ddy)]
                self.door_target = door
                if "This door is locked" in A.message or self.kick_dir == dname:
                    self.kick_dir = dname
                    self.kick_count += 1
                    if self.kick_count > 12:
                        self.door_giveup.add(door)
                        self.kick_dir = None
                        self.kick_count = 0
                        self.note(f"giving up on locked door {door}")
                        return None
                    self.queue = [dname]
                    self.queue_tag = "kick"
                    return "kick"
                self.queue = [dname]
                self.queue_tag = "open"
                return "open"
        # walk cardinal-adjacent to the nearest closed door
        targets = set()
        for (dx_, dy_) in doors:
            for name in CARDINALS:
                ddx, ddy = DIRS[name]
                ax2, ay2 = dx_ - ddx, dy_ - ddy
                if L.passable(ax2, ay2, doors_ok=False):
                    targets.add((ax2, ay2))
        if targets:
            path = L.bfs(A.agent, targets, avoid=self._suspects() | mcells,
                         doors_ok=False)
            if path:
                return self._step_path(path)
        return None

    # ------------------------------------------------------ hidden search
    def _hidden_search(self, obs):
        A = self.atlas
        L = A.level
        self._goal("find-stairs", "hidden-passage search")
        counts = L.search_counts
        topo_hosts = self._topo().search_hosts(L) if C2_TOPO else None
        cands = []
        for y in range(C.ROWS):
            for x in range(C.COLS):
                if not L.passable(x, y):
                    continue
                pot = 0
                for yy in range(max(0, y - 2), min(C.ROWS, y + 3)):
                    for xx in range(max(0, x - 2), min(C.COLS, x + 3)):
                        if not L.explored[yy][xx]:
                            pot += 1
                # dead-end bonus: hidden corridors continue from dead ends
                deg = sum(1 for _ in L.neighbors(x, y))
                # secret doors live in ROOM WALLS: any cell cardinal-adjacent
                # to a real (non-inferred) wall is a candidate host (dev seed
                # 103: 19.5k searches at dead ends only, secret door in a
                # room wall never probed)
                wall_adj = 0
                for name in CARDINALS:
                    ddx, ddy = DIRS[name]
                    nx2, ny2 = x + ddx, y + ddy
                    if 0 <= nx2 < C.COLS and 0 <= ny2 < C.ROWS and \
                            L.terrain[ny2][nx2] == C.WALL and \
                            not L.inferred_wall[ny2][nx2]:
                        wall_adj += 1
                host_bonus = 3 if (topo_hosts is not None and
                                   ((x, y) in topo_hosts or any(
                                       (x + dx, y + dy) in topo_hosts
                                       for dx, dy in ((1, 0), (-1, 0),
                                                      (0, 1), (0, -1))))) \
                    else 0
                if pot > 0 or deg <= 1 or wall_adj > 0 or host_bonus:
                    rounds = counts.get((x, y), 0) // 6
                    cands.append((rounds,
                                  -(pot + (4 if deg <= 1 else 0) + wall_adj
                                    + host_bonus),
                                  abs(x - A.agent[0]) + abs(y - A.agent[1]),
                                  (x, y)))
        if cands:
            cands.sort()
            # walk the ranking until a REACHABLE candidate (a never-melee
            # blocker can make the top pick unreachable forever — dev 116)
            for _r, _p, _d, tgt in cands[:60]:
                if tgt == A.agent:
                    counts[tgt] = counts.get(tgt, 0) + 1
                    return "search"
                path = L.bfs(A.agent, [tgt], avoid=self._mcells())
                if path:
                    return self._step_path(path)
        counts[A.agent] = counts.get(A.agent, 0) + 1
        return "search"

    # ---------------------------------------------------------- path steps
    def _step_path(self, path):
        A = self.atlas
        L = A.level
        self._log_plan(path)
        step = path[0]
        dx, dy = DIRS[step]
        nx, ny = A.agent[0] + dx, A.agent[1] + dy
        # closed door ahead: open instead of bumping
        if L.terrain[ny][nx] == C.DOOR_CLOSED:
            if dx == 0 or dy == 0:
                self.door_target = (nx, ny)
                if "This door is locked" in A.message or self.kick_dir == step:
                    self.kick_dir = step
                    self.kick_count += 1
                    if self.kick_count > 12:
                        self.door_giveup.add((nx, ny))
                        self.suspect_walls.setdefault(A.key, set()).add((nx, ny))
                        self.kick_dir = None
                        self.kick_count = 0
                        return "search"
                    self.queue = [step]
                    self.queue_tag = "kick"
                    return "kick"
                self.queue = [step]
                self.queue_tag = "open"
                return "open"
            return "search"
        # monster on the next cell
        for m in L.monsters:
            if m.pos == (nx, ny):
                if m.pet:
                    return step            # swap places with pet
                if m.pos in L.no_attack:
                    return self._detour(path, (nx, ny))
                if self._never_melee(m):
                    return self._detour(path, (nx, ny))
                return step                # attack by moving in
        return step

    def _detour(self, path, cell):
        A = self.atlas
        L = A.level
        # rebuild path avoiding this cell; fall back to waiting
        tgt = self._path_end(path)
        p = L.bfs(A.agent, [tgt], avoid=self._suspects() | {cell})
        if p:
            return p[0] if p[0] != path[0] else p[0]
        return "search"

    def _path_end(self, path):
        x, y = self.atlas.agent
        for stp in path:
            dx, dy = DIRS[stp]
            x, y = x + dx, y + dy
        return (x, y)

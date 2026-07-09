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

import json
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
C2_CASTHUNGER = _flag("NH_CASTHUNGER")  # Phase L: cast-refusal latch (V1a)
C2_ANTIFAINT = _flag("NH_ANTIFAINT")  # Phase L s9: eat-at-HUNGRY anti-faint guard
C2_PRAYHUNGER = _flag("NH_PRAYHUNGER")  # E39: emergency prayer fires on HUNGER
# crisis (Weak/Fainting), not only HP<=6. Diagnosis: 0/64 long starve-loop
# deaths ever prayed because the last-resort prayer trigger only checked HP.
# Prayer while Weak/Fainting from hunger => god feeds you (standard NetHack
# starvation rescue). Refactors emergency-prayer from an HP-only guard into a
# crisis-concern that BOTH hp-crisis and hunger-crisis feed (additive concern).
C2_FOODACQ = _flag("NH_FOODACQ")  # Phase L s11: proactive safe-corpse banking
C2_PET = _flag("NH_PET")          # Phase L s12: pet utilization (preserve-on-descent)
C2_WIELD = _flag("NH_WIELD")      # Phase L s13: wield best-in-inventory weapon (direct combat-capability injection)
C2_WIELDACQ = _flag("NH_WIELDACQ")  # Phase L s13: ACQUIRE a floor weapon that upgrades melee, then wield it
C2_LOOT = _flag("NH_LOOT")          # Phase L s15: EFFICIENT looting — value floor weapons(dpt)+armor(AC), grab IFF value/detour clears threshold under a per-LEVEL detour budget, then wield/wear
C2_CONSUME = _flag("NH_CONSUME")  # NH-E38: CONSUMABLE ECONOMY — engrave-ID wands
#   (low-risk, deterministic) + zap KNOWN offensive/control wand at a tough/
#   same-speed/fast threat (the spike-death counter: ends the unfleeable 1-shot
#   fight AND yields zero-exchange safe XP via sleep/striking), + quaff KNOWN
#   healing at HP-crisis, + quaff/read KNOWN gain-level (direct safe XP) +
#   enchant/identify when safe. Default OFF => bit-identical. See docs/
#   NH_ID_GAME_SCOPE.md. Aliased NH_IDGAME.
if not C2_CONSUME:
    C2_CONSUME = _flag("NH_IDGAME")
C2_SAFELEVEL = _flag("NH_SAFELEVEL")  # Phase L s16: SAFE EARLY LEVELING — on D1-3, before diving, route to an ISOLATED SAFE weak monster to farm XP so we arrive at the D5-6 kill-zone stronger (the bootstrap-breaker: XP = the other unused capability)
C2_CASTHUNGER_EAT = _flag("NH_CASTHUNGER_EAT")  # V1b eat-early: DROPPED
#   after CASTHUNGER-1 (clearly negative; kept behind sub-flag for the lab)
#   (guard-class only; lets the guards ride even on an otherwise-v1.1
#    configuration)
# NH-E13 FLOOR-ROLE UPLIFT (session 6, claude-opus-4-8[1m] max thinking):
# the WIKI-FED flagship — read the role at episode start and apply the
# role's provenance:wiki playbook (DOCTRINE_CARDS_s5.md). HEALER first
# (freq x headroom max): cast-heal-to-survive (SUSTAIN — a capability we
# have NEVER used) + pacifist/avoid-melee (no proactive grind, disengage
# early). Master flag NH_ROLE_PROFILE, default OFF => byte-identical when
# unset (flag-off regression gate). Every profile branch is guarded on
# C2_ROLE_PROFILE and the detected role, so non-target roles are untouched.
# Proximal KPI = target-role mean + survival@D5 (KPI_TREE.md); wiki-
# attributable delta reported explicitly.
C2_ROLE_PROFILE = _flag("NH_ROLE_PROFILE")
HEAL_HP_FRAC = float(_os.environ.get("NH_HEAL_HP", "0.55"))  # heal below this
# s7 refinement (fix the WHEN): heal in a MIDDLE HP band [LO,HI] UNDER THREAT.
# s6 found crisis-heal fires too late (~hp 4/21 -> heal-a-sliver-and-die) and
# proactive no-threat top-up perturbs good runs. The band's LO floor drops the
# too-late crisis heal; requiring an adjacent threat drops the harmful proactive
# top-up. HI == HEAL_HP_FRAC. Env-tunable: NH_HEAL_HP_LO / NH_HEAL_HP.
HEAL_HP_LO = float(_os.environ.get("NH_HEAL_HP_LO", "0.30"))  # too-late floor
# s7 kick-cost gate: kicking a locked door can break a leg -> slow -> death,
# worst at low HP and for fragile/low-HD roles. Gate the kick on HP/role and
# defer the door instead. Flag-off (default) == bit-identical (no kick change).
C2_KICK_GATE = _flag("NH_KICK_GATE")
# s7 HEADLINE: declarative survival rule base (nh_rulebase.py). Flag ON routes
# the four migrated guard predicates (NEVER_MELEE / TOUCH_KILL / PRAYFIX / HEAL
# band) through the base (behavior-preserving: rule conditions are exact ports).
# Flag OFF -> base never consulted, bit-identical to the s6 baseline.
C2_RULEBASE = _flag("NH_RULEBASE")
# NH-READY_GATE — role-conditioned READINESS gate before descending (Phase L
# session 8, claude-opus-4-8[max]). Diagnosis (NH-E12 backfill): 59% of combat
# deaths are ARRIVAL_CONSTRAINT (under-prepared arrival), agents descend at ~35%
# HP into a rising-threat floor (KPI death-shape). XP-grinding is INVALIDATED
# (PRIORS) and the s4 XP-pace-gate hurt diggers, so the ONLY realizable
# pre-descent prep is HP buffer. This gate is threat-conditional REST DEPTH: for
# a FRAGILE role (DIGGER-EXEMPT) about to take the '>' into a floor whose
# empirical threat band leaves readiness-ratio(d+1) below a per-role threshold,
# rest to fuller HP than the default rest gate — buy arrival buffer ONLY for
# dangerous descents. When RR(d+1) >= thresh (we are ready), the gate is inert.
# Bounded by the rest budget (never stalls to starvation). Default OFF =>
# bit-identical (flag-off regression). Proximal KPI = survival@D-next
# (KPI_TREE.md), not local. Role-conditional (validated role-stratified).
C2_READY_GATE = _flag("NH_READY_GATE")
READY_RR_THRESH = float(_os.environ.get("NH_READY_RR", "1.0"))    # RR(d+1) floor
READY_HP_TARGET = float(_os.environ.get("NH_READY_HP", "0.92"))   # rest-to frac
READY_GATE_ROLES = set(filter(None, _os.environ.get(
    "NH_READY_ROLES",
    "Tourist,Healer,Wizard,Priest,Priestess,Rogue").split(",")))
# NH-ADVISORY — the ADVISORY-PUSH / LLM-strategist consult (Phase L session 8,
# claude-opus-4-8[max]) — the never-run test of the intuition thesis on REAL
# NetHack (all prior intuition results are composition-worlds). At LOW-frequency
# STRATEGIC triggers (level-entry / impasse / novelty / low-HP crisis) the agent
# consults a live LLM strategist with the CONTEXT_SPEC package (map + memory +
# story) PLUS the rule base's pushed ADVISORY reminders (RB.reminders_text) and
# receives a structured strategy choice the code then executes (biases the
# decision cascade). Consults are capped/episode + min-spaced (cost) and logged
# VERBATIM. Requires NH_STORE + NH_RULEBASE (the context + reminder sources).
# Default OFF => bit-identical (flag-off regression). This is the Phase-E gate:
# does live intuition + the rule base beat pure compiled code on real NetHack?
C2_ADVISORY = _flag("NH_ADVISORY")
ADVISORY_MAX = int(_os.environ.get("NH_ADVISORY_MAX", "6"))       # consults/ep
ADVISORY_GAP = int(_os.environ.get("NH_ADVISORY_GAP", "40"))      # min env steps
ADVISORY_MODEL = _os.environ.get("NH_ADVISORY_MODEL", "")         # "" = default
ADVISORY_MINDEPTH = int(_os.environ.get("NH_ADVISORY_MINDEPTH", "2"))
KICK_MIN_HP = float(_os.environ.get("NH_KICK_MIN_HP", "0.5"))  # skip kick below
KICK_FRAGILE_ROLES = set(filter(None, _os.environ.get(
    "NH_KICK_FRAGILE", "Tourist,Wizard,Archeologist").split(",")))
PACE_DEPTH = int(_os.environ.get("NH_PACE_DEPTH", "3"))
PACE_XP_STEP = float(_os.environ.get("NH_PACE_XPSTEP", "2"))
PACE_BUDGET = int(_os.environ.get("NH_PACE_BUDGET", "900"))
C2_ANY = any((C2_EXPMAX, C2_RANGED, C2_ARMOR, C2_FOOD2, C2_PRAYFIX, C2_LOS,
              C2_THREAT, C2_TOPO, C2_PACE, C2_ELBERETH, C2_GUARD, C2_CAST,
              C2_E15, C2_REPEAT, C2_CASTHUNGER, C2_ROLE_PROFILE, C2_KICK_GATE,
              C2_RULEBASE, C2_READY_GATE, C2_ADVISORY, C2_ANTIFAINT,
              C2_FOODACQ, C2_PET, C2_WIELD, C2_WIELDACQ, C2_LOOT,
              C2_SAFELEVEL, C2_CONSUME))
if C2_RULEBASE:
    import nh_rulebase as _RB_MOD
    RULEBASE = _RB_MOD.build_default_base()
else:
    RULEBASE = None
WD_WINDOW = int(_os.environ.get("NH_WD_WINDOW", "150"))   # game turns
WD_DISENGAGE = int(_os.environ.get("NH_WD_DISENGAGE", "80"))  # env steps
# NH-E6 REST/disengage lever (session 4, claude-opus-4-8[1m] max thinking):
# the crisis-disengage HP fraction and the "die within N exchanges" predictor
# were hardcoded (0.28 / 2.0) at the P3 crisis gate. The e6_solve TRASH
# backtest (REST/disengage survives 10/20 TRASH deaths, wins at 40-step
# backoffs) + the DEV death-shape KPI (agents die at ~35% HP, ABOVE the 0.28
# flee floor -> lost in the 35->28% window while still trading blows) both
# say: break contact earlier. These knobs default to the PRIOR CONSTANTS, so
# unset == bit-identical behavior (flag-off regression gate). Proximal KPI:
# survival-to-depth via TRASH-death rate (see KPI_TREE.md). Paired-block gate.
CRISIS_HP = float(_os.environ.get("NH_CRISIS_HP", "0.28"))    # flee below hp-frac
CRISIS_EXCH = float(_os.environ.get("NH_CRISIS_EXCH", "2.0"))  # flee if maxhit*x>=hp
FOODACQ_COOLDOWN = int(_os.environ.get("NH_FOODACQ_COOLDOWN", "8"))  # s11 bank rate
# ^ cd=8 is the RECONCILED value (s11): moderate banking that removes the hunger
# death-class (death-while-fainting 5/15->0/15, progression-neutral) without the
# descent-stall that cd=0/routing caused (dev depth 15->1). cd=25 fired too little
# (hunger effect null). See DOCTRINE_CARDS_s11.md CARD S11-1.
# PET UTILIZATION (NH_PET, Phase L s12): before taking the down-stairs, wait a
# BOUNDED number of turns for the starting pet to reach an adjacent cell so it
# FOLLOWS us down (a pet descends only if adjacent when '>' is taken). Preserves
# the pet across the descent so it keeps tanking/killing the D2-6 trash that is
# the newly-unmasked combat death-class (s11: FOODACQ converted hunger-deaths
# into combat-deaths at the same depth). PET_WAIT_MAX caps per-stair dawdling so
# a far/stuck pet can't stall descent (the FOODACQ-stall lesson, CARD S11-2);
# PET_WAIT_RADIUS = only wait if the pet is close enough to plausibly catch up.
PET_WAIT_MAX = int(_os.environ.get("NH_PET_WAIT_MAX", "8"))     # turns per stair
PET_WAIT_RADIUS = int(_os.environ.get("NH_PET_WAIT_RADIUS", "5"))  # only wait if <=
# WIELD UPGRADE (NH_WIELD, Phase L s13): the CAPABILITY-side combat lever the s12
# PET null points to (presence side inert -> try the capability side). Before a
# non-crisis turn, if a carried (not-wielded) NON-thrown weapon beats the current
# wielded (or unarmed) melee dpt by WIELD_MARGIN and it is safe (no adjacent
# hostile -> we won't be caught mid-swap weaponless), wield it. Thrown-primary
# weapons (darts/daggers used for ranged) are EXCLUDED so we don't disarm the
# ranged game. Monk excluded (martial arts > any early weapon). dpt from the
# nh_sheet character sheet (counterfactual_power / attack_options). Zero wield
# actions have EVER been taken in program history -> cleanest direct combat-
# capability injection. Ships DEFAULT-OFF, bit-identical when off.
WIELD_MARGIN = float(_os.environ.get("NH_WIELD_MARGIN", "0.5"))  # min dpt gain to swap
# NH_WIELD_DIAG (s13): READ-ONLY diagnosis of WHY wield never fires. Distinguishes
# (a) acquisition-bound [a better weapon is ON THE FLOOR but the agent has no
# floor-weapon perception / never loots it] from (c) already-optimal [no better
# weapon exists anywhere]. Scans visible glyphs for WEAPON_CLASS objects, prices
# them via the character sheet, and tracks the best floor-weapon dpt seen vs the
# current wielded dpt. Pure observation -> emits notes only, never an action, so
# arms stay bit-identical.
WIELD_DIAG = _os.environ.get("NH_WIELD_DIAG") == "1"
# NH_WIELDACQ (s13 PIVOT): the diagnosis showed wield never fires because weak-
# weapon roles (Healer scalpel, Tourist) walk PAST a better weapon on the floor
# (seed 746 Healer: a mace, dpt +1.44, in view 25+ steps, never taken) — the
# agent has the wield mechanism but no LOOT behavior. This is the acquisition-
# bound meta-finding (the exact parallel to the anti-faint "no food to eat"
# null). NH_WIELDACQ closes the loop: detour up to WIELDACQ_RADIUS to a floor
# weapon that beats the current melee dpt by WIELD_MARGIN, pick it up (then the
# NH_WIELD lever wields it). Bounded detour + loot_tries cap = the FOODACQ
# no-stall discipline (CARD S11-2). Ammo/thrown-primary excluded (melee only).
WIELDACQ_RADIUS = int(_os.environ.get("NH_WIELDACQ_RADIUS", "8"))  # max detour steps
# EFFICIENT LOOTING (NH_LOOT, Phase L s15) — the ACQUISITION-BOUND meta-finding
# (s13, PROGRAM_FINDINGS 11th angle) turned into a lever. The agent has USE
# mechanisms (wield/wear/eat) but no ACQUIRE behaviour, so real combat capability
# sits UNLOOTED on the floor (seed 746 Healer walked past a +1.44-dpt mace for 25
# steps; 4054 Ranger past a flail 100 steps; 721 Knight past a two-handed sword).
# NH_LOOT values every floor WEAPON (melee dpt gain vs current wield) and ARMOR
# (AC bonus for an unfilled slot) and grabs the best one IFF value/detour_cost
# clears LOOT_EFF_THRESH — so high-value gear (a two-handed sword) justifies a
# longer detour and junk never does — all under a per-LEVEL total detour budget
# (LOOT_LEVEL_BUDGET) so descent NEVER stalls (the confound that nulled the s13
# WIELDACQ pivot: DEATH@D5 -> TRUNCATED@2000). Underfoot/adjacent grabs are free
# (always taken). The NH_WIELD (wield) + NH_ARMOR (wear) USE levers then fire on
# what was looted — the whole point. SCOPE: weapons+armor only. Floor potions/
# scrolls are UNIDENTIFIED (can't value healing/enchant pre-ID) and hoarding them
# risks burden -> descent-stall, so they are deliberately out of scope; gold
# auto-collects on step (no detour needed). Default OFF => bit-identical.
LOOT_EFF_THRESH = float(_os.environ.get("NH_LOOT_EFF", "0.12"))    # min value per detour-step for a FAR grab
LOOT_MAX_DETOUR = int(_os.environ.get("NH_LOOT_DETOUR", "12"))     # per-item detour cap (steps)
LOOT_LEVEL_BUDGET = int(_os.environ.get("NH_LOOT_BUDGET", "30"))   # max total loot-detour steps per dungeon level
LOOT_AC_WEIGHT = float(_os.environ.get("NH_LOOT_AC_W", "0.4"))     # armor value = ac_bonus * this (dpt-comparable units)
# SAFE EARLY LEVELING (NH_SAFELEVEL, Phase L s16) — the bootstrap-breaker.
SAFELEVEL_MAXDEPTH = int(_os.environ.get("NH_SAFELEVEL_MAXDEPTH", "3"))   # only farm XP on D1..this
SAFELEVEL_TARGET_XP = int(_os.environ.get("NH_SAFELEVEL_XP", "5"))        # hunt until xplvl>=this, then dive
SAFELEVEL_BUDGET = int(_os.environ.get("NH_SAFELEVEL_BUDGET", "200"))     # max safe-level hunt STEPS per dungeon level (turn cap)
SAFELEVEL_HP_FRAC = float(_os.environ.get("NH_SAFELEVEL_HP", "0.8"))      # only pick a fight when HP >= this*hpmax
SAFELEVEL_MARGIN = float(_os.environ.get("NH_SAFELEVEL_MARGIN", "0.25"))  # engage IFF expected HP-loss (dpt*ttk) <= this*hp
SAFELEVEL_MAX_DPT = float(_os.environ.get("NH_SAFELEVEL_MAXDPT", "2.0"))  # never engage a monster whose per-turn dpt exceeds this
SAFELEVEL_RADIUS = int(_os.environ.get("NH_SAFELEVEL_RADIUS", "8"))       # max path length to route to prey
SAFELEVEL_ISO_R = int(_os.environ.get("NH_SAFELEVEL_ISO", "3"))           # prey must have no OTHER hostile within this radius
# NH-E6 THROW-DISENGAGE lever (session 5, claude-opus-4-8[1m] max thinking):
# the s4 REST-lever paired block DROPPED because the crisis-flee threshold
# tune never reaches the failure mode — fatal TRASH deaths carry a SAME-SPEED
# (or faster) hostile ADJACENT, where _flee returns None (its slower-only +
# full-disengage gates refuse) and the agent falls through to trade blows.
# The e6_solve v2 menu re-adjudicated all 9 s3-UNRESOLVED TRASH deaths as
# MISPLAYED (0 UNWINNABLE) and THROW-DISENGAGE won >=3 on >=3 distinct seeds
# (class-solve rule, criterion ii). This lever fires a ranged throw at the
# nearest in-line hostile in the crisis branch AFTER _flee declines — a NEW
# ACTION (per-exchange ranged disengage), not a threshold tune. Default OFF
# => unset == bit-identical (flag-off regression gate). Proximal KPI:
# survival-to-depth via TRASH-death rate (KPI_TREE.md). Paired-block gate.
CRISIS_THROW = _os.environ.get("NH_CRISIS_THROW", "0") == "1"
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

# NH-E38 CONSUMABLE ECONOMY tables (provenance: knowledge=wiki + NetHack 3.6.7
# src/engrave.c WAND_CLASS switch, OFFLINE+disclosed; verified against local
# wiki_kb.sqlite). Object-class ints: WAND=11, POTION=8, SCROLL=9 (nle.nethack).
WAND_CLASS_INT, POTION_CLASS_INT, SCROLL_CLASS_INT = 11, 8, 9
# ENGRAVE-TEST -> wand identity. Engraving in dust with the wand as the writing
# tool ('E' -> wand-letter) discharges it; the message reveals the class with NO
# zap-effect risk (digging/teleport are SAFE via engraving; only lightning
# self-blinds, fire burns floor-items, create-monster spawns adjacent). We
# pattern-match the distinctive substring (verbatim from source). Value =
# whether the wand is a directional OFFENSIVE/CONTROL wand worth zapping at a
# threat (ends the unfleeable spike fight / free XP).
ENGRAVE_ID_SIGS = [
    ("unsuccessfully fights your attempt to write", "striking"),
    ("bugs on the",           "sleep_or_death"),   # "...stop moving!" (sleep OR death)
    ("ice cubes drop from the wand", "cold"),
    ("Flames fly from the wand",     "fire"),
    ("wand of fire",                 "fire"),
    ("Lightning arcs from the wand", "lightning"),
    ("wand of lightning",            "lightning"),
    ("riddled by bullet holes",      "magic missile"),
    ("wand of digging",              "digging"),
    ("Gravel flies up from the",     "digging"),
    ("slow down",             "slow monster"),
    ("speed up",              "speed monster"),
    ("engraving now reads",   "polymorph"),
    ("vanishes",              "ambiguous"),          # cancel/invis/teleport
]
# directional wands we will ZAP at a hostile (all end/neutralize the fight):
OFFENSIVE_WANDS = {"striking", "sleep_or_death", "sleep", "death", "cold",
                   "fire", "lightning", "magic missile", "cancellation",
                   "slow monster", "polymorph"}
# identity substrings appearing in an ALREADY-IDENTIFIED inventory desc:
HEAL_POTIONS = ("healing", "extra healing", "full healing")
GAINLEVEL_ITEMS = ("gain level",)
ENCHANT_SCROLLS = ("enchant armor", "enchant weapon")
# wands whose ENGRAVE-test carries a real (recoverable) cost -> engrave-test
# these last / only when nothing better (fire burns floor items; lightning
# blinds). Still worth IDing; we just note the cost.
ENGRAVE_RISKY = {"fire", "lightning"}
# NH-E38b REFLECTION GUARD: directional wands whose zap is a BUZZ RAY that
# bounces off walls and can re-enter the zapper's cell (NetHack 3.6.7 zap.c
# `buzz`: AD_MAGM/FIRE/COLD/SLEE/DISN/ELEC rays reflect off stone/walls). In a
# dead-end corridor a reversed ray returns to @ (the seed-4 self-reflected
# "bolt of lightning" death). Striking is a non-ray bolt but we guard it too
# (brief; conservative — over-guarding only costs a corridor zap, never a
# death). Provenance: knowledge=WIKI + src/zap.c buzz(), disclosed.
BOUNCING_RAY_WANDS = {"striking", "sleep_or_death", "sleep", "death", "cold",
                      "fire", "lightning", "magic missile", "cancellation",
                      "slow monster", "polymorph", "speed monster"}
CONSUME_RADIUS = int(_os.environ.get("NH_CONSUME_RADIUS", "10"))     # max detour to a floor consumable
CONSUME_LEVEL_BUDGET = int(_os.environ.get("NH_CONSUME_BUDGET", "25"))  # max detour steps/level (no-stall)
RAY_RANGE = int(_os.environ.get("NH_RAY_RANGE", "13"))  # buzz-ray max travel (rn1(7,7)=7..13; use the max for the guard)

# NH-E38b PRICE-ID reference (base-cost -> candidate identities per object
# class). Provenance: knowledge=WIKI (Price identification) via kb_prices.py
# parse of the NH-E13 wiki KB (results/kb_prices.json), OFFLINE + disclosed.
# A shop-priced unidentified item narrows to table[class][base_cost]; we only
# ACT on an UNAMBIGUOUS single-candidate cost (charisma/BUC price variance
# makes multi-candidate costs unreliable). Shops are floor-scarce on the
# shallow dungeon the dev sample dies in, so this fires rarely by design.
try:
    _PRICE_KB = json.load(open(_os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)), "results",
        "kb_prices.json"))) if _os.path.exists(_os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)), "results",
        "kb_prices.json")) else {}
except Exception:                       # noqa: BLE001 — never a gate
    _PRICE_KB = {}
RE_UNPAID = re.compile(r"\((?:unpaid|for sale)[^)]*?(\d+) zorkmid")

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
        # NH-E38 consumable economy state
        self.wand_belief = {}       # inv-letter -> believed wand type (from engrave-ID)
        self.engrave_tested = set() # inv-letters we have engrave-tested (don't retest)
        self.pending_engrave = None # (letter, steps_remaining) awaiting ID message
        self.zapped_at = {}         # (levelkey, monpos) -> zap count (anti-loop)
        self.consumed_letters = set()  # potion/scroll letters we've used up (one-shot guard)
        self.consume_kills = 0
        self.gainlevel_used = 0
        self.consume_detour = {}    # level key -> detour steps spent (no-stall budget)
        # NH-E38b: read-identify + price-ID (raise the USE fire-rate: turn
        # floor-acquired UNIDENTIFIED potions/scrolls into usable known items)
        # + zap reflection guard (seed-4 self-zap-lightning death class).
        self.item_belief = {}       # inv-letter -> resolved identity substring
                                    #   (price-ID belief for potions/scrolls;
                                    #   real read-ID mutates the desc directly)
        self.identify_in_flight = 0 # step budget while a read-identify's target
                                    #   prompt is being answered
        self.identify_scroll = None # letter of the identify scroll being read
        self._id_selected = False   # a target letter already toggled in a
                                    #   blessed multi-select identify menu
        self.priced_letters = set() # letters already price-ID adjudicated
        self.safelevel_turns = {}               # NH_SAFELEVEL: level key -> steps spent safe-leveling
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
        # ---- Phase L NH-E13 FLOOR-ROLE heal-casting (inert unless
        # C2_ROLE_PROFILE + Healer). Tracked independently of the attack-cast
        # state so a heal-only Healer (no attack spell) still casts. ----
        self.heal_choice = None     # (letter, name, pw_cost) of a heal spell
        self.heal_in_flight = False  # a heal cast issued, menu selection pends
        self.heal_fires = 0
        self.heal_scanned = False   # menu parsed at least once this episode
        # Phase L NH_CASTHUNGER state (tracking always on; behavior gated)
        self.cast_hunger_blocked = False
        self.cast_hunger_events = 0
        self.rest_budget = {}                   # level key -> turns rested
        self.ready_gate_fires = 0               # NH-READY_GATE rest-to-buffer
        self.wield_fires = 0                    # NH_WIELD (s13) upgrade swaps
        self._floor_wpn_max = 0.0               # NH_WIELD_DIAG: best floor-weapon dpt seen
        self._floor_wpn_name = None
        self._floor_upgrade_steps = 0           # steps w/ a floor weapon beating current
        self._cur_wield_dpt_last = 0.0
        self.wieldacq_fires = 0                 # NH_WIELDACQ pickups
        self.loot_fires = 0                     # NH_LOOT (s15) acquisitions (weapon+armor)
        self.loot_wpn_fires = 0                 # NH_LOOT weapon grabs
        self.loot_arm_fires = 0                 # NH_LOOT armor grabs
        self._loot_budget = {}                  # A.key -> loot-detour steps spent this level
        self._loot_target = None                 # (A.key, cell, kind, name, value): sticky loot goal
        self._loot_progress = {}                 # (A.key,cell) -> min dist seen (give up only when STUCK, not while approaching)
        self._pickup_wpn_kw = None              # targeted weapon keyword for pickup menu
        # NH-ADVISORY (LLM-strategist) per-episode state
        self.advisory_consults = 0              # consults issued this episode
        self.advisory_last_step = -10 ** 9      # min-gap throttle
        self.advisory_log = []                  # verbatim consult records
        self.advisory_depth_seen = set()        # level-entry consult de-dupe
        self._adv_descend_until = 0             # DESCEND bias window (env step)
        self._adv_explore_until = 0             # EXPLORE bias window
        self._adv_rest_until = 0                # REST bias window
        self._adv_novel = None                  # novel species seen this step
        self._adv_wd_seen = 0                   # watchdog-fire count consumed
        self._adv_crisis_active = False         # low-HP crisis edge tracker
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
        self._pet_waits = {}                    # (key, stair cell) -> wait count
        self.pet_wait_fires = 0                 # NH_PET: total pet-follow waits
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
                self._adv_novel = m.name        # NH-ADVISORY novelty trigger
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

        # NH-E38: attribute a kill to a recent wand-zap (mechanism metric).
        if C2_CONSUME and getattr(self, "_pending_zap_kill", 0) > 0:
            km = RE_KILLED.search(msg)
            if km:
                self.consume_kills += 1
                self.note(f"CONSUME kill ({km.group(1)}) via zap")
            self._pending_zap_kill -= 1

        # NH-E38: engrave-ID result capture. After an engrave-test we watch the
        # next few messages for the wand-signature; the first match resolves the
        # letter's identity in our belief (self-IDing wands also update the
        # inventory desc directly, caught by _consume_inv).
        if C2_CONSUME and self.pending_engrave is not None:
            pl, win = self.pending_engrave
            for sub, wtype in ENGRAVE_ID_SIGS:
                if sub in msg:
                    self.wand_belief[pl] = wtype
                    self.note(f"ENGRAVE-ID solved {pl}={wtype} ('{sub}')")
                    self.pending_engrave = None
                    break
            else:
                if win <= 1:
                    self.wand_belief.setdefault(pl, "tested_unknown")
                    self.pending_engrave = None
                else:
                    self.pending_engrave = (pl, win - 1)

        # NH-E38b: shop price-ID belief refresh (cheap; adjudicates each unid
        # priced consumable once). Kept ahead of the crisis quaff so a narrowed
        # heal is available when a spike hits.
        if C2_CONSUME:
            self._price_id(obs)

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

    def _rb_state(self, monster_name=None, adj_mobile=None):
        """Served-obs STATE VIEW for a rule-base check (no env internals)."""
        A = self.atlas
        return {"role": self.role, "hp": A.hp, "hpmax": A.hpmax,
                "hunger": A.hunger, "wields_weapon": self._wields_weapon,
                "monster_name": monster_name, "adj_mobile": adj_mobile}

    def _never_melee(self, m):
        # MIGRATED to rule base [NEVER_MELEE] (s7). Flag-off path is the literal
        # s6 predicate; flag-on delegates the membership check (exact port).
        hit = (RULEBASE.check("NEVER_MELEE", self._rb_state(monster_name=m.name))
               if C2_RULEBASE else m.name in C.NEVER_MELEE)
        if hit:
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
        hp_crisis = A.hp <= 6
        hunger_crisis = C2_PRAYHUNGER and A.hunger >= C.WEAK
        if (hp_crisis or hunger_crisis) and self._pray_ok(last_resort=True):
            self.prayed_at = A.time
            self.pray_count += 1
            self.emergency_fired += 1
            why = "hunger" if (hunger_crisis and not hp_crisis) else "hp"
            self._ev(f"VETO: last-resort prayer ({why}; hp {A.hp}/{A.hpmax} "
                     f"hunger {A.hunger})")
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

    # ================= NH-E38 CONSUMABLE ECONOMY ======================
    def _consume_inv(self, obs):
        """Bucket the inventory into usable consumables. A consumable is
        'known' when its true type is already in the desc string (pre-ID'd
        starting item, self-IDing wand, or price/use-ID'd) OR (for wands) when
        our engrave-belief resolved it. Returns dict of letter-lists."""
        out = {"off_wand": [], "heal_pot": [], "gainlevel": [], "enchant": [],
               "identify": [], "unid_wand": []}
        for letter, desc, oc in self._inv(obs):
            d = desc.lower()
            if oc == WAND_CLASS_INT:
                if "(0:" in desc:               # empty wand
                    continue
                m = re.search(r"wand of ([a-z ]+?)(?: \(|$|,)", d)
                wtype = m.group(1).strip() if m else self.wand_belief.get(letter)
                if wtype in OFFENSIVE_WANDS:
                    out["off_wand"].append((letter, wtype))
                elif wtype is None and letter not in self.engrave_tested:
                    out["unid_wand"].append((letter, desc))
            elif oc == POTION_CLASS_INT and letter not in self.consumed_letters:
                # NH-E38b: a price-ID belief augments the game's own desc so a
                # narrowed floor potion becomes usable (real read-ID mutates the
                # desc directly and needs no belief).
                dd = d + " " + self.item_belief.get(letter, "")
                if any(h in dd for h in HEAL_POTIONS) and "wand" not in d:
                    out["heal_pot"].append((letter, dd))
                if any(g in dd for g in GAINLEVEL_ITEMS):
                    out["gainlevel"].append((letter, "quaff"))
            elif oc == SCROLL_CLASS_INT and letter not in self.consumed_letters:
                dd = d + " " + self.item_belief.get(letter, "")
                if any(g in dd for g in GAINLEVEL_ITEMS):
                    out["gainlevel"].append((letter, "read"))
                if any(e in dd for e in ENCHANT_SCROLLS):
                    out["enchant"].append((letter, dd))
                if "identify" in d:
                    out["identify"].append((letter, d))
        return out

    def _is_unid(self, desc, oc):
        """True if a potion/scroll/wand desc shows only its random APPEARANCE
        (floor-acquired, not yet type-known) — the read-identify target set."""
        d = desc.lower()
        if oc == POTION_CLASS_INT:
            return "potion of " not in d
        if oc == SCROLL_CLASS_INT:
            return "scroll of " not in d
        if oc == WAND_CLASS_INT:
            return "wand of " not in d
        return False

    def _unid_consumables(self, obs):
        """Ordered read-identify targets: unidentified potions/scrolls first
        (engrave-ID can't touch them — this is the whole point), unid wands
        last (prefer the free engrave-test for those). Skips items we already
        hold a price-ID belief for and letters we've consumed."""
        pots_scrolls, wands = [], []
        for letter, desc, oc in self._inv(obs):
            if letter in self.consumed_letters or letter in self.item_belief:
                continue
            if oc in (POTION_CLASS_INT, SCROLL_CLASS_INT) and \
                    self._is_unid(desc, oc):
                pots_scrolls.append((letter, oc, desc))
            elif oc == WAND_CLASS_INT and self._is_unid(desc, oc) and \
                    letter not in self.wand_belief and "(0:" not in desc:
                wands.append((letter, oc, desc))
        return pots_scrolls + wands

    def _line_hostile(self, offensive=True, max_range=7):
        """Nearest non-peaceful hostile on a clear straight (cardinal/diagonal)
        line from us within max_range. Returns (monster, dirkey) or None."""
        A = self.atlas
        L = A.level
        ax, ay = A.agent
        best = None
        bestd = 99
        for m in L.monsters:
            if m.pet or m.name in C.IMMOBILE or m.pos in L.no_attack:
                continue
            if m.name in CAST_NEVER or m.cls == "@" and not m.pet:
                # never fire directional magic at peaceful-generating @-classes
                if m.name in CAST_NEVER:
                    continue
            dx, dy = m.x - ax, m.y - ay
            dist = max(abs(dx), abs(dy))
            if dist < 1 or dist > max_range:
                continue
            if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
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
            if clear and dist < bestd:
                best, bestd = (m, DIR_OF[(sx, sy)]), dist
        return best

    def _ray_blocks(self, x, y):
        """A cell that stops/reflects a buzz ray (wall/stone/bars/tree/closed
        door). UNKNOWN (unexplored) is treated as blocking = stone: this is the
        conservative choice that catches the dead-end-corridor return (the cell
        past a corridor end is unexplored stone)."""
        L = self.atlas.level
        if not (0 <= x < C.COLS and 0 <= y < C.ROWS):
            return True
        return int(L.terrain[y][x]) in (C.WALL, C.IRONBARS, C.TREE, C.UNKNOWN,
                                        C.DOOR_CLOSED)

    def _ray_self_hit(self, sx, sy, max_range=None):
        """Simulate a bouncing buzz ray fired from @ in direction (sx,sy) and
        return True if it re-enters @'s own cell within range (self-hit). Bounce
        model = NetHack src/zap.c buzz(): cardinal ray reverses off a head-on
        wall; diagonal ray flips the blocked component (conservative: if either
        diagonal bounce could return, we flag). One reversal then fizzle."""
        if max_range is None:
            max_range = RAY_RANGE
        ax, ay = self.atlas.agent
        x, y, dx, dy = ax, ay, sx, sy
        for _ in range(max_range):
            nx, ny = x + dx, y + dy
            if self._ray_blocks(nx, ny):
                if dx and dy:                       # diagonal
                    vert_ok = not self._ray_blocks(x - dx, y + dy)  # flip dx
                    horiz_ok = not self._ray_blocks(x + dx, y - dy)  # flip dy
                    if vert_ok and not horiz_ok:
                        dx = -dx
                    elif horiz_ok and not vert_ok:
                        dy = -dy
                    elif vert_ok and horiz_ok:
                        dx = -dx                    # corner: pick one
                    else:
                        dx, dy = -dx, -dy
                else:                               # cardinal: reverse the axis
                    if dx:
                        dx = -dx
                    else:
                        dy = -dy
                nx, ny = x + dx, y + dy
                if self._ray_blocks(nx, ny):
                    break                           # boxed in: ray fizzles
            if (nx, ny) == (ax, ay):
                return True
            x, y = nx, ny
        return False

    def _consume_zap(self, obs, crisis):
        """Zap a KNOWN offensive/control wand at a threat in line. THE spike-
        death counter: a wand of sleep/striking/death ends the unfleeable one-
        exchange fight and yields a zero-exchange (safe) kill = free XP. In
        crisis (low HP + adjacent) fire at any in-line hostile; proactively fire
        only at fast/same-speed/tough threats (the ones that spike-kill us)."""
        if not C2_CONSUME:
            return None
        inv = self._consume_inv(obs)
        if not inv["off_wand"]:
            return None
        A = self.atlas
        tgt = self._line_hostile(offensive=True, max_range=7)
        if tgt is None:
            return None
        m, dirkey = tgt
        adj = max(abs(m.x - A.agent[0]), abs(m.y - A.agent[1])) <= 1
        fast = m.speed >= OUR_SPEED or m.name in FAST_THREATS
        tough = m.difficulty >= max(3, A.xplvl)
        if not (crisis or adj or fast or tough):
            return None
        key = (A.key, m.pos)
        if self.zapped_at.get(key, 0) >= 4:
            return None
        # prefer striking (cheap/reliable) then rays; sleep/death end fights best
        pref = {"sleep_or_death": 0, "death": 0, "sleep": 0, "striking": 1,
                "magic missile": 2, "cold": 2, "fire": 2, "lightning": 3,
                "slow monster": 4, "cancellation": 5, "polymorph": 6}
        letter, wtype = sorted(inv["off_wand"],
                               key=lambda lw: pref.get(lw[1], 9))[0]
        # NH-E38b REFLECTION GUARD: a buzz ray fired down a dead-end corridor
        # reverses off the far wall and returns to @ (the seed-4 self-reflected
        # lightning death). Veto the zap if the ray path bounces back onto us;
        # fall through to melee/flee. (In an open room the ray exits, no return
        # -> zaps still fire.)
        if wtype in BOUNCING_RAY_WANDS and self._ray_self_hit(*DIRS[dirkey]):
            self.note(f"CONSUME zap-VETO reflect {wtype}({letter}) dir {dirkey} "
                      f"at {m.name} d{max(abs(m.x-A.agent[0]),abs(m.y-A.agent[1]))} "
                      f"(ray returns to @ in confined geometry)")
            self._ev(f"CONSUME zap-VETO reflect {wtype}")
            return None
        self.zapped_at[key] = self.zapped_at.get(key, 0) + 1
        self._pending_zap_kill = 3
        self._goal("zap", f"{wtype} at {m.name} d{max(abs(m.x-A.agent[0]),abs(m.y-A.agent[1]))}")
        self.note(f"CONSUME zap-offensive {wtype}({letter}) at {m.name} "
                  f"(crisis={int(crisis)} fast={int(fast)} tough={int(tough)})")
        self._ev(f"CONSUME zap {wtype} at {m.name}")
        self.queue = [letter, dirkey]
        self.queue_tag = "zap"
        return "zap"

    def _consume_heal(self, obs):
        """Quaff a KNOWN healing potion at HP crisis (secondary to the wand —
        a heal can't outrun a spike, but recovers a survivable band)."""
        if not C2_CONSUME:
            return None
        A = self.atlas
        if A.hp > 0.40 * A.hpmax:
            return None
        inv = self._consume_inv(obs)
        if not inv["heal_pot"]:
            return None
        letter, d = inv["heal_pot"][0]
        self.consumed_letters.add(letter)
        self._goal("quaff", f"heal {d[:24]}")
        self.note(f"CONSUME quaff-heal {letter} ({d[:30]}) hp {A.hp}/{A.hpmax}")
        self._ev(f"CONSUME quaff-heal hp {A.hp}/{A.hpmax}")
        self.queue = [letter]
        self.queue_tag = "quaff"
        return "quaff"

    def _consume_safe(self, obs):
        """Non-crisis, no-hostile: use KNOWN gain-level (direct safe XP —
        highest-value single item, but supply-limited) + enchant armor/weapon +
        read-identify to resolve an unknown consumable."""
        if not C2_CONSUME or self._adjacent_hostiles():
            return None
        A = self.atlas
        if A.hunger >= C.WEAK:
            return None
        inv = self._consume_inv(obs)
        if inv["gainlevel"]:
            letter, how = inv["gainlevel"][0]
            self.consumed_letters.add(letter)
            self.gainlevel_used += 1
            self._goal(how, "gain level")
            self.note(f"CONSUME gainlevel {how} {letter} (xp {A.xplvl})")
            self._ev(f"CONSUME gainlevel {how} xp {A.xplvl}")
            self.queue = [letter]
            self.queue_tag = how
            return how
        if inv["enchant"]:
            letter, d = inv["enchant"][0]
            self.consumed_letters.add(letter)
            self._goal("read", f"enchant {d[:20]}")
            self.note(f"CONSUME enchant read {letter} ({d[:26]})")
            self.queue = [letter]
            self.queue_tag = "read"
            return "read"
        # NH-E38b READ-IDENTIFY: spend a KNOWN scroll of identify on a floor-
        # acquired UNIDENTIFIED potion/scroll (engrave-ID can only touch wands,
        # so without this the USE layer never sees a picked-up potion/scroll ->
        # the pilot's under-firing). Real ID: the game mutates the item's desc,
        # so next step _consume_inv buckets it as usable (heal/gain-level/
        # enchant). No zap risk, deterministic. "blind" blocks reading.
        if inv["identify"] and self._unid_consumables(obs) and \
                "blind" not in A.message.lower():
            scroll_letter, _sd = inv["identify"][0]
            tgt_letter, tgt_oc, tgt_desc = self._unid_consumables(obs)[0]
            self.consumed_letters.add(scroll_letter)
            self.identify_in_flight = 6      # step budget for the target prompt
            self.identify_scroll = scroll_letter
            self._id_selected = False
            self._goal("read", f"identify {tgt_letter}")
            self.note(f"CONSUME read-identify scroll {scroll_letter} -> target "
                      f"{tgt_letter} ({tgt_desc[:24]})")
            self._ev("CONSUME read-identify")
            self.queue = [scroll_letter]     # answers 'What do you want to read?'
            self.queue_tag = "read_id"
            return "read"
        return None

    def _price_id(self, obs):
        """Shop PRICE-ID (NH-E38b): narrow an UNIDENTIFIED shop-priced potion/
        scroll to a known identity when the base cost is UNAMBIGUOUS (a single
        table candidate). Buy price = base * 4/3 (unid surcharge) at the Cha
        11-15 x1 band; we invert conservatively and accept ONLY an exact single-
        candidate hit so a mis-narrowed heal can't cause a bad quaff. Sets
        item_belief[letter] (a belief, not a real ID). Fires only in a shop ->
        rarely on the shallow dev sample (disclosed; charisma-band caveat)."""
        if not C2_CONSUME or not _PRICE_KB:
            return
        try:
            for letter, desc, oc in self._inv(obs):
                if letter in self.priced_letters or letter in self.item_belief:
                    continue
                if oc not in (POTION_CLASS_INT, SCROLL_CLASS_INT) or \
                        not self._is_unid(desc, oc):
                    continue
                m = RE_UNPAID.search(desc)
                if not m:
                    continue
                self.priced_letters.add(letter)     # adjudicate once
                price = int(m.group(1))
                cls = "potion" if oc == POTION_CLASS_INT else "scroll"
                names = set()
                for cost_s, items in _PRICE_KB.get(cls, {}).items():
                    base = int(cost_s)
                    if base and round(base * 4 / 3) == price and len(items) == 1:
                        names.add(items[0]["name"])
                if len(names) == 1:
                    name = next(iter(names))
                    self.item_belief[letter] = f"{cls} of {name}"
                    self.note(f"CONSUME price-id {letter}={cls} of {name} "
                              f"(shop price {price})")
                    self._ev(f"CONSUME price-id {cls} of {name}")
        except Exception:                   # noqa: BLE001 — never a gate
            return

    def _engrave_id(self, obs):
        """Low-risk wand identification: engrave-test an unidentified wand
        (write in dust with the wand as the tool -> the discharge message
        reveals the class, NO zap-effect risk). One test per wand. Safe-gated."""
        if not C2_CONSUME or self.pending_engrave is not None:
            return None
        A = self.atlas
        if self._adjacent_hostiles() or A.hunger >= C.WEAK or \
                "blind" in A.message.lower():
            return None
        inv = self._consume_inv(obs)
        if not inv["unid_wand"]:
            return None
        letter, desc = inv["unid_wand"][0]
        self.engrave_tested.add(letter)
        self.pending_engrave = (letter, 3)
        self._goal("engrave", f"ID-test wand {letter}")
        self.note(f"ENGRAVE-ID test wand {letter} ({desc[:26]})")
        self._ev(f"ENGRAVE-ID test {letter}")
        # mirror the validated Elbereth engrave queue (also lays protection):
        self.queue = [letter] + list("Elbereth") + ["more"]
        self.queue_tag = "engrave"
        return "engrave"

    def _consume_acquire(self, obs):
        """Bounded detour to a floor CONSUMABLE (wand>scroll>potion) so the
        engrave-ID + use policy has ammunition — the offensive wand that ends
        the spike fight is on the FLOOR, not in the starting kit. Same no-stall
        discipline as _weapon_acquire: per-cell tries cap + radius cap + a
        per-LEVEL detour budget so descent never stalls (the s13/FOODACQ
        lesson). Underfoot pickup completes it. Fail-safe -> None."""
        try:
            if P is None:
                return None
            A = self.atlas
            L = A.level
            spent = self.consume_detour.get(A.key, 0)
            if spent >= CONSUME_LEVEL_BUDGET:
                return None
            tgts = P.consumable_targets(obs["obs"]["glyphs"], A.agent,
                                        radius=CONSUME_RADIUS)
            if not tgts:
                return None
            _pr, cell, kind = tgts[0]
            tk = (A.key, cell)
            if self.loot_tries.get(tk, 0) >= 6:
                # try the next target if the best is stuck
                nxt = [t for t in tgts if self.loot_tries.get((A.key, t[1]), 0) < 6]
                if not nxt:
                    return None
                _pr, cell, kind = nxt[0]
                tk = (A.key, cell)
            if cell == A.agent:
                return None                 # underfoot handler picks it up
            path = L.bfs(A.agent, [cell], avoid=self._travel_avoid({cell}))
            if path and len(path) <= CONSUME_RADIUS:
                self.consume_detour[A.key] = spent + 1
                if len(path) <= 2:
                    self.loot_tries[tk] = self.loot_tries.get(tk, 0) + 1
                self._goal("acquire", f"{kind} d{len(path)}")
                self.note(f"CONSUME walk to {kind} ({len(path)} steps)")
                return self._step_path(path)
            return None
        except Exception:                   # noqa: BLE001 — never a gate
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
        # wear what we carry (multi-turn: only when safe). NH_LOOT reuses this
        # as its armor-USE step (wear what was looted).
        if (C2_ARMOR or C2_LOOT) and self.wearable:
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
        if C2_RANGED or C2_ARMOR or C2_LOOT:
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
            # NH-E38b: a read-identify interaction only lives across its
            # consecutive prompts; once no prompt is open it is finished.
            if C2_CONSUME and self.identify_in_flight:
                self.identify_in_flight = 0
                self._id_selected = False
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
        # NH-E38 CRISIS consumable: a spike fight (hostile adjacent, HP falling)
        # is exactly where a wand of sleep/striking/death ENDS it in one action
        # (the counter to the unfleeable one-exchange death). Fire it above
        # prayer/melee; then quaff-heal to recover a survivable band.
        if C2_CONSUME and adj and A.hp < 0.60 * A.hpmax:
            za = self._consume_zap(obs, crisis=True)
            if za is not None:
                return za
        if C2_CONSUME:
            ha = self._consume_heal(obs)
            if ha is not None:
                return ha
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
        # E39 HUNGER-CRISIS PRAYER: pray when Weak/Fainting from hunger => god
        # feeds you (the standard starvation rescue). Diagnosis: 0/64 long
        # starve-loop deaths ever prayed because every prayer trigger checked
        # only HP, never hunger. last_resort=True: imminent starvation waives
        # the turn gates (an angry god beats starving). Default-OFF (bit-ident).
        if C2_PRAYHUNGER and A.hunger >= C.WEAK and self._pray_ok(last_resort=True):
            self.prayed_at = A.time
            self.pray_count += 1
            self.note(f"pray (hunger {A.hunger}, starvation rescue)")
            self._goal("survive", f"pray hunger {A.hunger}")
            self.queue = ["y"]
            self.queue_tag = "pray"
            return "pray"
        # NH-E13b Healer MIDDLE-BAND heal (s7 refinement — the WHEN-fix): when a
        # threat is adjacent AND HP sits in the [LO,HI] band, cast-heal EARLY
        # (before the hp-4 crisis that heals-a-sliver-and-dies, s6) instead of
        # trading melee. Under-threat gate replaces the s6 proactive no-threat
        # top-up that perturbed good runs. Band-gated in _cast_heal; no-op unless
        # NH_ROLE_PROFILE + Healer (flag-off bit-identical).
        if C2_ROLE_PROFILE and self.role == "Healer" and adj:
            act = self._cast_heal(obs)
            if act:
                return act
        if C2_EXPMAX:
            if adj:
                act = self._c2_combat(obs, adj)
                if act:
                    return act
        else:
            # crisis zone: below ~28% max HP, or worst recent hit could
            # kill us within two more exchanges -> disengage from slower
            crisis = A.hp <= max(A.hpmax * CRISIS_HP, 6) or \
                (self.recent_max_hit * CRISIS_EXCH >= A.hp and
                 self.recent_max_hit > 0)
            if crisis and adj:
                act = self._flee(adj)
                if act:
                    return act
                # NH-E13 Healer (trapped): _flee declined -> cast-heal to
                # survive the trade rather than fall through to melee.
                act = self._cast_heal(obs)
                if act:
                    return act
                # _flee declined (same-speed/faster adjacent — the s4 REST
                # failure mode). THROW_DISENGAGE: ranged strike instead of
                # falling through to a stand-and-trade death (NH_CRISIS_THROW,
                # default off => this block is a no-op when unset).
                act = self._crisis_throw(obs)
                if act:
                    return act
        # s6 proactive no-threat top-up REMOVED (s7): it healed when safe and
        # perturbed otherwise-good runs (seed 900: D10 -> D4). The middle-band
        # UNDER-THREAT heal above is the replacement WHEN-trigger.

        # FOOD-ACQUISITION: OPPORTUNISTIC SAFE-CORPSE BANKING (NH_FOODACQ, s11).
        # RULE CARD [FOODACQ] (layer: LOGISTICS; model: claude-opus-4-8[max]).
        # s10 mechanism finding (CARD S10-1): the anti-faint guard FIRED but had
        # NOTHING to eat — hunger-prone roles reach Hungry with an empty larder
        # because they never BANK the free nutrition from the corpses they have
        # already made. Experts stay "never below Hungry" (S9-2) precisely because
        # they have ACQUIRED food. So bank proactively: eat a safe fresh corpse we
        # stand on, or step <=2 to one we just killed, whenever we are NOT already
        # Satiated and no hostile is adjacent. Nutrition is free after a fight we
        # already won; this fills the larder BEFORE the hunger cascade and gives
        # the anti-faint guard (NH_ANTIFAINT) something to act on. Choke-safe:
        # gated on hunger >= NotHungry (never eat at Satiated=0); once a bank
        # pushes us to Satiated the guard self-disables until we drop back — a
        # naturally self-limiting top-up. Corpse-only (inventory food + prayer
        # stay with the ANTIFAINT/WEAK crisis blocks below).
        # provenance: insight-origin=OP (DEATH_TO_CAPABILITY Tier-1 food-
        # acquisition / corpse-aggressiveness) + knowledge=our own S10-1 death
        # mechanism (guard-fired-empty-larder) + demonstration arbiter (S9-2:
        # experts have ACQUIRED food). replication: NH_FOODACQ[+NH_ANTIFAINT]
        # paired block vs REF on the hunger-enriched fainting corpus; KPI =
        # nutrition-secured (arrive-at-Hungry-with-food) -> fainting-incidence.
        # UNDERFOOT-ONLY (zero-diversion): eat a safe fresh corpse we are ALREADY
        # standing on. We deliberately do NOT route TO corpses at NotHungry — an
        # early build with a <=2-step walk-to-corpse leg turned the agent into a
        # corpse-vacuum that looped near kills and never descended (dev seeds
        # 101/102/110: depth 9/10/15 REF -> depth 1-2 TEST, ~650 fires). Active
        # routing to remembered corpses stays in the Hungry/Weak crisis blocks
        # below, where the detour is warranted. Here we only bank the free corpse
        # under our feet (typically after we stepped onto a kill cell) — no path
        # diversion, so descent is unaffected on non-hunger seeds.
        # Rate-limit: bank at most once per FOODACQ_COOLDOWN turns. Without it,
        # a NotHungry agent in a monster-dense pocket banks every corpse it steps
        # on and farms in place instead of descending (dev seed 101: depth 9 REF
        # -> depth 4 TEST, 559 fires). A single small corpse (newt=3 nutrition)
        # does not raise the hunger TIER, so tier-gating alone re-fires endlessly;
        # the cooldown caps the farm while still banking often enough to stay fed
        # (one bank per ~25 turns tops up the ~1/turn depletion many times over
        # the ~1400-turn Hungry->Fainting window).
        if (C2_FOODACQ and A.hunger >= 1 and not self._adjacent_hostiles()
                and A.time - getattr(self, "_foodacq_last", -9999)
                >= FOODACQ_COOLDOWN):
            corpse = self._fresh_corpse_here()
            if corpse:
                self._foodacq_last = A.time
                self._goal("eat", f"foodacq bank {corpse}")
                self.note(f"FOODACQ bank fresh corpse here ({corpse}, "
                          f"hunger {A.hunger})")
                self.queue = ["y"]
                self.queue_tag = "eat_corpse"
                return "eat"

        # ANTI-FAINT GUARD (NH_ANTIFAINT, Phase L s9). RULE CARD [ANTI_FAINT]
        # (layer: LOGISTICS; model: claude-opus-4-8[max]). Experts NEVER let
        # hunger drop below Hungry — E35c ttyrec evidence: 4 alt.org games /
        # ~35k turns, 0 frames below Hungry; they eat one tier EARLIER than our
        # WEAK trigger. The 52 faint deaths come from the short Weak->Fainting->
        # Fainted cascade outrunning food-acquisition once already at Weak. So
        # bank READILY-available food at HUNGRY (inventory food / corpse-here /
        # <=3-step safe corpse), BEFORE the cascade. Elective, so gate on no
        # adjacent hostile (don't donate a free attack for a non-crisis eat);
        # prayer + longer detours stay in the WEAK+ block below.
        # provenance: knowledge=DEMONSTRATION (alt.org expert hunger policy,
        # E35c) + insight-origin=OP (DEATH_TO_CAPABILITY Tier-1 anti-faint
        # guard) + precedent rule CAST_HUNGER ("casters eat at HUNGRY not Weak").
        # replication: NH_ANTIFAINT=1 paired block vs off; KPI = faint-death rate.
        if C2_ANTIFAINT and A.hunger == C.HUNGRY and not self._adjacent_hostiles():
            fl = self._food_letter(obs)
            if fl:
                self._goal("eat", f"antifaint hunger {A.hunger}")
                self.note(f"ANTIFAINT eat inventory food {fl} (hunger {A.hunger})")
                self.queue = [fl]
                self.queue_tag = "eat"
                return "eat"
            corpse = self._fresh_corpse_here()
            if corpse:
                self._goal("eat", f"antifaint corpse {corpse}")
                self.note(f"ANTIFAINT eat fresh corpse here ({corpse})")
                self.queue = ["y"]
                self.queue_tag = "eat_corpse"
                return "eat"
            cells = [k[0] for k in self.fresh_kills
                     if k[1] in C.SAFE_CORPSES and not self._cannibal(k[1])
                     and k[0] != A.agent]
            if cells:
                path = A.level.bfs(A.agent, cells,
                                   avoid=self._suspects() | self._mcells())
                if path and len(path) <= 3:
                    self._goal("eat", "antifaint walk-to-corpse")
                    self.note("ANTIFAINT walk to safe corpse "
                              f"(hunger {A.hunger}, {len(path)} steps)")
                    return self._step_path(path)

        if WIELD_DIAG:                         # read-only floor-weapon diagnosis
            self._wield_diag(obs)

        # EFFICIENT LOOTING (NH_LOOT, Phase L s15) — the acquisition-bound
        # meta-finding as a lever. Value floor weapons(dpt)+armor(AC) and grab
        # the best under a value/detour threshold + per-level detour budget; the
        # NH_WIELD/NH_ARMOR USE levers below then fire on the acquisition. Safe/
        # non-crisis gated (hunger < WEAK, no adjacent hostile).
        if C2_LOOT and A.hunger < C.WEAK and not self._adjacent_hostiles():
            la = self._efficient_loot(obs)
            if la is not None:
                return la

        # WEAPON ACQUISITION (NH_WIELDACQ, s13 pivot) — close the loot gap so a
        # floor weapon that upgrades melee is actually taken; the NH_WIELD lever
        # then wields it. Safe/non-crisis gated; bounded detour.
        if C2_WIELDACQ and A.hunger < C.WEAK and not self._adjacent_hostiles():
            aa = self._weapon_acquire(obs)
            if aa is not None:
                return aa

        # WIELD UPGRADE (NH_WIELD, Phase L s13) — direct combat-capability
        # injection. Non-crisis capability upkeep: swap to a strictly better
        # carried weapon while safe. Gated on hunger < WEAK (crisis eats win
        # below) and no adjacent hostile (never be caught mid-swap weaponless).
        # NH_LOOT reuses this as its weapon-USE step (wield what was looted).
        if (C2_WIELD or C2_LOOT) and A.hunger < C.WEAK \
                and not self._adjacent_hostiles():
            wa = self._wield_upgrade(obs)
            if wa is not None:
                return wa

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
            # MIGRATED to rule base [PRAYFIX_DEFER] (s7): the mobile-adjacent
            # trigger is the exact port `any(m.name not in IMMOBILE for m in adj)`.
            _adj_mobile = (RULEBASE.check("PRAYFIX_DEFER", self._rb_state(
                adj_mobile=any(m.name not in C.IMMOBILE for m in adj)))
                if C2_RULEBASE else any(m.name not in C.IMMOBILE for m in adj))
            if C2_PRAYFIX and pray_now and A.hunger < C.FAINTING and _adj_mobile:
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
            if C2_CASTHUNGER_EAT and self._caster_active():
                # CAST_HUNGER_V1(b) — DEMOTED to its own sub-flag after
                # CASTHUNGER-1: eat-early at Hungry fired on every caster
                # run (vs the rare refusal event), diverted mid-run
                # (s918 -9.91) and burned rations early so Weak-tier
                # found an empty inventory ("while fainted" deaths s912/
                # s940). Resource-TIMING lesson: earlier consumption of a
                # fixed stock is not more food. Latch (a) is the doctrine.
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

        # ---- P4.85: NH-E38 proactive offensive-wand zap --------------------
        # Zap a fast/same-speed/tough threat in line BEFORE trading melee (a
        # zero-exchange kill = the safe XP that raises arrival-XP@D5, and it
        # pre-empts the spike). Non-crisis: only fires at threats that are the
        # ones that spike-kill us (gated inside _consume_zap).
        if C2_CONSUME:
            za = self._consume_zap(obs, crisis=False)
            if za is not None:
                return za

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

        # ---- NH-ADVISORY: LLM-strategist consult at strategic triggers ------
        # placed AFTER the safety cascade (crisis/hunger/combat/ranged) so the
        # strategist never overrides a tactical emergency — it only redirects
        # the strategic explore/descend/rest/disengage choice below.
        if C2_ADVISORY:
            act = self._advisory(obs, msg)
            if act:
                return act

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

        # ---- P5.8: SAFE EARLY LEVELING (NH_SAFELEVEL, Phase L s16) ----------
        # RULE CARD [SAFELEVEL] (layer: PROGRESSION; model: claude-opus-4-8[max]).
        # The bootstrap-breaker. s13-s15 characterized the mean as ACQUISITION-
        # bound: gear is locked behind depth, the agent hits the D5-6 kill-zone at
        # xp 1-3 and dies to trash, and looting nulls on the mean because there is
        # nothing worth looting at the shallow depths where runs die (yet seed 700,
        # already at D9, saw looting compound D9->D12). XP is the OTHER unused
        # capability (the direct parallel to the WIELD/food-acquisition levers).
        # So on the early floors (D1..SAFELEVEL_MAXDEPTH), BEFORE committing to the
        # stairs, route to an ISOLATED, SAFE, weak monster and kill it for XP, so
        # we arrive at D5-6 at xp>=TARGET instead of xp 1-3 — arriving stronger to
        # survive shallow combat, reach the depth where gear exists, and let
        # acquisition compound (seed 700 proves compounding works once deep).
        # SAFE = exchange-model gated (the offline species model as safety oracle):
        # expected HP lost to the kill (species_dpt * species_ttk) <= MARGIN*hp AND
        # per-turn dpt <= MAX_DPT AND not never-melee AND not faster than us AND low
        # difficulty. ISOLATED = no OTHER hostile within ISO_R of the prey (never
        # wade into a pack). HP-healthy gated (only start a fight near full hp).
        # BOUNDED so it does NOT become the food-farm/loot-detour stall (s11/s13
        # descent-stall confound): stop at xplvl>=TARGET_XP OR when the per-level
        # SAFELEVEL_BUDGET of hunt-steps is spent, whichever first, then descend.
        # Adjacent safe monsters are already fought by the P5 combat layer (the
        # agent gains that XP in REF too); this layer's counterfactual is ROUTING
        # to DISTANT safe prey instead of beelining the stairs. Default OFF
        # (bit-identical when off — gated entirely on C2_SAFELEVEL).
        # provenance: insight-origin=OP (bootstrap wall: capability locked behind
        # depth, XP = the unused lever) + knowledge=our own s11-s15 acquisition-
        # bound corpus + the offline exchange model (species_dpt/ttk). KPI =
        # arrival-xp at D5 -> combat-survival -> PROGRESSION MEAN, paired on the
        # trash-melee combat-death corpus.
        if (C2_SAFELEVEL and A.depth <= SAFELEVEL_MAXDEPTH
                and A.xplvl < SAFELEVEL_TARGET_XP
                and A.hunger < C.WEAK
                and A.hp >= SAFELEVEL_HP_FRAC * A.hpmax
                and not self._adjacent_hostiles()
                and self.safelevel_turns.get(A.key, 0) < SAFELEVEL_BUDGET
                and P is not None):
            sl = self._safe_level(obs)
            if sl is not None:
                return sl

        # ---- P6.5: urgent/cheap item grabs before committing to descent ----
        # NH-ADVISORY DESCEND bias skips the loot detour: head straight down.
        if C2_ANY and not (C2_ADVISORY and self.steps < self._adv_descend_until):
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

        # ---- P8.55: NH-E38 safe consumables + engrave-ID -------------------
        # When safe (no adjacent hostile, not weak): use gain-level (direct XP),
        # enchant armor/weapon; and engrave-test an unidentified wand to unlock
        # the offensive-wand branch (deterministic, zap-risk-free ID).
        if C2_CONSUME:
            act = self._consume_safe(obs)
            if act:
                return act
            act = self._engrave_id(obs)
            if act:
                return act
            # NH_CONSUME_NOACQ (E38b disentangle): use-only variant — skip the
            # floor-consumable acquisition DETOUR to isolate consumable-USE effect
            # from path-perturbation confound (the +2.64 on-fire signal was
            # detour-driven: seed715 +7.92 had 0 use + 9 acq). Default unset =
            # bit-identical to prior NH_CONSUME behavior.
            if A.hunger < C.WEAK and not adj and not _os.environ.get("NH_CONSUME_NOACQ"):
                act = self._consume_acquire(obs)
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
            if (C2_ARMOR or C2_LOOT) and any(k in it for k in
                                P.BODY_ARMOR + P.HELMETS + P.SHIELDS +
                                P.BOOTS_GLOVES) and (
                    C2_ARMOR or self._armor_slot(it) not in
                    (set(self.worn_slots) | {s for _, s, _ in self.wearable})):
                self.note(f"picking up armor: {it}")
                self._goal("loot", f"armor here: {it[:30]}")
                self.pickup_kind = "armor"
                if C2_LOOT:
                    self.loot_fires += 1
                    self.loot_arm_fires += 1
                    self._loot_target = None
                self.queue_tag = "pickup"
                return "pickup"
            if C2_RANGED and len(self.ammo_letters) < 10 and \
                    any(k in it for k in P.AMMO_NAMES):
                self.note(f"picking up ammo: {it}")
                self._goal("loot", f"ammo here: {it[:30]}")
                self.pickup_kind = "ammo"
                self.queue_tag = "pickup"
                return "pickup"
            if C2_WIELDACQ or C2_LOOT:
                wn = self._weapon_upgrade_underfoot(obs, it)
                if wn:
                    # item-under-@ blind spot: complete the weapon-acquire the
                    # moment we stand on the upgrade (the glyph is hidden under
                    # @, so _weapon_acquire's cell==agent branch can't fire).
                    self.note(f"LOOT pickup {wn} (underfoot weapon, via message)")
                    self._goal("acquire", f"weapon here: {it[:30]}")
                    self.pickup_kind = "weapon"
                    self._pickup_wpn_kw = wn
                    self.wieldacq_fires += 1
                    if C2_LOOT:
                        self.loot_fires += 1
                        self.loot_wpn_fires += 1
                        self._loot_target = None
                    self.queue_tag = "pickup"
                    return "pickup"
            # NH-E38: grab a floor CONSUMABLE underfoot (wand/potion/scroll) so
            # the engrave-ID + use policy has something to act on (the offensive
            # wand that ends the spike fight is on the FLOOR, not in the starting
            # kit for most roles). Underfoot-only (zero detour) = no descent
            # stall; wands are light, potions/scrolls minor. Skip when burdened.
            if C2_CONSUME and not self.burdened and \
                    any(k in it for k in ("wand", "potion", "scroll")):
                self.note(f"CONSUME pickup (underfoot): {it}")
                self._goal("acquire", f"consumable here: {it[:30]}")
                self.pickup_kind = "consumable"
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
        # NH-E13 heal scan (ADDITIVE, independent of the attack path): a
        # Healer's cast_unavailable=True (no attack spell) must NOT hide the
        # healing spell. Pick the cheapest HP-restoring spell (name contains
        # "healing"; "healing" lvl1/5pw is the bread-and-butter, always
        # affordable and repeatable — Healers have a large Pw pool + regen).
        if C2_ROLE_PROFILE and self.role == "Healer":
            self.heal_scanned = True
            hbest = None
            for l, (n, lv, cat, f) in self.cast_spells.items():
                if "healing" in n and f <= 40:
                    if hbest is None or lv < hbest[0]:
                        hbest = (lv, l, n, 5 * lv)
            if hbest:
                self.heal_choice = (hbest[1], hbest[2], hbest[3])
                self.note(f"heal menu: choice {self.heal_choice}")
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

    def _kick_ok(self):
        """RULE CARD [KICK_COST_GATE] (layer: PROCEDURE; model:
        claude-opus-4-8[1m] s7; provenance: inferred — break-leg death mode).
        Kicking a locked door risks a broken leg (-> slowed -> death), a cost
        the s6 audit found ungated (kicks fired up to 12x with no HP/role
        check). Skip the kick when HP is below KICK_MIN_HP of max or the role is
        fragile/low-HD (KICK_FRAGILE_ROLES); the caller defers the door instead.
        Flag-off (NH_KICK_GATE unset) -> always True == bit-identical.
        """
        if not C2_KICK_GATE:
            return True
        A = self.atlas
        if self.role in KICK_FRAGILE_ROLES:
            return False
        if A.hpmax and A.hp < KICK_MIN_HP * A.hpmax:
            return False
        return True

    def _cast_heal(self, obs):
        """RULE CARD [HEALER_CAST_HEAL] (layer: PROCEDURE; model:
        claude-opus-4-8[1m] s6, WHEN-refined s7; provenance: wiki — nethackwiki
        Healer page, "cast healing for survival"). When a Healer's HP sits in the
        MIDDLE band [HEAL_HP_LO, HEAL_HP_FRAC] of max, cast the healing spell
        (self-target, no direction) to restore HP rather than trading melee or
        burning a prayer. s7: the band floor (LO) drops the s6 too-late crisis
        heal; the caller's under-threat gate drops the s6 proactive top-up. A
        capability the agent has NEVER used (pure headroom). Fires only under
        NH_ROLE_PROFILE + role==Healer (flag-off == bit-identical). First
        cast opens + parses the spell menu; heal_choice/heal_unavailable are
        latched from the parse. Respects the CAST_HUNGER latch (no too-hungry
        retry loop) and the Pw budget.
        """
        if not (C2_ROLE_PROFILE and self.role == "Healer"):
            return None
        A = self.atlas
        # MIDDLE-BAND gate (s7): heal only inside [HEAL_HP_LO, HEAL_HP_FRAC] of
        # max HP. Above HI: no need. Below LO: too late (s6: heal-a-sliver-and-
        # die) -> defer to crisis-flee / prayer. This band IS the WHEN-fix.
        # MIGRATED to rule base [HEAL_MIDBAND] (s7): exact port of the band gate.
        in_band = (RULEBASE.check("HEAL_MIDBAND", self._rb_state())
                   if C2_RULEBASE
                   else HEAL_HP_LO * A.hpmax <= A.hp <= HEAL_HP_FRAC * A.hpmax)
        if not in_band:
            return None
        if C2_CASTHUNGER and self.cast_hunger_blocked:
            return None
        if self.heal_scanned and self.heal_choice is None:
            return None                 # no HP-restoring spell in the book
        cost = self.heal_choice[2] if self.heal_choice else 5
        if A.pw < cost:
            return None
        self.heal_in_flight = True
        self._goal("survive", f"cast-heal hp {A.hp}/{A.hpmax}")
        self.note(f"cast-heal (hp {A.hp}/{A.hpmax} pw {A.pw})")
        self._ev(f"HEALER_CAST_HEAL: hp {A.hp}/{A.hpmax} pw {A.pw}")
        return "cast"

    def _answer_prompt(self, obs, msg, in_yn, in_getlin, waitspace):
        A = self.atlas
        # NH-E38b READ-IDENTIFY target selection. After reading a known scroll
        # of identify, the game asks "What would you like to identify?" — a
        # getobj (single, uncursed) or a multi-select menu (blessed). Select an
        # unidentified consumable letter; on a menu, toggle one then confirm.
        # Bounded by identify_in_flight; the P0 repeat-escape covers any stall.
        if C2_CONSUME and self.identify_in_flight > 0:
            self.identify_in_flight -= 1
            low = msg.lower()
            tgts = self._unid_consumables(obs)
            if (in_yn or in_getlin) and ("identify" in low or
                                         "what would you like" in low):
                return tgts[0][0] if tgts else "esc"
            if waitspace and ("identify" in low or self._tty_has(obs, "identify")):
                if tgts and not self._id_selected:
                    self._id_selected = True
                    return tgts[0][0]           # toggle in the multi-select menu
                self._id_selected = False
                return "more"                    # confirm selection / dismiss
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
        if (C2_CAST or (C2_ROLE_PROFILE and self.heal_in_flight)) and \
                ("Choose which spell to cast" in msg or
                 self._tty_has(obs, "Choose which spell")):
            self._parse_cast_menu(obs, msg)
            # NH-E13 heal-cast: self-target spell, NO direction prompt follows
            if self.heal_in_flight and self.heal_choice:
                self.heal_in_flight = False
                self.heal_fires += 1
                if self.store is not None:
                    self.store.first(self.steps, A.time, "verb", "cast_heal")
                return self.heal_choice[0]
            self.heal_in_flight = False
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
            elif self.pickup_kind == "weapon" and self._pickup_wpn_kw:
                kws = kws + (self._pickup_wpn_kw,)
            elif self.pickup_kind == "consumable":
                kws = kws + ("wand", "potion", "scroll")   # NH-E38
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

    # ------------------------------------------------------- pet utilization
    # RULE CARD [PET_FOLLOW] (layer: LOGISTICS/COMBAT; NH_PET; Phase L s12;
    # model: claude-opus-4-8[max]). The starting pet fights trash for free and
    # is the untried, zero-resource answer to the TRASH-MELEE death class that
    # s11 unmasked (FOODACQ removed hunger-death but converted it to combat-death
    # at the same depth). But the agent descends the instant it reaches the '>',
    # abandoning the pet on the level above -> the pet is lost after D1 and never
    # helps on the D2-6 kill-zone. A pet follows down the stairs ONLY if it is
    # ADJACENT when '>' is taken. So: preserve it -> before descending, wait a
    # BOUNDED number of turns for the pet to reach an adjacent cell, then go.
    # Bounded per stair cell (PET_WAIT_MAX) + radius-gated (PET_WAIT_RADIUS) so a
    # far/stuck pet cannot stall descent (the FOODACQ stall lesson, CARD S11-2).
    # Never dawdle beside a hostile. provenance: insight-origin=OP
    # (DEATH_TO_CAPABILITY Tier-2 PET UTILIZATION, zero prior use) + knowledge=
    # our own s11 STACKED-DEATH-CLASSES finding (combat is the binding layer once
    # hunger is fixed). replication: REF=C2.1+NH_FOODACQ vs TEST=REF+NH_PET on the
    # trash-melee death corpus; KPI = combat-death rate + progression mean.
    def _live_pet(self):
        """Nearest live pet on the current level, or None."""
        A = self.atlas
        ax, ay = A.agent
        pets = [m for m in A.level.monsters if m.pet]
        if not pets:
            return None
        return min(pets, key=lambda m: max(abs(m.x - ax), abs(m.y - ay)))

    def _pet_follow_wait(self):
        """Return a wait action if we should hold on the down-stairs for the pet
        to become adjacent (so it follows us down); else None. Flag-off (NH_PET
        unset) => immediate None => descent bit-identical."""
        if not C2_PET:
            return None
        A = self.atlas
        if self._adjacent_hostiles():        # never dawdle beside a threat
            return None
        pet = self._live_pet()
        if pet is None:
            return None
        dist = max(abs(pet.x - A.agent[0]), abs(pet.y - A.agent[1]))
        if dist <= 1:                        # already adjacent: it'll follow
            return None
        if dist > PET_WAIT_RADIUS:           # too far to catch up: don't stall
            return None
        key = (A.key, A.agent)
        n = self._pet_waits.get(key, 0)
        if n >= PET_WAIT_MAX:                # budget spent: descend without it
            return None
        self._pet_waits[key] = n + 1
        self.pet_wait_fires += 1
        self._goal("pet", f"wait for pet dist {dist}")
        self.note(f"PET wait for pet (dist {dist}, wait {n + 1}/{PET_WAIT_MAX})")
        return "search"

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
                    # MIGRATED to rule base [TOUCH_KILL_WEAPON] (s7); flag-off ==
                    # literal membership, flag-on delegates the exact port.
                    tk = (RULEBASE.check("TOUCH_KILL_WEAPON",
                                         self._rb_state(monster_name=m.name))
                          if C2_RULEBASE else m.name in TOUCH_KILL)
                    if tk:
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

    def _crisis_throw(self, obs):
        """RULE CARD [THROW_DISENGAGE] (layer: PROCEDURE; model:
        claude-opus-4-8[1m] s5; provenance: e6_solve v2 class-solve rule —
        THROW won >=3 of the 9 s3-UNRESOLVED TRASH deaths on >=3 distinct
        seeds, criterion ii). When the crisis-flee (_flee) declines because
        the adjacent threat is SAME-SPEED or faster (its slower-only +
        full-disengage gates), a stand-and-trade death follows. The v2 menu
        showed the winning line is a RANGED throw: hurl carried ammo at the
        nearest hostile on a clear straight ray, dealing damage without
        donating a melee turn. Fires only under NH_CRISIS_THROW (default
        off; flag-off == bit-identical). Any MOBILE hostile is a target here
        (unlike _throw_at_blocker, which is scoped to never-melee blockers).
        """
        if not CRISIS_THROW:
            return None
        letter = self._throwable_letter(obs)
        if not letter:
            return None
        A = self.atlas
        L = A.level
        ax, ay = A.agent
        cands = []
        for m in L.monsters:
            if m.pet or m.pos in L.no_attack or m.name in C.IMMOBILE:
                continue
            dx, dy = m.x - ax, m.y - ay
            dist = max(abs(dx), abs(dy))
            if dist < 1 or dist > 7:
                continue
            if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
                continue
            key = (A.key, m.pos)
            if self.throws_at.get(key, 0) >= 8:
                continue
            sx, sy = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
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
            cands.append((dist, sx, sy, m))
        if not cands:
            return None
        cands.sort(key=lambda c: c[0])
        _, sx, sy, m = cands[0]
        self.throws_at[(A.key, m.pos)] = \
            self.throws_at.get((A.key, m.pos), 0) + 1
        self.note(f"crisis-throw {letter} at {m.name} at {m.pos} "
                  f"(hp {A.hp})")
        self._ev(f"THROW_DISENGAGE: {letter}->{m.name} dist "
                 f"{cands[0][0]} (hp {A.hp}/{A.hpmax})")
        self.queue = [letter, DIR_OF[(sx, sy)]]
        self.queue_tag = "throw"
        return "throw"

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

    # -------------------------------------------- NH-ADVISORY (LLM strategist)
    def _advisory_trigger(self):
        """Return a (trigger_name) if a strategic trigger fires THIS step, else
        None. Triggers: level-entry / impasse (watchdog) / novelty / low-HP
        crisis. Cheap edge-detection over already-tracked state."""
        A = self.atlas
        # (a) new depth we have not strategized about yet. Robust level-entry:
        # the first advisory-REACHED step at a new max depth (the exact
        # level_changed step is often spent in combat, so keying on the depth
        # rather than the one-step flag is what actually fires). Marked seen in
        # _advisory only on an issued consult, so a throttled miss retries.
        if A.depth >= ADVISORY_MINDEPTH and \
                A.depth not in self.advisory_depth_seen:
            return f"level: first strategy at depth {A.depth} " \
                   f"(hp {A.hp}/{A.hpmax} xp {A.xplvl})"
        # (b) impasse: the stall watchdog fired since we last looked
        if len(self.wd_fires) > self._adv_wd_seen:
            self._adv_wd_seen = len(self.wd_fires)
            return f"impasse: stall watchdog fired at depth {A.depth}"
        # (c) novelty: a thin-evidence species just became adjacent
        if self._adv_novel is not None:
            nm = self._adv_novel
            return f"novelty: unfamiliar species '{nm}' adjacent at " \
                   f"depth {A.depth}"
        # (d) low-HP crisis onset (rising edge)
        crisis = A.hp <= max(A.hpmax * CRISIS_HP, 6)
        if crisis and not self._adv_crisis_active:
            self._adv_crisis_active = True
            return f"low-HP crisis: hp {A.hp}/{A.hpmax} at depth {A.depth}"
        if not crisis:
            self._adv_crisis_active = False
        return None

    def _advisory(self, obs, msg):
        """The advisory-push dispatcher (NH_ADVISORY). Applies any active
        strategy bias, then (throttled) detects a strategic trigger and
        consults the live LLM strategist with the CONTEXT_SPEC package + pushed
        rule-base reminders. Sets a bias window the decision cascade honors.
        Returns an immediate action only for an active REST bias; else None.
        Safety layers (P0-P5) run BEFORE this — the strategist never overrides
        a tactical emergency, only the strategic explore/descend/rest/disengage
        choice."""
        A = self.atlas
        # ---- apply an active REST bias (immediate, only when safe) ----
        if self.steps < self._adv_rest_until and self._rest_here_ok() and \
                A.hp < 0.9 * A.hpmax:
            return "search"
        # ---- trigger + throttle ----
        trig = self._advisory_trigger()
        self._adv_novel = None
        if trig is None:
            return None
        if self.advisory_consults >= ADVISORY_MAX:
            return None
        if self.steps - self.advisory_last_step < ADVISORY_GAP:
            return None
        if self.store is None or RULEBASE is None:
            return None                          # no context / no reminders
        # ---- build the context package + pushed reminders ----
        import nh_store
        import nh_strategist
        try:
            context = nh_store.ctx_package(self, self.store)
        except Exception:                        # noqa: BLE001
            return None
        adj = self._adjacent_hostiles()
        rb_state = self._rb_state(
            monster_name=(adj[0].name if adj else None),
            adj_mobile=bool([m for m in adj if m.name not in C.IMMOBILE]))
        reminders = RULEBASE.reminders_text(rb_state)
        rec = nh_strategist.consult(context, reminders, trig,
                                    model=ADVISORY_MODEL)
        self.advisory_consults += 1
        self.advisory_last_step = self.steps
        self.advisory_depth_seen.add(A.depth)   # mark this depth strategized
        rec["step"] = self.steps
        rec["depth"] = A.depth
        rec["reminders"] = reminders
        self.advisory_log.append(rec)
        strat = rec.get("strategy")
        self._ev(f"ADVISORY consult#{self.advisory_consults} "
                 f"[{trig[:40]}] -> {strat or 'FAIL'} "
                 f"({rec.get('rationale', '')[:80]})")
        # ---- install the bias window the cascade honors ----
        win = self.steps + ADVISORY_GAP
        if strat == "DISENGAGE":
            self.wd_disengage_until = self.steps + WD_DISENGAGE
        elif strat == "REST":
            self._adv_rest_until = win
            if self._rest_here_ok() and A.hp < 0.9 * A.hpmax:
                return "search"
        elif strat == "DESCEND":
            self._adv_descend_until = win
        elif strat == "EXPLORE":
            self._adv_explore_until = win
        # FIGHT / PRESS_ON / FAIL -> no strategic redirect
        return None

    def _wield_diag(self, obs):
        """NH_WIELD_DIAG (s13): READ-ONLY. Scan the visible map for floor
        weapons, price each via the sheet, and track the best floor-weapon dpt
        seen vs the current wielded dpt across the episode. Distinguishes
        acquisition-bound (a better weapon lies on the floor, unlooted) from
        already-optimal (none exists). Emits notes only; returns nothing."""
        try:
            import numpy as _np
            import nh_sheet
            A = self.atlas
            if self.steps % 5 != 0:          # bound cost over long episodes
                return
            inv = self._inv(obs)
            opts = nh_sheet.attack_options(self.role, A.xplvl, inv,
                                           spells=None, pw=A.pw)
            cur = [o for o in opts if o[0] == "wield-current"]
            unarmed = [o for o in opts if o[0] == "unarmed"]
            cur_dpt = cur[0][3] if cur else (unarmed[0][3] if unarmed else 0.0)
            self._cur_wield_dpt_last = cur_dpt
            ph = nh_sheet._p_hit_melee(A.xplvl, self.role)
            W = nh_sheet.weapons()
            ga = _np.asarray(obs["obs"]["glyphs"])
            ax, ay = A.agent
            best_dpt, best_name, best_dist = 0.0, None, 99
            for g, (nm, ocl) in P._OBJ_NAME.items():
                if ocl != P.WEAPON_CLASS or not nm:
                    continue
                ys, xs = _np.nonzero(ga == g)
                if not len(ys):
                    continue
                wl = nh_sheet.weapon_lookup(nm)
                if not wl:
                    continue
                dpt = round(wl[1]["dsmall"] * ph, 2)
                for y, x in zip(ys.tolist(), xs.tolist()):
                    dist = max(abs(x - ax), abs(y - ay))
                    if dpt > best_dpt or (dpt == best_dpt and dist < best_dist):
                        best_dpt, best_name, best_dist = dpt, wl[0], dist
            if best_name is None:
                return
            if best_dpt > self._floor_wpn_max + 1e-9:
                self._floor_wpn_max = best_dpt
                self._floor_wpn_name = best_name
                self.note(f"FLOORWPN see {best_name} dpt {best_dpt} "
                          f"(cur wield {cur_dpt:.2f}, dist {best_dist})")
            if best_dpt - cur_dpt >= WIELD_MARGIN:
                self._floor_upgrade_steps += 1
                if self._floor_upgrade_steps in (1, 5, 25, 100):
                    self.note(f"FLOORWPN UPGRADE {best_name} dpt {best_dpt} > "
                              f"cur {cur_dpt:.2f} (dist {best_dist}, "
                              f"n={self._floor_upgrade_steps})")
        except Exception:               # noqa: BLE001 — pure diagnostic
            return

    _ACQ_AMMO = {"arrow", "elven arrow", "orcish arrow", "silver arrow", "ya",
                 "crossbow bolt", "rock", "flint stone", "boomerang"}

    def _weapon_upgrade_underfoot(self, obs, it):
        """Return the canonical weapon name to pick up if `it` (a name parsed
        from a "You see here ..." message) is a MELEE weapon that upgrades the
        current wield by WIELD_MARGIN, else None.

        LOAD-BEARING [ITEM_UNDER_@, weapon variant]: an item on the agent's OWN
        cell is hidden beneath the @ glyph, so _best_floor_weapon (a pure glyph
        read) goes blind the instant the agent steps onto the weapon -- exactly
        when it should pick it up. The "You see here <weapon>." message is the
        authoritative on-cell item sensor (same channel the food/armor/ammo
        underfoot pickups already use). Without this, a weapon-acquire detour
        walks the agent ONTO the mace and then oscillates off it forever
        (seed 746: 11 walks, 0 pickups)."""
        try:
            import nh_sheet
            A = self.atlas
            wl = nh_sheet.weapon_lookup(it)
            if not wl:
                return None
            name, row = wl
            if name in self._ACQ_AMMO or row["skill"] in nh_sheet.THROWN_SKILLS:
                return None
            ph = nh_sheet._p_hit_melee(A.xplvl, self.role)
            dpt = round(row["dsmall"] * ph, 2)
            inv = self._inv(obs)
            opts = nh_sheet.attack_options(self.role, A.xplvl, inv,
                                           spells=None, pw=A.pw)
            cur = [o for o in opts if o[0] == "wield-current"]
            un = [o for o in opts if o[0] == "unarmed"]
            cur_dpt = cur[0][3] if cur else (un[0][3] if un else 0.0)
            if dpt - cur_dpt < WIELD_MARGIN:
                return None
            return name
        except Exception:               # noqa: BLE001 — fail-safe, never a gate
            return None

    def _armor_slot(self, name):
        """Classify an armor name into a body-slot (mirror of _c2_scan_inv),
        or None if not wearable armor we model."""
        n = name.lower()
        if any(a in n for a in P.BODY_ARMOR):
            return "body"
        if any(a in n for a in P.HELMETS):
            return "helmet"
        if any(a in n for a in P.SHIELDS):
            return "shield"
        if "boots" in n or "iron shoes" in n:
            return "boots"
        if "gloves" in n or "gauntlets" in n:
            return "gloves"
        return None

    def _best_floor_armor(self, obs):
        """NH_LOOT (s15): (ac_bonus, name, slot, (x,y), dist) of the best floor
        armor glyph in view whose slot we DON'T already have filled (worn or
        already carried) — grabbing armor for an occupied slot is wasted weight.
        Pure glyph read + frozen armor AC table. Returns None if none. Failsafe:
        any error -> None (never a gate)."""
        try:
            import numpy as _np
            import nh_sheet
            A = self.atlas
            ga = _np.asarray(obs["obs"]["glyphs"])
            ax, ay = A.agent
            have = set(self.worn_slots) | {s for _, s, _ in self.wearable}
            best = None
            for g, (nm, ocl) in P._OBJ_NAME.items():
                if ocl != P.ARMOR_CLASS or not nm:
                    continue
                slot = self._armor_slot(nm)
                if slot is None or slot in have:
                    continue
                al = nh_sheet.armor_lookup(nm)
                if not al:
                    continue
                acb = al[1].get("ac", 0)
                if acb <= 0:
                    continue
                ys, xs = _np.nonzero(ga == g)
                if not len(ys):
                    continue
                for y, x in zip(ys.tolist(), xs.tolist()):
                    dist = max(abs(x - ax), abs(y - ay))
                    if best is None or acb > best[0] or (
                            acb == best[0] and dist < best[4]):
                        best = (acb, nm, slot, (x, y), dist)
            return best
        except Exception:               # noqa: BLE001 — fail-safe, never a gate
            return None

    def _efficient_loot(self, obs):
        """NH_LOOT (s15): the acquisition-bound meta-finding as a lever. Value
        every floor WEAPON (melee dpt gain vs current wield) and ARMOR (AC bonus
        for an unfilled slot); grab the best one IFF value/detour_cost clears
        LOOT_EFF_THRESH, under a per-LEVEL detour budget (LOOT_LEVEL_BUDGET) so
        descent never stalls (the s13 WIELDACQ confound). Underfoot/adjacent
        grabs are free. Returns a pickup / step action or None. The NH_WIELD
        (wield) + NH_ARMOR (wear) USE levers fire on the acquisition next cycles.
        Caller has gated safety (no adjacent hostile) + non-crisis hunger.
        Failsafe: any error -> None (never a gate)."""
        try:
            import nh_sheet
            A = self.atlas
            L = A.level
            # current melee dpt (best available now) for the weapon counterfactual
            inv = self._inv(obs)
            opts = nh_sheet.attack_options(self.role, A.xplvl, inv,
                                           spells=None, pw=A.pw)
            cur = [o for o in opts if o[0] == "wield-current"]
            un = [o for o in opts if o[0] == "unarmed"]
            cur_dpt = cur[0][3] if cur else (un[0][3] if un else 0.0)

            budget = self._loot_budget.get(A.key, 0)

            # STICKY TARGET (s15): commit to the chosen loot cell until reached,
            # unreachable, or loot_tries-capped. Without this, two comparable
            # items flickering in/out of LOS make the agent zigzag between them
            # and never actually pick either up (seed 16: two-handed sword vs
            # morning star -> 31 walk-steps, 0 pickups). The final grab happens
            # via the message-channel underfoot path once we stand on the cell.
            tgt = self._loot_target
            if tgt and tgt[0] == A.key:
                cell = tgt[1]
                tk = (A.key, cell)
                if cell != A.agent and self.loot_tries.get(tk, 0) < 8 \
                        and budget < LOOT_LEVEL_BUDGET:
                    path = L.bfs(A.agent, [cell],
                                 avoid=self._travel_avoid({cell}))
                    if path and len(path) <= LOOT_MAX_DETOUR:
                        prev = self._loot_progress.get(tk, 99)
                        if len(path) < prev:
                            self._loot_progress[tk] = len(path)   # progress
                        else:
                            self.loot_tries[tk] = \
                                self.loot_tries.get(tk, 0) + 1     # stuck
                        self._loot_budget[A.key] = budget + 1
                        self._goal("loot", f"walk {tgt[2]} {tgt[3]} d{len(path)}")
                        self.note(f"LOOT walk to {tgt[2]} {tgt[3]} "
                                  f"({len(path)} steps, value {tgt[4]:.2f}, "
                                  f"sticky, budget {budget + 1}/"
                                  f"{LOOT_LEVEL_BUDGET})")
                        return self._step_path(path)
                # reached / unreachable / capped: release and re-choose below
                self._loot_target = None

            cands = []   # (value, kind, name, cell)
            if self.role != "Monk":              # Monk: martial arts > weapon
                bf = self._best_floor_weapon(obs, melee_only=True)
                if bf:
                    dpt, wname, wcell, _ = bf
                    gain = dpt - cur_dpt
                    if gain >= WIELD_MARGIN:
                        cands.append((gain, "weapon", wname, wcell))
            ba = self._best_floor_armor(obs)
            if ba:
                acb, aname, _slot, acell, _ = ba
                cands.append((acb * LOOT_AC_WEIGHT, "armor", aname, acell))
            if not cands:
                return None
            best = None   # (value, kind, name, cell, path)  path=[] means underfoot
            for value, kind, name, cell in cands:
                tk = (A.key, cell)
                if self.loot_tries.get(tk, 0) >= 8:
                    continue          # unreachable/refused: stop thrashing
                if cell == A.agent:
                    path = []         # underfoot: free grab
                else:
                    path = L.bfs(A.agent, [cell],
                                 avoid=self._travel_avoid({cell}))
                    if not path:
                        continue
                    dist = len(path)
                    if dist > LOOT_MAX_DETOUR:
                        continue
                    if value / dist < LOOT_EFF_THRESH:
                        continue      # not worth the steps-off-descent
                    if budget >= LOOT_LEVEL_BUDGET:
                        continue      # level detour budget spent: descend
                if best is None or value > best[0]:
                    best = (value, kind, name, cell, path)
            if best is None:
                return None
            value, kind, name, cell, path = best
            tk = (A.key, cell)
            pk = "weapon" if kind == "weapon" else "armor"
            if not path:                         # underfoot pickup
                self.loot_tries[tk] = self.loot_tries.get(tk, 0) + 1
                self.pickup_kind = pk
                if kind == "weapon":
                    self._pickup_wpn_kw = name
                    self.wieldacq_fires += 1
                    self.loot_wpn_fires += 1
                else:
                    self.loot_arm_fires += 1
                self.loot_fires += 1
                self._loot_target = None
                self.queue_tag = "pickup"
                self._goal("loot", f"{kind} {name} v{value:.2f}")
                self.note(f"LOOT pickup {kind} {name} "
                          f"(value {value:.2f}, underfoot)")
                return "pickup"
            # walk one step toward the target; commit to it (sticky) so LOS
            # flicker can't make us zigzag, and charge the level detour budget.
            # Give up only when STUCK (dist not decreasing), not while approaching.
            self._loot_target = (A.key, cell, kind, name, value)
            prev = self._loot_progress.get(tk, 99)
            if len(path) < prev:
                self._loot_progress[tk] = len(path)
            else:
                self.loot_tries[tk] = self.loot_tries.get(tk, 0) + 1
            self._loot_budget[A.key] = budget + 1
            self._goal("loot", f"walk {kind} {name} d{len(path)}")
            self.note(f"LOOT walk to {kind} {name} ({len(path)} steps, "
                      f"value {value:.2f}, budget {budget + 1}/"
                      f"{LOOT_LEVEL_BUDGET})")
            return self._step_path(path)
        except Exception:               # noqa: BLE001 — fail-safe, never a gate
            return None

    def _best_floor_weapon(self, obs, melee_only=True):
        """(dpt, name, (x,y), dist) of the highest-priced weapon glyph in view,
        or None. melee_only drops ammo/thrown-primary (we don't detour for an
        arrow). Pure read of the served glyphs + frozen weapon table."""
        try:
            import numpy as _np
            import nh_sheet
            A = self.atlas
            ph = nh_sheet._p_hit_melee(A.xplvl, self.role)
            W = nh_sheet.weapons()
            ga = _np.asarray(obs["obs"]["glyphs"])
            ax, ay = A.agent
            best = None
            for g, (nm, ocl) in P._OBJ_NAME.items():
                if ocl != P.WEAPON_CLASS or not nm:
                    continue
                wl = nh_sheet.weapon_lookup(nm)
                if not wl:
                    continue
                name, row = wl
                if melee_only and (name in self._ACQ_AMMO
                                   or row["skill"] in nh_sheet.THROWN_SKILLS):
                    continue
                ys, xs = _np.nonzero(ga == g)
                if not len(ys):
                    continue
                dpt = round(row["dsmall"] * ph, 2)
                for y, x in zip(ys.tolist(), xs.tolist()):
                    dist = max(abs(x - ax), abs(y - ay))
                    if best is None or dpt > best[0] or (
                            dpt == best[0] and dist < best[3]):
                        best = (dpt, name, (x, y), dist)
            return best
        except Exception:               # noqa: BLE001
            return None

    def _weapon_acquire(self, obs):
        """NH_WIELDACQ (s13 pivot): close the acquisition gap. If a floor weapon
        beats the current melee dpt by WIELD_MARGIN and is reachable within
        WIELDACQ_RADIUS while safe, detour to it and pick it up; the NH_WIELD
        lever then wields it next cycle. Bounded detour + loot_tries cap =
        no-stall discipline (FOODACQ CARD S11-2). Returns an action or None."""
        try:
            import nh_sheet
            A = self.atlas
            L = A.level
            inv = self._inv(obs)
            opts = nh_sheet.attack_options(self.role, A.xplvl, inv,
                                           spells=None, pw=A.pw)
            cur = [o for o in opts if o[0] == "wield-current"]
            un = [o for o in opts if o[0] == "unarmed"]
            cur_dpt = cur[0][3] if cur else (un[0][3] if un else 0.0)
            bf = self._best_floor_weapon(obs, melee_only=True)
            if not bf:
                return None
            dpt, name, cell, dist = bf
            if dpt - cur_dpt < WIELD_MARGIN or dist > WIELDACQ_RADIUS:
                return None
            tk = (A.key, cell)
            if self.loot_tries.get(tk, 0) >= 8:
                return None
            if cell == A.agent:
                self.loot_tries[tk] = self.loot_tries.get(tk, 0) + 1
                self.wieldacq_fires += 1
                self.pickup_kind = "weapon"
                self._pickup_wpn_kw = name
                self.queue_tag = "pickup"
                self._goal("acquire", f"weapon {name} {cur_dpt:.2f}->{dpt:.2f}")
                self.note(f"WIELDACQ pickup {name} (melee dpt "
                          f"{cur_dpt:.2f}->{dpt:.2f}, +{dpt - cur_dpt:.2f})")
                return "pickup"
            path = L.bfs(A.agent, [cell], avoid=self._travel_avoid({cell}))
            if path and len(path) <= WIELDACQ_RADIUS:
                if len(path) <= 2:
                    self.loot_tries[tk] = self.loot_tries.get(tk, 0) + 1
                self._goal("acquire", f"walk to {name} d{len(path)}")
                self.note(f"WIELDACQ walk to {name} ({len(path)} steps, "
                          f"dpt +{dpt - cur_dpt:.2f})")
                return self._step_path(path)
            return None
        except Exception:               # noqa: BLE001 — fail-safe, never a gate
            return None

    def _wield_upgrade(self, obs):
        """NH_WIELD (s13): wield the best CARRIED weapon when its melee dpt
        beats the current wielded (or unarmed) melee dpt by WIELD_MARGIN.
        Returns a "wield" action (with the item letter queued for the follow-up
        prompt, mirroring the wear action) or None. Fail-safe: any error -> None
        (never a gate). Excludes Monk (martial arts) and thrown-primary weapons
        (darts/daggers we keep for the ranged game). Caller has already gated on
        safety (no adjacent hostile) + non-crisis hunger.

        Program note (s13): this lever's counterfactual is EMPTY on the corpus
        (and across all 15 roles, 77/77 role-episodes) because NetHack roles
        start wielding their best in-inventory weapon -> zero upgrades exist in
        inventory. The mechanism is nonetheless correct and fires on a synthetic
        scalpel+long-sword inventory (snapshot fixture); the 0-fire-in-play is a
        WORLD property (no better weapon is carried), not a broken lever. See
        DOCTRINE_CARDS_s13 / PROGRAM_FINDINGS 11th angle."""
        try:
            import nh_sheet
            A = self.atlas
            if self.role == "Monk":
                return None
            inv = self._inv(obs)
            opts = nh_sheet.attack_options(self.role, A.xplvl, inv,
                                           spells=None, pw=A.pw)
            cur = [o for o in opts if o[0] == "wield-current"]
            unarmed = [o for o in opts if o[0] == "unarmed"]
            cur_dpt = cur[0][3] if cur else (unarmed[0][3] if unarmed else 0.0)
            W = nh_sheet.weapons()

            def _thrown(name):
                wl = W.get(name)
                return bool(wl and wl["skill"] in nh_sheet.THROWN_SKILLS)
            # best carried NON-thrown-primary wield candidate
            cand = None
            for o in opts:                       # opts sorted desc by dpt
                if o[0] == "wield-carried" and not _thrown(o[2]):
                    cand = o
                    break
            if cand is None:
                return None
            gain = cand[3] - cur_dpt
            if gain < WIELD_MARGIN:
                return None
            letter = cand[1]
            self.wield_fires = getattr(self, "wield_fires", 0) + 1
            self._goal("wield", f"{cand[2]} (dpt {cur_dpt:.2f}->{cand[3]:.2f})")
            self.note(f"WIELD upgrade to {cand[2]} letter {letter} "
                      f"(melee dpt {cur_dpt:.2f}->{cand[3]:.2f}, +{gain:.2f})")
            self.queue = [letter]
            self.queue_tag = "wield"
            return "wield"
        except Exception:               # noqa: BLE001 — fail-safe, never a gate
            return None

    def _readiness_ratio(self, obs, depth):
        """RR(depth) via nh_sheet: (best_dpt*hp)/(band_dpt_p75*band_hp).
        Returns None on any error (fail-safe: a None never gates)."""
        try:
            import nh_sheet
            A = self.atlas
            sheet = nh_sheet.character_sheet(
                self.role, A.xplvl, A.ac, A.hp, A.hpmax,
                self._inv(obs), depth, spells=None, pw=A.pw)
            return sheet["readiness_ratio"]
        except Exception:              # noqa: BLE001 — fail-safe, never a gate
            return None

    def _ready_gate(self, obs, digger):
        """NH-READY_GATE: threat-conditional rest-to-buffer before descending.
        Fires only for a FRAGILE (non-digger) role about to drop into a floor
        where RR(d+1) < threshold, HP is still recoverable, and it is safe to
        rest. Returns 'search' (rest one turn) or None (proceed to descend).
        Bounded by the level rest budget so it can never stall to starvation."""
        if not C2_READY_GATE or digger or self.role not in READY_GATE_ROLES:
            return None
        A = self.atlas
        _dbg = _os.environ.get("NH_READY_DEBUG") == "1"
        if A.hp >= READY_HP_TARGET * A.hpmax:
            if _dbg:
                import sys as _s
                print(f"RG hp-full hp={A.hp}/{A.hpmax}", file=_s.stderr)
            return None                          # already buffered; descend
        if not self._rest_here_ok():
            if _dbg:
                import sys as _s
                print(f"RG unsafe hp={A.hp}/{A.hpmax} "
                      f"mob={len(self._mobile_hostiles())} "
                      f"hunger={A.hunger}", file=_s.stderr)
            return None                          # a mobile hostile / weak; go
        used = self.rest_budget.get(A.key, 0)
        cap = 800 if (self._mem_danger_depth is not None and
                      A.depth >= self._mem_danger_depth - 1) else 400
        if used >= cap:
            return None                          # bounded: never starve waiting
        rr = self._readiness_ratio(obs, A.depth + 1)
        if _dbg:
            import sys as _s
            print(f"RG check hp={A.hp}/{A.hpmax} rr={rr} used={used}",
                  file=_s.stderr)
        if rr is None or rr >= READY_RR_THRESH:
            return None                          # ready (or unknown); descend
        self.rest_budget[A.key] = used + 1
        self.ready_gate_fires += 1
        if used == 0:
            self._ev(f"READY_GATE: rest before D{A.depth + 1} "
                     f"(rr={rr:.2f}<{READY_RR_THRESH} hp {A.hp}/{A.hpmax} "
                     f"role {self.role})")
        self._goal("ready-rest", f"rr {rr:.2f} for D{A.depth + 1}")
        return "search"

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

    def _safe_level(self, obs):
        """NH_SAFELEVEL (s16): route to the nearest ISOLATED SAFE weak monster
        to farm early XP. Returns a step action or None. Pre-gated by the caller
        (early depth, xp<target, hp healthy, no adjacent hostile, budget left).
        The exchange model is the safety oracle: expected HP loss to the kill =
        species_dpt * species_ttk; we only engage monsters where that is a small
        fraction of current HP AND the per-turn dpt is low AND the prey is alone."""
        A = self.atlas
        L = A.level
        hostiles = self._mobile_hostiles()
        if not hostiles:
            return None

        def isolated(prey):
            return not any(
                o is not prey and
                max(abs(o.x - prey.x), abs(o.y - prey.y)) <= SAFELEVEL_ISO_R
                for o in hostiles)

        cand = []
        for m in hostiles:
            # never the dangerous species (never-melee), never same-speed-or-
            # faster hitters we cannot disengage from
            if self._never_melee(m) or m.speed > OUR_SPEED:
                continue
            # low-difficulty only (belt-and-suspenders on top of the dpt gate)
            if m.difficulty > max(2, A.xplvl):
                continue
            dpt = P.species_dpt(m.name, m.difficulty)
            if dpt > SAFELEVEL_MAX_DPT:
                continue
            ttk = P.species_ttk(m.name, m.difficulty,
                                role=self.role, xplvl=A.xplvl)
            exp_loss = dpt * ttk               # expected HP lost to kill it
            if exp_loss > SAFELEVEL_MARGIN * A.hp:
                continue
            if not isolated(m):
                continue
            cand.append((m, exp_loss))
        if not cand:
            return None
        # nearest safe prey first (cheapest detour off the descent line)
        cand.sort(key=lambda t: max(abs(t[0].x - A.agent[0]),
                                    abs(t[0].y - A.agent[1])))
        for m, exp_loss in cand:
            path = L.bfs(A.agent, [m.pos],
                         avoid=self._suspects() | (self._mcells() - {m.pos}))
            if path and len(path) <= SAFELEVEL_RADIUS:
                t0 = self.safelevel_turns.get(A.key, 0)
                self.safelevel_turns[A.key] = t0 + 1
                if t0 == 0:
                    self.note(f"SAFELEVEL engage {m.name} d{A.depth} "
                              f"xp{A.xplvl} exp_loss {exp_loss:.1f}/hp {A.hp} "
                              f"(safe early leveling)")
                self._goal("safelevel",
                           f"{m.name} xp{A.xplvl}->{SAFELEVEL_TARGET_XP}")
                return self._step_path(path)
        return None

    def _descend(self, obs):
        A = self.atlas
        L = A.level

        # NH-ADVISORY EXPLORE bias: strategist wants this level explored first.
        # Defer descent (let the P9 explore layer run) UNLESS already standing
        # on a down-stair — don't wrestle the agent off the stairs.
        if C2_ADVISORY and self.steps < self._adv_explore_until:
            if A.agent not in (set(L.stairs_down) | set(L.holes)):
                return None

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
            ra = self._ready_gate(obs, digger)   # NH-READY_GATE (session 8)
            if ra:
                return ra
            if self._should_rest() and self._rest_here_ok():
                self.rest_budget[A.key] = self.rest_budget.get(A.key, 0) + 1
                self._goal("rest", f"hp {A.hp}/{A.hpmax} on stairs")
                return "search"
            # PET UTILIZATION (NH_PET, s12): hold for the pet to reach an adjacent
            # cell so it follows us down; bounded so it can't stall (no-op if off).
            pa = self._pet_follow_wait()
            if pa:
                return pa
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
                    if not self._kick_ok():
                        # KICK_COST_GATE: too fragile to risk a broken leg ->
                        # defer this door (re-approachable with a key later).
                        self.door_giveup.add(door)
                        self.kick_dir = None
                        self.kick_count = 0
                        self.note(f"kick-gate defer {door} "
                                  f"(hp {A.hp}/{A.hpmax} role {self.role})")
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
                    if not self._kick_ok():
                        # KICK_COST_GATE: defer rather than risk a broken leg.
                        self.door_giveup.add((nx, ny))
                        self.kick_dir = None
                        self.kick_count = 0
                        self.note(f"kick-gate defer {(nx, ny)} "
                                  f"(hp {A.hp}/{A.hpmax} role {self.role})")
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

"""NH-E14 CHARACTER SHEET — the self-model asymmetry fix (layer: PERCEPTION).

MODEL: Fable 5 (max reasoning), Phase L session 3. Spec:
papers/balrog/experiments/NH-E14-role-modules/CHARACTER_SHEET_SPEC.md
(operator directives 2026-07-07 s2; "build = top of session-3 queue").

The asymmetry: monster dpt is empirical from a 160k-row corpus
(nh_exchange), while OUR dpt was two hardcoded constants
(nh_percept.py:98, 5.5 strong / 3.0 weak). This module makes the
self-model first-class:

  sheet = character_sheet(role, xplvl, ac, hp, hpmax, inventory, depth,
                          spells=..., pw=...)

  - ATTACK OPTIONS: current wield, every carried weapon, force bolt,
    best throw/launcher pair -> expected damage/turn x P(hit) vs the
    depth's band-representative threat.
  - DEFENSE: AC, current hp (effective HP), speed.
  - POWER INDEX      PI = best_dpt x hp        (offense x staying power)
  - THREAT INDEX     TI(d) = band_dpt(d) x band_hp(d)   (empirical, from
                     the same combat corpus the exchange model uses)
  - READINESS RATIO  RR = PI / TI(d)
    Interpretation is exact: RR = (hp/band_dpt) / (band_hp/best_dpt)
    = (turns the band monster needs to kill us) / (turns we need to
    kill it). RR > 1 => we win the representative exchange at depth d.
    P1 ("level up before going down") becomes computable: descend when
    RR(d+1) >= threshold (per-role, to be swept on dev).

  - COUNTERFACTUAL POWER: counterfactual_power(sheet_inputs, item_name)
    recomputes PI with a hypothetical wield/wear -> wield/wear/loot-
    detour decisions become power-delta arithmetic; the item-value
    perceptor upgrades from class heuristics to computed deltas;
    unidentified item => unknown delta => information value (E18).

Data provenance (all disclosed offline world model, honest-observation
contract intact — at runtime everything is a lookup table):
  - weapon damage dice + armor AC: parsed from the FROZEN local wiki KB
    (wiki_kb.sqlite 'Weapon'/'Armor' pages, sha256 in the manifest;
    NH-E13 add-only corpus) -> results/weapon_table.json /
    results/armor_table.json. NLE's objclass does not expose damage
    dice, so the KB is the source here; entries are three-way
    validatable against logged fight outcomes (NH-E13 protocol).
  - force bolt: 2d12, hit iff d20 < target AC + 10 (KB 'Spellbook of
    force bolt', read s3).
  - per-depth threat bands: results/depth_threat.json built from the
    c2_cache combat rows (adjacency-exposure-weighted species mix per
    depth; dpt from nh_percept.species_dpt = empirical blend; monster
    hp ~= 4.5 x mlevel source prior, same as species_ttk).

Build the tables:   python3 nh_sheet.py --build
Live probe demo:    python3 nh_sheet.py --demo <dev_seed> [step]
                    (nh_branch replay to step, sheet from served obs;
                    dev seeds only — forbidden-seed guard inherited)
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(HERE, "pylib"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

RESULTS = os.path.join(HERE, "results")
WEAPON_FN = os.path.join(RESULTS, "weapon_table.json")
ARMOR_FN = os.path.join(RESULTS, "armor_table.json")
BANDS_FN = os.path.join(RESULTS, "depth_threat.json")

# ------------------------------------------------------------ table builders

_DAVG = re.compile(r"\{\{davg\|([^}]+)\}\}")
_LINK = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


def _dice_avg(cell):
    """Sum of averages over every {{davg|n|m[|bonus]}} in a cell, plus
    bare +k modifiers written between templates (e.g. 'd6+1')."""
    total, found = 0.0, False
    for args in _DAVG.findall(cell):
        found = True
        nums = []
        for a in args.split("|"):
            a = a.strip()
            if a.startswith("bonus="):
                total += float(a[6:])
            elif re.fullmatch(r"[+-]?\d+", a):
                nums.append(int(a))
        # nums = [n1, m1, n2, m2, ...] pairs of NdM; odd trailing = bonus
        for i in range(0, len(nums) - 1, 2):
            total += nums[i] * (nums[i + 1] + 1) / 2.0
        if len(nums) % 2 == 1:
            total += nums[-1]
    # bare "+1" style additions outside templates
    stripped = _DAVG.sub("", cell)
    for k in re.findall(r"(?<![|\d])\+(\d+)", stripped):
        total += int(k)
    return total if found else None


def build_weapon_table():
    import sqlite3
    db = sqlite3.connect(os.path.join(HERE, "wiki_kb.sqlite"))
    wt = db.execute("select wikitext, sha256 from pages where "
                    "page_title='Weapon'").fetchone()
    text, sha = wt
    table = {}
    for row in text.split("|-"):
        cells = [c.strip() for c in row.strip().lstrip("|").split("||")]
        if len(cells) < 8:
            continue
        m = _LINK.search(cells[0])
        if not m:
            continue
        name = m.group(1).strip().lower()
        skill = _LINK.sub(lambda g: g.group(1), cells[1]).strip().lower()
        ds = _dice_avg(cells[6])
        dl = _dice_avg(cells[7])
        if ds is None:
            continue
        table[name] = {"skill": skill, "dsmall": round(ds, 2),
                       "dlarge": round(dl, 2) if dl is not None else ds}
    doc = {"provenance": {"page": "Weapon", "sha256": sha,
                          "extractor": "nh_sheet.build_weapon_table",
                          "model": "Fable 5 (max reasoning), s3"},
           "weapons": table}
    json.dump(doc, open(WEAPON_FN, "w"), indent=1, sort_keys=True)
    return doc


def build_armor_table():
    import sqlite3
    db = sqlite3.connect(os.path.join(HERE, "wiki_kb.sqlite"))
    wt = db.execute("select wikitext, sha256 from pages where "
                    "page_title='Armor'").fetchone()
    text, sha = wt
    table = {}
    for row in text.split("|-"):
        cells = [c.strip() for c in row.strip().lstrip("|").split("||")]
        if len(cells) < 5:
            continue
        m = _LINK.search(cells[0])
        if not m:
            continue
        name = m.group(1).strip().lower()
        # find the first small integer cell after the name = AC column
        ac = None
        for c in cells[1:6]:
            c2 = re.sub(r"<[^>]+>", "", _LINK.sub(lambda g: g.group(1), c))
            mm = re.fullmatch(r"(\d+)", c2.strip())
            if mm:
                v = int(mm.group(1))
                if 0 <= v <= 10:
                    ac = v
                    break
        if ac is not None:
            table[name] = {"ac": ac}
    doc = {"provenance": {"page": "Armor", "sha256": sha,
                          "extractor": "nh_sheet.build_armor_table",
                          "model": "Fable 5 (max reasoning), s3"},
           "armor": table}
    json.dump(doc, open(ARMOR_FN, "w"), indent=1, sort_keys=True)
    return doc


def build_depth_bands():
    """Per-depth threat band from the c2_cache combat corpus:
    adjacency-exposure-weighted mean/p75 species dpt and mean monster hp
    (4.5 x mlevel source prior — same prior species_ttk uses)."""
    import glob
    import gzip
    import collections
    import nh_common as C
    import nh_percept as P
    lvl = {name: l for (name, l, d, s, k) in
           [C._SPECIES[i] for i in range(len(C._SPECIES))]}
    per = collections.defaultdict(lambda: collections.Counter())
    for fn in sorted(glob.glob(os.path.join(RESULTS, "c2_cache",
                                            "*.json.gz"))):
        d = json.load(gzip.open(fn, "rt"))
        for row in d.get("combat", []):
            (step, dt, depth, hp, hpmax, xp, ac, adj, act, dmg, kill) = row
            if dt <= 0:
                continue
            for s in adj.split("|"):
                per[int(depth)][s] += dt
    bands = {}
    for depth in sorted(per):
        cnt = per[depth]
        total = sum(cnt.values())
        if total < 50:
            continue
        # DAMAGE-MASS weighting (w = exposure x dpt), not raw exposure:
        # adjacency turns are dominated by near-zero-dpt coexistence
        # (lichen standoffs, pets, peacefuls) which diluted v0's bands
        # (D5 p75 read 0.007 dpt — absurd). The band answers "what HURTS
        # us at this depth", so species weight = their damage mass.
        pairs = []          # (damage_mass, dpt, hp)
        for s, n in cnt.items():
            dpt = P.species_dpt(s)
            hp = 4.5 * max(1, lvl.get(s, 3))
            pairs.append((n * dpt, dpt, hp))
        wtot = sum(w for w, d, h in pairs)
        if wtot <= 0:
            continue
        wd = sum(w * d for w, d, h in pairs) / wtot
        wh = sum(w * h for w, d, h in pairs) / wtot
        # damage-mass-weighted p75 of dpt
        pairs.sort(key=lambda t: t[1])
        acc, p75 = 0.0, pairs[-1][1]
        for w, d, h in pairs:
            acc += w
            if acc >= 0.75 * wtot:
                p75 = d
                break
        bands[str(depth)] = {"n_turns": total, "dpt_mean": round(wd, 3),
                             "dpt_p75": round(p75, 3),
                             "hp_mean": round(wh, 2),
                             "species": len(cnt)}
    doc = {"provenance": {"corpus": "results/c2_cache combat rows",
                          "dpt": "nh_percept.species_dpt (empirical blend)",
                          "hp_prior": "4.5 x mlevel (source arithmetic)",
                          "model": "Fable 5 (max reasoning), s3"},
           "bands": bands}
    json.dump(doc, open(BANDS_FN, "w"), indent=1)
    return doc


# ------------------------------------------------------------------- lookups

_TABLES = {}


def _tbl(fn, builder, key):
    if fn not in _TABLES:
        if not os.path.exists(fn):
            builder()
        _TABLES[fn] = json.load(open(fn))[key]
    return _TABLES[fn]


def weapons():
    return _tbl(WEAPON_FN, build_weapon_table, "weapons")


def armor_tbl():
    return _tbl(ARMOR_FN, build_armor_table, "armor")


def bands():
    return _tbl(BANDS_FN, build_depth_bands, "bands")


def band(depth):
    b = bands()
    ds = sorted(int(k) for k in b)
    if not ds:
        return {"dpt_p75": 1.5, "hp_mean": 12.0, "dpt_mean": 0.8}
    d = min(max(depth, ds[0]), ds[-1])
    while str(d) not in b:          # nearest shallower with data
        d -= 1
    return b[str(d)]


_ART = re.compile(r"^(?:a|an|the)\s+", re.I)
_NOISE = re.compile(
    r"\b(?:blessed|uncursed|cursed|rusty|very rusty|thoroughly rusty|"
    r"corroded|burnt|rotted|poisoned|partly eaten|greased|fireproof|"
    r"rustproof|holy|unholy)\b|\s*\([^)]*\)$|^\d+\s+|[+-]\d+\s+")


def _clean(desc):
    s = _ART.sub("", desc.strip().lower())
    prev = None
    while prev != s:
        prev = s
        s = _NOISE.sub("", s).strip()
    return s


def weapon_lookup(desc):
    """inventory description -> (name, row) or None. Handles plurals
    ('2 daggers'), enchantment/erosion prefixes, '(weapon in hand)'."""
    s = _clean(desc)
    W = weapons()
    if s in W:
        return s, W[s]
    if s.endswith("s") and s[:-1] in W:
        return s[:-1], W[s[:-1]]
    for name in sorted(W, key=len, reverse=True):
        if re.search(r"\b" + re.escape(name) + r"s?\b", s):
            return name, W[name]
    return None


def armor_lookup(desc):
    s = _clean(desc)
    A = armor_tbl()
    if s in A:
        return s, A[s]
    for name in sorted(A, key=len, reverse=True):
        if re.search(r"\b" + re.escape(name) + r"\b", s):
            return name, A[name]
    return None


# ---------------------------------------------------------------- the sheet

STRONG_ROLES = {"Barbarian", "Valkyrie", "Samurai", "Knight", "Caveman",
                "Cavewoman", "Monk"}
LAUNCHER_AMMO = {"bow": "arrow", "crossbow": "crossbow bolt",
                 "sling": "sling ammo"}
THROWN_SKILLS = {"dagger", "knife", "spear", "javelin", "boomerang",
                 "dart", "shuriken"}
UNARMED_AVG = {"Monk": 4.5}         # martial arts; others d2
FORCE_BOLT_AVG = 13.0               # 2d12 (KB, s3)


def _p_hit_melee(xplvl, role, target_ac=6.0):
    """Source-flavored to-hit: d20 <= 10 + target_AC_neg... simplified
    v0.1 (documented approximation, to be calibrated against logged
    p_hit): base 11 + xplvl/2 + strong-role bonus vs d20."""
    bon = 11 + xplvl / 2.0 + (2 if role in STRONG_ROLES else 0)
    return max(0.10, min(0.95, bon / 20.0 - (target_ac - 6.0) / 20.0))


def _p_hit_spell(target_ac=6.0):
    """KB rule: hits iff d20 < target AC + 10 (monster AC ~6 early)."""
    return max(0.10, min(0.95, (target_ac + 10 - 1) / 20.0))


def attack_options(role, xplvl, inventory, spells=None, pw=0,
                   target_ac=6.0):
    """[(kind, letter, name, exp_dpt)] — expected damage per attack turn
    (dice avg x p_hit) per available option. inventory =
    [(letter, description, oclass)] (nh_common.inventory format)."""
    opts = []
    ph = _p_hit_melee(xplvl, role, target_ac)
    wielded = None
    carried_launch, ammo = {}, {}
    for (let, desc, ocl) in inventory:
        wl = weapon_lookup(desc)
        in_hand = "weapon in hand" in desc or "wielded" in desc
        if wl:
            name, row = wl
            dmg = row["dsmall"]
            if name in ("arrow", "elven arrow", "orcish arrow",
                        "silver arrow", "ya", "crossbow bolt", "rock",
                        "flint stone"):
                ammo[name] = (let, dmg)     # ammo carries launcher skill
            elif row["skill"] in LAUNCHER_AMMO:
                carried_launch[row["skill"]] = (let, name)
            else:
                kind = "wield-current" if in_hand else "wield-carried"
                opts.append((kind, let, name, round(dmg * ph, 2)))
                if in_hand:
                    wielded = name
                if row["skill"] in THROWN_SKILLS:
                    opts.append(("throw", let, name,
                                 round(dmg * ph, 2)))
        elif in_hand:
            wielded = _clean(desc)
    # launcher + ammo pairs (multishot ignored, v0.1 conservative)
    for skill, (let, lname) in carried_launch.items():
        want = LAUNCHER_AMMO[skill]
        for aname, (alet, admg) in ammo.items():
            if want in aname or (skill == "bow" and "arrow" in aname) or \
                    (skill == "sling" and aname in ("rock", "flint stone")):
                opts.append(("ranged", let, f"{lname}+{aname}",
                             round(admg * ph, 2)))
    # force bolt: known attack spell w/ enough Pw (cast layer gates the
    # rest); Wizards start with it — presence of spells dict decides
    if spells:
        for sname, meta in spells.items():
            if "force bolt" in sname and pw >= 5:
                opts.append(("spell", meta.get("letter", "?"),
                             "force bolt",
                             round(FORCE_BOLT_AVG *
                                   _p_hit_spell(target_ac), 2)))
    opts.append(("unarmed", "-", "unarmed",
                 round(UNARMED_AVG.get(role, 1.5) * ph, 2)))
    return sorted(opts, key=lambda o: -o[3])


def character_sheet(role, xplvl, ac, hp, hpmax, inventory, depth,
                    spells=None, pw=0, speed=12):
    """The self-model. Returns dict with options, defense, power index,
    threat index, readiness ratio (see module docstring for semantics)."""
    b = band(depth)
    opts = attack_options(role, xplvl, inventory, spells, pw)
    best = opts[0][3] if opts else 1.0
    pi = best * hp
    ti = max(0.05, b["dpt_p75"]) * b["hp_mean"]
    rr = pi / ti
    return {
        "options": opts,
        "defense": {"ac": ac, "hp": hp, "hpmax": hpmax, "speed": speed},
        "best_dpt": best,
        "power_index": round(pi, 1),
        "band": {"depth": depth, **b},
        "threat_index": round(ti, 1),
        "readiness_ratio": round(rr, 2),
        "survivable_turns": round(hp / max(0.05, b["dpt_p75"]), 1),
        "ttk_ours": round(b["hp_mean"] / max(0.1, best), 1),
    }


def counterfactual_power(role, xplvl, ac, hp, hpmax, inventory, depth,
                         item_desc, spells=None, pw=0):
    """Power delta if we wielded/wore item_desc (seen on floor or in
    dossier). Returns (kind, delta_pi, delta_rr, note) or None if the
    item is unknown to the tables (=> information value, E18)."""
    base = character_sheet(role, xplvl, ac, hp, hpmax, inventory, depth,
                           spells, pw)
    wl = weapon_lookup(item_desc)
    if wl:
        name, row = wl
        inv2 = list(inventory) + [("*", f"{name} (weapon in hand)", 2)]
        alt = character_sheet(role, xplvl, ac, hp, hpmax, inv2, depth,
                              spells, pw)
        return ("wield", round(alt["power_index"] - base["power_index"], 1),
                round(alt["readiness_ratio"] - base["readiness_ratio"], 2),
                f"{name}: dpt {base['best_dpt']} -> {alt['best_dpt']}")
    al = armor_lookup(item_desc)
    if al:
        name, row = al
        # v0.1: AC delta only (worn-slot replacement not modeled); AC
        # does not enter PI yet -> report as defense note
        return ("wear", 0.0, 0.0,
                f"{name}: AC bonus {row['ac']} (slot economics v0.2)")
    return None


# ------------------------------------------------------------------ CLI

def _demo(seed, upto=120):
    """Live probe on a DEV seed: drive the real agent to `upto` steps on
    nh_branch's verified-deterministic stack, then compute the sheet
    from the SERVED obs (inventory arrays + blstats — honest-observation
    contract). Read-only; forbidden-seed guard inherited."""
    import warnings
    warnings.filterwarnings("ignore")
    import nh_branch as B
    import nh_common as C
    import nh_harness as H
    from nle import nethack as nh
    from nh_agent import DiveAgent
    B.assert_dev_seed(seed)
    env = H.make_env()
    obs, _ = env.reset(seed=seed)
    space = list(env.env.language_action_space)
    agent = DiveAgent(log=lambda *a, **k: None)
    agent.set_actions(space)
    for _ in range(upto):
        a = agent.act(obs)
        obs, r, term, trunc, info = env.step(a if a in space else "search")
        if term or trunc:
            break
    raw = obs["obs"]
    bl = raw["blstats"]
    inv = C.inventory(obs)
    role = agent.role or "Valkyrie"
    spells = getattr(agent, "cast_spells", None)
    sh = character_sheet(
        role, int(bl[nh.NLE_BL_XP]), int(bl[nh.NLE_BL_AC]),
        int(bl[nh.NLE_BL_HP]), int(bl[nh.NLE_BL_HPMAX]), inv,
        int(bl[nh.NLE_BL_DEPTH]),
        spells={s: {"letter": v[0] if isinstance(v, (list, tuple))
                    else "?"} for s, v in (spells or {}).items()}
        if spells else None,
        pw=int(bl[nh.NLE_BL_ENE]))
    env.close()
    print(f"# seed {seed} step<= {upto} role {role} "
          f"inv={[(l, d[:28]) for l, d, o in inv]}")
    print(json.dumps(sh, indent=1))
    for l, d, o in inv:
        pass
    return sh


if __name__ == "__main__":
    if "--build" in sys.argv:
        w = build_weapon_table()
        a = build_armor_table()
        b = build_depth_bands()
        print(f"weapon_table: {len(w['weapons'])} weapons")
        print(f"armor_table: {len(a['armor'])} pieces")
        print(f"depth_threat: depths {sorted(b['bands'])} ")
    elif "--demo" in sys.argv:
        i = sys.argv.index("--demo")
        _demo(int(sys.argv[i + 1]),
              int(sys.argv[i + 2]) if len(sys.argv) > i + 2 else 120)

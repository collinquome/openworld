"""NH-E37 — PER-CLASS EARLY-GAME OPENING CARDS (compiled from expert demonstration).

MODEL: claude-opus-4-8 (max thinking), Phase L NH-E37. Runtime identity verified
at session open (system-prompt id = claude-opus-4-8, matches intended assignment;
Fable at usage cap).

WHAT THIS IS
  Each expert early-game routine mined by e37_extract.py (alt.org ttyrecs) is,
  when decomposed, a SUBSET of levers the program has ALREADY built and tested
  in isolation (NH_CAST, NH_RANGED, NH_FOODACQ, NH_PET, NH_ELBERETH, NH_PACE,
  NH_ANTIFAINT, prayer). Individually each is null-to-directional; the FULLY
  STACKED arm is NEGATIVE (levers interact badly combined — PROGRAM_FINDINGS).
  The one UNTESTED composition is the per-class one: give each rolled class ONLY
  the small lever-subset ITS experts actually use, class-tuned. That is the
  NH_OPENING hypothesis. This module is the compiled policy table + the harness
  composer that turns a seed's rolled class into that class's opening env.

WHY HARNESS-LEVEL (not an in-agent branch): guaranteed bit-identical when OFF
  (agent code untouched) and safe to run alongside a concurrent agent sharing
  nh_agent.py. NH_OPENING=1 in the TEST arm => the composer sets the class's
  lever env vars BEFORE the env/agent import; REF sets none. Same seed => same
  rolled class (deterministic at reset), so "the agent runs its rolled class's
  expert opening routine" holds exactly.

provenance: DUAL. knowledge = DEMONSTRATION (public alt.org expert ttyrecs, see
  e37_extract.py / E37_PLAYBOOK.md, cited per card). insight-origin = OP (NH-E37
  directive). The lever SEMANTICS are the program's own prior builds (wiki/OP).

Baseline REF = frozen C2.1 (c2_env.sh): NH_FOOD2 NH_PRAYFIX NH_LOS NH_TOPO NH_GUARD.
TEST = REF + the rolled class's OPENING_CARDS[class] env.
Clean-protocol: OFFLINE-derived policy; scored runs are pure code.
"""
import os

# Frozen C2.1 baseline every arm carries (the program's committed baseline).
REF_ENV = {
    "NH_FOOD2": "1", "NH_PRAYFIX": "1", "NH_LOS": "1",
    "NH_TOPO": "1", "NH_GUARD": "1",
}

# Per-class opening cards. Each value is the DELTA env applied on top of REF_ENV
# in the TEST arm. Keys are canonical role names (role_census / RANK_TO_ROLE).
# "cite" = the ttyrec(s) the routine was read from; "why" = the demonstration
# signal (see E37_PLAYBOOK.md for the ordered routine + evidence turns).
OPENING_CARDS = {
    # ---- FRAGILE CASTER: cautious, cast-economy, panic-Elbereth, corpse-bank.
    # nnnet (gnomish Wizard): casts force bolt, engraves Elbereth 5x, banks
    # newt/jackal corpses BEFORE Hungry, altar-BUC 4x, slow dive (D5 @ T1505).
    "Wizard": {
        "env": {"NH_CAST": "1", "NH_CASTHUNGER": "1", "NH_ELBERETH": "1",
                "NH_FOODACQ": "1", "NH_ANTIFAINT": "1", "NH_PACE": "1"},
        "cite": ["nnnet__2026-07-08.00_18_03"],
        "why": "force-bolt economy (+2.41 proven) + Elbereth panic + opportunistic "
               "corpse-bank + cautious pace (expert D5@T1505 vs our fast dive)",
        "baked": True,
    },
    # ---- STRONG MARTIAL: ranged softening, fast dive, corpse-bank, Elbereth.
    # rschaff (human Samurai): 68 throws (bow/shuriken), engraves Elbereth 5x,
    # eats early newt corpses, aggressive dive (D5 @ T859 / D6 @ T1134), prays
    # early (T769). No wield-upgrade (starts weapon-optimal).
    "Samurai": {
        "env": {"NH_RANGED": "1", "NH_FOODACQ": "1", "NH_ELBERETH": "1",
                "NH_ANTIFAINT": "1"},
        "cite": ["rschaff__2026-07-06.02_42_54", "rschaff__2026-07-07.23_22_57"],
        "why": "ranged-first (68 throws) + early corpse-eat + Elbereth + fast "
               "tempo; strong class dives, does not defer",
        "baked": True,
    },
    # ---- FRAGILE PRAYER-FORWARD: heavy corpse-eating, early prayer, cautious.
    # DaveT (human Priest): 13 corpse-eats in-window, prays at T1549 (short
    # prayer timeout -> prays freely early), wears armor at T182, slow dive
    # (D5 @ T1109). BUC-detect is innate (no altar needed).
    "Priest": {
        "env": {"NH_FOODACQ": "1", "NH_ELBERETH": "1", "NH_ANTIFAINT": "1",
                "NH_PACE": "1"},
        "cite": ["DaveT__2026-07-08.00_11_28"],
        "why": "prayer-forward (Priest short timeout) + heavy safe-corpse eat "
               "(13 eats) + Elbereth + cautious pace",
        "baked": True,
    },
    # Priestess = same doctrine as Priest.
    "Priestess": {
        "env": {"NH_FOODACQ": "1", "NH_ELBERETH": "1", "NH_ANTIFAINT": "1",
                "NH_PACE": "1"},
        "cite": ["DaveT__2026-07-08.00_11_28"],
        "why": "same as Priest",
        "baked": False,
    },
    # ---- STRONG BRUISER: rock/sling ranged, pet-forward, corpse-bank.
    # Zapwai (Caveman): 63 throws (rocks), 76 pet interactions, banks corpses,
    # moderate dive (D5 @ T1494). EXPLORATORY (not in baked-first set).
    "Caveman": {
        "env": {"NH_RANGED": "1", "NH_PET": "1", "NH_FOODACQ": "1",
                "NH_ANTIFAINT": "1"},
        "cite": ["Zapwai__2026-07-08.00_12_26"],
        "why": "rock/sling ranged (63 throws) + pet-forward (76) + corpse-bank",
        "baked": False,
    },
    "Cavewoman": {
        "env": {"NH_RANGED": "1", "NH_PET": "1", "NH_FOODACQ": "1",
                "NH_ANTIFAINT": "1"},
        "cite": ["Zapwai__2026-07-08.00_12_26"],
        "why": "same as Caveman",
        "baked": False,
    },
    # ---- STRONG PET-FORWARD: pony pet, ranged, corpse-bank.
    # Langmuir (human Knight): 40 pet(pony) interactions, moderate dive.
    "Knight": {
        "env": {"NH_PET": "1", "NH_RANGED": "1", "NH_FOODACQ": "1",
                "NH_ANTIFAINT": "1"},
        "cite": ["Langmuir__2026-07-08.00_50_17"],
        "why": "pony pet-forward (40) + ranged + corpse-bank",
        "baked": False,
    },
}

# Classes with a clear expert game in the corpus but NO baked card yet:
GAP_CLASSES = ["Valkyrie", "Barbarian", "Tourist", "Healer", "Ranger",
               "Monk", "Rogue", "Archeologist"]
# NOTE Valkyrie/Barbarian/Tourist/Healer = [GAP]: no expert ttyrec acquired
# this session (alt.org early-game archives are class-varied but these players
# were not surfaced; the extractor + fetch recipe generalizes — see HANDOFF).


def resolve_class(seed):
    """Rolled class for a dev seed via the deterministic role census."""
    import role_seeds
    by = role_seeds.load()
    for role, seeds in by.items():
        if seed in seeds:
            return role
    return None


def opening_env_for(seed, arm):
    """Return the full env dict for (seed, arm).
    arm='REF' -> REF_ENV only. arm='TEST' -> REF_ENV + the class opening card
    (empty delta if the class has no card => TEST==REF for that class)."""
    env = dict(REF_ENV)
    role = resolve_class(seed)
    card = OPENING_CARDS.get(role)
    if arm == "TEST" and card:
        env.update(card["env"])
    return env, role, (card is not None)


if __name__ == "__main__":
    import sys
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 811
    for arm in ("REF", "TEST"):
        env, role, has = opening_env_for(seed, arm)
        print(f"seed={seed} arm={arm} role={role} has_card={has}")
        print("  env:", " ".join(f"{k}={v}" for k, v in sorted(env.items())))

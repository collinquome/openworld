# Doctrine Cards — NH-E41 CORRIDOR-FUNNEL ANTI-PACK COMBAT
MODEL: claude-opus-4-8 (max thinking). Runtime identity VERIFIED at open
(system-prompt id = claude-opus-4-8; Fable at usage cap). All E41 artifacts
stamped claude-opus-4-8[max]. Fork aleph/fable-nethack, worktree wt-fable-nethack.
insight-origin: OP (operator directive — "improve the avg NetHack score through
further experimentation"); the specific lever = E36's replay-winner CORRIDOR made
to fire PROACTIVELY against the live spike/burst death mechanism.

## DUAL PROVENANCE
- insight-origin = OP: improve mean progression; a genuinely-untested lever with a
  sound mechanism against the actual wall (the ~Dlvl5 spike death).
- knowledge = OUR OWN corpus: E36 (§NH-E36) found CORRIDOR (funnel-and-fight) BEATS
  the shipped KITE lever in robust 18-seed replay (survival 0.50 vs 0.28) but
  deployed as a MECHANICAL NULL — its signature never fired live (signature-fidelity
  gap). E38's spike/burst death mechanism (killed in ~one exchange at ~35% HP). The
  hypothesis: the burst is driven by MULTIPLE simultaneous attackers (a pack); the
  classic counter is choke-point fighting (1-tile corridor/doorway → only one
  attacks per turn).
- demonstration arbiter = classic NetHack doctrine (funnel packs into a corridor).

## CARD E41-1 — the lever (NH_FUNNEL, default-OFF, bit-identical)
BUILD (nh_agent.py, additive + flag-guarded — bit-identical OFF, 4-way verified):
- flag C2_FUNNEL = _flag("NH_FUNNEL"); tunables FUNNEL_RADIUS(3)/FUNNEL_PACK(2)/
  FUNNEL_BURST_FRAC(0.30)/FUNNEL_MAXDIST(4)/FUNNEL_HP_HI(1.01=off).
- _funnel(obs, adj): PACK = ≥2 non-pet mobile hostiles within Chebyshev radius 3;
  BURST gate = fire iff Σ species_dpt(pack) ≥ FUNNEL_BURST_FRAC·HP (the spike gate,
  fires at FULL HP against a lethal pack — the fix for E36's "hp-not-full" signature
  that never fired because packs engage at full HP); retreat via L.bfs to the nearest
  reachable Topology.choke ≤ MAXDIST steps (nh_common corridor/doorway cells). Fires
  at P4.97, ABOVE normal open-combat (_combat), BELOW every P3 emergency (crisis-zap/
  heal/pray/flee already ran). Emits a "FUNNEL retreat" note per fire.
- CALIBRATION LESSON (E36 sibling, quantified): the literal "HP not-full" trigger
  BAILED 18/18 live calls (diag_funnel.py) because the strong config arrives at
  packs at hp_frac=1.0. Proactive choke-fighting MUST fire at full HP (you go to the
  choke BEFORE the pack hits). For the validation block the burst gate was opened
  MAX-FIRE (burst_frac 0.0) to give the mechanism every chance to fire.

## CARD E41-2 — paired validation (n=16 dev seeds 101-116, cap 2000)
REF=C2.1 (NH_FOOD2/PRAYFIX/LOS/TOPO/GUARD) vs TEST=+NH_FUNNEL (max-fire). One
seed per process (s8 leakage). PRIMARY KPI = progression mean Δ + paired CI.
- **Δ prog = −0.0054, 95% bootstrap CI [−0.0234, +0.0065] — INCLUDES 0 (NULL).**
  2 TEST-better / 2 worse / 12 tie. depth Δ −0.25. deaths 13/16 both.
- **FIRES live: 7/16 seeds, 18 fires** (beats E36's 0 — not a mechanical/signature
  null). But leave-one-out: dropping seed 108 (Archeologist D11→D6, −0.126) FLIPS Δ
  positive → the slight negative is ONE-SEED (the on-fire mirage, caught by LOO).
- **Multi-attacker rate went the WRONG way: REF 0.0091 → TEST 0.0294** (Δ +0.020);
  seed 116 (Valkyrie) one fire → ma 4.7% → 30.4% (retreat backed into a swarm).
- **Addressable scenario is RARE: faced-2+-pack rate 3.3% (269/8232);** ≥2 adjacent
  rarer. The one pack-heavy seed (113 Wizard, 19.7% faced-2) fired 0× (no reachable
  choke). Lethal spikes are SINGLE strong/fast monsters (giant spider/ant/kobold).

## CARD E41-3 — per-role table (n=16)
```
role         n  REFprog  TESTprog   dP      fires  firedSeeds
Archeologist 3  0.1986   0.1566   -0.0419    3     1/3   (seed108 D11->D6 = the LOO outlier)
Barbarian    1  0.0265   0.0265   +0.0000    0     0/1
Caveman      1  0.0000   0.0000   +0.0000    0     0/1
Healer       2  0.0239   0.0239   +0.0000    0     0/2
Knight       1  0.0977   0.0977   +0.0000    0     0/1
Monk         1  0.0212   0.0185   -0.0027    4     1/1
Priest       1  0.0977   0.0977   +0.0000    0     0/1
Priestess    1  0.1256   0.1613   +0.0357    3     1/1   (modest gain, endogenous)
Rogue        1  0.0154   0.0212   +0.0058    3     1/1   (modest gain, endogenous)
Valkyrie     2  0.0196   0.0196   +0.0000    2     2/2   (fired, no prog change; 116 ma-swarm)
Wizard       2  0.0227   0.0227   +0.0000    3     1/2
```

## HONEST READ — does choke-point fighting beat the pack-burst spike?
NO — not because choke-fighting is wrong, but because **we do not die to packs.**
Three quantified factors: (a) the multi-attacker state is RARE (3.3%; the config's
LOS/topology/corridor pathing already engages monsters single-file, so surrounds
rarely form); (b) on the one pack-heavy seed the choke was not reachable in time; (c)
when it fires it does NOT collapse burst to 1-on-1 — multi-attacker rate INCREASES
(retreat converges the pack; 116: 4.7%→30.4%) and it perturbs the trajectory into
different RNG deaths (108 catastrophe). This is the 15th converging angle on
capability-boundedness, at the tactical-positioning layer: the wall is
survive-the-traversal CAPABILITY (out-trading the FIRST kill-zone monster an
under-leveled character meets), not multi-attacker positioning. The under-leveled
character loses the fight it actually faces — usually a single strong monster, and
when a pack does form, 1-on-1-at-a-choke still doesn't save an under-geared char.
NH_FUNNEL ships flag-OFF (bit-identical, snapshot GREEN 21/21) as a validated
negative result + reusable scaffold. No MILESTONE/GIF (no funnel-fight saved a run
baseline lost — the reverse happened on 108 and 116).

## RECIPE (reproduce)
```
cd work/fable_nethack   # run env (has pylib/nle); code mirrors wt-fable-nethack
# paired block (max-fire calibration), foreground one-seed-per-process, resumable:
env NH_STEPCAP=2000 NH_FUNNEL_BURST_FRAC=0.0 NH_FUNNEL_HP_HI=1.01 \
    PYTHONPATH=pylib python3 e41_block.py 101 102 ... 116
python3 e41_analyze.py                       # Δ+CI, fires, faced-2+ rate, LOO, fired-split
# firing diagnostic (why it fires/bails; pack-encounter distribution):
env NH_FOOD2=1 NH_PRAYFIX=1 NH_LOS=1 NH_TOPO=1 NH_GUARD=1 NH_FUNNEL=1 \
    PYTHONPATH=pylib python3 diag_funnel.py <seed> 2000
# regression gate (flags OFF): python3 snapshot_suite.py  -> SUITE GREEN 21/21
# bit-identical check: REF seed 101 prog == 0.09770935198701912 (pre-edit)
```
Artifacts: results/e41_funnel.jsonl (32 rows, 16 pairs). Dev seeds 101-116 only
(6000-6099/7000-7024 UNTOUCHABLE). Flag default-OFF; ship-shape = scaffold, not on.

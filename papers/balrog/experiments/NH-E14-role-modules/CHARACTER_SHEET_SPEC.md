# CHARACTER SHEET MODEL + COUNTERFACTUAL POWER (operator directives 2026-07-07 s2)

MODEL: Fable 5 (max reasoning) — registration; build queued top of session 3
(perceptor layer LEADS Phase L per the operator reweight).

## 1. Character sheet (the self-model asymmetry fix)
Monster dpt is empirical from 160k rows; OUR dpt is two hardcoded constants
(nh_percept.py:98). Build the self-model first-class:
- per available ATTACK OPTION (current wield, each carried weapon, force
  bolt, best throw) → expected damage/turn + to-hit vs a reference threat
  (source arithmetic + our own logged fight outcomes — per-fight data
  exists in the corpus);
- defense: AC, effective HP, speed; verb availability;
- → POWER INDEX. Power index vs the depth's empirical threat band =
  **READINESS RATIO** — P1 ("level up before going down") becomes
  COMPUTABLE instead of heuristic: descend when ratio ≥ threshold
  (per-role, swept on dev).

## 2. Counterfactual power ("how strong could I be with item X")
power_index(current) vs power_index(hypothetical: wielding/wearing seen
item X) for every item in view or dossier:
- wield/wear/loot-detour decisions become power-delta arithmetic
  ("long sword seen: +38% melee output → worth a 40-step detour at
  current risk");
- item-value perceptor upgrades from class heuristics to computed deltas;
- revaluation triggers fire on big deltas ("that armor on D2 is now worth
  the trip");
- unidentified weapon = unknown delta = information value (feeds E18
  curiosity objectives).

Deliverables: nh_sheet.py (perceptor+model), readiness-ratio logging in
every dev episode, WIELD/ARMOR doctrine built ON TOP of power deltas
(closes the top coverage-matrix mass cells), paired dev validation.

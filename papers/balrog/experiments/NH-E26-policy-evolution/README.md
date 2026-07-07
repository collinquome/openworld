# NH-E26 — Policy-function evolution (REGISTERED, Phase L; operator directive 2026-07-07, source: FunSearch pattern)

MODEL: Fable 5 (max reasoning) — registration, session 2. (Handoffs logged here.)

Pattern (FunSearch): LLM as MUTATION OPERATOR over small programs; an automatic
evaluator selects. Bounded to SINGLE FUNCTIONS — FunSearch's sweet spot — never
whole-agent evolution.

## Target functions (the hot small functions of the decision layer)
- readiness gate (P1/P4 descend check)
- threat-cost function (combat EV / threat budget)
- descent pacing (rest thresholds × depth)
- kite heuristic (choke selection + engage/disengage radii)

## Loop
1. POPULATION of variants per function (incumbent + LLM mutations; each variant
   a self-contained function with its rule-card header).
2. CHEAP FITNESS = E20 lab-scenario batteries (des-file micro-scenarios make
   evaluation nearly free; n=50+ per scenario, seeds from the lab range).
3. ISLANDS for diversity (2–3 independent populations, periodic migration).
4. Survivors must STILL pass paired dev validation + the drop-rule before
   shipping — lab fitness sets the prior, the dev block confirms (same transfer
   gate as all E20 work).

## Logging
Every mutation logged {parent, diff, model, fitness, generation}; the
mutation-tree is the experiment artifact. Model provenance per mutation
(the mutation model may differ from the analysis model).

Status: registered; blocked on E20 lab bootstrap (the evaluator). First
candidate function: readiness gate (E12's 59% arrival-constraint mass makes it
the highest-value target).

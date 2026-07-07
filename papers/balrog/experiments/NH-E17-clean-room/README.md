# NH-E17 — Clean-room rebuild from knowledge artifacts (REGISTERED; runs at Phase L exit, before/alongside Phase E)

MODEL: Fable 5 (max reasoning) — design + registration. (Handoffs logged here if a successor model continues this experiment.)

**Operator directive (2026-07-07).** Once Phase-L exit criteria are met and
"what works" is known, a FRESH agent context (spawned by the operator/coordinator
at that time — flag them when exit criteria are met) builds a NEW implementation
from scratch using ONLY the distilled knowledge artifacts:

- rule cards (in-code cards are readable as text; the rebuild agent may read
  cards/docstrings quoted in docs, never the module source around them)
- priors files (`papers/balrog/priors/`)
- lesson tables (NH-E12 retrospectives)
- experiment READMEs + reports (C2 report, PHASE_L report, program registry)
- the NH-E13 wiki KB

**Hard rule:** the rebuild agent may read docs, NEVER source. No copying modules.

Then both agents — incumbent and rebuild — run the SAME fresh dev block
(a never-touched dev seed range, declared at rebuild time). The comparison is
the ultimate code-as-bridge test:

- rebuild ≈ incumbent ⇒ the documentation genuinely contains the knowledge;
  the program's knowledge is portable and complete.
- gap ⇒ tacit knowledge trapped in code that the docs failed to capture —
  itemize what was missing (each miss is a documentation defect to fix).

Either result is a first-class finding about knowledge representation in
code-weights systems.

**Standing obligation on Phase L (in force NOW):** every rule card and lesson is
written as if it must reconstruct the system without its author — mechanism,
constants, scope, trigger conditions, and integration point all explicit. A card
that only makes sense next to its code fails this test by definition.

## Status log
- 2026-07-07: registered. Runs at Phase L exit; do not start early.

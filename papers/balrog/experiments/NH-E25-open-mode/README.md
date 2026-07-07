# NH-E25 — Open-mode play (REGISTERED, Phase L; operator directive 2026-07-07, source: Cleese 1991 open/closed modes)

MODEL: Fable 5 (max reasoning) — registration, session 2. (Handoffs logged here.)

Premise (Cleese): creativity needs the OPEN mode — playful, unhurried, tolerant
of not-solving — which is a different regime from the CLOSED execution mode the
agent (and this program's dev loop) normally runs in. Three components, each
with a measurable dividend:

## (a) Unstructured play sessions
Scheduled dev-seed sessions with NO objectives, NO gold stars, NO scoring — the
intuition layer just plays and notices. **Metric: discovery yield** (mechanics
pinned, relations found, curiosity hypotheses generated) **vs an equal-budget
structured-practice control.** PRE-REGISTERED BOTH DIRECTIONS: open-mode may
out-discover structured practice (Cleese thesis) or structured practice may win
(deliberate-practice thesis) — either result is a finding. Sessions logged like
deliberate-play transcripts (dev/gym seeds only; discoveries enter policy only
through the standard card→validation pipeline).

## (b) Second-solution rule (gym)
Past the first adequate winning line in a gym scenario, KEEP SEARCHING for a
better one (Cleese: don't take the first idea just because it relieves the
discomfort of not-solving). **Metric: first-found vs best-found quality delta**
(damage taken, turns, resources spent) — the measurable creativity dividend.
Implementation: gym solver gets a `second_solution` budget knob; both lines are
recorded in the scenario record.

## (c) Pondering passes
Reflection consultations with explicitly NO decision required — the package
says "nothing is asked of you; just notice things." **Metric: what pondering
surfaces that decision-pressure consultations don't** (hypotheses/relations per
pass, compared against E18 dot-connector passes on the same episodes).
Consultations logged verbatim per CONTEXT_SPEC.

Status: registered; not started. Depends on: E-NH6 gym harvest (for b),
E18 reflection loop (for c). Folder: results/ for session transcripts + yield
tables.

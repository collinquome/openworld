# NH-E21b Composition-Worlds Ablation — BLIND ARM

**Arm:** blind / quarantined fresh-context agent (no intuition-layer priors).
**Worktree:** `wt-e21b-blind` · branch `aleph/e21b-blind-ablation`.
**Runtime model (this agent):** `claude-opus-4-8`, high effort ("max thinking").
**In-loop model (arms 2–4):** `claude-haiku` via the Claude CLI over subscription
(OAuth) auth — the environment `ANTHROPIC_API_KEY` is invalid (401), so it is
stripped and the CLI login is used instead.
**Date:** 2026-07-07.

---

## 1. Quarantine audit — exactly what I read (and did not)

This arm tests whether an agent **without** the intuition layer's accumulated
knowledge can solve composition worlds. To keep the test valid I did **not** read
any solution, transcript, or mechanic-answer.

**Files I READ (harness / framework only — allowed):**
- `openworld/world.py`, `agent.py`, `memory.py`, `llm.py`, `state.py` — the pure
  `(state,action)->state` framework primitives + `MemoryStore` (the memory arms
  are grounded in the real `MemoryStore`).
- `docs/superpowers/specs/2026-06-12-composite-worlds-design.md` — **header only**
  (goal + `CompositeWorld` step-semantics design). Generator/harness design, not a
  solution; I stopped before any world-specific content.
- Directory listings across `experiments/`, `papers/`, `openworld/` to locate the
  generator. No `papers/balrog`, no NetHack/`nle`, no `e21b` harness exists in this
  repo — the NetHack E21b worlds live in the **quarantined** `wt-fable-nethack`
  worktree, which I never touched.

**Files I DID NOT read (quarantined):**
- Any NetHack/E21b run transcript or the T1/T5/T6 solution writeups.
- Any consult log or doc stating the winning lines.
- `experiments/results/*_traces/{transcripts,solutions}/` (identified by name and
  deliberately avoided).
- Anything in `wt-fable-nethack` or the main clone.

**On mechanic archetypes:** my own tasking prompt names, as examples of winning
lines I must not look up, the patterns *reveal-by-sacrifice / never-pick-up /
charm-keyed gates / damage-as-key*. I therefore already had those archetype
**names** from my instructions (not from any repo file). My fresh worlds use a
generic **"damage-as-key"** counterintuitive mechanic — the archetype named in my
prompt — instantiated as my own symbolic puzzle, not as any NetHack world. I never
recovered a specific E21b world solution.

## 2. Why a fresh grammar-generated set (not the registered E21b worlds)

The registered E21b NetHack worlds are not discoverable in this worktree without
reading quarantined material (their generator + solutions live behind the
`wt-fable-nethack` boundary). Per the tasking fallback, I generate a **fresh set at
matched composition-depth**: `worldgen.py` is a deterministic grammar over
`(class, seed)` producing symbolic "gate" puzzles that isolate the two factors
under study. Fully reproducible; touches zero quarantined content.

## 3. World classes (the composition-depth ladder)

Traversal is scripted (navigation is not the tested skill); the only decision is
the **key action at the gate**. Anti-leak rule: for composition worlds the gate
room carries **no** discriminative content — every fact needed to identify the
opening action sits in an **earlier** room, so an agent with no accumulated
observation store cannot recover it. Class A is the deliberate control: its single
instruction is co-located with the decision (in the gate room).

| Class | Depth | Key action | What it isolates |
|------|------|-----------|------------------|
| **A** intuitive        | D=1 | safe (`present`)     | control — single fact, no composition, no principle conflict |
| **B** composition      | D=2 | safe (`present`)     | needs **memory** to chain 2 facts; key is safe |
| **C** counterintuitive | D=2 | **damage** (`brave`) | needs memory **and override** — chain 2 facts, then self-damage |
| **D** deep-counter     | D=3 | **damage** (`brave`) | as C, deeper chain (3 hops) |

## 4. The four arms (differ ONLY structurally)

1. **CODE-ONLY** — no LLM. Procedural "explore + greedy-goal": collect facts, apply
   a fixed string-trigger rule (`present the <X>`) + greedy last-relic heuristic;
   `avoid_damage` is hard-coded (never selects a `brave` action). No composition.
2. **NO-MEMORY** — LLM sees **only the current (gate) room's** observation; no
   accumulated store. One decision call.
3. **NO-OVERRIDE** — LLM + full observation store (real `openworld.MemoryStore`,
   recalled against the gate goal), but `avoid_damage` is a **hard constraint**: any
   `brave` choice is vetoed and replaced by a safe fallback. We log whether the LLM
   *identified* the correct damaging action before the veto.
4. **FULL STACK** — LLM + memory + **override authority** (may suspend
   `avoid_damage`). Reference arm; run on the same fresh worlds (running it leaks no
   NetHack solution, so it is included rather than cited).

## 5. Pre-registered predictions

- **(P1) CODE-ONLY** ~0% on counterintuitive worlds (baseline signature).
- **(P2) NO-MEMORY** fails composition worlds (can't connect facts seen far apart).
- **(P3) NO-OVERRIDE** fails counterintuitive worlds (can't do damage-as-key).
- **(P4) Thesis:** only arms with **BOTH memory AND override** solve the
  counterintuitive composition worlds (C, D).

---

## 6. Results

In-loop model: `haiku`. Seeds: [1, 2, 3]. Trials/LLM-arm: 1. 

**Solve rate (fraction of episodes solved), rows = arm, cols = world-class:**

| Arm | A intuitive | B composition | C counterintuitive | D deep-counter |
|-----|:-----------:|:-------------:|:------------------:|:--------------:|
| **CODE-ONLY** | 1.00 | 0.00 | 0.00 | 0.00 |
| **NO-MEMORY** | 1.00 | 0.00 | 0.00 | 0.00 |
| **NO-OVERRIDE** | 1.00 | 1.00 | 0.00 | 0.00 |
| **FULL STACK** | 1.00 | 1.00 | 1.00 | 0.33 |

**LLM identified the correct opening action (pre-veto), by arm/class:**

| Arm | A | B | C | D |
|---|:-:|:-:|:-:|:-:|
| NO-MEMORY | 1.00 | 0.00 | 0.00 | 0.00 |
| NO-OVERRIDE | 1.00 | 1.00 | 1.00 | 0.67 |
| FULL STACK | 1.00 | 1.00 | 1.00 | 0.33 |

**NO-OVERRIDE vetoes** (correct damaging action identified then blocked): {'no_override': 6}


## 7. Verdict

Pre-registered predictions:

- **CONFIRMED** — P1 CODE-ONLY ~0% on counterintuitive (C,D). _(C=0.00 D=0.00)_
- **CONFIRMED** — P2 NO-MEMORY fails composition (B,C,D at/below chance). _(B=0.00 C=0.00 D=0.00)_
- **CONFIRMED** — P3 NO-OVERRIDE fails counterintuitive (C,D = 0). _(B=1.00 C=0.00 D=0.00)_
- **CONFIRMED** — P4 THESIS: only memory+override (FULL) solves counterintuitive worlds; all other arms score 0 on C,D. _(FULL C=1.00 D=0.33; all other arms C,D = 0: True)_

**4/4 predictions confirmed.** The dissociation observed:
- **CODE-ONLY** solves only the co-located control (A); it never composes and never self-damages -> 0 on B/C/D. Matches the pre-registered baseline signature.
- **NO-MEMORY** cannot chain facts split across rooms: the moment a discriminative fact was seen in an earlier room, it is gone, so composition (B/C/D) collapses -> solves only A.
- **NO-OVERRIDE** has memory and, on the counterintuitive worlds, *identifies the correct self-damaging action* (identified-opener rate C=1.00, D=0.67) but the hard `avoid_damage` constraint **vetoes** it every time -> it solves B (safe composition) yet scores **0 on C and D**. This is the smoking gun: override authority, not reasoning capability, is the blocker on counterintuitive worlds.
- **FULL STACK** is the *only* arm that solves any counterintuitive world (C=1.00, D=0.33); every other arm scores 0 on C and D.

The depth-3 worlds (D) are solved by FULL at 0.33, below its C rate: the small in-loop model (haiku) mis-composes the 3-hop chain in some cases (choosing a plausible-but-wrong hazard). That is a **capability ceiling on composition depth**, orthogonal to the memory x override axis (NO-OVERRIDE still *identified* the correct D action in the majority of cases before being vetoed). Net: perception+memory+procedure plateau on counterintuitive composition; the override-bearing (intuition) layer is what breaks them. **Both memory AND override are necessary** — memory alone (NO-OVERRIDE) unlocks safe composition (B) but not counterintuitive worlds; override without memory is untestable here because without memory the correct action is never even identified. The intuition-necessity thesis is supported.

---

## 8. Reproduce

```
cd papers/balrog/experiments/NH-E21b-ablation
env -u ANTHROPIC_API_KEY python3 -u run.py --seeds 1 2 3 --trials 1 --model haiku
python3 finalize.py   # regenerates this REPORT.md + prints the table
```

Files: `worldgen.py` (grammar), `harness.py` (arms + CLI LLM adapter + real
`MemoryStore`), `run.py` (runner + checkpointing), `finalize.py` (report gen),
`results/e21b_blind_results.json` (episodes + table).

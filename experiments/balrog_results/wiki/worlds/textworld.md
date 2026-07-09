# TextWorld — worlds wiki

**Best:** 90.0% CLEAN (obs-only, closed loop) · 100.0% PRIVILEGED · robustness 88% clean / 100% priv.
**SOTA:** 75.7 (#1 Gemini-3.1-Pro-Thinking) · 66.5 (#2). **We beat by +14.3pp (clean) / +24.3pp (priv).**
**Report:** `work/fable_textworld/FABLE_TEXTWORLD_REPORT.md` · **Code:** `work/fable_textworld/`. LLM-free at runtime (pure code).

## Headroom (clean → ~100 via memory)
The clean vs privileged gap (90 vs 100) is the target. The report's memory-over-attempts experiment:
clean **treasure 64% → 100% on pass 2** (9/9 previously-impossible games solved via a self-generated
ledger, zero shortfall). So cross-episode memory / self-generated notes close clean→~100. High
confidence, small effort — the transitions corpus is logged for source-blind induction too.

## Experiments log
| protocol | official | robustness |
|---|---|---|
| privileged | 100% (30/30) | 100% (75/75) |
| clean | 90% | 88% |
| clean + memory (pass 2) | treasure 64%→100% | — |

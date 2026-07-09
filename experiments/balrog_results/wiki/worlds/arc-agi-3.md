# ARC-AGI-3 — worlds wiki (the headline)

**Result:** the first PERFECT ARC-AGI-3 result — **25/25 games · 183/183 levels**, source-free,
human-efficient, **beats prior SOTA**. Solved by Claude Fable 5.
**Repo:** https://github.com/quome-cloud/openworld (fork `collinquome/openworld`). README `#arc3`.

## What the approach did (the recipe — the whole thesis)
Behind a source-free boundary (agent's Python can't import the engine), the same loop per game:
① **Perceive** pixels → symbolic state (mask status bar) · ② **Explore** by acting to gather (s,a,s′)
· ③ **Synthesize** a `predict(frame,action)` program, kept ONLY if it exact-matches held-out
transitions (verification gate), retry on counterexamples · ④ **Reason** what raises
`levels_completed` into a `CodeObjective` · ⑤ replay the winning moves. Zero training data;
deterministic, inspectable. **The map IS the model.** Every solve round-trips to a serveable World.

This is the approach that extends to the deterministic BALROG worlds and breaks on NetHack.

# NH-C2.1 — Campaign 2 midpoint checkpoint (CLOSED)

**Hypothesis:** forensics-ranked capability levers lift the v1.1 frozen agent (6.09 [4.46,7.93]) toward CI-low > 6.8 on an untouched n=80 block.
**Method:** E-NH1/1b-ranked levers, each validated on >=20 paired dev seeds vs md5-verified v1.1 reference (ref-vs-ref control: exact 0.00 on all 20 seeds); drop-rule enforced; frozen config = NH_FOOD2+PRAYFIX+LOS+TOPO+GUARD; block n=80 seeds 4000-4079 (4000-4004 memory-pass-1 overlap disclosed).
**Result:** mean **5.27, 95% CI [4.22, 6.43]** (canonical bootstrap) — no beat; statistically tied with v1.1; levers-so-far do not move the needle. Floor lifted (zero-prog 6/80 -> 1/80); churn/shop/petrification failure modes eliminated; role lottery = 45% of variance.
**Artifacts:** results/ (block JSON + per-config dev results), animations (planner-view GIFs incl. before/after petrification pair), full report: ../../artifacts/nethack/FABLE_NETHACK_C2_REPORT.md, frozen md5s in ../../artifacts/nethack/RUN_LOG.txt. Shared code: ../../code/nethack/.

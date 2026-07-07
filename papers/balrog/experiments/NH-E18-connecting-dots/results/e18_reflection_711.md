# NH-E18 reflection pass #2 — devb1 seed 711 (Wizard, D8, died to plains centaur region)

MODEL: Fable 5 (max reasoning) — the dot-connector consultation below is
logged VERBATIM (CONTEXT_SPEC discipline). Input: traj["store"] of
devb1__ep711 (story, monster ledger, features, firsts; items/prices empty
this episode).

## Consultation (verbatim)

The story reads as a textbook ARRIVAL_CONSTRAINT trajectory: depth 8 by
T327 with xp 1 and hp 15-16 the whole way (the "FIRST depth" awards come
faster than the "FIRST kill" awards — descent outran combat learning).
Dots I connect from the ledgers:

R4 — DIVE-VS-XP IMBALANCE IS VISIBLE IN THE FIRSTS STREAM ITSELF.
Firsts #1-#12 are almost all depth awards in the first 327 turns; kills
only catch up afterwards (T354-T463). Hypothesis: the RATIO of
depth-firsts to kill-firsts in the first 400 turns predicts
arrival-constraint deaths (E12's 59% class). Cheap to compute per episode
from store["firsts"] alone; validate against the retro corpus.
STATUS: proposed; validation = correlation over the 794-scenario library.

R5 — PASSIVE-SPECIES EVIDENCE ACCUMULATES CORRECTLY BUT IS UNCONSUMED.
lichen (seen 19, hit_us 0, passive_adj 2) and acid blob (seen 4,
passive_adj 4, hit_us 0) — the didn't-attack⇒harmless-unless-touched
pattern the store was built to catch. acid blob passive_adj=4 is exactly
the CAUTION case (passive acid ON TOUCH — attacking it is the mistake;
the store cannot see counterattack damage yet because hit_us only counts
their attacks). Hypothesis R5: adjacency-without-attack for N≥3 rows ⇒
downgrade threat BUT check kb for passive-touch before melee (dot to
NH-E13 KB: acid blob page). Feeds the monster-state perceptor backlog.

R6 — NOVELTY EVENT AND DEATH ARE ADJACENT. The single ev of the episode:
"NOVEL species adjacent: plains centaur (rows 0, diff 6)" at step 554 —
an xp-1 Wizard meeting a difficulty-6 novel species deep. P6 (thrown
probe before melee) and the novelty caution gate are EXACTLY this
moment's missing procedures; the character-sheet readiness ratio would
have vetoed D8 at xp1 long before. This episode is the operator's whole
thesis in one trajectory: capability-bound at the moment (nothing to
fight a centaur with), preparation-bound at the trajectory (12 levels of
skipped xp).

## Instrument notes
- items_seen/prices empty on a D8 Wizard run — item sighting capture is
  under-firing outside shops (check RE patterns vs floor-item messages);
  filed for the item-appearance perceptor build.
- store lacks our own melee outcomes vs passive species (hit_us counts
  their hits only) — counterattack (passive damage ON OUR ATTACK) is
  invisible; add passive_counter field when the monster-state perceptor
  lands.

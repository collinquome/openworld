# NH-E34 — Community Corpus (forums beyond the wiki)

MODEL: claude-opus-4-8[1m] (max thinking), Phase L session 5. Operator
directive via coordinator, 2026-07-07. DESIGN-STAGE; sequence AFTER the
floor-role uplift workstream.

## Idea
Extend the knowledge base beyond the reference wiki with COMMUNITY knowledge:
r/nethack, rec.games.roguelike.nethack (rgrn) strategy threads, the wiki's
own Talk pages, and well-known strategy guides. This is a DIFFERENT KNOWLEDGE
TYPE from the wiki's reference style: forums carry EXPERIENTIAL / tactical
knowledge — "here's how I actually survive the early game as a Tourist,"
death post-mortems, situational judgment — that reference pages lack.

## Discipline (same as the wiki KB, new provenance tag)
- FTS5 KB rows, **provenance:forum** (distinct from provenance:wiki /
  provenance:demonstration), sha256 content snapshots + source URL + fetch date.
- THREE-WAY validation on every forum claim (forum claim vs our exchange-model
  vs gym experiment) — NO trust exemption: community wisdom can be
  wrong-for-our-metric too (the same posture applied to the wiki cards).

## The larger experiment this grows
"Does external knowledge help, and WHICH KIND?" — wiki (reference) vs forum
(experiential) vs demonstration (ttyrec, NH-E35) vs none, sliced by provenance
tag. The s5 floor-role uplift (NH-E13 flagship) is the wiki arm; NH-E34 adds
the experiential arm; NH-E35b adds the ground-truth-winners arm. Per-role
slicing throughout (experiential Tourist survival tips feed the Tourist
playbook alongside the wiki card).

## Clean-protocol / legality
Public community text, used OFFLINE to build knowledge/priors (like reading
the wiki or source); scored runs stay pure-code/clean; disclosed prominently;
respect forum data/robots policies; flag the coordinator before any heavy
scrape.

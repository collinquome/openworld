#!/bin/bash
# Sync s9+s10 NetHack artifacts from the flat dev dir into the git worktree,
# keeping the two locations from diverging (armor-bug-at-repo-scale lesson).
set -e
SRC=/data/doh/teams/researchy/work/fable_nethack
WT=/data/doh/teams/researchy/work/wt-fable-nethack
CODE=$WT/papers/balrog/code/nethack
ART=$WT/papers/balrog/artifacts/nethack
DOCS=/data/doh/teams/researchy/docs

# --- CODE ---
for f in nh_agent.py e35_ttyrec.py e35_validate.py e35_antifaint_smoke.py \
         analyze_antifaint.py run_antifaint_block.sh e22_departure_analysis.py \
         package_artifacts.sh; do
  [ -f "$SRC/$f" ] && cp "$SRC/$f" "$CODE/$f" && echo "code  $f"
done

# --- DOCS (doctrine cards, handoff, findings) ---
for f in DOCTRINE_CARDS_s9.md DOCTRINE_CARDS_s10.md HANDOFF_10.md; do
  [ -f "$SRC/$f" ] && cp "$SRC/$f" "$ART/$f" && echo "doc   $f"
done
cp "$DOCS/PROGRAM_FINDINGS.md" "$ART/PROGRAM_FINDINGS.md" && echo "doc   PROGRAM_FINDINGS.md"

# --- DATA ARTIFACTS ---
mkdir -p "$ART/ttyrecs" "$ART/results"
cp -r "$SRC/ttyrecs/." "$ART/ttyrecs/" 2>/dev/null && echo "data  ttyrecs/"
[ -f "$SRC/results/e35_validate.json" ] && cp "$SRC/results/e35_validate.json" "$ART/results/" && echo "data  e35_validate.json"
[ -f "$SRC/results/antifaint_enriched.jsonl" ] && cp "$SRC/results/antifaint_enriched.jsonl" "$ART/results/" && echo "data  antifaint_enriched.jsonl"
[ -f "$SRC/results/antifaint_block.jsonl" ] && cp "$SRC/results/antifaint_block.jsonl" "$ART/results/" && echo "data  antifaint_block.jsonl"
echo "SYNC_DONE"

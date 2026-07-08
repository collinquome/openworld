#!/bin/bash
# Copy code + artifacts into the openworld worktree (PR layout mirrors #211).
set -e
SRC=/data/doh/teams/researchy/work/fable_nethack
WT=/data/doh/teams/researchy/work/wt-fable-nethack
CODE=$WT/papers/balrog/code/nethack
ART=$WT/papers/balrog/artifacts/nethack
mkdir -p "$CODE" "$ART"

cp $SRC/{nh_harness.py,nh_common.py,nh_agent.py,nh_memory.py,nh_transitions.py,nh_runner.py,run_suite.py,run_memory.py,run_explore_data.py,render_animations.py,verify_leaderboard.py,make_tables.py,dev_run.py,dev_batch.sh,README.md} "$CODE/"

cp $SRC/FABLE_NETHACK_REPORT.md "$ART/"
cp $SRC/results/nethack_results.json "$ART/" 2>/dev/null || true
cp $SRC/results/nethack_results_*.json "$ART/" 2>/dev/null || true
cp $SRC/results/memory_experiment.json "$ART/" 2>/dev/null || true
cp $SRC/results/memory_paired.json "$ART/" 2>/dev/null || true
cp $SRC/results/RUN_LOG.txt "$ART/" 2>/dev/null || true
cp $SRC/{bootstrap_ci.py,merge_baseline25.py,run_chunk.py,run_chunk_v11.py,run_memory_paired.py,dev_batch2.sh} "$WT/papers/balrog/code/nethack/" 2>/dev/null || true
mkdir -p "$ART/evidence" "$ART/memory" "$ART/animations" "$ART/transitions"
cp $SRC/results/evidence/* "$ART/evidence/" 2>/dev/null || true
cp $SRC/results/memory/*.json "$ART/memory/" 2>/dev/null || true
cp $SRC/results/animations/*.gif "$ART/animations/" 2>/dev/null || true
# transitions: scored blocks + induction data
for d in clean_A baseline25 robustness memory_pass1 memory_pass2 memory_pass3 memory_paired exploration v11block40; do
  if [ -d "$SRC/results/transitions/$d" ]; then
    mkdir -p "$ART/transitions/$d"
    cp $SRC/results/transitions/$d/*.gz "$ART/transitions/$d/"
  fi
done
du -sh "$ART" "$CODE"

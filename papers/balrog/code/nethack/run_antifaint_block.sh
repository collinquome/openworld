#!/bin/bash
# Anti-faint pre-registered paired block. ONE seed per PROCESS (s8 cross-seed
# leakage). Resumable: skips (arm,seed) already present in the JSONL.
# Usage: ./run_antifaint_block.sh <out.jsonl> <seed> [seed ...]
cd /data/doh/teams/researchy/work/fable_nethack
export PYTHONPATH=pylib
REF_FLAGS="NH_FOOD2=1 NH_PRAYFIX=1 NH_LOS=1 NH_TOPO=1 NH_GUARD=1 NH_CAST=1 NH_CASTHUNGER=1 NH_E15=1"
OUT=$1; shift
touch "$OUT"
for seed in "$@"; do
  for arm in REF TEST; do
    if grep -q "\"seed\": $seed, \"arm\": \"$arm\"" "$OUT" 2>/dev/null; then
      echo "skip $arm $seed (done)"; continue
    fi
    EXTRA=""; [ "$arm" = "TEST" ] && EXTRA="NH_ANTIFAINT=1"
    line=$(env NH_STEPCAP=2000 $REF_FLAGS $EXTRA timeout 300 \
           python3 e35_antifaint_smoke.py "$arm" "$seed" 2>/dev/null | grep "^JSONL ")
    if [ -z "$line" ]; then
      echo "FAIL/timeout $arm $seed"
      echo "{\"seed\": $seed, \"arm\": \"$arm\", \"end_reason\": \"TIMEOUT_OR_FAIL\", \"maxhunger\": -1}" >> "$OUT"
    else
      echo "${line#JSONL }" >> "$OUT"
      echo "ok $arm $seed"
    fi
  done
done
echo "CHUNK_DONE"

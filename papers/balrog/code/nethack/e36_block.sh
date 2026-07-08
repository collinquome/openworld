#!/bin/bash
# NH-E36 DEPLOY paired block. ONE seed per PROCESS (s8 leakage). Resumable
# (skips done (arm,seed)). SERIAL (s10 VM-contention). Per-episode timeout.
# REF = C2.1 standing config. TEST = REF + NH_E36 (compiled CORRIDOR selector
# fires on the TRASH-crisis predicate). Cap must reach the mid-episode crisis.
# Usage: ./e36_block.sh <out.jsonl> <seed> [seed ...]
cd /data/doh/teams/researchy/work/fable_nethack
export PYTHONPATH=pylib
REF_FLAGS="NH_FOOD2=1 NH_PRAYFIX=1 NH_LOS=1 NH_TOPO=1 NH_GUARD=1 NH_CAST=1 NH_CASTHUNGER=1 NH_E15=1"
CAP=${NH_STEPCAP:-1500}
TIMEOUT=${NH_EP_TIMEOUT:-600}
OUT=$1; shift
touch "$OUT"
for seed in "$@"; do
  for arm in REF TEST; do
    if grep -q "\"seed\": $seed, \"arm\": \"$arm\"" "$OUT" 2>/dev/null; then
      echo "skip $arm $seed (done)"; continue
    fi
    EXTRA=""; [ "$arm" = "TEST" ] && EXTRA="NH_E36=1"
    line=$(env NH_STEPCAP=$CAP $REF_FLAGS $EXTRA timeout $TIMEOUT \
           python3 e36_paired.py "$arm" "$seed" 2>/dev/null | grep "^JSONL ")
    if [ -z "$line" ]; then
      echo "FAIL/timeout $arm $seed"
      echo "{\"seed\": $seed, \"arm\": \"$arm\", \"end_reason\": \"TIMEOUT_OR_FAIL\", \"prog\": -1}" >> "$OUT"
    else
      echo "${line#JSONL }" >> "$OUT"
      echo "ok $arm $seed $(echo $line | grep -oE 'prog[^,]*|fires[^,]*')"
    fi
  done
done
echo "E36_BLOCK_DONE"

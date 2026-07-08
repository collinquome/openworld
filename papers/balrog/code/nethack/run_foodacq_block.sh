#!/bin/bash
# FOOD-ACQUISITION paired block (Phase L s11). ONE seed per PROCESS (s8 cross-
# seed leakage). Resumable: skips (arm,seed) already present in the JSONL.
# REF  = C2.1 frozen. TEST = REF + NH_FOODACQ + NH_ANTIFAINT (acquisition on,
# guard live on top). SERIAL to avoid VM-contention timeouts (s10 lesson).
# Usage: ./run_foodacq_block.sh <out.jsonl> <seed> [seed ...]
cd /data/doh/teams/researchy/work/fable_nethack
export PYTHONPATH=pylib
REF_FLAGS="NH_FOOD2=1 NH_PRAYFIX=1 NH_LOS=1 NH_TOPO=1 NH_GUARD=1 NH_CAST=1 NH_CASTHUNGER=1 NH_E15=1"
CAP=${NH_STEPCAP:-2500}
OUT=$1; shift
touch "$OUT"
for seed in "$@"; do
  for arm in REF TEST; do
    if grep -q "\"seed\": $seed, \"arm\": \"$arm\"" "$OUT" 2>/dev/null; then
      echo "skip $arm $seed (done)"; continue
    fi
    EXTRA=""; [ "$arm" = "TEST" ] && EXTRA="NH_FOODACQ=1 NH_ANTIFAINT=1"
    line=$(env NH_STEPCAP=$CAP $REF_FLAGS $EXTRA timeout 280 \
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

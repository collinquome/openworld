#!/bin/bash
# NH-E38 CONSUMABLE-ECONOMY paired block. ONE seed/arm per PROCESS (s8 cross-seed
# leakage). Resumable: skips (arm,seed) already in the JSONL, so a foreground
# Bash call cut at the ~9min auto-background limit just resumes on re-invoke
# (BLOCKING foreground, NO detached waiter — OPS rule).
#   REF  = C2.1 frozen + NH_FOODACQ + NH_ANTIFAINT (the standing config, matches
#          loot_block/pet_block REF so those REF rows are comparable).
#   TEST = REF + NH_CONSUME (engrave-ID wands + zap KNOWN offensive/control wand
#          at a spike-threat + quaff KNOWN heal + gain-level/enchant when safe +
#          underfoot consumable pickup).
# Per-episode timeout 480s (survivors truncate ~1750 steps at the slow VM).
# cap default 3000 (brief). Usage: ./run_consume_block.sh <out.jsonl> <seed>...
cd /data/doh/teams/researchy/work/fable_nethack
export PYTHONPATH=pylib
REF_FLAGS="NH_FOOD2=1 NH_PRAYFIX=1 NH_LOS=1 NH_TOPO=1 NH_GUARD=1 NH_CAST=1 NH_CASTHUNGER=1 NH_E15=1 NH_FOODACQ=1 NH_ANTIFAINT=1"
CAP=${NH_STEPCAP:-3000}
TIMEOUT=${NH_EP_TIMEOUT:-480}
OUT=$1; shift
touch "$OUT"
for seed in "$@"; do
  for arm in REF TEST; do
    if grep -q "\"seed\": $seed, \"arm\": \"$arm\"" "$OUT" 2>/dev/null; then
      echo "skip $arm $seed (done)"; continue
    fi
    EXTRA=""; [ "$arm" = "TEST" ] && EXTRA="NH_CONSUME=1"
    line=$(env NH_STEPCAP=$CAP $REF_FLAGS $EXTRA timeout $TIMEOUT \
           python3 e35_antifaint_smoke.py "$arm" "$seed" 2>>"$OUT.err" | grep "^JSONL ")
    if [ -z "$line" ]; then
      echo "FAIL/timeout $arm $seed"
      echo "{\"seed\": $seed, \"arm\": \"$arm\", \"end_reason\": \"TIMEOUT_OR_FAIL\", \"prog\": null}" >> "$OUT"
    else
      echo "${line#JSONL }" >> "$OUT"
      r=$(echo "${line#JSONL }" | python3 -c "import sys,json;r=json.load(sys.stdin);print(f\"prog={r.get('prog')} depth={r.get('depth_max')} xpD5={r.get('arrival_xp_d5')} zap={r.get('zap_off_fires')} eng={r.get('engrave_id_tests')} pick={r.get('consume_pickups')} gl={r.get('gainlevel_fires')} end={str(r.get('end_reason'))[:24]}\")" 2>/dev/null)
      echo "ok $arm $seed  $r"
    fi
  done
done
echo "CHUNK_DONE"

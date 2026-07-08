#!/bin/bash
# NH-E38 TEST-only (pairs vs the reused cap-3000 standing-config REF baseline,
# results/e38_ref_baseline.jsonl — REF is deterministic + the E38 code additions
# are bit-identical, so reuse is valid). timeout 720 so cap-3000 survivors
# COMPLETE (avoids the survival-win exclusion bias, HANDOFF_14). Resumable.
cd /data/doh/teams/researchy/work/fable_nethack
export PYTHONPATH=pylib
REF_FLAGS="NH_FOOD2=1 NH_PRAYFIX=1 NH_LOS=1 NH_TOPO=1 NH_GUARD=1 NH_CAST=1 NH_CASTHUNGER=1 NH_E15=1 NH_FOODACQ=1 NH_ANTIFAINT=1"
CAP=${NH_STEPCAP:-3000}; TIMEOUT=${NH_EP_TIMEOUT:-720}
OUT=$1; shift; touch "$OUT"
for seed in "$@"; do
  if grep -q "\"seed\": $seed, \"arm\": \"TEST\"" "$OUT" 2>/dev/null; then echo "skip $seed"; continue; fi
  line=$(env NH_STEPCAP=$CAP $REF_FLAGS NH_CONSUME=1 timeout $TIMEOUT \
         python3 e35_antifaint_smoke.py TEST "$seed" 2>>"$OUT.err" | grep "^JSONL ")
  if [ -z "$line" ]; then
    echo "FAIL/timeout TEST $seed"
    echo "{\"seed\": $seed, \"arm\": \"TEST\", \"end_reason\": \"TIMEOUT_OR_FAIL\", \"prog\": null}" >> "$OUT"
  else
    echo "${line#JSONL }" >> "$OUT"
    echo "ok TEST $seed  $(echo "${line#JSONL }" | python3 -c "import sys,json;r=json.load(sys.stdin);print('prog=%s d=%s xpD5=%s zap=%s eng=%s walk=%s acq=%s gl=%s'%(round(r.get('prog') or 0,4),r.get('depth_max'),r.get('arrival_xp_d5'),r.get('zap_off_fires'),r.get('engrave_id_tests'),r.get('consume_walks'),r.get('consume_acq'),r.get('gainlevel_fires')))" 2>/dev/null)"
  fi
done
echo "TESTONLY_DONE"

#!/bin/bash
# THROW_DISENGAGE paired block (s6). ref=standing vs test=standing+CRISIS_THROW.
# 12 seeds (4 THROW-win + 8 fresh), cap 6000, 3 workers/arm. Disjoint suffixes.
cd /data/doh/teams/researchy/work/fable_nethack
export PYTHONPATH=pylib
export NH_FOOD2=1 NH_PRAYFIX=1 NH_LOS=1 NH_TOPO=1 NH_GUARD=1
export NH_CAST=1 NH_CASTHUNGER=1 NH_E15=1
export NH_STEPCAP=6000

G0="707 714 727 732"
G1="780 781 782 783"
G2="784 785 786 787"

# ref arm (throw OFF)
NH_CRISIS_THROW=0 python3 capblock.py throwref w0 $G0 &
NH_CRISIS_THROW=0 python3 capblock.py throwref w1 $G1 &
NH_CRISIS_THROW=0 python3 capblock.py throwref w2 $G2 &
# test arm (throw ON)
NH_CRISIS_THROW=1 python3 capblock.py throwtest w0 $G0 &
NH_CRISIS_THROW=1 python3 capblock.py throwtest w1 $G1 &
NH_CRISIS_THROW=1 python3 capblock.py throwtest w2 $G2 &
wait
echo "THROW_BLOCK_ALLDONE"

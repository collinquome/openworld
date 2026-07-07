#!/bin/bash
# HEALER role-stratified paired block (NH-E13 wiki flagship, s6).
# ref=standing vs test=standing+NH_ROLE_PROFILE(Healer cast-heal profile).
# 20 Healer seeds (role_seeds.py Healer pool), cap 6000, 4 workers/arm.
cd /data/doh/teams/researchy/work/fable_nethack
export PYTHONPATH=pylib
export NH_FOOD2=1 NH_PRAYFIX=1 NH_LOS=1 NH_TOPO=1 NH_GUARD=1
export NH_CAST=1 NH_CASTHUNGER=1 NH_E15=1
export NH_STEPCAP=6000

H0="825 828 831 833 844"
H1="854 867 874 879 886"
H2="888 891 894 895 900"
H3="907 911 927 932 935"

for W in 0 1 2 3; do
  eval S=\$H$W
  NH_ROLE_PROFILE=0 python3 capblock.py healref w$W $S &
  NH_ROLE_PROFILE=1 python3 capblock.py healtest w$W $S &
done
wait
echo "HEALER_BLOCK_ALLDONE"

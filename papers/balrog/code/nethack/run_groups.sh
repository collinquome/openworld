#!/bin/bash
cd "$(dirname "$0")"
SEEDS_W0="700 703 706 709 712 715 718"
SEEDS_W1="701 704 707 710 713 716 719"
SEEDS_W2="702 705 708 711 714 717"
rg () {
  local label="$1"; shift
  ( export "$@"; python3 run_c2.py "$label" w0 $SEEDS_W0 > "results/${label}_w0.log" 2>&1 & \
    python3 run_c2.py "$label" w1 $SEEDS_W1 > "results/${label}_w1.log" 2>&1 & \
    python3 run_c2.py "$label" w2 $SEEDS_W2 > "results/${label}_w2.log" 2>&1 & \
    wait )
  echo "GROUP $label done $(date -u +%H:%M:%S)" >> results/c2_groups_done.txt
}
rg c2g_combat NH_EXPMAX=1 NH_RANGED=1 NH_THREAT=1
rg c2g_food   NH_FOOD2=1 NH_PRAYFIX=1
rg c2g_armor  NH_ARMOR=1
rg c2g_nav    NH_LOS=1 NH_TOPO=1
rg c2g_pace   NH_PACE=1
echo ALL DONE >> results/c2_groups_done.txt

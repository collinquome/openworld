"""Paired KITE vs DOOR_KITE across backoffs — isolates door-routing.
Reports per (seed,backoff): alive/escaped/maxdepth/hp/steps for each, and
whether the two ACTION SEQUENCES diverged (proof the door term changed play)."""
import sys, os, json
sys.path.insert(0,'pylib'); sys.path.insert(0,'.')
import e6_solve_v2 as E
import nh_branch as B
import nh_common as C
from nle import nethack as nh
RES='results'

def run_traced(seed, prefix, policy, stop_time, budget, start_depth):
    br=B.Branch(seed,tuple(prefix)); A=C.Atlas()
    alive=True; t=None; hp=None; steps=0; escaped=False; maxd=start_depth
    trace=[]
    ps={}
    while steps<budget:
        A.update(br.obs)
        if A.depth!=start_depth: escaped=True
        maxd=max(maxd,A.depth)
        acts=policy(A,br.obs,ps) or ["search"]
        trace.append(acts[0] if acts else "?")
        broke=False
        for a in acts:
            _,done=br.step(a); steps+=1
            bl=br.obs["obs"]["blstats"]; hp=int(bl[nh.NLE_BL_HP]); t=int(bl[nh.NLE_BL_TIME])
            if done or hp<=0: alive=False; broke=True; break
            if t>=stop_time: broke=True; break
        if broke or not alive or (t is not None and t>=stop_time): break
    br.close()
    return {"alive":alive,"hp":hp,"steps":steps,"escaped":escaped,"max_depth":maxd,"trace":trace}

lib=json.load(open(os.path.join(RES,'e6_scenarios.json')))
seeds={707,714,727,732}
by={}
for sc in lib['scenarios']:
    if sc.get('class')!='TRASH' or not sc.get('branchable'): continue
    if sc['seed'] in by or sc['seed'] not in seeds: continue
    if not os.path.exists(os.path.join(RES,sc['transitions_file'])): continue
    by[sc['seed']]=sc

BACKOFFS=[15,30,50,80]
WINDOW=600; BUDGET=400
agg={"KITE":0,"DOOR_KITE":0}; npairs=0; ndiverged=0; nboth=0
print(f"{'seed':>5} {'role':8} {'bko':>4} {'KITE':>18} {'DOOR_KITE':>18}  diverged")
for seed in sorted(by):
    sc=by[seed]
    acts,hps,times,depths=E.logged_actions(sc['transitions_file'])
    n=len(acts); death_t=max(times); start_depth=max(depths); stop=death_t+WINDOW
    for bko in BACKOFFS:
        prefix=acts[:max(1,n-bko)]
        rk=run_traced(seed,prefix,E.pol_kite,stop,BUDGET,start_depth)
        rd=run_traced(seed,prefix,E.pol_door_kite,stop,BUDGET,start_depth)
        div = rk["trace"]!=rd["trace"]
        npairs+=1; ndiverged+=int(div)
        agg["KITE"]+=int(rk["alive"]); agg["DOOR_KITE"]+=int(rd["alive"])
        def fmt(r): return f"a{int(r['alive'])} e{int(r['escaped'])} D{r['max_depth']} hp{r['hp']}"
        print(f"{seed:>5} {str(sc.get('role'))[:8]:8} {bko:>4} {fmt(rk):>18} {fmt(rd):>18}  {'YES' if div else '.'}")
print(f"\nPAIRED over {npairs} (seed,backoff) branch states:")
print(f"  KITE      survive {agg['KITE']}/{npairs}")
print(f"  DOOR_KITE survive {agg['DOOR_KITE']}/{npairs}")
print(f"  policies diverged (door term changed a step): {ndiverged}/{npairs}")

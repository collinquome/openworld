"""Proximal KPI for a POSITIONING lever: does DOOR_KITE gain distance on the
pursuer vs KITE? Per rollout: turns-adjacent (Cheb<=1 to any mobile hostile),
mean & max min-distance to nearest mobile, over the pre-escape chase window."""
import sys, os, json
sys.path.insert(0,'pylib'); sys.path.insert(0,'.')
import e6_solve_v2 as E
import nh_branch as B
import nh_common as C
from nle import nethack as nh
RES='results'

def run_metrics(seed, prefix, policy, stop_time, budget, start_depth):
    br=B.Branch(seed,tuple(prefix)); A=C.Atlas(); ps={}
    steps=0; turns_adj=0; dists=[]; obs_turns=0; escaped=False; alive=True; hp=None
    while steps<budget:
        A.update(br.obs); L=A.level; ax,ay=A.agent
        if A.depth!=start_depth: escaped=True; break   # measure only the local chase
        mob=[m for m in L.monsters if not m.pet and m.name not in C.IMMOBILE and m.pos not in L.no_attack]
        if mob:
            d=min(max(abs(m.x-ax),abs(m.y-ay)) for m in mob)
            dists.append(d); obs_turns+=1
            if d<=1: turns_adj+=1
        acts=policy(A,br.obs,ps) or ["search"]
        broke=False
        for a in acts:
            _,done=br.step(a); steps+=1
            bl=br.obs["obs"]["blstats"]; hp=int(bl[nh.NLE_BL_HP]); t=int(bl[nh.NLE_BL_TIME])
            if done or hp<=0: alive=False; broke=True; break
            if t>=stop_time: broke=True; break
        if broke or not alive: break
    br.close()
    md = max(dists) if dists else 0
    mean_d = sum(dists)/len(dists) if dists else 0
    return {"turns_adj":turns_adj,"obs_turns":obs_turns,"max_d":md,"mean_d":round(mean_d,2),"escaped":escaped,"alive":alive}

lib=json.load(open(os.path.join(RES,'e6_scenarios.json')))
seeds={707,714,727,732}; by={}
for sc in lib['scenarios']:
    if sc.get('class')!='TRASH' or not sc.get('branchable'): continue
    if sc['seed'] in by or sc['seed'] not in seeds: continue
    if not os.path.exists(os.path.join(RES,sc['transitions_file'])): continue
    by[sc['seed']]=sc
BACKOFFS=[15,30,50,80]; WINDOW=600; BUDGET=200
tot={"KITE":{"adj":0,"obs":0,"maxd":0},"DOOR_KITE":{"adj":0,"obs":0,"maxd":0},"DOOR_TB":{"adj":0,"obs":0,"maxd":0}}
print(f"{'seed':>5} {'bko':>4} | {'KITE adj/obs maxd meand':>26} | {'DOOR adj/obs maxd meand':>26}")
for seed in sorted(by):
    sc=by[seed]; acts,hps,times,depths=E.logged_actions(sc['transitions_file'])
    n=len(acts); death_t=max(times); sd=max(depths); stop=death_t+WINDOW
    for bko in BACKOFFS:
        pfx=acts[:max(1,n-bko)]
        k=run_metrics(seed,pfx,E.pol_kite,stop,BUDGET,sd)
        d=run_metrics(seed,pfx,E.pol_door_kite,stop,BUDGET,sd)
        tb=run_metrics(seed,pfx,E.pol_door_kite_tb,stop,BUDGET,sd)
        for nm,r in (("KITE",k),("DOOR_KITE",d),("DOOR_TB",tb)):
            tot[nm]["adj"]+=r["turns_adj"]; tot[nm]["obs"]+=r["obs_turns"]; tot[nm]["maxd"]+=r["max_d"]
        print(f"{seed:>5} {bko:>4} | K {k['turns_adj']:>3}/{k['obs_turns']:<3} md{k['max_d']} | A {d['turns_adj']:>3}/{d['obs_turns']:<3} md{d['max_d']} | B {tb['turns_adj']:>3}/{tb['obs_turns']:<3} md{tb['max_d']}")
print("\n=== aggregate over 16 branch states (local-chase window only) ===")
for nm in ("KITE","DOOR_KITE","DOOR_TB"):
    t=tot[nm]; frac=t["adj"]/t["obs"] if t["obs"] else 0
    print(f"  {nm:10} turns-adjacent {t['adj']}/{t['obs']} ({frac*100:.0f}%)  sum-maxdist {t['maxd']}")

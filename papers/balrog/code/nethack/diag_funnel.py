"""NH-E41 funnel-firing / pack-encounter diagnostic. Wraps DiveAgent._funnel to
record, at every call (adj present at P4.97): depth, hp_frac, pack size within
radius, pack simultaneous-burst dpt, burst/hp ratio, nearest reachable choke,
and the WOULD_FIRE classification under the current gates. Summarizes the
burst-fraction distribution of PACK (>=2) encounters so we can see whether
dangerous multi-attacker packs actually occur live, and at what depth.

Run: NH_FUNNEL=1 ...REFflags... PYTHONPATH=pylib python3 diag_funnel.py <seed> [cap]
"""
import os
import sys
from collections import Counter

import nh_agent
import nh_percept as P
import nh_runner

seed = int(sys.argv[1])
cap = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
nh_runner.MAX_LOOP = cap

reasons = Counter()
pack_events = []   # (depth, hp_frac, pack, burst, burst_frac, near)
_orig = nh_agent.DiveAgent._funnel


def _diag(self, obs, adj):
    A = self.atlas
    L = A.level
    reasons["CALLED"] += 1
    hp_frac = A.hp / max(A.hpmax, 1)
    ax, ay = A.agent
    pack = [m for m in L.monsters
            if (not m.pet) and m.name not in nh_agent.C.IMMOBILE
            and m.pos not in L.no_attack and not self._never_melee(m)
            and max(abs(m.x - ax), abs(m.y - ay)) <= nh_agent.FUNNEL_RADIUS]
    burst = 0.0
    for m in pack:
        try:
            burst += P.species_dpt(m.name, m.difficulty)
        except Exception:
            pass
    bf = burst / max(A.hp, 1)
    near = None
    try:
        topo = self._topo()
        chokes = topo.chokes
        if chokes and A.agent not in chokes:
            avoid = self._suspects() | self._mcells()
            best = 999
            for cell in chokes:
                d = max(abs(cell[0] - ax), abs(cell[1] - ay))
                if 0 < d <= nh_agent.FUNNEL_MAXDIST:
                    p = L.bfs(A.agent, [cell], avoid=avoid)
                    if p:
                        best = min(best, len(p))
            near = best if best < 999 else None
        elif chokes and A.agent in chokes:
            near = "ON_CHOKE"
    except Exception:
        pass
    if len(pack) >= 2:
        pack_events.append((A.depth, round(hp_frac, 2), len(pack),
                            round(burst, 1), round(bf, 2), near))
    return _orig(self, obs, adj)


nh_agent.DiveAgent._funnel = _diag
res = nh_runner.run_episode(ep=seed, seed=seed, condition="TEST", label="TEST",
                            log=lambda *a, **k: None)
print(f"seed {seed} cap {cap} end={res.get('end_reason')} "
      f"depth={res.get('depth_max')} prog={round(res.get('progression'),4)}")
print(f"_funnel CALLED={reasons['CALLED']}  PACK(>=2) events={len(pack_events)}")
# burst-fraction histogram over pack events
buckets = Counter()
depth = Counter()
reach = Counter()
for d, hpf, n, b, bf, near in pack_events:
    if bf < 0.15:
        buckets["burst<0.15hp"] += 1
    elif bf < 0.30:
        buckets["0.15-0.30"] += 1
    elif bf < 0.50:
        buckets["0.30-0.50"] += 1
    else:
        buckets[">=0.50"] += 1
    depth_band = f"D{d}"
    depth_bucket = ">=0.30hp" if bf >= 0.30 else "<0.30hp"
    depth[(depth_band, depth_bucket)] += 1
    if isinstance(near, int):
        reach["choke_reachable"] += 1
    elif near == "ON_CHOKE":
        reach["already_on_choke"] += 1
    else:
        reach["no_reachable_choke"] += 1
print("burst/HP distribution over pack events:", dict(buckets))
print("choke reachability over pack events:", dict(reach))
print("dangerous packs (burst>=0.30hp) by depth:",
      {k: v for k, v in sorted(depth.items()) if k[1] == ">=0.30hp"})
print("sample pack events (depth,hp_frac,pack,burst,burst/hp,near):")
for e in pack_events[:30]:
    print("   ", e)

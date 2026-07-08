"""NH-E36 DEPLOY — compiled selector wired into the live agent (step 5).

MODEL: claude-opus-4-8 (max thinking), NH-E36.

The compiled selector = {crisis_predicate (scenario signature), CORRIDOR
(winning strategy from the simulate matrix)}. It is injected as a DiveAgent
SUBCLASS (E36Agent) via monkeypatch — ZERO edits to the shared/parallel-owned
nh_agent.py / nh_runner.py. Flag NH_E36 (env). Default-OFF is bit-identical:
when off, act() delegates verbatim to the base DiveAgent (single atlas update,
identical decide path). When on, at each step: if the TRASH-crisis predicate
fires (mobile hostile adjacent, hp_frac<=gate, D2-7) the agent yields to the
CORRIDOR policy (funnel to a 1-wide corridor + fight the weakest) until the
crisis clears; otherwise the base agent decides unchanged.

ARCHITECTURE (coordinator directive): three decoupled layers —
  STRATEGY  = e36_candidates.pol_* (reusable policies, NO baked-in qualifier)
  SIGNATURE = e36_compile.crisis_predicate (recognizes the scenario TYPE)
  SELECTOR  = the simulate matrix -> top strategy per scenario (here CORRIDOR).
The qualifier ("use CORRIDOR here") is LEARNED (the survival matrix), not
hand-coded into the strategy.

Usage (one arm / one seed per process — s8 leakage rule):
  NH_STEPCAP=1200 python3 e36_paired.py REF  <seed>
  NH_STEPCAP=1200 NH_E36=1 python3 e36_paired.py TEST <seed>
"""

import json
import os
import sys

import nh_agent
import nh_runner
from nh_agent import DiveAgent
from e36_candidates import pol_corridor
from e36_compile import crisis_predicate

E36_ON = os.environ.get("NH_E36") == "1"
CAP = int(os.environ.get("NH_STEPCAP", "1200"))
nh_runner.MAX_LOOP = CAP
TRAJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results",
                    "trajectories")


class E36Agent(DiveAgent):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._e36_ps = {}
        self._e36_queue = []
        self._e36_fires = 0

    def _finish(self, A, a):
        self.last_action = a
        self.last_pos = A.agent
        self.last_time = A.time
        self.last_hp = A.hp
        self.steps += 1
        return a

    def act(self, obs):
        if not E36_ON:
            return super().act(obs)          # bit-identical base behavior
        A = self.atlas
        A.update(obs)
        # continue a queued multi-token CORRIDOR action
        if self._e36_queue:
            return self._finish(A, self._e36_queue.pop(0))
        if crisis_predicate(A, obs):
            toks = pol_corridor(A, obs, self._e36_ps) or ["search"]
            self._e36_fires += 1
            self.notes.append((self.steps, "E36_CORRIDOR fire"))
            self._e36_queue = list(toks[1:])
            return self._finish(A, toks[0])
        # not in crisis: replicate the base decide path (atlas already updated)
        msg = A.message
        self._bookkeeping(obs, msg)
        if nh_agent.C2_ANY:
            self._log_pred()
        return self._finish(A, self._decide(obs, msg))


def main():
    nh_runner.DiveAgent = E36Agent           # inject the subclass
    arm = sys.argv[1]
    seeds = [int(s) for s in sys.argv[2:]]
    print(f"ARM={arm} NH_E36={E36_ON} CAP={CAP} flags="
          + ",".join(f"{k}={v}" for k, v in sorted(os.environ.items())
                     if k.startswith("NH_")), flush=True)
    for s in seeds:
        res = nh_runner.run_episode(ep=s, seed=s, condition=arm, label=arm,
                                    log=lambda *a, **k: None)
        tj = os.path.join(TRAJ, f"{arm}__ep{s}.json")
        traj = json.load(open(tj)) if os.path.exists(tj) else {}
        fires = sum(1 for n in traj.get("notes", []) if "E36_CORRIDOR" in str(n))
        out = {"seed": s, "arm": arm, "nh_e36": E36_ON,
               "end_reason": res.get("end_reason"), "steps": res.get("steps"),
               "depth_max": res.get("depth_max"), "prog": res.get("progression"),
               "e36_fires": fires, "role": res.get("role")}
        print(f"  seed {s} {arm} prog={out['prog']} depth={out['depth_max']} "
              f"fires={fires} end={str(out['end_reason'])[:30]} "
              f"steps={out['steps']}", flush=True)
        print("JSONL " + json.dumps(out), flush=True)


if __name__ == "__main__":
    main()

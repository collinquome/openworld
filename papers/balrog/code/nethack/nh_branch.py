"""NH-E16 replay/branch executor — "deterministic replay as an epistemic instrument".

MODEL provenance: designed/written by Fable 5 (max reasoning), Phase L session 1.

Foundation (verified, NH-C2.1 report §E-NH2): the env stack is perfectly
deterministic on this host — same seed + same action sequence => identical
state (ref-vs-ref control n=20, all paired deltas exactly 0.00). Therefore a
(seed, action_prefix) pair IS a state snapshot, and replay-then-diverge is a
sound branch operator.

Clean protocol: everything here uses reset(seed)/step(action) + served
observations only — no env internals, no state cloning. DEV/GYM SEEDS ONLY:
this module asserts snapshots never touch reserved scored ranges
(4000-4079 checkpoint, 6000-6099 Arm A, 7000-7024 Arm B).

Uses (NH-E16 card):
  component 1 (search teaches policy): snapshot at high-uncertainty decision
    points, branch-explore alternatives, distill winners into rule cards.
  component 2 (branch-probe mechanics): before uncertain interactions, try
    the action on a branch and observe (verb grammar, effects, dangers).
    Teaches GENERAL mechanics only — item appearances shuffle per seed, so
    per-episode identities never transfer (pre-declared honest scope).

Determinism discipline: verify_determinism() re-checked per session before
any probe batch is trusted; drift => STOP and investigate.
"""

import hashlib
import json
import os
import time

import nh_harness as H
import nh_common as C
from nh_agent import DiveAgent

HERE = os.path.dirname(os.path.abspath(__file__))
PROBE_DIR = os.path.join(HERE, "results", "e16_probes")
os.makedirs(PROBE_DIR, exist_ok=True)

# Scored/reserved ranges (program registry). Snapshots must never use them.
FORBIDDEN = [(1000, 1004), (2000, 2024), (3000, 3079), (4000, 4079),
             (5000, 5024), (6000, 6099), (7000, 7024)]


def assert_dev_seed(seed):
    for lo, hi in FORBIDDEN:
        if lo <= seed <= hi:
            raise ValueError(
                f"seed {seed} is in reserved scored range {lo}-{hi}; "
                f"branch/replay is dev/gym-only")


def state_sig(obs):
    """Hash of the served state (tty + blstats): equality across replays is
    the determinism check. Served-obs only."""
    raw = obs["obs"]
    h = hashlib.sha256()
    for row in raw["tty_chars"]:
        h.update(bytes(int(c) & 0xFF for c in row))
    h.update(",".join(str(int(v)) for v in raw["blstats"]).encode())
    return h.hexdigest()[:16]


def obs_brief(obs):
    """Compact human-readable state extract for probe transcripts."""
    raw = obs["obs"]
    bl = raw["blstats"]
    nh = C.nh
    return {
        "msg": raw.get("text_message", ""),
        "hp": int(bl[nh.NLE_BL_HP]), "hpmax": int(bl[nh.NLE_BL_HPMAX]),
        "pw": int(bl[nh.NLE_BL_ENE]),
        "pwmax": int(bl[nh.NLE_BL_ENEMAX]),
        "time": int(bl[nh.NLE_BL_TIME]),
        "depth": int(bl[nh.NLE_BL_DEPTH]),
        "hunger": int(bl[nh.NLE_BL_HUNGER]),
        "misc": [int(v) for v in raw["misc"]],
    }


def tty_lines(obs, top=None):
    raw = obs["obs"]
    rows = ["".join(chr(int(c)) for c in row).rstrip()
            for row in raw["tty_chars"]]
    return rows[:top] if top else rows


class Branch:
    """A live env parked at (seed, prefix). step()/script() to diverge."""

    def __init__(self, seed, prefix=(), env=None):
        assert_dev_seed(seed)
        self.seed = seed
        self.prefix = list(prefix)
        self.env = env or H.make_env()
        self.obs, _ = self.env.reset(seed=seed)
        self.space = list(self.env.env.language_action_space)
        self.done = False
        self.divergence = []          # actions taken past the prefix
        for a in self.prefix:
            self._raw_step(a)
            if self.done:
                break

    def _raw_step(self, a):
        if a not in self.space:
            a = "search"
        self.obs, r, term, trunc, info = self.env.step(a)
        self.done = term or trunc
        return self.obs

    def step(self, a):
        """One divergent action; returns (brief, done)."""
        self.divergence.append(a)
        self._raw_step(a)
        return obs_brief(self.obs), self.done

    def script(self, actions):
        """Run a scripted sequence; returns transcript [(action, brief)]."""
        out = []
        for a in actions:
            if self.done:
                break
            brief, _ = self.step(a)
            out.append((a, brief))
        return out

    def sig(self):
        return state_sig(self.obs)

    def close(self):
        self.env.close()


def agent_prefix(seed, n_steps, flags_note=""):
    """Run the real DiveAgent for n_steps on a dev seed; return the exact
    env-level action list (post legality-substitution) + final brief.
    This is how 'wherever the agent actually is at step N' becomes a
    snapshot other branches can replay to."""
    assert_dev_seed(seed)
    env = H.make_env()
    obs, _ = env.reset(seed=seed)
    space = list(env.env.language_action_space)
    agent = DiveAgent(log=lambda *a, **k: None)
    agent.set_actions(space)
    actions = []
    done = False
    steps = 0
    while not done and steps < n_steps:
        a = agent.act(obs)
        if a not in space:
            a = "search"
        actions.append(a)
        obs, r, term, trunc, info = env.step(a)
        done = term or trunc
        steps += 1
    brief = obs_brief(obs)
    sig = state_sig(obs)
    env.close()
    return {"seed": seed, "n_steps": steps, "actions": actions,
            "final_brief": brief, "sig": sig, "done": done,
            "agent_role": agent.role, "flags": flags_note}


def verify_determinism(seed=805, n_steps=300):
    """Session gate: same prefix twice => same signature. Run before any
    probe batch; failure means STOP (env/version drift)."""
    p1 = agent_prefix(seed, n_steps)
    b = Branch(seed, p1["actions"])
    ok = b.sig() == p1["sig"]
    b.close()
    return ok, p1["sig"]


def save_probe(record, name):
    """Probe records: results/e16_probes/<name>.json (append-numbered)."""
    record.setdefault("model", "Fable 5 (max reasoning)")
    record.setdefault("when", time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                            time.gmtime()))
    i = 0
    while True:
        fn = os.path.join(PROBE_DIR, f"{name}{'' if i == 0 else '_%d' % i}.json")
        if not os.path.exists(fn):
            break
        i += 1
    with open(fn, "w") as f:
        json.dump(record, f, indent=1)
    return fn

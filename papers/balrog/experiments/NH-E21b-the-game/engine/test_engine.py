"""
NH-E21b engine — MODEL: Sonnet subagent, spec by Fable 5 (max), Phase L session 1.

test_engine.py — engine test suite.

Run with:  python3 -m unittest test_engine -v
(or just:  python3 test_engine.py)

Asserts:
  - determinism: same (template_id, seed), same action sequence => identical
    event-message streams.
  - the cheating reference solver solves all 6 templates for seeds 0-19.
  - the baseline agent FAILS T1 for all seeds (proves the counterintuitive
    damage-as-key gate actually requires a deliberate self-harming play a
    no-intuition agent will never make).
  - the knowledge log accumulates facts over an episode.
"""

from __future__ import annotations

import unittest

import game as game_mod
import templates
from baseline_agent import BaselineAgent
from knowledge import KnowledgeLog


class TestDeterminism(unittest.TestCase):
    def test_same_seed_same_events(self):
        for tid in templates.ALL_TEMPLATE_IDS:
            for seed in (0, 5, 17):
                env_a = game_mod.Game(max_steps=200)
                obs_a = env_a.reset(tid, seed)
                actions = templates.reference_solution(env_a.world)

                env_b = game_mod.Game(max_steps=200)
                obs_b = env_b.reset(tid, seed)

                self.assertEqual(obs_a["messages"], obs_b["messages"],
                                  f"{tid} seed={seed}: reset messages differ")
                self.assertEqual(obs_a["grid"], obs_b["grid"],
                                  f"{tid} seed={seed}: reset grid differs")

                stream_a, stream_b = [], []
                done_a = done_b = False
                for act in actions:
                    if not done_a:
                        oa, done_a, _ = env_a.step(act)
                        stream_a.append(list(oa["messages"]))
                    if not done_b:
                        ob, done_b, _ = env_b.step(act)
                        stream_b.append(list(ob["messages"]))
                self.assertEqual(stream_a, stream_b,
                                  f"{tid} seed={seed}: event streams diverged under identical actions")

    def test_different_seeds_differ(self):
        # sanity: across a handful of seeds, flavor text / bindings should
        # vary (proving the RNG is actually wired into world generation,
        # not just a fixed layout with a fixed seed baked in)
        seen_signatures = set()
        for seed in range(6):
            env = game_mod.Game()
            env.reset("T1", seed)
            gt = env.world.ground_truth
            seen_signatures.add((gt["hazard_item_pos"], gt["magnitude"], gt["gate_threshold"]))
        self.assertGreater(len(seen_signatures), 1,
                            "ground truth bindings should vary across seeds")


class TestReferenceSolverSolvesAllTemplates(unittest.TestCase):
    def test_solves_seeds_0_to_19(self):
        failures = []
        for tid in templates.ALL_TEMPLATE_IDS:
            for seed in range(20):
                env = game_mod.Game(max_steps=200)
                env.reset(tid, seed)
                actions = templates.reference_solution(env.world)
                done, win, info = False, False, {}
                for act in actions:
                    if done:
                        break
                    _, done, info = env.step(act)
                    win = info["win"]
                if not win:
                    failures.append((tid, seed, info))
        self.assertEqual(failures, [], f"reference solver failed on: {failures}")

    def test_mechanics_fully_discovered_when_solved(self):
        expected_totals = {"T1": 2, "T2": 2, "T3": 3, "T4": 3, "T5": 3, "T6": 4}
        for tid, expected in expected_totals.items():
            env = game_mod.Game(max_steps=200)
            env.reset(tid, 0)
            actions = templates.reference_solution(env.world)
            done, info = False, {}
            for act in actions:
                if done:
                    break
                _, done, info = env.step(act)
            self.assertEqual(info["mechanics_total"], expected, f"{tid} mechanic count")
            self.assertEqual(info["mechanics_discovered"], expected,
                              f"{tid}: solving it should discover every mechanic")


class TestBaselineFailsCounterintuitiveGates(unittest.TestCase):
    def _run_baseline(self, tid: str, seed: int, max_steps: int = 200) -> dict:
        env = game_mod.Game(max_steps=max_steps)
        obs = env.reset(tid, seed)
        agent = BaselineAgent(seed=seed)
        done, info = False, {}
        while not done:
            action = agent.act(obs)
            obs, done, info = env.step(action)
        return info

    def test_baseline_fails_T1_all_seeds(self):
        for seed in range(10):
            info = self._run_baseline("T1", seed)
            self.assertFalse(info["win"], f"T1 seed={seed}: baseline should never solve the "
                              f"damage-as-key gate (it never voluntarily eats)")

    def test_baseline_fails_T5_all_seeds(self):
        for seed in range(10):
            info = self._run_baseline("T5", seed)
            self.assertFalse(info["win"], f"T5 seed={seed}: baseline should never solve "
                              f"sacrifice-info (it never voluntarily eats)")

    def test_baseline_fails_T6_all_seeds(self):
        for seed in range(10):
            info = self._run_baseline("T6", seed)
            self.assertFalse(info["win"], f"T6 seed={seed}: baseline should never solve "
                              f"double-override (it never eats or drops)")


class TestKnowledgeLog(unittest.TestCase):
    def test_accumulates_facts_over_episode(self):
        env = game_mod.Game(max_steps=200)
        obs = env.reset("T1", 0)
        klog = KnowledgeLog()
        klog.ingest(0, obs["messages"], obs["state"])
        actions = templates.reference_solution(env.world)
        step_no = 0
        done = False
        for act in actions:
            if done:
                break
            obs, done, _ = env.step(act)
            step_no += 1
            klog.ingest(step_no, obs["messages"], obs["state"])
        self.assertGreater(len(klog.facts), 0, "knowledge log should have accumulated facts")
        tags = {f["tag"] for f in klog.facts}
        self.assertIn("effect_hp", tags, "eating the hazardous fruit should log an effect_hp fact")
        self.assertIn("gate", tags, "crossing the gate should log a gate fact")
        # serialization round-trips
        d = klog.to_dict()
        restored = KnowledgeLog.from_dict(d)
        self.assertEqual(len(restored.facts), len(klog.facts))

    def test_no_duplicate_facts_for_repeated_identical_messages(self):
        klog = KnowledgeLog()
        klog.ingest(0, ["You feel life drain away! [-10 HP]"], {})
        klog.ingest(1, ["You feel life drain away! [-10 HP]"], {})
        self.assertEqual(len(klog.facts), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

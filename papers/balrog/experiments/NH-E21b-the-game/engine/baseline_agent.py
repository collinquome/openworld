"""
NH-E21b engine — MODEL: Sonnet subagent, spec by Fable 5 (max), Phase L session 1.

baseline_agent.py — the no-intuition scripted baseline (ablation arm b/d).

Policy, purely from obs (no ground truth access):
  1. Explore systematically — BFS to the nearest visible, passable,
     not-yet-visited tile; this naturally re-attempts any adjacent closed
     gate on every single turn (a hard-avoid-damage agent has nothing
     better to do while stuck), which is exactly how a step-parity gate
     (T2) eventually gets cracked with zero special-casing.
  2. Hard avoid-damage constraint: any tile that has ever been experienced
     as damaging (an event message mentioning HP drain while standing
     there, or a discovered hazard glyph '^') is permanently excluded from
     the passable set.
  3. Interact with every interactable it stands on, exactly once.
  4. Pick up every item it stands on.
  5. It NEVER eats and NEVER drops inventory items — those are precisely
     the counterintuitive, self-harming/self-sacrificing moves this
     benchmark is designed around. A policy with no notion of deliberate
     self-harm or deliberate sacrifice will therefore solve T2/T3/T4-ish
     worlds (pure explore/carry/interact puzzles) but fails T1/T5/T6 BY
     CONSTRUCTION — that's the ablation's whole point.
"""

from __future__ import annotations

import random
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

Coord = Tuple[int, int]
DIRS = [("up", (0, -1)), ("down", (0, 1)), ("left", (-1, 0)), ("right", (1, 0))]


class BaselineAgent:
    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)
        self._reset_episode_state()

    def _reset_episode_state(self) -> None:
        self.visited: Set[Coord] = set()
        self.hazard_positions: Set[Coord] = set()
        self.interacted: Set[Coord] = set()
        self.picked_up_positions: Set[Coord] = set()
        self.known_items: Set[Coord] = set()
        self.known_interactables: Set[Coord] = set()

    def reset(self) -> None:
        self._reset_episode_state()

    # -----------------------------------------------------------------

    def act(self, obs: dict, knowledge_log=None) -> str:
        grid: List[str] = obs["grid"]
        state = obs["state"]
        messages = obs["messages"]
        pos: Coord = tuple(state["pos"])
        self.visited.add(pos)

        if any("drain away" in m.lower() for m in messages):
            self.hazard_positions.add(pos)

        height = len(grid)
        for y in range(height):
            row = grid[y]
            for x, ch in enumerate(row):
                if ch in (" ", "#", ".", "+", "^", "@"):
                    continue
                if ch.isdigit():
                    self.known_items.add((x, y))
                elif ch.isalpha() and ch.isupper():
                    self.known_interactables.add((x, y))

        def passable(x: int, y: int) -> bool:
            if not (0 <= y < height and 0 <= x < len(grid[y])):
                return False
            ch = grid[y][x]
            if ch in (" ", "#", "^"):
                return False
            if (x, y) in self.hazard_positions:
                return False
            return True

        # 1. interact with anything we're standing on, once
        if pos in self.known_interactables and pos not in self.interacted:
            self.interacted.add(pos)
            return "interact"

        # 2. pick up anything we're standing on
        if pos in self.known_items and pos not in self.picked_up_positions:
            self.picked_up_positions.add(pos)
            self.known_items.discard(pos)
            return "pickup"

        # 3. systematic frontier exploration (also re-attempts adjacent
        # closed gates every turn, for free)
        target = self._nearest_frontier(grid, pos, passable, height)
        if target is not None:
            path = self._bfs_path(pos, target, passable, height)
            if path:
                return path[0]

        return "wait"

    # -----------------------------------------------------------------

    def _nearest_frontier(self, grid, start: Coord, passable, height: int) -> Optional[Coord]:
        q = deque([start])
        seen = {start}
        while q:
            cur = q.popleft()
            if cur != start and cur not in self.visited:
                return cur
            x, y = cur
            for _, (dx, dy) in DIRS:
                nxt = (x + dx, y + dy)
                if nxt in seen or not passable(*nxt):
                    continue
                seen.add(nxt)
                q.append(nxt)
        return None

    def _bfs_path(self, start: Coord, goal: Coord, passable, height: int) -> List[str]:
        q = deque([start])
        came: Dict[Coord, Optional[Tuple[Coord, str]]] = {start: None}
        while q:
            cur = q.popleft()
            if cur == goal:
                break
            for name, (dx, dy) in DIRS:
                nxt = (cur[0] + dx, cur[1] + dy)
                if nxt in came or not passable(*nxt):
                    continue
                came[nxt] = (cur, name)
                q.append(nxt)
        if goal not in came:
            return []
        moves = []
        cur = goal
        while came[cur] is not None:
            prev, name = came[cur]
            moves.append(name)
            cur = prev
        moves.reverse()
        return moves

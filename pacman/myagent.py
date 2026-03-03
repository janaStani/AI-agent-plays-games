#!/usr/bin/env python3
from game.controllers import PacManControllerBase
from game.pacman import Game, Direction
import sys
from os.path import dirname

sys.path.append(dirname(dirname(dirname(__file__))))
from search_templates import Problem, Solution
from ucs import ucs
from typing import List, Optional
import time

class PacManProblem(Problem):
    def __init__(self, game: Game, max_depth: int = 50):
        self.game = game
        self.max_depth = max_depth
        self.pacman_node = game.pac_loc
        self.goals = []
        self._collect_goals()

    def _collect_goals(self):
        """Collect all goal nodes with priority (higher = better)"""
        self.goals = []
        
        # 1. Power Pills (highest priority)
        for node in self.game.get_active_power_pills_nodes():
            self.goals.append((node, 1000))

        # 2. Edible Ghosts (prioritize closer ones)
        for g in range(len(self.game.ghost_locs)):
            if self.game.is_edible(g):
                ghost_node = self.game.ghost_locs[g]
                dist = self.game.get_path_distance(self.pacman_node, ghost_node)
                if dist >= 0:
                    self.goals.append((ghost_node, 500 - dist * 2))

        # 3. Fruit
        if self.game.fruit_loc != -1:
            self.goals.append((self.game.fruit_loc, 300))

        # 4. Regular Pills (only if few left, to avoid too many goals)
        active_pills = self.game.get_active_pills_nodes()
        if len(active_pills) < 20:  # Limit to avoid explosion
            for node in active_pills[:10]:  # Top 10 closest
                self.goals.append((node, 10))

        # Sort by priority descending
        self.goals.sort(key=lambda x: x[1], reverse=True)

    # FIXED: Make it a METHOD, not property
    def initial_state(self):
        return self.game.pac_loc

    def is_goal(self, state) -> bool:
        """Check if state has edible entity"""
        # Power pill
        pp_index = self.game.get_power_pill_index(state)
        if pp_index >= 0 and self.game.check_power_pill(pp_index):
            return True
        
        # Regular pill  
        pill_index = self.game.get_pill_index(state)
        if pill_index >= 0 and self.game.check_pill(pill_index):
            return True
            
        # Fruit
        if self.game.fruit_loc == state:
            return True
            
        # Edible ghost
        for g in range(len(self.game.ghost_locs)):
            if self.game.ghost_locs[g] == state and self.game.is_edible(g):
                return True
                
        return False

    def actions(self, state) -> List[int]:
        """All valid directions (no reverse filtering for UCS)"""
        neighbors = self.game._graph[state].neighbors
        return [d for d in range(4) if neighbors[d] != -1]

    def result(self, state, action) -> int:
        return self.game.get_neighbor(state, action)

    def cost(self, state, action) -> float:
        next_node = self.result(state, action)
        cost = 1.0

        # DANGER: Non-edible ghosts
        for g in range(len(self.game.ghost_locs)):
            if not self.game.is_edible(g):
                ghost_node = self.game.ghost_locs[g]
                dist = self.game.get_path_distance(next_node, ghost_node)
                if dist == 0:
                    return float('inf')  # Instant death = impossible
                elif dist <= 2:
                    cost += 100
                elif dist <= 4:
                    cost += 20
                elif dist <= 6:
                    cost += 5

        # REWARD: Good targets
        pp_index = self.game.get_power_pill_index(next_node)
        if pp_index >= 0 and self.game.check_power_pill(pp_index):
            cost *= 0.3  # Big discount for power pills
        
        pill_index = self.game.get_pill_index(next_node)
        if pill_index >= 0 and self.game.check_pill(pill_index):
            cost *= 0.8  # Small discount for pills

        if self.game.fruit_loc == next_node:
            cost *= 0.4

        return max(cost, 0.1)  # Minimum cost > 0

class MyAgent(PacManControllerBase):
    def __init__(self, human: bool = False, seed: int = 0, verbose: bool = False):
        super().__init__(human, seed, verbose)

    def tick(self, game: Game) -> None:
        problem = PacManProblem(game, max_depth=30)
        solution = ucs(problem)

        if solution and len(solution.actions) > 0:
            # Take first action from optimal path
            action = solution.actions[0]
            self.pacman.set(action)
        else:
            # Smart fallback: safest direction
            directions = game.get_possible_pacman_dirs(True)
            if not directions:
                self.pacman.set(Direction.STOP)
                return

            best_dir = directions[0]
            best_score = float('-inf')
            
            for d in directions:
                next_node = game.get_neighbor(game.pac_loc, d)
                score = 0
                
                # Reward edible ghosts, penalize dangerous ones
                for g in range(len(game.ghost_locs)):
                    dist = game.get_path_distance(next_node, game.ghost_locs[g])
                    if game.is_edible(g):
                        score += 100 / max(dist, 1)
                    else:
                        if dist <= 2:
                            score -= 1000
                        else:
                            score -= 10 / max(dist, 1)
                
                # Prefer power pills
                pp_idx = game.get_power_pill_index(next_node)
                if pp_idx >= 0 and game.check_power_pill(pp_idx):
                    score += 500
                    
                if score > best_score:
                    best_score = score
                    best_dir = d
            
            self.pacman.set(best_dir)
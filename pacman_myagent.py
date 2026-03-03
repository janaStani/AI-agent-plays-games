#!/usr/bin/env python3
from game.controllers import PacManControllerBase
from game.pacman import Game, Direction

# from game.pac_gui import PacView
import sys
from os.path import dirname

# hack for importing from parent package
sys.path.append(dirname(dirname(dirname(__file__))))   
from search_templates import *
from ucs import ucs                                    # import the implementation of ucs
from typing import List, Optional
import time

# we create search problem for UCS to work on
class PacManProblem(Problem):
    def __init__(self, game: Game, max_depth: int = 50):
        self.game = game                  
        self.max_depth = max_depth
        self.pacman_node = game.pac_loc     # save pacmans current maze location
        self.goals = []                     # list of goal nodes
        self._collect_goals()

    def _collect_goals(self):
        """Collect all goal nodes with priority (higher = better)"""
        self.goals = []
        
        # 1. Power Pills (highest priority)
        for node in self.game.get_active_power_pills_nodes():        # find all active power pills
            self.goals.append((node, 1000))

        # 2. Edible Ghosts (prioritize closer ones)
        for g in range(len(self.game.ghost_locs)):              # loop through all ghost
            if self.game.is_edible(g):                          # check if ghost is edible 
                ghost_node = self.game.ghost_locs[g]               # get ghost current location
                dist = self.game.get_path_distance(self.pacman_node, ghost_node)    # compute the shortest path
                if dist >= 0:                                                    # -1 no path
                    self.goals.append((ghost_node, 500 - dist * 2))              # if ghost is closer, higher priority

        # 3. Fruit
        if self.game.fruit_loc != -1:                            # when there is no fruit value is -1
            self.goals.append((self.game.fruit_loc, 300))        # position of fruit, 300 is priority score (medium priority)

        # 4. Regular Pills (only if few left, to avoid too many goals)
        active_pills = self.game.get_active_pills_nodes()             # returns list of node indices where pills are still present in maze
        if len(active_pills) < 20:                             # add pills as goal only when fewer than 20 pills left
            for node in active_pills[:10]:                  # take justthe  first 10 
                self.goals.append((node, 10))               # give priority 10, (low priority)

        # after collecting all types of goals, sort by priority descending
        self.goals.sort(key=lambda x: x[1], reverse=True)

    # get starting state for search problem
    def initial_state(self):
        return self.game.pac_loc

    # check state of node
    def is_goal(self, state) -> bool:
        
        # Power pill, checks if node is power pill
        pp_index = self.game.get_power_pill_index(state)
        if pp_index >= 0 and self.game.check_power_pill(pp_index): # and if power pill is uneaten
            return True           # if both are true return true
        
        # Regular pill, checks if node is regular pill  
        pill_index = self.game.get_pill_index(state)
        if pill_index >= 0 and self.game.check_pill(pill_index): # and if pill is uneaten
            return True                       # if there is active regular pill here, return true
            
        # Fruit
        if self.game.fruit_loc == state:
            return True
            
        # loop over all ghosts
        for g in range(len(self.game.ghost_locs)):
            if self.game.ghost_locs[g] == state and self.game.is_edible(g):   # check if ghost is located on this node, and if there is a ghost check if its edible
                return True
                
        return False

    def actions(self, state) -> List[int]:
        """All valid directions (no reverse filtering for UCS)"""
        neighbors = self.game._graph[state].neighbors          # get list of the 4 neighbors of the current node (up, down, left, right), in no path exists -1
        return [d for d in range(4) if neighbors[d] != -1]      # loop trough directions, keep directions where neighbor exists, remove invalid moves
    # returns list of valid moves


    def result(self, state, action) -> int:
        return self.game.get_neighbor(state, action)      # return node that Pacman reaches if he moves in direction action

    def cost(self, state, action) -> float:
        next_node = self.result(state, action)           # where Pacman will be after taking the action
        cost = 1.0                                       # base movement cost

        # DANGER non-edible ghosts
        for g in range(len(self.game.ghost_locs)):       # loop over all ghost, check if not edible they are dangerous
            if not self.game.is_edible(g):
                ghost_node = self.game.ghost_locs[g]    # find ghost position
                dist = self.game.get_path_distance(next_node, ghost_node)     # compute shortest path between next step and ghost
                if dist == 0:
                    return float('inf')     # instant death, never make this move
                elif dist <= 2:       
                    cost += 100             # ghost very close, add danger cost 100
                elif dist <= 4:
                    cost += 20              # ghost kinda close, add danger cost 20
                elif dist <= 6:
                    cost += 5               # ghost nearby, add danger cost 5
        # UCS avoids dangerous paths by making them extremely expensive

        # REWARDS good targets
        pp_index = self.game.get_power_pill_index(next_node)             # is next node a power pill
        if pp_index >= 0 and self.game.check_power_pill(pp_index):
            cost *= 0.3                              # make cost cheaper, so UCS chooses the power pill
        
        pill_index = self.game.get_pill_index(next_node)                # is next node a pill
        if pill_index >= 0 and self.game.check_pill(pill_index):
            cost *= 0.8                              # Small discount for pills

        if self.game.fruit_loc == next_node:         # make cost cheaper but not as much as power pill 
            cost *= 0.4

        return max(cost, 0.1)  # Minimum cost > 0

# every game tick run ucs to calc best move
class MyAgent(PacManControllerBase):
    def __init__(self, human: bool = False, seed: int = 0, verbose: bool = False):
        super().__init__(human, seed, verbose)

    # called every moment Pacman must choose a move
    def tick(self, game: Game) -> None:
        problem = PacManProblem(game, max_depth=30)             # create search problem instance, max depth prevents UCS from searching forever
        solution = ucs(problem)                       # run ucs, start from current tile, explore possible paths, calc cost for each path, choose path with lowest cost
        # usc tries to find the beat path to target: pill, power pill, edible ghost, fruit, result stored in solution

        if solution and len(solution.actions) > 0:    # if solution exists, ucs found a path and found at least one move
            # Take first action from optimal path
            action = solution.actions[0]
            self.pacman.set(action)
        else:
            # smart fallback: safest direction
            # this code runs only when UCS did not return a usable path
            directions = game.get_possible_pacman_dirs(True)         # get legal directions
            if not directions:                                       # if there are no legal moves, exit
                self.pacman.set(Direction.STOP)
                return

            best_dir = directions[0]             
            best_score = float('-inf')
            

            # loop over each candidate direction
            for d in directions:
                next_node = game.get_neighbor(game.pac_loc, d)         # compute the tile pacman would be on if he moves d
                score = 0                                              # start score for this candidate move
                
                # go through ghosts
                for g in range(len(game.ghost_locs)):
                    dist = game.get_path_distance(next_node, game.ghost_locs[g])     # how many steps between candidate tile and ghost
                    if game.is_edible(g):                         # if ghost is edible
                        score += 100 / max(dist, 1)               # positive reward when ghost is closer
                    else:                                         # else ghost not edible
                        if dist <= 2:
                            score -= 1000                         # if ghost within 2 steps, hudge penalty
                        else:
                            score -= 10 / max(dist, 1)           # otherwise sub smaller penalty
                
                # check if candidate is power pills
                pp_idx = game.get_power_pill_index(next_node)
                if pp_idx >= 0 and game.check_power_pill(pp_idx):     # if there is an active power pill, add 500 to score
                    score += 500
                    
                if score > best_score:                          # if direction score is better than prev, remember this direction as current best
                    best_score = score 
                    best_dir = d
            
            self.pacman.set(best_dir)              # move to that direction

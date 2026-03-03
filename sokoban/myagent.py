#!/usr/bin/env python3
from game.action import *
from game.board import *
from game.artificial_agent import ArtificialAgent
from dead_square_detector import detect
from typing import List, Tuple, FrozenSet
import sys
from time import perf_counter
from os.path import dirname

# Import your A* implementation
sys.path.append(dirname(dirname(dirname(__file__))))
from astar import AStar
from search_templates import HeuristicProblem, Solution


class MyAgent(ArtificialAgent):
    @staticmethod
    def think(board: Board, optimal: bool, verbose: bool) -> List[EDirection]:
        start_time = perf_counter()

        problem = SokobanProblem(board.clone(), verbose=verbose)
        solution: Solution = AStar(problem)

        if solution is None:
            if verbose:
                print("No solution found!")
            return []

        # Extract only the directions
        directions = [action.get_direction() for action in solution.actions]

        if verbose:
            print(f"Solution length: {len(directions)} moves")
            print(f"Nodes explored : {problem.nodes_explored}")
            print(f"Time           : {perf_counter() - start_time:.2f}s")

        return directions


class SokobanProblem(HeuristicProblem):
    def __init__(self, initial_board: Board, verbose: bool = False):
        self.initial_board = initial_board
        self.dead_squares = detect(initial_board)           # pre-computed dead squares
        self.goals = self._collect_goals()
        self.goal_list = list(self.goals)
        self.verbose = verbose
        self.nodes_explored = 0

    def _collect_goals(self) -> FrozenSet[Tuple[int, int]]:
        goals = set()
        b = self.initial_board
        for x in range(b.width):
            for y in range(b.height):
                if ETile.is_target(b.tile(x, y)):
                    goals.add((x, y))
        return frozenset(goals)

    def initial_state(self):
        return self._minimal_state(self.initial_board)

    def is_goal(self, state) -> bool:
        boxes = state[1]                                 # frozenset of box positions
        return boxes.issubset(self.goals)

    def actions(self, state) -> List[Action]:
        board: Board = state[0]
        self.nodes_explored += 1

        possible: List[Action] = []

        # simple moves (no box push)
        for m in Move.get_actions():
            if m.is_possible(board):
                possible.append(m)

        # pushes – with dead-square pruning
        for p in Push.get_actions():
            if not p.is_possible(board):
                continue

            dir = p.get_direction()
            sx, sy = board.sokoban                     
            bx = sx + dir.dx
            by = sy + dir.dy
            new_bx = bx + dir.dx
            new_by = by + dir.dy

            # prune pushes that place a box on a dead square
            if self.dead_squares[new_bx][new_by]:
                continue

            possible.append(p)

        return possible

    def result(self, state, action: Action):
        new_board: Board = state[0].clone()
        action.perform(new_board)
        return self._minimal_state(new_board)

    def cost(self, state, action: Action) -> float:
        return 1.0                                          # every action costs 1

    def estimate(self, state) -> float:
        """Admissible heuristic: sum of minimal Manhattan distances (greedy assignment)"""
        boxes = list(state[1])
        if not boxes:
            return 0.0

        total = 0.0
        used = set()

        for bx, by in boxes:
            best = float('inf')
            for gx, gy in self.goal_list:
                if (gx, gy) in used:
                    continue
                dist = abs(bx - gx) + abs(by - gy)
                if dist < best:
                    best = dist
            total += best
            # mark the closest goal as used (lower bound → admissible)
            if best != float('inf'):
                # find and mark it
                for g in self.goal_list:
                    if (abs(bx - g[0]) + abs(by - g[1])) == best and g not in used:
                        used.add(g)
                        break

        return total

    
    # compact and hashable representation of a state
    def _minimal_state(self, board: Board) -> Tuple[Board, FrozenSet[Tuple[int, int]]]:
        boxes = set()
        for x in range(board.width):
            for y in range(board.height):
                if ETile.is_box(board.tile(x, y)):
                    boxes.add((x, y))
        return (board, frozenset(boxes))
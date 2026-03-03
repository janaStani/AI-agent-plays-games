#!/usr/bin/env python3
from search_templates import Solution, HeuristicProblem
from typing import Optional, Any, List, Dict
from dataclasses import dataclass, field
import heapq


"""
search_templates.py contains:
    Problem (base class)
    HeuristicProblem (inherits from Problem + adds estimate)
    Solution (the return type)
problem.py contains actual puzzles 
    Each puzzle class inherits from HeuristicProblem and implements all the methods above
"""



# We need to store f = g + h in the Node for priority
@dataclass(order=True)
class Node:
    f: float = field(default=0.0, init=True)                    # f is the key used for heap ordering and comparing, used to pick nodest with smallest f, f = g + h
    g: float = field(default=0.0, compare=False)                # the real path cost from start to tis node, don’t use it when sorting nodes
    state: Any = field(default=None, compare=False)             # the actual puzzle state, must have default
    action: Any = field(default=None, compare=False)            # action taken from the parent to reach node, used for reconstructing 
    parent: Optional["Node"] = field(default=None, compare=False)   # link to the parent Node so we can rebuild the action path when we reach the goal.

    # walk backwards from goal to start, collecting actions
    # reverse list give correct order start to goal
    def extract_actions(self) -> List[Any]:
        actions = []
        node = self
        while node.parent is not None:
            actions.append(node.action)
            node = node.parent
        actions.reverse()
        return actions


# main function take any puzzle with heuristic, return solution or None
def AStar(prob: HeuristicProblem) -> Optional[Solution]:
    """A* search using f(n) = g(n) + h(n)"""
    
    start_state = prob.initial_state()          # starting position of puzzle

    if prob.is_goal(start_state):              # already at the goal, empty solution
        return Solution([], start_state, 0)

    # Create start node
    h = prob.estimate(start_state)       # heuristic from start to goal, estimated remaining cost to goal from start
    start_node = Node(f=h, g=0, state=start_state, action=None, parent=None) # g = 0 no cost jet, f = 0 + h

    frontier = []                                 # always pops node with smallest f
    heapq.heappush(frontier, start_node)          # start node goes firs into frontier (priority queue)

    # keep track of best g-cost found for each state, cheapest way to reach state
    best_g: Dict[Any, float] = {start_state: 0}

    explored = set()     # states we have fully expanded


    # keep going untill no more nodes to try
    while frontier:
        current = heapq.heappop(frontier)          # take the best node lowest f value

        # skip if we already found a better way to this state
        if current.state in explored:
            continue
        if best_g.get(current.state, float('inf')) < current.g:
            continue

        explored.add(current.state) # expand state

        # goal found, reconstruct path and return the solution
        if prob.is_goal(current.state):
            return Solution(current.extract_actions(), current.state, current.g)

        # try every possible move from current position.
        for action in prob.actions(current.state):
            
            child_state = prob.result(current.state, action)       # state after move
            step_cost = prob.cost(current.state, action)           # cost of move
            tentative_g = current.g + step_cost                    # new total path cost g

            # if we already reached child_state with better/equal cost, skip
            if tentative_g >= best_g.get(child_state, float('inf')):
                continue

            # found a better path, update
            best_g[child_state] = tentative_g
            h_child = prob.estimate(child_state)    # compute heuristic for child
            f_child = tentative_g + h_child         # compute f = g + h (only once!)

            # create new node with correct f-value
            child_node = Node(
                f=f_child,
                g=tentative_g,
                state=child_state,
                action=action,
                parent=current
            )
            heapq.heappush(frontier, child_node)   # push into priority queue, will be picked later if it’s good

    return None    # if frontier is empty and no goal found, no solution exists
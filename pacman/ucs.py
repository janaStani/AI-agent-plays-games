#!/usr/bin/env python3
from search_templates import Problem, Solution
from typing import Optional, Any, List, Dict, Tuple
from dataclasses import dataclass, field
import heapq



@dataclass(order=True)    # make class sortable
class Node:
    path_cost: float       # total cost from start node to this node, used for priority ordering (UCS uses this to decide which node to expand first)
    state: Any = field(compare=False)      # current position in the problrm, e.g. position in a maze, we sort nodes by cost, the state doesn’t affect the order
    action: Any = field(compare=False)     # action that led to this node from its parent (Used later to reconstruct the full path)
    parent: Optional["Node"] = field(compare=False, default=None)       # reference to previous Node we came from, for reconstructing solution path

    # reconstructs full action path, get list of moves from start to this node
    def extract_actions(self) -> List[Any]:
        actions = []                            # start from this node, usually the goal
        node = self              
        while node.parent is not None:          # go up the tree until root is reached
            actions.append(node.action)         # add the action that led to this node
            node = node.parent                  
        actions.reverse()                       # we collected actions from goal to start, so we reverse to get start → goal
        return actions                          # return final ordered list of actions that solves the problem


# the main Uniform-Cost Search function
# run usc on Problem and return Solution with cheapest action sequence
# or None if no solution exists
def ucs(prob: Problem) -> Optional[Solution]:

    start = prob.initial_state()              # get starting state of problem, where search begins

    # check if start state is already a goal
    if prob.is_goal(start):
        return Solution([], start, 0)              # if yes return solution with empty action list, the start state itself, and path cost 0

    # frontier is a priority queue implemented as a list (min-heap)
    frontier: List[Node] = []                # frontier stores nodes to be expanded, ordered by path_cost (lowest cost first)
    start_node = Node(path_cost=0, state=start, action=None, parent=None)    # start state with path_cost = 0, no parent, no action
    heapq.heappush(frontier, start_node)       # inserts start_node into heap so it can be popped in cost order

    # frontier lookup: state -> lowest known cost
    frontier_costs: Dict[Any, float] = {start: 0}

    # Explored set
    explored: set = set()          # hold states that have already been expanded

    # go through nodes in frontier
    while frontier:
        node = heapq.heappop(frontier)      # remove and return node with lowest path_cost from the frontier

        # if state of popped node is in explored, we already expanded that state via a cheaper path
        if node.state in explored:
            continue
        if frontier_costs.get(node.state, float("inf")) < node.path_cost:
            continue
        # if frontier_costs contains smaller cost for the same state, skip it

        explored.add(node.state)    # mark current state as expanded

        # Goal?
        if prob.is_goal(node.state):
            return Solution(node.extract_actions(), node.state, node.path_cost)       # reconstruct actions from start to this node

        # Expand
        for action in prob.actions(node.state):               # iterate through actions we can take in current state 
            child_state = prob.result(node.state, action)     # compute new state after applying acion
            cost = node.path_cost + prob.cost(node.state, action)    # path cost to reach that child

            # for each child check to se lowest cost we already know in frontier, if we dont assume inf
            old_cost = frontier_costs.get(child_state, float("inf"))
            if cost < old_cost:                                     # if new comp cost is cheaper then we update
                frontier_costs[child_state] = cost
                child_node = Node(cost, child_state, action, node)  # create new object child_node whose parent is the node we expanded and whose action is the action that lead to it
                heapq.heappush(frontier, child_node)             # push 

    return None  # No solution found

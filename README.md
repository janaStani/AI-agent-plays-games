# AI-agent-plays-games
AI assignments, implementation of AI agents that play different games using different approaches

Dino
* Rule-based agent
* Simple implementation of Google Chrome T-Rex. The goal is to control tyrannosaurus so he won't collide with obstacles, cactuses and birds for as long as possible, while it slowly accelerates.

Pac-Man	
* General-purpose implementation of uniform-cost search, its able to search any problem implementing Problem interface, that can be found in search_templates.py. Search returns Solution instance if solution is found, otherwise None.
* Pac-Man agent uses search-based decision making to navigate the maze intelligently. On each game tick, the agent models the maze as a graph where nodes represent positions and edges represent possible movements.
* Agent uses the UCS algorithm to compute optimal paths, targets pills, fruits, or edible ghosts as goal states, assigns higher movement costs to positions near ghosts to avoid danger, chooses the first action from the optimal solution path

Sokoban	
* General-purpose implementation of A* search, its able to search any problem implementing HeuristicProblem interface (can be found in search_templates.py), which extends Problem from the previous assignment by method estimate. Search returns Solution instance if a solution is found, otherwise None (as in the previous assignment).
* Sokoban is a puzzle game where the player pushes boxes onto designated goal squares. The complexity arises from irreversible moves and dead positions that can make a level unsolvable. The agent works as follows: models Sokoban as a HeuristicProblem, uses A* search to find an optimal sequence of moves, applies a custom admissible and consistent heuristic, and prunes invalid states using dead square detection

Cell Wars	
* Search algorithm implemented using the minmax with alpha-beta pruning
* Implements an agent for the Cell Wars game using search-based decision making. The agent models the game as a graph of cells with mass and ownership and makes strategic transfer decisions to expand territory and defeat the opponent. The solution leverages Minimax with alpha–beta pruning to evaluate game states and choose optimal actions. For Minimax, a heuristic evaluation function estimates the desirability of positions when the search depth limit is reached

Minesweeper	
* Backtracking search for CSPs (Constraint Satisfaction Problem), each constraint specifies that exactly k variables from a subset must be True. The solver includes: forward checking (constraint propagation), which infers variable values using propagation similar to AC-3. Backtracking search with inference uses degree heuristic for variable selection and maintains arc consistency during search. Proof-by-contradiction inference (infer_var) determines forced variable values by testing satisfiability. The implementation efficiently detects contradictions, propagates constraints, and finds solutions while respecting time limits.
* Using the CSP solver, I implemented an intelligent Minesweeper agent. The agent: models each tile as a Boolean variable (mine / no mine), adds constraints based on revealed numbers, uses forward checking to infer safe tiles and mines, applies contradiction-based inference when propagation alone is insufficient, and requests hints only when logically necessary.

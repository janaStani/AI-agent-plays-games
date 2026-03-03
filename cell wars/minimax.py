#!/usr/bin/env python3
from minimax_templates import *       # import all base classes

class Minimax(Strategy):
    
    def __init__(self, game: HeuristicGame, limit: int = 0, seed: Optional[int] = None) -> None:
        super().__init__(seed)
        self.game = game
        self.limit = limit

    # get best move for given state
    def action(self, state) -> object:
        current = self.game.clone(state)                  # copy so we won’t modify original game state

        # get all possible moves for current player
        actions = self.game.actions(current)
        if not actions:                        # in no moves available, return
            return None

        # which players turn
        maximizing = (self.game.player(current) == 1)  

        # move ordering, center columns first (good for Connect Four)
        if hasattr(self.game, 'width'):
            width = self.game.width() if callable(self.game.width) else self.game.width
            actions = sorted(actions, key=lambda a: abs(a - width // 2))   # smaller distance to center, higher priority

        best_action = actions[0]                      # current best move
        best_value = float('-inf') if maximizing else float('inf')       # best score found so far
        alpha = float('-inf')                         # current best maximizing value along the path
        beta = float('inf')                           # current best minimizing value along the path

        # loop through each action, loop over all possible moves at the current state
        for action in actions:
            child = self.game.clone(current)            # copy move
            self.game.apply(child, action)              # apply action
            
            # call recursively for next state, next player is the opponent
            value = self._minimax(child, depth=1, alpha=alpha, beta=beta, maximizing=not maximizing)

            # update best value and alpha/beta
            if maximizing:
                if value > best_value:               # choose move with highest value
                    best_value = value
                    best_action = action
                alpha = max(alpha, value)
            else:
                if value < best_value:              # choose move with lowest value
                    best_value = value
                    best_action = action
                beta = min(beta, value)

            if beta <= alpha:                  # no need to check further moves because they cannot affect result
                break 

        return best_action

    # recursive minmax function
    def _minimax(self, state, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        
        # base case if game is over
        if self.game.is_done(state):
            outcome = self.game.outcome(state)         # game outcome
            
            if outcome > 0:             # current player max wins
                return 1000 - depth     # win faster, higher score
            elif outcome < 0:           # did opponent win
                return -1000 + depth    # lose later, better than losing immediately
            else:
                return 0                # draw

        # if we reach the max search depth, stop search and estimate how good is position using heuristic
        if self.limit > 0 and depth >= self.limit:
            return self.game.evaluate(state)

        actions = self.game.actions(state)  # generate all possible moves

        # reorder at deeper levels too, for the connect four, explore center columns first
        if hasattr(self.game, 'width'):
            width = self.game.width() if callable(self.game.width) else self.game.width
            actions = sorted(actions, key=lambda a: abs(a - width // 2))

        # recursive evaluation
        if maximizing:                     # player 1s turn, highest score possible
            value = float('-inf')          # any real move will be better than -inf
            
            # try every legal move from the position
            for action in actions:
                child = self.game.clone(state)        # copy state
                self.game.apply(child, action)        # apply move
                
                # switch turn, compare score, keep max score
                value = max(value, self._minimax(child, depth + 1, alpha, beta, False))
                alpha = max(alpha, value)            # update, max best score
                if beta <= alpha:                    # stop checking remaining moves
                    break
            return value
        else:                                       # player 2s turn, lowest score possible
            value = float('inf')                    # any real move will be worse than +inf
            
            # try every legal move
            for action in actions:
                child = self.game.clone(state)      # copy state
                self.game.apply(child, action)      # apply move

                # recursevly evaluate position, switch turn, choose min score
                value = min(value, self._minimax(child, depth + 1, alpha, beta, True))
                beta = min(beta, value)             # update beta, best min score
                if beta <= alpha:                   # stop searching further, cannot improve final dec
                    break
            return value
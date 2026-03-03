# dead_square_detector.py
from game.board import Board, ETile
from game.action import EDirection
from typing import List, Tuple
from collections import deque

def detect(board: Board) -> List[List[bool]]:
    """
    Detect dead squares: positions where a box can never reach any goal,
    even with perfect Sokoban teleportation.
    Returns 2D list of bools: True = dead square
    """
    width = board.width
    height = board.height

    # mark reachable (alive) box positions
    alive = [[False for _ in range(height)] for _ in range(width)]

    # Directions: (dx, dy)
    directions = [
        (0, -1),   # up
        (0, 1),    # down
        (-1, 0),   # left
        (1, 0),    # right
    ]

    queue = deque()

    # find all goal positions and enqueue them as alive
    for x in range(width):
        for y in range(height):
            tile = board.tile(x, y)
            if ETile.is_target(tile):
                alive[x][y] = True
                queue.append((x, y))

    # BFS in reverse, find all positions from which we can reach a goal
    while queue:
        bx, by = queue.popleft()

        # try all 4 possible push directions (forward)
        for dx, dy in directions:
            # previous box position, bx - dx, by - dy
            prev_x = bx - dx
            prev_y = by - dy
            # player standing position before push, prev - dir = bx - 2*dx, by - 2*dy
            player_x = bx - 2 * dx
            player_y = by - 2 * dy

            # check bounds for previous box pos
            if not (0 <= prev_x < width and 0 <= prev_y < height):
                continue
            # check bounds for player pos
            if not (0 <= player_x < width and 0 <= player_y < height):
                continue

            # previous box position must not be wall
            if ETile.is_wall(board.tile(prev_x, prev_y)):
                continue

            # player standing position must not be wall
            if ETile.is_wall(board.tile(player_x, player_y)):
                continue

            # if not already alive, mark and enqueue
            if not alive[prev_x][prev_y]:
                alive[prev_x][prev_y] = True
                queue.append((prev_x, prev_y))

    # build dead map, wall or not alive = dead
    dead = [[False for _ in range(height)] for _ in range(width)]
    for x in range(width):
        for y in range(height):
            if ETile.is_wall(board.tile(x, y)) or not alive[x][y]:
                dead[x][y] = True

    return dead
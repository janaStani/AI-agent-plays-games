#!/usr/bin/env python3
from game.dino import *
from game.agent import Agent

class MyAgent(Agent):
    """High-speed reflex agent for Dino game with obstacle awareness."""
    
    duck_timer = 0
    jump_timer = 0
    
    def __init__(self) -> None:
        # Agent won't be initialized
        raise RuntimeError

    @staticmethod
    def get_move(game: Game) -> DinoMove:
        """
        Decide next move based on closest obstacle in danger zone.
        Uses variable jump heights for small/large cactuses and
        duck/jump/no-move for birds depending on vertical position.
        """
        dino = game.dino

        # danger distance calcu
        # base danger distance plus extra for high speeds
        danger_distance = 140 + 10 * (game.speed - 5) ** 1.3

        base_jump = int(40 - game.speed * 1.2)
        MyAgent.jump_timer = max(10, base_jump)


        if MyAgent.duck_timer > 0:
            MyAgent.duck_timer -= 1
            return DinoMove.DOWN
        
        # Handle ongoing jump timer (force fall after a short time)
        if MyAgent.jump_timer > 0:
            MyAgent.jump_timer -= 1
            # if timer is small and still jumping, press DOWN to fall sooner
            if MyAgent.jump_timer == 1:
                return DinoMove.DOWN
            else:
                return DinoMove.NO_MOVE


        # loop through obstacles in front
        for obs in game.obstacles:

            dx = obs.rect.x - dino.x   # horizontal distance
            
            if dx <= 0 or dx > danger_distance:
                continue  # skip obstacles behind or too far

            # Cactus handling (different jump durations)
            if "SMALL_CACTUS1" in obs.type.name:
                MyAgent.jump_timer = 16   # short jump, force fall soon
                return DinoMove.UP
            elif "SMALL_CACTUS2" in obs.type.name:
                MyAgent.jump_timer = 25
                return DinoMove.UP
            elif "SMALL_CACTUS3" in obs.type.name:
                MyAgent.jump_timer = 50   # medium jump
                return DinoMove.UP
            elif "LARGE_CACTUS1" in obs.type.name:
                MyAgent.jump_timer = 28   # long jump, no early fall
                return DinoMove.UP
            elif "LARGE_CACTUS2" in obs.type.name:
                MyAgent.jump_timer = 50   # long jump, no early fall
                return DinoMove.UP
            elif "LARGE_CACTUS3" in obs.type.name:
                MyAgent.jump_timer = 50   # long jump, no early fall
                return DinoMove.UP

            
            # bird handling
            elif "BIRD" in obs.type.name:
                
                y = obs.rect.y # obstacle vertical coordinate 
                
                if y < 230:  # high bird 
                    return DinoMove.NO_MOVE
                elif y < 280:  # middle bird
                    MyAgent.duck_timer = 30
                    return DinoMove.DOWN
                else:  # low bird
                    MyAgent.jump_timer = 50
                    return DinoMove.UP

        # no immediate threat, continue running
        return DinoMove.NO_MOVE

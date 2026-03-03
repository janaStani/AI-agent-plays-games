#!/usr/bin/env python3
import sys
from os.path import dirname, abspath
from math import ceil
from typing import List

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))

from game.agent import Agent
from game.cells import *
from minimax import Minimax


class CellsGame:
    """Wrapper for Minimax."""

    def clone(self, state: Game) -> Game:
        return state.clone()

    def player(self, state: Game) -> int:
        return state.current_player

    def actions(self, state: Game) -> list:
        me = state.current_player
        actions = []
        my_cells = state.get_player_cells(me)

        # Inside → Border reinforcement first
        inside_cells = [c for c in my_cells if not state.borders_enemy_cells(c.index, me)]
        border_cells = [c for c in my_cells if state.borders_enemy_cells(c.index, me)]

        for src in inside_cells + border_cells:
            if src.mass <= 1:
                continue
            # Use MAXIMAL for borders, MEDIUM for insides to allow more flexibility
            min_size = CellType.MAXIMAL.min_size if src in border_cells else CellType.MEDIUM.min_size
            available = src.mass - min_size
            if available <= 0:
                continue

            # Collect potential targets: enemies/neutrals for attacks, own for reinforcements
            targets = []
            for tgt in src.neighbors:
                tgt_owner = tgt.owner
                # Score for sorting later
                base_score = available
                if tgt_owner == me:
                    # Reinforce own: prioritize needy borders
                    if state.borders_enemy_cells(tgt.index, me):
                        base_score += 80  # High for border reinforce
                    else:
                        base_score += 30  # Lower for inside
                else:
                    # Attack: bonus if can capture, penalize if weak
                    attack_power = available * Game.ATTACK_MUL
                    if attack_power > tgt.mass:
                        base_score += 100 if state.borders_enemy_cells(tgt.index, 3 - me) else 50
                    else:
                        base_score -= 20  # Risky partial attack

                targets.append((tgt, base_score))

            # Sort targets by score desc
            targets.sort(key=lambda x: x[1], reverse=True)
            for tgt, _ in targets[:5]:  # Limit per src to top 5 targets
                # Discretize mass: 25%,50%,75%,100% to limit branching
                for frac in [0.25, 0.5, 0.75, 1.0]:
                    mass = max(1, int(available * frac))
                    if mass > 0:
                        actions.append((src.index, tgt.index, mass))

        # Global sort and limit
        def score(a):
            src_idx, tgt_idx, mass = a
            tgt_cell = state.get_cell(tgt_idx)
            tgt_owner = tgt_cell.owner
            bonus = 0
            if tgt_owner == me:
                bonus += 50 if state.borders_enemy_cells(tgt_idx, me) else 20
            else:
                attack_power = mass * Game.ATTACK_MUL
                bonus += 100 if attack_power > tgt_cell.mass else -10
                if state.borders_enemy_cells(tgt_idx, 3 - me):
                    bonus += 30
            return mass + bonus

        actions.sort(key=score, reverse=True)
        return actions[:100]  # Expanded limit

    def apply(self, state: Game, action) -> None:
        if not action: return
        src_idx, tgt_idx, mass = action
        mass = int(mass)
        src_mass = int(state.masses[src_idx])
        tgt_mass = int(state.masses[tgt_idx])
        tgt_owner = state.owners[tgt_idx]
        state.masses[src_idx] = src_mass - mass

        if tgt_owner == state.current_player:
            # Reinforce: just add
            state.masses[tgt_idx] = tgt_mass + mass
        else:
            # Attack
            damage = int(mass * Game.ATTACK_MUL)
            new_mass = tgt_mass - damage
            if new_mass <= 0:
                state.owners[tgt_idx] = state.current_player
                state.masses[tgt_idx] = -new_mass
            else:
                state.masses[tgt_idx] = new_mass

    def is_done(self, state: Game) -> bool:
        return (len(state.get_player_cells(0)) == 0 or
                len(state.get_player_cells(1)) == 0 or
                getattr(state, 'round', 0) >= getattr(state, 'round_limit', float('inf')))

    def outcome(self, state: Game) -> float:
        if len(state.get_player_cells(0)) == 0:
            return -1000
        if len(state.get_player_cells(1)) == 0:
            return 1000
        return 0

    def evaluate(self, state: Game) -> float:
        me = state.current_player
        opp = 3 - me

        my_cells_count = len(state.get_player_cells(me))
        opp_cells_count = len(state.get_player_cells(opp))
        my_mass = state.total_mass(me)
        opp_mass = state.total_mass(opp)

        score = my_cells_count * 60 - opp_cells_count * 60 + my_mass * 3 - opp_mass * 3

        # Reward potential captures and reinforcements
        for cell in state.get_player_cells(me):
            is_border = state.borders_enemy_cells(cell.index, me)
            min_size = CellType.MAXIMAL.min_size if is_border else CellType.MEDIUM.min_size
            available = cell.mass - min_size
            if available <= 0:
                continue

            for neigh in cell.neighbors:
                if neigh.owner != me:
                    attack_power = available * Game.ATTACK_MUL
                    if attack_power > neigh.mass:
                        if state.borders_enemy_cells(neigh.index, opp):
                            score += 120
                        else:
                            score += 40
                    else:
                        score -= 20
                else:
                    # Reinforce needy borders
                    if state.borders_enemy_cells(neigh.index, me) and neigh.mass < CellType.MAXIMAL.min_size * 1.5:
                        score += 50

        # Penalize vulnerable borders (SAFE VERSION)
        for cell in state.get_player_cells(me):
            if state.borders_enemy_cells(cell.index, me):
                enemy_threats = [n.mass * Game.ATTACK_MUL for n in cell.neighbors if n.owner == opp]
                if enemy_threats and cell.mass < max(enemy_threats):
                    score -= 40

        # Reward mass on the front line
        border_mass = sum(
            c.mass for c in state.get_player_cells(me)
            if state.borders_enemy_cells(c.index, me)
        )
        score += border_mass * 0.5

        return score


class myagent(Agent):
    def __init__(self):
        self.search = None

    def get_move(self, game: Game) -> List[Transfer]:
        if self.search is None:
            wrapper = CellsGame()
            self.search = Minimax(wrapper, limit=4)  # Reduce to 4 for speed, actions broader now

        best_action = self.search.action(game)
        if not best_action:
            return []

        src_idx, tgt_idx, mass = best_action
        src_cell = game.get_cell(src_idx)
        tgt_cell = game.get_cell(tgt_idx)

        move = TransferMove()
        move.add_transfer(Transfer(src_cell, tgt_cell, mass))
        return move.get_transfers()
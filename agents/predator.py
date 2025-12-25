"""
Predator Agent class
FIXED: Properly uses combat system for honour awards
"""
from typing import Tuple, Optional, List
from agents.base_agent import BaseAgent
import random


class Predator(BaseAgent):
    """Predator agent with honour, stamina, and clan mechanics"""

    def __init__(self, name: str, position: Tuple[int, int],
                 health: int = 100, stamina: int = 100, honour: int = 0,
                 is_dek: bool = False, clan_rank: str = "Unblooded"):
        super().__init__(name, position, health, health)
        self.stamina = stamina
        self.max_stamina = stamina
        self.honour = honour
        self.is_dek = is_dek
        self.clan_rank = clan_rank
        self.trophies = []
        self.carrying_thia = False

    def decide_action(self, environment):
        """Decide action based on current state"""
        if self.stamina < 20:
            return {'type': 'rest'}

        if self.is_dek:
            return self._dek_decision_logic(environment)
        else:
            return self._clan_decision_logic(environment)

    def _dek_decision_logic(self, environment):
        """Decision logic specific to Dek"""
        # Find immediate threats
        nearby_threats = self._find_nearby_threats(environment, radius=2)
        if nearby_threats and self.stamina >= 10:
            closest = min(nearby_threats, key=lambda t: self._distance_to(t.position))
            if self._distance_to(closest.position) <= 1:
                return {'type': 'attack', 'target': closest}

        # Rest if low health
        if self.health < 30:
            return {'type': 'rest'}

        # Rest if very low stamina
        if self.stamina < 20:
            return {'type': 'rest'}

        # Hunt wildlife if honour is low
        if self.honour < 50:
            wildlife_pos = environment.get_nearest_wildlife(self.position)
            if wildlife_pos:
                distance = self._distance_to(wildlife_pos)
                if distance <= 1:
                    wildlife_agents = [a for a in environment.get_agents_at(wildlife_pos)
                                       if a.__class__.__name__ == 'Wildlife']
                    if wildlife_agents:
                        return {'type': 'attack', 'target': wildlife_agents[0]}
                else:
                    direction = self._calculate_direction(self.position, wildlife_pos)
                    return {'type': 'move', 'direction': direction}

        # Approach adversary when ready
        adversary_pos = environment.get_adversary_position()
        if self.honour >= 50 and self.health > 50 and adversary_pos:
            distance = self._distance_to(adversary_pos)
            if distance <= 1:
                adversary_agents = [a for a in environment.get_agents_at(adversary_pos)
                                    if a.__class__.__name__ in ['Adversary', 'AdaptiveAdversary']]
                if adversary_agents:
                    return {'type': 'attack', 'target': adversary_agents[0]}
            else:
                direction = self._calculate_direction(self.position, adversary_pos)
                return {'type': 'move', 'direction': direction}

        # Default: explore
        return {'type': 'move', 'direction': random.choice(['N', 'S', 'E', 'W'])}

    def _clan_decision_logic(self, environment):
        """Decision logic for clan members"""
        dek_pos = environment.get_dek_position()

        if dek_pos and self._distance_to(dek_pos) < 3:
            return {'type': 'challenge'}

        return {'type': 'move', 'direction': random.choice(['N', 'S', 'E', 'W'])}

    def execute_action(self, action, environment):
        """
        Execute the chosen action
        FIXED: Uses CombatSystem for attacks
        """
        action_type = action.get('type')

        if action_type == 'move':
            self._execute_move(action['direction'], environment)
        elif action_type == 'rest':
            self._execute_rest()
        elif action_type == 'attack':
            self._execute_attack(action.get('target'), environment)
        elif action_type == 'challenge':
            self._execute_challenge(environment)

    def _execute_move(self, direction: str, environment):
        """Move in specified direction"""
        x, y = self.position

        moves = {
            'N': (x, y - 1),
            'S': (x, y + 1),
            'E': (x + 1, y),
            'W': (x - 1, y)
        }

        new_pos = moves.get(direction, self.position)

        # Stamina cost
        cost = 5 if self.carrying_thia else 2
        self.stamina = max(0, self.stamina - cost)

        # Wrap position
        wrapped_x = new_pos[0] % environment.width
        wrapped_y = new_pos[1] % environment.height
        wrapped_pos = (wrapped_x, wrapped_y)

        if environment.is_valid_position(wrapped_pos):
            environment.move_agent(self, wrapped_pos)

    def _execute_rest(self):
        """Rest to recover stamina and health"""
        self.stamina = min(self.stamina + 15, self.max_stamina)  # Increased regen
        self.health = min(self.health + 5, self.max_health)

    def _execute_attack(self, target, environment):
        """
        Attack a target using CombatSystem
        FIXED: Properly uses combat system
        """
        if target and target.is_alive and self._distance_to(target.position) <= 1:
            # Use CombatSystem which handles honour awards
            from mechanics.combat import CombatSystem
            result = CombatSystem.resolve_combat(self, target)

            # Combat system handles honour and trophy collection automatically

    def _execute_challenge(self, environment):
        """Challenge another predator"""
        # Find Dek or nearest predator
        dek_agents = [a for a in environment.agents
                      if hasattr(a, 'is_dek') and a.is_dek]

        if dek_agents:
            from mechanics.combat import CombatSystem
            CombatSystem.clan_challenge(self, dek_agents[0])

    def _calculate_direction(self, from_pos: Tuple[int, int],
                             to_pos: Tuple[int, int]) -> str:
        """Calculate direction to move toward target"""
        fx, fy = from_pos
        tx, ty = to_pos

        dx = tx - fx
        dy = ty - fy

        if abs(dx) > abs(dy):
            return 'E' if dx > 0 else 'W'
        else:
            return 'S' if dy > 0 else 'N'

    def _distance_to(self, position: Tuple[int, int]) -> float:
        """Calculate Manhattan distance"""
        return abs(self.position[0] - position[0]) + abs(self.position[1] - position[1])

    def _find_nearby_threats(self, environment, radius: int = 1) -> List:
        """Find threatening wildlife/adversaries nearby"""
        threats = []
        for agent in environment.agents:
            if agent == self or not agent.is_alive:
                continue
            if agent.__class__.__name__ in ['Wildlife', 'Adversary', 'AdaptiveAdversary']:
                dist = self._distance_to(agent.position)
                if dist <= radius:
                    threats.append(agent)
        return threats

    def carry_synthetic(self, synthetic):
        """Pick up Thia"""
        self.carrying_thia = True
        print(f"{self.name} is now carrying {synthetic.name}")

    def drop_synthetic(self):
        """Put down synthetic"""
        self.carrying_thia = False
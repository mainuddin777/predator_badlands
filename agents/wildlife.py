"""
Wildlife creatures for hunting and threats
"""
from typing import Tuple
from agents.base_agent import BaseAgent
import random


class Wildlife(BaseAgent):
    """
    Wildlife creature that can be hunted for trophies
    Provides honour when defeated according to Yautja code
    """

    def __init__(self, name: str, position: Tuple[int, int],
                 health: int = 30, threat_level: int = 1):
        super().__init__(name, position, health, health)
        self.threat_level = threat_level  # 1-3: weak to dangerous
        self.is_hostile = threat_level >= 2
        self.attack_power = 5 * threat_level
        self.movement_style = random.choice(['wandering', 'territorial', 'fleeing'])
        self.territory_center = position
        self.flee_threshold = 10  # Health below which creature flees

    def decide_action(self, environment):
        """
        Wildlife AI behavior:
        - Wander randomly if peaceful
        - Attack nearby predators if hostile
        - Flee if health is low
        """
        # Flee if badly wounded
        if self.health < self.flee_threshold:
            return {
                'type': 'flee',
                'from': self._find_nearest_threat(environment)
            }

        # If hostile, attack nearby predators (but not constantly)
        if self.is_hostile:
            nearby_predator = self._find_nearby_predator(environment, radius=2)
            if nearby_predator:
                distance = self._manhattan_distance(self.position, nearby_predator.position)

                if distance <= 1:
                    # Only attack 30% of the time when adjacent to reduce spam
                    import random
                    if random.random() < 0.3:
                        return {
                            'type': 'attack',
                            'target': nearby_predator
                        }
                    else:
                        return {
                            'type': 'move',
                            'direction': self._get_wander_direction()
                        }
                else:
                    return {
                        'type': 'move',
                        'direction': self._calculate_direction(self.position, nearby_predator.position)
                    }

        # Default: wander
        return {
            'type': 'move',
            'direction': self._get_wander_direction()
        }

    def execute_action(self, action, environment):
        """Execute wildlife action"""
        action_type = action.get('type')

        if action_type == 'move':
            self._execute_move(action['direction'], environment)
        elif action_type == 'attack':
            self._execute_attack(action['target'])
        elif action_type == 'flee':
            self._execute_flee(action.get('from'), environment)

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

        # Wrap position if wrapping is enabled
        wrapped_x = new_pos[0] % environment.width
        wrapped_y = new_pos[1] % environment.height
        wrapped_pos = (wrapped_x, wrapped_y)

        if environment.is_valid_position(wrapped_pos):
            environment.move_agent(self, wrapped_pos)

    def _execute_attack(self, target):
        """Attack target"""
        if target:
            target.take_damage(self.attack_power)
            print(f"[{self.name}]: Attacks {target.name} for {self.attack_power} damage!")

    def _execute_flee(self, threat, environment):
        """Flee from threat"""
        if threat:
            # Move away from threat
            direction = self._calculate_flee_direction(self.position, threat.position)
            self._execute_move(direction, environment)
        else:
            # Random flee
            self._execute_move(random.choice(['N', 'S', 'E', 'W']), environment)

    def _get_wander_direction(self) -> str:
        """Get random wander direction"""
        if self.movement_style == 'territorial':
            # Stay near territory center
            dist = self._manhattan_distance(self.position, self.territory_center)
            if dist > 5:
                return self._calculate_direction(self.position, self.territory_center)

        return random.choice(['N', 'S', 'E', 'W'])

    def _find_nearby_predator(self, environment, radius: int = 3):
        """Find nearby predator"""
        for agent in environment.agents:
            if agent.__class__.__name__ == 'Predator':
                dist = self._manhattan_distance(self.position, agent.position)
                if dist <= radius:
                    return agent
        return None

    def _find_nearest_threat(self, environment):
        """Find nearest threatening agent"""
        threats = [a for a in environment.agents
                   if a.__class__.__name__ in ['Predator', 'Adversary']]

        if not threats:
            return None

        nearest = min(threats,
                      key=lambda t: self._manhattan_distance(self.position, t.position))
        return nearest

    def _calculate_direction(self, from_pos: Tuple[int, int],
                             to_pos: Tuple[int, int]) -> str:
        """Calculate direction toward target"""
        fx, fy = from_pos
        tx, ty = to_pos

        dx = tx - fx
        dy = ty - fy

        if abs(dx) > abs(dy):
            return 'E' if dx > 0 else 'W'
        else:
            return 'S' if dy > 0 else 'N'

    def _calculate_flee_direction(self, from_pos: Tuple[int, int],
                                  threat_pos: Tuple[int, int]) -> str:
        """Calculate direction away from threat"""
        fx, fy = from_pos
        tx, ty = threat_pos

        dx = fx - tx  # Reversed for fleeing
        dy = fy - ty

        if abs(dx) > abs(dy):
            return 'E' if dx > 0 else 'W'
        else:
            return 'S' if dy > 0 else 'N'

    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def is_worthy_prey(self) -> bool:

        return self.threat_level >= 2 and self.is_alive
"""
Ultimate Adversary / Boss Creature
Complete implementation for Requirement (d)
"""
from typing import Tuple, List
from agents.base_agent import BaseAgent
import random


class Adversary(BaseAgent):
    """
    Boss-level creature that Dek must defeat
    High resilience, territorial, presents major threat
    """

    def __init__(self, name: str, position: Tuple[int, int],
                 health: int = 500, threat_radius: int = 5):
        super().__init__(name, position, health, health)
        self.threat_radius = threat_radius
        self.territory_center = position
        self.aggression_level = 5
        self.attack_power = 30
        self.defended_successfully = 0
        self.times_attacked = 0
        self.movement_pattern = 'patrol'  # patrol, chase, defend
        self.patrol_route = []
        self._generate_patrol_route()
        self.current_patrol_index = 0

    def _generate_patrol_route(self):
        """Generate a patrol route around territory"""
        cx, cy = self.territory_center
        # Square patrol pattern
        self.patrol_route = [
            (cx - 2, cy - 2),
            (cx + 2, cy - 2),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2)
        ]

    def decide_action(self, environment):
        """
        Adversary AI decision making
        - Patrols territory when calm
        - Chases intruders when threatened
        - Defends when cornered
        """
        # Find nearest threat
        nearest_predator = self._find_nearest_predator(environment)

        if nearest_predator:
            distance = self._manhattan_distance(self.position, nearest_predator.position)

            # If predator is very close, attack
            if distance <= 1:
                return {
                    'type': 'attack',
                    'target': nearest_predator
                }

            # If predator is in threat radius, chase
            elif distance <= self.threat_radius:
                self.movement_pattern = 'chase'
                return {
                    'type': 'move',
                    'direction': self._calculate_direction(self.position, nearest_predator.position)
                }

        # Default: patrol territory
        self.movement_pattern = 'patrol'
        return {
            'type': 'move',
            'direction': self._get_patrol_direction()
        }

    def execute_action(self, action, environment):
        """Execute the adversary's action"""
        action_type = action.get('type')

        if action_type == 'move':
            self._execute_move(action['direction'], environment)
        elif action_type == 'attack':
            self._execute_attack(action['target'], environment)

    def _execute_move(self, direction: str, environment):
        """Move in specified direction"""
        x, y = self.position

        moves = {
            'N': (x, y - 1),
            'S': (x, y + 1),
            'E': (x + 1, y),
            'W': (x - 1, y),
            'NE': (x + 1, y - 1),
            'NW': (x - 1, y - 1),
            'SE': (x + 1, y + 1),
            'SW': (x - 1, y + 1)
        }

        new_pos = moves.get(direction, self.position)

        # Wrap position if needed
        wrapped_x = new_pos[0] % environment.width
        wrapped_y = new_pos[1] % environment.height
        wrapped_pos = (wrapped_x, wrapped_y)

        if environment.is_valid_position(wrapped_pos):
            environment.move_agent(self, wrapped_pos)

    def _execute_attack(self, target, environment):
        """Attack a target with powerful strikes"""
        if target and self._manhattan_distance(self.position, target.position) <= 1:
            damage = self.attack_power
            target.take_damage(damage)
            self.times_attacked += 1

            print(f"[{self.name}]: ROARS and strikes {target.name} for {damage} damage!")

            if not target.is_alive:
                print(f"[{self.name}]: {target.name} has fallen!")

    def _get_patrol_direction(self) -> str:
        """Get direction for patrol movement"""
        if not self.patrol_route:
            return random.choice(['N', 'S', 'E', 'W'])

        target = self.patrol_route[self.current_patrol_index]

        # If reached current patrol point, move to next
        if self.position == target:
            self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_route)
            target = self.patrol_route[self.current_patrol_index]

        return self._calculate_direction(self.position, target)

    def _find_nearest_predator(self, environment):
        """Find the nearest predator threat"""
        predators = [a for a in environment.agents if a.__class__.__name__ == 'Predator']

        if not predators:
            return None

        nearest = min(predators,
                      key=lambda p: self._manhattan_distance(self.position, p.position))
        return nearest

    def _calculate_direction(self, from_pos: Tuple[int, int],
                             to_pos: Tuple[int, int]) -> str:
        """Calculate direction to move toward target"""
        fx, fy = from_pos
        tx, ty = to_pos

        dx = tx - fx
        dy = ty - fy

        # Determine primary direction
        if abs(dx) > abs(dy):
            return 'E' if dx > 0 else 'W'
        elif abs(dy) > abs(dx):
            return 'S' if dy > 0 else 'N'
        else:
            # Diagonal or equal - choose based on both
            if dx > 0 and dy > 0:
                return 'SE'
            elif dx > 0 and dy < 0:
                return 'NE'
            elif dx < 0 and dy > 0:
                return 'SW'
            else:
                return 'NW'

    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def take_damage(self, damage: int):
        """Override to track defensive success"""
        super().take_damage(damage)
        self.times_attacked += 1

        if self.is_alive:
            self.defended_successfully += 1
            # Increase aggression when damaged
            self.aggression_level = min(10, self.aggression_level + 1)
            self.threat_radius = min(10, self.threat_radius + 1)
            print(f"[{self.name}]: Wounded but enraged! HP: {self.health}/{self.max_health}")
        else:
            print(f"[{self.name}]: The great beast has been defeated!")

    def get_stats(self) -> dict:
        """Return adversary statistics"""
        return {
            'health': f"{self.health}/{self.max_health}",
            'position': self.position,
            'threat_radius': self.threat_radius,
            'aggression': self.aggression_level,
            'times_attacked': self.times_attacked,
            'successful_defenses': self.defended_successfully,
            'movement_pattern': self.movement_pattern
        }
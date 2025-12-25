"""
Synthetic Android agents (Thia and others)
"""
from typing import Tuple, Optional, Dict, List
from agents.base_agent import BaseAgent
import random


class Synthetic(BaseAgent):
    """
    Synthetic android with damaged state and support capabilities
    Thia is damaged and provides knowledge/reconnaissance
    """

    def __init__(self, name: str, position: Tuple[int, int],
                 health: int = 50, is_damaged: bool = True):
        super().__init__(name, position, health, health)
        self.is_damaged = is_damaged
        self.mobility = 0 if is_damaged else 5  # Cannot move if damaged
        self.knowledge_base = {}
        self.scanned_areas = set()  # Areas Thia has analyzed
        self.being_carried = False
        self.carrier = None
        self.last_advice_turn = -10  # Track when last advice was given

        # Thia's specialized knowledge
        self._initialize_knowledge()

    def _initialize_knowledge(self):
        """Initialize Thia's knowledge about the environment"""
        self.knowledge_base = {
            'adversary_weakness': 'Exposed cooling vents on back',
            'optimal_strategy': 'Strike from elevated position',
            'danger_zones': [],  # Will be populated as she scans
            'safe_paths': [],
            'resource_locations': []
        }

    def decide_action(self, environment):
        """
        Thia's decision making - primarily support and reconnaissance
        """
        if self.being_carried:
            # Provide guidance while being carried
            return {'type': 'provide_knowledge'}

        if self.is_damaged and not self.being_carried:
            # Wait to be picked up or provide remote analysis
            return {'type': 'scan_area'}

        # If somehow mobile (repaired), scout ahead
        return {'type': 'reconnaissance'}

    def execute_action(self, action, environment):
        """Execute Thia's actions"""
        action_type = action.get('type')

        if action_type == 'provide_knowledge':
            self._provide_knowledge(environment)
        elif action_type == 'scan_area':
            self._scan_surrounding_area(environment)
        elif action_type == 'reconnaissance':
            self._perform_reconnaissance(environment)

    def _provide_knowledge(self, environment):
        """
        Provide strategic knowledge to nearby Predators
        This is Thia's main support function
        """
        # Find nearby predators
        nearby_predators = self._find_nearby_predators(environment, radius=2)

        for predator in nearby_predators:
            if hasattr(predator, 'is_dek') and predator.is_dek:
                # Share knowledge with Dek
                advice = self._generate_advice(environment, predator)
                if advice:
                    print(f"[Thia]: {advice}")

    def _generate_advice(self, environment, predator) -> str:
        """Generate contextual advice for the predator"""
        # Check predator's health
        if predator.health < 40:
            return "Warning: Your health is critical. Seek safety and rest."

        # Check stamina
        if predator.stamina < 30:
            return "Your stamina is low. Rest before engaging in combat."

        # Advise on adversary
        adversary_pos = environment.get_adversary_position()
        if adversary_pos:
            dist = self._manhattan_distance(predator.position, adversary_pos)
            if dist < 5:
                return f"The adversary is nearby ({dist} units). {self.knowledge_base['adversary_weakness']}"
            elif predator.honour >= 50:
                return "You have sufficient honour. Consider confronting the adversary."

        # Advise on honour
        if predator.honour < 30:
            return "Your honour is low. Hunt worthy prey to prove yourself."

        return ""

    def _scan_surrounding_area(self, environment):
        """
        Scan and analyze surrounding area for threats/resources
        """
        x, y = self.position
        scan_radius = 3

        # Scan area around current position
        for dx in range(-scan_radius, scan_radius + 1):
            for dy in range(-scan_radius, scan_radius + 1):
                scan_pos = (x + dx, y + dy)
                if environment.is_valid_position(scan_pos):
                    self.scanned_areas.add(scan_pos)

                    # Analyze what's there
                    cell = environment.get_cell(scan_pos)
                    if cell and cell.terrain_type == 'obstacle':
                        if scan_pos not in self.knowledge_base['danger_zones']:
                            self.knowledge_base['danger_zones'].append(scan_pos)

    def _perform_reconnaissance(self, environment):
        """
        Scout ahead (if mobile after repair)
        """
        # Move toward unexplored areas
        direction = random.choice(['N', 'S', 'E', 'W'])
        x, y = self.position

        moves = {
            'N': (x, y - 1),
            'S': (x, y + 1),
            'E': (x + 1, y),
            'W': (x - 1, y)
        }

        new_pos = moves.get(direction, self.position)
        if environment.is_valid_position(new_pos):
            self.move_to(new_pos)
            self._scan_surrounding_area(environment)

    def _find_nearby_predators(self, environment, radius: int = 2) -> List:
        """Find all predators within radius"""
        nearby = []
        x, y = self.position

        for agent in environment.agents:
            if agent.__class__.__name__ == 'Predator':
                dist = self._manhattan_distance(self.position, agent.position)
                if dist <= radius:
                    nearby.append(agent)

        return nearby

    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def get_picked_up(self, carrier):
        """Be picked up by a predator"""
        self.being_carried = True
        self.carrier = carrier
        print(f"[Thia]: {carrier.name} is carrying me now.")

    def get_put_down(self):
        """Be put down by carrier"""
        self.being_carried = False
        carrier_name = self.carrier.name if self.carrier else "carrier"
        self.carrier = None
        print(f"[Thia]: {carrier_name} has put me down.")

    def repair(self, amount: int):
        """Repair damage - improves mobility"""
        self.health = min(self.health + amount, self.max_health)
        if self.health > 70:
            self.is_damaged = False
            self.mobility = 5
            print(f"[Thia]: Systems restored. I can move independently now.")

    def get_knowledge_summary(self) -> Dict:
        """Return Thia's accumulated knowledge"""
        return {
            'scanned_cells': len(self.scanned_areas),
            'known_dangers': len(self.knowledge_base['danger_zones']),
            'adversary_info': self.knowledge_base['adversary_weakness'],
            'carrier': self.carrier.name if self.carrier else None
        }
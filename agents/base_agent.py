"""
Base Agent class for all entities in the simulation
"""
from abc import ABC, abstractmethod
from typing import Tuple, Optional


class BaseAgent(ABC):
    """Abstract base class for all agents in the simulation"""

    def __init__(self, name: str, position: Tuple[int, int],
                 health: int, max_health: int):
        self.name = name
        self.position = position
        self.health = health
        self.max_health = max_health
        self.is_alive = True

    @abstractmethod
    def decide_action(self, environment):
        """
        Decide what action to take this turn
        Returns: action dictionary
        """
        pass

    @abstractmethod
    def execute_action(self, action, environment):
        """Execute the decided action"""
        pass

    def take_damage(self, damage: int):
        """Reduce health by damage amount"""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.is_alive = False

    def heal(self, amount: int):
        """Restore health"""
        self.health = min(self.health + amount, self.max_health)

    def move_to(self, new_position: Tuple[int, int]):
        """Update agent position"""
        self.position = new_position

    def get_position(self) -> Tuple[int, int]:
        """Return current position"""
        return self.position

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, pos={self.position}, HP={self.health})"
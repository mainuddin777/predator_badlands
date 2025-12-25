"""
Grid Environment for the Predator: Badlands simulation
"""
from typing import Tuple, List, Optional
import random
from config.settings import GRID_WIDTH, GRID_HEIGHT, WRAPPING_ENABLED


class Cell:
    """Represents a single cell in the grid"""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.terrain_type = 'empty'  # empty, obstacle, trap
        self.occupants = []  # Agents in this cell

    def add_occupant(self, agent):
        """Add an agent to this cell"""
        if agent not in self.occupants:
            self.occupants.append(agent)

    def remove_occupant(self, agent):
        """Remove an agent from this cell"""
        if agent in self.occupants:
            self.occupants.remove(agent)

    def is_passable(self) -> bool:
        """Check if cell can be entered"""
        return self.terrain_type not in ['obstacle']

    def __repr__(self):
        return f"Cell({self.x},{self.y})"


class Grid:
    """Grid environment for the simulation"""

    def __init__(self, width: int = GRID_WIDTH, height: int = GRID_HEIGHT):
        self.width = width
        self.height = height
        self.wrapping = WRAPPING_ENABLED
        self.cells = [[Cell(x, y) for y in range(height)] for x in range(width)]
        self.agents = []
        self.turn_count = 0

    def initialize_environment(self, num_obstacles: int = 20):
        """Set up initial environment with obstacles"""
        for _ in range(num_obstacles):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            self.cells[x][y].terrain_type = 'obstacle'

    def add_agent(self, agent):
        """Add agent to the grid"""
        self.agents.append(agent)
        x, y = agent.position
        self.cells[x][y].add_occupant(agent)

    def remove_agent(self, agent):
        """Remove agent from grid"""
        if agent in self.agents:
            self.agents.remove(agent)
            x, y = agent.position
            if 0 <= x < self.width and 0 <= y < self.height:
                self.cells[x][y].remove_occupant(agent)

    def move_agent(self, agent, new_position: Tuple[int, int]):
        """Move agent to new position with proper wrapping"""
        old_x, old_y = agent.position
        new_x, new_y = new_position

        # Apply wrapping if enabled
        if self.wrapping:
            new_x = new_x % self.width
            new_y = new_y % self.height

        # Ensure position is valid
        if not (0 <= new_x < self.width and 0 <= new_y < self.height):
            return  # Invalid position, don't move

        # Remove from old cell
        if 0 <= old_x < self.width and 0 <= old_y < self.height:
            self.cells[old_x][old_y].remove_occupant(agent)

        # Add to new cell
        self.cells[new_x][new_y].add_occupant(agent)

        # Update agent position
        agent.move_to((new_x, new_y))

    def is_valid_position(self, position: Tuple[int, int]) -> bool:
        """Check if position is valid and passable"""
        x, y = position

        # Apply wrapping if enabled
        if self.wrapping:
            x = x % self.width
            y = y % self.height

        # Check bounds
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False

        # Check if passable
        return self.cells[x][y].is_passable()

    def _wrap_position(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """Apply wrapping to position if enabled"""
        x, y = position

        if self.wrapping:
            x = x % self.width
            y = y % self.height
        else:
            # Clamp to boundaries if no wrapping
            x = max(0, min(x, self.width - 1))
            y = max(0, min(y, self.height - 1))

        return (x, y)

    def get_cell(self, position: Tuple[int, int]) -> Optional[Cell]:
        """Get cell at position"""
        x, y = self._wrap_position(position)
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.cells[x][y]
        return None

    def get_neighbors(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid neighboring positions"""
        x, y = position
        neighbors = [
            (x, y - 1),  # North
            (x, y + 1),  # South
            (x + 1, y),  # East
            (x - 1, y)  # West
        ]

        valid_neighbors = []
        for pos in neighbors:
            wrapped_pos = self._wrap_position(pos)
            if self.is_valid_position(wrapped_pos):
                valid_neighbors.append(wrapped_pos)

        return valid_neighbors

    def get_agents_at(self, position: Tuple[int, int]) -> List:
        """Get all agents at a position"""
        cell = self.get_cell(position)
        return cell.occupants if cell else []

    def get_dek_position(self) -> Optional[Tuple[int, int]]:
        """Find Dek's position"""
        for agent in self.agents:
            if hasattr(agent, 'is_dek') and agent.is_dek:
                return agent.position
        return None

    def get_adversary_position(self) -> Optional[Tuple[int, int]]:
        """Find adversary's position"""
        for agent in self.agents:
            if agent.__class__.__name__ == 'Adversary':
                return agent.position
        return None

    def get_nearest_wildlife(self, position: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Find nearest wildlife creature"""
        wildlife = [a for a in self.agents if a.__class__.__name__ == 'Wildlife' and a.is_alive]

        if not wildlife:
            return None

        nearest = min(wildlife, key=lambda w: self._manhattan_distance(position, w.position))
        return nearest.position

    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def update(self):
        """Update grid state each turn"""
        self.turn_count += 1

        # Remove dead agents
        dead_agents = [a for a in self.agents if not a.is_alive]
        for agent in dead_agents:
            self.remove_agent(agent)

    def get_state(self) -> dict:
        """Get current state for visualization/analysis"""
        return {
            'turn': self.turn_count,
            'agents': [(a.name, a.position, a.health) for a in self.agents],
            'grid_size': (self.width, self.height)
        }
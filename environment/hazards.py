"""
Environmental Hazards
Traps, hostile terrain, weather effects
"""
from typing import Tuple, List
import random


class Hazard:
    """Base class for environmental hazards"""

    def __init__(self, position: Tuple[int, int], hazard_type: str):
        self.position = position
        self.hazard_type = hazard_type
        self.active = True
        self.damage = 10

    def trigger(self, agent) -> dict:
        """Trigger hazard effect on agent"""
        if not self.active:
            return {'triggered': False}

        result = {
            'triggered': True,
            'hazard': self.hazard_type,
            'agent': agent.name,
            'damage': self.damage
        }

        agent.take_damage(self.damage)
        print(f"⚠️  {agent.name} triggered {self.hazard_type}! Took {self.damage} damage.")

        return result


class Trap(Hazard):
    """Hidden trap that damages agents"""

    def __init__(self, position: Tuple[int, int], trap_type: str = 'spike'):
        super().__init__(position, f"{trap_type}_trap")
        self.visible = False
        self.uses = 1  # One-time use

        # Trap-specific damage
        trap_damages = {
            'spike': 15,
            'net': 5,  # Less damage, but immobilizes
            'pit': 25
        }
        self.damage = trap_damages.get(trap_type, 10)

    def trigger(self, agent) -> dict:
        """Trigger trap"""
        if not self.active or self.uses <= 0:
            return {'triggered': False}

        result = super().trigger(agent)

        self.uses -= 1
        if self.uses <= 0:
            self.active = False
            self.visible = True

        return result


class HostileTerrain(Hazard):
    """Difficult terrain that costs extra stamina"""

    def __init__(self, position: Tuple[int, int], terrain_type: str = 'rough'):
        super().__init__(position, terrain_type)
        self.damage = 0  # Doesn't damage, just drains stamina

        self.stamina_cost = {
            'rough': 3,
            'marsh': 5,
            'lava': 10
        }.get(terrain_type, 2)

    def trigger(self, agent) -> dict:
        """Apply terrain effect"""
        if not self.active:
            return {'triggered': False}

        # Drain stamina
        if hasattr(agent, 'stamina'):
            agent.stamina = max(0, agent.stamina - self.stamina_cost)
            print(f"⚠️  {agent.name} crossed {self.hazard_type}. Stamina -{self.stamina_cost}")

        return {
            'triggered': True,
            'hazard': self.hazard_type,
            'stamina_cost': self.stamina_cost
        }


class WeatherEffect:
    """Environmental weather effects"""

    def __init__(self, weather_type: str = 'clear'):
        self.weather_type = weather_type
        self.duration = 0
        self.active = False

    def activate(self, duration: int):
        """Activate weather effect"""
        self.active = True
        self.duration = duration
        print(f"🌤️  Weather changed to: {self.weather_type}")

    def update(self) -> bool:
        """Update weather duration"""
        if not self.active:
            return False

        self.duration -= 1
        if self.duration <= 0:
            self.active = False
            print(f"🌤️  {self.weather_type} weather has ended")
            return False

        return True

    def apply_effect(self, agents: List):
        """Apply weather effects to all agents"""
        if not self.active:
            return

        if self.weather_type == 'storm':
            # Reduces visibility, increases stamina costs
            for agent in agents:
                if hasattr(agent, 'stamina'):
                    agent.stamina = max(0, agent.stamina - 1)

        elif self.weather_type == 'heat':
            # Increased stamina drain
            for agent in agents:
                if hasattr(agent, 'stamina'):
                    agent.stamina = max(0, agent.stamina - 2)

        elif self.weather_type == 'fog':
            # Reduces detection range
            pass


class HazardManager:
    """Manages all environmental hazards"""

    def __init__(self, grid):
        self.grid = grid
        self.hazards = []
        self.weather = WeatherEffect('clear')

    def add_hazard(self, hazard: Hazard):
        """Add hazard to the environment"""
        self.hazards.append(hazard)

    def generate_random_hazards(self, num_traps: int = 10):
        """Generate random hazards across the grid"""
        for _ in range(num_traps):
            x = random.randint(0, self.grid.width - 1)
            y = random.randint(0, self.grid.height - 1)

            # Check if position is valid
            if self.grid.is_valid_position((x, y)):
                trap_type = random.choice(['spike', 'net', 'pit'])
                trap = Trap((x, y), trap_type)
                self.add_hazard(trap)

        print(f"✓ Generated {num_traps} random traps")

    def check_hazards(self, agent):
        """Check if agent triggered any hazards"""
        for hazard in self.hazards:
            if hazard.position == agent.position and hazard.active:
                hazard.trigger(agent)

    def update_weather(self):
        """Update weather effects"""
        self.weather.update()
        if self.weather.active:
            self.weather.apply_effect(self.grid.agents)

    def trigger_random_weather(self):
        """Randomly trigger weather event"""
        if not self.weather.active and random.random() < 0.1:  # 10% chance
            weather_type = random.choice(['storm', 'heat', 'fog', 'clear'])
            duration = random.randint(10, 30)
            self.weather = WeatherEffect(weather_type)
            self.weather.activate(duration)

    def get_hazard_at(self, position: Tuple[int, int]) -> List[Hazard]:
        """Get all hazards at position"""
        return [h for h in self.hazards if h.position == position and h.active]
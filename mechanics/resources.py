"""
Resource Management System
"""


class ResourceManager:
    """
    Manage resources for all agents
    Tracks stamina, health, energy costs
    """

    @staticmethod
    def consume_stamina(agent, amount: int) -> bool:
        """
        Consume stamina from agent
        Returns True if successful, False if insufficient
        """
        if not hasattr(agent, 'stamina'):
            return True  # Non-predator agents don't use stamina

        if agent.stamina >= amount:
            agent.stamina -= amount
            return True
        else:
            return False

    @staticmethod
    def regenerate_stamina(agent, amount: int = 10):
        """Regenerate stamina when resting"""
        if hasattr(agent, 'stamina') and hasattr(agent, 'max_stamina'):
            agent.stamina = min(agent.stamina + amount, agent.max_stamina)

    @staticmethod
    def consume_health(agent, amount: int):
        """Consume health (damage)"""
        agent.take_damage(amount)

    @staticmethod
    def restore_health(agent, amount: int):
        """Restore health"""
        agent.heal(amount)

    @staticmethod
    def check_exhaustion(agent) -> bool:
        """Check if agent is exhausted"""
        if hasattr(agent, 'stamina'):
            return agent.stamina < 10
        return False

    @staticmethod
    def get_movement_cost(agent, terrain_type: str = 'normal') -> int:
        """
        Calculate movement cost based on terrain and agent state
        """
        base_cost = 2

        # Terrain modifiers
        terrain_costs = {
            'normal': 1.0,
            'difficult': 1.5,
            'obstacle': 999,  # Can't pass
            'trap': 1.2
        }

        cost = base_cost * terrain_costs.get(terrain_type, 1.0)

        # Agent-specific modifiers
        if hasattr(agent, 'carrying_thia') and agent.carrying_thia:
            cost *= 2.5  # Much harder to move while carrying

        return int(cost)

    @staticmethod
    def get_resource_status(agent) -> dict:
        """Get complete resource status for agent"""
        status = {
            'health': f"{agent.health}/{agent.max_health}",
            'health_percent': (agent.health / agent.max_health) * 100
        }

        if hasattr(agent, 'stamina'):
            status['stamina'] = f"{agent.stamina}/{agent.max_stamina}"
            status['stamina_percent'] = (agent.stamina / agent.max_stamina) * 100
            status['exhausted'] = agent.stamina < 10

        return status
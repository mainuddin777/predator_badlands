"""
Combat System Mechanics

"""
import random
from typing import Tuple, Optional


class CombatSystem:
    """
    Handle combat encounters between agents
    """

    @staticmethod
    def resolve_combat(attacker, defender, honour_system=None) -> dict:
        """
        Resolve a combat encounter
        """
        # Check if both agents are alive
        if not attacker.is_alive or not defender.is_alive:
            return {
                'success': False,
                'reason': 'One or both combatants are not alive'
            }

        # Check stamina for attacker
        if hasattr(attacker, 'stamina'):
            if attacker.stamina < 10:
                return {
                    'success': False,
                    'reason': f'{attacker.name} is too exhausted to fight'
                }
            attacker.stamina -= 10

        # Calculate damage
        base_damage = CombatSystem._calculate_damage(attacker, defender)
        critical = random.random() < 0.15
        final_damage = int(base_damage * 1.5) if critical else base_damage

        # Apply damage
        defender.take_damage(final_damage)

        result = {
            'success': True,
            'attacker': attacker.name,
            'defender': defender.name,
            'damage': final_damage,
            'critical': critical,
            'defender_alive': defender.is_alive
        }

        # Print combat log
        crit_text = " [CRITICAL HIT!]" if critical else ""
        print(f"⚔️  {attacker.name} attacks {defender.name} for {final_damage} damage{crit_text}")

        # Handle defeat and honour
        if not defender.is_alive:
            print(f"💀 {defender.name} has been defeated!")
            result['defeated'] = True

            # AWARD HONOUR FOR DEFEAT
            if attacker.__class__.__name__ == 'Predator' or hasattr(attacker, 'honour'):
                CombatSystem._award_honour_for_defeat(attacker, defender, honour_system)

        return result

    @staticmethod
    def _award_honour_for_defeat(attacker, defender, honour_system=None):
        """
        Award honour for defeating an enemy
        """
        # Import here to avoid circular dependency
        from mechanics.honour import HonourSystem

        if honour_system is None:
            honour_system = HonourSystem

        # Determine honour gain based on target type
        if defender.__class__.__name__ == 'Wildlife':
            # Wildlife is worthy prey if threat_level >= 1
            if hasattr(defender, 'threat_level') and defender.threat_level >= 1:
                honour_gain = 15 + (defender.threat_level * 5)
                honour_system.update_honour(
                    attacker,
                    'hunt_worthy_prey',
                    {'target': defender}
                )

                # Collect trophy
                if hasattr(attacker, 'trophies'):
                    attacker.trophies.append(defender.name)
                    print(f"🏆 {attacker.name} collected trophy from {defender.name}")
            else:
                # Unworthy prey - penalty
                honour_system.update_honour(
                    attacker,
                    'hunt_unworthy_prey',
                    {'target': defender}
                )

        elif defender.__class__.__name__ in ['Adversary', 'AdaptiveAdversary']:
            # Adversary defeat - MASSIVE honour
            honour_system.update_honour(
                attacker,
                'defeat_adversary',
                {'target': defender}
            )

            # Collect ultimate trophy
            if hasattr(attacker, 'trophies'):
                attacker.trophies.append(f"ULTIMATE_TROPHY_{defender.name}")
                print(f"🏆👑 {attacker.name} claimed the ULTIMATE TROPHY from {defender.name}!")

        elif defender.__class__.__name__ == 'Predator':
            # Defeated another predator in challenge
            honour_system.update_honour(
                attacker,
                'successful_challenge',
                {'target': defender, 'opponent_honour': defender.honour}
            )

    @staticmethod
    def _calculate_damage(attacker, defender) -> int:
        """Calculate base damage based on agent types"""
        base_damage = 20

        # Attacker bonuses
        if attacker.__class__.__name__ in ['Predator', 'QLearningPredator']:
            # Honour increases combat effectiveness
            if hasattr(attacker, 'honour'):
                honour_bonus = min(15, attacker.honour // 10)
                base_damage += honour_bonus

            # Carrying Thia reduces effectiveness
            if hasattr(attacker, 'carrying_thia') and attacker.carrying_thia:
                base_damage = int(base_damage * 0.7)

        elif attacker.__class__.__name__ in ['Adversary', 'AdaptiveAdversary']:
            base_damage = 35  # Powerful

            if hasattr(attacker, 'aggression_level'):
                base_damage += attacker.aggression_level * 2

        elif attacker.__class__.__name__ == 'Wildlife':
            if hasattr(attacker, 'threat_level'):
                base_damage = 5 * attacker.threat_level

        # Defender resistances
        if defender.__class__.__name__ in ['Adversary', 'AdaptiveAdversary']:
            # Tough but not invincible
            base_damage = int(base_damage * 0.85)

        # Add randomness (±20%)
        variance = random.uniform(0.8, 1.2)
        final_damage = int(base_damage * variance)

        return max(1, final_damage)

    @staticmethod
    def can_attack(attacker, defender, max_range: int = 1) -> bool:
        """Check if attacker can attack defender"""
        if not attacker.is_alive or not defender.is_alive:
            return False

        # Check distance
        distance = CombatSystem._manhattan_distance(
            attacker.position,
            defender.position
        )

        if distance > max_range:
            return False

        # Check stamina
        if hasattr(attacker, 'stamina'):
            if attacker.stamina < 10:
                return False

        return True

    @staticmethod
    def _manhattan_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    @staticmethod
    def clan_challenge(challenger, challenged, honour_system=None) -> dict:
        """
        Resolve a clan challenge between two Predators
        Non-lethal combat to establish dominance
        """
        if challenger.__class__.__name__ not in ['Predator', 'QLearningPredator'] or \
                challenged.__class__.__name__ not in ['Predator', 'QLearningPredator']:
            return {
                'success': False,
                'reason': 'Both must be Predators for clan challenge'
            }

        print(f"\n⚔️  CLAN CHALLENGE: {challenger.name} vs {challenged.name}")

        # Compare honour and health
        challenger_score = challenger.honour + (challenger.health / 2)
        challenged_score = challenged.honour + (challenged.health / 2)

        # Add randomness
        challenger_score *= random.uniform(0.8, 1.2)
        challenged_score *= random.uniform(0.8, 1.2)

        winner = challenger if challenger_score > challenged_score else challenged
        loser = challenged if winner == challenger else challenger

        # Non-lethal damage
        damage = 15
        loser.take_damage(damage)

        # Honour changes
        from mechanics.honour import HonourSystem
        if honour_system is None:
            honour_system = HonourSystem

        honour_system.update_honour(winner, 'win_clan_challenge')
        honour_system.update_honour(loser, 'lose_clan_challenge')

        print(f"🏆 {winner.name} wins the challenge!")

        # Both lose stamina
        if hasattr(challenger, 'stamina'):
            challenger.stamina = max(0, challenger.stamina - 15)
        if hasattr(challenged, 'stamina'):
            challenged.stamina = max(0, challenged.stamina - 15)

        return {
            'success': True,
            'winner': winner.name,
            'loser': loser.name
        }
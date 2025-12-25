"""
Adaptive Procedural Adversary
"""
from typing import Tuple, List, Dict
from agents.adversary import Adversary
import random
from collections import deque, defaultdict


class AdaptiveAdversary(Adversary):
    """
    Enhanced adversary that adapts behavior based on combat history
    Learns player patterns and evolves strategies
    """

    def __init__(self, name: str, position: Tuple[int, int],
                 health: int = 500, threat_radius: int = 5):
        super().__init__(name, position, health, threat_radius)

        # Adaptation tracking
        self.attack_pattern_memory = deque(maxlen=20)  # Last 20 encounters
        self.predator_position_history = deque(maxlen=30)
        self.successful_defenses = 0
        self.failed_defenses = 0

        # Learned behaviors
        self.preferred_attack_direction = None
        self.learned_retreat_threshold = 100
        self.chase_aggressiveness = 1.0  # Multiplier for chase behavior

        # Pattern recognition
        self.detected_patterns = {
            'circle_strategy': 0,
            'hit_and_run': 0,
            'frontal_assault': 0,
            'cautious_approach': 0
        }

        # Adaptive abilities (unlock based on combat experience)
        self.abilities_unlocked = {
            'berserker_rage': False,  # Unlocks at 10 attacks
            'predictive_movement': False,  # Unlocks at 15 attacks
            'area_denial': False,  # Unlocks at 20 attacks
            'adaptive_armor': False  # Unlocks after taking 200 damage
        }

        self.total_damage_received = 0
        self.combat_encounters = 0

    def decide_action(self, environment):
        """
        Enhanced decision making with adaptation
        """
        # Update combat intelligence
        self._update_combat_intelligence(environment)

        # Find nearest predator
        nearest_predator = self._find_nearest_predator(environment)

        if nearest_predator:
            # Record position for pattern learning
            self.predator_position_history.append(nearest_predator.position)

            distance = self._manhattan_distance(self.position, nearest_predator.position)

            # Adaptive behavior based on learned patterns
            if self._detect_circle_strategy():
                return self._counter_circle_strategy(nearest_predator, environment)

            if self._detect_hit_and_run():
                return self._counter_hit_and_run(nearest_predator, environment)

            # Check for ability usage
            if self.abilities_unlocked['berserker_rage'] and self.health < 200:
                return self._execute_berserker_rage(nearest_predator)

            if self.abilities_unlocked['predictive_movement']:
                return self._predictive_attack(nearest_predator, environment)

            # Standard combat logic with adaptations
            if distance <= 1:
                self.combat_encounters += 1
                return {
                    'type': 'attack',
                    'target': nearest_predator
                }

            elif distance <= self.threat_radius * self.chase_aggressiveness:
                self.movement_pattern = 'chase'
                return {
                    'type': 'move',
                    'direction': self._calculate_adaptive_direction(
                        self.position, nearest_predator.position, environment
                    )
                }

        # Adaptive patrol with learned preferences
        self.movement_pattern = 'patrol'
        return {
            'type': 'move',
            'direction': self._get_adaptive_patrol_direction()
        }

    def _update_combat_intelligence(self, environment):
        """Update intelligence based on combat history"""
        # Unlock abilities based on experience
        if self.times_attacked >= 10 and not self.abilities_unlocked['berserker_rage']:
            self.abilities_unlocked['berserker_rage'] = True
            print(f"⚡ [{self.name}] UNLOCKED: Berserker Rage!")

        if self.times_attacked >= 15 and not self.abilities_unlocked['predictive_movement']:
            self.abilities_unlocked['predictive_movement'] = True
            print(f"⚡ [{self.name}] UNLOCKED: Predictive Movement!")

        if self.times_attacked >= 20 and not self.abilities_unlocked['area_denial']:
            self.abilities_unlocked['area_denial'] = True
            self.threat_radius += 3
            print(f"⚡ [{self.name}] UNLOCKED: Area Denial! Threat radius increased!")

        if self.total_damage_received >= 200 and not self.abilities_unlocked['adaptive_armor']:
            self.abilities_unlocked['adaptive_armor'] = True
            print(f"⚡ [{self.name}] UNLOCKED: Adaptive Armor! Damage resistance increased!")

        # Adjust chase aggressiveness based on success rate
        if self.times_attacked > 5:
            success_rate = self.defended_successfully / self.times_attacked
            if success_rate > 0.7:
                self.chase_aggressiveness = min(1.5, self.chase_aggressiveness + 0.1)
            elif success_rate < 0.3:
                self.chase_aggressiveness = max(0.7, self.chase_aggressiveness - 0.1)

    def _detect_circle_strategy(self) -> bool:
        """Detect if predator is using circle/kiting strategy"""
        if len(self.predator_position_history) < 10:
            return False

        # Check if positions form a circular pattern
        recent_positions = list(self.predator_position_history)[-10:]

        # Calculate if predator maintains consistent distance
        distances = [self._manhattan_distance(self.position, pos) for pos in recent_positions]
        avg_distance = sum(distances) / len(distances)
        distance_variance = sum((d - avg_distance) ** 2 for d in distances) / len(distances)

        # Low variance + medium distance = circling
        if distance_variance < 4 and 3 < avg_distance < 7:
            self.detected_patterns['circle_strategy'] += 1
            if self.detected_patterns['circle_strategy'] >= 3:
                print(f"🧠 [{self.name}] Detected circling strategy!")
                return True

        return False

    def _detect_hit_and_run(self) -> bool:
        """Detect hit and run tactics"""
        if len(self.attack_pattern_memory) < 5:
            return False

        recent_attacks = list(self.attack_pattern_memory)[-5:]

        # Check for pattern: close -> attack -> retreat -> repeat
        retreat_count = sum(1 for attack in recent_attacks if attack.get('retreated'))

        if retreat_count >= 3:
            self.detected_patterns['hit_and_run'] += 1
            if self.detected_patterns['hit_and_run'] >= 2:
                print(f"🧠 [{self.name}] Detected hit-and-run tactics!")
                return True

        return False

    def _counter_circle_strategy(self, target, environment):
        """Counter circling by cutting off escape routes"""
        # Predict next position and move to intercept
        predicted_pos = self._predict_next_position(target)

        if predicted_pos:
            direction = self._calculate_direction(self.position, predicted_pos)
            print(f"🎯 [{self.name}] Intercepting circular pattern!")
            return {
                'type': 'move',
                'direction': direction
            }

        return {
            'type': 'move',
            'direction': self._calculate_direction(self.position, target.position)
        }

    def _counter_hit_and_run(self, target, environment):
        """Counter hit-and-run by zone control"""
        # Move aggressively and increase threat radius temporarily
        self.threat_radius = min(15, self.threat_radius + 2)

        print(f"🎯 [{self.name}] Enforcing zone control against hit-and-run!")

        if self._manhattan_distance(self.position, target.position) <= 2:
            return {
                'type': 'attack',
                'target': target
            }

        return {
            'type': 'move',
            'direction': self._calculate_aggressive_direction(self.position, target.position)
        }

    def _execute_berserker_rage(self, target):
        """Berserker mode: high damage, no retreat"""
        print(f"😡 [{self.name}] BERSERKER RAGE ACTIVATED!")
        self.attack_power = int(self.attack_power * 1.5)

        return {
            'type': 'attack',
            'target': target
        }

    def _predictive_attack(self, target, environment):
        """Use pattern learning to predict and attack"""
        predicted_pos = self._predict_next_position(target)

        if predicted_pos:
            distance = self._manhattan_distance(self.position, predicted_pos)

            if distance <= 2:
                print(f"🎯 [{self.name}] Predictive strike!")
                # Move to predicted position
                direction = self._calculate_direction(self.position, predicted_pos)
                return {
                    'type': 'move',
                    'direction': direction
                }

        # Fall back to standard attack
        return {
            'type': 'attack',
            'target': target
        }

    def _predict_next_position(self, target) -> Tuple[int, int]:
        """Predict target's next position based on movement history"""
        if len(self.predator_position_history) < 3:
            return None

        # Calculate movement vector from last 3 positions
        positions = list(self.predator_position_history)[-3:]

        dx = positions[-1][0] - positions[-3][0]
        dy = positions[-1][1] - positions[-3][1]

        # Predict next position
        predicted = (target.position[0] + dx, target.position[1] + dy)

        return predicted

    def _calculate_adaptive_direction(self, from_pos: Tuple[int, int],
                                      to_pos: Tuple[int, int], environment) -> str:
        """Calculate direction with adaptation to learned patterns"""
        # If we've learned the predator's preferred direction, compensate
        if self.preferred_attack_direction:
            # Add slight deviation to cut off escape
            return self._calculate_intercept_direction(from_pos, to_pos)

        return self._calculate_direction(from_pos, to_pos)

    def _calculate_aggressive_direction(self, from_pos: Tuple[int, int],
                                        to_pos: Tuple[int, int]) -> str:
        """More direct aggressive movement"""
        fx, fy = from_pos
        tx, ty = to_pos

        dx = tx - fx
        dy = ty - fy

        # Prefer diagonal movement for faster closing
        if abs(dx) > 0 and abs(dy) > 0:
            if dx > 0 and dy > 0:
                return 'SE'
            elif dx > 0 and dy < 0:
                return 'NE'
            elif dx < 0 and dy > 0:
                return 'SW'
            else:
                return 'NW'

        return self._calculate_direction(from_pos, to_pos)

    def _calculate_intercept_direction(self, from_pos: Tuple[int, int],
                                       to_pos: Tuple[int, int]) -> str:
        """Calculate interception vector"""
        predicted = self._predict_next_position(
            type('obj', (), {'position': to_pos})()
        )

        if predicted:
            return self._calculate_direction(from_pos, predicted)

        return self._calculate_direction(from_pos, to_pos)

    def _get_adaptive_patrol_direction(self) -> str:
        """Patrol with learned preferences"""
        if not self.patrol_route:
            return random.choice(['N', 'S', 'E', 'W'])

        target = self.patrol_route[self.current_patrol_index]

        # Reached patrol point
        if self.position == target:
            # Randomly vary patrol to be less predictable
            if random.random() < 0.3:
                self.current_patrol_index = random.randint(0, len(self.patrol_route) - 1)
            else:
                self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_route)

            target = self.patrol_route[self.current_patrol_index]

        return self._calculate_direction(self.position, target)

    def take_damage(self, damage: int):
        """Override to track damage and learn"""
        original_health = self.health
        super().take_damage(damage)

        actual_damage = original_health - self.health
        self.total_damage_received += actual_damage

        # Record attack for pattern learning
        self.attack_pattern_memory.append({
            'damage': actual_damage,
            'health_after': self.health,
            'retreated': False  # Will be updated if predator retreats
        })

        # Adaptive armor reduces damage over time
        if self.abilities_unlocked['adaptive_armor']:
            # Heal a small amount as "adaptation"
            self.health = min(self.max_health, self.health + int(actual_damage * 0.1))
            print(f"🛡️ [{self.name}] Adaptive armor mitigates {int(actual_damage * 0.1)} damage!")

    def get_adaptation_stats(self) -> Dict:
        """Return adaptation statistics"""
        return {
            'combat_encounters': self.combat_encounters,
            'detected_patterns': self.detected_patterns,
            'abilities_unlocked': self.abilities_unlocked,
            'chase_aggressiveness': self.chase_aggressiveness,
            'threat_radius': self.threat_radius,
            'total_damage_received': self.total_damage_received,
            'adaptation_level': sum(1 for v in self.abilities_unlocked.values() if v)
        }
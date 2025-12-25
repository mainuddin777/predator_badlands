"""
Q-Learning Enhanced Predator Agent

"""
from typing import Tuple, Optional, Dict
from agents.predator import Predator
import random
import pickle


class QLearningPredator(Predator):
    """
    Predator agent with Q-Learning capabilities
    """

    def __init__(self, name: str, position: Tuple[int, int],
                 health: int = 100, stamina: int = 100, honour: int = 0,
                 is_dek: bool = False, clan_rank: str = "Unblooded",
                 learning_rate: float = 0.1, discount_factor: float = 0.9,
                 epsilon: float = 0.2):
        super().__init__(name, position, health, stamina, honour, is_dek, clan_rank)

        # Q-Learning parameters
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon

        # Q-table: state -> action -> Q-value
        self.q_table = {}

        # Experience tracking
        self.last_state = None
        self.last_action = None
        self.last_honour = honour

        # Learning statistics
        self.total_rewards = 0
        self.actions_taken = 0
        self.exploration_count = 0
        self.exploitation_count = 0

    def _get_state_representation(self, environment) -> str:
        """
        Create state representation for Q-learning
        """
        # Discretize health
        if self.health > 70:
            health_level = "high"
        elif self.health > 40:
            health_level = "medium"
        else:
            health_level = "low"

        # Discretize stamina
        if self.stamina > 60:
            stamina_level = "high"
        elif self.stamina > 30:
            stamina_level = "medium"
        else:
            stamina_level = "low"

        # Discretize honour (MORE GRANULAR)
        if self.honour >= 80:
            honour_level = "elite"
        elif self.honour >= 50:
            honour_level = "ready"  # Ready for adversary
        elif self.honour >= 30:
            honour_level = "blooded"
        else:
            honour_level = "low"

        # Find nearest wildlife
        wildlife_nearby = self._count_nearby_wildlife(environment, radius=5)
        if wildlife_nearby >= 3:
            wildlife_level = "many"
        elif wildlife_nearby >= 1:
            wildlife_level = "some"
        else:
            wildlife_level = "none"

        # Check adversary proximity
        adversary_pos = environment.get_adversary_position()
        if adversary_pos:
            adv_dist = self._distance_to(adversary_pos)
            if adv_dist <= 3:
                adversary_level = "close"
            elif adv_dist <= 8:
                adversary_level = "near"
            else:
                adversary_level = "far"
        else:
            adversary_level = "none"

        state = f"{health_level}_{stamina_level}_{honour_level}_{wildlife_level}_{adversary_level}"
        return state

    def _count_nearby_wildlife(self, environment, radius: int) -> int:
        """Count wildlife within radius"""
        count = 0
        for agent in environment.agents:
            if agent.__class__.__name__ == 'Wildlife' and agent.is_alive:
                if self._distance_to(agent.position) <= radius:
                    count += 1
        return count

    def _get_possible_actions(self, environment) -> list:
        """
        Get list of possible actions
        """
        actions = []

        # Always allow rest (but make it less attractive in rewards)
        actions.append('rest')

        # Movement actions if have stamina
        if self.stamina >= 5:
            actions.extend(['move_N', 'move_S', 'move_E', 'move_W'])

        # Hunt wildlife aggressively (increased radius)
        nearby_wildlife = self._find_nearby_threats(environment, radius=5)
        if nearby_wildlife and self.stamina >= 10:
            actions.append('hunt_wildlife')

        # Approach adversary when honour >= 40 (LOWERED threshold)
        adversary_pos = environment.get_adversary_position()
        if adversary_pos and self.honour >= 40 and self.health > 40:
            actions.append('engage_adversary')

        # Seek wildlife if honour is low
        if self.honour < 50:
            actions.append('seek_prey')

        return actions

    def decide_action(self, environment):
        """
        Q-Learning decision making
        """
        current_state = self._get_state_representation(environment)
        possible_actions = self._get_possible_actions(environment)

        # Initialize Q-values for new state
        if current_state not in self.q_table:
            self.q_table[current_state] = {action: 0.0 for action in possible_actions}

        # FORCED ADVERSARY ENGAGEMENT when ready
        if self.honour >= 50 and self.health > 50 and self.stamina > 40:
            adversary = self._find_adversary(environment)
            if adversary:
                distance = self._distance_to(adversary.position)

                # Force approach 80% of the time when ready
                if random.random() < 0.8:
                    self.last_state = current_state
                    self.last_action = 'engage_adversary'
                    self.last_honour = self.honour
                    self.actions_taken += 1

                    if distance <= 1:
                        return {'type': 'attack', 'target': adversary}
                    else:
                        direction = self._calculate_direction(self.position, adversary.position)
                        return {'type': 'move', 'direction': direction}

        # FORCED HUNTING when honour is low
        if self.honour < 40 and self.stamina > 20:
            wildlife_nearby = self._find_nearby_threats(environment, radius=5)
            if wildlife_nearby:
                # Force hunting 70% of the time
                if random.random() < 0.7:
                    self.last_state = current_state
                    self.last_action = 'hunt_wildlife'
                    self.last_honour = self.honour
                    self.actions_taken += 1

                    closest = min(wildlife_nearby, key=lambda w: self._distance_to(w.position))
                    if self._distance_to(closest.position) <= 1:
                        return {'type': 'attack', 'target': closest}
                    else:
                        direction = self._calculate_direction(self.position, closest.position)
                        return {'type': 'move', 'direction': direction}

        # Epsilon-greedy action selection
        if random.random() < self.epsilon:
            chosen_action = random.choice(possible_actions)
            self.exploration_count += 1
        else:
            q_values = self.q_table[current_state]
            max_q = max(q_values.values())
            best_actions = [a for a, q in q_values.items() if q == max_q]
            chosen_action = random.choice(best_actions)
            self.exploitation_count += 1

        # Store for learning
        self.last_state = current_state
        self.last_action = chosen_action
        self.last_honour = self.honour
        self.actions_taken += 1

        # Convert to simulation action
        return self._convert_to_simulation_action(chosen_action, environment)

    def _find_adversary(self, environment):
        """Find the adversary agent"""
        for agent in environment.agents:
            if agent.__class__.__name__ in ['Adversary', 'AdaptiveAdversary']:
                if agent.is_alive:
                    return agent
        return None

    def _convert_to_simulation_action(self, q_action: str, environment) -> dict:
        """Convert Q-learning action to simulation action format"""
        if q_action == 'rest':
            return {'type': 'rest'}

        elif q_action.startswith('move_'):
            direction = q_action.split('_')[1]
            return {'type': 'move', 'direction': direction}

        elif q_action == 'hunt_wildlife':
            nearby_wildlife = self._find_nearby_threats(environment, radius=5)
            if nearby_wildlife:
                closest = min(nearby_wildlife, key=lambda w: self._distance_to(w.position))
                if self._distance_to(closest.position) <= 1:
                    return {'type': 'attack', 'target': closest}
                else:
                    direction = self._calculate_direction(self.position, closest.position)
                    return {'type': 'move', 'direction': direction}
            return {'type': 'rest'}

        elif q_action == 'engage_adversary':
            adversary = self._find_adversary(environment)
            if adversary:
                if self._distance_to(adversary.position) <= 1:
                    return {'type': 'attack', 'target': adversary}
                else:
                    direction = self._calculate_direction(self.position, adversary.position)
                    return {'type': 'move', 'direction': direction}
            return {'type': 'rest'}

        elif q_action == 'seek_prey':
            # Move toward nearest wildlife
            wildlife = self._find_nearby_threats(environment, radius=10)
            if wildlife:
                closest = min(wildlife, key=lambda w: self._distance_to(w.position))
                direction = self._calculate_direction(self.position, closest.position)
                return {'type': 'move', 'direction': direction}
            return {'type': 'move', 'direction': random.choice(['N', 'S', 'E', 'W'])}

        return {'type': 'rest'}

    def update_q_value(self, environment, reward: float = None):
        """
        Update Q-value based on observed reward
        """
        if self.last_state is None or self.last_action is None:
            return

        # Calculate reward if not provided
        if reward is None:
            reward = self._calculate_reward(environment)

        current_state = self._get_state_representation(environment)

        # Initialize Q-values for new state if needed
        if current_state not in self.q_table:
            possible_actions = self._get_possible_actions(environment)
            self.q_table[current_state] = {action: 0.0 for action in possible_actions}

        # Q-Learning update
        old_q = self.q_table[self.last_state].get(self.last_action, 0.0)
        max_future_q = max(self.q_table[current_state].values()) if self.q_table[current_state] else 0.0

        new_q = old_q + self.learning_rate * (reward + self.discount_factor * max_future_q - old_q)
        self.q_table[self.last_state][self.last_action] = new_q

        self.total_rewards += reward

    def _calculate_reward(self, environment) -> float:
        """
        Calculate reward based on state changes

        """
        reward = 0.0

        # MASSIVE reward for honour gain
        honour_change = self.honour - self.last_honour
        reward += honour_change * 10.0  # Increased from 5.0

        # Survival bonus
        if self.is_alive:
            reward += 1.0
        else:
            reward -= 200.0  # Death penalty

        # Health management
        if self.health < 20:
            reward -= 10.0  # Danger
        elif self.health > 70:
            reward += 2.0  # Healthy

        # Stamina management (less penalty to encourage action)
        if self.stamina < 10:
            reward -= 2.0

        # Adversary proximity rewards (when ready)
        adversary = self._find_adversary(environment)
        if adversary and adversary.is_alive:
            dist = self._distance_to(adversary.position)
            if self.honour >= 50 and self.health > 50:
                # REWARD being close to adversary when ready
                if dist < 5:
                    reward += 15.0
                elif dist < 10:
                    reward += 8.0
            else:
                # Small penalty for being too close when not ready
                if dist < 5:
                    reward -= 5.0

        # Reward for having trophies
        if hasattr(self, 'trophies'):
            reward += len(self.trophies) * 5.0

        # Penalty for inaction (resting too much)
        if self.last_action == 'rest' and self.stamina > 50:
            reward -= 5.0

        return reward

    def decay_epsilon(self, decay_rate: float = 0.995):
        """Gradually reduce exploration rate"""
        self.epsilon = max(0.05, self.epsilon * decay_rate)  # Min 5%

    def get_learning_stats(self) -> dict:
        """Return learning statistics"""
        return {
            'total_rewards': self.total_rewards,
            'actions_taken': self.actions_taken,
            'avg_reward': self.total_rewards / max(1, self.actions_taken),
            'exploration_count': self.exploration_count,
            'exploitation_count': self.exploitation_count,
            'exploration_rate': self.exploration_count / max(1, self.actions_taken),
            'q_table_size': len(self.q_table),
            'total_state_actions': sum(len(actions) for actions in self.q_table.values()),
            'current_epsilon': self.epsilon
        }
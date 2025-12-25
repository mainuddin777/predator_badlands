
import random
import sys
import os
from typing import Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from environment.grid import Grid
    from environment.hazards import HazardManager  # FIXED: Changed from mechanics.hazards
    from agents.qlearning_predator import QLearningPredator
    from agents.synthetic import Synthetic
    from agents.wildlife import Wildlife
    from agents.adaptive_adversary import AdaptiveAdversary
    from mechanics.honour import HonourSystem
    from mechanics.resources import ResourceManager
    from evaluation.statistical_evaluator import StatisticalEvaluator
    from config.settings import *

    HAS_HAZARDS = True
except ImportError as e:
    print(f"Import Error: {e}")
    print("\nPlease ensure all required files are in place:")
    print("  - agents/qlearning_predator.py")
    print("  - agents/adaptive_adversary.py")
    print("  - evaluation/statistical_evaluator.py")
    print("  - environment/hazards.py")
    print("\nAlso ensure all directories have __init__.py files")

    # Create a minimal HazardManager replacement if import fails
    HAS_HAZARDS = False
    print("\nWarning: Some modules not found, using fallback versions")


    class HazardManager:
        def __init__(self, grid):
            self.grid = grid
            self.hazards = []

        def generate_random_hazards(self, num):
            pass

        def check_hazards(self, agent):
            pass

        def update_weather(self):
            pass

        def trigger_random_weather(self):
            pass


class PredatorBadlandsSimulation:
    """
    Complete simulation with learning and adaptation
    """

    def __init__(self, seed: int = None, use_qlearning: bool = True,
                 use_adaptive_adversary: bool = True):
        if seed is not None:
            random.seed(seed)

        self.seed = seed
        self.use_qlearning = use_qlearning
        self.use_adaptive_adversary = use_adaptive_adversary

        # Initialize environment
        self.grid = Grid(GRID_WIDTH, GRID_HEIGHT)
        self.grid.initialize_environment(num_obstacles=20)

        # Initialize agents
        if use_qlearning:
            self.dek = QLearningPredator(
                "Dek", DEK_INITIAL_POSITION,
                health=DEK_INITIAL_HEALTH,
                stamina=DEK_INITIAL_STAMINA,
                honour=DEK_INITIAL_HONOUR,
                is_dek=True,
                learning_rate=0.15,  # Increased from 0.1
                discount_factor=0.9,
                epsilon=0.4  # Increased from 0.2 for more exploration
            )
        else:
            from agents.predator import Predator
            self.dek = Predator(
                "Dek", DEK_INITIAL_POSITION,
                health=DEK_INITIAL_HEALTH,
                stamina=DEK_INITIAL_STAMINA,
                honour=DEK_INITIAL_HONOUR,
                is_dek=True
            )

        self.thia = Synthetic("Thia", THIA_INITIAL_POSITION, is_damaged=True)

        if use_adaptive_adversary:
            self.adversary = AdaptiveAdversary(
                "The Great Beast",
                ADVERSARY_INITIAL_POSITION,
                health=ADVERSARY_INITIAL_HEALTH
            )
        else:
            from agents.adversary import Adversary
            self.adversary = Adversary(
                "The Great Beast",
                ADVERSARY_INITIAL_POSITION,
                health=ADVERSARY_INITIAL_HEALTH
            )

        # Add agents to grid
        self.grid.add_agent(self.dek)
        self.grid.add_agent(self.thia)
        self.grid.add_agent(self.adversary)

        # Add wildlife
        self._spawn_wildlife(NUM_WILDLIFE)

        # Initialize systems
        self.hazard_manager = HazardManager(self.grid)
        self.hazard_manager.generate_random_hazards(10)

        self.running = True
        self.turn = 0

    def _spawn_wildlife(self, count: int):
        """Spawn wildlife creatures"""
        for i in range(count):
            pos = self._find_empty_position()
            threat_level = random.randint(1, 3)
            wildlife = Wildlife(f"Creature_{i + 1}", pos, threat_level=threat_level)
            self.grid.add_agent(wildlife)

    def _find_empty_position(self) -> Tuple[int, int]:
        """Find random empty position"""
        while True:
            x = random.randint(0, self.grid.width - 1)
            y = random.randint(0, self.grid.height - 1)
            if self.grid.is_valid_position((x, y)):
                cell = self.grid.get_cell((x, y))
                if len(cell.occupants) == 0:
                    return (x, y)

    def run_turn(self):
        """Execute one simulation turn"""
        self.turn += 1

        # All agents decide and act
        for agent in self.grid.agents[:]:
            if not agent.is_alive:
                continue

            # Agent decision
            action = agent.decide_action(self.grid)

            # Execute action
            agent.execute_action(action, self.grid)

            # Update Q-learning if applicable
            if hasattr(agent, 'update_q_value'):
                agent.update_q_value(self.grid)

            # Check hazards
            self.hazard_manager.check_hazards(agent)

        # Thia provides advice every 10 turns
        if self.turn % 10 == 0 and self.thia.is_alive:
            self.thia._provide_knowledge(self.grid)

        # Update environment
        self.grid.update()
        self.hazard_manager.update_weather()
        self.hazard_manager.trigger_random_weather()

        # Decay epsilon for Q-learning
        if hasattr(self.dek, 'decay_epsilon'):
            if self.turn % 50 == 0:
                self.dek.decay_epsilon()

        # Check end conditions
        if not self.dek.is_alive:
            self.running = False
            return False

        if not self.adversary.is_alive:
            self.running = False
            return True

        return None

    def run(self, max_turns: int = 500, verbose: bool = False) -> dict:
        """
        Run complete simulation

        Returns:
            dict with simulation results
        """
        while self.running and self.turn < max_turns:
            result = self.run_turn()

            if verbose and self.turn % 50 == 0:
                print(f"Turn {self.turn}: Dek HP={self.dek.health}, "
                      f"Honour={self.dek.honour}, Stamina={self.dek.stamina}")

        # Return results
        return {
            'turns': self.turn,
            'honour': self.dek.honour,
            'adversary_alive': self.adversary.is_alive if self.adversary else True,
            'dek_alive': self.dek.is_alive,
            'victory': not self.adversary.is_alive if self.adversary else False
        }


def simulation_factory(seed: int):
    """Factory function to create simulations for statistical evaluation"""
    return PredatorBadlandsSimulation(
        seed=seed,
        use_qlearning=True,
        use_adaptive_adversary=True
    )


def run_full_evaluation(num_runs: int = 20):
    """
    Run complete evaluation with all requirements for 80-100 band
    """
    print("=" * 70)
    print("PREDATOR: BADLANDS - COMPREHENSIVE EVALUATION")
    print("Expert-Level Challenge Implementation")
    print("=" * 70)
    print()

    # Create evaluator
    evaluator = StatisticalEvaluator(num_runs=num_runs)

    # Run simulations with reduced max_turns to encourage confrontation
    evaluator.run_multiple_simulations(simulation_factory, max_turns=300)  # Reduced from 500

    # Generate outputs
    print("\nGenerating analysis outputs...")

    # 1. Statistical report
    report_file = evaluator.generate_report()

    # 2. Visualizations
    evaluator.generate_visualizations()

    # 3. Raw data
    data_file = evaluator.save_raw_data()

    # 4. Print summary statistics
    stats = evaluator.calculate_statistics()
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    print(f"Total Simulations:        {stats['num_runs']}")
    print(
        f"Mean Survival Time:       {stats['turns_survived']['mean']:.2f} ± {stats['turns_survived']['std']:.2f} turns")
    print(f"Mean Final Honour:        {stats['final_honour']['mean']:.2f} ± {stats['final_honour']['std']:.2f}")
    print(f"Adversary Defeat Rate:    {stats['adversary_defeat_rate']:.1f}%")
    print(f"Dek Survival Rate:        {stats['survival_rate']:.1f}%")
    print(f"95% CI (Survival):        ({stats['turns_survived']['confidence_interval_95'][0]:.2f}, "
          f"{stats['turns_survived']['confidence_interval_95'][1]:.2f})")
    print(f"95% CI (Honour):          ({stats['final_honour']['confidence_interval_95'][0]:.2f}, "
          f"{stats['final_honour']['confidence_interval_95'][1]:.2f})")
    print("=" * 70)

    print("\n Evaluation complete!")
    print(f" Report saved: {report_file}")
    print(f" Data saved: {data_file}")
    print(f" Visualizations generated")

    return evaluator


def run_single_demo():
    """Run a single demonstration simulation with detailed output"""
    print("=" * 70)
    print("RUNNING SINGLE DEMONSTRATION")
    print("=" * 70)

    sim = PredatorBadlandsSimulation(seed=42, use_qlearning=True, use_adaptive_adversary=True)

    print(f"\nInitial State:")
    print(f"  Dek: Position {sim.dek.position}, HP={sim.dek.health}, Stamina={sim.dek.stamina}")
    print(f"  Adversary: Position {sim.adversary.position}, HP={sim.adversary.health}")
    print(f"  Thia: Position {sim.thia.position}, HP={sim.thia.health}")
    print()

    result = sim.run(max_turns=500, verbose=True)

    print(f"\nFinal Results:")
    print(f"  Turns Survived: {result['turns']}")
    print(f"  Final Honour: {result['honour']}")
    print(f"  Victory: {result['victory']}")
    print(f"  Dek Status: {'Alive' if result['dek_alive'] else 'Defeated'}")

    if hasattr(sim.dek, 'get_learning_stats'):
        print(f"\nQ-Learning Statistics:")
        stats = sim.dek.get_learning_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

    if hasattr(sim.adversary, 'get_adaptation_stats'):
        print(f"\nAdversary Adaptation:")
        stats = sim.adversary.get_adaptation_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Predator: Badlands Evaluation')
    parser.add_argument('--demo', action='store_true', help='Run single demonstration')
    parser.add_argument('--runs', type=int, default=20, help='Number of evaluation runs')

    args = parser.parse_args()

    if args.demo:
        run_single_demo()
    else:
        run_full_evaluation(num_runs=args.runs)
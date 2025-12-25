"""
Statistical Evaluation System
"""
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict
import json
from datetime import datetime


class SimulationResult:


    def __init__(self, seed: int):
        self.seed = seed
        self.turns_survived = 0
        self.final_honour = 0
        self.initial_honour = 0
        self.honour_progression = []
        self.health_progression = []
        self.stamina_progression = []
        self.adversary_defeated = False
        self.dek_survived = False
        self.trophies_collected = 0
        self.total_damage_dealt = 0
        self.total_damage_taken = 0
        self.clan_rank_achieved = "Unblooded"
        self.wildlife_killed = 0


class StatisticalEvaluator:

    def __init__(self, num_runs: int = 20):
        self.num_runs = num_runs
        self.results: List[SimulationResult] = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_multiple_simulations(self, simulation_factory, max_turns: int = 500):
        """
        Run multiple simulations with different random seeds

        Args:
            simulation_factory: Function that creates a new simulation
            max_turns: Maximum turns per simulation
        """
        print(f"\n{'=' * 60}")
        print(f"RUNNING {self.num_runs} SIMULATIONS FOR STATISTICAL ANALYSIS")
        print(f"{'=' * 60}\n")

        for i in range(self.num_runs):
            print(f"[Run {i + 1}/{self.num_runs}] Starting simulation with seed {i}...")

            # Create new simulation with unique seed
            sim = simulation_factory(seed=i)
            result = SimulationResult(seed=i)

            # Track initial state
            result.initial_honour = sim.dek.honour

            # Run simulation
            turn = 0
            while sim.running and turn < max_turns:
                turn += 1

                # Execute turn
                for agent in sim.grid.agents[:]:
                    if agent.is_alive:
                        action = agent.decide_action(sim.grid)
                        agent.execute_action(action, sim.grid)

                        # Update Q-learning if applicable
                        if hasattr(agent, 'update_q_value'):
                            agent.update_q_value(sim.grid)

                sim.grid.update()

                # Track metrics every 10 turns
                if turn % 10 == 0:
                    result.honour_progression.append(sim.dek.honour if sim.dek.is_alive else 0)
                    result.health_progression.append(sim.dek.health if sim.dek.is_alive else 0)
                    if hasattr(sim.dek, 'stamina'):
                        result.stamina_progression.append(sim.dek.stamina if sim.dek.is_alive else 0)

                # Check end conditions
                if not sim.dek.is_alive:
                    sim.running = False
                    break

                if sim.adversary and not sim.adversary.is_alive:
                    result.adversary_defeated = True
                    sim.running = False
                    break

            # Record final results
            result.turns_survived = turn
            result.final_honour = sim.dek.honour if sim.dek.is_alive else 0
            result.dek_survived = sim.dek.is_alive
            result.clan_rank_achieved = sim.dek.clan_rank if sim.dek.is_alive else "Dead"

            if hasattr(sim.dek, 'trophies'):
                result.trophies_collected = len(sim.dek.trophies)

            self.results.append(result)

            # Print summary
            status = "✓ VICTORY" if result.adversary_defeated else "✗ DEFEAT" if not result.dek_survived else "→ ONGOING"
            print(
                f"   {status} | Turns: {result.turns_survived} | Honour: {result.final_honour} | Rank: {result.clan_rank_achieved}")

        print(f"\n{'=' * 60}")
        print(f"COMPLETED {self.num_runs} SIMULATIONS")
        print(f"{'=' * 60}\n")

    def calculate_statistics(self) -> Dict:
        """Calculate comprehensive statistics"""
        if not self.results:
            return {}

        turns = [r.turns_survived for r in self.results]
        honours = [r.final_honour for r in self.results]
        defeats = sum(1 for r in self.results if r.adversary_defeated)
        survivals = sum(1 for r in self.results if r.dek_survived)

        stats = {
            'num_runs': self.num_runs,
            'turns_survived': {
                'mean': np.mean(turns),
                'std': np.std(turns),
                'min': np.min(turns),
                'max': np.max(turns),
                'median': np.median(turns),
                'confidence_interval_95': self._confidence_interval(turns, 0.95)
            },
            'final_honour': {
                'mean': np.mean(honours),
                'std': np.std(honours),
                'min': np.min(honours),
                'max': np.max(honours),
                'median': np.median(honours),
                'confidence_interval_95': self._confidence_interval(honours, 0.95)
            },
            'adversary_defeat_rate': defeats / self.num_runs * 100,
            'survival_rate': survivals / self.num_runs * 100,
            'average_trophies': np.mean([r.trophies_collected for r in self.results])
        }

        return stats

    def _confidence_interval(self, data: List[float], confidence: float = 0.95) -> tuple:
        """Calculate confidence interval"""
        n = len(data)
        mean = np.mean(data)
        std_err = np.std(data) / np.sqrt(n)
        margin = 1.96 * std_err  # z-score for 95% confidence
        return (mean - margin, mean + margin)

    def generate_report(self, filename: str = None):
        """Generate text report of statistics"""
        stats = self.calculate_statistics()

        if filename is None:
            filename = f"simulation_report_{self.timestamp}.txt"

        with open(filename, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("PREDATOR: BADLANDS - STATISTICAL EVALUATION REPORT\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Number of Simulations: {stats['num_runs']}\n")
            f.write(f"Timestamp: {self.timestamp}\n\n")

            f.write("-" * 70 + "\n")
            f.write("SURVIVAL METRICS\n")
            f.write("-" * 70 + "\n")
            f.write(
                f"Turns Survived (Mean ± Std):  {stats['turns_survived']['mean']:.2f} ± {stats['turns_survived']['std']:.2f}\n")
            f.write(f"Turns Survived (Median):      {stats['turns_survived']['median']:.2f}\n")
            f.write(
                f"Turns Survived (Range):       {stats['turns_survived']['min']:.0f} - {stats['turns_survived']['max']:.0f}\n")
            f.write(
                f"95% Confidence Interval:      ({stats['turns_survived']['confidence_interval_95'][0]:.2f}, {stats['turns_survived']['confidence_interval_95'][1]:.2f})\n\n")

            f.write("-" * 70 + "\n")
            f.write("HONOUR METRICS\n")
            f.write("-" * 70 + "\n")
            f.write(
                f"Final Honour (Mean ± Std):    {stats['final_honour']['mean']:.2f} ± {stats['final_honour']['std']:.2f}\n")
            f.write(f"Final Honour (Median):        {stats['final_honour']['median']:.2f}\n")
            f.write(
                f"Final Honour (Range):         {stats['final_honour']['min']:.0f} - {stats['final_honour']['max']:.0f}\n")
            f.write(
                f"95% Confidence Interval:      ({stats['final_honour']['confidence_interval_95'][0]:.2f}, {stats['final_honour']['confidence_interval_95'][1]:.2f})\n\n")

            f.write("-" * 70 + "\n")
            f.write("SUCCESS RATES\n")
            f.write("-" * 70 + "\n")
            f.write(f"Adversary Defeat Rate:        {stats['adversary_defeat_rate']:.1f}%\n")
            f.write(f"Dek Survival Rate:            {stats['survival_rate']:.1f}%\n")
            f.write(f"Average Trophies Collected:   {stats['average_trophies']:.2f}\n\n")

            f.write("-" * 70 + "\n")
            f.write("INDIVIDUAL RUN DETAILS\n")
            f.write("-" * 70 + "\n")
            for i, result in enumerate(self.results, 1):
                status = "VICTORY" if result.adversary_defeated else "DEFEAT" if not result.dek_survived else "ONGOING"
                f.write(f"Run {i:2d} | {status:8s} | Turns: {result.turns_survived:3d} | "
                        f"Honour: {result.final_honour:3d} | Rank: {result.clan_rank_achieved}\n")

        print(f"✓ Report saved to {filename}")
        return filename

    def generate_visualizations(self, output_dir: str = "."):
        """Generate comprehensive visualization graphs"""
        if not self.results:
            print("⚠ No results to visualize")
            return

        # Create figure with multiple subplots
        fig = plt.figure(figsize=(16, 12))

        # 1. Survival Time Distribution
        ax1 = plt.subplot(2, 3, 1)
        turns = [r.turns_survived for r in self.results]
        ax1.hist(turns, bins=15, color='#2E86AB', alpha=0.7, edgecolor='black')
        ax1.axvline(np.mean(turns), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(turns):.1f}')
        ax1.set_xlabel('Turns Survived', fontweight='bold')
        ax1.set_ylabel('Frequency', fontweight='bold')
        ax1.set_title('Distribution of Survival Time', fontweight='bold', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. Final Honour Distribution
        ax2 = plt.subplot(2, 3, 2)
        honours = [r.final_honour for r in self.results]
        ax2.hist(honours, bins=15, color='#A23B72', alpha=0.7, edgecolor='black')
        ax2.axvline(np.mean(honours), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(honours):.1f}')
        ax2.set_xlabel('Final Honour', fontweight='bold')
        ax2.set_ylabel('Frequency', fontweight='bold')
        ax2.set_title('Distribution of Final Honour', fontweight='bold', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. Success Rates
        ax3 = plt.subplot(2, 3, 3)
        defeats = sum(1 for r in self.results if r.adversary_defeated)
        survivals = sum(1 for r in self.results if r.dek_survived)
        categories = ['Adversary\nDefeated', 'Dek\nSurvived']
        values = [defeats / self.num_runs * 100, survivals / self.num_runs * 100]
        bars = ax3.bar(categories, values, color=['#F18F01', '#06A77D'], alpha=0.7, edgecolor='black')
        ax3.set_ylabel('Success Rate (%)', fontweight='bold')
        ax3.set_title('Mission Success Rates', fontweight='bold', fontsize=12)
        ax3.set_ylim(0, 100)
        ax3.grid(True, alpha=0.3, axis='y')
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')

        # 4. Honour Progression Over Time (averaged)
        ax4 = plt.subplot(2, 3, 4)
        max_len = max(len(r.honour_progression) for r in self.results)
        honour_matrix = np.zeros((len(self.results), max_len))
        for i, result in enumerate(self.results):
            honour_matrix[i, :len(result.honour_progression)] = result.honour_progression
            if len(result.honour_progression) < max_len:
                honour_matrix[i, len(result.honour_progression):] = result.honour_progression[-1]

        mean_honour = np.mean(honour_matrix, axis=0)
        std_honour = np.std(honour_matrix, axis=0)
        turns_axis = np.arange(0, max_len * 10, 10)[:max_len]

        ax4.plot(turns_axis, mean_honour, color='#A23B72', linewidth=2, label='Mean Honour')
        ax4.fill_between(turns_axis, mean_honour - std_honour, mean_honour + std_honour,
                         alpha=0.3, color='#A23B72', label='±1 Std Dev')
        ax4.set_xlabel('Turn Number', fontweight='bold')
        ax4.set_ylabel('Honour', fontweight='bold')
        ax4.set_title('Honour Progression Over Time', fontweight='bold', fontsize=12)
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        # 5. Box Plot: Turns vs Outcome
        ax5 = plt.subplot(2, 3, 5)
        victory_turns = [r.turns_survived for r in self.results if r.adversary_defeated]
        defeat_turns = [r.turns_survived for r in self.results if not r.dek_survived]
        ongoing_turns = [r.turns_survived for r in self.results if r.dek_survived and not r.adversary_defeated]

        data_to_plot = []
        labels = []
        if victory_turns:
            data_to_plot.append(victory_turns)
            labels.append(f'Victory\n(n={len(victory_turns)})')
        if ongoing_turns:
            data_to_plot.append(ongoing_turns)
            labels.append(f'Ongoing\n(n={len(ongoing_turns)})')
        if defeat_turns:
            data_to_plot.append(defeat_turns)
            labels.append(f'Defeat\n(n={len(defeat_turns)})')

        bp = ax5.boxplot(data_to_plot, labels=labels, patch_artist=True)
        colors = ['#06A77D', '#F18F01', '#C73E1D']
        for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax5.set_ylabel('Turns Survived', fontweight='bold')
        ax5.set_title('Survival Time by Outcome', fontweight='bold', fontsize=12)
        ax5.grid(True, alpha=0.3, axis='y')

        # 6. Correlation: Honour vs Survival
        ax6 = plt.subplot(2, 3, 6)
        colours_scatter = ['#06A77D' if r.adversary_defeated else '#C73E1D' if not r.dek_survived else '#F18F01'
                           for r in self.results]
        ax6.scatter([r.final_honour for r in self.results],
                    [r.turns_survived for r in self.results],
                    c=colours_scatter, alpha=0.6, s=100, edgecolors='black')
        ax6.set_xlabel('Final Honour', fontweight='bold')
        ax6.set_ylabel('Turns Survived', fontweight='bold')
        ax6.set_title('Honour vs Survival Time', fontweight='bold', fontsize=12)
        ax6.grid(True, alpha=0.3)

        # Add correlation line
        z = np.polyfit([r.final_honour for r in self.results],
                       [r.turns_survived for r in self.results], 1)
        p = np.poly1d(z)
        ax6.plot(sorted([r.final_honour for r in self.results]),
                 p(sorted([r.final_honour for r in self.results])),
                 "r--", alpha=0.8, linewidth=2, label='Trend')
        ax6.legend()

        plt.suptitle(f'Predator: Badlands - Statistical Analysis ({self.num_runs} runs)',
                     fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()

        filename = f"{output_dir}/statistical_analysis_{self.timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ Visualization saved to {filename}")
        plt.show()

    def save_raw_data(self, filename: str = None):
        """Save raw results data to JSON"""
        if filename is None:
            filename = f"raw_results_{self.timestamp}.json"

        # Convert numpy types to native Python types for JSON serialization
        def convert_to_native(obj):
            """Convert numpy types to Python native types"""
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_to_native(value) for key, value in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_native(item) for item in obj]
            return obj

        stats = self.calculate_statistics()

        data = {
            'metadata': {
                'num_runs': self.num_runs,
                'timestamp': self.timestamp
            },
            'results': [
                {
                    'seed': r.seed,
                    'turns_survived': r.turns_survived,
                    'final_honour': r.final_honour,
                    'adversary_defeated': r.adversary_defeated,
                    'dek_survived': r.dek_survived,
                    'trophies_collected': r.trophies_collected,
                    'clan_rank_achieved': r.clan_rank_achieved,
                    'honour_progression': r.honour_progression,
                    'health_progression': r.health_progression,
                    'stamina_progression': r.stamina_progression
                }
                for r in self.results
            ],
            'statistics': convert_to_native(stats)
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Raw data saved to {filename}")
        return filename
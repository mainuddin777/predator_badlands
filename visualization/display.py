"""
Visualization module for the simulation
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import numpy as np


class GridVisualizer:
    """
    Visualize the simulation grid and agents
    """

    def __init__(self, grid, cell_size=20):
        self.grid = grid
        self.cell_size = cell_size
        self.fig = None
        self.ax = None

        # Colors
        self.colors = {
            'empty': '#F4E4C1',
            'obstacle': '#8B7355',
            'dek': '#00FF00',
            'thia': '#87CEEB',
            'adversary': '#8B0000',
            'wildlife': '#CD853F',
            'clan': '#FFD700'
        }

    def create_figure(self):
        """Create the matplotlib figure"""
        self.fig, self.ax = plt.subplots(figsize=(12, 12))
        self.ax.set_xlim(0, self.grid.width)
        self.ax.set_ylim(0, self.grid.height)
        self.ax.set_aspect('equal')
        self.ax.invert_yaxis()  # Invert Y-axis so (0,0) is top-left

        # Remove ticks
        self.ax.set_xticks(range(self.grid.width))
        self.ax.set_yticks(range(self.grid.height))
        self.ax.grid(True, alpha=0.3)

        plt.title("Predator: Badlands Simulation", fontsize=16, fontweight='bold')

    def render(self, turn=0):
        """Render current state of the grid"""
        if self.fig is None:
            self.create_figure()

        self.ax.clear()
        self.ax.set_xlim(0, self.grid.width)
        self.ax.set_ylim(0, self.grid.height)
        self.ax.set_aspect('equal')
        self.ax.invert_yaxis()
        self.ax.set_xticks(range(0, self.grid.width, 5))
        self.ax.set_yticks(range(0, self.grid.height, 5))
        self.ax.grid(True, alpha=0.3)

        # Draw obstacles
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                cell = self.grid.cells[x][y]
                if cell.terrain_type == 'obstacle':
                    rect = patches.Rectangle(
                        (x, y), 1, 1,
                        linewidth=0,
                        edgecolor='none',
                        facecolor=self.colors['obstacle']
                    )
                    self.ax.add_patch(rect)

        # Draw agents
        for agent in self.grid.agents:
            if not agent.is_alive:
                continue

            x, y = agent.position

            # Determine color and marker
            if agent.__class__.__name__ == 'Predator':
                if hasattr(agent, 'is_dek') and agent.is_dek:
                    color = self.colors['dek']
                    marker = 's'  # Square for Dek
                    size = 200
                    label = 'Dek'
                else:
                    color = self.colors['clan']
                    marker = '^'  # Triangle for clan
                    size = 150
                    label = agent.name

            elif agent.__class__.__name__ == 'Synthetic':
                color = self.colors['thia']
                marker = 'D'  # Diamond for Thia
                size = 150
                label = 'Thia'

            elif agent.__class__.__name__ == 'Adversary':
                color = self.colors['adversary']
                marker = '*'  # Star for Adversary
                size = 400
                label = 'ADVERSARY'

            elif agent.__class__.__name__ == 'Wildlife':
                color = self.colors['wildlife']
                marker = 'o'  # Circle for wildlife
                size = 80
                label = None

            else:
                color = 'gray'
                marker = 'x'
                size = 100
                label = None

            # Plot agent
            self.ax.scatter(x + 0.5, y + 0.5, c=color, marker=marker,
                            s=size, edgecolors='black', linewidths=1.5, zorder=5)

            # Add label for important agents
            if label and agent.__class__.__name__ != 'Wildlife':
                self.ax.text(x + 0.5, y + 0.3, label,
                             ha='center', va='center',
                             fontsize=8, fontweight='bold',
                             bbox=dict(boxstyle='round,pad=0.3',
                                       facecolor='white', alpha=0.7))

        # Add title with turn info
        plt.title(f"Predator: Badlands - Turn {turn}",
                  fontsize=14, fontweight='bold')

        # Add legend
        legend_elements = [
            plt.Line2D([0], [0], marker='s', color='w',
                       markerfacecolor=self.colors['dek'], markersize=10, label='Dek'),
            plt.Line2D([0], [0], marker='^', color='w',
                       markerfacecolor=self.colors['clan'], markersize=10, label='Clan'),
            plt.Line2D([0], [0], marker='D', color='w',
                       markerfacecolor=self.colors['thia'], markersize=10, label='Thia'),
            plt.Line2D([0], [0], marker='*', color='w',
                       markerfacecolor=self.colors['adversary'], markersize=15, label='Adversary'),
            plt.Line2D([0], [0], marker='o', color='w',
                       markerfacecolor=self.colors['wildlife'], markersize=8, label='Wildlife'),
        ]
        self.ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))

        plt.tight_layout()
        plt.draw()
        plt.pause(0.01)

    def save_snapshot(self, filename, turn=0):
        """Save current visualization to file"""
        self.render(turn)
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"📸 Saved snapshot: {filename}")

    def show(self):
        """Display the visualization"""
        plt.show()

    def close(self):
        """Close the visualization"""
        plt.close(self.fig)


def visualize_simulation_run(simulation, save_snapshots=False):
    """
    Run simulation with live visualization

    Args:
        simulation: PredatorBadlandsSimulation instance
        save_snapshots: Whether to save periodic snapshots
    """
    visualizer = GridVisualizer(simulation.grid)
    visualizer.create_figure()

    turn = 0
    max_turns = 200

    while simulation.running and turn < max_turns:
        turn += 1

        # Execute one turn of simulation
        for agent in simulation.grid.agents[:]:
            if agent.is_alive:
                action = agent.decide_action(simulation.grid)
                agent.execute_action(action, simulation.grid)

        simulation.grid.update()

        # Visualize
        visualizer.render(turn)

        # Save snapshot every 20 turns
        if save_snapshots and turn % 20 == 0:
            visualizer.save_snapshot(f'snapshot_turn_{turn}.png', turn)

        # Check end conditions
        if not simulation.dek.is_alive or \
                (simulation.adversary and not simulation.adversary.is_alive):
            break

    visualizer.show()
    visualizer.close()


if __name__ == "__main__":
    # Test visualization with a simple grid
    from environment.grid import Grid
    from agents.predator import Predator

    grid = Grid(20, 20)
    grid.initialize_environment(10)

    dek = Predator("Dek", (5, 5), is_dek=True)
    grid.add_agent(dek)

    viz = GridVisualizer(grid)
    viz.render()
    viz.show()
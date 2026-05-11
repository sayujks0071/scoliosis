from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def generate_energy_deficit_plot():
    # File paths
    input_file = Path("outputs/thermodynamic_cost/energy_deficit_window.csv")
    output_file = Path("research/figures/energy_deficit_window_plot.png")

    if not input_file.exists():
        print(f"Error: Could not find data file at {input_file}")
        return

    # Read data
    df = pd.read_csv(input_file)

    # Set up the plot style
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))

    # Plot the lines
    sns.lineplot(data=df, x="L", y="P_counter", label="Energy Cost (P_counter)", color="red", linewidth=2.5)
    sns.lineplot(data=df, x="L", y="S_proprio_alpha05", label="Supply (alpha=0.5)", color="blue", linestyle="--")
    sns.lineplot(data=df, x="L", y="S_proprio_alpha10", label="Supply (alpha=1.0)", color="green", linestyle="--")

    # Fill the 'Energy Deficit Window' where cost exceeds supply
    plt.fill_between(
        df["L"],
        df["P_counter"],
        df["S_proprio_alpha05"],
        where=(df["P_counter"] > df["S_proprio_alpha05"]),
        color="red",
        alpha=0.1,
        interpolate=True,
        label="Deficit Window (alpha=0.5)"
    )

    # Add labels and title
    plt.xlabel("Spinal Length L (m)", fontsize=12)
    plt.ylabel("Energy (Arbitrary Units)", fontsize=12)
    plt.title("Thermodynamic Instability: Energy Deficit Window", fontsize=14, pad=15)

    # Legend
    plt.legend(loc="upper left")

    # Tight layout and save
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Successfully saved plot to {output_file}")

if __name__ == "__main__":
    generate_energy_deficit_plot()

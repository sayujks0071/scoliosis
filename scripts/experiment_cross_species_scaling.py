"""
Experiment: Cross-Species Scaling — The Allometric Trap.

This script implements the "Cross-Species Validation" (Figure 3) for the Nature submission.
It calculates the Bio-Gravitational Number (Bg) across 9 species to demonstrate that
humans occupy a unique "Allometric Trap" where passive stiffness is insufficient
to resist gravity (Bg < 0.1), necessitating a fragile active control system.

Formula:
    Bg = EI / (M * g * L^2)

    Where:
    - EI: Flexural Rigidity (Nm^2)
    - M: Body Mass (kg)
    - g: Gravitational Acceleration (9.81 m/s^2)
    - L: Spinal Length (m)

Interpretation:
    - Bg >> 1: Stiff, passively stable (e.g., Mouse).
    - Bg << 1: Flexible, buckling-prone, requires active control (e.g., Human).

Data Source:
    - data/species_parameters.csv

Outputs:
    - outputs/thermodynamic_cost/cross_species_scaling.csv
    - outputs/figures/cross_species_scaling.png
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Constants
G_EARTH = 9.81  # m/s^2

def calculate_bg(row):
    """Calculate Bio-Gravitational Number."""
    try:
        M = float(row['Mass_kg'])
        L = float(row['Length_m'])
        EI = float(row['EI_Nm2'])

        if M <= 0 or L <= 0:
            return None

        # Bg = EI / (M * g * L^2)
        # Note: M*g*L is the moment of the weight. L is the lever arm.
        # Sometimes formulated as EI / (P_crit * L^2) where P_crit ~ M*g.
        # Using the formulation from the manuscript: Bg = EI / (M g L^2)

        bg = EI / (M * G_EARTH * (L**2))
        return bg
    except (ValueError, TypeError):
        return None

def run_experiment():
    print("=" * 80)
    print("EXPERIMENT: Cross-Species Scaling (The Allometric Trap)")
    print("=" * 80)

    input_file = Path("data/species_parameters.csv")
    output_dir_csv = Path("outputs/thermodynamic_cost")
    output_dir_fig = Path("outputs/figures")

    # Ensure output directories exist
    output_dir_csv.mkdir(parents=True, exist_ok=True)
    output_dir_fig.mkdir(parents=True, exist_ok=True)

    if not input_file.exists():
        print(f"ERROR: Input file {input_file} not found.")
        sys.exit(1)

    # Read Data
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} species from {input_file}")

    # Calculate Bg
    df['Bg'] = df.apply(calculate_bg, axis=1)

    # Drop invalid rows
    df_clean = df.dropna(subset=['Bg'])

    # Save Results
    output_csv = output_dir_csv / "cross_species_scaling.csv"
    df_clean.to_csv(output_csv, index=False)
    print(f"Saved calculated metrics to {output_csv}")

    # --- Visualization ---
    plt.figure(figsize=(10, 8))

    # Log-Log Plot: Bg vs Mass
    # We plot Bg on Y, Mass on X.

    x = df_clean['Mass_kg']
    y = df_clean['Bg']
    labels = df_clean['Species']
    postures = df_clean['Posture']

    # Color mapping for posture
    colors = {'Quadruped': 'blue', 'Biped': 'red', 'Facultative_Biped': 'orange'}
    c_list = [colors.get(p, 'gray') for p in postures]

    plt.scatter(x, y, c=c_list, s=150, alpha=0.7, edgecolors='black')

    plt.xscale('log')
    plt.yscale('log')

    plt.xlabel('Body Mass M (kg)', fontsize=14)
    plt.ylabel('Bio-Gravitational Number Bg (Dimensionless)', fontsize=14)
    plt.title('The Allometric Trap: Passive Stiffness vs. Mass', fontsize=16)

    # Add Threshold Zones
    # Bg = 0.1 Threshold
    xmin, xmax = plt.xlim()
    plt.hlines(0.1, xmin, xmax, colors='red', linestyles='dashed', label='Stability Threshold (Bg=0.1)')

    # Fill Zones
    plt.fill_between([xmin, xmax], 0.1, 1000, color='green', alpha=0.05, label='Passively Stable')
    plt.fill_between([xmin, xmax], 0.0001, 0.1, color='red', alpha=0.05, label='Metabolically Dependent')

    # Annotate Points
    for i, txt in enumerate(labels):
        plt.annotate(txt, (x.iloc[i], y.iloc[i]), xytext=(5, 5), textcoords='offset points', fontsize=9)

    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.legend(loc='upper right')

    # Save Plot
    output_fig = output_dir_fig / "cross_species_scaling.png"
    plt.savefig(output_fig, dpi=300, bbox_inches='tight')
    print(f"Saved figure to {output_fig}")
    print("=" * 80)

    # Print a summary table to console
    print(f"{'Species':<20} | {'Mass (kg)':<10} | {'Bg':<10} | {'Regime'}")
    print("-" * 60)
    for _, row in df_clean.sort_values('Bg', ascending=False).iterrows():
        regime = "Stable" if row['Bg'] > 0.1 else "UNSTABLE"
        print(f"{row['Species']:<20} | {row['Mass_kg']:<10.2f} | {row['Bg']:<10.4f} | {regime}")
    print("-" * 60)

if __name__ == "__main__":
    run_experiment()

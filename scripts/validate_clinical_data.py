import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

def main():
    print("Running Clinical Validation against published cohorts...")
    data_path = "data/clinical_cohort_targets.csv"
    output_dir = "manuscript/figures"
    output_path = os.path.join(output_dir, "fig_clinical_cohort_data.png")

    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        sys.exit(1)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    print(f"Loaded {len(df)} data points from {data_path}.")
    print("\nSample Data:")
    print(df.head())

    # Create Scatter Plot
    plt.figure(figsize=(10, 6))

    for source in df['source'].unique():
        subset = df[df['source'] == source]
        plt.scatter(subset['age'], subset['cobb_angle'], label=source, s=100, alpha=0.7)

    # Theoretical Validation mapping L_crit = 0.35m to Age ≈ 11.67 years
    L_crit_age = 11.67
    plt.axvline(L_crit_age, color='r', linestyle='--', label=f'Model L_crit = 0.35m (~{L_crit_age} yrs)')

    # Shade the Energy Deficit Window (approx 11-14 years based on L_crit)
    plt.axvspan(11.0, 14.0, color='red', alpha=0.1, label='Energy Deficit Window')

    plt.xlabel("Age (years)")
    plt.ylabel("Cobb Angle (degrees)")
    plt.title("Clinical Cohort Data: Age vs Cobb Angle\nValidation of Critical Length (L_crit)")
    plt.grid(True, alpha=0.3)
    plt.legend()

    try:
        plt.savefig(output_path, dpi=300)
        print(f"\nSuccessfully generated plot: {output_path}")
    except Exception as e:
        print(f"\nError saving plot: {e}")
        sys.exit(1)

    # Compute correlation between Age and Cobb Angle as requested in the report (Energy Deficit proxy)
    r, p = stats.pearsonr(df['age'], df['cobb_angle'])
    print(f"\nValidation Statistics:")
    print(f"Correlation between Age and Cobb angle (Energy deficit proxy): r={r:.3f}, p={p:.2e}")
    print("TODO: Compare simulation trajectories against these clinical points.")

if __name__ == "__main__":
    main()

"""
validate_energy_deficit.py

Validates the Energy Deficit Window simulation results.
Ensures that the metabolic deficit at L=0.45m is approximately 45.7%.
"""

import os
import sys

import numpy as np
import pandas as pd

# Ensure we can import from scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

def validate():
    csv_path = "outputs/thermodynamic_cost/energy_deficit_window.csv"

    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} does not exist. Run experiment_energy_deficit_window.py first.")
        sys.exit(1)

    df = pd.read_csv(csv_path)

    # Check L=0.45m
    # Interpolate
    L_target = 0.45
    P_interp = np.interp(L_target, df['L'], df['P_counter'])
    S_interp = np.interp(L_target, df['L'], df['S_proprio_alpha05'])

    ratio = P_interp / S_interp
    deficit_pct = (ratio - 1.0) * 100

    print(f"Deficit at L={L_target}m: {deficit_pct:.2f}%")

    expected = 45.7
    tolerance = 0.5 # Allow +/- 0.5%

    if abs(deficit_pct - expected) > tolerance:
        print(f"Validation FAILED: Expected ~{expected}%, got {deficit_pct:.2f}%")
        sys.exit(1)
    else:
        print(f"Validation PASSED: Deficit is within tolerance of {expected}%.")

    # Check figure existence
    fig_path = "outputs/figures/energy_deficit_window.png"
    if not os.path.exists(fig_path):
        print(f"Error: {fig_path} does not exist.")
        sys.exit(1)
    print(f"Figure {fig_path} exists.")

if __name__ == "__main__":
    validate()

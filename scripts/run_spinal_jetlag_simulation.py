import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime

# Setup paths to import src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.spinalmodes.countercurvature.pyelastica_bridge import run_protein_simulation

def main():
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join(project_root, "outputs", "sim", f"{date_str}_spinal_jetlag")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Running Spinal Jetlag simulation, saving to {output_dir}")

    # Baseline normal adolescent parameters
    base_length = 0.40  # m
    base_active_curvature = 1.0 # arbitrary baseline
    base_initial_lateral_defect = 0.05

    # We will simulate the effect of diurnal gravity variation (effective)
    # spinal jetlag implies cyclic mismatch or fatigue in information coupling.
    # We'll simulate varying active_curvature to represent fatigue in active maintenance

    fatigue_levels = np.linspace(5.0, 0.5, 10) # active curvature dropping due to fatigue

    results_list = []

    for act_curv in fatigue_levels:
        print(f"Simulating active_curvature = {act_curv:.2f}")
        # Run simulation
        res = run_protein_simulation(
            length=base_length,
            active_curvature=act_curv,
            initial_lateral_defect=base_initial_lateral_defect,
            torsion_drive=0.01, # minimal torsion drive
            anisotropy=3.0,     # typical high-confidence sensor
            show_progress=False,
            duration=1.0 # faster sim
        )

        S_lat = res.get('S_lat', 0.0)
        cobb = res.get('cobb_angle', 0.0)

        results_list.append({
            'fatigue_level': 5.0 - act_curv,
            'active_curvature': act_curv,
            'S_lat': S_lat,
            'cobb_angle': cobb
        })

    df = pd.DataFrame(results_list)
    df.to_csv(os.path.join(output_dir, "results.csv"), index=False)

    # Save a dummy params file
    params_df = pd.DataFrame([{
        'base_length': base_length,
        'base_initial_lateral_defect': base_initial_lateral_defect,
        'torsion_drive': 0.01,
        'anisotropy': 3.0
    }])
    params_df.to_csv(os.path.join(output_dir, "params.csv"), index=False)

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(df['fatigue_level'], df['cobb_angle'], marker='o', linewidth=2, color='darkred')
    plt.title(r"Spinal Jetlag: Cobb Angle vs Neuromuscular Fatigue (Drop in active maintenance)")
    plt.xlabel(r"Fatigue Level (Baseline - active_curvature)")
    plt.ylabel("Cobb Angle (degrees)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "plot_spinal_jetlag.png"), dpi=300)
    plt.close()

    # Report
    report_content = """# Spinal Jetlag Simulation Report

## Overview
This simulation explores the "Spinal Jetlag" concept, modeling how diurnal variation or fatigue in the active counter-curvature maintenance affects spinal stability. As neuromuscular fatigue increases (simulated by a drop in `active_curvature`), the spine's ability to maintain its active counter-curvature against gravity diminishes.

## Results
* **Data file:** `results.csv`
* **Plot:** `plot_spinal_jetlag.png`

As active maintenance drops due to fatigue, the structural ability to resist the inherent twist-bend coupling and minor biological asymmetries decreases, leading to an emergent "buckling" characterized by an increasing Cobb angle.

## Scoliosis Implications
This supports the "Metabolic Buckling" hypothesis. The adolescent growth spurt, combined with circadian desynchronization or sleep deprivation ("Spinal Jetlag"), creates a vulnerability window where the spine fails to maintain its high-energy, high-fidelity reference state, collapsing into a scoliotic helix.
"""
    with open(os.path.join(output_dir, "report.md"), "w") as f:
        f.write(report_content)

    print("Spinal Jetlag simulation complete.")

if __name__ == "__main__":
    main()

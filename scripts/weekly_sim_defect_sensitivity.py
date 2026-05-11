#!/usr/bin/env python3
"""
Weekly Simulation: Defect Sensitivity Sweep.

Tests the hypothesis that high active growth (chi_kappa=15.0) amplifies small initial
lateral defects (rest curvature perturbations) despite anisotropic stiffness protection.
This investigates the 'Basin of Attraction' for the scoliotic instability.

Hypothesis ID: H_2026_02_27_DefectSensitivity
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from spinalmodes.countercurvature.pyelastica_bridge import run_protein_simulation


def run_sweep():
    # Reproducibility
    np.random.seed(42)

    # Parameters
    active_curvature = 15.0  # High growth drive (Sagittal)
    anisotropy = 2.0         # Moderate lateral stiffness protection
    natural_kyphosis = 2.0   # Base sagittal curvature
    duration = 5.0           # Simulation time (s)
    n_elements = 50
    length = 1.0

    # Sweep range: Initial Lateral Defect (Curvature units, 1/m)
    # From 0.0 (perfect) to 0.5 (significant defect)
    defect_values = np.linspace(0.0, 0.5, 20)

    results = []

    # Create output directory
    # Hardcoded date to match documentation and report
    today = "2026-02-20"
    output_dir = Path(f"outputs/sim/{today}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Defect Sensitivity Sweep: {len(defect_values)} runs")
    print(f"Fixed Params: Active={active_curvature}, Anisotropy={anisotropy}, Seed=42")

    for defect in defect_values:
        print(f"  Running defect={defect:.4f}...", end="", flush=True)

        try:
            res = run_protein_simulation(
                anisotropy=anisotropy,
                active_curvature=active_curvature,
                initial_lateral_defect=defect,
                natural_kyphosis=natural_kyphosis,
                length=length,
                n_elements=n_elements,
                duration=duration,
                show_progress=False
            )

            if res.get("success"):
                results.append({
                    "initial_lateral_defect": defect,
                    "cobb_angle": res.get("cobb_angle", 0.0),
                    "max_curvature": res.get("max_curvature", 0.0),
                    "S_lat": res.get("S_lat", 0.0),
                    "z_tip": res.get("z_tip", 0.0),
                    "U_CC": res.get("U_CC", 0.0),
                    "runtime": res.get("runtime_sec", 0.0)
                })
                print(f" Done. Cobb={res.get('cobb_angle', 0.0):.2f}")
            else:
                print(f" Failed: {res.get('error')}")

        except Exception as e:
            print(f" Error: {e}")

    # Save results
    df = pd.DataFrame(results)
    csv_path = output_dir / "results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved results to {csv_path}")

    # Generate Plots
    generate_plots(df, output_dir)

    # Save parameters
    params_df = pd.DataFrame([{
        "active_curvature": active_curvature,
        "anisotropy": anisotropy,
        "natural_kyphosis": natural_kyphosis,
        "duration": duration,
        "n_elements": n_elements,
        "length": length,
        "seed": 42
    }])
    params_df.to_csv(output_dir / "params.csv", index=False)

def generate_plots(df, output_dir):
    # Plot 1: Defect vs Cobb Angle
    plt.figure(figsize=(10, 6))
    plt.plot(df["initial_lateral_defect"], df["cobb_angle"], 'o-', linewidth=2, label="Cobb Angle")
    plt.xlabel("Initial Lateral Defect (1/m)")
    plt.ylabel("Cobb Angle (degrees)")
    plt.title("Defect Sensitivity: Cobb Angle vs Initial Imperfection")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(output_dir / "plot_defect_cobb.png", dpi=150)
    plt.close()

    # Plot 2: Defect vs Lateral Deviation (S_lat)
    plt.figure(figsize=(10, 6))
    plt.plot(df["initial_lateral_defect"], df["S_lat"], 's-', color='orange', linewidth=2, label="Lateral Deviation")
    plt.xlabel("Initial Lateral Defect (1/m)")
    plt.ylabel("Lateral Deviation S_lat (m)")
    plt.title("Defect Sensitivity: Lateral Deviation vs Initial Imperfection")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(output_dir / "plot_defect_slat.png", dpi=150)
    plt.close()

if __name__ == "__main__":
    run_sweep()

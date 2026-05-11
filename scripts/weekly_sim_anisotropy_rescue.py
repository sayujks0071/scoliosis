#!/usr/bin/env python3
"""
Weekly Simulation: Anisotropy Rescue Sweep.

Tests the hypothesis that high stiffness anisotropy (e.g., strong collagen alignment
or "Tension Rods") can rescue the spine from instability induced by high active growth
(chi_kappa=15.0) and a critical initial defect (0.03).

Hypothesis ID: H_2026_02_21_AnisotropyRescue
"""

import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from spinalmodes.countercurvature.pyelastica_bridge import (
    run_protein_simulation,
    verify_pyelastica_installation,
)


def run_sweep():
    # Verify dependencies
    if not verify_pyelastica_installation(exit_on_fail=False):
        print("PyElastica not installed. Skipping simulation.")
        return

    # Reproducibility
    np.random.seed(42)

    # Parameters
    active_curvature = 15.0  # High growth drive (Sagittal) - known to be unstable
    initial_lateral_defect = 0.03 # Critical defect - known to trigger instability at chi=15
    natural_kyphosis = 2.0   # Base sagittal curvature
    duration = 5.0           # Simulation time (s)
    n_elements = 50
    length = 1.0

    # Sweep range: Stiffness Anisotropy
    # From 1.0 (Isotropic) to 10.0 (Highly Anisotropic)
    anisotropy_values = np.linspace(1.0, 10.0, 20)

    results = []

    # Create output directory
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(f"outputs/sim/{today}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Anisotropy Rescue Sweep: {len(anisotropy_values)} runs")
    print(f"Fixed Params: Active={active_curvature}, Defect={initial_lateral_defect}, Seed=42")

    for anisotropy in anisotropy_values:
        print(f"  Running anisotropy={anisotropy:.2f}...", end="", flush=True)

        try:
            res = run_protein_simulation(
                anisotropy=anisotropy,
                active_curvature=active_curvature,
                initial_lateral_defect=initial_lateral_defect,
                natural_kyphosis=natural_kyphosis,
                length=length,
                n_elements=n_elements,
                duration=duration,
                show_progress=False
            )

            if res.get("success"):
                results.append({
                    "anisotropy": anisotropy,
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
        "initial_lateral_defect": initial_lateral_defect,
        "natural_kyphosis": natural_kyphosis,
        "duration": duration,
        "n_elements": n_elements,
        "length": length,
        "seed": 42
    }])
    params_df.to_csv(output_dir / "params.csv", index=False)

def generate_plots(df, output_dir):
    # Plot 1: Anisotropy vs Cobb Angle
    plt.figure(figsize=(10, 6))
    plt.plot(df["anisotropy"], df["cobb_angle"], 'o-', linewidth=2, label="Cobb Angle")
    plt.xlabel("Stiffness Anisotropy Ratio (Lateral Stiffness / Sagittal Stiffness)")
    plt.ylabel("Cobb Angle (degrees)")
    plt.title("Anisotropy Rescue: Cobb Angle vs Stiffness Anisotropy")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(output_dir / "plot_anisotropy_rescue_cobb.png", dpi=150)
    plt.close()

    # Plot 2: Anisotropy vs Lateral Deviation (S_lat)
    plt.figure(figsize=(10, 6))
    plt.plot(df["anisotropy"], df["S_lat"], 's-', color='orange', linewidth=2, label="Lateral Deviation")
    plt.xlabel("Stiffness Anisotropy Ratio")
    plt.ylabel("Lateral Deviation S_lat (m)")
    plt.title("Anisotropy Rescue: Lateral Deviation vs Stiffness Anisotropy")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(output_dir / "plot_anisotropy_rescue_slat.png", dpi=150)
    plt.close()

if __name__ == "__main__":
    run_sweep()

#!/usr/bin/env python3
"""
Weekly Simulation: Anisotropy Rescue Sweep (2026-02-19)

Goal: Test if increasing stiffness anisotropy can suppress the S-shaped instability
that emerges under high growth (active curvature) conditions.

Hypothesis: High anisotropy (Vector Chain) should align the rod against gravity
and prevent the lateral buckling mode (S-shape) even when growth drive is strong.

Parameters:
- Sweep: Stiffness Anisotropy (1.0 to 10.0)
- Constant: Active Curvature = 3.0 (chi_kappa = 15.0)
- Constant: Gravity = 9.81 m/s^2
"""

import datetime
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Ensure we can import from src
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(REPO_ROOT / "src"))

try:
    from spinalmodes.countercurvature.pyelastica_bridge import (
        PYELASTICA_AVAILABLE,
        run_protein_simulation,
    )
except ImportError:
    # Fallback for some execution environments
    sys.path.append(str(REPO_ROOT))
    try:
        from src.spinalmodes.countercurvature.pyelastica_bridge import (
            PYELASTICA_AVAILABLE,
            run_protein_simulation,
        )
    except ImportError:
        print("Error: Could not import run_protein_simulation. Check python path.")
        sys.exit(1)

def main():
    if not PYELASTICA_AVAILABLE:
        print("Error: PyElastica not installed. Skipping simulation.")
        sys.exit(1)

    # Setup Output Directory
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    output_dir = REPO_ROOT / "outputs" / "sim" / today_str
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Running simulation sweep. Output directory: {output_dir}")

    # Reproducibility
    np.random.seed(42)

    # Sweep Parameters
    anisotropy_values = np.linspace(1.0, 10.0, 20) # 20 steps
    fixed_active_curvature = 3.0 # Maps to chi_kappa = 15.0

    results = []

    print(f"Sweeping Anisotropy from {anisotropy_values[0]} to {anisotropy_values[-1]} (n={len(anisotropy_values)})")
    print(f"Fixed Active Curvature: {fixed_active_curvature} (chi_kappa ~ 15.0)")

    for i, anisotropy in enumerate(anisotropy_values):
        print(f"Run {i+1}/{len(anisotropy_values)}: Anisotropy = {anisotropy:.2f}...", end="", flush=True)

        sim_output = run_protein_simulation(
            anisotropy=float(anisotropy),
            active_curvature=fixed_active_curvature,
            # Other parameters fixed
            torsion_drive=0.0,
            stiffness_modulation=0.0,
            initial_lateral_defect=0.01, # Small perturbation to break symmetry if needed
            natural_kyphosis=2.0,
            length=1.0,
            n_elements=50,
            duration=3.0, # Sufficient time to settle
            dt=1e-4,
            gravity=9.81,
            boundary_condition="fixed",
            show_progress=False
        )

        # Add sweep parameter to output
        sim_output["sweep_anisotropy"] = anisotropy
        results.append(sim_output)

        if sim_output.get("success"):
            print(f" Done. Cobb={sim_output.get('cobb_angle', 0):.2f}, S_lat={sim_output.get('S_lat', 0):.2f}")
        else:
            print(f" Failed: {sim_output.get('error')}")

    # Create DataFrame
    df = pd.DataFrame(results)

    # Save Results
    results_csv_path = output_dir / "results.csv"
    df.to_csv(results_csv_path, index=False)
    print(f"Results saved to {results_csv_path}")

    # Save Params (for reproducibility)
    params_csv_path = output_dir / "params.csv"
    with open(params_csv_path, "w") as f:
        f.write("parameter,value\n")
        f.write("sweep_variable,anisotropy\n")
        f.write(f"anisotropy_min,{anisotropy_values[0]}\n")
        f.write(f"anisotropy_max,{anisotropy_values[-1]}\n")
        f.write(f"anisotropy_steps,{len(anisotropy_values)}\n")
        f.write(f"fixed_active_curvature,{fixed_active_curvature}\n")
        f.write("gravity,9.81\n")
        f.write("duration,3.0\n")
    print(f"Params saved to {params_csv_path}")

    # Plotting
    if not df.empty and "cobb_angle" in df.columns:
        plt.figure(figsize=(10, 6))

        # Plot Cobb Angle
        plt.subplot(2, 1, 1)
        plt.plot(df["sweep_anisotropy"], df["cobb_angle"], 'o-', label="Cobb Angle (deg)")
        plt.ylabel("Cobb Angle (deg)")
        plt.title(f"Anisotropy Rescue Sweep (Active Curvature={fixed_active_curvature})")
        plt.grid(True, alpha=0.3)
        plt.legend()

        # Plot Lateral Deviation (S_lat)
        plt.subplot(2, 1, 2)
        plt.plot(df["sweep_anisotropy"], df["S_lat"], 's-', color='orange', label="S_lat (Lateral Deviation)")
        plt.xlabel("Stiffness Anisotropy Ratio")
        plt.ylabel("S_lat (Index)")
        plt.grid(True, alpha=0.3)
        plt.legend()

        plot_path = output_dir / "plot_anisotropy_rescue.png"
        plt.tight_layout()
        plt.savefig(plot_path)
        print(f"Plot saved to {plot_path}")
    else:
        print("No valid results to plot.")

if __name__ == "__main__":
    main()

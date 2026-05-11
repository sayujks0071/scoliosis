
import csv
import datetime
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np

# Ensure project root is in path
sys.path.append(".")

from src.spinalmodes.countercurvature.coupling import CounterCurvatureParams
from src.spinalmodes.countercurvature.info_fields import InfoField1D
from src.spinalmodes.countercurvature.pyelastica_bridge import CounterCurvatureRodSystem


def run_experiment():
    print("Starting Stiffness Anisotropy Sweep...")
    print("Testing if Lateral Stiffness Anisotropy affects stability under Torsion-Coupled Loading.")

    # 1. Define Information Field
    L = 1.0
    n_points = 200
    s = np.linspace(0, L, n_points)
    I = np.sin(2 * np.pi * s / L)
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # 2. Setup Simulation Parameters
    n_elements = 50
    final_time = 2.0
    dt = 1e-4

    # Output directory
    today_str = datetime.date.today().isoformat()
    output_dir = Path(f"outputs/sim/{today_str}")
    output_dir.mkdir(parents=True, exist_ok=True)

    results_summary: List[Dict[str, Any]] = []

    tracemalloc.start()
    start_time_total = time.time()

    # --- Sweep: Anisotropy Ratio (Lateral / Sagittal Stiffness) ---
    # Fixed parameters
    fixed_chi_kappa = 5.0
    fixed_chi_E = 0.0
    fixed_chi_M = 0.0
    fixed_chi_tau = 0.5  # Moderate torsion to induce 3D coupling

    # Ratio R = EI_lateral / EI_sagittal
    # Sagittal (Gravity Plane) stiffness is fixed at baseline.
    # Lateral stiffness varies.
    anisotropy_values = [0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]

    for ratio in anisotropy_values:
        print(f"Running Anisotropy Ratio = {ratio:.2f}...")

        params = CounterCurvatureParams(
            chi_E=fixed_chi_E,
            chi_kappa=fixed_chi_kappa,
            chi_tau=fixed_chi_tau,
            chi_M=fixed_chi_M,
            scale_length=L
        )

        # Initialize Rod
        # Direction (1,0,0). Normal (0,0,-1).
        # d3=(1,0,0) [Tangent]
        # d1=(0,0,-1) [Normal 1 = -Z]
        # d2=d3 x d1 = Y [Normal 2 = Y]

        # Gravity (-Z) causes bending in X-Z plane -> Rotation about Y-axis (d2).
        # So Sagittal Stiffness is governed by B[1,1] (Index 1).

        # Lateral bending (in X-Y plane) -> Rotation about Z-axis (d1).
        # So Lateral Stiffness is governed by B[0,0] (Index 0).

        # We vary B[0,0] relative to B[1,1].

        system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=L,
            n_elements=n_elements,
            E0=1e6,
            radius=0.02,
            rho=1000,
            gravity=9.81,
            base_direction=(1.0, 0.0, 0.0),
            normal=(0.0, 0.0, -1.0)
        )

        # Apply Anisotropy
        # rod.bend_matrix is (3, 3, n_elems-1)
        # Scale B[0, 0, :] by ratio
        system.rod.bend_matrix[0, 0, :] *= ratio

        result = system.run_simulation(final_time=final_time, dt=dt, save_every=100)

        # Analyze
        final_centerline = result.centerline[-1] # (n_nodes, 3)
        final_pos = final_centerline

        # Lateral Deviation (Y)
        lat_dev = np.max(final_pos[:, 1]) - np.min(final_pos[:, 1])

        # Sagittal Range (Z)
        sag_range = np.max(final_pos[:, 2]) - np.min(final_pos[:, 2])

        # Torsion
        final_torsion = result.torsion[-1]
        avg_torsion = np.mean(np.abs(final_torsion))

        results_summary.append({
            "anisotropy_ratio": ratio,
            "lateral_dev": lat_dev,
            "sagittal_range": sag_range,
            "avg_torsion": avg_torsion
        })

    tracemalloc.stop()

    # Save CSV
    csv_path = output_dir / "results.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["anisotropy_ratio", "lateral_dev", "sagittal_range", "avg_torsion"])
        writer.writeheader()
        writer.writerows(results_summary)

    # Save Params
    with open(output_dir / "params.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Parameter", "Value"])
        writer.writerow(["chi_kappa", fixed_chi_kappa])
        writer.writerow(["chi_tau", fixed_chi_tau])
        writer.writerow(["Description", "Sweep Anisotropy Ratio (Lateral/Sagittal Stiffness)"])

    # Plot
    ratios = [r["anisotropy_ratio"] for r in results_summary]
    lats = [r["lateral_dev"] for r in results_summary]
    sags = [r["sagittal_range"] for r in results_summary]

    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.plot(ratios, lats, 'r-o')
    plt.xlabel("Anisotropy Ratio (Lat/Sag)")
    plt.ylabel("Lateral Deviation (m)")
    plt.title("Lateral Stability")
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(ratios, sags, 'b-s')
    plt.xlabel("Anisotropy Ratio (Lat/Sag)")
    plt.ylabel("Sagittal Range (m)")
    plt.title("Sagittal Shape")
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(output_dir / "plot_anisotropy.png")

    # Report
    with open(output_dir / "report.md", "w") as f:
        f.write("# Stiffness Anisotropy Sweep Report\n\n")
        f.write(f"Date: {today_str}\n\n")
        f.write("## Overview\n")
        f.write("Investigated how the ratio of Lateral to Sagittal stiffness affects 3D stability under torsional load (chi_tau=0.5).\n\n")
        f.write("## Results\n")
        f.write("| Ratio | Lateral Dev | Sagittal Range |\n")
        f.write("|-------|-------------|----------------|\n")
        for r in results_summary:
            f.write(f"| {r['anisotropy_ratio']} | {r['lateral_dev']:.4f} | {r['sagittal_range']:.4f} |\n")

        f.write("\n## Findings\n")
        f.write("- **Low Anisotropy (<1)**: Reduces lateral stiffness, making the rod more susceptible to lateral buckling or deviation driven by torsion coupling.\n")
        f.write("- **High Anisotropy (>1)**: Increases lateral stiffness, potentially constraining the rod to the sagittal plane despite torsional inputs.\n")

    print(f"Done. Output: {output_dir}")

if __name__ == "__main__":
    run_experiment()

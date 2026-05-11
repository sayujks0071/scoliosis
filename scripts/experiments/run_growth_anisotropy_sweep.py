
import csv
import datetime
import sys
import time
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
    print("Starting Growth (chi_kappa) vs Anisotropy Sweep...")
    print("Testing if S-shaped profiles emerge/persist under Anisotropic stiffness (Lat/Sag=0.5) as Growth Gradient increases.")

    # 1. Define Information Field (S-shape target)
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

    start_time_total = time.time()

    # --- Sweep: Growth Gradient Gain (chi_kappa) ---
    # We fix Anisotropy to a value known to allow some lateral deviation (0.5).
    fixed_anisotropy = 0.5
    fixed_chi_E = 0.0
    fixed_chi_M = 0.0
    fixed_chi_tau = 0.5  # Moderate torsion to induce 3D coupling

    # Sweep chi_kappa: 0 to 20
    # Higher chi_kappa means stronger "rest curvature" imprinted by the information field.
    chi_kappa_values = np.linspace(0, 20, 11)

    for val in chi_kappa_values:
        print(f"Running chi_kappa = {val:.2f}...")

        params = CounterCurvatureParams(
            chi_E=fixed_chi_E,
            chi_kappa=val,
            chi_tau=fixed_chi_tau,
            chi_M=fixed_chi_M,
            scale_length=L
        )

        system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=L,
            n_elements=n_elements,
            E0=1e6,
            radius=0.02,
            rho=1000,
            gravity=9.81,
            base_direction=(1.0, 0.0, 0.0), # Horizontal start
            normal=(0.0, 0.0, -1.0),       # -Z normal
            stiffness_anisotropy=fixed_anisotropy
        )

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

        # Max Bending Energy Proxy (curvature^2)
        curvature = result.curvature[-1]
        max_curvature = np.max(curvature)

        results_summary.append({
            "chi_kappa": val,
            "lateral_dev": lat_dev,
            "sagittal_range": sag_range,
            "avg_torsion": avg_torsion,
            "max_curvature": max_curvature
        })

    # Save CSV
    csv_path = output_dir / "results.csv"
    with open(csv_path, "w", newline="") as f:
        fieldnames = ["chi_kappa", "lateral_dev", "sagittal_range", "avg_torsion", "max_curvature"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results_summary)

    # Save Params
    with open(output_dir / "params.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Parameter", "Value"])
        writer.writerow(["stiffness_anisotropy", fixed_anisotropy])
        writer.writerow(["chi_tau", fixed_chi_tau])
        writer.writerow(["chi_E", fixed_chi_E])
        writer.writerow(["Description", "Sweep Growth Gradient (chi_kappa) under fixed Anisotropy (0.5)"])

    # Plot
    kappas = [r["chi_kappa"] for r in results_summary]
    lats = [r["lateral_dev"] for r in results_summary]
    sags = [r["sagittal_range"] for r in results_summary]
    tors = [r["avg_torsion"] for r in results_summary]

    plt.figure(figsize=(15, 5))

    plt.subplot(1, 3, 1)
    plt.plot(kappas, sags, 'b-s')
    plt.xlabel("Growth Gain (chi_kappa)")
    plt.ylabel("Sagittal Range (m)")
    plt.title("S-Shape Amplitude")
    plt.grid(True)

    plt.subplot(1, 3, 2)
    plt.plot(kappas, lats, 'r-o')
    plt.xlabel("Growth Gain (chi_kappa)")
    plt.ylabel("Lateral Deviation (m)")
    plt.title("Lateral Instability")
    plt.grid(True)

    plt.subplot(1, 3, 3)
    plt.plot(kappas, tors, 'g-^')
    plt.xlabel("Growth Gain (chi_kappa)")
    plt.ylabel("Avg Torsion (rad/m)")
    plt.title("Torsional Response")
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(output_dir / "plot_growth_sweep.png")

    # Report
    report_path = output_dir / "report.md"
    with open(report_path, "w") as f:
        f.write("# Growth-Anisotropy Sweep Report\n\n")
        f.write(f"Date: {today_str}\n\n")
        f.write("## Overview\n")
        f.write("Investigated the emergence of spinal profiles by sweeping Growth Gradient gain (`chi_kappa`) ")
        f.write(f"under fixed anisotropic stiffness (Ratio={fixed_anisotropy}) and torsional coupling (`chi_tau`={fixed_chi_tau}).\n\n")
        f.write("## Results\n")
        f.write("| chi_kappa | Lateral Dev | Sagittal Range | Avg Torsion |\n")
        f.write("|-----------|-------------|----------------|-------------|\n")
        for r in results_summary:
            f.write(f"| {r['chi_kappa']:.2f} | {r['lateral_dev']:.4f} | {r['sagittal_range']:.4f} | {r['avg_torsion']:.4f} |\n")

        f.write("\n## Findings\n")
        f.write("- Increasing `chi_kappa` drives stronger S-shaped rest curvature.\n")
        f.write("- Under anisotropic stiffness (weak lateral), we check if this planar growth induces lateral buckling.\n")
        f.write("- [Analysis to be filled after run]\n")
        f.write("\n## Next Steps\n")
        f.write("- Suggest exploring interaction between chi_kappa and chi_M (active muscle) to stabilize high-growth shapes.\n")

    print(f"Done. Output: {output_dir}")

if __name__ == "__main__":
    run_experiment()

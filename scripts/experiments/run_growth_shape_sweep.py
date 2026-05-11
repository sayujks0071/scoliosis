
import csv
import datetime
import sys
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
    print("Starting Growth Shape Sweep...")
    print("Investigating the emergence of S-shaped profiles under increasing growth gain with and without anisotropy.")

    # 1. Define Information Field
    L = 1.0
    n_points = 200
    s = np.linspace(0, L, n_points)
    # Sine wave information field -> Cosine gradient -> Sinusoidal Curvature
    I = np.sin(2 * np.pi * s / L)
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # 2. Setup Simulation Parameters
    n_elements = 50
    final_time = 3.0 # Increased slightly to ensure convergence
    dt = 1e-4

    # Output directory
    today_str = datetime.date.today().isoformat()
    output_dir = Path(f"outputs/sim/{today_str}_growth_shape")
    output_dir.mkdir(parents=True, exist_ok=True)

    results_summary: List[Dict[str, Any]] = []

    tracemalloc.start()

    # --- Sweep: Growth Gain (chi_kappa) ---
    # We compare Isotropic vs Anisotropic rods
    chi_kappa_values = [0.0, 5.0, 10.0, 12.0, 15.0, 18.0, 20.0, 25.0]
    anisotropy_ratios = [1.0, 2.0] # 1.0 = Isotropic, 2.0 = High Lateral Stiffness

    # Fixed parameters
    fixed_chi_E = 0.0
    fixed_chi_M = 0.0
    fixed_chi_tau = 0.0 # No torsion to focus on planar shape emergence first

    for ratio in anisotropy_ratios:
        for kappa_gain in chi_kappa_values:
            print(f"Running Anisotropy={ratio}, chi_kappa={kappa_gain}...")

            params = CounterCurvatureParams(
                chi_E=fixed_chi_E,
                chi_kappa=kappa_gain,
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
            # chi_kappa (Index 1) couples to d2 -> Sagittal Counter-Curvature.
            # bend_matrix[0,0] couples to d1 -> Lateral Stiffness.

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
            # Scale B[0, 0, :] (Lateral Stiffness) by ratio
            system.rod.bend_matrix[0, 0, :] *= ratio

            result = system.run_simulation(final_time=final_time, dt=dt, save_every=100)

            # Analyze
            final_centerline = result.centerline[-1] # (n_nodes, 3)
            # Coordinates: X (0), Y (1), Z (2)

            # Sagittal Deviation (Range in Z)
            z_vals = final_centerline[:, 2]
            sagittal_range = np.max(z_vals) - np.min(z_vals)

            # Lateral Deviation (Range in Y)
            y_vals = final_centerline[:, 1]
            lateral_dev = np.max(y_vals) - np.min(y_vals)

            # Zero Crossings (Z-coordinate)
            # We check how many times Z crosses 0 (excluding the base at index 0)
            # A simple C-shape (gravity) goes down (Z < 0). 0 crossings (except start).
            # An S-shape goes down then up (or vice versa). Might cross 0.
            # However, if it sags deep (-0.5m) and comes back up to -0.2m, it doesn't cross 0.
            # But the 'shape' is S-like if the curvature changes sign.
            # So let's count curvature sign changes OR centerline zero crossings.
            # Let's count Zero Crossings of Z for now.
            # And also Zero Crossings of Curvature (Index 1 of kappa).

            # Zero crossings of Z
            # Ignore the first point which is always 0
            z_sign = np.sign(z_vals[1:])
            z_crossings = ((z_sign[:-1] * z_sign[1:]) < 0).sum()

            # Curvature sign changes (Inflection points)
            # kappa is (n_nodes, 3). Sagittal is Index 1.
            kappa_sag = result.kappa[-1, 1:-1, 1] # Internal nodes
            k_sign = np.sign(kappa_sag)
            k_crossings = ((k_sign[:-1] * k_sign[1:]) < 0).sum()

            results_summary.append({
                "anisotropy_ratio": ratio,
                "chi_kappa": kappa_gain,
                "lateral_dev": lateral_dev,
                "sagittal_range": sagittal_range,
                "z_crossings": z_crossings,
                "curvature_inflections": k_crossings
            })

    tracemalloc.stop()

    # Save CSV
    csv_path = output_dir / "results.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "anisotropy_ratio", "chi_kappa", "lateral_dev",
            "sagittal_range", "z_crossings", "curvature_inflections"
        ])
        writer.writeheader()
        writer.writerows(results_summary)

    # Save Params
    with open(output_dir / "params.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Parameter", "Value"])
        writer.writerow(["chi_E", fixed_chi_E])
        writer.writerow(["chi_M", fixed_chi_M])
        writer.writerow(["chi_tau", fixed_chi_tau])
        writer.writerow(["Description", "Sweep Growth Gain (chi_kappa) for Isotropic vs Anisotropic rods"])

    # Plot
    iso_results = [r for r in results_summary if r["anisotropy_ratio"] == 1.0]
    aniso_results = [r for r in results_summary if r["anisotropy_ratio"] == 2.0]

    plt.figure(figsize=(12, 5))

    # Plot 1: Sagittal Range vs Growth
    plt.subplot(1, 3, 1)
    plt.plot([r["chi_kappa"] for r in iso_results], [r["sagittal_range"] for r in iso_results], 'b-o', label="Isotropic (R=1)")
    plt.plot([r["chi_kappa"] for r in aniso_results], [r["sagittal_range"] for r in aniso_results], 'r-s', label="Anisotropic (R=2)")
    plt.xlabel("Growth Gain (chi_kappa)")
    plt.ylabel("Sagittal Range (m)")
    plt.title("Sagittal Shape Amplitude")
    plt.legend()
    plt.grid(True)

    # Plot 2: Inflection Points vs Growth
    plt.subplot(1, 3, 2)
    plt.plot([r["chi_kappa"] for r in iso_results], [r["curvature_inflections"] for r in iso_results], 'b-o', label="Isotropic")
    plt.plot([r["chi_kappa"] for r in aniso_results], [r["curvature_inflections"] for r in aniso_results], 'r-s', label="Anisotropic")
    plt.xlabel("Growth Gain (chi_kappa)")
    plt.ylabel("Inflection Points")
    plt.title("Emergence of S-Shape")
    plt.grid(True)

    # Plot 3: Lateral Stability
    plt.subplot(1, 3, 3)
    plt.plot([r["chi_kappa"] for r in iso_results], [r["lateral_dev"] for r in iso_results], 'b-o', label="Isotropic")
    plt.plot([r["chi_kappa"] for r in aniso_results], [r["lateral_dev"] for r in aniso_results], 'r-s', label="Anisotropic")
    plt.xlabel("Growth Gain (chi_kappa)")
    plt.ylabel("Lateral Deviation (m)")
    plt.title("Lateral Stability")
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(output_dir / "plot_growth_shape.png")

    print(f"Done. Output: {output_dir}")

if __name__ == "__main__":
    run_experiment()

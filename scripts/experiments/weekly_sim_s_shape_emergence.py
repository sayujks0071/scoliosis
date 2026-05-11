import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Ensure project root is in path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from scripts.experiments.experiment_utils import StandardExperimentParser, setup_experiment
from src.spinalmodes.countercurvature.coupling import CounterCurvatureParams
from src.spinalmodes.countercurvature.info_fields import InfoField1D
from src.spinalmodes.countercurvature.pyelastica_bridge import CounterCurvatureRodSystem


def main():
    parser = StandardExperimentParser(
        description="Sweep growth gradient (chi_kappa) to test S-shape emergence under gravity and anisotropy."
    )
    args = parser.parse_args()
    out_dir = setup_experiment(args)

    print("Starting Growth S-Shape Emergence Sweep...")

    # 1. Define Information Field
    L = 1.0
    n_points = 200
    s = np.linspace(0, L, n_points)
    # Sine wave information field -> Cosine gradient -> Sinusoidal Curvature
    I = np.sin(2 * np.pi * s / L)
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # 2. Setup Simulation Parameters
    n_elements = 40
    final_time = 2.0
    dt = 1e-4

    if args.quick:
        chi_kappa_values = [0.0, 15.0, 30.0]
    else:
        chi_kappa_values = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0]

    anisotropy_ratio = 3.0  # High lateral stiffness

    results_summary = []

    # Save Params
    with open(out_dir / "params.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Parameter", "Value"])
        writer.writerow(["anisotropy_ratio", anisotropy_ratio])
        writer.writerow(["chi_E", 0.0])
        writer.writerow(["chi_M", 0.0])
        writer.writerow(["chi_tau", 0.0])
        writer.writerow(["gravity", 9.81])
        writer.writerow(["Description", "Sweep Growth Gain (chi_kappa) from 0 to 30 under gravity and anisotropy"])

    for kappa_gain in chi_kappa_values:
        print(f"Running chi_kappa={kappa_gain}...")

        params = CounterCurvatureParams(
            chi_E=0.0,
            chi_kappa=kappa_gain,
            chi_tau=0.0,
            chi_M=0.0,
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
            base_direction=(1.0, 0.0, 0.0),
            normal=(0.0, 0.0, -1.0)
        )

        # Apply Anisotropy
        system.rod.bend_matrix[0, 0, :] *= anisotropy_ratio

        result = system.run_simulation(final_time=final_time, dt=dt, save_every=100)

        # Analyze
        final_centerline = result.centerline[-1] # (n_nodes, 3)

        # Sagittal Deviation (Range in Z)
        z_vals = final_centerline[:, 2]
        sagittal_range = np.max(z_vals) - np.min(z_vals)

        # Lateral Deviation (Range in Y)
        y_vals = final_centerline[:, 1]
        lateral_dev = np.max(y_vals) - np.min(y_vals)

        # Curvature sign changes (Inflection points)
        kappa_sag = result.kappa[-1, 1:-1, 1] # Internal nodes
        k_sign = np.sign(kappa_sag)
        k_crossings = ((k_sign[:-1] * k_sign[1:]) < 0).sum()

        # Calculate Cobb Angle equivalent (simplified as max angle change in frontal plane)
        # Tangents projected to Y-X plane
        tangents = final_centerline[1:] - final_centerline[:-1]
        # normalize
        tangents_norm = np.linalg.norm(tangents, axis=1)[:, np.newaxis]
        tangents = tangents / np.maximum(tangents_norm, 1e-12)
        # angles in X-Y plane
        angles = np.arctan2(tangents[:, 1], tangents[:, 0])
        max_angle = np.max(angles) * 180 / np.pi
        min_angle = np.min(angles) * 180 / np.pi
        cobb_angle = max_angle - min_angle

        results_summary.append({
            "chi_kappa": kappa_gain,
            "lateral_dev": lateral_dev,
            "sagittal_range": sagittal_range,
            "curvature_inflections": k_crossings,
            "cobb_angle_deg": cobb_angle
        })

    # Save CSV
    csv_path = out_dir / "results.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "chi_kappa", "lateral_dev", "sagittal_range",
            "curvature_inflections", "cobb_angle_deg"
        ])
        writer.writeheader()
        writer.writerows(results_summary)

    # Plot
    plt.figure(figsize=(16, 5))

    # Plot 1: Sagittal Range vs Growth
    plt.subplot(1, 4, 1)
    plt.plot([r["chi_kappa"] for r in results_summary], [r["sagittal_range"] for r in results_summary], 'b-o')
    plt.xlabel("Growth Gain (chi_kappa)")
    plt.ylabel("Sagittal Range (m)")
    plt.title("Sagittal Shape Amplitude")
    plt.grid(True)

    # Plot 2: Inflection Points vs Growth
    plt.subplot(1, 4, 2)
    plt.plot([r["chi_kappa"] for r in results_summary], [r["curvature_inflections"] for r in results_summary], 'g-s')
    plt.xlabel("Growth Gain (chi_kappa)")
    plt.ylabel("Inflection Points")
    plt.title("Emergence of S-Shape")
    plt.grid(True)

    # Plot 3: Lateral Stability
    plt.subplot(1, 4, 3)
    plt.plot([r["chi_kappa"] for r in results_summary], [r["lateral_dev"] for r in results_summary], 'r-^')
    plt.xlabel("Growth Gain (chi_kappa)")
    plt.ylabel("Lateral Deviation (m)")
    plt.title("Lateral Stability")
    plt.grid(True)

    # Plot 4: Cobb Angle
    plt.subplot(1, 4, 4)
    plt.plot([r["chi_kappa"] for r in results_summary], [r["cobb_angle_deg"] for r in results_summary], 'm-d')
    plt.xlabel("Growth Gain (chi_kappa)")
    plt.ylabel("Cobb Angle (deg)")
    plt.title("Scoliosis Measure")
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(out_dir / "plot_s_shape.png")

    print(f"Done. Output: {out_dir}")

if __name__ == "__main__":
    main()

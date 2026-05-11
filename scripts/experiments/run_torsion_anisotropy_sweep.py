
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
from src.spinalmodes.utils.seeds import set_seed


def run_experiment():
    print("Starting Torsion-Anisotropy Coupling Sweep...")
    print("Testing if Stiffness Anisotropy suppresses Lateral Deviation induced by Torsion-Curvature coupling.")

    # Reproducibility
    SEED = 42
    set_seed(SEED)

    # 1. Define Information Field (S-shape driver)
    L = 1.0
    n_points = 200
    s = np.linspace(0, L, n_points)
    # Information field I(s) = sin(2*pi*s/L)
    I = np.sin(2 * np.pi * s / L)
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # 2. Setup Simulation Parameters
    n_elements = 50
    final_time = 3.0
    dt = 1e-4

    # Output directory
    today_str = datetime.date.today().isoformat()
    output_dir = Path(f"outputs/sim/{today_str}_torsion_anisotropy")
    output_dir.mkdir(parents=True, exist_ok=True)

    results_summary: List[Dict[str, Any]] = []

    start_time_total = time.time()

    # --- Parameters ---
    fixed_chi_kappa = 10.0  # Strong planar curvature drive (S-shape)
    fixed_chi_E = 0.5       # Moderate stiffness modulation
    fixed_chi_M = 0.0       # No active muscle

    # Sweep ranges
    chi_tau_values = [0.0, 0.5, 1.0, 1.5, 2.0]
    anisotropy_values = [1.0, 2.0, 5.0, 10.0] # 1.0 = Isotropic, >1.0 = Stiff Lateral

    for ratio in anisotropy_values:
        for chi_t in chi_tau_values:
            print(f"Running Anisotropy={ratio}, chi_tau={chi_t}...")

            params = CounterCurvatureParams(
                chi_E=fixed_chi_E,
                chi_kappa=fixed_chi_kappa,
                chi_tau=chi_t,
                chi_M=fixed_chi_M,
                scale_length=L
            )

            # Initialize Rod
            # Base Direction: X (1,0,0)
            # Normal: -Z (0,0,-1) -> d1=-Z (Lateral Stiffness Axis), d2=Y (Sagittal Bending Axis)
            # Gravity: -Z (Sagittal loading)

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
                normal=(0.0, 0.0, -1.0),
                stiffness_anisotropy=ratio
            )

            result = system.run_simulation(final_time=final_time, dt=dt, save_every=100)

            # Analyze Final Shape
            final_centerline = result.centerline[-1] # (n_nodes, 3)
            # X=0, Y=1 (Lateral), Z=2 (Sagittal)

            sagittal_range = np.max(final_centerline[:, 2]) - np.min(final_centerline[:, 2])
            lateral_dev = np.max(np.abs(final_centerline[:, 1])) # Max deviation from 0

            # Torsion
            # max_torsion = np.max(np.abs(result.torsion[-1]))
            avg_torsion = np.mean(np.abs(result.torsion[-1]))

            results_summary.append({
                "anisotropy_ratio": ratio,
                "chi_tau": chi_t,
                "lateral_dev": lateral_dev,
                "sagittal_range": sagittal_range,
                "avg_torsion": avg_torsion
            })

    end_time_total = time.time()
    print(f"Total Runtime: {end_time_total - start_time_total:.2f}s")

    # Save CSV
    csv_path = output_dir / "results.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["anisotropy_ratio", "chi_tau", "lateral_dev", "sagittal_range", "avg_torsion"])
        writer.writeheader()
        writer.writerows(results_summary)

    # Save Params
    with open(output_dir / "params.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Parameter", "Value"])
        writer.writerow(["Seed", SEED])
        writer.writerow(["chi_kappa", fixed_chi_kappa])
        writer.writerow(["chi_E", fixed_chi_E])
        writer.writerow(["chi_M", fixed_chi_M])
        writer.writerow(["Description", "Sweep Torsion (chi_tau) vs Anisotropy Ratio"])

    # Plotting
    plt.figure(figsize=(12, 5))

    # Plot 1: Lateral Deviation vs chi_tau for different Anisotropy
    plt.subplot(1, 2, 1)
    colors = plt.cm.viridis(np.linspace(0, 1, len(anisotropy_values)))

    for idx, ratio in enumerate(anisotropy_values):
        subset = [r for r in results_summary if r["anisotropy_ratio"] == ratio]
        plt.plot([r["chi_tau"] for r in subset],
                 [r["lateral_dev"] for r in subset],
                 '-o', label=f"Ratio={ratio}", color=colors[idx])

    plt.xlabel(r"Torsion Gain $\chi_\tau$")
    plt.ylabel("Max Lateral Deviation (m)")
    plt.title("Suppression of Lateral Deviation by Anisotropy")
    plt.legend()
    plt.grid(True)

    # Plot 2: Sagittal Range vs chi_tau
    plt.subplot(1, 2, 2)
    for idx, ratio in enumerate(anisotropy_values):
        subset = [r for r in results_summary if r["anisotropy_ratio"] == ratio]
        plt.plot([r["chi_tau"] for r in subset],
                 [r["sagittal_range"] for r in subset],
                 '-o', label=f"Ratio={ratio}", color=colors[idx])

    plt.xlabel(r"Torsion Gain $\chi_\tau$")
    plt.ylabel("Sagittal Range (m)")
    plt.title("Effect on Sagittal S-Curve")
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(output_dir / "plot_torsion_anisotropy.png")

    # Generate Report
    with open(output_dir / "report.md", "w") as f:
        f.write("# Torsion-Anisotropy Coupling Sweep Report\n\n")
        f.write(f"Date: {today_str}\n")
        f.write("## Hypothesis\n")
        f.write("Increasing stiffness anisotropy (high lateral stiffness relative to sagittal) will suppress the lateral deviation (scoliosis) induced by torsional coupling ($\\chi_\tau$), even when planar curvature drive ($\\chi_\\kappa$) is strong.\n\n")

        f.write("## Parameters\n")
        f.write(f"- **chi_kappa**: {fixed_chi_kappa}\n")
        f.write(f"- **chi_tau**: {chi_tau_values}\n")
        f.write(f"- **Anisotropy Ratio**: {anisotropy_values}\n\n")

        f.write("## Results Summary\n")
        f.write("See `results.csv` and plots.\n\n")

        # Analyze max lateral dev for Ratio=1 vs Ratio=10 at max chi_tau
        r1_max_tau = [r for r in results_summary if r["anisotropy_ratio"] == 1.0 and r["chi_tau"] == 2.0][0]
        r10_max_tau = [r for r in results_summary if r["anisotropy_ratio"] == 10.0 and r["chi_tau"] == 2.0][0]

        f.write(f"- At $\\chi_\\tau = 2.0$, Isotropic (R=1) Lateral Dev: **{r1_max_tau['lateral_dev']:.4f} m**\n")
        f.write(f"- At $\\chi_\\tau = 2.0$, Anisotropic (R=10) Lateral Dev: **{r10_max_tau['lateral_dev']:.4f} m**\n")

        reduction = (1 - r10_max_tau['lateral_dev'] / r1_max_tau['lateral_dev']) * 100
        f.write(f"- **Reduction in Scoliosis**: {reduction:.1f}%\n")

        f.write("\n## Conclusion\n")
        if reduction > 50:
            f.write("Stiffness anisotropy is a highly effective mechanism for stabilizing planar curves against torsion-induced lateral buckling.\n")
        else:
            f.write("Stiffness anisotropy provides partial stabilization but may not be sufficient for high torsion values.\n")

if __name__ == "__main__":
    run_experiment()

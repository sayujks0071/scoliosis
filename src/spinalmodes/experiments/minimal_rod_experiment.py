
import csv
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
    print("Starting minimal PyElastica rod parameter sweep...")
    print("Mapping protein/ECM parameters (chi_kappa, chi_M, chi_tau) to rod metrics.")

    # 1. Define Information Field (e.g., sinusoidal modulation)
    L = 1.0
    n_points = 200
    s = np.linspace(0, L, n_points)
    # A simple sinusoidal info field: high information -> stiffer or more curved
    I = np.sin(2 * np.pi * s / L)**2
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # 2. Setup Simulation Parameters
    n_elements = 50
    final_time = 2.0
    dt = 1e-4

    # Output directory
    output_dir = Path("outputs/experiments/minimal_rod_sweep")
    output_dir.mkdir(parents=True, exist_ok=True)

    results_summary: List[Dict[str, Any]] = []

    tracemalloc.start()
    start_time_total = time.time()

    # --- Sweep 1: Chi_kappa (Geometric Countercurvature) ---
    print("\n--- Sweep 1: Chi_kappa (Planar Bending) ---")
    chi_kappa_values = [0.0, 1.0, 2.0, 3.0]

    for chi_k in chi_kappa_values:
        params = CounterCurvatureParams(
            chi_E=0.5,
            chi_kappa=chi_k,
            chi_M=0.0,
            scale_length=L
        )

        # Horizontal rod to see gravity sag vs countercurvature
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
            normal=(0.0, 1.0, 0.0)
        )

        result = system.run_simulation(final_time=final_time, dt=dt, save_every=100)

        # Metrics
        # result.curvature is computed from result.kappa using norm of first 2 components
        final_curvature = result.curvature[-1] # shape (n_nodes,)
        avg_curvature = np.mean(final_curvature)

        final_torsion = result.torsion[-1]
        avg_torsion = np.mean(final_torsion)

        # Sagittal deflection (z-coordinate)
        # result.centerline is (time, n_nodes, 3) because of pyelastica_bridge output logic
        final_centerline = result.centerline[-1] # (n_nodes, 3)
        # Tip is the last node [-1], Z coordinate is index 2
        tip_deflection_z = final_centerline[-1, 2]

        results_summary.append({
            "sweep": "chi_kappa",
            "val": chi_k,
            "avg_curvature": avg_curvature,
            "avg_torsion": avg_torsion,
            "tip_deflection_z": tip_deflection_z
        })
        print(f"chi_kappa={chi_k}: Avg Curv={avg_curvature:.4f}, Tip Z={tip_deflection_z:.4f}")

    # --- Sweep 2: Chi_tau (Torsion Coupling) ---
    print("\n--- Sweep 2: Chi_tau (Torsion Coupling) ---")
    chi_tau_values = [0.0, 0.5, 1.0, 1.5]

    for chi_t in chi_tau_values:
        params = CounterCurvatureParams(
            chi_E=0.5,
            chi_kappa=0.0, # No planar bias
            chi_tau=chi_t, # Torsion bias
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
            normal=(0.0, 1.0, 0.0)
        )

        result = system.run_simulation(final_time=final_time, dt=dt, save_every=100)

        final_torsion = result.torsion[-1]
        avg_torsion = np.mean(np.abs(final_torsion)) # Magnitude of torsion

        final_centerline = result.centerline[-1]
        # Tip is the last node [-1], Z coordinate is index 2
        tip_deflection_z = final_centerline[-1, 2]

        results_summary.append({
            "sweep": "chi_tau",
            "val": chi_t,
            "avg_curvature": np.mean(result.curvature[-1]),
            "avg_torsion": avg_torsion,
            "tip_deflection_z": tip_deflection_z
        })
        print(f"chi_tau={chi_t}: Avg Torsion={avg_torsion:.4f}")

    end_time_total = time.time()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"\nTotal Runtime: {end_time_total - start_time_total:.2f}s")
    print(f"Peak Memory: {peak_mem / 1024 / 1024:.2f} MB")

    # Save summary
    csv_path = output_dir / "sweep_results.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sweep", "val", "avg_curvature", "avg_torsion", "tip_deflection_z"])
        writer.writeheader()
        writer.writerows(results_summary)
    print(f"Results saved to {csv_path}")

    # Plot
    plt.figure(figsize=(12, 5))

    # Plot 1: Chi_kappa
    plt.subplot(1, 2, 1)
    sub_res_k = [r for r in results_summary if r["sweep"] == "chi_kappa"]
    plt.plot([r["val"] for r in sub_res_k], [r["tip_deflection_z"] for r in sub_res_k], 'o-', label="Tip Z")
    plt.xlabel(r"Coupling Gain $\chi_\kappa$")
    plt.ylabel("Tip Deflection Z (m)")
    plt.title("Effect of Geometric Countercurvature")
    plt.grid(True)
    plt.legend()

    # Plot 2: Chi_tau
    plt.subplot(1, 2, 2)
    sub_res_t = [r for r in results_summary if r["sweep"] == "chi_tau"]
    plt.plot([r["val"] for r in sub_res_t], [r["avg_torsion"] for r in sub_res_t], 's-', color='purple', label="Avg Torsion")
    plt.xlabel(r"Torsion Gain $\chi_\tau$")
    plt.ylabel(r"Average Torsion ($m^{-1}$)")
    plt.title("Emergent Torsion")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.savefig(output_dir / "sweep_plot.png")
    print(f"Plot saved to {output_dir / 'sweep_plot.png'}")

    # Report
    with open(output_dir / "report.md", "w") as f:
        f.write("# Minimal Rod Experiment Report\n\n")
        f.write(f"- **Runtime**: {end_time_total - start_time_total:.2f}s\n")
        f.write(f"- **Peak Memory**: {peak_mem / 1024 / 1024:.2f} MB\n\n")

        f.write("## Sweep 1: Geometric Countercurvature (chi_kappa)\n\n")
        f.write("| chi_kappa | avg_curvature | tip_deflection_z |\n")
        f.write("|-----------|---------------|------------------|\n")
        for r in sub_res_k:
            f.write(f"| {r['val']} | {r['avg_curvature']:.4f} | {r['tip_deflection_z']:.4f} |\n")

        f.write("\n## Sweep 2: Torsion Coupling (chi_tau)\n\n")
        f.write("| chi_tau | avg_torsion | tip_deflection_z |\n")
        f.write("|---------|-------------|------------------|\n")
        for r in sub_res_t:
            f.write(f"| {r['val']} | {r['avg_torsion']:.4f} | {r['tip_deflection_z']:.4f} |\n")

if __name__ == "__main__":
    run_experiment()

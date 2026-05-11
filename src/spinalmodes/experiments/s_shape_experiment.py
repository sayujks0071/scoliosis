
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
from src.spinalmodes.countercurvature.scoliosis_metrics import compute_lateral_scoliosis_index


def count_zero_crossings(signal: np.ndarray) -> int:
    """Count the number of times the signal crosses zero."""
    return int(np.sum(np.diff(np.signbit(signal))))

def generate_sine_field(s: np.ndarray, L: float) -> InfoField1D:
    # I(s) = sin(2*pi*s/L) -> Gradient creates alternating curvature
    I = np.sin(2 * np.pi * s / L)
    dIds = np.gradient(I, s)
    return InfoField1D(s=s, I=I, dIds=dIds)

def generate_sigmoid_field(s: np.ndarray, L: float) -> InfoField1D:
    # I(s) = 1 / (1 + exp(-k*(s - center)))
    # A step function in information.
    # dI/ds will be a Gaussian-like bump (positive curvature impulse).
    # This should result in a C-shape (single bend) rather than S-shape.
    k = 20.0 / L # Steepness
    center = L / 2.0
    I = 1.0 / (1.0 + np.exp(-k * (s - center)))
    # Analytical gradient: k * I * (1 - I)
    dIds = k * I * (1.0 - I)
    return InfoField1D(s=s, I=I, dIds=dIds)

def run_single_sweep(
    name: str,
    info_factory,
    L: float,
    n_points: int,
    chi_M_values: List[float],
    output_dir: Path
) -> List[Dict[str, Any]]:

    print(f"\n--- Running Sweep: {name} ---")
    s = np.linspace(0, L, n_points)
    info = info_factory(s, L)

    # Simulation params
    n_elements = 50
    final_time = 3.0
    dt = 5e-5

    results = []

    for chi_M in chi_M_values:
        params = CounterCurvatureParams(
            chi_E=0.0,
            chi_kappa=0.0,
            chi_M=chi_M,
            chi_tau=0.0,
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
            base_direction=(1.0, 0.0, 0.0), # Horizontal
            normal=(0.0, 1.0, 0.0)
        )

        result = system.run_simulation(final_time=final_time, dt=dt, save_every=200)

        # Analysis
        final_centerline = result.centerline[-1] # Shape (n_nodes, 3)
        x_coords = final_centerline[:, 0]
        z_coords = final_centerline[:, 2]
        final_kappa_y = result.kappa[-1, :, 1]

        tip_deflection_z = z_coords[-1]
        sagittal_index, _, max_dev = compute_lateral_scoliosis_index(x_coords, z_coords)
        zero_crossings = count_zero_crossings(final_kappa_y)

        results.append({
            "field": name,
            "chi_M": chi_M,
            "tip_deflection_z": tip_deflection_z,
            "sagittal_index": sagittal_index,
            "max_dev_z": max_dev,
            "zero_crossings": zero_crossings
        })

        print(f"[{name}] chi_M={chi_M:4.1f} | Tip Z={tip_deflection_z:7.4f} m | Z-Crossings={zero_crossings}")

    return results

def run_experiment():
    print("Starting S-Shape vs Sigmoid Counter-Curvature Experiment...")

    L = 1.0
    n_points = 200
    output_dir = Path("outputs/experiments/s_shape_sweep")
    output_dir.mkdir(parents=True, exist_ok=True)

    chi_M_values = [0.0, 5.0, 10.0, 15.0, 20.0]

    tracemalloc.start()
    start_time_total = time.time()

    # Run Sine Sweep (Standard S-shape)
    results_sine = run_single_sweep("Sine", generate_sine_field, L, n_points, chi_M_values, output_dir)

    # Run Sigmoid Sweep (Requested comparison)
    results_sigmoid = run_single_sweep("Sigmoid", generate_sigmoid_field, L, n_points, chi_M_values, output_dir)

    all_results = results_sine + results_sigmoid

    end_time_total = time.time()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"\nTotal Runtime: {end_time_total - start_time_total:.2f}s")
    print(f"Peak Memory: {peak_mem / 1024 / 1024:.2f} MB")

    # Save Results
    csv_path = output_dir / "comparison_results.csv"
    with open(csv_path, "w", newline="") as f:
        fieldnames = ["field", "chi_M", "tip_deflection_z", "sagittal_index", "max_dev_z", "zero_crossings"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    print(f"Results saved to {csv_path}")

    # Plot Comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Tip Deflection
    for name, res in [("Sine", results_sine), ("Sigmoid", results_sigmoid)]:
        ax1.plot([r["chi_M"] for r in res], [r["tip_deflection_z"] for r in res], 'o-', label=name)
    ax1.set_xlabel(r"Active Muscle Gain $\chi_M$")
    ax1.set_ylabel("Tip Deflection Z (m)")
    ax1.set_title("Tip Deflection (Gravity Sag vs Lift)")
    ax1.grid(True)
    ax1.legend()

    # Plot 2: Zero Crossings (Shape Complexity)
    for name, res in [("Sine", results_sine), ("Sigmoid", results_sigmoid)]:
        ax2.plot([r["chi_M"] for r in res], [r["zero_crossings"] for r in res], 's--', label=name)
    ax2.set_xlabel(r"Active Muscle Gain $\chi_M$")
    ax2.set_ylabel("Curvature Zero Crossings")
    ax2.set_title("Shape Complexity (Zero Crossings)")
    ax2.grid(True)
    ax2.legend()

    plt.tight_layout()
    plt.savefig(output_dir / "comparison_plot.png")
    print(f"Plot saved to {output_dir / 'comparison_plot.png'}")

    # Report
    with open(output_dir / "report.md", "w") as f:
        f.write("# Counter-Curvature Field Comparison: Sine vs Sigmoid\n\n")
        f.write("Comparing standard Sine information field (periodic) vs Sigmoid field (monotonic).\n\n")
        f.write(f"- **Runtime**: {end_time_total - start_time_total:.2f}s\n")

        f.write("## Results\n\n")
        f.write("| Field | chi_M | Tip Z (m) | Zero Crossings | Note |\n")
        f.write("|-------|-------|-----------|----------------|------|\n")
        for r in all_results:
            note = "S-shape" if r["zero_crossings"] > 2 else "C-shape/Flat"
            f.write(f"| {r['field']} | {r['chi_M']} | {r['tip_deflection_z']:.4f} | {r['zero_crossings']} | {note} |\n")

        f.write("\n## Interpretation\n\n")
        f.write("- **Sine Field**: Gradient `dI/ds` oscillates (Cos), creating alternating active moments. Result: **S-shaped rod** (Multiple zero crossings).\n")
        f.write("- **Sigmoid Field**: Gradient `dI/ds` is a Gaussian bump (single sign). Creates a localized active moment region. Result: **Local Bend (C-shape)** or Lift, but no S-shape.\n")

if __name__ == "__main__":
    run_experiment()

"""
Mechano-Shape Map Experiment.

Maps the interaction between:
1. Stiffness Anisotropy (ECM/Protein alignment)
2. Preferred Curvature (Intrinsic tissue shape/growth)
3. Boundary Conditions (Joint health/stiffness)

To emergent mechanical outputs:
- Peak Curvature
- Peak Torsion
- Lateral Instability
"""

import csv
import sys
import time
from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Add repo root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.spinalmodes.countercurvature.coupling import CounterCurvatureParams
from src.spinalmodes.countercurvature.info_fields import InfoField1D
from src.spinalmodes.countercurvature.pyelastica_bridge import CounterCurvatureRodSystem


def run_experiment():
    # Setup
    date_str = time.strftime("%Y-%m-%d")
    output_dir = Path(f"outputs/sim/{date_str}_mechano_shape_map")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Mechano-Shape Experiment in {output_dir}")

    # Parameters
    L = 1.0
    n_elements = 40
    E0 = 1e6
    radius = 0.02
    rho = 1000
    gravity = 9.81

    # Sweep
    stiffness_levels = [0.5, 1.0, 2.0] # 0.5=Lateral Weak, 2.0=Lateral Stiff
    curvature_levels = [0.0, 5.0, 10.0] # Intrinsic curvature magnitude
    boundary_conditions = ["fixed", "pinned"]

    # Information field: Linear gradient (s/L)
    # This creates a constant preferred curvature along the rod
    s = np.linspace(0, L, n_elements + 1)
    I = s / L
    dIds = np.ones_like(s) / L
    info = InfoField1D(s=s, I=I, dIds=dIds)

    results = []

    total_sims = len(stiffness_levels) * len(curvature_levels) * len(boundary_conditions)
    print(f"Running {total_sims} simulations...")

    count = 0
    for bc, stiff, curv in product(boundary_conditions, stiffness_levels, curvature_levels):
        count += 1
        print(f"[{count}/{total_sims}] BC={bc}, Anisotropy={stiff}, Chi_Kappa={curv}")

        # We use chi_kappa to drive curvature.
        # We also add Torsion coupling (chi_tau) to see if anisotropy helps.
        # Fixed small torsion coupling
        chi_tau = 1.0

        params = CounterCurvatureParams(
            chi_kappa=curv,
            chi_tau=chi_tau,
            chi_E=0.0,
            chi_M=0.0,
            scale_length=L
        )

        system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=L,
            n_elements=n_elements,
            E0=E0,
            radius=radius,
            rho=rho,
            gravity=gravity,
            base_direction=(1.0, 0.0, 0.0), # Horizontal X
            normal=(0.0, 0.0, 1.0),         # Normal Z (curvature in Y-Z plane usually)
            stiffness_anisotropy=stiff
        )

        # Run
        start_t = time.time()
        # Using a slightly shorter time/dt for speed in "minimal" experiment
        res = system.run_simulation(
            final_time=1.0,
            dt=2e-4,
            gravity=gravity,
            boundary_condition=bc
        )
        dur = time.time() - start_t

        # Metrics
        # Max curvature (bending) - take max over time and space
        max_kappa = np.max(res.curvature)
        # Max torsion
        max_tau = np.max(np.abs(res.torsion))
        # Lateral Deviation (Y) - induced by torsion/instability
        # centerline is (time, 3, n_nodes)
        lat_dev = np.max(np.abs(res.centerline[:, 1, :]))
        # Vertical Sag (Z)
        sag = np.max(np.abs(res.centerline[:, 2, :]))

        results.append({
            "boundary": bc,
            "anisotropy": stiff,
            "chi_kappa": curv,
            "max_curvature": max_kappa,
            "max_torsion": max_tau,
            "lateral_dev": lat_dev,
            "sag": sag,
            "runtime": dur
        })

    # Save CSV
    csv_path = output_dir / "results.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"Results saved to {csv_path}")

    # Generate Heatmaps
    generate_plots(results, output_dir)

def generate_plots(results, output_dir):
    # We want to visualize Torsion stability as a function of Anisotropy and Curvature
    # for each BC.

    bcs = sorted(list(set(r["boundary"] for r in results)))

    fig, axes = plt.subplots(1, len(bcs), figsize=(12, 5), sharey=True)
    if len(bcs) == 1: axes = [axes]

    stiffs = sorted(list(set(r["anisotropy"] for r in results)))
    curvs = sorted(list(set(r["chi_kappa"] for r in results)))

    for ax, bc in zip(axes, bcs):
        # Extract matrix
        matrix = np.zeros((len(curvs), len(stiffs)))
        for r in results:
            if r["boundary"] == bc:
                i = curvs.index(r["chi_kappa"])
                j = stiffs.index(r["anisotropy"])
                matrix[i, j] = r["lateral_dev"] # Metric: Lateral Instability

        im = ax.imshow(matrix, origin="lower", cmap="viridis", aspect="auto")
        ax.set_title(f"BC: {bc.capitalize()}\nLateral Deviation (m)")
        ax.set_xlabel("Stiffness Anisotropy")
        ax.set_ylabel("Preferred Curvature (chi_kappa)")
        ax.set_xticks(range(len(stiffs)))
        ax.set_xticklabels(stiffs)
        ax.set_yticks(range(len(curvs)))
        ax.set_yticklabels(curvs)
        plt.colorbar(im, ax=ax)

    plt.tight_layout()
    plt.savefig(output_dir / "mechano_shape_map.png")
    print(f"Plot saved to {output_dir}/mechano_shape_map.png")

if __name__ == "__main__":
    run_experiment()

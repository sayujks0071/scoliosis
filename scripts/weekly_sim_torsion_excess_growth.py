import csv
import random
import sys
import time
import tracemalloc
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Ensure project root is in path
sys.path.append(".")

from src.spinalmodes.countercurvature.pyelastica_bridge import run_protein_simulation


def run_experiment():
    print("Starting Torsion with Excess Growth Experiment...")

    # Set and save a random seed for reproducibility
    seed_value = 42
    np.random.seed(seed_value)
    random.seed(seed_value)

    # Parameters based on previous sweep
    L = 1.0
    n_elements = 50
    duration = 3.0
    dt = 1e-4

    # We found chi_kappa = 25 caused planar buckling
    # We will map active_curvature to chi_kappa via scale_factor_kappa
    # so active_curvature = 25.0 / scale_factor_kappa
    scale_factor_kappa = 5.0
    active_curvature_val = 25.0 / scale_factor_kappa

    anisotropy_val = 3.0

    # Sweep torsion drive
    scale_factor_tau = 5.0
    # Let's sweep chi_tau from 0.0 to 1.0, so torsion_drive from 0.0 to 0.2
    torsion_drives = np.linspace(0.0, 0.2, 11)

    output_dir = Path("outputs/sim/2026-03-04")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save params
    with open(output_dir / "params.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["parameter", "value"])
        writer.writerow(["random_seed", seed_value])
        writer.writerow(["L", L])
        writer.writerow(["n_elements", n_elements])
        writer.writerow(["duration", duration])
        writer.writerow(["chi_kappa", 25.0])
        writer.writerow(["anisotropy", anisotropy_val])
        writer.writerow(["scale_factor_tau", scale_factor_tau])

    results = []

    tracemalloc.start()
    start_time_total = time.time()

    for t_drive in torsion_drives:
        print(f"\n--- Running Torsion Drive: {t_drive:.4f} (chi_tau: {t_drive*scale_factor_tau:.2f}) ---")

        res = run_protein_simulation(
            anisotropy=anisotropy_val,
            active_curvature=active_curvature_val,
            torsion_drive=t_drive,
            length=L,
            n_elements=n_elements,
            duration=duration,
            dt=dt,
            scale_factor_kappa=scale_factor_kappa,
            scale_factor_tau=scale_factor_tau,
            show_progress=False
        )

        if res["success"]:
            # Check S_lat and cobb_angle as scoliosis indicators
            s_lat = res.get("S_lat", 0.0)
            cobb = res.get("cobb_angle", 0.0)
            print(f"Success. S_lat: {s_lat:.4f}, Cobb: {cobb:.2f} deg")

            results.append({
                "torsion_drive": t_drive,
                "chi_tau": t_drive * scale_factor_tau,
                "S_lat": s_lat,
                "cobb_angle": cobb,
                "max_curvature": res.get("max_curvature", 0.0),
                "z_tip": res.get("z_tip", 0.0)
            })
        else:
            print(f"Failed: {res['error']}")

    end_time_total = time.time()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"\nTotal Runtime: {end_time_total - start_time_total:.2f}s")

    # Save Results
    csv_path = output_dir / "results.csv"
    with open(csv_path, "w", newline="") as f:
        fieldnames = ["torsion_drive", "chi_tau", "S_lat", "cobb_angle", "max_curvature", "z_tip"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"Results saved to {csv_path}")

    # Plot Comparison
    fig, ax1 = plt.subplots(figsize=(8, 6))

    chi_taus = [r["chi_tau"] for r in results]
    cobb_angles = [r["cobb_angle"] for r in results]

    color = 'tab:red'
    ax1.set_xlabel(r"Torsion Drive $\chi_\tau$")
    ax1.set_ylabel("Cobb Angle (degrees)", color=color)
    ax1.plot(chi_taus, cobb_angles, 'o-', color=color, label="Cobb Angle")
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:blue'
    s_lats = [r["S_lat"] for r in results]
    ax2.set_ylabel("Lateral Scoliosis Index ($S_{lat}$)", color=color)
    ax2.plot(chi_taus, s_lats, 's--', color=color, label="S_lat")
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title(r"Scoliosis Emergence with Excess Growth ($\chi_\kappa=25$)")
    fig.tight_layout()
    plt.savefig(output_dir / "plot_torsion_excess_growth.png")
    print(f"Plot saved to {output_dir / 'plot_torsion_excess_growth.png'}")

if __name__ == "__main__":
    run_experiment()

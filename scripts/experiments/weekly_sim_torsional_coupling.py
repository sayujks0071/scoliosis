"""
Weekly Simulation: Torsional Coupling Sweep.

Investigates whether increasing torsional coupling (chi_tau) induces 3D scoliosis-like
(S-shaped) profiles under gravity-like loading with fixed growth drive and anisotropy.

Hypothesis:
    High torsional coupling converts planar curvature (induced by chi_kappa) into
    3D helical buckling, manifesting as lateral deviation (S_lat) and Cobb angle.
"""

import csv
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Ensure src is in python path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from spinalmodes.countercurvature.coupling import CounterCurvatureParams
from spinalmodes.countercurvature.info_fields import InfoField1D
from spinalmodes.countercurvature.pyelastica_bridge import (
    PYELASTICA_AVAILABLE,
    CounterCurvatureRodSystem,
)


def run_experiment():
    # 1. Setup Output
    today_str = "2026-03-24"
    output_dir = Path(f"outputs/sim/{today_str}_torsion_sweep")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Running Weekly Sim: Torsional Coupling -> {output_dir}")

    if not PYELASTICA_AVAILABLE:
        print("Error: PyElastica not found. Cannot run simulation.")
        return

    # Set Seed for Reproducibility
    SEED = 42
    np.random.seed(SEED)

    # 2. Parameters
    # Fixed High Growth Drive (Planar Curvature Source)
    FIXED_CHI_KAPPA = 10.0
    # Fixed Moderate Anisotropy (Sagittal > Lateral Stiffness)
    FIXED_ANISOTROPY = 2.0

    # Sweep Torsional Coupling: 0.0 to 5.0
    # chi_tau couples Info Gradient -> Rest Torsion (twist)
    chi_tau_values = [0.0, 0.2, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]

    L = 1.0
    n_elements = 30 # Reduced elements to match previous faster test speed constraints
    final_time = 1.0 # Reduced time to match previous faster test speed constraints
    dt = 1e-4

    # 3. Define Info Field (Gradient)
    s = np.linspace(0, L, n_elements + 1)
    # Simple sine wave info field to create gradients along the rod
    # This simulates segmented gene expression (e.g. HOX boundaries)
    I = 0.5 + 0.5 * np.sin(np.pi * s / L)
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    results = []

    print(f"{'chi_tau':<10} | {'Lat Dev':<10} | {'Max Tor':<10} | {'Cobb':<10} | {'Time':<8}")
    print("-" * 60)

    for chi_tau in chi_tau_values:
        t0 = time.time()

        # Configure Params
        params = CounterCurvatureParams(
            chi_kappa=FIXED_CHI_KAPPA,
            chi_tau=chi_tau,
            chi_E=0.0,
            chi_M=0.0,
            scale_length=L
        )

        # Create System
        sys_obj = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=L,
            n_elements=n_elements,
            E0=1e6,
            radius=0.01, # Slender rod
            stiffness_anisotropy=FIXED_ANISOTROPY
        )

        res = sys_obj.run_simulation(
            final_time=final_time,
            dt=dt,
            save_every=500
        )

        metrics = res.compute_final_metrics()
        runtime = time.time() - t0

        results.append({
            "chi_tau": chi_tau,
            "max_curvature": metrics.get("max_curvature", 0.0),
            "max_torsion": metrics.get("max_torsion", 0.0),
            "s_lat": metrics.get("S_lat", 0.0),
            "cobb_angle": metrics.get("cobb_angle", 0.0),
            "end_to_end": metrics.get("end_to_end_distance", 0.0),
            "runtime": runtime
        })

        print(f"{chi_tau:<10.2f} | {metrics.get('S_lat',0.0):<10.4f} | {metrics.get('max_torsion',0.0):<10.4f} | {metrics.get('cobb_angle',0.0):<10.2f} | {runtime:<8.2f}")

    # 4. Save Results
    keys = results[0].keys()
    with open(output_dir / "results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    with open(output_dir / "params.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Parameter", "Value"])
        writer.writerow(["seed", SEED])
        writer.writerow(["chi_kappa", FIXED_CHI_KAPPA])
        writer.writerow(["stiffness_anisotropy", FIXED_ANISOTROPY])
        writer.writerow(["Description", "Sweep chi_tau (Torsional Coupling). Fixed Growth & Anisotropy."])

    # 5. Plot
    chi_taus = [r["chi_tau"] for r in results]
    s_lats = [r["s_lat"] for r in results]
    torsions = [r["max_torsion"] for r in results]
    cobbs = [r["cobb_angle"] for r in results]

    plt.figure(figsize=(10, 8))

    plt.subplot(3, 1, 1)
    plt.plot(chi_taus, s_lats, 'o-', color='blue')
    plt.ylabel("Lateral Deviation (S_lat)")
    plt.title(f"Torsional Coupling Effects (chi_kappa={FIXED_CHI_KAPPA}, R={FIXED_ANISOTROPY})")
    plt.grid(True)

    plt.subplot(3, 1, 2)
    plt.plot(chi_taus, torsions, '^-', color='green')
    plt.ylabel("Max Torsion (rad/m)")
    plt.grid(True)

    plt.subplot(3, 1, 3)
    plt.plot(chi_taus, cobbs, 's-', color='red')
    plt.ylabel("Cobb Angle (deg)")
    plt.xlabel("Torsional Coupling (chi_tau)")
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(output_dir / "plot_torsion_sweep.png")
    plt.close()

    # 6. Report skeleton
    report_path = output_dir / "report.md"
    if not report_path.exists():
        with open(report_path, 'w') as f:
            f.write("# Simulation Report: Torsional Coupling Sweep\n\n")
            f.write("**Date**: 2026-03-24\n\n")
            f.write("## Hypothesis\n")
            f.write("Testing whether increasing torsional coupling (chi_tau) breaks the symmetry of planar S-curves and induces 3D scoliosis-like buckling.\n\n")
            f.write("## Parameters\n")
            f.write(f"- **Torsion Sweep**: {chi_tau_values}\n")
            f.write(f"- **Growth Drive (chi_kappa)**: {FIXED_CHI_KAPPA}\n")
            f.write("- **Anisotropy (R)**: {FIXED_ANISOTROPY}\n")
            f.write("- **Boundary Condition**: Fixed\n\n")
            f.write("## Results\n")
            f.write("See attached `plot_torsion_sweep.png`.\n\n")

    print("Experiment Complete.")

if __name__ == "__main__":
    run_experiment()

"""
Weekly Simulation: Critical Anisotropy Threshold.

Investigates the critical stiffness anisotropy ratio required to contain/stabilize
a spine under high active growth drive (chi_kappa = 10.0).

Hypothesis:
    There exists a critical anisotropy threshold (R_crit) below which the spine
    buckles into an unstable lateral mode (S-shape or simple deviation) driven by
    growth gain, and above which it remains stable (or confined to sagittal plane).
"""

import csv
import sys
import time
import tracemalloc
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
    # Hardcode date for reproducibility of this specific weekly sim
    today_str = "2026-02-01"
    output_dir = Path(f"outputs/sim/{today_str}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Running Weekly Sim: Critical Anisotropy -> {output_dir}")

    if not PYELASTICA_AVAILABLE:
        print("Error: PyElastica not found. Cannot run simulation.")
        return

    # 2. Parameters
    # Fixed High Growth Drive
    FIXED_CHI_KAPPA = 10.0
    # Small Torsion to break symmetry
    FIXED_CHI_TAU = 0.2

    # Sweep Anisotropy: 0.5 (Lateral < Sagittal) to 10.0 (Lateral >> Sagittal)
    # R scales bend_matrix[0,0] (Sagittal Stiffness).
    # If R > 1, Sagittal is Stiffer -> Rod prefers Lateral bending?
    # Wait, if Sagittal is stiff, it costs more energy to bend in Sagittal.
    # So it should buckle into Lateral if forced.
    anisotropy_values = [0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 8.0, 10.0]

    L = 1.0
    n_elements = 50
    final_time = 2.0
    dt = 1e-4

    # 3. Define Info Field (Gradient)
    s = np.linspace(0, L, n_elements + 1)
    # Simple sine wave info field
    I = 0.5 + 0.5 * np.sin(np.pi * s / L)
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    results = []

    print(f"{'Anisotropy':<12} | {'Lat Dev':<10} | {'Cobb':<10} | {'Time':<8}")
    print("-" * 50)

    tracemalloc.start()

    for r in anisotropy_values:
        t0 = time.time()

        # Configure Params
        params = CounterCurvatureParams(
            chi_kappa=FIXED_CHI_KAPPA,
            chi_tau=FIXED_CHI_TAU,
            chi_E=0.0,
            chi_M=0.0,
            scale_length=L
        )

        # Create System
        # stiffness_anisotropy scales Sagittal Stiffness (d1/X-axis normal)
        sys_obj = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=L,
            n_elements=n_elements,
            E0=1e6,
            radius=0.01, # Slender rod
            stiffness_anisotropy=r
        )

        res = sys_obj.run_simulation(
            final_time=final_time,
            dt=dt,
            save_every=500
        )

        metrics = res.compute_final_metrics()
        runtime = time.time() - t0

        results.append({
            "anisotropy": r,
            "max_curvature": metrics.get("max_curvature", 0.0),
            "s_lat": metrics.get("S_lat", 0.0),
            "cobb_angle": metrics.get("cobb_angle", 0.0),
            "end_to_end": metrics.get("end_to_end_distance", 0.0),
            "runtime": runtime
        })

        print(f"{r:<12.2f} | {metrics.get('S_lat',0.0):<10.4f} | {metrics.get('cobb_angle',0.0):<10.2f} | {runtime:<8.2f}")

    tracemalloc.stop()

    # 4. Save Results
    keys = results[0].keys()
    with open(output_dir / "results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    with open(output_dir / "params.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Parameter", "Value"])
        writer.writerow(["chi_kappa", FIXED_CHI_KAPPA])
        writer.writerow(["chi_tau", FIXED_CHI_TAU])
        writer.writerow(["Description", "Sweep stiffness_anisotropy (scales Sagittal stiffness). Fixed High Growth."])

    # 5. Plot
    anisotropies = [r["anisotropy"] for r in results]
    s_lats = [r["s_lat"] for r in results]
    cobbs = [r["cobb_angle"] for r in results]

    plt.figure(figsize=(10, 6))

    plt.subplot(2, 1, 1)
    plt.plot(anisotropies, s_lats, 'o-', color='blue')
    plt.ylabel("Lateral Deviation (S_lat)")
    plt.title(f"Stability vs Anisotropy (chi_kappa={FIXED_CHI_KAPPA})")
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(anisotropies, cobbs, 's-', color='red')
    plt.ylabel("Cobb Angle (deg)")
    plt.xlabel("Stiffness Anisotropy (Sagittal Scaling)")
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(output_dir / "plot_anisotropy_stability.png")
    plt.close()

    print("Experiment Complete.")

if __name__ == "__main__":
    run_experiment()

"""
Weekly Simulation: Torsion Coupling Stability at High Anisotropy
Goal: Test if Torsional Coupling (chi_tau) destabilizes a spine with High Stiffness Anisotropy (R=10) under High Growth Drive.
Hypothesis: While High Anisotropy (R=10) stabilizes Lateral Bending (Scoliosis), Torsional Coupling (chi_tau > 0) will introduce a new mode of instability (twist-buckling), re-opening the S-curve window.
"""

import csv
import os
import sys
import time
import tracemalloc
from datetime import datetime
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


def run_experiment(
    out_file: str,
    chi_tau_values: list[float],
    anisotropy: float,
    chi_kappa: float,
    info_amplitude: float,
    n_elements: int = 50,
    final_time: float = 2.0,
) -> None:
    if not PYELASTICA_AVAILABLE:
        print("Error: PyElastica not installed.")
        return

    # Create Output Directory
    out_dir = os.path.dirname(out_file)
    os.makedirs(out_dir, exist_ok=True)

    # Simulation Constants
    length = 0.5
    radius = 0.01
    E0 = 1e6
    rho = 1000.0
    gravity = 9.81
    dt = 1e-5

    # Info Field Parameters (Gaussian Bump)
    info_center = 0.6
    info_width = 0.1

    # Prepare CSV
    fieldnames = [
        "chi_tau", "anisotropy", "chi_kappa", "info_amplitude",
        "cobb_angle", "s_lat", "max_curvature", "max_torsion",
        "bending_energy", "runtime_sec"
    ]

    print(f"Starting Sweep: Anisotropy={anisotropy}, Chi_Kappa={chi_kappa}")
    print(f"Output: {out_file}")
    print("-" * 80)
    print(f"{'Chi_Tau':<10} | {'Cobb':<8} | {'S_lat':<8} | {'MaxCurv':<8} | {'MaxTor':<8} | {'Time':<6}")
    print("-" * 80)

    results = []

    with open(out_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for chi_tau in chi_tau_values:
            tracemalloc.start()
            t0 = time.time()

            # 1. Setup Info Field
            s = np.linspace(0, length, n_elements + 1)
            # Gaussian bump
            I = 0.5 + info_amplitude * np.exp(
                -0.5 * ((s - info_center * length) / (info_width * length))**2
            )
            dIds = np.gradient(I, s)
            info = InfoField1D(s=s, I=I, dIds=dIds)

            # 2. Setup Params
            params = CounterCurvatureParams(
                chi_kappa=chi_kappa,
                chi_tau=chi_tau,
                chi_E=0.0,
                chi_M=0.0,
                scale_length=length
            )

            # 3. Setup Rod System
            # Normal in X (d1=X) -> Bending about d2=Y (Lateral) is driven by chi_kappa (index 1)
            kappa_gen = np.zeros((3, n_elements + 1))
            kappa_gen[0, :] = 2.0 # Constant sagittal curvature about d1=X (Kyphosis)

            rod_system = CounterCurvatureRodSystem.from_iec(
                info=info,
                params=params,
                length=length,
                n_elements=n_elements,
                E0=E0,
                rho=rho,
                radius=radius,
                kappa_gen=kappa_gen,
                gravity=gravity,
                base_position=(0.0, 0.0, 0.0),
                base_direction=(0.0, 0.0, 1.0),
                normal=(1.0, 0.0, 0.0), # Important: Normal in X
                stiffness_anisotropy=anisotropy
            )

            # 4. Run Simulation
            result = rod_system.run_simulation(
                final_time=final_time,
                dt=dt,
                save_every=5000,
                boundary_condition="fixed",
                progress_bar=False
            )

            t1 = time.time()
            tracemalloc.stop()

            # 5. Metrics
            metrics = result.compute_final_metrics()

            row = {
                "chi_tau": chi_tau,
                "anisotropy": anisotropy,
                "chi_kappa": chi_kappa,
                "info_amplitude": info_amplitude,
                "cobb_angle": metrics.get("cobb_angle", 0.0),
                "s_lat": metrics.get("S_lat", 0.0),
                "max_curvature": metrics.get("max_curvature", 0.0),
                "max_torsion": metrics.get("max_torsion", 0.0),
                "bending_energy": metrics.get("bending_energy", 0.0),
                "runtime_sec": t1 - t0
            }

            writer.writerow(row)
            csvfile.flush()
            results.append(row)

            print(
                f"{chi_tau:<10.2f} | {row['cobb_angle']:<8.2f} | "
                f"{row['s_lat']:<8.4f} | {row['max_curvature']:<8.4f} | "
                f"{row['max_torsion']:<8.4f} | {row['runtime_sec']:<6.2f}"
            )

    # Plotting
    plot_results(out_dir, results)

def plot_results(out_dir, results):
    if not results:
        return

    chi_taus = [r['chi_tau'] for r in results]
    cobbs = [r['cobb_angle'] for r in results]
    s_lats = [r['s_lat'] for r in results]
    torsions = [r['max_torsion'] for r in results]

    plt.figure(figsize=(15, 5))

    plt.subplot(1, 3, 1)
    plt.plot(chi_taus, cobbs, 'o-', color='blue')
    plt.xlabel('Torsion Coupling (chi_tau)')
    plt.ylabel('Cobb Angle (deg)')
    plt.title('Effect of Torsion on Cobb Angle (R=10)')
    plt.grid(True)

    plt.subplot(1, 3, 2)
    plt.plot(chi_taus, s_lats, 's-', color='green')
    plt.xlabel('Torsion Coupling (chi_tau)')
    plt.ylabel('Lateral Deviation (S_lat)')
    plt.title('Effect of Torsion on S-Shape')
    plt.grid(True)

    plt.subplot(1, 3, 3)
    plt.plot(chi_taus, torsions, '^-', color='red')
    plt.xlabel('Torsion Coupling (chi_tau)')
    plt.ylabel('Max Torsion (rad/m)')
    plt.title('Induced Torsion')
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "plot_torsion_sweep.png"))
    print(f"Plots saved to {out_dir}")

def main():
    date_str = datetime.now().strftime('%Y-%m-%d')
    out_dir = f"outputs/sim/{date_str}"
    out_file = os.path.join(out_dir, "results.csv")

    # Save Params
    params_file = os.path.join(out_dir, "params.csv")
    os.makedirs(out_dir, exist_ok=True)

    # Sweep Definition
    chi_tau_values = np.linspace(0.0, 2.0, 11).tolist() # 0.0, 0.2, ..., 2.0
    anisotropy = 10.0
    chi_kappa = 10.0
    info_amplitude = 0.1
    seed = 42
    np.random.seed(seed)

    with open(params_file, 'w') as f:
        f.write("parameter,value\n")
        f.write(f"seed,{seed}\n")
        f.write(f"chi_tau_values,{chi_tau_values}\n")
        f.write(f"anisotropy,{anisotropy}\n")
        f.write(f"chi_kappa,{chi_kappa}\n")
        f.write(f"info_amplitude,{info_amplitude}\n")

    run_experiment(
        out_file=out_file,
        chi_tau_values=chi_tau_values,
        anisotropy=anisotropy,
        chi_kappa=chi_kappa,
        info_amplitude=info_amplitude
    )

if __name__ == "__main__":
    main()

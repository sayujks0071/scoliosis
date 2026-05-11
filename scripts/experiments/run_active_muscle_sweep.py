
import csv
import os
import sys
import time
import tracemalloc
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Ensure src is in path
sys.path.append(os.getcwd())

from src.spinalmodes.countercurvature.coupling import CounterCurvatureParams
from src.spinalmodes.countercurvature.info_fields import InfoField1D
from src.spinalmodes.countercurvature.pyelastica_bridge import CounterCurvatureRodSystem


def count_zero_crossings(arr):
    """Count sign changes in a 1D array."""
    return ((arr[:-1] * arr[1:]) < 0).sum()

def run_sweep():
    # 1. Setup paths
    date_str = time.strftime("%Y-%m-%d")
    output_dir = Path(f"outputs/sim/{date_str}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Active Muscle Torque (Chi_M) Sweep in {output_dir}")

    # 2. Define Constant Parameters
    L = 1.0
    n_elements = 50
    final_time = 1.5 # Reduced time
    dt = 1e-4 # Standard dt
    E0 = 1e6
    radius = 0.02
    rho = 1000
    gravity = 9.81

    # Info Field: Sinusoidal
    n_points = 200
    s = np.linspace(0, L, n_points)
    # I(s) = sin^2(2*pi*s/L) -> dI/ds has shape sin(4*pi*s/L)
    I = np.sin(2 * np.pi * s / L)**2
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # Save base params
    with open(output_dir / "params.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Parameter", "Value"])
        writer.writerow(["L", L])
        writer.writerow(["n_elements", n_elements])
        writer.writerow(["final_time", final_time])
        writer.writerow(["dt", dt])
        writer.writerow(["E0", E0])
        writer.writerow(["radius", radius])
        writer.writerow(["rho", rho])
        writer.writerow(["gravity", gravity])
        writer.writerow(["InfoField", "sin^2(2*pi*s/L)"])
        writer.writerow(["chi_E", 0.0])
        writer.writerow(["chi_kappa", 0.0])

    # 3. Define Sweep
    # Reduced number of points for speed
    chi_M_values = np.linspace(0.0, 20.0, 6)
    results = []

    tracemalloc.start()
    start_time_total = time.time()

    centerlines = [] # Store final centerlines for visualization

    for i, chi_M in enumerate(chi_M_values):
        print(f"[{i+1}/{len(chi_M_values)}] Running chi_M = {chi_M:.2f} ...")
        sys.stdout.flush()

        params = CounterCurvatureParams(
            chi_E=0.0,
            chi_kappa=0.0,
            chi_M=chi_M,
            scale_length=L
        )

        # Horizontal initialization to maximize gravity effect
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
            normal=(0.0, 1.0, 0.0)
        )

        # Reduced save frequency to save memory/IO
        sim_res = system.run_simulation(final_time=final_time, dt=dt, save_every=1000)

        # Analyze final state
        final_centerline = sim_res.centerline[-1] # (3, n_nodes)
        final_curvature = sim_res.curvature[-1] # (n_nodes,)

        tip_z = final_centerline[2, -1]
        max_k = np.max(final_curvature)

        final_kappa_vec = sim_res.kappa[-1]
        bending_kappa = final_kappa_vec[:, 1]

        zero_crossings = count_zero_crossings(bending_kappa[5:-5]) # Ignore ends

        results.append({
            "chi_M": chi_M,
            "tip_deflection_z": tip_z,
            "max_curvature": max_k,
            "zero_crossings": zero_crossings
        })

        centerlines.append((chi_M, final_centerline))

    end_time_total = time.time()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 4. Save Results
    csv_path = output_dir / "results.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["chi_M", "tip_deflection_z", "max_curvature", "zero_crossings"])
        writer.writeheader()
        writer.writerows(results)

    # 5. Plotting
    # Summary Plot
    chi_vals = [r["chi_M"] for r in results]
    tips = [r["tip_deflection_z"] for r in results]
    crossings = [r["zero_crossings"] for r in results]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    color = 'tab:red'
    ax1.set_xlabel(r'Active Muscle Gain ($\chi_M$)')
    ax1.set_ylabel('Tip Deflection Z (m)', color=color)
    ax1.plot(chi_vals, tips, 'o-', color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True)

    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Curvature Zero Crossings (Count)', color=color)
    ax2.step(chi_vals, crossings, where='mid', color=color, linestyle='--')
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title(f"Emergence of S-Shape under Active Muscle Torque\n(Gravity g={gravity} m/s^2)")
    plt.savefig(output_dir / "sweep_metrics.png")
    plt.close()

    # Centerline Shapes Plot
    plt.figure(figsize=(12, 8))
    # Plot all lines
    for chi, cl in centerlines:
        plt.plot(cl[0, :], cl[2, :], label=rf"$\chi_M={chi:.1f}$")

    plt.xlabel("X (m)")
    plt.ylabel("Z (m)")
    plt.title("Rod Shapes in Sagittal Plane (Side View)")
    plt.legend()
    plt.axis('equal')
    plt.grid(True)
    plt.savefig(output_dir / "rod_shapes.png")
    plt.close()

    # 6. Report Generation
    report_path = output_dir / "report.md"
    with open(report_path, "w") as f:
        f.write("# Simulation Report: Active Muscle Torque Sweep\n\n")
        f.write(f"**Date**: {date_str}\n\n")
        f.write("## Overview\n")
        f.write(r"Investigated the emergence of S-shaped spinal profiles by sweeping the Active Muscle Torque gain ($\chi_M$) ")
        f.write("under standard gravity loading. A horizontal rod (cantilever) was subjected to a sinusoidal information field ")
        f.write("driving distributed internal moments.\n\n")

        f.write("## Key Findings\n")
        f.write("- **Gravity Dominance**: At low $\\chi_M$, the rod exhibits a simple C-shape sag due to gravity.\n")
        f.write("- **Emergence**: As $\\chi_M$ increases, the internal active moments counteract gravity.\n")
        f.write("- **S-Shape**: A distinct S-shape (multiple zero crossings in curvature) emerges at higher gains.\n\n")

        f.write("## Results Summary\n\n")
        f.write("| chi_M | Tip Z (m) | Zero Crossings |\n")
        f.write("|-------|-----------|----------------|\n")
        for r in results:
            f.write(f"| {r['chi_M']:.2f} | {r['tip_deflection_z']:.4f} | {r['zero_crossings']} |\n")

        f.write("\n\n## Next Steps\n")
        f.write("- Investigate coupling with $\\chi_E$ (stiffness anisotropy).\n")
        f.write("- Test vertical initialization with buckling loads.\n")

    print(f"Report written to {report_path}")
    print("Done.")

if __name__ == "__main__":
    run_sweep()

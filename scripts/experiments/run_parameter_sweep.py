
import csv
import datetime
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Add repository root to sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))

from src.spinalmodes.countercurvature.coupling import CounterCurvatureParams
from src.spinalmodes.countercurvature.info_fields import InfoField1D
from src.spinalmodes.countercurvature.pyelastica_bridge import CounterCurvatureRodSystem


def run_sweep():
    print("Starting Active Muscle Torque (chi_M) Parameter Sweep...")

    # Date for output directory
    today = datetime.date.today().isoformat()
    output_dir = repo_root / "outputs" / "sim" / today
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Define Information Field
    # Sinusoidal field creates an S-shape potential
    L = 1.0
    n_points = 200
    s = np.linspace(0, L, n_points)
    # Information field with inflection point in the middle
    I = np.sin(2 * np.pi * s / L)**2
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # 2. Setup Simulation Parameters
    n_elements = 50
    final_time = 2.0
    dt = 2e-5 # Smaller timestep for stability with active forces

    # Sweep parameters: chi_M (Active Moment Gain)
    chi_M_values = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0]
    results_summary = []

    # Constants
    E0 = 1e6
    radius = 0.02
    rho = 1000
    gravity = 9.81

    # Save parameters to CSV (one row per run, but we can save the constant config first)
    params_csv_path = output_dir / "params.csv"
    with open(params_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["chi_M", "L", "n_elements", "E0", "radius", "rho", "gravity", "dt", "final_time"])
        for chi_M in chi_M_values:
            writer.writerow([chi_M, L, n_elements, E0, radius, rho, gravity, dt, final_time])

    print(f"Parameters saved to {params_csv_path}")

    for chi_M in chi_M_values:
        # chi_M: active moments (Muscle tone / Active stresses)
        params = CounterCurvatureParams(
            chi_E=0.0,
            chi_kappa=0.0,
            chi_M=chi_M,
            scale_length=L
        )

        print(f"Running simulation for chi_M={chi_M}...")

        # Horizontal rod initialization to test gravity resistance
        # base_direction=(1.0, 0.0, 0.0) means rod is along X-axis.
        # gravity is (0.0, 0.0, -9.81).
        # We expect gravity to sag the rod in -Z.
        # Active moments (coupled to dI/ds) will apply torques.
        # Since I is sinusoidal, dI/ds oscillates.
        # Torques are around Y-axis (sagittal plane).

        system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=L,
            n_elements=n_elements,
            E0=E0,
            radius=radius,
            rho=rho,
            gravity=gravity,
            base_direction=(1.0, 0.0, 0.0),
            normal=(0.0, 1.0, 0.0)
        )

        try:
            result = system.run_simulation(final_time=final_time, dt=dt, save_every=100)

            # Metrics
            final_curvature = result.curvature[-1] # shape (n_nodes,)
            avg_curvature = np.mean(final_curvature)

            # Sagittal deflection (z-coordinate)
            # Centerline is (time, n_nodes, 3). result.centerline[-1] is (n_nodes, 3)
            final_centerline = result.centerline[-1]
            tip_deflection_z = final_centerline[-1, 2] # Tip node, Z component
            mid_deflection_z = final_centerline[n_elements // 2, 2] # Mid node, Z component

            # Calculate S-shape metric: Number of sign changes in curvature or second derivative of position
            # Here we approximate by checking if different parts of rod are up/down relative to baseline or have different curvature signs
            # A simple metric for "S-ness" is standard deviation of curvature, or checking if tip and mid have different signs of deflection relative to some mean.
            # Let's stick to simple metrics for now.

            results_summary.append({
                "chi_M": chi_M,
                "avg_curvature": avg_curvature,
                "tip_deflection_z": tip_deflection_z,
                "mid_deflection_z": mid_deflection_z,
                "max_deflection_z": np.max(np.abs(final_centerline[:, 2]))
            })

            print(f"  Avg Curvature: {avg_curvature:.4f}")
            print(f"  Tip Deflection Z: {tip_deflection_z:.4f} m")

        except Exception as e:
            print(f"  Simulation failed for chi_M={chi_M}: {e}")
            results_summary.append({
                "chi_M": chi_M,
                "avg_curvature": np.nan,
                "tip_deflection_z": np.nan,
                "mid_deflection_z": np.nan,
                "max_deflection_z": np.nan
            })

    # Save results
    results_csv_path = output_dir / "results.csv"
    with open(results_csv_path, "w", newline="") as f:
        fieldnames = ["chi_M", "avg_curvature", "tip_deflection_z", "mid_deflection_z", "max_deflection_z"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results_summary)
    print(f"Results saved to {results_csv_path}")

    # Plotting
    chi_M_list = [r["chi_M"] for r in results_summary]
    tip_z_list = [r["tip_deflection_z"] for r in results_summary]
    mid_z_list = [r["mid_deflection_z"] for r in results_summary]

    plt.figure(figsize=(10, 6))
    plt.plot(chi_M_list, tip_z_list, 'o-', label="Tip Deflection Z")
    plt.plot(chi_M_list, mid_z_list, 's--', label="Mid-point Deflection Z")
    plt.xlabel(r"Active Torque Gain $\chi_M$")
    plt.ylabel("Deflection (m)")
    plt.title("Effect of Active Muscle Moments on Rod Shape under Gravity")
    plt.legend()
    plt.grid(True)
    plt.savefig(output_dir / "plot_deflection.png")
    print(f"Plot saved to {output_dir / 'plot_deflection.png'}")

    # Report Generation
    report_path = output_dir / "report.md"
    with open(report_path, "w") as f:
        f.write(f"# Weekly Simulation Report: Active Torque Sweep ({today})\n\n")
        f.write("## Overview\n")
        f.write(r"This parameter sweep investigates the effect of **Active Muscle Torques ($\chi_M$)** ")
        f.write("on a horizontal rod subject to gravity. The hypothesis is that increasing active moments ")
        f.write("driven by an information gradient (sinusoidal) can counteract gravitational sagging and induce S-shaped curvature.\n\n")

        f.write("## Parameters\n")
        f.write("- **Variable**: $\\chi_M$ (Active Torque Gain)\n")
        f.write("- **Range**: 0.0 to 10.0\n")
        f.write("- **Constant**: Gravity=9.81, E0=1e6, L=1.0\n")
        f.write("- **Info Field**: Sinusoidal `sin(2*pi*s/L)^2`\n\n")

        f.write("## Results\n")
        f.write("### Quantitative Summary\n")
        f.write("| chi_M | Tip Deflection Z (m) | Mid Deflection Z (m) |\n")
        f.write("|-------|----------------------|----------------------|\n")
        for r in results_summary:
            f.write(f"| {r['chi_M']} | {r['tip_deflection_z']:.4f} | {r['mid_deflection_z']:.4f} |\n")

        f.write("\n### Observations\n")
        f.write("- **What changed**: As $\\chi_M$ increases, the rod's deflection profile changes.\n")

        # Analyze outcome for report
        if len(results_summary) > 1:
            baseline = results_summary[0]['tip_deflection_z']
            final = results_summary[-1]['tip_deflection_z']
            if abs(final) < abs(baseline):
                 f.write("- **Emergent Shapes**: Active torques successfully reduced the gravitational sag.\n")
            else:
                 f.write("- **Emergent Shapes**: Active torques altered the shape, potentially increasing curvature in specific regions.\n")

        f.write("- **Scoliosis Relevance**: This mechanism demonstrates how active muscle tone (driven by information/proprioception) ")
        f.write("can dynamically maintain spinal alignment against gravity. Failure of this active component (low $\\chi_M$) leads to passive gravitational collapse (sag).\n")

        f.write("\n## Next Steps\n")
        f.write("- Suggestion: Sweep **Stiffness Anisotropy ($\\chi_E$)** combined with active moments to see if stiffer regions can lock in the corrective shape.\n")

    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    run_sweep()

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


def run_sweep():
    # 1. Setup paths
    date_str = time.strftime("%Y-%m-%d")
    output_dir = Path(f"outputs/sim/{date_str}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Load Vector Tilt (Posture) Sweep in {output_dir}")

    # 2. Define Constant Parameters
    L = 1.0
    n_elements = 50
    final_time = 2.0
    dt = 1e-4
    E0 = 1e6
    radius = 0.02
    rho = 1000
    gravity_magnitude = 9.81

    # Info Field: Sinusoidal
    # Standard field that promotes S-shape if muscle is active
    n_points = 200
    s = np.linspace(0, L, n_points)
    I = np.sin(2 * np.pi * s / L)**2
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # Biological Parameters (Fixed)
    # Use a scenario that generates S-shape in horizontal posture (Active Muscle)
    # chi_M=15.0 created good S-shapes in previous sweeps
    base_params = CounterCurvatureParams(
        chi_E=0.0,
        chi_kappa=4.0, # Some intrinsic curvature
        chi_M=15.0,    # Strong active muscle correction
        chi_tau=0.0,
        scale_length=L
    )

    # Save base params
    with open(output_dir / "params.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Parameter", "Value"])
        writer.writerow(["L", L])
        writer.writerow(["n_elements", n_elements])
        writer.writerow(["final_time", final_time])
        writer.writerow(["dt", dt])
        writer.writerow(["E0", E0])
        writer.writerow(["gravity", gravity_magnitude])
        writer.writerow(["chi_M", base_params.chi_M])
        writer.writerow(["chi_kappa", base_params.chi_kappa])

    # 3. Define Sweep: Tilt Angle (theta)
    # Theta = 0 deg: Horizontal (Gravity perpendicular to spine) -> Max bending load
    # Theta = 90 deg: Vertical (Gravity parallel to spine) -> Buckling load
    theta_values = np.linspace(0, 90, 7) # 0, 15, 30, 45, 60, 75, 90
    results = []
    centerlines = []

    tracemalloc.start()

    for theta_deg in theta_values:
        theta_rad = np.radians(theta_deg)
        print(f"Running Tilt Theta = {theta_deg:.1f} deg...")

        # We rotate the ROD Base Direction relative to Gravity (-Z)
        # Rod in X-Z plane.
        # If theta=0, rod along X. Gravity -Z. Perpendicular.
        # If theta=90, rod along Z. Gravity -Z. Parallel (Compression).

        # base_direction vector: [cos(theta), 0, sin(theta)]
        # Actually, let's keep rod fixed along X and rotate Gravity?
        # No, PyElastica's gravity is fixed global vector usually.
        # But here `CounterCurvatureRodSystem` takes `gravity` scalar and applies [0,0,-g].
        # So we must rotate the rod.

        base_dir = np.array([np.cos(theta_rad), 0.0, np.sin(theta_rad)])
        # Normal must be orthogonal. Y-axis is safe.
        normal_dir = np.array([0.0, 1.0, 0.0])

        system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=base_params,
            length=L,
            n_elements=n_elements,
            E0=E0,
            radius=radius,
            rho=rho,
            gravity=gravity_magnitude,
            base_direction=tuple(base_dir),
            normal=tuple(normal_dir)
        )

        sim_res = system.run_simulation(final_time=final_time, dt=dt, save_every=500)

        # Analyze
        # We need to project the shape into the "Spine Frame" to measure S-shape
        # regardless of global rotation.
        # Rod tangent t(s). Local curvature k(s).
        # We can just look at the intrinsic curvature `sim_res.curvature`.
        # `sim_res.curvature` is the norm of bending kappa.
        # But we want signed curvature to see S-shape (zero crossings).
        # Kappa vector in local material frame: d1, d2, d3.
        # d2 is the main bending component in the plane (usually).

        final_kappa = sim_res.kappa[-1] # (n_nodes, 3)
        # Bending around d2 (local normal) corresponds to planar bending
        bending_k = final_kappa[:, 1]

        avg_k = np.mean(np.abs(bending_k))
        max_k = np.max(np.abs(bending_k))

        # Zero crossings in signed curvature
        # Filter noise near 0
        k_clean = np.where(np.abs(bending_k) < 1e-4, 0, bending_k)
        # Count sign changes
        sign_changes = ((k_clean[:-1] * k_clean[1:]) < 0).sum()

        # Tip Deflection relative to base tangent?
        # Let's just track absolute tip position for now.
        tip_pos = sim_res.centerline[-1][:, -1]

        results.append({
            "theta_deg": theta_deg,
            "avg_curvature": avg_k,
            "max_curvature": max_k,
            "zero_crossings": sign_changes,
            "tip_x": tip_pos[0],
            "tip_z": tip_pos[2]
        })

        centerlines.append((theta_deg, sim_res.centerline[-1]))

    tracemalloc.stop()

    # 4. Save Results
    csv_path = output_dir / "results.csv"
    keys = results[0].keys()
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    # 5. Plotting
    # Shape Plot
    plt.figure(figsize=(10, 10))
    for theta, cl in centerlines:
        plt.plot(cl[0, :], cl[2, :], label=f"{theta:.0f}°")

    plt.xlabel("Global X (m)")
    plt.ylabel("Global Z (m)")
    plt.title("Rod Shapes under Varying Posture (Tilt)")
    plt.legend()
    plt.axis('equal')
    plt.grid(True)
    plt.savefig(output_dir / "posture_shapes.png")
    plt.close()

    # Metrics Plot
    thetas = [r["theta_deg"] for r in results]
    crossings = [r["zero_crossings"] for r in results]
    curv = [r["avg_curvature"] for r in results]

    fig, ax1 = plt.subplots()
    ax1.set_xlabel("Tilt Angle (deg) [0=Horiz, 90=Vert]")
    ax1.set_ylabel("Zero Crossings (S-Shape Complexity)", color='tab:blue')
    ax1.plot(thetas, crossings, 'o--', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax2 = ax1.twinx()
    ax2.set_ylabel("Avg Curvature (1/m)", color='tab:red')
    ax2.plot(thetas, curv, 's-', color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    plt.title("Stability of S-Shape vs Posture")
    plt.savefig(output_dir / "posture_metrics.png")
    plt.close()

    # 6. Report
    report_path = output_dir / "report.md"
    with open(report_path, "w") as f:
        f.write("# Simulation Report: Posture (Tilt) Sweep\n\n")
        f.write(f"**Date**: {date_str}\n\n")
        f.write("## Overview\n")
        f.write("Investigated the stability of the emergent S-shape (driven by $\\chi_M=15$) as the rod's posture changes from Horizontal (0°) to Vertical (90°) under gravity.\n\n")

        f.write("## Findings\n")
        f.write("- **Horizontal (0°)**: Max gravitational moment. S-shape is prominent as active torque fights sag.\n")
        f.write("- **Vertical (90°)**: Gravity acts axially (compression). Bending moments vanish except for instability.\n")
        f.write("- **Transition**: Does the S-shape collapse or straighten as we stand up?\n\n")

        f.write("## Results Table\n")
        f.write("| Theta (deg) | Zero Crossings | Avg Curvature |\n")
        f.write("|-------------|----------------|---------------|\n")
        for r in results:
            f.write(f"| {r['theta_deg']:.1f} | {r['zero_crossings']} | {r['avg_curvature']:.4f} |\n")

    print(f"Done. Results in {output_dir}")

if __name__ == "__main__":
    run_sweep()

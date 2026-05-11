
import csv
import datetime
import os
import sys
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
    today_str = datetime.date.today().isoformat()
    output_dir = Path(f"outputs/sim/{today_str}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Growth-Posture Sweep in {output_dir}")
    print("Goal: Test stability of Growth-Induced S-shapes (chi_kappa) under varying Posture (Theta).")

    # 2. Define Constant Parameters
    L = 1.0
    n_elements = 50
    final_time = 5.0 # Longer time for growth stability
    dt = 1e-4
    E0 = 1e6
    radius = 0.02
    rho = 1000
    gravity_magnitude = 9.81

    # Info Field: Sinusoidal
    # We want a field that imprints an S-shape via growth
    n_points = 200
    s = np.linspace(0, L, n_points)
    I = np.sin(2 * np.pi * s / L) # Simple Sine
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # Biological Parameters (Fixed)
    # Strong Growth (chi_kappa=12), Anisotropy (0.5), Torsion (0.5)
    # No active muscle (chi_M=0)
    fixed_anisotropy = 0.5
    base_params = CounterCurvatureParams(
        chi_E=0.0,
        chi_kappa=12.0, # Strong growth-driven rest curvature
        chi_M=0.0,      # Passive mechanics only (plus growth)
        chi_tau=0.5,    # Torsional coupling enabled
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
        writer.writerow(["chi_kappa", base_params.chi_kappa])
        writer.writerow(["chi_tau", base_params.chi_tau])
        writer.writerow(["stiffness_anisotropy", fixed_anisotropy])
        writer.writerow(["Description", "Sweep Posture (Theta) on Growth-Driven (chi_kappa) Anisotropic Spine"])

    # 3. Define Sweep: Tilt Angle (theta)
    # Theta = 0 deg: Horizontal (Gravity perpendicular to spine)
    # Theta = 90 deg: Vertical (Gravity parallel to spine)
    # Increased resolution: 10 steps (0, 10, ..., 90)
    theta_values = np.linspace(0, 90, 10)
    results = []
    centerlines = []

    for theta_deg in theta_values:
        theta_rad = np.radians(theta_deg)
        print(f"Running Tilt Theta = {theta_deg:.1f} deg...")

        # Rotate Rod Base Direction in X-Z plane
        # Rod starts along this direction. Gravity is -Z.
        # If theta=0 (Horiz): Rod=(1,0,0), Gravity=(0,0,-1). Cross -> Y bending.
        # If theta=90 (Vert): Rod=(0,0,1), Gravity=(0,0,-1). Parallel -> Buckling.

        base_dir = np.array([np.cos(theta_rad), 0.0, np.sin(theta_rad)])
        normal_dir = np.array([0.0, 1.0, 0.0]) # Y is always normal to X-Z plane

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
            normal=tuple(normal_dir),
            stiffness_anisotropy=fixed_anisotropy
        )

        sim_res = system.run_simulation(final_time=final_time, dt=dt, save_every=500)

        # Analyze
        final_pos = sim_res.centerline[-1] # (n_nodes, 3)

        # We need to compute Lateral Deviation relative to the Rod's Frame.
        # Since rod rotates, global Y is always "Lateral" because we rotate in X-Z.
        # So Global Y deviation is valid lateral deviation.
        lat_dev = np.max(final_pos[:, 1]) - np.min(final_pos[:, 1])

        # Curvature
        curvature = sim_res.curvature[-1] # (n_nodes-1,)
        avg_k = np.mean(curvature)
        max_k = np.max(curvature)

        # Torsion
        torsion = sim_res.torsion[-1]
        avg_tau = np.mean(np.abs(torsion))

        results.append({
            "theta_deg": theta_deg,
            "lateral_dev": lat_dev,
            "avg_curvature": avg_k,
            "max_curvature": max_k,
            "avg_torsion": avg_tau
        })

        centerlines.append((theta_deg, final_pos))

    # 4. Save Results CSV
    csv_path = output_dir / "results.csv"
    keys = results[0].keys()
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    # 5. Plotting
    # Lateral Stability vs Posture
    thetas = [r["theta_deg"] for r in results]
    lats = [r["lateral_dev"] for r in results]
    curvs = [r["avg_curvature"] for r in results]

    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.plot(thetas, lats, 'r-o')
    plt.xlabel("Posture Angle (deg) [0=Horiz, 90=Vert]")
    plt.ylabel("Lateral Deviation (m)")
    plt.title("Lateral Instability (Scoliotic Mode)")
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(thetas, curvs, 'b-s')
    plt.xlabel("Posture Angle (deg)")
    plt.ylabel("Avg Curvature (1/m)")
    plt.title("Sagittal Curvature Retention")
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(output_dir / "plot_posture_growth.png")

    # 6. Report
    report_path = output_dir / "report.md"
    with open(report_path, "w") as f:
        f.write("# Growth-Posture Sweep Report\n\n")
        f.write(f"**Date**: {today_str}\n\n")
        f.write("## Overview\n")
        f.write("Investigated whether growth-induced S-shapes (`chi_kappa=12`) retain their planar form or buckle laterally ")
        f.write("under anisotropic stiffness (`ratio=0.5`) as posture shifts from Horizontal (0°) to Vertical (90°).\n\n")

        f.write("## Results\n")
        f.write("| Theta (deg) | Lateral Dev (m) | Avg Curvature (1/m) | Avg Torsion |\n")
        f.write("|-------------|-----------------|---------------------|-------------|\n")
        for r in results:
            f.write(f"| {r['theta_deg']:.1f} | {r['lateral_dev']:.4f} | {r['avg_curvature']:.4f} | {r['avg_torsion']:.4f} |\n")

        f.write("\n## Findings\n")
        # Logic to infer findings
        max_lat = max(lats)
        max_lat_theta = thetas[lats.index(max_lat)]

        if max_lat > 0.1:
            f.write(f"- **Instability**: Significant lateral deviation ({max_lat:.3f}m) observed at {max_lat_theta:.1f}°.\n")
            f.write("- This suggests that as the spine becomes vertical, the growth-induced planar curve couples with gravity to induce 3D buckling (scoliosis).\n")
        else:
            f.write("- **Stability**: Lateral deviation remained low (<0.1m) across all postures.\n")
            f.write("- The anisotropic stiffness was sufficient to maintain planar growth shapes.\n")

        f.write(f"- **Curvature**: Average curvature {'increased' if curvs[-1] > curvs[0] else 'decreased'} as the spine became vertical.\n")

    print(f"Done. Results in {output_dir}")

if __name__ == "__main__":
    run_sweep()

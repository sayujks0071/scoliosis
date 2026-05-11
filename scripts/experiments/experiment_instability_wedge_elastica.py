"""
Experiment: PyElastica-based Instability Wedge Map.

This script reproduces the "Energy Deficit Window" hypothesis using a fully 3D Cosserat rod
model (PyElastica) instead of a 2D beam solver. It maps the interaction between:

1. Stiffness Anisotropy (Vector Cue): Represents ECM fiber alignment (Fibrillin-1).
   - High Anisotropy (e.g. 5.0) -> Strong Vector.
   - Low Anisotropy (e.g. 1.0) -> Weak Vector (Marfan-like).

2. Preferred Curvature (Scalar Drive): Represents growth/mechanosensing gain (Piezo2).
   - High chi_kappa -> Strong Scalar Drive.
   - Low chi_kappa -> Weak Scalar Drive.

Hypothesis:
A "Wedge" of instability forms where Anisotropy is Low and Curvature Drive is High, leading
to emergent torsion and lateral buckling (Scoliosis).

Measurable Step:
- Generates a phase diagram of Cobb Angle and Max Torsion.
- Measures runtime and memory for performance tracking.
"""

import argparse
import csv
import os
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import List

import numpy as np

# Ensure src is in python path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from spinalmodes.countercurvature.coupling import CounterCurvatureParams
from spinalmodes.countercurvature.info_fields import InfoField1D
from spinalmodes.countercurvature.pyelastica_bridge import (
    CounterCurvatureRodSystem,
    verify_pyelastica_installation,
)


def run_instability_sweep(
    out_file: str,
    anisotropies: List[float],
    chi_kappas: List[float],
    n_elements: int = 50,
    final_time: float = 2.0,
    save_every: int = 5000,
):
    """Run the parameter sweep and save results."""
    verify_pyelastica_installation(exit_on_fail=True)

    print("Running PyElastica Instability Wedge Experiment...")
    print(f"Sweeping Anisotropy: {anisotropies}")
    print(f"Sweeping chi_kappa: {chi_kappas}")
    print(f"Results will be saved to: {out_file}")

    # Ensure output directory exists
    out_dir = os.path.dirname(out_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Rod parameters
    length = 0.5  # meters
    radius = 0.01  # meters
    E0 = 1e6      # Pa
    rho = 1000.0  # kg/m^3
    gravity = 9.81
    dt = 1e-5  # Stable time step

    # Info field (Gaussian bump)
    info_center = 0.6
    info_width = 0.1
    info_amplitude = 0.1

    # Prepare CSV
    fieldnames = [
        "timestamp",
        "stiffness_anisotropy",
        "chi_kappa",
        "max_curvature",
        "max_torsion",
        "cobb_angle",
        "s_lat",
        "bending_energy",
        "runtime_sec",
        "peak_memory_mb"
    ]

    file_exists = os.path.isfile(out_file)

    with open(out_file, mode='a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        print("-" * 100)
        print(
            f"{'Aniso':<8} | {'chi_k':<8} | {'Cobb':<8} | {'Torsion':<9} | "
            f"{'Time (s)':<9} | {'Mem (MB)':<8}"
        )
        print("-" * 100)

        for anisotropy in anisotropies:
            for chi_kappa in chi_kappas:
                # Start tracking
                tracemalloc.start()
                t0 = time.time()

                # 1. Setup Information Field
                s = np.linspace(0, length, n_elements + 1)
                info_density = 0.5 + info_amplitude * np.exp(
                    -0.5 * ((s - info_center * length) / (info_width * length))**2
                )
                dIds = np.gradient(info_density, s)
                info = InfoField1D(s=s, I=info_density, dIds=dIds)

                # 2. Setup Coupling (Pure Scalar Drive)
                params = CounterCurvatureParams(
                    chi_kappa=chi_kappa,
                    chi_tau=0.0,
                    chi_E=0.0,
                    chi_M=0.0,
                    scale_length=length
                )

                # 3. Setup Geometric Curvature (Baseline Sagittal Kyphosis)
                kappa_gen = np.zeros((3, n_elements + 1))
                kappa_gen[0, :] = 2.0  # Sagittal curvature about d1 (X-axis)

                # 4. Create Rod System
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
                    stiffness_anisotropy=anisotropy
                )

                # 5. Run Simulation
                result = rod_system.run_simulation(
                    final_time=final_time,
                    dt=dt,
                    save_every=save_every,
                    gravity=gravity,
                    boundary_condition="fixed",
                    progress_bar=False # Silent for batch
                )

                t1 = time.time()
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                runtime = t1 - t0
                peak_mb = peak / (1024 * 1024)

                # 6. Metrics
                metrics = result.compute_final_metrics()

                row = {
                    "timestamp": datetime.now().isoformat(),
                    "stiffness_anisotropy": anisotropy,
                    "chi_kappa": chi_kappa,
                    "max_curvature": metrics.get('max_curvature', 0.0),
                    "max_torsion": metrics.get('max_torsion', 0.0),
                    "cobb_angle": metrics.get('cobb_angle', 0.0),
                    "s_lat": metrics.get('S_lat', 0.0),
                    "bending_energy": metrics.get('bending_energy', 0.0),
                    "runtime_sec": round(runtime, 4),
                    "peak_memory_mb": round(peak_mb, 2)
                }

                writer.writerow(row)
                csvfile.flush()

                print(
                    f"{anisotropy:<8.2f} | {chi_kappa:<8.2f} | "
                    f"{row['cobb_angle']:<8.2f} | {row['max_torsion']:<9.4f} | "
                    f"{runtime:<9.3f} | {peak_mb:<8.2f}"
                )

    print("-" * 100)
    print("Experiment complete.")
    generate_markdown_report(out_file)


def generate_markdown_report(csv_file: str):
    """Generate a Markdown summary of the experiment."""
    md_file = str(Path(csv_file).with_suffix(".md"))

    with open(md_file, "w") as f:
        f.write("# PyElastica Instability Wedge Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Source:** `{os.path.basename(csv_file)}`\n\n")

        f.write("## Hypothesis Validation\n")
        f.write("We expect higher Cobb angles and torsion in the region of **Low Anisotropy** and **High chi_kappa**.\n\n")

        f.write("| Anisotropy | chi_kappa | Cobb Angle | Max Torsion |\n")
        f.write("|---|---|---|---|\n")

        # Read CSV and populate table (limiting rows if too large)
        with open(csv_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            # Sort by Cobb angle descending to highlight instability
            rows.sort(key=lambda x: float(x['cobb_angle']), reverse=True)

            for r in rows[:20]: # Top 20 unstable cases
                f.write(f"| {float(r['stiffness_anisotropy']):.2f} | {float(r['chi_kappa']):.2f} | {float(r['cobb_angle']):.2f} | {float(r['max_torsion']):.4f} |\n")

    print(f"Report generated: {md_file}")


def parse_args():
    parser = argparse.ArgumentParser(description="Instability Wedge Sweep")
    parser.add_argument(
        "--out-file",
        type=str,
        default="outputs/thermodynamic_cost/phase_diagram_elastica.csv",
        help="Path to output CSV"
    )
    parser.add_argument(
        "--quick-test",
        action="store_true",
        help="Run a minimal test set."
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.quick_test:
        anisotropies = [1.0, 5.0]
        chi_kappas = [0.0, 10.0]
        n_elements = 20
        final_time = 0.1
    else:
        # Full sweep
        anisotropies = [0.5, 1.0, 2.0, 3.0, 5.0]
        chi_kappas = [0.0, 5.0, 10.0, 15.0, 20.0]
        n_elements = 50
        final_time = 2.0

    run_instability_sweep(
        out_file=args.out_file,
        anisotropies=anisotropies,
        chi_kappas=chi_kappas,
        n_elements=n_elements,
        final_time=final_time
    )

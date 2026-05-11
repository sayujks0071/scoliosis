"""
Bio-Gravitational Number Experiment.

This script executes a focused parameter sweep to validate the "Bio-Gravitational Number"
(Bg) hypothesis. Bg is defined as the ratio of active information-driven restoration
to passive gravitational deformation:

    Bg = (chi_M * <|grad I|>) / (rho * A * g * L^2)

We hypothesize that there exists a critical Bg (~1.0) where the system transitions from
gravity-dominated (sagging) to information-dominated (counter-curved/S-shape).

This experiment:
1. Sweeps chi_M (Active Muscle Tone) for a fixed Gravity (g).
2. Calculates Bg for each case.
3. Measures the "Counter-Curvature Efficiency" (reduction in tip sag) and lateral scoliosis indices.
4. Tracks runtime and memory to ensure performance.
"""

import csv
import sys
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np

from src.spinalmodes.countercurvature.coupling import CounterCurvatureParams
from src.spinalmodes.countercurvature.info_fields import InfoField1D

# Execute as module: python -m src.spinalmodes.experiments.bio_gravitational_experiment
from src.spinalmodes.countercurvature.pyelastica_bridge import (
    PYELASTICA_AVAILABLE,
    CounterCurvatureRodSystem,
)
from src.spinalmodes.countercurvature.scoliosis_metrics import compute_scoliosis_metrics

if not PYELASTICA_AVAILABLE:
    print("Error: PyElastica is not installed. Please install it to run this experiment.")
    sys.exit(1)

@dataclass
class BgResult:
    chi_M: float
    gravity: float
    Bg: float
    tip_deflection_z: float
    curvature_energy: float
    S_lat: float # Lateral scoliosis index (if any lateral deviation occurs)
    runtime: float

def run_bg_experiment():
    print("Starting Bio-Gravitational Number (Bg) Experiment...")

    # 1. Configuration
    date_str = time.strftime("%Y-%m-%d")
    output_dir = Path(f"outputs/sim/{date_str}_bg_sweep")
    output_dir.mkdir(parents=True, exist_ok=True)

    L = 1.0
    radius = 0.02
    rho = 1000.0
    A = np.pi * radius**2
    n_elements = 50
    E0 = 1e6
    final_time = 2.0
    dt = 1e-4

    # Information Field: Sinusoidal I = sin(2*pi*s/L)^2
    n_points = 200
    s = np.linspace(0, L, n_points)
    I = np.sin(2 * np.pi * s / L)**2
    dIds = np.gradient(I, s)
    avg_grad_I = np.mean(np.abs(dIds))

    info = InfoField1D(s=s, I=I, dIds=dIds)

    # Sweep Parameters
    gravity = 9.81
    chi_M_values = [0.0, 2.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0]

    results: List[BgResult] = []

    # 2. Execution
    tracemalloc.start()

    for chi_M in chi_M_values:
        iter_start = time.time()

        # Calculate theoretical Bg
        denominator = rho * A * gravity * (L**2)
        bg_val = (chi_M * avg_grad_I) / denominator if denominator > 0 else 0.0

        print(f"Running chi_M={chi_M:.1f}, Bg={bg_val:.4f}...")

        params = CounterCurvatureParams(
            chi_kappa=0.0, # Isolate active moment effect
            chi_E=0.0,
            chi_M=chi_M,
            chi_tau=0.0,
            scale_length=1.0
        )

        # Initialize horizontally to maximize gravity moment
        # base_direction=(1.0, 0.0, 0.0) -> X-axis is longitudinal
        # normal=(0.0, 1.0, 0.0) -> Y-axis is lateral
        # Gravity acts in -Z (default in run_simulation)
        system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=L,
            n_elements=n_elements,
            E0=E0,
            radius=radius,
            rho=rho,
            gravity=gravity,
            base_direction=(1.0, 0.0, 0.0), # X-axis
            normal=(0.0, 1.0, 0.0)
        )

        sim_res = system.run_simulation(final_time=final_time, dt=dt, save_every=500)

        # Analysis
        final_centerline = sim_res.centerline[-1] # (N, 3)
        # Coordinates: X (longitudinal), Y (lateral), Z (vertical/gravity)
        # Note: PyElastica coordinates depend on initialization.
        # With dir=(1,0,0) and gravity -Z:
        # X is axis. Z is deflection. Y is lateral.

        tip_z = final_centerline[-1, 2] # Tip vertical deflection

        # Use existing metrics module
        # compute_scoliosis_metrics(z, y) expects (longitudinal, lateral)
        # Here: longitudinal is X (index 0), lateral is Y (index 1).
        x_coords = final_centerline[:, 0]
        y_coords = final_centerline[:, 1]
        metrics = compute_scoliosis_metrics(x_coords, y_coords)

        # Curvature energy (proxy): integral of curvature^2
        curv = sim_res.curvature[-1] # (N,)
        energy = np.sum(curv**2)

        iter_time = time.time() - iter_start

        results.append(BgResult(
            chi_M=chi_M,
            gravity=gravity,
            Bg=bg_val,
            tip_deflection_z=tip_z,
            curvature_energy=energy,
            S_lat=metrics.S_lat,
            runtime=iter_time
        ))

    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 3. Output
    print("\nExperiment Complete.")
    print(f"Peak Memory: {peak_mem / 1024 / 1024:.2f} MB")

    csv_path = output_dir / "bg_sweep_results.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["chi_M", "gravity", "Bg", "tip_deflection_z", "curvature_energy", "S_lat", "runtime"])
        for r in results:
            writer.writerow([r.chi_M, r.gravity, r.Bg, r.tip_deflection_z, r.curvature_energy, r.S_lat, r.runtime])

    report_path = output_dir / "report.md"
    with open(report_path, "w") as f:
        f.write("# Bio-Gravitational Number (Bg) Experiment\n\n")
        f.write(f"**Date**: {date_str}\n\n")
        f.write("## Hypothesis\n")
        f.write("Increasing Bg (via chi_M) reduces gravitational sagging (negative Z deflection).\n\n")
        f.write("## Results\n\n")
        f.write("| chi_M | Bg | Tip Deflection (m) | Curvature Energy | S_lat | Runtime (s) |\n")
        f.write("|-------|----|--------------------|------------------|-------|-------------|\n")
        for r in results:
            f.write(f"| {r.chi_M:.1f} | {r.Bg:.4f} | {r.tip_deflection_z:.4f} | {r.curvature_energy:.2f} | {r.S_lat:.4f} | {r.runtime:.2f} |\n")

        f.write("\n\n## Interpretation\n")
        base_sag = results[0].tip_deflection_z
        f.write(f"Baseline passive sag: {base_sag:.4f} m\n")

        # Find critical Bg where sag is halved?
        for r in results:
            if r.tip_deflection_z > base_sag / 2.0:
                 f.write(f"- At Bg={r.Bg:.4f}, sag is reduced by >50% (Tip: {r.tip_deflection_z:.4f}).\n")
                 break

    print(f"Results saved to {output_dir}")

if __name__ == "__main__":
    run_bg_experiment()

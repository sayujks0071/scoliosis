"""
Integrated Rod Experiment: Biological Counter-Curvature

This script implements a unified parameter sweep for the Counter-Curvature hypothesis,
mapping biological proxies (Protein Anisotropy, ECM Stiffness, Muscle Activation)
to physical rod parameters (chi_kappa, chi_E, chi_M) and measuring emergent
geometric outputs (Curvature, Torsion, Scoliosis Index).

It fulfills the requirement to:
1. Map protein/ECM parameters to rod mechanics.
2. Produce reproducible, minimal experiments.
3. Measure runtime/memory.
4. Verify PyElastica integration.
"""

import csv
import sys
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src.spinalmodes.countercurvature.coupling import CounterCurvatureParams
from src.spinalmodes.countercurvature.info_fields import InfoField1D

# To run this script, execute it as a module from the project root:
# python -m src.spinalmodes.experiments.integrated_rod_experiment
from src.spinalmodes.countercurvature.pyelastica_bridge import (
    PYELASTICA_AVAILABLE,
    CounterCurvatureRodSystem,
)
from src.spinalmodes.countercurvature.scoliosis_metrics import compute_scoliosis_metrics

if not PYELASTICA_AVAILABLE:
    print("Error: PyElastica is not installed. Please install it to run this experiment.")
    sys.exit(1)

@dataclass
class BiologicalScenario:
    name: str
    protein_anisotropy_score: float # 0-10 (Maps to chi_kappa)
    ecm_integrity_score: float      # 0-10 (Maps to chi_E)
    muscle_tone_score: float        # 0-10 (Maps to chi_M)
    pcp_defect_score: float         # 0-10 (Maps to chi_tau)
    gravity: float = 9.81           # m/s^2

def map_bio_to_physics(bio: BiologicalScenario, L: float = 1.0) -> CounterCurvatureParams:
    """
    Maps biological scores to non-dimensional coupling parameters.

    Mapping Logic:
    - chi_kappa (Preferred Curvature) ~ Anisotropy * 0.5
    - chi_E (Stiffness Modulation)    ~ ECM Integrity * 1.0
    - chi_M (Active Moment)           ~ Muscle Tone * 2.0
    - chi_tau (Torsion)               ~ PCP Defect * 0.2
    """
    return CounterCurvatureParams(
        chi_kappa=bio.protein_anisotropy_score * 0.5,
        chi_E=bio.ecm_integrity_score * 1.0,
        chi_M=bio.muscle_tone_score * 2.0,
        chi_tau=bio.pcp_defect_score * 0.2,
        scale_length=L
    )

def run_integrated_experiment():
    print("Starting Integrated Rod Experiment...")

    # 1. Setup
    date_str = time.strftime("%Y-%m-%d")
    output_dir = Path(f"outputs/sim/{date_str}_integrated")
    output_dir.mkdir(parents=True, exist_ok=True)

    L = 1.0
    n_elements = 50
    final_time = 2.0
    dt = 1e-4

    # Information Field: Standard Sinusoidal
    n_points = 200
    s = np.linspace(0, L, n_points)
    I = np.sin(2 * np.pi * s / L)**2
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # 2. Define Scenarios
    scenarios = [
        BiologicalScenario("Healthy_Earth", 8.0, 8.0, 8.0, 0.0, 9.81),
        BiologicalScenario("Microgravity_Unloaded", 8.0, 6.0, 2.0, 0.0, 0.001), # Small gravity to define 'down'
        BiologicalScenario("Scoliosis_Candidate", 4.0, 8.0, 4.0, 8.0, 9.81),
        BiologicalScenario("Degenerative_Weak", 2.0, 2.0, 1.0, 0.0, 9.81),
        BiologicalScenario("Therapeutic_Rescue", 8.0, 8.0, 10.0, 2.0, 9.81)
    ]

    results = []

    tracemalloc.start()
    start_time_total = time.time()

    for sc in scenarios:
        print(f"Running Scenario: {sc.name}...")
        params = map_bio_to_physics(sc, L)

        # Horizontal initialization to test sag resistance
        system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=L,
            n_elements=n_elements,
            E0=1e6,
            radius=0.02,
            rho=1000,
            gravity=sc.gravity,
            base_direction=(1.0, 0.0, 0.0), # X-axis
            normal=(0.0, 1.0, 0.0)
        )

        sim_res = system.run_simulation(final_time=final_time, dt=dt, save_every=500)

        # Analysis
        final_centerline = sim_res.centerline[-1] # (3, N) -> Need to verify shape.
        # pyelastica_bridge output logic:
        # system.position_collection is (3, n_nodes).
        # Bridge returns centerline as np.array(results["centerline"])
        # results["centerline"] appends system.position_collection.copy().T -> (n_nodes, 3)
        # So final_centerline is (n_nodes, 3)

        x_coords = final_centerline[:, 0]
        y_coords = final_centerline[:, 1] # Lateral (if any twist rotates it)
        z_coords = final_centerline[:, 2] # Vertical (Gravity acts in -Z)

        # Use Scoliosis Metrics (projected to X-Y 'coronal' if we treat X as longitudinal for horizontal rod?)
        # For horizontal rod: X is longitudinal, Z is Sagittal (Gravity), Y is Lateral.
        # compute_scoliosis_metrics(z, y) expects z=longitudinal, y=lateral.
        metrics = compute_scoliosis_metrics(x_coords, y_coords)

        tip_sag_z = z_coords[-1]
        max_torsion = np.max(np.abs(sim_res.torsion[-1]))
        avg_curvature = np.mean(sim_res.curvature[-1])

        results.append({
            "scenario": sc.name,
            "bio_aniso": sc.protein_anisotropy_score,
            "bio_muscle": sc.muscle_tone_score,
            "phys_chi_M": params.chi_M,
            "tip_sag_z": tip_sag_z,
            "S_lat": metrics.S_lat,
            "cobb_angle": metrics.cobb_like_deg,
            "max_torsion": max_torsion,
            "avg_curvature": avg_curvature
        })

    end_time_total = time.time()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 3. Reporting
    print(f"\nTotal Runtime: {end_time_total - start_time_total:.2f}s")
    print(f"Peak Memory: {peak_mem / 1024 / 1024:.2f} MB")

    csv_path = output_dir / "integrated_results.csv"
    keys = results[0].keys()
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    report_path = output_dir / "report.md"
    with open(report_path, "w") as f:
        f.write("# Integrated Rod Experiment: Biological Scenarios\n\n")
        f.write(f"**Date**: {date_str}\n\n")
        f.write("## Overview\n")
        f.write("Mapping biological scores (0-10) to physical parameters to predict spinal geometry.\n\n")

        f.write("## Results\n\n")
        f.write("| Scenario | Aniso | Muscle | Tip Sag Z | S_lat | Cobb | Torsion |\n")
        f.write("|----------|-------|--------|-----------|-------|------|---------|\n")
        for r in results:
            f.write(f"| {r['scenario']} | {r['bio_aniso']} | {r['bio_muscle']} | {r['tip_sag_z']:.4f} | {r['S_lat']:.4f} | {r['cobb_angle']:.2f} | {r['max_torsion']:.4f} |\n")

    print(f"Results saved to {output_dir}")

if __name__ == "__main__":
    run_integrated_experiment()

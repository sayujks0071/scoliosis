#!/usr/bin/env python3
"""
Minimal reproducible experiment: Protein-Driven Countercurvature Physics.

This script maps protein-inspired parameters (ECM Stiffness Anisotropy, Piezo2 Active Curvature)
to emergent spinal geometry (Cobb Angle, Kyphosis, Torsion) using the PyElastica Cosserat rod solver.

It performs a parameter sweep and saves metrics to 'outputs/protein_physics/experiment_results.csv'.
"""

import sys
import time
from pathlib import Path

import pandas as pd

# Ensure src is in python path
current_dir = Path(__file__).resolve().parent
src_path = current_dir.parent / "src"
sys.path.append(str(src_path))

try:
    from spinalmodes.countercurvature.pyelastica_bridge import (
        PYELASTICA_AVAILABLE,
        run_protein_simulation,
    )
except ImportError as e:
    print(f"Error importing simulation bridge: {e}")
    print("Ensure you are running from the repo root or have installed the package.")
    sys.exit(1)

def main():
    if not PYELASTICA_AVAILABLE:
        print("ERROR: PyElastica is not installed but is required for this experiment.")
        print("To install, run:")
        print("    pip install pyelastica")
        print("Or visit: https://github.com/GazzolaLab/PyElastica")
        sys.exit(1)

    print(">>> Starting Protein Physics Experiment (PyElastica)")
    output_dir = Path("outputs/protein_physics")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "experiment_results.csv"

    # --- Parameter Sweep Definition ---
    # 1. Anisotropy (A): Ratio of Lateral/Sagittal Stiffness.
    #    Biological proxy: Collagen fiber alignment (Vimentin/Col1a1 organization).
    #    Range: 1.0 (Isotropic/Disordered) to 4.0 (Highly Aligned).
    anisotropy_levels = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]

    # 2. Active Curvature (C): Magnitude of active bending drive.
    #    Biological proxy: Piezo2-mediated ion flux / Proprioceptive drive.
    #    Range: 0.0 (Passive) to 2.0 (Strong Active Drive).
    active_curvature_levels = [0.0, 0.5, 1.0, 1.5, 2.0]

    # 3. Torsion Drive (T): Magnitude of active twisting drive.
    #    Biological proxy: Asymmetric growth or chiral packing in ECM.
    torsion_levels = [0.0, 0.5, 1.0]

    # Fixed Parameters
    stiffness_modulation = 0.0   # Uniform stiffness for now
    initial_lateral_defect = 0.05 # Small perturbation to seed symmetry breaking (5% curvature)

    results = []

    total_runs = len(anisotropy_levels) * len(active_curvature_levels) * len(torsion_levels)
    count = 0

    start_time_global = time.time()

    print(f"Running {total_runs} simulations...")
    print(f"{'Aniso (A)':<10} | {'ActCurv (C)':<12} | {'TorDrive (T)':<13} | {'Cobb (deg)':<10} | {'MaxTorsion':<10} | {'Energy (J)':<10} | {'Time (s)':<8} | {'Mem (MB)':<8}")
    print("-" * 105)

    for A in anisotropy_levels:
        for C in active_curvature_levels:
            for T in torsion_levels:
                count += 1

                # Run Simulation
                # using default duration=2.0s, dt=1e-4, n_elements=50
                sim_output = run_protein_simulation(
                    anisotropy=A,
                    active_curvature=C,
                    torsion_drive=T,
                    stiffness_modulation=stiffness_modulation,
                    initial_lateral_defect=initial_lateral_defect,
                    show_progress=False  # Keep stdout clean
                )

                # Collect Metrics
                if sim_output.get("success"):
                    cobb = sim_output.get("cobb_angle", 0.0)
                    energy = sim_output.get("U_CC", 0.0)
                    runtime = sim_output.get("runtime_sec", 0.0)
                    memory = sim_output.get("peak_memory_mb", 0.0)
                    max_torsion = sim_output.get("max_torsion", 0.0)

                    print(f"{A:<10.1f} | {C:<12.1f} | {T:<13.1f} | {cobb:<10.2f} | {max_torsion:<10.4f} | {energy:<10.4f} | {runtime:<8.2f} | {memory:<8.2f}")

                    results.append({
                        "anisotropy": A,
                        "active_curvature": C,
                        "torsion_drive": T,
                        "cobb_angle": cobb,
                        "max_curvature": sim_output.get("max_curvature"),
                        "max_torsion": max_torsion,
                        "U_CC": energy,
                        "U_elastic": sim_output.get("U_elastic"),
                        "U_info": sim_output.get("U_info"),
                        "runtime_sec": runtime,
                        "peak_memory_mb": memory
                    })
                else:
                    print(f"{A:<10.1f} | {C:<12.1f} | {T:<13.1f} | {'FAILED':<10} | {'N/A':<10} | {'N/A':<10} | {'N/A':<8} | {'N/A':<8}")
                    results.append({
                        "anisotropy": A,
                        "active_curvature": C,
                        "torsion_drive": T,
                        "error": sim_output.get("error")
                    })

    # Save Results
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)

    end_time_global = time.time()
    total_time = end_time_global - start_time_global

    print("-" * 70)
    print(f"Experiment completed in {total_time:.2f} seconds.")
    print(f"Results saved to: {output_csv}")

if __name__ == "__main__":
    main()

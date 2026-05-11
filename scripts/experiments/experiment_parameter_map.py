"""
PyElastica Parameter Map Experiment

This script maps protein/ECM-inspired parameters to emergent curvature/torsion outputs
using the Counter-Curvature Rod System.

It performs a parameter sweep over:
1. Stiffness Anisotropy (Simulating 'Rod' vs 'Block' protein clusters)
2. Preferred Curvature (Simulating intrinsic developmental curvature)
3. Boundary Conditions (Simulating different anchoring constraints)

Results are saved to `outputs/parameter_map_results.csv`.
"""

import os
import sys
import time
import tracemalloc
from itertools import product

import numpy as np
import pandas as pd

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

try:
    import elastica
except ImportError:
    print("PyElastica is not installed.")
    print("This experiment requires PyElastica to run rod simulations.")
    print("To install, run:")
    print("  pip install pyelastica")
    print("  # OR")
    print("  pip install -r requirements.txt")
    print("\nPlan to proceed without PyElastica:")
    print("1. Install PyElastica using the instructions above.")
    print("2. Re-run this script.")
    sys.exit(0)

from spinalmodes.countercurvature.coupling import CounterCurvatureParams
from spinalmodes.countercurvature.info_fields import InfoField1D
from spinalmodes.countercurvature.pyelastica_bridge import CounterCurvatureRodSystem


def run_experiment():
    print("Running PyElastica Parameter Map Experiment...")
    print("Mapping: Stiffness Anisotropy, Preferred Curvature, Boundary Conditions -> Emergent Metrics")

    # Define Parameter Space
    # ----------------------

    # 1. Stiffness Anisotropy: Ratio of Stiffness about d1 vs d2.
    # We scale bend_matrix[0,0] (Rotation about d1 -> Sagittal Bending) by this factor.
    # Anisotropy > 1.0: Stiffer in Sagittal plane (Ribbon-like).
    # High anisotropy (~10.0) corresponds to "Cluster 0" (Tension Rods, e.g., POC5).
    # Low anisotropy (~1.0) corresponds to "Cluster 1" (Signaling Blocks, e.g., YAP1).
    anisotropies = [1.0, 5.0, 10.0]

    # 2. Preferred Curvature (kappa_gen): Intrinsic curvature in 1/m about d1 (Sagittal).
    # 0.0: Straight rod.
    # 2.0: Moderate curvature (e.g., physiological lordosis/kyphosis).
    # 5.0: High curvature (potentially pathological or strong developmental drive).
    curvatures = [0.0, 2.0, 5.0]

    # 3. Boundary Conditions:
    # "fixed": Clamped at base (position and rotation fixed). Like strong sacral anchoring.
    # "pinned": Pinned at base (position fixed, rotation free). Weaker anchoring/ball-joint.
    bcs = ["fixed", "pinned"]

    # Rod parameters (Human Spine Scale)
    length = 0.5  # meters
    radius = 0.01 # meters
    n_elements = 30 # Reduced for minimal experiment speed
    E0 = 1e6      # Pa (Soft tissue/cartilage range)
    rho = 1000.0  # kg/m^3
    gravity = 9.81

    # Time parameters
    final_time = 1.0 # Sufficient to see trends
    dt = 4e-5 # Stable time step (Conservative: dl=0.5/30=0.016, c=31.6, dt_crit~5e-4)

    results = []

    # Iterate over all combinations
    total_runs = len(anisotropies) * len(curvatures) * len(bcs)
    run_count = 0

    print(f"Total simulations to run: {total_runs}")
    print("-" * 120)
    print(f"{'Run':<4} | {'Aniso':<6} | {'Kappa':<6} | {'BC':<8} | {'MaxCurv':<8} | {'MaxTor':<8} | {'Z-Tip':<8} | {'Cobb':<8} | {'Time(s)':<8} | {'Mem(MB)':<8}")
    print("-" * 120)

    for aniso, kappa, bc in product(anisotropies, curvatures, bcs):
        run_count += 1

        # Start tracking resources
        tracemalloc.start()
        t0 = time.time()

        try:
            # 1. Setup Information Field (Baseline: Uniform)
            s = np.linspace(0, length, n_elements + 1)
            I = np.ones_like(s) * 0.5
            dIds = np.zeros_like(s)
            info = InfoField1D(s=s, I=I, dIds=dIds)

            # 2. Setup Coupling Parameters
            params = CounterCurvatureParams(
                chi_kappa=0.0,
                chi_E=0.0,
                chi_M=0.0,
                scale_length=length
            )

            # 3. Setup Geometric Curvature
            # Constant curvature about d1 (Normal) -> Sagittal Bending
            kappa_gen_arr = np.zeros((3, n_elements + 1))
            kappa_gen_arr[0, :] = kappa

            # 4. Create Rod System
            rod_system = CounterCurvatureRodSystem.from_iec(
                info=info,
                params=params,
                length=length,
                n_elements=n_elements,
                E0=E0,
                rho=rho,
                radius=radius,
                kappa_gen=kappa_gen_arr,
                gravity=gravity,
                base_position=(0.0, 0.0, 0.0),
                base_direction=(0.0, 0.0, 1.0), # Vertical (+Z)
                normal=(1.0, 0.0, 0.0),         # Normal along +X
                stiffness_anisotropy=aniso
            )

            # 5. Run Simulation
            result = rod_system.run_simulation(
                final_time=final_time,
                dt=dt,
                save_every=int(final_time/dt), # Save only final state to save memory
                gravity=gravity,
                boundary_condition=bc
            )

            # 6. Compute Metrics
            metrics = result.compute_final_metrics()

            # Resource measurement
            t1 = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            runtime = t1 - t0
            peak_mb = peak / (1024 * 1024)

            # Record Result
            res_row = {
                "stiffness_anisotropy": aniso,
                "preferred_curvature": kappa,
                "boundary_condition": bc,
                "max_curvature": metrics.get("max_curvature", np.nan),
                "max_torsion": metrics.get("max_torsion", np.nan),
                "z_tip": metrics.get("z_tip", np.nan),
                "s_lat": metrics.get("S_lat", np.nan),
                "cobb_angle": metrics.get("cobb_angle", np.nan),
                "runtime_sec": runtime,
                "peak_memory_mb": peak_mb
            }
            results.append(res_row)

            # Print Progress
            print(f"{run_count:<4} | {aniso:<6.1f} | {kappa:<6.1f} | {bc:<8} | "
                  f"{res_row['max_curvature']:<8.4f} | {res_row['max_torsion']:<8.4f} | "
                  f"{res_row['z_tip']:<8.4f} | {res_row['cobb_angle']:<8.4f} | "
                  f"{runtime:<8.2f} | {peak_mb:<8.2f}")

        except Exception as e:
            print(f"Run {run_count} failed: {e}")
            if tracemalloc.is_tracing():
                tracemalloc.stop()

    print("-" * 120)

    # Save to CSV
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "parameter_map_results.csv")

    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    run_experiment()

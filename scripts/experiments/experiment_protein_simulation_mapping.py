#!/usr/bin/env python3
"""
Experiment: Protein Simulation Mapping

This script performs a parameter sweep over stiffness anisotropy (ECM metric) and
active curvature (Piezo/Ion metric) to map emergent spinal geometries.

It generates a CSV file containing geometric and energetic metrics for each simulation.

Usage:
    python3 experiment_protein_simulation_mapping.py [--test-mode]
"""

import argparse
import itertools
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

# Ensure src is in path
current_dir = Path(__file__).resolve().parent
src_path = current_dir.parent.parent / "src"
sys.path.append(str(src_path))

try:
    from spinalmodes.countercurvature.pyelastica_bridge import run_protein_simulation
except ImportError as e:
    print(f"Error importing simulation bridge: {e}")
    print("Please ensure you are running from the repo root or have set up paths correctly.")
    sys.exit(1)

def run_experiment(test_mode: bool = False):
    """Run the parameter sweep experiment."""

    output_dir = current_dir.parent.parent / "outputs" / "experiments"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "protein_simulation_mapping.csv"

    print("Starting Protein Simulation Mapping Experiment...")
    print(f"Output will be saved to: {output_file}")

    # Parameter Grid
    if test_mode:
        print(">>> RUNNING IN TEST MODE (Minimal Grid) <<<")
        anisotropy_levels = [1.0, 5.0]
        active_curvature_levels = [0.0, 1.0]
        duration = 0.5  # Short duration for test
        n_elements = 20 # Low resolution
    else:
        # Full Grid
        anisotropy_levels = [1.0, 2.0, 3.0, 5.0, 10.0, 15.0]
        active_curvature_levels = [0.0, 0.2, 0.5, 0.8, 1.0, 1.5, 2.0]
        duration = 2.0  # Full duration
        n_elements = 50 # Standard resolution

    # Cartesian Product of parameters
    param_grid = list(itertools.product(anisotropy_levels, active_curvature_levels))

    results = []

    with tqdm(total=len(param_grid), desc="Simulations") as pbar:
        for anisotropy, active_curv in param_grid:

            # Run simulation
            sim_result = run_protein_simulation(
                anisotropy=anisotropy,
                active_curvature=active_curv,
                n_elements=n_elements,
                duration=duration,
                show_progress=False, # Don't nest progress bars
                initial_lateral_defect=0.02, # Small seed defect
                natural_kyphosis=2.0
            )

            if sim_result.get("success", False):
                # Extract key metrics
                row = {
                    "anisotropy": anisotropy,
                    "active_curvature": active_curv,
                    "max_curvature": sim_result.get("max_curvature"),
                    "max_torsion": sim_result.get("max_torsion"),
                    "S_lat": sim_result.get("S_lat"),
                    "cobb_angle": sim_result.get("cobb_angle"),
                    "U_CC": sim_result.get("U_CC"),
                    "U_info": sim_result.get("U_info"),
                    "info_gain_ratio": sim_result.get("info_gain_ratio"),
                    "runtime_sec": sim_result.get("runtime_sec")
                }
                results.append(row)
            else:
                print(f"Simulation failed for A={anisotropy}, C={active_curv}: {sim_result.get('error')}")

            pbar.update(1)

    # Save to CSV
    if results:
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False)
        print(f"Experiment completed. {len(df)} simulations successful.")
        print(f"Results saved to {output_file}")
    else:
        print("Experiment failed. No results generated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Protein Simulation Mapping Experiment")
    parser.add_argument("--test-mode", action="store_true", help="Run a minimal test set")
    args = parser.parse_args()

    run_experiment(test_mode=args.test_mode)

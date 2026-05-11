"""
Minimal, Reproducible PyElastica Experiment Script.

This script implements a "minimal experiment" that maps protein/ECM-inspired
parameters (stiffness anisotropy, preferred curvature) to emergent curvature/torsion
outputs using a vertical rod model.

It is designed to be self-contained (handling paths) and robust.
"""

import argparse
import csv
import sys
import time
from pathlib import Path

# Removed tracemalloc from outer script as run_protein_simulation handles it internally

# Ensure src is in python path
# This handles execution from repo root or scripts/ dir
current_file = Path(__file__).resolve()
# Assuming this script is at scripts/experiments/experiment_pyelastica_minimal.py
# src is at ../../../src relative to this file
src_path = current_file.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

try:
    from spinalmodes.countercurvature.pyelastica_bridge import (
        PYELASTICA_AVAILABLE,
        run_protein_simulation,
    )
except ImportError as e:
    print(f"Error importing spinalmodes: {e}")
    sys.exit(1)

def run_experiment(
    out_dir: str = "outputs/minimal_experiment",
    quick_test: bool = False
):
    """
    Run the minimal experiment parameter sweep.

    Parameters:
    - out_dir: Directory to save results.
    - quick_test: If True, runs a very small sweep for testing purposes.
    """
    if not PYELASTICA_AVAILABLE:
        print("Error: PyElastica is not installed.")
        sys.exit(1)

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    csv_file = out_path / "results.csv"
    md_file = out_path / "report.md"

    print(f"Starting experiment. Results will be saved to {out_path}")

    # Define sweep parameters
    if quick_test:
        anisotropies = [1.0, 5.0]
        active_curvatures = [0.0, 5.0]
        boundary_conditions = ["fixed", "pinned"]
        stiffness_modulations = [0.0, 0.5]
        n_elements = 20
        duration = 0.5
    else:
        anisotropies = [1.0, 2.0, 5.0, 10.0]
        active_curvatures = [0.0, 2.0, 5.0, 10.0, 20.0]
        boundary_conditions = ["fixed", "pinned"]
        stiffness_modulations = [0.0, 0.5]
        n_elements = 50
        duration = 2.0

    # Fixed parameters
    radius = 0.01
    E0 = 1e6
    gravity = 9.81
    dt = 1e-4
    initial_lateral_defect = 0.02

    results = []

    # Header for console output
    print(f"{'BC':<8} | {'Mod':<5} | {'Aniso':<6} | {'Active':<6} | {'S_lat':<8} | {'Cobb':<6} | {'Max K':<6} | {'Time':<6}")
    print("-" * 80)

    start_time_all = time.time()
    max_peak_memory = 0.0

    for bc in boundary_conditions:
        for mod in stiffness_modulations:
            for anisotropy in anisotropies:
                for active_curvature in active_curvatures:

                    # Map active_curvature (0-20) to chi_kappa via scale_factor
                    # We use scale_factor_kappa=1.0 for direct control if we want,
                    # or rely on the default mapping. Let's use the function's scaling.
                    # run_protein_simulation uses: chi_kappa = active_curvature * scale_factor_kappa
                    # Default scale_factor_kappa is 5.0.
                    # So input 0.0 -> chi_kappa 0.0
                    # Input 10.0 -> chi_kappa 50.0 (very strong)

                    # Let's assume active_curvature here is the "protein level" input.

                    result = run_protein_simulation(
                        anisotropy=anisotropy,
                        active_curvature=active_curvature,
                        boundary_condition=bc,
                        stiffness_modulation=mod,
                        initial_lateral_defect=initial_lateral_defect,
                        radius=radius,
                        E0=E0,
                        n_elements=n_elements,
                        duration=duration,
                        dt=dt,
                        gravity=gravity,
                        show_progress=False
                    )

                    if not result.get("success", False):
                        print(f"Failed for A={anisotropy}, C={active_curvature}, BC={bc}, Mod={mod}: {result.get('error')}")
                        continue

                    # Track peak memory across all runs
                    run_peak_mem = result.get("peak_memory_mb", 0.0)
                    if run_peak_mem > max_peak_memory:
                        max_peak_memory = run_peak_mem

                    # Store result
                    row = {
                        "boundary_condition": bc,
                        "stiffness_modulation": mod,
                        "anisotropy": anisotropy,
                        "active_curvature": active_curvature,
                        "initial_lateral_defect": initial_lateral_defect,
                        "radius": radius,
                        "E0": E0,
                        **result
                    }
                    results.append(row)

                    print(
                        f"{bc:<8} | {mod:<5.1f} | {anisotropy:<6.1f} | {active_curvature:<6.1f} | "
                        f"{result.get('S_lat', 0.0):<8.4f} | {result.get('cobb_angle', 0.0):<6.1f} | "
                        f"{result.get('max_curvature', 0.0):<6.2f} | "
                        f"{result.get('runtime_sec', 0.0):<6.2f}"
                    )

    total_time = time.time() - start_time_all
    print("-" * 70)
    print(f"Total experiment time: {total_time:.2f} s")
    print(f"Max Peak memory usage (single run): {max_peak_memory:.2f} MB")

    # Save to CSV
    if results:
        keys = list(results[0].keys())
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        print(f"Results saved to {csv_file}")

        # Generate Report
        generate_report(md_file, results, total_time, max_peak_memory)
        print(f"Report saved to {md_file}")

def generate_report(md_file, results, total_time, peak_mb):
    """Generate a Markdown summary."""
    with open(md_file, "w") as f:
        f.write("# Minimal PyElastica Experiment Report\n\n")
        f.write(f"**Total Time:** {total_time:.2f} s\n")
        f.write(f"**Max Peak Memory (Single Run):** {peak_mb:.2f} MB\n\n")

        f.write("| BC | Mod | Anisotropy | Active Curv | S_lat | Cobb (deg) | Max Curv | Max Torsion | Runtime (s) |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")

        for r in results:
            f.write(
                f"| {r['boundary_condition']} | {r['stiffness_modulation']:.1f} | "
                f"{r['anisotropy']:.2f} | {r['active_curvature']:.2f} | "
                f"{r.get('S_lat', 0.0):.4f} | {r.get('cobb_angle', 0.0):.2f} | "
                f"{r.get('max_curvature', 0.0):.2f} | "
                f"{r.get('max_torsion', 0.0):.4f} | {r.get('runtime_sec', 0.0):.4f} |\n"
            )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run minimal PyElastica experiment.")
    parser.add_argument("--quick", action="store_true", help="Run a quick smoke test.")
    parser.add_argument("--out-dir", type=str, default="outputs/minimal_experiment", help="Output directory.")
    args = parser.parse_args()

    run_experiment(out_dir=args.out_dir, quick_test=args.quick)

"""
Experiment: PyElastica Curvature Mapping

This script produces a reproducible minimal experiment mapping protein/ECM-inspired
parameters (Stiffness Anisotropy, Active Curvature) to emergent curvature/torsion outputs
using a PyElastica-based Cosserat rod simulation.

It leverages `StandardExperimentParser` to ensure consistent CLI arguments, output
directory structure (e.g. `outputs/sim/{YYYY-MM-DD}/`), and reproducibility (saving config).
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure src is in python path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from experiment_utils import StandardExperimentParser, setup_experiment

try:
    from spinalmodes.countercurvature.pyelastica_bridge import (
        PYELASTICA_AVAILABLE,
        run_protein_simulation,
    )
except ImportError as e:
    # Handle absolute failure to import core modules
    print(f"CRITICAL ERROR: Failed to import spinalmodes modules. {e}")
    sys.exit(1)


def parse_args():
    # Force a unique default output directory to prevent collisions with other same-day experiments
    today = datetime.now().strftime("%Y-%m-%d")
    unique_out_dir = str(Path(f"outputs/sim/{today}_pyelastica"))

    parser = StandardExperimentParser(
        description="Map protein parameters to curvature using PyElastica.",
        default_out_dir=unique_out_dir
    )

    parser.add_argument(
        "--anisotropy",
        type=float,
        nargs="+",
        default=[1.0, 3.0, 5.0],
        help="Stiffness anisotropy values."
    )
    parser.add_argument(
        "--active-curvature",
        type=float,
        nargs="+",
        default=[0.5, 2.0, 4.0],
        help="Active curvature values."
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Check for PyElastica before doing anything else
    if not PYELASTICA_AVAILABLE:
        print("PyElastica is not installed in the current environment.")
        print("Minimal install/activation instructions:")
        print("  pip install pyelastica")
        print("\nPlan: Keeping dependencies unchanged as requested. Exiting gracefully.")
        sys.exit(0)

    # 2. Setup standard experiment directory
    out_dir = setup_experiment(args)

    # Apply quick mode if requested
    anisotropies = args.anisotropy
    active_curvatures = args.active_curvature
    n_elements = 50
    duration = 2.0
    dt = 1e-4

    if args.quick:
        print("Running in quick mode...")
        anisotropies = [1.0, 5.0]
        active_curvatures = [1.0]
        n_elements = 20
        duration = 0.1
        dt = 5e-4

    # 3. Save configuration for reproducibility
    config = {
        "timestamp": datetime.now().isoformat(),
        "anisotropy_sweep": anisotropies,
        "active_curvature_sweep": active_curvatures,
        "n_elements": n_elements,
        "duration": duration,
        "dt": dt,
        "quick_mode": args.quick,
        "seed": 42 # For reproducibility documentation
    }

    with open(out_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)

    # 4. Prepare output CSV
    results_file = out_dir / "results.csv"
    fieldnames = [
        "input_anisotropy",
        "input_active_curvature",
        "cobb_angle",
        "max_curvature",
        "max_torsion",
        "s_lat",
        "u_cc",
        "runtime_sec",
        "peak_memory_mb",
        "success"
    ]

    results = []

    with open(results_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # 5. Run parameter sweep
        print(f"Starting parameter sweep: {len(anisotropies)} anisotropies x {len(active_curvatures)} active curvatures")
        print("-" * 100)
        print(f"{'Anisotropy':<15} | {'Active Curv':<15} | {'Cobb':<10} | {'S_lat':<10} | {'Runtime (s)':<12} | {'Memory (MB)'}")
        print("-" * 100)

        for a in anisotropies:
            for c in active_curvatures:
                # Call the PyElastica wrapper (measures runtime and memory internally)
                res = run_protein_simulation(
                    anisotropy=a,
                    active_curvature=c,
                    n_elements=n_elements,
                    duration=duration,
                    dt=dt,
                    show_progress=False
                )

                # Extract requested fields
                row = {
                    "input_anisotropy": a,
                    "input_active_curvature": c,
                    "cobb_angle": res.get("cobb_angle", 0.0),
                    "max_curvature": res.get("max_curvature", 0.0),
                    "max_torsion": res.get("max_torsion", 0.0),
                    "s_lat": res.get("S_lat", 0.0),
                    "u_cc": res.get("U_CC", 0.0),
                    "runtime_sec": res.get("runtime_sec", 0.0),
                    "peak_memory_mb": res.get("peak_memory_mb", 0.0),
                    "success": res.get("success", False)
                }

                writer.writerow(row)
                csvfile.flush()
                results.append(row)

                print(
                    f"{a:<15.1f} | {c:<15.1f} | {row['cobb_angle']:<10.4f} | "
                    f"{row['s_lat']:<10.4f} | {row['runtime_sec']:<12.3f} | {row['peak_memory_mb']:.2f}"
                )

    print("-" * 100)
    print(f"Experiment complete. Results saved to: {results_file}")

    # 6. Generate minimal markdown report
    report_file = out_dir / "report.md"
    with open(report_file, "w") as f:
        f.write("# PyElastica Curvature Mapping\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Overview\n")
        f.write("Mapped protein/ECM-inspired parameters to emergent spinal curvature metrics.\n\n")
        f.write("## Performance Summary\n")
        if results:
            avg_time = sum(r['runtime_sec'] for r in results) / len(results)
            max_mem = max(r['peak_memory_mb'] for r in results)
            f.write(f"- **Average Runtime:** {avg_time:.3f} s\n")
            f.write(f"- **Peak Memory:** {max_mem:.2f} MB\n")

if __name__ == "__main__":
    main()

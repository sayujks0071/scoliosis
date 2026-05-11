"""
Experiment: Protein-Driven Spinal Mechanics Simulation (PyElastica)

This script executes a reproducible experiment that maps protein/ECM-inspired parameters
(Stiffness Anisotropy, Active Curvature) to emergent macroscopic spinal geometry using
a Cosserat rod simulation (PyElastica).

Key Features:
- Maps biological parameters (e.g., FBN1 defects -> Low Anisotropy) to mechanical inputs.
- Simulates growth-driven deformation under gravity.
- Computes clinically relevant metrics: Cobb Angle, Lateral Scoliosis Index (S_lat).
- Tracks thermodynamic costs (U_CC) and computational performance (Runtime, Memory).
- Generates structured outputs: CSV dataset and Markdown report.

Usage:
    python scripts/experiments/experiment_protein_simulation_pyelastica.py --scenario bio_map
    python scripts/experiments/experiment_protein_simulation_pyelastica.py --quick-test
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Ensure src is in python path to allow imports from spinalmodes
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

try:
    from spinalmodes.countercurvature.pyelastica_bridge import (
        PYELASTICA_AVAILABLE,
        run_protein_simulation,
    )
except ImportError as e:
    print(f"CRITICAL ERROR: Failed to import spinalmodes modules. {e}")
    sys.exit(1)


def get_bio_label(anisotropy: float, active_curvature: float) -> str:
    """Map parameters to biological labels for easier interpretation."""
    labels = []
    # Fibrillin-1 (FBN1) determines Anisotropy
    if anisotropy >= 5.0:
        labels.append("WildType (Structured ECM)")
    elif anisotropy <= 1.0:
        labels.append("Marfan-like (Degraded ECM)")
    else:
        labels.append(f"Anisotropy={anisotropy}")

    # Growth Signaling Gain (Piezo/Ion Flux) determines Active Curvature
    if active_curvature >= 2.0:
        labels.append("Hyper-Growth (High Gain)")
    elif active_curvature <= 0.5:
        labels.append("Homeostatic (Low Gain)")
    else:
        labels.append(f"Growth={active_curvature}")

    return " | ".join(labels)


def run_experiment(
    out_file: str,
    anisotropies: list[float],
    active_curvatures: list[float],
    torsion_drive: float = 0.0,
    stiffness_modulation: float = 0.0,
    n_elements: int = 50,
    duration: float = 2.0,
    dt: float = 1e-4,
    gravity: float = 9.81,
    initial_lateral_defect: float = 0.05,  # Small perturbation to seed instability
):
    """
    Run the parameter sweep and save results.

    Args:
        out_file: Path to output CSV.
        anisotropies: List of anisotropy values to sweep.
        active_curvatures: List of active curvature values to sweep.
        torsion_drive: Active torsion drive magnitude.
        stiffness_modulation: Stiffness modulation amplitude.
        n_elements: Number of rod elements.
        duration: Simulation duration in seconds.
        dt: Time step in seconds.
        gravity: Gravitational acceleration.
        initial_lateral_defect: Initial lateral curvature perturbation.
    """

    # Check PyElastica availability explicitly
    if not PYELASTICA_AVAILABLE:
        print("ERROR: PyElastica is not installed.")
        print("Please install it using: pip install pyelastica")
        sys.exit(1)

    print("Starting Protein Mapping Experiment...")
    print(f"Output File: {out_file}")
    print(f"Scenarios: {len(anisotropies)} anisotropies x {len(active_curvatures)} active_curvatures")
    print(f"Parameters: N={n_elements}, T={duration}s, dt={dt}s, g={gravity}")

    # Ensure output directory exists
    out_dir = os.path.dirname(out_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Prepare CSV Header
    fieldnames = [
        "timestamp",
        "bio_label",
        "input_anisotropy",
        "input_active_curvature",
        "input_torsion_drive",
        "input_stiffness_modulation",
        "input_gravity",
        "max_curvature",
        "max_torsion",
        "cobb_angle",
        "s_lat",
        "end_to_end_distance",
        "bending_energy",
        "u_cc",
        "info_gain_ratio",
        "runtime_sec",
        "peak_memory_mb",
        "success",
        "error"
    ]

    results_accumulator = []

    # Check if file exists to write header or append
    file_exists = os.path.isfile(out_file)

    with open(out_file, mode='a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, restval='nan')
        if not file_exists:
            writer.writeheader()

        print("-" * 140)
        print(
            f"{'Bio Label':<40} | {'Cobb (deg)':<10} | {'Max Curv':<10} | {'Energy (J)':<10} | {'Time (s)':<8} | {'Status'}"
        )
        print("-" * 140)

        for anisotropy in anisotropies:
            for active_k in active_curvatures:

                # Run Simulation with measurement
                result = run_protein_simulation(
                    anisotropy=anisotropy,
                    active_curvature=active_k,
                    torsion_drive=torsion_drive,
                    stiffness_modulation=stiffness_modulation,
                    initial_lateral_defect=initial_lateral_defect,
                    n_elements=n_elements,
                    duration=duration,
                    dt=dt,
                    gravity=gravity,
                    show_progress=False # Keep stdout clean
                )

                # Process Result
                bio_label = get_bio_label(anisotropy, active_k)
                status = "OK" if result.get('success', False) else "FAIL"

                row_data = {
                    "timestamp": datetime.now().isoformat(),
                    "bio_label": bio_label,
                    "input_anisotropy": anisotropy,
                    "input_active_curvature": active_k,
                    "input_torsion_drive": torsion_drive,
                    "input_stiffness_modulation": stiffness_modulation,
                    "input_gravity": gravity,
                    "max_curvature": result.get('max_curvature', 0.0),
                    "max_torsion": result.get('max_torsion', 0.0),
                    "cobb_angle": result.get('cobb_angle', 0.0),
                    "s_lat": result.get('S_lat', 0.0),
                    "end_to_end_distance": result.get('end_to_end_distance', 0.0),
                    "bending_energy": result.get('bending_energy', 0.0),
                    "u_cc": result.get('U_CC', 0.0),
                    "info_gain_ratio": result.get('info_gain_ratio', 0.0),
                    "runtime_sec": result.get('runtime_sec', 0.0),
                    "peak_memory_mb": result.get('peak_memory_mb', 0.0),
                    "success": result.get('success', False),
                    "error": result.get('error', "")
                }

                writer.writerow(row_data)
                csvfile.flush()

                results_accumulator.append(row_data)

                # Print to console
                print(
                    f"{bio_label:<40} | {row_data['cobb_angle']:<10.4f} | "
                    f"{row_data['max_curvature']:<10.4f} | {row_data['bending_energy']:<10.4e} | "
                    f"{row_data['runtime_sec']:<8.3f} | {status}"
                )

    print("-" * 140)
    generate_markdown_report(out_file, results_accumulator)


def generate_markdown_report(csv_file: str, results: List[Dict[str, Any]]):
    """Generate a Markdown summary of the experiment."""
    if not results:
        print("No results to report.")
        return

    md_file = str(Path(csv_file).with_suffix(".md"))

    avg_runtime = np.mean([r["runtime_sec"] for r in results])
    max_mem = np.max([r["peak_memory_mb"] for r in results])

    with open(md_file, "w") as f:
        f.write("# Protein-to-Geometry Mapping Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Source Data:** `{os.path.basename(csv_file)}`\n\n")

        f.write("## Experiment Summary\n")
        f.write("This experiment maps biological parameters to mechanical spine outcomes.\n")
        f.write("- **Anisotropy (FBN1):** Higher values indicate structured ECM (Wild Type), resisting lateral buckling.\n")
        f.write("- **Active Curvature (Growth):** Higher values indicate rapid growth or high mechanosensory gain.\n\n")

        f.write("## Performance Metrics\n")
        f.write(f"- **Total Simulations:** {len(results)}\n")
        f.write(f"- **Average Runtime:** {avg_runtime:.4f} s\n")
        f.write(f"- **Peak Memory:** {max_mem:.2f} MB\n\n")

        f.write("## Results Table\n")
        f.write("| Bio Label | Anisotropy | Active Curv | Cobb Angle (deg) | Max Curvature | Energy (J) | Status |\n")
        f.write("|---|---|---|---|---|---|---|\n")

        for r in results:
            status_icon = "✅" if r['success'] else "❌"
            f.write(
                f"| {r['bio_label']} | {r['input_anisotropy']:.2f} | {r['input_active_curvature']:.2f} | "
                f"{r['cobb_angle']:.4f} | {r['max_curvature']:.4f} | {r['bending_energy']:.4e} | {status_icon} |\n"
            )

        f.write("\n## Interpretation\n")
        f.write("1. **WildType Stability:** High anisotropy (e.g., 5.0) should maintain low Cobb angles even with some active curvature.\n")
        f.write("2. **Marfan Instability:** Low anisotropy (e.g., 1.0) makes the spine susceptible to buckling (high Cobb angle) under active growth loads.\n")
        f.write("3. **Energy Costs:** Higher bending energy typically correlates with higher metabolic cost (U_CC).\n")

    print(f"\nReport generated: {md_file}")


def parse_args():
    parser = argparse.ArgumentParser(description="Protein-Driven Spinal Mechanics Simulation (PyElastica)")

    parser.add_argument(
        "--out-file",
        type=str,
        default="outputs/experiments/protein_simulation_results.csv",
        help="Path to output CSV file"
    )

    parser.add_argument(
        "--quick-test",
        action="store_true",
        help="Run a fast smoke test (low resolution, short duration)."
    )

    parser.add_argument(
        "--scenario",
        type=str,
        default="minimal",
        choices=["minimal", "bio_map", "growth_sweep", "microgravity"],
        help="Pre-configured simulation scenarios."
    )

    parser.add_argument(
        "--elements",
        type=int,
        default=50,
        help="Number of elements in the rod."
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Default parameters
    n_elements = args.elements
    duration = 2.0
    gravity = 9.81
    dt = 1e-4

    # Configure Scenarios
    anisotropies = [2.0]
    active_curvatures = [1.0]

    if args.quick_test:
        print(">>> Running Quick Test Mode")
        anisotropies = [1.0, 5.0]
        active_curvatures = [0.1]
        n_elements = 20
        duration = 0.1
        dt = 5e-4 # Larger timestep for speed

    elif args.scenario == "minimal":
        print(">>> Scenario: Minimal Experiment")
        # Simple proof of concept
        anisotropies = [2.0]
        active_curvatures = [0.5]

    elif args.scenario == "bio_map":
        print(">>> Scenario: Biological Mapping (WildType vs Marfan)")
        # Anisotropy: 1.0 (Marfan/Isotropic), 5.0 (WildType/Anisotropic)
        # Active Curvature: 0.5 (Homeostatic), 3.0 (Growth Spurt)
        anisotropies = [1.0, 5.0]
        active_curvatures = [0.5, 3.0]

    elif args.scenario == "growth_sweep":
        print(">>> Scenario: Growth Drive Sweep")
        anisotropies = [1.0, 5.0]
        active_curvatures = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]

    elif args.scenario == "microgravity":
        print(">>> Scenario: Microgravity Simulation")
        gravity = 0.001 # Microgravity
        anisotropies = [1.5] # Mild anisotropy
        active_curvatures = [1.5] # Moderate growth

    run_experiment(
        out_file=args.out_file,
        anisotropies=anisotropies,
        active_curvatures=active_curvatures,
        n_elements=n_elements,
        duration=duration,
        dt=dt,
        gravity=gravity
    )

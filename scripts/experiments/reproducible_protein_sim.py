"""
Reproducible Protein-Driven Simulation Experiment

This script maps "Virtual Protein Profiles" (representing different genetic/environmental conditions)
to macroscopic spinal mechanics using the PyElastica integration in `spinalmodes`.

It serves as a minimal, standalone experiment that demonstrates:
1. Mapping of protein metrics (Anisotropy, Curvature) to mechanical parameters.
2. Simulation of rod dynamics under gravity and active counter-curvature.
3. Measurement of emergent geometry (Scoliosis Index, Cobb Angle).
4. Runtime and memory profiling.
"""

import csv
import time
from datetime import datetime
from pathlib import Path

# Import the new high-level simulation function
try:
    from spinalmodes.countercurvature.pyelastica_bridge import (
        PYELASTICA_AVAILABLE,
        run_protein_simulation,
    )
except ImportError:
    print("Error: spinalmodes package not found or installation issue.")
    exit(1)

def run_experiment():
    if not PYELASTICA_AVAILABLE:
        print("Error: PyElastica is not installed. Please install it to run this experiment.")
        exit(1)

    print("Running Reproducible Protein-Driven Simulation...")

    # 1. Define Virtual Protein Profiles
    profiles = {
        "WildType_Control": {
            'anisotropy': 2.0,
            'active_curvature': 0.1,
            'torsion_drive': 0.0,
            'stiffness_modulation': 0.5
        },
        "Marfan_Like (Low Anisotropy)": {
            'anisotropy': 1.0,  # Isotropic
            'active_curvature': 0.1,
            'torsion_drive': 0.0,
            'stiffness_modulation': 0.2
        },
        "Piezo_Gain (High Drive)": {
            'anisotropy': 2.0,
            'active_curvature': 2.0, # High active drive
            'torsion_drive': 0.0,
            'stiffness_modulation': 0.5
        },
        "Scoliotic_Risk (Mismatch)": {
            'anisotropy': 1.1,
            'active_curvature': 2.0,
            'torsion_drive': 0.5,
            'stiffness_modulation': 0.3
        },
        "Microgravity (Unloaded)": {
            'anisotropy': 1.5,
            'active_curvature': 1.5,
            'torsion_drive': 0.2,
            'stiffness_modulation': 0.4
        }
    }

    output_dir = Path("outputs/reproducible_protein_sim")
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "results.csv"
    md_path = output_dir / "report.md"

    results = []
    total_start_time = time.time()

    print("-" * 100)
    print(f"{'Profile':<30} | {'Aniso':<6} | {'Curv':<6} | {'S_lat':<8} | {'Cobb':<8} | {'U_CC (J)':<10} | {'Gain':<6} | {'Time (s)':<8}")
    print("-" * 120)

    # Use a small lateral curvature defect to test stability (perturbation)
    # A perfectly straight spine (in X-Z) is an unstable equilibrium if not perturbed.
    lateral_defect = 0.05  # 1/m

    for name, params in profiles.items():
        # Handle Microgravity scenario by checking name or adding param to profile
        gravity = 9.81
        if "Microgravity" in name:
            gravity = 0.001

        sim_out = run_protein_simulation(
            **params,
            initial_lateral_defect=lateral_defect,
            length=0.5,
            n_elements=50,
            duration=2.0,
            dt=1e-4,
            gravity=gravity,
            show_progress=False
        )

        if not sim_out.get('success', False):
            print(f"Error running {name}: {sim_out.get('error')}")
            continue

        row = {
            "profile_name": name,
            **params,
            **sim_out
        }
        results.append(row)

        print(
            f"{name:<30} | "
            f"{params['anisotropy']:<6.2f} | "
            f"{params['active_curvature']:<6.2f} | "
            f"{sim_out.get('S_lat', 0):<8.4f} | "
            f"{sim_out.get('cobb_angle', 0):<8.2f} | "
            f"{sim_out.get('U_CC', 0):<10.2e} | "
            f"{sim_out.get('info_gain_ratio', 0):<6.2f} | "
            f"{sim_out.get('runtime_sec', 0):<8.4f}"
        )

    total_time = time.time() - total_start_time
    print("-" * 120)
    print(f"Experiment completed in {total_time:.2f}s")

    # Save CSV
    if results:
        # Get all keys from first result, ensuring profile_name is first
        all_keys = list(results[0].keys())
        if "profile_name" in all_keys:
            all_keys.remove("profile_name")
            fieldnames = ["profile_name"] + all_keys
        else:
            fieldnames = all_keys

        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"CSV saved to {csv_path}")

    # Generate Markdown Report
    generate_markdown_report(md_path, results, total_time)
    print(f"Report saved to {md_path}")

def generate_markdown_report(filepath, results, total_time):
    avg_runtime = sum(r['runtime_sec'] for r in results) / len(results) if results else 0
    max_mem = max(r['peak_memory_mb'] for r in results) if results else 0
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(filepath, 'w') as f:
        f.write("# Reproducible Protein-Driven Simulation Report\n\n")
        f.write(f"**Date:** {date_str}\n\n")
        f.write("## Summary\n")
        f.write(f"- **Total Experiment Time:** {total_time:.2f} s\n")
        f.write(f"- **Average Simulation Time:** {avg_runtime:.4f} s\n")
        f.write(f"- **Peak Memory Usage:** {max_mem:.2f} MB\n\n")

        f.write("## Results\n\n")
        f.write("| Profile | Anisotropy | Active Curvature | S_lat | Cobb Angle (deg) | Max Torsion | U_CC (J) | Info Gain |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")

        for r in results:
            name = r['profile_name']
            aniso = r['anisotropy']
            curv = r['active_curvature']
            s_lat = r.get('S_lat', 0.0)
            cobb = r.get('cobb_angle', 0.0)
            tor = r.get('max_torsion', 0.0)
            u_cc = r.get('U_CC', 0.0)
            gain = r.get('info_gain_ratio', 0.0)

            f.write(f"| {name} | {aniso:.2f} | {curv:.2f} | {s_lat:.4f} | {cobb:.2f} | {tor:.4f} | {u_cc:.2e} | {gain:.2f} |\n")

if __name__ == "__main__":
    run_experiment()

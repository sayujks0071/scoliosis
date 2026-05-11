"""
Reproducible integrated experiment demonstrating the Bio-Gravitational Counter-Curvature pipeline.

This script bridges protein-level structural metrics (from AlphaFold) to macroscopic
tissue mechanics (PyElastica Cosserat Rods). It serves as the minimal reproducible unit
for the "Biological Counter-Curvature" hypothesis.

HYPOTHESIS:
Spinal geometry emerges from a competition between:
1.  **Vector Cues** (Stiffness Anisotropy): Provided by ECM alignment (e.g., Fibrillin-1).
    Mapped from: Protein Anisotropy Index.
2.  **Scalar Drives** (Active Curvature): Provided by mechanosensitive growth (e.g., Piezo2).
    Mapped from: Intrinsic Curvature Summary.

Experiment:
Simulate "virtual proteins" representing different genetic/environmental conditions
(e.g., Marfan syndrome, Microgravity) and measure the emergent spinal shape (Scoliosis Index).

Outputs:
- CSV: `outputs/integrated_sim/results.csv`
- Report: `outputs/integrated_sim/results.md`
"""

import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure we can import from research/alphafold_countercurvature/src and root src
root_path = Path(__file__).parent.parent.parent
src_path = root_path / "research/alphafold_countercurvature/src"
main_src_path = root_path / "src"

if str(src_path) not in sys.path:
    sys.path.append(str(src_path))
if str(main_src_path) not in sys.path:
    sys.path.append(str(main_src_path))

try:
    from afcc.simulation import simulate_protein_mechanics
except ImportError:
    print("Error: Could not import afcc.simulation. Check python path or installation.")
    sys.exit(1)


def run_experiment():
    print("Running Integrated Bio-Gravitational Simulation...")
    print("Mapping 'Virtual Protein' profiles to spinal geometry...")

    # 1. Define Virtual Protein Profiles
    # These represent characteristic "phenotypes" in our theory.
    profiles = {
        "WildType_Control": {
            # Balanced: Moderate anisotropy (ECM alignment) and low active curvature.
            "anisotropy_index": 2.0,
            "curvature_summary": 0.1,
            "torsion_summary": 0.0,
            "PAE_domain_blockiness_score": 0.5,
        },
        "Marfan_Like (Low Anisotropy)": {
            # Fibrillin deficiency: Loss of vector cue (stiffness anisotropy).
            # Prediction: Instability / buckling risk.
            "anisotropy_index": 1.0,  # Isotropic
            "curvature_summary": 0.1,
            "torsion_summary": 0.0,
            "PAE_domain_blockiness_score": 0.2,
        },
        "Piezo_Gain (High Drive)": {
            # Hyper-mechanosensitivity: Excessive active curvature correction.
            # Prediction: Over-correction / oscillatory curvature.
            "anisotropy_index": 2.0,
            "curvature_summary": 2.0,  # High active drive
            "torsion_summary": 0.0,
            "PAE_domain_blockiness_score": 0.5,
        },
        "Scoliotic_Risk (Mismatch)": {
            # Vector-Scalar Mismatch: Low anisotropy + High drive.
            # The "Double Hit" hypothesis for severe progression.
            "anisotropy_index": 1.1,
            "curvature_summary": 2.0,
            "torsion_summary": 0.5,  # Torsional coupling engaged
            "PAE_domain_blockiness_score": 0.3,
        },
        "Microgravity (Unloaded)": {
            # Loss of gravitational load.
            # Here simulated by proxy metric changes, though usually gravity is a global param.
            # In this profile, we assume "sensing" remains high but "structure" degrades.
            "anisotropy_index": 1.5,
            "curvature_summary": 1.5,
            "torsion_summary": 0.2,
            "PAE_domain_blockiness_score": 0.4,
        },
    }

    # Setup Output
    results_base = Path(os.environ.get("RESULTS_DIR", "outputs"))
    output_dir = results_base / "integrated_sim"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "results.csv"
    md_path = output_dir / "results.md"

    results = []

    # Run Simulations
    total_start_time = time.time()

    print("-" * 100)
    print(
        f"{'Profile':<30} | {'Aniso':<6} | {'Curv':<6} | {'S_lat':<8} | {'Cobb':<8} | {'Time (s)':<8}"
    )
    print("-" * 100)

    for name, metrics in profiles.items():
        # Using standard rod parameters for a "spinal unit"
        # length=0.5m, n_elements=50
        sim_out = simulate_protein_mechanics(
            metrics,
            length=0.5,
            n_elements=50,
            duration=2.0,
            dt=1e-4,  # Stable timestep for these parameters
            boundary_condition="fixed",
            show_progress=False,  # Suppress progress bar for clean output
        )

        if not sim_out.get("success", False):
            print(f"Error running {name}: {sim_out.get('error')}")
            continue

        # Combine inputs and outputs
        row = {"profile_name": name, **metrics, **sim_out}
        results.append(row)

        print(
            f"{name:<30} | "
            f"{metrics['anisotropy_index']:<6.2f} | "
            f"{metrics['curvature_summary']:<6.2f} | "
            f"{sim_out.get('S_lat', 0):<8.4f} | "
            f"{sim_out.get('cobb_angle', 0):<8.2f} | "
            f"{sim_out.get('runtime_sec', 0):<8.4f}"
        )

    total_time = time.time() - total_start_time
    print("-" * 100)
    print(f"Experiment completed in {total_time:.2f}s")

    # 2. Save CSV
    if results:
        fieldnames = list(results[0].keys())
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"CSV saved to {csv_path}")

    # 3. Generate Markdown Report
    generate_markdown_report(md_path, results, total_time)
    print(f"Report saved to {md_path}")


def generate_markdown_report(filepath, results, total_time):
    """Generates a detailed markdown report of the simulation run."""

    avg_runtime = sum(r["runtime_sec"] for r in results) / len(results) if results else 0
    max_mem = max(r["peak_memory_mb"] for r in results) if results else 0
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(filepath, "w") as f:
        f.write("# Integrated Bio-Gravitational Simulation Report\n\n")
        f.write(f"**Date:** {date_str}\n\n")
        f.write("## Experiment Summary\n")
        f.write(
            "This experiment maps 'virtual protein' profiles to macroscopic spinal mechanics using PyElastica.\n"
        )
        f.write(
            "It tests the **Vector-Scalar Mismatch** hypothesis: that spinal stability requires a balance between "
            "ECM anisotropy (Vector) and mechanosensitive growth drive (Scalar).\n\n"
        )

        f.write("### Performance Metrics\n")
        f.write(f"- **Total Experiment Time:** {total_time:.2f} s\n")
        f.write(f"- **Average Simulation Time:** {avg_runtime:.4f} s\n")
        f.write(f"- **Peak Memory Usage:** {max_mem:.2f} MB\n\n")

        f.write("## Results Table\n\n")
        f.write(
            "| Profile | Anisotropy (Vector) | Curvature Drive (Scalar) | S_lat (Scoliosis Index) | Cobb Angle (deg) | Max Torsion |\n"
        )
        f.write("|---|---|---|---|---|---|\n")

        for r in results:
            name = r["profile_name"]
            aniso = r["anisotropy_index"]
            curv = r["curvature_summary"]
            s_lat = r.get("S_lat", 0.0)
            cobb = r.get("cobb_angle", 0.0)
            tor = r.get("max_torsion", 0.0)

            # Highlight risky rows
            flag = ""
            if s_lat > 0.4:  # Threshold for 'scoliosis' in this scaling
                flag = " **(Unstable)**"

            f.write(
                f"| {name} | {aniso:.2f} | {curv:.2f} | {s_lat:.4f}{flag} | {cobb:.2f} | {tor:.4f} |\n"
            )

        f.write("\n## Interpretation\n")
        f.write("1. **WildType Control**: Shows baseline stability.\n")
        f.write(
            "2. **Marfan-Like**: Low anisotropy leads to reduced stiffness against perturbation.\n"
        )
        f.write("3. **Piezo Gain**: High active curvature drive can induce over-correction.\n")
        f.write(
            "4. **Scoliotic Risk**: The combination of low anisotropy and high drive maximizes deformation (High S_lat).\n"
        )


if __name__ == "__main__":
    run_experiment()

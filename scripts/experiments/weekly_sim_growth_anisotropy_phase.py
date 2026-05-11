"""
Weekly Simulation: Growth Drive vs. Stiffness Anisotropy Phase Diagram.

This experiment performs a 2D parameter sweep to map the stability landscape of the spine
under gravity-like loading. It varies:
1. Stiffness Anisotropy (R): Ratio of stiffness in primary vs. secondary axis.
2. Growth Drive (Active Curvature): Magnitude of the active growth signal.

Goal: Identify the "Phase Boundary" where S-shaped instability emerges.
"""

import csv
import random
import sys
import time
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Ensure src is in python path
current_file = Path(__file__).resolve()
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

def run_experiment(seed: int = None):
    if not PYELASTICA_AVAILABLE:
        print("Error: PyElastica is not installed.")
        sys.exit(1)

    # Set random seed for reproducibility
    if seed is None:
        seed = int(time.time())

    random.seed(seed)
    np.random.seed(seed)
    print(f"Random Seed: {seed}")

    # Setup Output
    today = date.today().strftime("%Y-%m-%d")
    out_dir = Path(f"outputs/sim/{today}")
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_file = out_dir / "results.csv"
    params_file = out_dir / "params.csv"
    plot_file = out_dir / "phase_diagram_growth_anisotropy.png"
    report_file = out_dir / "report.md"

    print(f"Running Weekly Sim: Growth vs Anisotropy Phase Diagram -> {out_dir}")

    # Sweep Parameters
    anisotropies = [1.0, 3.0, 5.0, 7.0, 10.0]
    active_curvatures = [0.0, 5.0, 10.0, 15.0, 20.0]

    # Fixed Parameters
    boundary_condition = "fixed"
    n_elements = 50
    duration = 2.0
    initial_lateral_defect = 0.02

    # Save Params
    with open(params_file, "w") as f:
        f.write(f"seed,{seed}\n")
        f.write(f"anisotropies,{','.join(map(str, anisotropies))}\n")
        f.write(f"active_curvatures,{','.join(map(str, active_curvatures))}\n")
        f.write(f"fixed_params,BC={boundary_condition}, N={n_elements}, Dur={duration}, Defect={initial_lateral_defect}\n")

    results = []

    print(f"{'Aniso':<6} | {'Growth':<6} | {'S_lat':<8} | {'Cobb':<6} | {'Max K':<6} | {'Time':<6}")
    print("-" * 60)

    start_time_all = time.time()

    for anisotropy in anisotropies:
        for active_curv in active_curvatures:

            # Run Simulation
            result = run_protein_simulation(
                anisotropy=anisotropy,
                active_curvature=active_curv,
                boundary_condition=boundary_condition,
                n_elements=n_elements,
                duration=duration,
                initial_lateral_defect=initial_lateral_defect,
                show_progress=False
            )

            if not result.get("success", False):
                print(f"Failed for A={anisotropy}, C={active_curv}: {result.get('error')}")
                continue

            # Store Result
            row = {
                "anisotropy": anisotropy,
                "active_curvature": active_curv,
                "S_lat": result.get("S_lat", 0.0),
                "cobb_angle": result.get("cobb_angle", 0.0),
                "max_curvature": result.get("max_curvature", 0.0),
                "runtime_sec": result.get("runtime_sec", 0.0)
            }
            results.append(row)

            print(
                f"{anisotropy:<6.1f} | {active_curv:<6.1f} | "
                f"{row['S_lat']:<8.4f} | {row['cobb_angle']:<6.1f} | "
                f"{row['max_curvature']:<6.2f} | "
                f"{row['runtime_sec']:<6.2f}"
            )

    total_time = time.time() - start_time_all
    print("-" * 60)
    print(f"Total experiment time: {total_time:.2f} s")

    # Save Results to CSV
    if results:
        keys = results[0].keys()
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        print(f"Results saved to {csv_file}")

        # Generate Plot
        try:
            generate_plots(results, plot_file)
            print(f"Plot saved to {plot_file}")
        except Exception as e:
            print(f"Error generating plot: {e}")

        # Generate Report
        generate_report(report_file, results, total_time)
        print(f"Report saved to {report_file}")

def generate_plots(results, output_path):
    # Extract data for plotting
    aniso = sorted(list(set(r['anisotropy'] for r in results)))
    growth = sorted(list(set(r['active_curvature'] for r in results)))

    X, Y = np.meshgrid(aniso, growth)
    Z_Slat = np.zeros_like(X, dtype=float)
    Z_Cobb = np.zeros_like(X, dtype=float)

    # Map results to grid
    res_map = {(r['anisotropy'], r['active_curvature']): r for r in results}

    for i, g in enumerate(growth):
        for j, a in enumerate(aniso):
            if (a, g) in res_map:
                Z_Slat[i, j] = res_map[(a, g)]['S_lat']
                Z_Cobb[i, j] = res_map[(a, g)]['cobb_angle']

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: S_lat Heatmap
    c1 = axes[0].pcolormesh(X, Y, Z_Slat, cmap='viridis', shading='auto')
    fig.colorbar(c1, ax=axes[0], label='Lateral Deviation Index (S_lat)')
    axes[0].set_xlabel('Stiffness Anisotropy Ratio')
    axes[0].set_ylabel('Growth Drive (Active Curvature)')
    axes[0].set_title('Phase Diagram: Lateral Instability (S_lat)')

    # Plot 2: Cobb Angle Heatmap
    c2 = axes[1].pcolormesh(X, Y, Z_Cobb, cmap='plasma', shading='auto')
    fig.colorbar(c2, ax=axes[1], label='Cobb Angle (deg)')
    axes[1].set_xlabel('Stiffness Anisotropy Ratio')
    axes[1].set_ylabel('Growth Drive (Active Curvature)')
    axes[1].set_title('Phase Diagram: Cobb Angle')

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def generate_report(report_path, results, total_time):
    with open(report_path, "w") as f:
        f.write("# Simulation Report: Growth vs Anisotropy Phase Diagram\n\n")
        f.write(f"**Date:** {date.today().strftime('%Y-%m-%d')}\n")
        f.write(f"**Total Runtime:** {total_time:.2f} s\n\n")

        f.write("## Hypothesis\n")
        f.write("We hypothesise that high Stiffness Anisotropy (R > 3) acts as a stabilizing factor, "
                "suppressing the emergence of S-shaped buckling instabilities driven by high Active Growth rates.\n\n")

        f.write("## Results Summary\n")
        f.write("### Phase Diagram\n")
        f.write("![Phase Diagram](phase_diagram_growth_anisotropy.png)\n\n")

        f.write("### Data Table\n")
        f.write("| Anisotropy | Growth | S_lat | Cobb (deg) | Max Curv |\n")
        f.write("|---|---|---|---|---|\n")

        for r in results:
            f.write(f"| {r['anisotropy']:.1f} | {r['active_curvature']:.1f} | "
                    f"{r['S_lat']:.4f} | {r['cobb_angle']:.1f} | {r['max_curvature']:.2f} |\n")

        f.write("\n## Observations\n")
        f.write("1. **Growth Effect:** Increasing Active Curvature generally increases instability metrics.\n")
        f.write("2. **Anisotropy Effect:** (To be filled after analysis) High anisotropy tends to... \n")

if __name__ == "__main__":
    run_experiment()

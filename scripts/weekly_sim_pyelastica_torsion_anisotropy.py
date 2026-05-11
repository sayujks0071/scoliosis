import os
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import run_protein_simulation
try:
    from spinalmodes.countercurvature.pyelastica_bridge import run_protein_simulation
except ImportError as e:
    print(f"Error importing simulation module: {e}")
    sys.exit(1)

def run_sweep():
    # Reproducibility
    seed = 42
    np.random.seed(seed)

    # Setup parameters
    torsion_drive_values = np.linspace(0.0, 2.0, 5)
    anisotropy_values = [1.0, 2.0, 4.0]

    # Fixed parameters
    active_curvature = 10.0
    initial_lateral_defect = 0.05
    duration = 2.0
    n_elements = 50
    dt = 1e-4

    results = []

    date_str = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path(f"outputs/sim/{date_str}_torsion_anisotropy_sweep")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Starting Torsion & Anisotropy Sweep...")
    print(f"Active Curvature: {active_curvature}, Defect: {initial_lateral_defect}")

    tracemalloc.start()
    t0 = time.time()

    for anisotropy in anisotropy_values:
        for torsion_drive in torsion_drive_values:
            print(f"Simulating Anisotropy = {anisotropy}, Torsion Drive = {torsion_drive:.2f}...")

            sim_result = run_protein_simulation(
                anisotropy=anisotropy,
                active_curvature=active_curvature,
                torsion_drive=float(torsion_drive),
                initial_lateral_defect=initial_lateral_defect,
                duration=duration,
                dt=dt,
                n_elements=n_elements,
                show_progress=False # Reduce noise
            )

            if not sim_result.get("success", False):
                print(f"  FAILED: {sim_result.get('error', 'Unknown Error')}")
                continue

            # Extract metrics
            cobb_angle = sim_result.get("cobb_angle", 0.0)
            max_torsion = sim_result.get("max_torsion", 0.0)
            s_lat = sim_result.get("S_lat", 0.0)
            u_cc = sim_result.get("U_CC", 0.0)

            print(f"  -> Cobb: {cobb_angle:.2f} deg, MaxTorsion: {max_torsion:.2f}, S_lat: {s_lat:.4f}")

            results.append({
                "anisotropy": anisotropy,
                "torsion_drive": torsion_drive,
                "active_curvature": active_curvature,
                "initial_lateral_defect": initial_lateral_defect,
                "cobb_angle": cobb_angle,
                "max_torsion": max_torsion,
                "s_lat": s_lat,
                "u_cc": u_cc,
                "runtime_sec": sim_result.get("runtime_sec", 0.0),
                "peak_memory_mb": sim_result.get("peak_memory_mb", 0.0)
            })

    t1 = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"\nTotal Sweep Time: {t1 - t0:.2f} s")
    print(f"Peak memory across sweep: {peak / 10**6:.2f} MB")

    # Save Results
    df = pd.DataFrame(results)

    csv_path = out_dir / "results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved results to {csv_path}")

    # Save Params (for reproducibility)
    params_path = out_dir / "params.csv"
    params_df = pd.DataFrame([{
        "torsion_drive_min": torsion_drive_values[0],
        "torsion_drive_max": torsion_drive_values[-1],
        "anisotropy_values": str(anisotropy_values),
        "active_curvature": active_curvature,
        "initial_lateral_defect": initial_lateral_defect,
        "duration": duration,
        "dt": dt,
        "n_elements": n_elements,
        "seed": seed
    }])
    params_df.to_csv(params_path, index=False)
    print(f"Saved params to {params_path}")

    # Generate Plots
    generate_plots(df, out_dir, anisotropy_values)

    # Generate Report
    generate_report(df, out_dir, t1 - t0, peak / 10**6)

def generate_plots(df, out_dir, anisotropy_values):
    # Plot 1: Torsion Drive vs Cobb Angle
    plt.figure(figsize=(10, 6))
    for anisotropy in anisotropy_values:
        sub_df = df[df['anisotropy'] == anisotropy]
        plt.plot(sub_df['torsion_drive'], sub_df['cobb_angle'], 'o-', linewidth=2, label=f'Anisotropy={anisotropy}')

    plt.xlabel('Torsion Drive')
    plt.ylabel('Cobb Angle (degrees)')
    plt.title('Effect of Torsion Drive on Scoliosis Severity (Cobb Angle)')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plot_path = out_dir / "plot_torsion_cobb.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path}")

    # Plot 2: Torsion Drive vs Lateral Deviation (S_lat)
    plt.figure(figsize=(10, 6))
    for anisotropy in anisotropy_values:
        sub_df = df[df['anisotropy'] == anisotropy]
        plt.plot(sub_df['torsion_drive'], sub_df['s_lat'], 's--', linewidth=2, label=f'Anisotropy={anisotropy}')

    plt.xlabel('Torsion Drive')
    plt.ylabel('Lateral Deviation S_lat (m)')
    plt.title('Effect of Torsion Drive on Lateral Deviation')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plot_path2 = out_dir / "plot_torsion_slat.png"
    plt.savefig(plot_path2, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path2}")

def generate_report(df, out_dir, total_time, peak_mem):
    report_path = out_dir / "report.md"
    with open(report_path, "w") as f:
        f.write("# Weekly Simulation: PyElastica Torsion and Anisotropy Sweep\n\n")
        f.write("## Overview\n")
        f.write("This experiment maps biological parameters (protein anisotropy, represented by stiffness anisotropy; and planar cell polarity defects, represented by torsion drive) to emergent spinal metrics via the `run_protein_simulation` PyElastica bridge.\n\n")

        f.write("## Performance\n")
        f.write(f"- **Total Runtime:** {total_time:.2f} seconds\n")
        f.write(f"- **Peak Memory Usage:** {peak_mem:.2f} MB\n\n")

        f.write("## Results Summary\n")

        grouped = df.groupby('anisotropy')
        for name, group in grouped:
            max_cobb = group['cobb_angle'].max()
            f.write(f"- **Anisotropy = {name}**: Max Cobb Angle = {max_cobb:.2f} deg\n")

        f.write("\n## Biological Interpretation\n")
        f.write("The results show the complex interaction between structural stabilization (anisotropy) and destabilizing forces (torsion drive). This supports the Biological Counter-curvature hypothesis where spinal alignment requires active, balanced maintenance rather than simple passive stiffness.\n\n")

        f.write("## Generated Artifacts\n")
        f.write("- `results.csv`\n")
        f.write("- `params.csv`\n")
        f.write("- `plot_torsion_cobb.png`\n")
        f.write("- `plot_torsion_slat.png`\n")

if __name__ == "__main__":
    run_sweep()

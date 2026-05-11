import os
import sys
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
    stiffness_mod_values = np.linspace(-0.8, 0.8, 20)

    # Fixed parameters
    anisotropy = 2.0
    active_curvature = 12.0
    initial_lateral_defect = 0.05
    duration = 2.0
    n_elements = 50
    dt = 1e-4

    results = []

    print(f"Starting Stiffness Modulation Sweep (N={len(stiffness_mod_values)})...")
    print(f"Anisotropy: {anisotropy}, Active Curvature: {active_curvature}, Defect: {initial_lateral_defect}")

    for i, stiffness_mod in enumerate(stiffness_mod_values):
        print(f"[{i+1}/{len(stiffness_mod_values)}] Simulating Stiffness Modulation = {stiffness_mod:.2f}...")

        sim_result = run_protein_simulation(
            anisotropy=anisotropy,
            active_curvature=active_curvature,
            stiffness_modulation=float(stiffness_mod),
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
        max_curvature = sim_result.get("max_curvature", 0.0)
        s_lat = sim_result.get("S_lat", 0.0)
        u_cc = sim_result.get("U_CC", 0.0)

        print(f"  -> Cobb: {cobb_angle:.2f} deg, MaxCurv: {max_curvature:.2f}, S_lat: {s_lat:.4f}")

        results.append({
            "stiffness_modulation": stiffness_mod,
            "anisotropy": anisotropy,
            "active_curvature": active_curvature,
            "initial_lateral_defect": initial_lateral_defect,
            "cobb_angle": cobb_angle,
            "max_curvature": max_curvature,
            "s_lat": s_lat,
            "u_cc": u_cc,
            "runtime_sec": sim_result.get("runtime_sec", 0.0)
        })

    # Save Results
    df = pd.DataFrame(results)
    out_dir = Path("outputs/sim/2026-02-28")
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved results to {csv_path}")

    # Save Params (for reproducibility)
    params_path = out_dir / "params.csv"
    params_df = pd.DataFrame([{
        "stiffness_mod_min": stiffness_mod_values[0],
        "stiffness_mod_max": stiffness_mod_values[-1],
        "steps": len(stiffness_mod_values),
        "anisotropy": anisotropy,
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
    generate_plots(df, out_dir)

def generate_plots(df, out_dir):
    # Plot 1: Stiffness Modulation vs Cobb Angle
    plt.figure(figsize=(10, 6))
    plt.plot(df['stiffness_modulation'], df['cobb_angle'], 'o-', linewidth=2, color='blue')
    plt.xlabel('Stiffness Modulation')
    plt.ylabel('Cobb Angle (degrees)')
    plt.title('Effect of Stiffness Modulation on Lateral Instability (Cobb Angle)\n(Anisotropy=2.0, Active Curvature=12.0)')
    plt.grid(True, alpha=0.3)
    # Add vertical line for "no modulation"
    plt.axvline(x=0, color='gray', linestyle='--')

    plot_path = out_dir / "plot_stiffness_mod_cobb.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path}")

    # Plot 2: Stiffness Modulation vs Lateral Deviation (S_lat)
    plt.figure(figsize=(10, 6))
    plt.plot(df['stiffness_modulation'], df['s_lat'], 's--', linewidth=2, color='red')
    plt.xlabel('Stiffness Modulation')
    plt.ylabel('Lateral Deviation S_lat (m)')
    plt.title('Effect of Stiffness Modulation on Lateral Deviation\n(Anisotropy=2.0, Active Curvature=12.0)')
    plt.grid(True, alpha=0.3)

    plot_path2 = out_dir / "plot_stiffness_mod_slat.png"
    plt.savefig(plot_path2, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path2}")

if __name__ == "__main__":
    run_sweep()

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
    anisotropy_values = np.linspace(1.0, 10.0, 20)
    active_curvature = 10.0
    initial_lateral_defect = 0.05
    natural_kyphosis = 2.0
    duration = 2.0
    n_elements = 50
    dt = 1e-4

    results = []

    print(f"Starting Anisotropy Sweep (N={len(anisotropy_values)})...")
    print(f"Active Curvature: {active_curvature}, Defect: {initial_lateral_defect}, Kyphosis: {natural_kyphosis}")

    for i, anisotropy in enumerate(anisotropy_values):
        print(f"[{i+1}/{len(anisotropy_values)}] Simulating Anisotropy = {anisotropy:.2f}...")

        sim_result = run_protein_simulation(
            anisotropy=float(anisotropy),
            active_curvature=active_curvature,
            initial_lateral_defect=initial_lateral_defect,
            natural_kyphosis=natural_kyphosis,
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
            "anisotropy": anisotropy,
            "active_curvature": active_curvature,
            "initial_lateral_defect": initial_lateral_defect,
            "natural_kyphosis": natural_kyphosis,
            "cobb_angle": cobb_angle,
            "max_curvature": max_curvature,
            "s_lat": s_lat,
            "u_cc": u_cc,
            "runtime_sec": sim_result.get("runtime_sec", 0.0)
        })

    # Save Results
    df = pd.DataFrame(results)
    out_dir = Path("outputs/sim/2026-02-22")
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved results to {csv_path}")

    # Save Params (for reproducibility)
    params_path = out_dir / "params.csv"
    params_df = pd.DataFrame([{
        "anisotropy_min": anisotropy_values[0],
        "anisotropy_max": anisotropy_values[-1],
        "steps": len(anisotropy_values),
        "active_curvature": active_curvature,
        "initial_lateral_defect": initial_lateral_defect,
        "natural_kyphosis": natural_kyphosis,
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
    # Plot 1: Anisotropy vs Cobb Angle
    plt.figure(figsize=(10, 6))
    plt.plot(df['anisotropy'], df['cobb_angle'], 'o-', linewidth=2, color='blue')
    plt.xlabel('Stiffness Anisotropy Ratio')
    plt.ylabel('Cobb Angle (degrees)')
    plt.title('Effect of Stiffness Anisotropy on Cobb Angle\n(Active Curvature = 10.0)')
    plt.grid(True, alpha=0.3)

    plot_path = out_dir / "plot_anisotropy_cobb.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path}")

    # Plot 2: Anisotropy vs Lateral Deviation (S_lat)
    plt.figure(figsize=(10, 6))
    plt.plot(df['anisotropy'], df['s_lat'], 's--', linewidth=2, color='red')
    plt.xlabel('Stiffness Anisotropy Ratio')
    plt.ylabel('Lateral Deviation S_lat (m)')
    plt.title('Effect of Stiffness Anisotropy on Lateral Deviation\n(Active Curvature = 10.0)')
    plt.grid(True, alpha=0.3)

    plot_path2 = out_dir / "plot_anisotropy_slat.png"
    plt.savefig(plot_path2, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path2}")

    # Plot 3: Anisotropy vs U_CC (Cost Function)
    plt.figure(figsize=(10, 6))
    plt.plot(df['anisotropy'], df['u_cc'], '^-', linewidth=2, color='green')
    plt.xlabel('Stiffness Anisotropy Ratio')
    plt.ylabel('Total Energy U_CC (J)')
    plt.title('Effect of Stiffness Anisotropy on Total Energy Cost\n(Active Curvature = 10.0)')
    plt.grid(True, alpha=0.3)

    plot_path3 = out_dir / "plot_anisotropy_ucc.png"
    plt.savefig(plot_path3, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path3}")

if __name__ == "__main__":
    run_sweep()

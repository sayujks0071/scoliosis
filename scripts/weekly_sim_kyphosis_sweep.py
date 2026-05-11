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
    kyphosis_values = np.linspace(0.0, 5.0, 20)

    # Fixed parameters
    anisotropy = 2.0
    active_curvature = 12.0
    initial_lateral_defect = 0.05
    duration = 2.0
    n_elements = 50
    dt = 1e-4

    results = []

    print(f"Starting Kyphosis Sweep (N={len(kyphosis_values)})...")
    print(f"Anisotropy: {anisotropy}, Active Curvature: {active_curvature}, Defect: {initial_lateral_defect}")

    for i, kyphosis in enumerate(kyphosis_values):
        print(f"[{i+1}/{len(kyphosis_values)}] Simulating Natural Kyphosis = {kyphosis:.2f}...")

        sim_result = run_protein_simulation(
            anisotropy=anisotropy,
            active_curvature=active_curvature,
            initial_lateral_defect=initial_lateral_defect,
            natural_kyphosis=float(kyphosis),
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
            "natural_kyphosis": kyphosis,
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
    out_dir = Path("outputs/sim/2026-03-05_kyphosis")
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved results to {csv_path}")

    # Save Params (for reproducibility)
    params_path = out_dir / "params.csv"
    params_df = pd.DataFrame([{
        "kyphosis_min": kyphosis_values[0],
        "kyphosis_max": kyphosis_values[-1],
        "steps": len(kyphosis_values),
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
    # Plot 1: Kyphosis vs Cobb Angle
    plt.figure(figsize=(10, 6))
    plt.plot(df['natural_kyphosis'], df['cobb_angle'], 'o-', linewidth=2, color='blue')
    plt.xlabel('Natural Kyphosis (1/m)')
    plt.ylabel('Cobb Angle (degrees)')
    plt.title('Effect of Natural Kyphosis on Lateral Instability (Cobb Angle)\n(Anisotropy=2.0, Active Curvature=12.0)')
    plt.grid(True, alpha=0.3)
    # Add vertical line for "flat back" (kyphosis=0)
    plt.axvline(x=0, color='gray', linestyle='--')
    plt.text(0.1, max(df['cobb_angle'])*0.9, 'Hypokyphosis', color='gray')

    plot_path = out_dir / "plot_kyphosis_cobb.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path}")

    # Plot 2: Kyphosis vs Lateral Deviation (S_lat)
    plt.figure(figsize=(10, 6))
    plt.plot(df['natural_kyphosis'], df['s_lat'], 's--', linewidth=2, color='red')
    plt.xlabel('Natural Kyphosis (1/m)')
    plt.ylabel('Lateral Deviation S_lat (m)')
    plt.title('Effect of Natural Kyphosis on Lateral Deviation\n(Anisotropy=2.0, Active Curvature=12.0)')
    plt.grid(True, alpha=0.3)

    plot_path2 = out_dir / "plot_kyphosis_slat.png"
    plt.savefig(plot_path2, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path2}")

    # Plot 3: Kyphosis vs U_CC (Cost Function)
    plt.figure(figsize=(10, 6))
    plt.plot(df['natural_kyphosis'], df['u_cc'], '^-', linewidth=2, color='green')
    plt.xlabel('Natural Kyphosis (1/m)')
    plt.ylabel('Total Energy U_CC (J)')
    plt.title('Effect of Natural Kyphosis on Total Energy Cost\n(Anisotropy=2.0, Active Curvature=12.0)')
    plt.grid(True, alpha=0.3)

    plot_path3 = out_dir / "plot_kyphosis_ucc.png"
    plt.savefig(plot_path3, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path3}")

if __name__ == "__main__":
    run_sweep()

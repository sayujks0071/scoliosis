import os
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import from spinalmodes
try:
    from spinalmodes.countercurvature.pyelastica_bridge import (
        PYELASTICA_AVAILABLE,
        run_protein_simulation,
    )
except ImportError as e:
    print(f"Error importing simulation module: {e}")
    sys.exit(1)

def run_defect_sweep():
    if not PYELASTICA_AVAILABLE:
        print("PyElastica not available. Exiting.")
        sys.exit(1)

    # Reproducibility
    seed = 42
    np.random.seed(seed)

    # Setup parameters
    defect_values = np.linspace(0.0, 0.15, 20)
    anisotropy = 3.0 # Moderate anisotropy
    active_curvature = 10.0 # High growth drive
    natural_kyphosis = 2.0
    duration = 2.0
    dt = 1e-4
    n_elements = 50

    results = []

    date_str = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path(f"outputs/sim/{date_str}_defect_sweep")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Initial Lateral Defect Sweep (N={len(defect_values)})...")
    print(f"Defect Range: [{defect_values[0]:.3f}, {defect_values[-1]:.3f}]")
    print(f"Anisotropy: {anisotropy}, Active Curvature: {active_curvature}")

    for i, defect in enumerate(defect_values):
        print(f"[{i+1}/{len(defect_values)}] Simulating Initial Defect = {defect:.3f}...")

        tracemalloc.start()
        t0 = time.time()

        try:
            # 4. Run Simulation via the bridge API
            sim_result = run_protein_simulation(
                anisotropy=anisotropy,
                active_curvature=active_curvature,
                initial_lateral_defect=defect,
                natural_kyphosis=natural_kyphosis,
                duration=duration,
                dt=dt,
                n_elements=n_elements,
                show_progress=False
            )

            success = sim_result.get("success", False)
            error_msg = sim_result.get("error", "")

        except Exception as e:
            success = False
            error_msg = str(e)
            sim_result = {}
            print(f"  FAILED: {error_msg}")

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        t1 = time.time()

        if success:
            cobb_angle = sim_result.get("cobb_angle", 0.0)
            max_curvature = sim_result.get("max_curvature", 0.0)
            s_lat = sim_result.get("S_lat", 0.0)
            u_cc = sim_result.get("U_CC", 0.0)

            print(f"  -> Cobb: {cobb_angle:.2f} deg, MaxCurv: {max_curvature:.2f}, S_lat: {s_lat:.4f}")

            results.append({
                "initial_lateral_defect": defect,
                "anisotropy": anisotropy,
                "active_curvature": active_curvature,
                "cobb_angle": cobb_angle,
                "max_curvature": max_curvature,
                "s_lat": s_lat,
                "u_cc": u_cc,
                "runtime_sec": t1 - t0,
                "peak_memory_mb": peak / (1024 * 1024),
                "success": success,
                "error": error_msg
            })
        else:
             results.append({
                "initial_lateral_defect": defect,
                "anisotropy": anisotropy,
                "active_curvature": active_curvature,
                "cobb_angle": np.nan,
                "max_curvature": np.nan,
                "s_lat": np.nan,
                "u_cc": np.nan,
                "runtime_sec": t1 - t0,
                "peak_memory_mb": peak / (1024 * 1024),
                "success": success,
                "error": error_msg
            })


    # Save Results
    df = pd.DataFrame(results)
    csv_path = out_dir / "results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved results to {csv_path}")

    # Save Params (for reproducibility)
    params_path = out_dir / "params.csv"
    params_df = pd.DataFrame([{
        "defect_min": defect_values[0],
        "defect_max": defect_values[-1],
        "steps": len(defect_values),
        "anisotropy": anisotropy,
        "active_curvature": active_curvature,
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
    df_valid = df.dropna(subset=['cobb_angle'])

    if df_valid.empty:
        print("No valid results to plot.")
        return

    # Plot 1: Defect vs Cobb Angle
    plt.figure(figsize=(10, 6))
    plt.plot(df_valid['initial_lateral_defect'], df_valid['cobb_angle'], 'o-', linewidth=2, color='blue')
    plt.xlabel('Initial Lateral Defect (1/m)')
    plt.ylabel('Cobb Angle (degrees)')
    plt.title('Effect of Initial Lateral Defect on Cobb Angle\n(Anisotropy=3.0, Active Growth=10.0)')
    plt.grid(True, alpha=0.3)

    plot_path = out_dir / "plot_defect_cobb.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path}")

    # Plot 2: Defect vs Lateral Deviation (S_lat)
    plt.figure(figsize=(10, 6))
    plt.plot(df_valid['initial_lateral_defect'], df_valid['s_lat'], 's--', linewidth=2, color='red')
    plt.xlabel('Initial Lateral Defect (1/m)')
    plt.ylabel('Lateral Deviation S_lat (m)')
    plt.title('Effect of Initial Lateral Defect on Lateral Deviation\n(Anisotropy=3.0, Active Growth=10.0)')
    plt.grid(True, alpha=0.3)

    plot_path2 = out_dir / "plot_defect_slat.png"
    plt.savefig(plot_path2, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path2}")

if __name__ == "__main__":
    run_defect_sweep()

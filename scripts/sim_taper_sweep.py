import os
import sys
import time
import tracemalloc
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import from spinalmodes
try:
    from spinalmodes.countercurvature.coupling import CounterCurvatureParams
    from spinalmodes.countercurvature.info_fields import InfoField1D
    from spinalmodes.countercurvature.pyelastica_bridge import (
        PYELASTICA_AVAILABLE,
        CounterCurvatureRodSystem,
        compute_U_CC,
    )
except ImportError as e:
    print(f"Error importing simulation module: {e}")
    sys.exit(1)

def run_taper_sweep():
    if not PYELASTICA_AVAILABLE:
        print("PyElastica not available. Exiting.")
        sys.exit(1)

    # Reproducibility
    seed = 42
    np.random.seed(seed)

    # Setup parameters
    taper_values = np.linspace(0.5, 1.5, 21) # 21 points for 0.05 step
    anisotropy = 2.0
    active_curvature = 10.0 # High growth drive
    initial_lateral_defect = 0.05
    natural_kyphosis = 2.0
    duration = 2.0
    dt = 1e-4
    n_elements = 50
    length = 1.0
    radius = 0.01
    E0 = 1e6
    rho = 1000.0
    gravity = 9.81

    # Scale factors (matching run_protein_simulation defaults)
    scale_factor_kappa = 5.0
    chi_kappa = active_curvature * scale_factor_kappa # 50.0

    results = []

    print(f"Starting Taper Ratio Sweep (N={len(taper_values)})...")
    print(f"Taper Range: [{taper_values[0]:.2f}, {taper_values[-1]:.2f}]")
    print(f"Anisotropy: {anisotropy}, Active Curvature: {active_curvature} (chi_kappa={chi_kappa})")

    out_dir = Path("outputs/sim/2026-03-05")
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, taper_ratio in enumerate(taper_values):
        print(f"[{i+1}/{len(taper_values)}] Simulating Taper Ratio = {taper_ratio:.2f}...")

        tracemalloc.start()
        t0 = time.time()

        try:
            # 1. Setup Information Field
            s = np.linspace(0, length, n_elements + 1)
            info_center = 0.5 * length
            info_width = 0.1 * length
            I = 0.5 + 0.5 * np.exp(-0.5 * ((s - info_center) / info_width)**2)
            dIds = np.gradient(I, s)
            info = InfoField1D(s=s, I=I, dIds=dIds)

            # 2. Setup Parameters
            params = CounterCurvatureParams(
                chi_kappa=chi_kappa,
                chi_tau=0.0,
                chi_E=0.0,
                chi_M=0.0,
                scale_length=length
            )

            # 3. Create System with constant intrinsic curvature base
            kappa_gen = np.zeros((3, n_elements + 1))
            kappa_gen[1, :] = natural_kyphosis # Sagittal Kyphosis
            if initial_lateral_defect != 0.0:
                kappa_gen[0, :] = initial_lateral_defect # Lateral Defect

            rod_system = CounterCurvatureRodSystem.from_iec(
                info=info,
                params=params,
                length=length,
                n_elements=n_elements,
                E0=E0,
                rho=rho,
                radius=radius,
                kappa_gen=kappa_gen,
                gravity=gravity,
                stiffness_anisotropy=anisotropy,
                taper_ratio=taper_ratio
            )

            # 4. Run Simulation
            sim_result = rod_system.run_simulation(
                final_time=duration,
                dt=dt,
                save_every=max(1, int(duration/dt/10)),
                boundary_condition="fixed",
                progress_bar=False
            )

            sim_metrics = sim_result.compute_final_metrics()

            # Compute thermodynamic cost metrics
            energy_metrics = compute_U_CC(
                sim_result, info, params, gravity=gravity, rho=rho, E0=E0,
                radius=radius, anisotropy=anisotropy
            )
            sim_metrics.update(energy_metrics)

            success = True
            error_msg = ""

        except Exception as e:
            success = False
            error_msg = str(e)
            sim_metrics = {}
            print(f"  FAILED: {error_msg}")

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        t1 = time.time()

        # Extract metrics
        cobb_angle = sim_metrics.get("cobb_angle", 0.0)
        max_curvature = sim_metrics.get("max_curvature", 0.0)
        s_lat = sim_metrics.get("S_lat", 0.0)
        u_cc = sim_metrics.get("U_CC", 0.0)

        print(f"  -> Cobb: {cobb_angle:.2f} deg, MaxCurv: {max_curvature:.2f}, S_lat: {s_lat:.4f}")

        results.append({
            "taper_ratio": taper_ratio,
            "anisotropy": anisotropy,
            "chi_kappa": chi_kappa,
            "cobb_angle": cobb_angle,
            "max_curvature": max_curvature,
            "s_lat": s_lat,
            "u_cc": u_cc,
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
        "taper_min": taper_values[0],
        "taper_max": taper_values[-1],
        "steps": len(taper_values),
        "anisotropy": anisotropy,
        "active_curvature": active_curvature,
        "chi_kappa": chi_kappa,
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
    # Plot 1: Taper Ratio vs Cobb Angle
    plt.figure(figsize=(10, 6))
    plt.plot(df['taper_ratio'], df['cobb_angle'], 'o-', linewidth=2, color='blue')
    plt.xlabel('Taper Ratio (r_tip / r_base)')
    plt.ylabel('Cobb Angle (degrees)')
    plt.title('Effect of Geometric Tapering on Cobb Angle\n(Anisotropy=2.0, Active Growth=10.0)')
    plt.grid(True, alpha=0.3)
    plt.axvline(x=1.0, color='k', linestyle='--', alpha=0.5, label='Uniform Rod')
    plt.legend()

    plot_path = out_dir / "plot_taper_cobb.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path}")

    # Plot 2: Taper Ratio vs Lateral Deviation (S_lat)
    plt.figure(figsize=(10, 6))
    plt.plot(df['taper_ratio'], df['s_lat'], 's--', linewidth=2, color='red')
    plt.xlabel('Taper Ratio (r_tip / r_base)')
    plt.ylabel('Lateral Deviation S_lat (m)')
    plt.title('Effect of Geometric Tapering on Lateral Deviation\n(Anisotropy=2.0, Active Growth=10.0)')
    plt.grid(True, alpha=0.3)
    plt.axvline(x=1.0, color='k', linestyle='--', alpha=0.5, label='Uniform Rod')
    plt.legend()

    plot_path2 = out_dir / "plot_taper_slat.png"
    plt.savefig(plot_path2, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path2}")

    # Plot 3: Taper Ratio vs U_CC (Cost Function)
    plt.figure(figsize=(10, 6))
    plt.plot(df['taper_ratio'], df['u_cc'], '^-', linewidth=2, color='green')
    plt.xlabel('Taper Ratio (r_tip / r_base)')
    plt.ylabel('Total Energy U_CC (J)')
    plt.title('Effect of Geometric Tapering on Total Energy Cost\n(Anisotropy=2.0, Active Growth=10.0)')
    plt.grid(True, alpha=0.3)
    plt.axvline(x=1.0, color='k', linestyle='--', alpha=0.5, label='Uniform Rod')
    plt.legend()

    plot_path3 = out_dir / "plot_taper_ucc.png"
    plt.savefig(plot_path3, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path3}")

if __name__ == "__main__":
    run_taper_sweep()

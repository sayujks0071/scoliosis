"""
Weekly Simulation: Focal Anisotropy Defect (FBN1 Loss)

This experiment tests the hypothesis that a localized loss of stiffness anisotropy
(representing a focal defect in the ECM, e.g., Fibrillin-1 degradation)
acts as a nucleation site for spinal instability under high growth drive.

We sweep the LOCATION of the defect along the spine (0.0 to 1.0).
- Background Anisotropy: 5.0 (Healthy, stiff)
- Defect Anisotropy: 1.0 (Isotropic, weak)
- Growth Drive: Constant High (chi_kappa = 10.0)

Hypothesis: Apical defects (0.6-0.8) will cause the most severe S-shaped buckling.
"""

import csv
import random
import sys
import time
import tracemalloc
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
        CounterCurvatureParams,
        CounterCurvatureRodSystem,
        InfoField1D,
    )
except ImportError as e:
    print(f"Error importing spinalmodes: {e}")
    sys.exit(1)

def run_experiment(seed: int = None):
    if not PYELASTICA_AVAILABLE:
        print("Error: PyElastica is not installed.")
        sys.exit(1)

    # Set random seed
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
    plot_file = out_dir / "plot_defect_location.png"

    print(f"Running Weekly Sim: Focal Anisotropy Defect -> {out_dir}")

    # Sweep Parameters: Defect Location (fraction of length)
    defect_centers = np.linspace(0.1, 0.9, 9)

    # Fixed Parameters
    length = 1.0
    n_elements = 50
    duration = 2.0
    dt = 1e-4
    boundary_condition = "fixed"

    # Model Parameters
    chi_kappa = 20.0   # Very high uniform growth
    chi_tau = 0.0
    chi_e = 0.0
    chi_m = 0.0

    # Anisotropy Profile
    R_background = 5.0
    R_defect = 1.0
    defect_width = 0.15 # Gaussian sigma/width

    # Save Params
    with open(params_file, "w") as f:
        f.write(f"seed,{seed}\n")
        f.write(f"defect_centers,{','.join(map(str, defect_centers))}\n")
        f.write(f"R_background,{R_background}\n")
        f.write(f"R_defect,{R_defect}\n")
        f.write(f"defect_width,{defect_width}\n")
        f.write(f"chi_kappa,{chi_kappa}\n")
        f.write(f"fixed_params,BC={boundary_condition}, N={n_elements}, Dur={duration}\n")

    results = []

    print(f"{'Loc':<6} | {'S_lat':<8} | {'Cobb':<6} | {'Max K':<6} | {'Time':<6}")
    print("-" * 50)

    start_time_all = time.time()

    for center in defect_centers:
        tracemalloc.start()
        t0 = time.time()

        # 1. Setup Info Field (Uniform Growth -> Constant Info Field I=1.0)
        # However, to drive curvature, we need chi_kappa * kappa_rest.
        # kappa_rest depends on gradient of Info field?
        # Wait, if Info Field is constant, gradient is zero.
        # If gradient is zero, active curvature is zero?
        # Let's check `coupling.compute_rest_curvature`.
        # Usually kappa_rest ~ chi_kappa * dI/ds * normal
        # If dI/ds is zero, then no active curvature.

        # So we need a gradient to drive curvature.
        # Let's use a standard "Growth Gradient" (Gaussian bump) centered at 0.5
        # And move the ANISOTROPY defect relative to it.
        # If we just want uniform growth, we need a linear gradient I = s/L -> dI/ds = 1/L constant.

        s = np.linspace(0, length, n_elements + 1)

        # Linear Gradient for Constant Active Curvature Drive
        # I(s) = s/length -> dI/ds = 1/length
        # This gives constant active curvature along the rod.
        I = s / length
        dIds = np.ones_like(s) / length
        info = InfoField1D(s=s, I=I, dIds=dIds)

        # 2. Setup Anisotropy Profile (Gaussian Dip)
        # R(s) = R_back - (R_back - R_def) * exp(-0.5 * ((s - center*L)/width*L)**2)
        # We need this on internal nodes (n_elements - 1) for pyelastica bridge
        # But the bridge handles interpolation if we pass an array.
        # Let's generate it on 's' grid.

        sigma = defect_width * length
        mu = center * length
        gaussian = np.exp(-0.5 * ((s - mu) / sigma)**2)
        anisotropy_profile = R_background - (R_background - R_defect) * gaussian

        # 3. Setup Params
        params = CounterCurvatureParams(
            chi_kappa=chi_kappa,
            chi_tau=chi_tau,
            chi_E=chi_e,
            chi_M=chi_m,
            scale_length=length
        )

        # 4. Create System
        # Kappa_gen: Intrinsic curvature (e.g. kyphosis). Let's keep it 0 or small constant.
        # Natural kyphosis = 2.0
        # Add small initial lateral defect to seed instability
        kappa_gen = np.zeros((3, n_elements + 1))
        kappa_gen[1, :] = 2.0
        kappa_gen[0, :] = 0.03 # Initial lateral imperfection

        try:
            rod_system = CounterCurvatureRodSystem.from_iec(
                info=info,
                params=params,
                length=length,
                n_elements=n_elements,
                stiffness_anisotropy=anisotropy_profile, # Passes array!
                kappa_gen=kappa_gen
            )

            # 5. Run
            res = rod_system.run_simulation(
                final_time=duration,
                dt=dt,
                save_every=int(duration/dt/10), # Save 10 frames
                boundary_condition=boundary_condition,
                progress_bar=False
            )

            metrics = res.compute_final_metrics()

            row = {
                "defect_center": center,
                "S_lat": metrics.get("S_lat", 0.0),
                "cobb_angle": metrics.get("cobb_angle", 0.0),
                "max_curvature": metrics.get("max_curvature", 0.0),
                "runtime_sec": time.time() - t0
            }
            results.append(row)

            print(
                f"{center:<6.1f} | "
                f"{row['S_lat']:<8.4f} | {row['cobb_angle']:<6.1f} | "
                f"{row['max_curvature']:<6.2f} | "
                f"{row['runtime_sec']:<6.2f}"
            )

        except Exception as e:
            print(f"Failed for Center={center}: {e}")
            import traceback
            traceback.print_exc()

        tracemalloc.stop()

    total_time = time.time() - start_time_all
    print("-" * 50)
    print(f"Total time: {total_time:.2f} s")

    # Save Results
    if results:
        keys = results[0].keys()
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        print(f"Results saved to {csv_file}")

        # Generate Plot
        generate_plots(results, plot_file)

def generate_plots(results, output_path):
    centers = [r['defect_center'] for r in results]
    slats = [r['S_lat'] for r in results]
    cobbs = [r['cobb_angle'] for r in results]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    color = 'tab:red'
    ax1.set_xlabel('Defect Center Location (Fraction of Length)')
    ax1.set_ylabel('Cobb Angle (deg)', color=color)
    ax1.plot(centers, cobbs, 'o-', color=color, label='Cobb Angle')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('Lateral Deviation (S_lat)', color=color)  # we already handled the x-label with ax1
    ax2.plot(centers, slats, 's--', color=color, label='S_lat')
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title('Impact of Focal Anisotropy Defect Location on Spinal Instability')
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.savefig(output_path)
    print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    run_experiment()

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

try:
    from spinalmodes.countercurvature.coupling import CounterCurvatureParams
    from spinalmodes.countercurvature.info_fields import InfoField1D
    from spinalmodes.countercurvature.pyelastica_bridge import CounterCurvatureRodSystem
except ImportError:
    # If not found, try adding the research src path explicitly
    sys.path.append(str(Path(__file__).parent.parent.parent / "research/alphafold_countercurvature/src"))
    from spinalmodes.countercurvature.coupling import CounterCurvatureParams
    from spinalmodes.countercurvature.info_fields import InfoField1D
    from spinalmodes.countercurvature.pyelastica_bridge import CounterCurvatureRodSystem

def run_experiment(
    gravity: float,
    anisotropy: float,
    chi_kappa: float = 10.0,
    chi_tau: float = 0.0,
    base_length: float = 1.0,
    n_elements: int = 30,
    final_time: float = 5.0,
    dt: float = 1e-4,
) -> dict:
    """
    Run a single simulation with specified gravity and anisotropy.
    """

    # Base setup
    base_direction = (0.0, 0.0, 1.0) # Vertical +Z
    normal = (0.0, 1.0, 0.0) # Normal along Y (sagittal depth)

    # Create info field (Linear Gradient)
    # I(s) = s / L (0 to 1)
    # This ensures dI/ds is non-zero (1/L)
    s = np.linspace(0, base_length, n_elements + 1)
    I = s / base_length
    info = InfoField1D.from_array(s, I)

    # Params
    params = CounterCurvatureParams(
        chi_kappa=chi_kappa,
        chi_tau=chi_tau,
        chi_E=0.0,
        chi_M=0.0,
        scale_length=1.0
    )

    # Create System
    system = CounterCurvatureRodSystem.from_iec(
        info=info,
        params=params,
        length=base_length,
        n_elements=n_elements,
        radius=0.02,
        E0=1e6,
        rho=1000.0,
        base_direction=base_direction,
        normal=normal,
        stiffness_anisotropy=anisotropy,
        gravity=gravity
    )

    # Run
    res = system.run_simulation(
        final_time=final_time,
        dt=dt,
        save_every=int(final_time/dt/50),
        boundary_condition="fixed"
    )

    metrics = res.compute_final_metrics()
    metrics['gravity'] = gravity
    metrics['anisotropy'] = anisotropy
    metrics['chi_kappa'] = chi_kappa

    return metrics

def main():
    # Set Seed for Reproducibility
    seed = 20260801
    np.random.seed(seed)

    # Setup Output
    date_str = "2026-08-01"
    output_dir = Path(f"outputs/sim/{date_str}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Gravity-Anisotropy Sweep (Linear Gradient) -> {output_dir}")
    print(f"Random Seed: {seed}")

    # Parameters to sweep
    gravities = [0.0, 4.9, 9.81, 19.6] # 0g, 0.5g, 1g, 2g
    anisotropies = [1.0, 2.0, 5.0, 10.0]

    # Fixed parameters
    chi_kappa = 10.0 # Intrinsic curvature drive (C-curve)

    # CSV path
    csv_path = output_dir / "results.csv"

    # Fieldnames
    fieldnames = ['gravity', 'anisotropy', 'chi_kappa', 'max_curvature', 'max_torsion',
                  'end_to_end_distance', 'S_lat', 'cobb_angle', 'z_tip', 'x_tip', 'y_tip']

    # Reset CSV for this re-run
    if csv_path.exists():
        os.remove(csv_path)

    pd.DataFrame(columns=fieldnames).to_csv(csv_path, index=False)

    results = []

    # Compute total runs
    combinations = []
    for g in gravities:
        for a in anisotropies:
            combinations.append((g, a))

    total_runs = len(combinations)
    run_count = 0

    print("-" * 100)
    print(f"{'Gravity':<10} | {'Aniso':<10} | {'Cobb':<10} | {'S_lat':<10} | {'Max Tor':<10}")
    print("-" * 100)

    new_results = []

    for g, a in combinations:
        run_count += 1

        print(f"Run {run_count}/{total_runs}: g={g}, a={a}...", end="\r")
        try:
            metrics = run_experiment(
                gravity=g,
                anisotropy=a,
                chi_kappa=chi_kappa
            )
            metrics_row = {k: metrics.get(k, np.nan) for k in fieldnames}

            # Save immediately
            df_row = pd.DataFrame([metrics_row])
            df_row.to_csv(csv_path, mode='a', header=False, index=False)

            new_results.append(metrics_row)
            print(f"{g:<10.2f} | {a:<10.1f} | {metrics.get('cobb_angle', 0):<10.2f} | {metrics.get('S_lat', 0):<10.4f} | {metrics.get('max_torsion', 0):<10.4f}")

        except Exception as e:
            print(f"\nFailed run at g={g}, a={a}: {e}")

    # Reload all for plotting
    df = pd.DataFrame(new_results)

    # Save Params
    params_path = output_dir / "params.csv"
    with open(params_path, 'w') as f:
        f.write(f"seed,{seed}\n")
        f.write(f"gravities,{gravities}\n")
        f.write(f"anisotropies,{anisotropies}\n")
        f.write(f"chi_kappa,{chi_kappa}\n")

    # Plotting
    if not df.empty:
        # 1. Heatmap of S_lat
        pivot_s = df.pivot(index='anisotropy', columns='gravity', values='S_lat')

        plt.figure(figsize=(8, 6))
        plt.imshow(pivot_s, origin='lower', aspect='auto', cmap='viridis')
        plt.colorbar(label='Lateral S-Index (S_lat)')
        plt.xlabel('Gravity (m/s^2)')
        plt.ylabel('Stiffness Anisotropy')
        plt.title(f'Gravity vs Anisotropy (chi_kappa={chi_kappa})')
        plt.xticks(range(len(gravities)), gravities)
        plt.yticks(range(len(anisotropies)), anisotropies)
        plt.tight_layout()
        plt.savefig(output_dir / "plot_heatmap_s_lat.png")
        plt.close()

        # 2. Line Plot: Cobb vs Gravity for different Anisotropy
        plt.figure(figsize=(10, 6))
        for a in anisotropies:
            subset = df[df['anisotropy'] == a]
            if not subset.empty:
                plt.plot(subset['gravity'], subset['cobb_angle'], marker='o', label=f'Aniso={a}')

        plt.xlabel('Gravity (m/s^2)')
        plt.ylabel('Cobb Angle (deg)')
        plt.title('Effect of Gravity on Cobb Angle')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / "plot_gravity_cobb.png")
        plt.close()

        # 3. Line Plot: S_lat vs Anisotropy for different Gravity
        plt.figure(figsize=(10, 6))
        for g in gravities:
            subset = df[df['gravity'] == g]
            if not subset.empty:
                plt.plot(subset['anisotropy'], subset['S_lat'], marker='s', label=f'g={g}')

        plt.xlabel('Stiffness Anisotropy')
        plt.ylabel('Lateral Deviation (S_lat)')
        plt.title('Effect of Anisotropy on Lateral Deviation')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / "plot_anisotropy_slat.png")
        plt.close()

if __name__ == "__main__":
    main()

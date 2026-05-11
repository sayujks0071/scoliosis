"""
Weekly Simulation: Growth-Torsion Interaction
Goal: Test the interaction between Growth Magnitude (chi_kappa) and Torsional Coupling (chi_tau)
under fixed anisotropy and tilt.
Hypothesis: Torsional coupling acts as a multiplier on growth-induced instability, converting
planar buckling into 3D scoliosis even at lower growth gains.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from spinalmodes.countercurvature.coupling import CounterCurvatureParams
from spinalmodes.countercurvature.info_fields import InfoField1D
from spinalmodes.countercurvature.pyelastica_bridge import CounterCurvatureRodSystem


def run_experiment(
    chi_kappa: float,
    chi_tau: float,
    anisotropy: float = 2.0,
    tilt_deg: float = 5.0,
    base_length: float = 1.0,
    n_elements: int = 25,  # Increased slightly for better fidelity
    final_time: float = 5.0,
    dt: float = 2e-4,
) -> dict:
    """
    Run a single simulation with specified growth and torsion coupling.
    """

    theta = np.deg2rad(tilt_deg)
    base_direction = (np.sin(theta), 0.0, np.cos(theta))
    normal = (0.0, 1.0, 0.0) # Normal stays along Y

    # Create info field (Gaussian bump at center)
    s = np.linspace(0, base_length, n_elements + 1)
    center = 0.5 * base_length
    width = 0.1 * base_length
    # Gaussian: I(s) = exp(-0.5 * ((s-c)/w)^2)
    I = np.exp(-0.5 * ((s - center) / width)**2)

    # We construct InfoField1D using from_array which computes gradient numerically
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
    )

    # Run
    res = system.run_simulation(
        final_time=final_time,
        dt=dt,
        save_every=int(final_time/dt/50),
        boundary_condition="fixed"
    )

    metrics = res.compute_final_metrics()
    metrics['chi_kappa'] = chi_kappa
    metrics['chi_tau'] = chi_tau
    metrics['anisotropy'] = anisotropy
    metrics['tilt_deg'] = tilt_deg

    return metrics

def main():
    # Set Seed for Reproducibility
    seed = 20260208
    np.random.seed(seed)

    # Setup Output
    date_str = "2026-02-08"
    output_dir = Path(f"outputs/sim/{date_str}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Growth-Torsion Interaction Sweep -> {output_dir}")
    print(f"Random Seed: {seed}")

    # Parameters to sweep
    chi_kappas = [0.0, 10.0, 20.0]
    chi_taus = [0.0, 1.0, 5.0]

    # Fixed parameters
    anisotropy = 2.0
    tilt_deg = 5.0

    # CSV path
    csv_path = output_dir / "results.csv"

    # Explicit Column Order
    fieldnames = ['chi_kappa', 'chi_tau', 'anisotropy', 'tilt_deg', 'max_curvature', 'max_torsion',
                  'end_to_end_distance', 'S_lat', 'cobb_angle', 'z_tip', 'x_tip', 'y_tip']

    # Initialize CSV if not exists
    if not csv_path.exists():
        pd.DataFrame(columns=fieldnames).to_csv(csv_path, index=False)

    results = []
    if csv_path.exists():
        try:
            df_existing = pd.read_csv(csv_path)
            if not df_existing.empty:
                results = df_existing.to_dict('records')
        except pd.errors.EmptyDataError:
            pass # File empty, fine

    # Compute total runs
    combinations = []
    for ck in chi_kappas:
        for ct in chi_taus:
            combinations.append((ck, ct))

    total_runs = len(combinations)
    run_count = 0

    print("-" * 100)
    print(f"{'chi_kappa':<10} | {'chi_tau':<10} | {'S_lat':<10} | {'Cobb':<10} | {'Max Tor':<10}")
    print("-" * 100)

    for ck, ct in combinations:
        run_count += 1

        # Check if already run (approximate float comparison)
        already_done = False
        for res in results:
            if np.isclose(res.get('chi_kappa', -1), ck) and np.isclose(res.get('chi_tau', -1), ct):
                print(f"Skipping {ck}, {ct} (already done)")
                already_done = True
                break

        if already_done:
            continue

        print(f"Run {run_count}/{total_runs}: chi_kappa={ck}, chi_tau={ct}...", end="\r")
        try:
            metrics = run_experiment(
                chi_kappa=ck,
                chi_tau=ct,
                anisotropy=anisotropy,
                tilt_deg=tilt_deg
            )
            results.append(metrics)

            # Create DataFrame row ensuring column order matches CSV header
            df_row = pd.DataFrame([metrics])
            # Ensure all columns exist
            for col in fieldnames:
                if col not in df_row.columns:
                    df_row[col] = np.nan
            # Reorder
            df_row = df_row[fieldnames]

            # Append
            df_row.to_csv(csv_path, mode='a', header=False, index=False)

            print(f"{ck:<10.1f} | {ct:<10.1f} | {metrics.get('S_lat', 0):<10.4f} | {metrics.get('cobb_angle', 0):<10.2f} | {metrics.get('max_torsion', 0):<10.4f}")

        except Exception as e:
            print(f"\nFailed run at chi_kappa={ck}, chi_tau={ct}: {e}")

    # Reload full results for plotting
    df = pd.read_csv(csv_path)

    # Save Params
    params_path = output_dir / "params.csv"
    with open(params_path, 'w') as f:
        f.write(f"seed,{seed}\n")
        f.write(f"anisotropy,{anisotropy}\n")
        f.write(f"tilt_deg,{tilt_deg}\n")
        f.write(f"chi_kappas,{chi_kappas}\n")
        f.write(f"chi_taus,{chi_taus}\n")

    # Plotting
    if not df.empty:
        # 1. Heatmap of S_lat
        pivot_s = df.pivot(index='chi_tau', columns='chi_kappa', values='S_lat')

        plt.figure(figsize=(8, 6))
        plt.imshow(pivot_s, origin='lower', aspect='auto', cmap='viridis')
        plt.colorbar(label='Lateral S-Index (S_lat)')
        plt.xlabel('Growth Gain (chi_kappa)')
        plt.ylabel('Torsional Coupling (chi_tau)')
        plt.title(f'Interaction: Growth vs Torsion (Aniso={anisotropy})')

        # Set ticks
        plt.xticks(range(len(chi_kappas)), chi_kappas)
        plt.yticks(range(len(chi_taus)), chi_taus)

        plt.tight_layout()
        plt.savefig(output_dir / "plot_heatmap_s_lat.png")
        plt.close()

        # 2. Line Plot: S_lat vs chi_kappa for different chi_tau
        plt.figure(figsize=(10, 6))
        for ct in chi_taus:
            subset = df[df['chi_tau'] == ct]
            if not subset.empty:
                plt.plot(subset['chi_kappa'], subset['S_lat'], marker='o', label=f'chi_tau={ct}')

        plt.xlabel('Growth Gain (chi_kappa)')
        plt.ylabel('Lateral S-Index (S_lat)')
        plt.title('Effect of Torsion on Growth-Induced Instability')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / "plot_interaction_lines.png")
        plt.close()

        # 3. Line Plot: Cobb vs chi_kappa
        plt.figure(figsize=(10, 6))
        for ct in chi_taus:
            subset = df[df['chi_tau'] == ct]
            if not subset.empty:
                plt.plot(subset['chi_kappa'], subset['cobb_angle'], marker='s', label=f'chi_tau={ct}')

        plt.xlabel('Growth Gain (chi_kappa)')
        plt.ylabel('Cobb Angle (deg)')
        plt.title('Effect of Torsion on Cobb Angle')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / "plot_cobb_lines.png")
        plt.close()

if __name__ == "__main__":
    main()

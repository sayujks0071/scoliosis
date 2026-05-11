"""
Weekly Simulation: Torsion Drive Sweep
Goal: Test for emergent S-shaped profiles under tilted gravity loading with fixed active growth (chi=10) and fixed intermediate anisotropy (R=2.0), while sweeping Torsional Coupling (chi_tau).
"""

import datetime
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
    chi_tau: float,
    anisotropy: float = 2.0,
    tilt_deg: float = 5.0,
    chi_kappa: float = 10.0,
    base_length: float = 1.0,
    n_elements: int = 40,
    final_time: float = 20.0,
    dt: float = 1e-4,
) -> dict:
    """
    Run a single simulation with a tilted base and specific torsional coupling.
    """

    theta = np.deg2rad(tilt_deg)
    base_direction = (np.sin(theta), 0.0, np.cos(theta))
    normal = (0.0, 1.0, 0.0) # Normal stays along Y

    # Create info field (linear growth gradient)
    # I(s) = s / L (linear increase from 0 to 1)
    s = np.linspace(0, base_length, n_elements + 1)
    I = s / base_length
    info = InfoField1D.from_array(s, I)

    # Params
    params = CounterCurvatureParams(
        chi_kappa=chi_kappa,
        chi_E=0.0,
        chi_M=0.0,
        chi_tau=chi_tau,
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
        save_every=int(final_time/dt/100), # 100 frames total
        boundary_condition="fixed"
    )

    metrics = res.compute_final_metrics()
    metrics['tilt_deg'] = tilt_deg
    metrics['chi_kappa'] = chi_kappa
    metrics['anisotropy'] = anisotropy
    metrics['chi_tau'] = chi_tau

    return metrics

def main():
    # Set Seed for Reproducibility
    seed = 42
    np.random.seed(seed)

    # Setup Output
    today = datetime.date.today().isoformat()
    output_dir = Path(f"outputs/sim/{today}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Torsion Drive Sweep -> {output_dir}")
    print(f"Random Seed: {seed}")

    # Parameters to sweep
    chi_taus = [0.0, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]

    # Fixed parameters
    tilt_deg = 5.0
    chi_kappa = 10.0
    anisotropy = 2.0

    results = []

    print("-" * 80)
    print(f"{'chi_tau':<10} | {'S_lat':<10} | {'Cobb':<10} | {'Max Tor':<10}")
    print("-" * 80)

    for val in chi_taus:
        try:
            metrics = run_experiment(val, anisotropy, tilt_deg, chi_kappa)
            results.append(metrics)
            print(f"{val:<10.2f} | {metrics.get('S_lat', 0):<10.4f} | {metrics.get('cobb_angle', 0):<10.2f} | {metrics.get('max_torsion', 0):<10.4f}")
        except Exception as e:
            print(f"Failed run at chi_tau={val}: {e}")

    # Save CSV
    df = pd.DataFrame(results)
    csv_path = output_dir / "results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved results to {csv_path}")

    # Save Params
    params_path = output_dir / "params.csv"
    with open(params_path, 'w') as f:
        f.write(f"seed,{seed}\n")
        f.write(f"chi_kappa,{chi_kappa}\n")
        f.write(f"tilt_deg,{tilt_deg}\n")
        f.write(f"anisotropy,{anisotropy}\n")
        f.write("variable,chi_tau,0.0,10.0,7\n")

    # Plotting
    if not df.empty:
        # Plot 1: chi_tau vs S_lat
        plt.figure(figsize=(10, 6))
        plt.plot(df['chi_tau'], df['S_lat'], marker='o', color='purple')
        plt.xlabel('Torsional Coupling (chi_tau)')
        plt.ylabel('Lateral S-Index (S_lat)')
        plt.title(f'S-Shape Emergence vs Torsion (Aniso={anisotropy}, Tilt={tilt_deg})')
        plt.grid(True)
        plt.savefig(output_dir / "plot_s_lat.png")
        plt.close()

        # Plot 2: chi_tau vs Cobb Angle
        plt.figure(figsize=(10, 6))
        plt.plot(df['chi_tau'], df['cobb_angle'], marker='s', color='red')
        plt.xlabel('Torsional Coupling (chi_tau)')
        plt.ylabel('Cobb Angle (deg)')
        plt.title(f'Cobb Angle vs Torsion (Aniso={anisotropy}, Tilt={tilt_deg})')
        plt.grid(True)
        plt.savefig(output_dir / "plot_cobb.png")
        plt.close()

        # Plot 3: chi_tau vs Max Torsion
        plt.figure(figsize=(10, 6))
        plt.plot(df['chi_tau'], df['max_torsion'], marker='^', color='orange')
        plt.xlabel('Torsional Coupling (chi_tau)')
        plt.ylabel('Max Torsion (rad/m)')
        plt.title(f'Torsion vs Torsion Coupling (Aniso={anisotropy}, Tilt={tilt_deg})')
        plt.grid(True)
        plt.savefig(output_dir / "plot_torsion.png")
        plt.close()

    print("Experiment complete.")

if __name__ == "__main__":
    main()

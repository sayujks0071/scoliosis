"""
Weekly Simulation: Tilted Anisotropy Sweep
Goal: Test for emergent S-shaped profiles under tilted gravity loading with active growth and varying stiffness anisotropy.
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
    anisotropy: float,
    tilt_deg: float = 5.0,
    chi_kappa: float = 10.0,
    base_length: float = 1.0,
    n_elements: int = 40,
    final_time: float = 20.0,
    dt: float = 1e-4,
) -> dict:
    """
    Run a single simulation with a tilted base and specific anisotropy.
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
        chi_tau=0.0,
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

    return metrics

def main():
    # Set Seed for Reproducibility
    seed = 42
    np.random.seed(seed)

    # Setup Output
    today = datetime.date.today().isoformat()
    output_dir = Path(f"outputs/sim/{today}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Tilted Anisotropy Sweep -> {output_dir}")
    print(f"Random Seed: {seed}")

    # Parameters to sweep
    anisotropies = [0.1, 0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
    tilt_deg = 5.0
    chi_kappa = 10.0

    results = []

    print("-" * 80)
    print(f"{'Anisotropy':<10} | {'S_lat':<10} | {'Cobb':<10} | {'Max Tor':<10}")
    print("-" * 80)

    for val in anisotropies:
        try:
            metrics = run_experiment(val, tilt_deg, chi_kappa)
            results.append(metrics)
            print(f"{val:<10.2f} | {metrics.get('S_lat', 0):<10.4f} | {metrics.get('cobb_angle', 0):<10.2f} | {metrics.get('max_torsion', 0):<10.4f}")
        except Exception as e:
            print(f"Failed run at Anisotropy={val}: {e}")

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
        f.write("variable,stiffness_anisotropy,0.1,12.0,9\n")

    # Plotting
    if not df.empty:
        # Plot 1: Anisotropy vs S_lat
        plt.figure(figsize=(10, 6))
        plt.plot(df['anisotropy'], df['S_lat'], marker='o', color='purple')
        plt.xlabel('Stiffness Anisotropy Ratio')
        plt.ylabel('Lateral S-Index (S_lat)')
        plt.title(f'S-Shape Emergence vs Anisotropy (Tilt={tilt_deg}deg, chi={chi_kappa})')
        plt.grid(True)
        plt.savefig(output_dir / "plot_s_lat.png")
        plt.close()

        # Plot 2: Anisotropy vs Cobb Angle
        plt.figure(figsize=(10, 6))
        plt.plot(df['anisotropy'], df['cobb_angle'], marker='s', color='red')
        plt.xlabel('Stiffness Anisotropy Ratio')
        plt.ylabel('Cobb Angle (deg)')
        plt.title(f'Cobb Angle vs Anisotropy (Tilt={tilt_deg}deg, chi={chi_kappa})')
        plt.grid(True)
        plt.savefig(output_dir / "plot_cobb.png")
        plt.close()

        # Plot 3: Anisotropy vs Max Torsion
        plt.figure(figsize=(10, 6))
        plt.plot(df['anisotropy'], df['max_torsion'], marker='^', color='orange')
        plt.xlabel('Stiffness Anisotropy Ratio')
        plt.ylabel('Max Torsion (rad/m)')
        plt.title(f'Torsion vs Anisotropy (Tilt={tilt_deg}deg, chi={chi_kappa})')
        plt.grid(True)
        plt.savefig(output_dir / "plot_torsion.png")
        plt.close()

    # Generate Report
    report_path = output_dir / "report.md"
    with open(report_path, "w") as f:
        f.write(f"# Tilted Anisotropy Sweep Report - {today}\n\n")
        f.write("## Hypothesis\n")
        f.write("Testing if increasing stiffness anisotropy under a small lateral tilt (5 deg) and high growth drive (chi=10) triggers S-shaped buckling (scoliosis) via torsional instability.\n\n")
        f.write("## Parameters\n")
        f.write(f"- Random Seed: {seed}\n")
        f.write(f"- Growth Gradient (chi_kappa): {chi_kappa}\n")
        f.write(f"- Load Vector Tilt: {tilt_deg} degrees\n")
        f.write("- Stiffness Anisotropy: 0.1 to 12.0\n\n")
        f.write("## Results Summary\n")
        if not df.empty:
            max_s = df['S_lat'].max()
            max_cobb = df['cobb_angle'].max()
            max_tor = df['max_torsion'].max()

            # Find anisotropy where peaks occur
            idx_s = df['S_lat'].idxmax()
            best_aniso_s = df.loc[idx_s, 'anisotropy']

            f.write(f"- Max Lateral S-Index: {max_s:.4f} (at Anisotropy={best_aniso_s})\n")
            f.write(f"- Max Cobb Angle: {max_cobb:.2f} deg\n")
            f.write(f"- Max Torsion: {max_tor:.4f}\n\n")

            f.write("## Interpretation\n")
            if max_s > 0.15:
                f.write(f"Significant S-shape emerged (S_lat={max_s:.2f}). This suggests that high anisotropy amplifies small asymmetries into complex curves, potentially via torsional coupling.\n")
            elif max_s > 0.05:
                 f.write(f"Minor S-shape emerged (S_lat={max_s:.2f}). Anisotropy plays a role but might need higher torsional coupling to drive full scoliosis.\n")
            else:
                f.write("No significant S-shape emerged. The system likely remained in a planar buckling mode.\n")

            f.write("\n## Next Steps\n")
            f.write("- If S-shape is low, consider sweeping Torsional Coupling (chi_tau) next.\n")
            f.write("- If S-shape is high, investigate the role of specific protein candidates matching this anisotropy profile.\n")

        else:
            f.write("No results generated.\n")

    print(f"Report written to {report_path}")

if __name__ == "__main__":
    main()

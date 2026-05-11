"""
Weekly Simulation: Growth Width Sweep
Goal: Test if localized growth gradients (small info_width) trigger S-shaped buckling profiles
more effectively than broad, distributed growth, under high growth drive and stiffness anisotropy.
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
    info_width: float,
    chi_kappa: float = 20.0,
    anisotropy: float = 2.0,
    info_center: float = 0.5,
    base_length: float = 1.0,
    n_elements: int = 40,
    final_time: float = 20.0,
    dt: float = 1e-4,
) -> dict:
    """
    Run a single simulation with a specific growth width.
    """

    # Vertical rod
    base_direction = (0.0, 0.0, 1.0)
    normal = (1.0, 0.0, 0.0) # Normal in X

    # Create info field (Gaussian bump)
    # I(s) = 0.5 + exp(...)
    s = np.linspace(0, base_length, n_elements + 1)
    # Gaussian bump
    # info_amplitude = 0.5 (results in peak ~1.0 if base is 0.5)
    info_density = 0.5 + 0.5 * np.exp(
        -0.5 * ((s - info_center * base_length) / (info_width * base_length))**2
    )
    # Recompute gradient
    dIds = np.gradient(info_density, s)
    info = InfoField1D(s=s, I=info_density, dIds=dIds)

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
    # Use 'fixed' boundary condition (cantilever)
    res = system.run_simulation(
        final_time=final_time,
        dt=dt,
        save_every=int(final_time/dt/100), # 100 frames total
        boundary_condition="fixed"
    )

    metrics = res.compute_final_metrics()
    metrics['info_width'] = info_width
    metrics['chi_kappa'] = chi_kappa
    metrics['anisotropy'] = anisotropy

    return metrics

def main():
    # Set Seed for Reproducibility
    seed = 20260205
    np.random.seed(seed)

    # Setup Output
    today = datetime.date.today().isoformat()
    output_dir = Path(f"outputs/sim/{today}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Growth Width Sweep -> {output_dir}")
    print(f"Random Seed: {seed}")

    # Parameters to sweep
    info_widths = [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]

    # Fixed parameters
    chi_kappa = 20.0
    anisotropy = 2.0
    info_center = 0.5

    results = []

    print("-" * 80)
    print(f"{'Width':<10} | {'S_lat':<10} | {'Cobb':<10} | {'Max Curv':<10}")
    print("-" * 80)

    for val in info_widths:
        try:
            metrics = run_experiment(
                info_width=val,
                chi_kappa=chi_kappa,
                anisotropy=anisotropy,
                info_center=info_center
            )
            results.append(metrics)
            print(f"{val:<10.2f} | {metrics.get('S_lat', 0):<10.4f} | {metrics.get('cobb_angle', 0):<10.2f} | {metrics.get('max_curvature', 0):<10.4f}")
        except Exception as e:
            print(f"Failed run at Width={val}: {e}")

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
        f.write(f"anisotropy,{anisotropy}\n")
        f.write(f"info_center,{info_center}\n")
        f.write("variable,info_width,0.05,1.0,7\n")

    # Plotting
    if not df.empty:
        # Plot 1: Width vs S_lat
        plt.figure(figsize=(10, 6))
        plt.plot(df['info_width'], df['S_lat'], marker='o', color='purple')
        plt.xlabel('Growth Gradient Width (Fraction of Length)')
        plt.ylabel('Lateral S-Index (S_lat)')
        plt.title(f'S-Shape vs Growth Localization (chi={chi_kappa}, Aniso={anisotropy})')
        plt.grid(True)
        plt.savefig(output_dir / "plot_s_lat.png")
        plt.close()

        # Plot 2: Width vs Cobb Angle
        plt.figure(figsize=(10, 6))
        plt.plot(df['info_width'], df['cobb_angle'], marker='s', color='red')
        plt.xlabel('Growth Gradient Width (Fraction of Length)')
        plt.ylabel('Cobb Angle (deg)')
        plt.title(f'Cobb Angle vs Growth Localization (chi={chi_kappa})')
        plt.grid(True)
        plt.savefig(output_dir / "plot_cobb.png")
        plt.close()

    # Generate Report
    report_path = output_dir / "report.md"
    with open(report_path, "w") as f:
        f.write(f"# Growth Width Sweep Report - {today}\n\n")
        f.write("## Hypothesis\n")
        f.write("Testing if localized growth gradients (small info_width) act as 'hinges' that trigger S-shaped buckling (S_lat), compared to broad distributed growth.\n\n")
        f.write("## Parameters\n")
        f.write(f"- Random Seed: {seed}\n")
        f.write(f"- Growth Amplitude (chi_kappa): {chi_kappa}\n")
        f.write(f"- Stiffness Anisotropy: {anisotropy} (Stiffer Sagittal)\n")
        f.write(f"- Growth Center: {info_center}\n")
        f.write("- Growth Widths swept: 0.05 to 1.0\n\n")
        f.write("## Results Summary\n")
        if not df.empty:
            max_s = df['S_lat'].max()
            max_cobb = df['cobb_angle'].max()

            # Find peak width
            idx_s = df['S_lat'].idxmax()
            best_width_s = df.loc[idx_s, 'info_width']

            f.write(f"- Max Lateral S-Index: {max_s:.4f} (at Width={best_width_s})\n")
            f.write(f"- Max Cobb Angle: {max_cobb:.2f} deg\n\n")

            f.write("## Interpretation\n")
            if max_s > 0.15:
                f.write(f"Significant S-shape emerged (S_lat={max_s:.2f}). Localization at Width={best_width_s} appears to drive complex curvature.\n")
            elif max_s > 0.05:
                 f.write(f"Minor S-shape emerged (S_lat={max_s:.2f}).\n")
            else:
                f.write("No significant S-shape emerged. The system mostly exhibited C-shaped bending or planar behavior.\n")

            f.write("\n## Emergent Behavior\n")
            # Analyze trend
            if df.loc[0, 'S_lat'] > df.loc[len(df)-1, 'S_lat']:
                 f.write("Sharp localization (small width) tends to increase S-shape complexity compared to broad growth.\n")
            else:
                 f.write("Broad growth tends to favor S-shapes, or the relationship is non-monotonic.\n")

        else:
            f.write("No results generated.\n")

    print(f"Report written to {report_path}")

if __name__ == "__main__":
    main()

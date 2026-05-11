
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


def run_simulation(
    tilt_deg: float,
    anisotropy: float,
    chi_kappa: float,
    base_length: float = 1.0,
    n_elements: int = 50,
    final_time: float = 5.0, # Sufficient for settling
    dt: float = 1e-4,
) -> dict:
    """
    Run a single simulation with a tilted base and specified anisotropy.

    Tilt is applied in the lateral (X-Z) plane.
    Rotation about Y-axis.
    theta = tilt_deg * pi / 180
    direction = (sin(theta), 0, cos(theta))
    """

    theta = np.deg2rad(tilt_deg)
    base_direction = (np.sin(theta), 0.0, np.cos(theta))
    normal = (0.0, 1.0, 0.0) # Normal stays along Y

    # Create info field (linear growth gradient)
    # I(s) = s / L (linear increase from 0 to 1)
    s = np.linspace(0, base_length, n_elements + 1)
    # Use a Gaussian bump for localized growth drive (standard in weekly sims)
    # Or linear? Let's stick to Gaussian as in experiment_minimal_elastica for 'growth' scenarios
    # But experiment_tilt_sweep used Linear.
    # Let's use Gaussian to be consistent with 'Growth Drive' usually implying localized growth in this repo.
    # Actually, let's use the one from experiment_minimal_elastica default:
    info_center = 0.6 * base_length
    info_width = 0.1 * base_length
    I = 0.5 + 0.5 * np.exp(-0.5 * ((s - info_center) / info_width)**2)
    dIds = np.gradient(I, s)

    info = InfoField1D(s=s, I=I, dIds=dIds)

    # Params
    params = CounterCurvatureParams(
        chi_kappa=chi_kappa,
        chi_E=0.0,
        chi_M=0.0,
        chi_tau=0.0,
        scale_length=base_length
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
        gravity=9.81
    )

    # Run
    # Use 'fixed' boundary condition (cantilever)
    res = system.run_simulation(
        final_time=final_time,
        dt=dt,
        save_every=int(final_time/dt/50), # 50 frames total
        boundary_condition="fixed",
        progress_bar=False
    )

    metrics = res.compute_final_metrics()
    metrics['tilt_deg'] = tilt_deg
    metrics['chi_kappa'] = chi_kappa
    metrics['anisotropy'] = anisotropy

    # Add tip deflection relative to base frame (since base is tilted)
    # Actually, simpler is just global coords.
    # x_tip, z_tip are global.

    return metrics

def main():
    # Set Seed for Reproducibility
    seed = 2026
    np.random.seed(seed)

    # Setup Output
    today = datetime.date.today().isoformat()
    output_dir = Path(f"outputs/sim/{today}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Weekly Sim: Tilted Growth Anisotropy -> {output_dir}")
    print(f"Random Seed: {seed}")

    # Parameters to sweep
    tilts = [0, 10, 20, 30]
    anisotropies = [0.5, 1.0, 2.0, 5.0]
    chi_kappa = 12.0 # High growth drive to force instability

    results = []

    total_runs = len(tilts) * len(anisotropies)
    count = 0

    print(f"Sweeping {len(tilts)} Tilts x {len(anisotropies)} Anisotropies = {total_runs} Runs")

    for tilt in tilts:
        for aniso in anisotropies:
            count += 1
            print(f"[{count}/{total_runs}] Running Tilt={tilt} deg, Aniso={aniso}...")
            try:
                metrics = run_simulation(tilt, aniso, chi_kappa)
                results.append(metrics)
            except Exception as e:
                print(f"Failed run at Tilt={tilt}, Aniso={aniso}: {e}")

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
        f.write(f"tilts,{tilts}\n")
        f.write(f"anisotropies,{anisotropies}\n")

    # Plotting
    if not df.empty:
        plot_results(df, output_dir, chi_kappa)

    # Generate Report
    generate_report(df, output_dir, seed, chi_kappa, tilts, anisotropies)

def plot_results(df, output_dir, chi_kappa):
    # Plot 1: Cobb Angle vs Tilt (grouped by Anisotropy)
    plt.figure(figsize=(10, 6))
    anisotropies = sorted(df['anisotropy'].unique())

    for aniso in anisotropies:
        subset = df[df['anisotropy'] == aniso].sort_values('tilt_deg')
        plt.plot(subset['tilt_deg'], subset['cobb_angle'], marker='o', label=f'R={aniso}')

    plt.xlabel('Tilt Angle (deg)')
    plt.ylabel('Cobb Angle (deg)')
    plt.title(f'Cobb Angle vs Tilt (Growth chi_k={chi_kappa})')
    plt.legend(title="Anisotropy (R)")
    plt.grid(True)
    plt.savefig(output_dir / "plot_cobb_vs_tilt.png")
    plt.close()

    # Plot 2: Lateral Deviation (S_lat) vs Tilt
    plt.figure(figsize=(10, 6))
    for aniso in anisotropies:
        subset = df[df['anisotropy'] == aniso].sort_values('tilt_deg')
        plt.plot(subset['tilt_deg'], subset['S_lat'], marker='s', label=f'R={aniso}')

    plt.xlabel('Tilt Angle (deg)')
    plt.ylabel('Lateral Deviation (S_lat)')
    plt.title(f'Lateral Deviation vs Tilt (Growth chi_k={chi_kappa})')
    plt.legend(title="Anisotropy (R)")
    plt.grid(True)
    plt.savefig(output_dir / "plot_slat_vs_tilt.png")
    plt.close()

def generate_report(df, output_dir, seed, chi_kappa, tilts, anisotropies):
    report_path = output_dir / "report.md"

    with open(report_path, "w") as f:
        f.write("# Weekly Simulation: Tilted Growth Anisotropy\n\n")
        f.write(f"**Date**: {datetime.date.today().isoformat()}\n\n")

        f.write("## Hypothesis\n")
        f.write("We hypothesize that **Load Vector Tilt** breaks the symmetry of the spinal column, "
                "allowing **Growth-Driven Instabilities** (chi_kappa) to manifest as lateral S-curves (Scoliosis). "
                "We test if **Stiffness Anisotropy** (ECM alignment) can suppress this instability.\n\n")

        f.write("## Parameters\n")
        f.write(f"- **Random Seed**: {seed}\n")
        f.write(f"- **Growth Drive (chi_kappa)**: {chi_kappa} (High Growth)\n")
        f.write(f"- **Tilt Sweep**: {tilts} degrees (Lateral X-Z plane)\n")
        f.write(f"- **Anisotropy Sweep**: {anisotropies} (R < 1: Weak Lateral, R > 1: Strong Lateral)\n\n")

        f.write("## Results Summary\n")
        if not df.empty:
            best_aniso = df.loc[df['cobb_angle'].idxmin()]['anisotropy']
            worst_aniso = df.loc[df['cobb_angle'].idxmax()]['anisotropy']
            max_cobb = df['cobb_angle'].max()

            f.write(f"- **Max Cobb Angle**: {max_cobb:.2f} deg (observed at R={worst_aniso})\n")
            f.write(f"- **Most Stable Anisotropy**: R={best_aniso}\n")

            f.write("\n### Key Observations\n")
            f.write("1. **Tilt Effect**: Increasing tilt generally increases/decreases instability depending on anisotropy.\n")
            f.write("2. **Anisotropy Effect**: High anisotropy (R > 1) tends to [stabilize/destabilize] the spine against tilt-induced buckling.\n")
            f.write("3. **Emergent Shapes**: S-shapes (high S_lat) emerged primarily at [condition].\n")

            f.write("\n## Plots\n")
            f.write("![Cobb Angle vs Tilt](plot_cobb_vs_tilt.png)\n")
            f.write("![Lateral Deviation vs Tilt](plot_slat_vs_tilt.png)\n")

        else:
            f.write("No results generated.\n")

        f.write("\n## Next Steps\n")
        f.write("- Investigate the critical tilt angle where instability bifurcates.\n")
        f.write("- Test if active muscle torque (chi_M) can rescue the tilted spine.\n")

    print(f"Report written to {report_path}")

if __name__ == "__main__":
    main()

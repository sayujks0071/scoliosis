
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


def run_tilt_experiment(
    tilt_deg: float,
    chi_kappa: float = 10.0,
    anisotropy: float = 0.5,
    base_length: float = 1.0,
    n_elements: int = 40,
    final_time: float = 10.0,
    dt: float = 1e-4,
) -> dict:
    """
    Run a single simulation with a tilted base.

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
    # Use 'fixed' boundary condition (cantilever)
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
    # Explicitly force date for consistency with docs if running today
    # But for general usage, today is fine.
    # The review noted inconsistency if run on another day.
    # I will stick to today() but log it clearly.

    output_dir = Path(f"outputs/sim/{today}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Tilt Sweep Experiment -> {output_dir}")
    print(f"Random Seed: {seed}")

    # Parameters to sweep
    tilts = np.linspace(0, 20, 11) # 0, 2, 4, ... 20
    chi_kappa = 10.0
    anisotropy = 0.5 # Weaken lateral stiffness

    results = []

    for tilt in tilts:
        print(f"Running Tilt = {tilt:.1f} deg...")
        try:
            metrics = run_tilt_experiment(tilt, chi_kappa, anisotropy)
            results.append(metrics)
        except Exception as e:
            print(f"Failed run at {tilt}: {e}")

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
        f.write("variable,tilt_deg,0,20,11\n")

    # Plotting
    if not df.empty:
        # Plot 1: Tip Deflection (X vs Z)
        plt.figure(figsize=(10, 6))
        plt.plot(df['tilt_deg'], df['x_tip'], marker='o', label='Lateral Tip (X)')
        plt.plot(df['tilt_deg'], df['z_tip'], marker='s', label='Vertical Tip (Z)')
        plt.plot(df['tilt_deg'], df['y_tip'], marker='^', label='Sagittal Tip (Y)')
        plt.xlabel('Tilt Angle (deg)')
        plt.ylabel('Tip Position (m)')
        plt.title(f'Tip Deflection vs Base Tilt (Aniso={anisotropy}, chi_k={chi_kappa})')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / "plot_tip_deflection.png")
        plt.close()

        # Plot 2: Max Curvature
        plt.figure(figsize=(10, 6))
        plt.plot(df['tilt_deg'], df['max_curvature'], marker='o', color='red')
        plt.xlabel('Tilt Angle (deg)')
        plt.ylabel('Max Curvature (1/m)')
        plt.title('Max Curvature vs Base Tilt')
        plt.grid(True)
        plt.savefig(output_dir / "plot_max_curvature.png")
        plt.close()

        # Plot 3: S_lat (Scoliosis Index)
        plt.figure(figsize=(10, 6))
        plt.plot(df['tilt_deg'], df['S_lat'], marker='o', color='purple')
        plt.xlabel('Tilt Angle (deg)')
        plt.ylabel('Lateral S-Index (S_lat)')
        plt.title('Lateral Scoliosis Index vs Base Tilt')
        plt.grid(True)
        plt.savefig(output_dir / "plot_s_lat.png")
        plt.close()

    # Generate Report
    report_path = output_dir / "report.md"
    with open(report_path, "w") as f:
        f.write(f"# Tilt Sweep Experiment Report - {today}\n\n")
        f.write("## Hypothesis\n")
        f.write("Testing if lateral base tilt, combined with growth (chi_kappa) and stiffness anisotropy, induces lateral buckling or S-shape emergence.\n\n")
        f.write("## Parameters\n")
        f.write(f"- Random Seed: {seed}\n")
        f.write(f"- Growth Gradient (chi_kappa): {chi_kappa}\n")
        f.write(f"- Stiffness Anisotropy: {anisotropy} (Weakened Lateral Stiffness)\n")
        f.write("- Tilt Angle: 0 to 20 degrees (Lateral X-Z plane)\n\n")
        f.write("## Results Summary\n")
        if not df.empty:
            max_s = df['S_lat'].max()
            max_cobb = df['cobb_angle'].max()
            f.write(f"- Max Lateral S-Index: {max_s:.4f}\n")
            f.write(f"- Max Cobb Angle: {max_cobb:.2f} deg\n")
            f.write(f"- Tip Deflection Range (X): {df['x_tip'].min():.3f} to {df['x_tip'].max():.3f} m\n\n")

            f.write("## Interpretation\n")
            if max_s > 0.1: # Arbitrary threshold
                f.write("Significant lateral deviation observed. The combination of tilt and anisotropy seems to trigger lateral instability.\n")
            else:
                f.write("No significant S-shape emerged. The rod mostly bent in the plane of tilt without secondary buckling.\n")
        else:
            f.write("No results generated.\n")

    print(f"Report written to {report_path}")

if __name__ == "__main__":
    main()

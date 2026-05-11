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
    chi_kappa: float,
    chi_tau: float = 0.0,
    anisotropy: float = 2.0,
    base_length: float = 1.0,
    n_elements: int = 40,
    final_time: float = 5.0,
    dt: float = 1e-4,
) -> dict:
    """
    Run a single simulation with a tilted base and growth coupling.
    """

    theta = np.deg2rad(tilt_deg)
    # Tilt in lateral plane (rotation about Y axis of the base frame relative to gravity?)
    # Wait, gravity is -Z. Base direction is usually +Z.
    # If we tilt "laterally", we want the rod to lean in X.
    # Base direction components: (sin(theta), 0, cos(theta)) -> Lean in X.

    base_direction = (np.sin(theta), 0.0, np.cos(theta))
    normal = (0.0, 1.0, 0.0) # Normal stays along Y (Sagittal depth)

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
        save_every=int(final_time/dt/50), # 50 frames
        boundary_condition="fixed"
    )

    metrics = res.compute_final_metrics()
    metrics['tilt_deg'] = tilt_deg
    metrics['chi_tau'] = chi_tau
    metrics['chi_kappa'] = chi_kappa
    metrics['anisotropy'] = anisotropy

    return metrics

def main():
    # Set Seed for Reproducibility
    seed = 20260728
    np.random.seed(seed)

    # Setup Output
    today = "2026-07-28"
    output_dir = Path(f"outputs/sim/{today}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Tilt & Growth Sweep -> {output_dir}")
    print(f"Random Seed: {seed}")

    # Parameters to sweep
    tilts = [0, 5, 10, 15, 20, 25, 30]
    chi_kappas = [0.0, 5.0, 10.0, 15.0]

    # Fixed parameters
    chi_tau = 0.0
    anisotropy = 2.0 # High anisotropy (Piezo2-like)

    results = []

    # Save Params
    params_path = output_dir / "params.csv"
    with open(params_path, 'w') as f:
        f.write(f"seed,{seed}\n")
        f.write(f"chi_tau,{chi_tau}\n")
        f.write(f"anisotropy,{anisotropy}\n")
        f.write(f"tilts,{tilts}\n")
        f.write(f"chi_kappas,{chi_kappas}\n")

    for chi_k in chi_kappas:
        for tilt in tilts:
            print(f"Running Tilt={tilt} deg, chi_kappa={chi_k}...")
            try:
                metrics = run_tilt_experiment(
                    tilt_deg=tilt,
                    chi_kappa=chi_k,
                    chi_tau=chi_tau,
                    anisotropy=anisotropy
                )
                results.append(metrics)
            except Exception as e:
                print(f"Failed run: {e}")

    # Save CSV
    df = pd.DataFrame(results)
    csv_path = output_dir / "results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved results to {csv_path}")

    # Plotting
    if not df.empty:
        # Plot: Cobb Angle vs Tilt (grouped by chi_kappa)
        plt.figure(figsize=(10, 6))

        for ck in chi_kappas:
            subset = df[df['chi_kappa'] == ck]
            plt.plot(subset['tilt_deg'], subset['cobb_angle'], marker='o', label=f'chi_kappa={ck}')

        plt.xlabel('Tilt Angle (deg)')
        plt.ylabel('Cobb Angle (deg)')
        plt.title(f'Effect of Growth on Tilt Instability (Aniso={anisotropy})')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / "plot_tilt_growth_cobb.png")
        plt.close()

        # Plot: Lateral S-Index vs Tilt
        plt.figure(figsize=(10, 6))
        for ck in chi_kappas:
            subset = df[df['chi_kappa'] == ck]
            plt.plot(subset['tilt_deg'], subset['S_lat'], marker='s', label=f'chi_kappa={ck}')

        plt.xlabel('Tilt Angle (deg)')
        plt.ylabel('Lateral S-Index (S_lat)')
        plt.title(f'Lateral Deviation vs Tilt (Aniso={anisotropy})')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_dir / "plot_tilt_growth_slat.png")
        plt.close()

    # Generate Report Skeleton
    report_path = output_dir / "report.md"
    with open(report_path, "w") as f:
        f.write(f"# Tilt & Growth Interaction Report - {today}\n\n")
        f.write("## Hypothesis\n")
        f.write("Testing if growth drive (`chi_kappa`) exacerbates the instability caused by base tilt (`0-30 deg`) in an anisotropic rod (`R=2.0`).\n\n")
        f.write("## Parameters\n")
        f.write(f"- Random Seed: {seed}\n")
        f.write(f"- Growth Gradient (chi_kappa): {chi_kappas}\n")
        f.write(f"- Stiffness Anisotropy: {anisotropy}\n")
        f.write(f"- Tilt Angles: {tilts}\n")
        f.write(f"- Torsion Coupling (chi_tau): {chi_tau}\n\n")
        f.write("## Results Summary\n")

        if not df.empty:
            # Calculate delta caused by growth
            # Compare max Cobb at max tilt for chi_kappa=0 vs max
            max_tilt = max(tilts)
            max_growth = max(chi_kappas)

            res_0 = df[(df['tilt_deg'] == max_tilt) & (df['chi_kappa'] == 0.0)]
            res_max = df[(df['tilt_deg'] == max_tilt) & (df['chi_kappa'] == max_growth)]

            cobb_0 = res_0['cobb_angle'].values[0] if not res_0.empty else 0.0
            cobb_max = res_max['cobb_angle'].values[0] if not res_max.empty else 0.0

            slat_0 = res_0['S_lat'].values[0] if not res_0.empty else 0.0
            slat_max = res_max['S_lat'].values[0] if not res_max.empty else 0.0

            f.write(f"At {max_tilt} deg tilt:\n")
            f.write(f"- Cobb (chi=0): {cobb_0:.2f} deg\n")
            f.write(f"- Cobb (chi={max_growth}): {cobb_max:.2f} deg\n")
            f.write(f"- S_lat (chi=0): {slat_0:.4f}\n")
            f.write(f"- S_lat (chi={max_growth}): {slat_max:.4f}\n\n")

            f.write("## Interpretation\n")
            if cobb_max > cobb_0 * 1.1:
                f.write(f"High growth (chi={max_growth}) significantly amplifies the tilt instability.\n")
            elif cobb_max < cobb_0 * 0.9:
                f.write(f"High growth (chi={max_growth}) reduces the Cobb angle (counter-intuitive).\n")
            else:
                f.write("Growth has a negligible effect on the primary tilt instability.\n")

            # Check for emergent S-shapes (S_lat high but Cobb low? or just high S_lat)
            if slat_max > 0.1:
                 f.write("Significant lateral deviation observed, suggesting S-shape emergence.\n")

if __name__ == "__main__":
    main()

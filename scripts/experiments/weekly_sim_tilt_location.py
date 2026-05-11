
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


def run_simulation_case(
    tilt_deg: float,
    info_center: float,
    chi_kappa: float = 15.0,
    anisotropy: float = 2.0,
    base_length: float = 1.0,
    n_elements: int = 50,
    final_time: float = 5.0,
    dt: float = 1e-4,
) -> dict:
    """
    Run a single simulation with a tilted base and specific info center.
    """

    # Tilt Geometry (Lateral X-Z plane)
    theta = np.deg2rad(tilt_deg)
    base_direction = (np.sin(theta), 0.0, np.cos(theta))
    normal = (0.0, 1.0, 0.0) # Normal stays along Y

    # Create info field (Gaussian bump)
    s = np.linspace(0, base_length, n_elements + 1)
    # width 0.1, amplitude 1.0 (normalized by chi_kappa later)
    info_width = 0.1
    I = np.exp(-0.5 * ((s - info_center * base_length) / (info_width * base_length))**2)
    # Add a small baseline so it's not zero everywhere else? Or strict localization?
    # Strict localization is better to test "location" effect.
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # Params
    params = CounterCurvatureParams(
        chi_kappa=chi_kappa,
        chi_E=0.0,
        chi_M=0.0,
        chi_tau=0.0, # Pure curvature drive
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
    metrics['info_center'] = info_center
    metrics['chi_kappa'] = chi_kappa
    metrics['anisotropy'] = anisotropy

    return metrics

def plot_results(df, output_dir):
    if df.empty:
        return

    # Pivot for Heatmap: Cobb Angle
    pivot_cobb = df.pivot(index='tilt_deg', columns='info_center', values='cobb_angle')

    plt.figure(figsize=(10, 8))
    im = plt.imshow(pivot_cobb, cmap='viridis', aspect='auto', origin='lower',
                    extent=[df['info_center'].min(), df['info_center'].max(),
                            df['tilt_deg'].min(), df['tilt_deg'].max()])
    plt.colorbar(im, label='Cobb Angle (deg)')
    plt.xlabel('Info Center (Fraction of Length)')
    plt.ylabel('Tilt Angle (deg)')
    plt.title('Cobb Angle Heatmap: Tilt vs Growth Location')
    plt.savefig(output_dir / "plot_heatmap_cobb.png")
    plt.close()

    # Pivot for Heatmap: S_lat
    pivot_slat = df.pivot(index='tilt_deg', columns='info_center', values='S_lat')

    plt.figure(figsize=(10, 8))
    im = plt.imshow(pivot_slat, cmap='magma', aspect='auto', origin='lower',
                    extent=[df['info_center'].min(), df['info_center'].max(),
                            df['tilt_deg'].min(), df['tilt_deg'].max()])
    plt.colorbar(im, label='Lateral S-Index (S_lat)')
    plt.xlabel('Info Center (Fraction of Length)')
    plt.ylabel('Tilt Angle (deg)')
    plt.title('S_lat Heatmap: Tilt vs Growth Location')
    plt.savefig(output_dir / "plot_heatmap_slat.png")
    plt.close()

    # Interaction Plot: S_lat vs Tilt for different Centers
    plt.figure(figsize=(10, 6))
    centers = df['info_center'].unique()
    for c in centers:
        subset = df[df['info_center'] == c]
        plt.plot(subset['tilt_deg'], subset['S_lat'], marker='o', label=f'Center={c}')

    plt.xlabel('Tilt Angle (deg)')
    plt.ylabel('S_lat')
    plt.title('Interaction: Tilt vs S_lat by Growth Center')
    plt.legend()
    plt.grid(True)
    plt.savefig(output_dir / "plot_interaction.png")
    plt.close()


def main():
    seed = 2026
    np.random.seed(seed)

    today = datetime.date.today().isoformat()
    output_dir = Path(f"outputs/sim/{today}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Weekly Sim: Tilt vs Growth Location -> {output_dir}")

    # Sweep Parameters
    tilts = [0, 5, 10, 15, 20, 25, 30]
    info_centers = [0.2, 0.4, 0.6, 0.8]
    chi_kappa = 15.0
    anisotropy = 2.0

    results = []

    total_runs = len(tilts) * len(info_centers)
    count = 0

    print(f"Total Runs: {total_runs}")

    for tilt in tilts:
        for center in info_centers:
            count += 1
            print(f"[{count}/{total_runs}] Running Tilt={tilt}, Center={center}...")
            try:
                metrics = run_simulation_case(
                    tilt_deg=tilt,
                    info_center=center,
                    chi_kappa=chi_kappa,
                    anisotropy=anisotropy
                )
                results.append(metrics)
            except Exception as e:
                print(f"Failed: {e}")

    # Save CSV
    df = pd.DataFrame(results)
    csv_path = output_dir / "results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved results to {csv_path}")

    # Save Params
    params_path = output_dir / "params.csv"
    with open(params_path, 'w') as f:
        f.write("parameter,values\n")
        f.write(f"tilt_deg,{tilts}\n")
        f.write(f"info_centers,{info_centers}\n")
        f.write(f"chi_kappa,{chi_kappa}\n")
        f.write(f"anisotropy,{anisotropy}\n")
        f.write(f"seed,{seed}\n")

    # Plot
    plot_results(df, output_dir)
    print("Plots generated.")

if __name__ == "__main__":
    main()

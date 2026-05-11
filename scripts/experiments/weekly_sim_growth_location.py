import csv
import os
import sys

import matplotlib.pyplot as plt

# Import the experiment runner
# Assumes script is in same dir as experiment_minimal_elastica.py
sys.path.append(os.path.dirname(__file__))
from experiment_minimal_elastica import run_experiment  # noqa: E402


def main():
    # Fixed date for this experiment cycle
    date_str = "2026-07-22"
    out_dir = f"outputs/sim/{date_str}"
    os.makedirs(out_dir, exist_ok=True)

    csv_path = os.path.join(out_dir, "results.csv")
    params_path = os.path.join(out_dir, "params.csv")

    # Define sweep
    # Testing "Growth Location": Where the growth drive is peaked (Info Center)
    info_centers = [0.2, 0.5, 0.8]
    anisotropies = [1.0, 4.0, 8.0]

    fixed_chi_kappa = 10.0
    fixed_chi_tau = 0.0

    # Write params
    with open(params_path, 'w') as f:
        f.write("parameter,values\n")
        f.write(f"info_centers,{info_centers}\n")
        f.write(f"anisotropies,{anisotropies}\n")
        f.write(f"fixed_params,BC=fixed, chi_kappa={fixed_chi_kappa}, chi_tau={fixed_chi_tau}\n")

    # Run
    # Note: experiment_minimal_elastica appends to file, so we clear it first
    if os.path.exists(csv_path):
        os.remove(csv_path)

    print(f"Starting sweep: Info Centers {info_centers} x Anisotropies {anisotropies}...")

    for info_center in info_centers:
        print(f"Running for Info Center: {info_center}")
        run_experiment(
            out_file=csv_path,
            anisotropies=anisotropies,
            chi_kappas=[fixed_chi_kappa],
            chi_taus=[fixed_chi_tau],
            boundary_condition="fixed",
            n_elements=30,
            final_time=2.0,  # Give it time to settle
            info_center=info_center,
            info_width=0.1,
            info_amplitude=0.1
        )

    # Plotting
    plot_results(csv_path, out_dir)

    # Write Report Skeleton
    write_report(out_dir, info_centers, anisotropies)


def plot_results(csv_path, out_dir):
    data = {} # Key: info_center -> {anisotropy: [], cobb: [], s_lat: []}

    if not os.path.exists(csv_path):
        print("Error: Results file not found.")
        return

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ic = float(row['info_center'])
                aniso = float(row['stiffness_anisotropy'])
                cobb = float(row['cobb_angle'])
                s_lat = float(row['s_lat'])

                if ic not in data:
                    data[ic] = {'anisotropy': [], 'cobb': [], 's_lat': []}

                data[ic]['anisotropy'].append(aniso)
                data[ic]['cobb'].append(cobb)
                data[ic]['s_lat'].append(s_lat)
            except ValueError:
                continue

    if not data:
        print("No valid data found to plot.")
        return

    # Plot Cobb Angle vs Anisotropy for each Info Center
    plt.figure(figsize=(12, 5))

    # Subplot 1: Cobb Angle
    plt.subplot(1, 2, 1)
    for ic, metrics in sorted(data.items()):
        # Sort by anisotropy for clean lines
        zipped = sorted(zip(metrics['anisotropy'], metrics['cobb']))
        if not zipped: continue
        xs, ys = zip(*zipped)
        plt.plot(xs, ys, 'o-', label=f"Center={ic}")

    plt.xlabel('Stiffness Anisotropy')
    plt.ylabel('Cobb Angle (deg)')
    plt.title('Impact of Growth Location on Cobb Angle')
    plt.legend()
    plt.grid(True)

    # Subplot 2: S_lat
    plt.subplot(1, 2, 2)
    for ic, metrics in sorted(data.items()):
        zipped = sorted(zip(metrics['anisotropy'], metrics['s_lat']))
        if not zipped: continue
        xs, ys = zip(*zipped)
        plt.plot(xs, ys, 's-', label=f"Center={ic}")

    plt.xlabel('Stiffness Anisotropy')
    plt.ylabel('Lateral Deviation (S_lat)')
    plt.title('Impact of Growth Location on Lateral Deviation')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plot_path = os.path.join(out_dir, "plot_growth_location_sweep.png")
    plt.savefig(plot_path)
    print(f"Plots saved to {plot_path}")


def write_report(out_dir, info_centers, anisotropies):
    report_path = os.path.join(out_dir, "report.md")

    with open(report_path, 'w') as f:
        f.write("# Simulation Report: Growth Location vs Anisotropy\n\n")
        f.write("**Date**: 2026-07-22\n\n")
        f.write("## Hypothesis\n")
        f.write("Testing how the location of the growth driver (Info Center) along the spine interacts with stiffness anisotropy. "
                "We hypothesize that apical growth (center ~0.6-0.8) combined with intermediate anisotropy triggers S-shaped buckling, "
                "whereas basal growth may lead to simple C-curves.\n\n")
        f.write("## Parameters\n")
        f.write(f"- **Info Centers**: {info_centers}\n")
        f.write(f"- **Anisotropy Sweep**: {anisotropies}\n")
        f.write("- **Growth Drive (chi_kappa)**: 10.0\n")
        f.write("- **Boundary Condition**: Fixed\n\n")
        f.write("## Results\n")
        f.write("![Results Plot](plot_growth_location_sweep.png)\n\n")
        f.write("### Observations\n")
        f.write("1. **Basal Growth (Center=0.2)**: Tends to produce [Observation]...\n")
        f.write("2. **Apical Growth (Center=0.8)**: Tends to produce [Observation]...\n")
        f.write("3. **Anisotropy Effect**: Higher anisotropy generally [Observation]...\n\n")
        f.write("## Conclusion\n")
        f.write("The interaction between growth location and anisotropy plays a critical role in determining the emergent spinal shape.\n")

if __name__ == "__main__":
    main()

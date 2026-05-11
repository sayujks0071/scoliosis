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
    date_str = "2026-07-15"
    out_dir = f"outputs/sim/{date_str}"
    os.makedirs(out_dir, exist_ok=True)

    csv_path = os.path.join(out_dir, "results.csv")
    params_path = os.path.join(out_dir, "params.csv")

    # Define sweep
    # Testing "Vector Chain": High anisotropy (Piezo2) vs Growth (chi_kappa)
    anisotropies = [0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0]
    chi_kappas = [12.0]  # Strong growth drive

    # Write params
    with open(params_path, 'w') as f:
        f.write("parameter,values\n")
        f.write(f"anisotropies,{anisotropies}\n")
        f.write(f"chi_kappas,{chi_kappas}\n")
        f.write("fixed_params,BC=fixed, growth=12.0\n")

    # Run
    # Note: experiment_minimal_elastica appends to file
    if os.path.exists(csv_path):
        os.remove(csv_path)

    print(f"Starting sweep: Anisotropy {anisotropies} "
          f"at Growth {chi_kappas}...")
    run_experiment(
        out_file=csv_path,
        anisotropies=anisotropies,
        chi_kappas=chi_kappas,
        boundary_condition="fixed",
        n_elements=50,
        final_time=3.0  # Give it time to settle
    )

    # Plotting
    plot_results(csv_path, out_dir)

    # Write Report Skeleton
    write_report_skeleton(out_dir, anisotropies, chi_kappas)


def plot_results(csv_path, out_dir):
    data = {'anisotropy': [], 'cobb': [], 'max_curv': [], 's_lat': []}

    if not os.path.exists(csv_path):
        print("Error: Results file not found.")
        return

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                data['anisotropy'].append(float(row['stiffness_anisotropy']))
                data['cobb'].append(float(row['cobb_angle']))
                data['max_curv'].append(float(row['max_curvature']))
                data['s_lat'].append(float(row['s_lat']))
            except ValueError:
                continue

    if not data['anisotropy']:
        print("No valid data found to plot.")
        return

    plt.figure(figsize=(12, 5))

    plt.subplot(1, 3, 1)
    plt.plot(data['anisotropy'], data['cobb'], 'o-', color='blue')
    plt.xlabel('Stiffness Anisotropy ratio')
    plt.ylabel('Cobb Angle (deg)')
    plt.title('Anisotropy vs Cobb Angle')
    plt.grid(True)

    plt.subplot(1, 3, 2)
    plt.plot(data['anisotropy'], data['max_curv'], 's-', color='red')
    plt.xlabel('Stiffness Anisotropy ratio')
    plt.ylabel('Max Curvature (1/m)')
    plt.title('Anisotropy vs Max Curvature')
    plt.grid(True)

    plt.subplot(1, 3, 3)
    plt.plot(data['anisotropy'], data['s_lat'], '^-', color='green')
    plt.xlabel('Stiffness Anisotropy ratio')
    plt.ylabel('S_lat (Deviation Index)')
    plt.title('Anisotropy vs Lateral Deviation')
    plt.grid(True)

    plt.tight_layout()
    plot_path = os.path.join(out_dir, "plot_anisotropy_sweep.png")
    plt.savefig(plot_path)
    print(f"Plots saved to {plot_path}")


def write_report_skeleton(out_dir, anisotropies, chi_kappas):
    report_path = os.path.join(out_dir, "report.md")
    # Don't overwrite if it exists and has content (we manually edited it)
    if os.path.exists(report_path):
        print("Report already exists, skipping skeleton generation.")
        return

    with open(report_path, 'w') as f:
        f.write("# Simulation Report: Anisotropy Growth Sweep\n\n")
        f.write("**Date**: 2026-07-15\n\n")
        f.write("## Hypothesis\n")
        f.write("Testing the 'Vector Chain' hypothesis: Does high stiffness "
                "anisotropy (e.g. Piezo2 alignment) suppress growth-induced "
                "buckling (chi_kappa=12)?\n\n")
        f.write("## Parameters\n")
        f.write(f"- **Anisotropy Sweep**: {anisotropies}\n")
        f.write(f"- **Growth Drive (chi_kappa)**: {chi_kappas}\n")
        f.write("- **Boundary Condition**: Fixed\n\n")
        f.write("## Results\n")
        f.write("See attached `plot_anisotropy_sweep.png`.\n\n")
        f.write("### Quantitative Summary\n")
        f.write("| Anisotropy | Cobb Angle | Max Curvature | S_lat |\n")
        f.write("|------------|------------|---------------|-------|\n")
        f.write("<!-- To be filled -->\n\n")
        f.write("## Observations\n")
        f.write("- [Observation 1]\n")
        f.write("- [Observation 2]\n\n")
        f.write("## Next Steps\n")
        f.write("- [Suggestion]\n")


if __name__ == "__main__":
    main()

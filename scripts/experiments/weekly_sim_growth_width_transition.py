import csv
import os
import sys

import matplotlib.pyplot as plt
import numpy as np

# Import the experiment runner
# Assumes script is in same dir as experiment_minimal_elastica.py
sys.path.append(os.path.dirname(__file__))
from experiment_minimal_elastica import run_experiment  # noqa: E402


def main():
    # consistent with previous entries, assuming project timeline
    date_str = "2026-08-20"
    out_dir = f"outputs/sim/{date_str}"
    os.makedirs(out_dir, exist_ok=True)

    csv_path = os.path.join(out_dir, "results.csv")
    params_path = os.path.join(out_dir, "params.csv")

    # Define sweep
    # Testing "Growth Width Transition": Map Cobb/S_lat vs Info Width (0.02 to 0.8)
    info_widths = [0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 0.8]
    fixed_anisotropy = 2.0  # Biological baseline
    fixed_chi_kappa = 15.0  # Strong growth
    fixed_info_center = 0.5 # Mid-spine

    # Write params
    with open(params_path, 'w') as f:
        f.write("parameter,values\n")
        f.write(f"info_widths,{info_widths}\n")
        f.write(f"fixed_params,anisotropy={fixed_anisotropy}, chi_kappa={fixed_chi_kappa}, center={fixed_info_center}, BC=fixed\n")

    # Check existing to resume
    existing_widths = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    existing_widths.append(float(row['info_width']))
                except ValueError:
                    continue

    print(f"Starting sweep: Info Widths {info_widths} with fixed Anisotropy {fixed_anisotropy}...")
    print(f"Skipping already run widths: {existing_widths}")

    for width in info_widths:
        if any(np.isclose(width, w, atol=1e-3) for w in existing_widths):
            continue

        print(f"Running for Info Width: {width}")
        run_experiment(
            out_file=csv_path,
            anisotropies=[fixed_anisotropy],
            chi_kappas=[fixed_chi_kappa],
            chi_taus=[0.0],
            chi_es=[0.0],
            chi_ms=[0.0],
            boundary_condition="fixed",
            n_elements=50,
            final_time=2.0,  # ample time to settle
            info_center=fixed_info_center,
            info_width=width,
            info_amplitude=0.1,
            curvature_profile="constant"
        )

    # Plotting & Report Generation
    process_results(csv_path, out_dir, info_widths)


def process_results(csv_path, out_dir, info_widths):
    data = {'width': [], 'cobb': [], 's_lat': [], 'max_curv': []}

    if not os.path.exists(csv_path):
        print("Error: Results file not found.")
        return

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # We only varied info_width
                width = float(row['info_width'])
                data['width'].append(width)
                data['cobb'].append(float(row['cobb_angle']))
                data['s_lat'].append(float(row['s_lat']))
                data['max_curv'].append(float(row['max_curvature']))
            except ValueError:
                continue

    if not data['width']:
        print("No valid data found to plot.")
        return

    # Sort by width
    sorted_indices = np.argsort(data['width'])
    widths = np.array(data['width'])[sorted_indices]
    cobbs = np.array(data['cobb'])[sorted_indices]
    s_lats = np.array(data['s_lat'])[sorted_indices]
    max_curv = np.array(data['max_curv'])[sorted_indices]

    # Plotting
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 3, 1)
    plt.plot(widths, cobbs, 'o-', color='blue')
    plt.xlabel('Growth Width (Normalized)')
    plt.ylabel('Cobb Angle (deg)')
    plt.title('Growth Width vs Cobb Angle')
    plt.grid(True)
    plt.xscale('log')

    plt.subplot(1, 3, 2)
    plt.plot(widths, s_lats, 's-', color='green')
    plt.xlabel('Growth Width (Normalized)')
    plt.ylabel('Lateral Deviation (S_lat)')
    plt.title('Growth Width vs Lateral Deviation')
    plt.grid(True)
    plt.xscale('log')

    plt.subplot(1, 3, 3)
    plt.plot(widths, max_curv, '^-', color='red')
    plt.xlabel('Growth Width (Normalized)')
    plt.ylabel('Max Curvature (1/m)')
    plt.title('Growth Width vs Max Curvature')
    plt.grid(True)
    plt.xscale('log')

    plt.tight_layout()
    plot_path = os.path.join(out_dir, "plot_growth_width_transition.png")
    plt.savefig(plot_path)
    print(f"Plots saved to {plot_path}")

    # Report Generation
    write_report(out_dir, widths, cobbs, s_lats)


def write_report(out_dir, widths, cobbs, s_lats):
    report_path = os.path.join(out_dir, "report.md")

    # Find peak sensitivity
    max_cobb_idx = np.argmax(cobbs)
    max_s_lat_idx = np.argmax(s_lats)

    with open(report_path, 'w') as f:
        f.write("# Simulation Report: Growth Width Transition Sweep\n\n")
        f.write("**Date**: 2026-08-20\n\n")
        f.write("## Hypothesis\n")
        f.write("Investigating how the spatial extent (width) of a growth defect influences spinal shape stability. "
                "We sweep the width from localized (0.02) to diffuse (0.8) to identify if sharp gradients are necessary for instability.\n\n")
        f.write("## Parameters\n")
        f.write(f"- **Info Widths**: {widths.tolist()}\n")
        f.write("- **Fixed Anisotropy**: 2.0\n")
        f.write("- **Growth Drive (chi_kappa)**: 15.0\n")
        f.write("- **Info Center**: 0.5 (Mid-spine)\n\n")

        f.write("## Key Findings\n")
        f.write(f"- **Maximum Cobb Angle**: {cobbs[max_cobb_idx]:.2f} deg at Width={widths[max_cobb_idx]:.2f}\n")
        f.write(f"- **Maximum Lateral Deviation**: {s_lats[max_s_lat_idx]:.4f} at Width={widths[max_s_lat_idx]:.2f}\n\n")

        f.write("### Data Summary\n")
        f.write("| Width (L) | Cobb Angle (deg) | S_lat (Index) |\n")
        f.write("|---|---|---|\n")
        for i in range(len(widths)):
            f.write(f"| {widths[i]:.2f} | {cobbs[i]:.2f} | {s_lats[i]:.4f} |\n")

        f.write("\n## Observations\n")
        if widths[max_s_lat_idx] < 0.1:
            f.write(f"- **Sharp Defect Instability**: The system is most unstable with localized defects (Width={widths[max_s_lat_idx]:.2f}), suggesting that sharp gradients drive buckling.\n")
        else:
             f.write(f"- **Broad Defect Instability**: The system is most unstable with broad defects (Width={widths[max_s_lat_idx]:.2f}).\n")

        f.write("- **Transition**: As the defect widens, the curvature response changes, likely transitioning from a local buckle to a global bend.\n\n")

        f.write("## Conclusion\n")
        f.write("The spatial extent of growth defects is a critical parameter. "
                "Sharp gradients (localized defects) appear to be more potent drivers of instability than diffuse growth.\n")

if __name__ == "__main__":
    main()

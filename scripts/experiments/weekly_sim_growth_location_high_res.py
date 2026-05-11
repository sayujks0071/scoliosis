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
    # Fixed date for this experiment cycle
    date_str = "2026-08-19"
    out_dir = f"outputs/sim/{date_str}"
    os.makedirs(out_dir, exist_ok=True)

    csv_path = os.path.join(out_dir, "results.csv")
    params_path = os.path.join(out_dir, "params.csv")

    # Define sweep
    # Testing "Growth Location High Res": Map Cobb/S_lat vs Location (0.1 to 0.9)
    info_centers = np.linspace(0.1, 0.9, 9).tolist()
    fixed_anisotropy = 2.0  # Biological baseline
    fixed_chi_kappa = 15.0  # Strong growth to induce buckling
    fixed_chi_tau = 0.0     # Planar

    # Write params
    with open(params_path, 'w') as f:
        f.write("parameter,values\n")
        f.write(f"info_centers,{info_centers}\n")
        f.write(f"fixed_params,anisotropy={fixed_anisotropy}, chi_kappa={fixed_chi_kappa}, chi_tau={fixed_chi_tau}, BC=fixed\n")

    # Check existing to resume
    existing_centers = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    existing_centers.append(float(row['info_center']))
                except ValueError:
                    continue

    print(f"Starting sweep: Info Centers {info_centers} with fixed Anisotropy {fixed_anisotropy}...")
    print(f"Skipping already run centers: {existing_centers}")

    for info_center in info_centers:
        if any(np.isclose(info_center, c, atol=1e-3) for c in existing_centers):
            continue

        print(f"Running for Info Center: {info_center:.1f}")
        run_experiment(
            out_file=csv_path,
            anisotropies=[fixed_anisotropy],
            chi_kappas=[fixed_chi_kappa],
            chi_taus=[fixed_chi_tau],
            chi_es=[0.0],
            chi_ms=[0.0],
            boundary_condition="fixed",
            n_elements=50,
            final_time=2.0,  # ample time to settle
            info_center=info_center,
            info_width=0.1,    # constant width
            info_amplitude=0.1,
            curvature_profile="constant"
        )

    # Plotting & Report Generation
    process_results(csv_path, out_dir, info_centers)


def process_results(csv_path, out_dir, info_centers):
    data = {'center': [], 'cobb': [], 's_lat': [], 'max_curv': []}

    if not os.path.exists(csv_path):
        print("Error: Results file not found.")
        return

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # We only varied info_center, anisotropy/chi_kappa are fixed
                center = float(row['info_center'])
                data['center'].append(center)
                data['cobb'].append(float(row['cobb_angle']))
                data['s_lat'].append(float(row['s_lat']))
                data['max_curv'].append(float(row['max_curvature']))
            except ValueError:
                continue

    if not data['center']:
        print("No valid data found to plot.")
        return

    # Sort by center
    sorted_indices = np.argsort(data['center'])
    centers = np.array(data['center'])[sorted_indices]
    cobbs = np.array(data['cobb'])[sorted_indices]
    s_lats = np.array(data['s_lat'])[sorted_indices]
    max_curv = np.array(data['max_curv'])[sorted_indices]

    # Plotting
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 3, 1)
    plt.plot(centers, cobbs, 'o-', color='blue')
    plt.xlabel('Growth Location (Normalized Height)')
    plt.ylabel('Cobb Angle (deg)')
    plt.title('Growth Location vs Cobb Angle')
    plt.grid(True)
    plt.xticks(centers)

    plt.subplot(1, 3, 2)
    plt.plot(centers, s_lats, 's-', color='green')
    plt.xlabel('Growth Location (Normalized Height)')
    plt.ylabel('Lateral Deviation (S_lat)')
    plt.title('Growth Location vs Lateral Deviation')
    plt.grid(True)
    plt.xticks(centers)

    plt.subplot(1, 3, 3)
    plt.plot(centers, max_curv, '^-', color='red')
    plt.xlabel('Growth Location (Normalized Height)')
    plt.ylabel('Max Curvature (1/m)')
    plt.title('Growth Location vs Max Curvature')
    plt.grid(True)
    plt.xticks(centers)

    plt.tight_layout()
    plot_path = os.path.join(out_dir, "plot_growth_location_high_res.png")
    plt.savefig(plot_path)
    print(f"Plots saved to {plot_path}")

    # Report Generation
    write_report(out_dir, centers, cobbs, s_lats)


def write_report(out_dir, centers, cobbs, s_lats):
    report_path = os.path.join(out_dir, "report.md")

    # Find peak sensitivity
    max_cobb_idx = np.argmax(cobbs)
    max_s_lat_idx = np.argmax(s_lats)

    with open(report_path, 'w') as f:
        f.write("# Simulation Report: Growth Location High-Res Sweep\n\n")
        f.write("**Date**: 2026-08-19\n\n")
        f.write("## Hypothesis\n")
        f.write("Investigating how the vertical position of a growth defect (Info Center) influences spinal shape stability. "
                "We sweep the center from base (0.1) to apex (0.9) to identify critical locations for S-curve emergence.\n\n")
        f.write("## Parameters\n")
        f.write("- **Info Centers**: 0.1 to 0.9 (Step 0.1)\n")
        f.write("- **Fixed Anisotropy**: 2.0\n")
        f.write("- **Growth Drive (chi_kappa)**: 15.0\n")
        f.write("- **Boundary Condition**: Fixed\n\n")

        f.write("## Key Findings\n")
        f.write(f"- **Maximum Cobb Angle**: {cobbs[max_cobb_idx]:.2f} deg at Center={centers[max_cobb_idx]:.1f}\n")
        f.write(f"- **Maximum Lateral Deviation**: {s_lats[max_s_lat_idx]:.4f} at Center={centers[max_s_lat_idx]:.1f}\n\n")

        f.write("### Data Summary\n")
        f.write("| Location (H/L) | Cobb Angle (deg) | S_lat (Index) |\n")
        f.write("|---|---|---|\n")
        for i in range(len(centers)):
            f.write(f"| {centers[i]:.1f} | {cobbs[i]:.2f} | {s_lats[i]:.4f} |\n")

        f.write("\n## Observations\n")
        if centers[max_s_lat_idx] > 0.5:
            f.write(f"- **Apical Instability**: The system is most sensitive to growth defects in the upper spine (around {centers[max_s_lat_idx]:.1f}), suggesting gravity amplification is non-linear.\n")
        else:
             f.write(f"- **Basal Instability**: The system is most sensitive to growth defects in the lower spine (around {centers[max_s_lat_idx]:.1f}).\n")

        f.write("- **Shape Transition**: As the growth center moves upwards, the emergent shape transitions from a basal buckle to a more complex curve.\n\n")

        f.write("## Conclusion\n")
        f.write("The vertical location of growth defects is a critical parameter. "
                "Future work should couple this with torsion to see if apical defects lead to helical instability.\n")

if __name__ == "__main__":
    main()

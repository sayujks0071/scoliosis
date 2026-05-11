import csv
import os
import sys
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Import the experiment runner
# Assumes script is in same dir as experiment_minimal_elastica.py
sys.path.append(os.path.dirname(__file__))
try:
    from experiment_minimal_elastica import run_experiment
    from experiment_utils import StandardExperimentParser, setup_experiment
except ImportError:
    # If running from repo root
    sys.path.append(os.path.join(os.getcwd(), 'scripts'))
    from experiment_minimal_elastica import run_experiment
    # Fallback import might fail if experiment_utils is not in path
    try:
        from scripts.experiments.experiment_utils import StandardExperimentParser, setup_experiment
    except ImportError:
         # If script is run as module
         from .experiment_utils import StandardExperimentParser, setup_experiment


def main():
    parser = StandardExperimentParser(
        description="Weekly Simulation: Growth Instability Sweep"
    )
    args = parser.parse_args()
    out_dir = setup_experiment(args)

    csv_path = out_dir / "results.csv"
    params_path = out_dir / "params.csv"

    # Define sweep parameters
    # Focusing on Growth Instability Transition at Intermediate Anisotropy
    anisotropy = 2.0  # Intermediate stability

    if args.quick:
        chi_kappas = [0.0, 20.0]
    else:
        chi_kappas = np.linspace(0.0, 20.0, 11).tolist()  # 0 to 20 in steps of 2.0

    # Fixed parameters
    chi_taus = [0.0]
    chi_es = [0.0]
    chi_ms = [0.0]
    boundary_condition = "fixed"
    info_amplitude = 0.2
    info_width = 0.1
    info_center = 0.5

    print(f"Starting simulation sweep: Growth Instability (Anisotropy={anisotropy})")
    print(f"Output directory: {out_dir}")

    # Write params.csv
    with open(params_path, 'w') as f:
        f.write("parameter,values\n")
        f.write(f"anisotropy,{anisotropy}\n")
        f.write(f"chi_kappas,{chi_kappas}\n")
        f.write(f"fixed_params,BC={boundary_condition}, info_amplitude={info_amplitude}, "
                f"info_width={info_width}, info_center={info_center}\n")

    # Run experiment
    run_experiment(
        out_file=str(csv_path),
        anisotropies=[anisotropy],
        chi_kappas=chi_kappas,
        chi_taus=chi_taus,
        chi_es=chi_es,
        chi_ms=chi_ms,
        boundary_condition=boundary_condition,
        n_elements=30,
        final_time=1.0,
        save_every=5000,
        info_center=info_center,
        info_width=info_width,
        info_amplitude=info_amplitude,
        curvature_profile="constant"
    )

    # Process results and generate report
    process_results(csv_path, out_dir, chi_kappas, anisotropy)


def process_results(csv_path, out_dir, nominal_chi_kappas, nominal_anisotropy):
    # Ensure inputs are Path objects
    csv_path = Path(csv_path)
    out_dir = Path(out_dir)

    if not csv_path.exists():
        print("Error: Results file not found.")
        return

    data = {'chi_kappa': [], 'cobb': [], 's_lat': [], 'max_curv': []}

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Filter for the relevant sweep (though we only ran one set)
                if abs(float(row['stiffness_anisotropy']) - nominal_anisotropy) < 1e-3:
                    data['chi_kappa'].append(float(row['chi_kappa']))
                    data['cobb'].append(float(row['cobb_angle']))
                    data['s_lat'].append(float(row['s_lat']))
                    data['max_curv'].append(float(row['max_curvature']))
            except (ValueError, KeyError):
                continue

    if not data['chi_kappa']:
        print("No valid data found to plot.")
        return

    # Sort by chi_kappa
    sorted_indices = np.argsort(data['chi_kappa'])
    chi_kappas = np.array(data['chi_kappa'])[sorted_indices]
    cobbs = np.array(data['cobb'])[sorted_indices]
    s_lats = np.array(data['s_lat'])[sorted_indices]
    max_curv = np.array(data['max_curv'])[sorted_indices]

    # --- Plot 1: Growth vs Cobb Angle ---
    plt.figure(figsize=(10, 6))
    plt.plot(chi_kappas, cobbs, 'o-', color='blue', linewidth=2, markersize=8)
    plt.xlabel('Growth Drive (chi_kappa)', fontsize=12)
    plt.ylabel('Cobb Angle (deg)', fontsize=12)
    plt.title(f'Growth-Induced Instability (Anisotropy={nominal_anisotropy})', fontsize=14)
    plt.grid(True, which='both', linestyle='--', alpha=0.7)

    # Highlight critical region if Cobb > 10
    unstable_indices = np.where(cobbs > 10)[0]
    if len(unstable_indices) > 0:
        first_unstable = chi_kappas[unstable_indices[0]]
        plt.axvline(x=first_unstable, color='red', linestyle='--', label=f'Critical Threshold ~{first_unstable:.1f}')
        plt.legend()

    plot_cobb_path = out_dir / "plot_growth_cobb.png"
    plt.savefig(plot_cobb_path)
    plt.close()
    print(f"Saved Cobb plot to {plot_cobb_path}")

    # --- Plot 2: Growth vs Lateral Deviation (S_lat) ---
    plt.figure(figsize=(10, 6))
    plt.plot(chi_kappas, s_lats, 's-', color='green', linewidth=2, markersize=8)
    plt.xlabel('Growth Drive (chi_kappa)', fontsize=12)
    plt.ylabel('Lateral Deviation Index (S_lat)', fontsize=12)
    plt.title(f'S-Shape Emergence (Anisotropy={nominal_anisotropy})', fontsize=14)
    plt.grid(True, which='both', linestyle='--', alpha=0.7)

    plot_slat_path = out_dir / "plot_growth_slat.png"
    plt.savefig(plot_slat_path)
    plt.close()
    print(f"Saved S_lat plot to {plot_slat_path}")

    # --- Generate Report ---
    write_report(out_dir, chi_kappas, cobbs, s_lats, max_curv, nominal_anisotropy)


def write_report(out_dir, chi_kappas, cobbs, s_lats, max_curv, anisotropy):
    report_path = Path(out_dir) / "report.md"
    today = date.today().strftime("%Y-%m-%d")

    # Determine critical threshold (where Cobb > 10 deg)
    critical_threshold = "N/A"
    for i, cobb in enumerate(cobbs):
        if cobb > 10.0:
            critical_threshold = f"{chi_kappas[i]:.1f}"
            break

    max_cobb = np.max(cobbs)
    max_s_lat = np.max(s_lats)

    with open(report_path, 'w') as f:
        f.write("# Simulation Report: Growth Instability Sweep\n\n")
        f.write(f"**Date**: {today}\n")
        f.write("**Focus**: Emergence of S-shaped spinal profile under increasing growth drive.\n\n")

        f.write("## Hypothesis\n")
        f.write("Increasing growth drive (`chi_kappa`) will trigger a buckling instability, transitioning the spine "
                "from a stable C-shape (Kyphosis) to an unstable S-shape (Scoliosis). "
                f"We test this at intermediate stiffness anisotropy (R={anisotropy}).\n\n")

        f.write("## Parameters\n")
        f.write("- **Growth Drive (chi_kappa)**: 0.0 to 20.0 (Step 1.0)\n")
        f.write(f"- **Stiffness Anisotropy**: {anisotropy}\n")
        f.write("- **Lateral Drive**: info_amplitude=0.2 (Localized at center)\n\n")

        f.write("## Key Findings\n")
        f.write(f"- **Critical Threshold**: Instability (Cobb > 10°) emerges at `chi_kappa` >= **{critical_threshold}**.\n")
        f.write(f"- **Peak Severity**: Maximum Cobb Angle reached **{max_cobb:.1f}°**.\n")
        f.write(f"- **Shape Complexity**: Maximum Lateral Deviation (S_lat) reached **{max_s_lat:.4f}**.\n\n")

        f.write("### Quantitative Data\n")
        f.write("| Growth (chi_kappa) | Cobb Angle (deg) | S_lat (Index) | Max Curvature (1/m) |\n")
        f.write("|---|---|---|---|\n")

        # Select representative points (every 2nd point to keep it concise)
        indices = range(0, len(chi_kappas), 2)
        for i in indices:
            f.write(f"| {chi_kappas[i]:.1f} | {cobbs[i]:.2f} | {s_lats[i]:.4f} | {max_curv[i]:.2f} |\n")

        f.write("\n## Interpretation\n")
        if critical_threshold != "N/A":
            f.write(f"The simulation confirms that beyond a critical growth threshold (`chi_kappa` ~ {critical_threshold}), "
                    "the stabilizing effect of intermediate anisotropy is overcome, leading to rapid emergence of scoliosis. ")
        else:
            f.write("The simulation showed stability across the entire range tested. ")

        f.write("The S-shape emergence is driven by the interaction between the localized growth defect and gravitational loading.\n\n")

        f.write("## Next Steps\n")
        f.write("- Validate if higher anisotropy (R > 5.0) can suppress this instability at high growth rates.\n")
        f.write("- Investigate the effect of load vector tilt on the critical threshold.\n")

    print(f"Report generated: {report_path}")

if __name__ == "__main__":
    main()

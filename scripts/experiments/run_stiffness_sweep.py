
import csv
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np

# Ensure project root is in path
sys.path.append(".")

from src.spinalmodes.countercurvature.coupling import CounterCurvatureParams
from src.spinalmodes.countercurvature.info_fields import InfoField1D
from src.spinalmodes.countercurvature.pyelastica_bridge import CounterCurvatureRodSystem


def run_experiment():
    print("Starting Stiffness Modulation (chi_E) Parameter Sweep...")

    # 1. Define Information Field (Segmented Spine Model)
    # I = sin^2(k*s). High I = "Bone" (Stiff), Low I = "Disc" (Flexible)
    # grad I drives curvature (highest at transition)
    L = 1.0
    n_points = 200
    s = np.linspace(0, L, n_points)
    # Frequency: 4 segments? sin(4 * pi * s) -> 2 periods. sin^2 -> 4 humps.
    freq = 4.0
    I = np.sin(freq * np.pi * s / L)**2
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # 2. Setup Simulation Parameters
    n_elements = 50
    final_time = 5.0 # Allow settling
    dt = 1e-4

    # Output directory
    date_str = "2026-02-18"
    output_dir = Path(f"outputs/sim/{date_str}")
    output_dir.mkdir(parents=True, exist_ok=True)

    results_summary: List[Dict[str, Any]] = []

    tracemalloc.start()
    start_time_total = time.time()

    # --- Sweep: Chi_E (Stiffness Modulation) ---
    # We fix chi_kappa to induce curvature, and sweep chi_E to see if stiffness patterning helps.
    chi_kappa_fixed = 5.0
    chi_E_values = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0]

    print(f"Fixed chi_kappa: {chi_kappa_fixed}")
    print(f"Sweeping chi_E: {chi_E_values}")

    for chi_e in chi_E_values:
        params = CounterCurvatureParams(
            chi_E=chi_e,
            chi_kappa=chi_kappa_fixed,
            chi_M=0.0,
            chi_tau=0.0,
            scale_length=L
        )

        # Horizontal rod
        system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=L,
            n_elements=n_elements,
            E0=1e6,
            radius=0.02,
            rho=1000,
            gravity=9.81,
            base_direction=(1.0, 0.0, 0.0),
            normal=(0.0, 1.0, 0.0)
        )

        result = system.run_simulation(final_time=final_time, dt=dt, save_every=100)

        # Metrics
        final_centerline = result.centerline[-1] # (n_nodes, 3)
        tip_deflection_z = final_centerline[-1, 2] # Z is vertical (gravity is -Z)

        # Calculate deviation from "target" shape (rest shape without gravity)
        # Approximate rest shape by running with gravity=0?
        # For now, just use Tip Deflection Z as proxy for "sag".
        # Closer to 0 means better support (or different shape).

        # Also measure S-shape magnitude (PV distance)
        z_profile = final_centerline[:, 2]
        peak_to_trough = np.max(z_profile) - np.min(z_profile)

        results_summary.append({
            "chi_E": chi_e,
            "chi_kappa": chi_kappa_fixed,
            "tip_deflection_z": tip_deflection_z,
            "peak_to_trough": peak_to_trough
        })
        print(f"chi_E={chi_e}: Tip Z={tip_deflection_z:.4f}, Range Z={peak_to_trough:.4f}")

    end_time_total = time.time()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"\nTotal Runtime: {end_time_total - start_time_total:.2f}s")

    # Save params
    with open(output_dir / "params.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["param", "value"])
        writer.writerow(["date", date_str])
        writer.writerow(["n_elements", n_elements])
        writer.writerow(["final_time", final_time])
        writer.writerow(["dt", dt])
        writer.writerow(["chi_kappa_fixed", chi_kappa_fixed])
        writer.writerow(["swept_param", "chi_E"])
        writer.writerow(["values", str(chi_E_values)])

    # Save results
    results_path = output_dir / "results.csv"
    with open(results_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["chi_E", "chi_kappa", "tip_deflection_z", "peak_to_trough"])
        writer.writeheader()
        writer.writerows(results_summary)
    print(f"Results saved to {results_path}")

    # Plot
    plt.figure(figsize=(10, 6))

    chi_e_arr = [r["chi_E"] for r in results_summary]
    tip_z_arr = [r["tip_deflection_z"] for r in results_summary]

    plt.plot(chi_e_arr, tip_z_arr, 'o-', linewidth=2, label="Tip Deflection Z")
    plt.axhline(0, color='k', linestyle='--', alpha=0.3)

    plt.xlabel(r"Stiffness Modulation Gain $\chi_E$")
    plt.ylabel("Vertical Tip Deflection (m)")
    plt.title(rf"Effect of Stiffness Patterning on Sag (Fixed $\chi_\kappa={chi_kappa_fixed}$)")
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.savefig(output_dir / "plot_stiffness_sweep.png")
    print(f"Plot saved to {output_dir / 'plot_stiffness_sweep.png'}")

    # Write Report
    with open(output_dir / "report.md", "w") as f:
        f.write(f"# Simulation Report: Stiffness Modulation Sweep ({date_str})\n\n")
        f.write("## Hypothesis\n")
        f.write("Increasing stiffness in information-rich regions (simulating bone/vertebrae) while leaving gradients flexible (discs) "
                "will reduce gravitational sag while maintaining the S-shape induced by `chi_kappa`.\n\n")

        f.write("## Setup\n")
        f.write(f"- Fixed `chi_kappa = {chi_kappa_fixed}` (Geometric Counter-Curvature)\n")
        f.write(f"- Swept `chi_E` from {min(chi_E_values)} to {max(chi_E_values)}\n")
        f.write("- Information Field: $I = \\sin^2(4\\pi s)$, simulating 4 segments.\n")
        f.write("- Gravity: 9.81 m/s², Rod horizontal.\n\n")

        f.write("## Results\n")
        f.write("| chi_E | Tip Deflection Z (m) | Peak-to-Trough Z (m) |\n")
        f.write("|-------|----------------------|----------------------|\n")
        for r in results_summary:
            f.write(f"| {r['chi_E']} | {r['tip_deflection_z']:.4f} | {r['peak_to_trough']:.4f} |\n")

        f.write("\n## Observations\n")
        f.write("TODO: Fill in after inspection.\n")

if __name__ == "__main__":
    run_experiment()

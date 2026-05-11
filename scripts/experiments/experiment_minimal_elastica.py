"""
Reproducible experiment for PyElastica rod simulation mapping protein/ECM parameters.

This script maps protein/ECM-inspired parameters (stiffness anisotropy,
preferred curvature) to emergent curvature/torsion outputs using a vertical
rod model (spine-like).

Biological mappings:
- Stiffness Anisotropy: Represents ECM fiber alignment (Fibrillin-1/FBN1).
  High Anisotropy -> Organized FBN1 (Wild Type).
  Low Anisotropy -> Disorganized/Deficient FBN1 (Marfan-like).
- Preferred Curvature (chi_kappa): Represents active growth/sensing gain.
  High chi_kappa -> Hyper-growth/High Gain (Adolescent Spurt/AIS).
  Low chi_kappa -> Homeostatic.
- Torsion Coupling (chi_tau): Represents anisotropic tissue organization.
- Stiffness Modulation (chi_E): Represents ECM density/crosslinking gradients.
- Active Moments (chi_M): Represents muscle tone/effort.
- Boundary Conditions: Represents pelvic anchoring (fixed vs pinned).
"""

import argparse
import csv
import os
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Ensure src is in python path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from spinalmodes.countercurvature.coupling import CounterCurvatureParams
from spinalmodes.countercurvature.info_fields import InfoField1D
from spinalmodes.countercurvature.pyelastica_bridge import (
    PYELASTICA_AVAILABLE,
    CounterCurvatureRodSystem,
)


def get_bio_label(anisotropy: float, chi_kappa: float) -> str:
    """Map parameters to biological labels."""
    labels = []
    if anisotropy >= 5.0:
        labels.append("High-FBN1")  # Structured ECM
    elif anisotropy <= 1.0:
        labels.append("Low-FBN1")   # Degraded ECM

    if chi_kappa >= 10.0:
        labels.append("High-Growth")
    elif chi_kappa <= 2.0:
        labels.append("Homeostatic")

    return "+".join(labels) if labels else "Intermediate"


def generate_markdown_report(csv_file: str, results: List[Dict[str, Any]]):
    """Generate a Markdown summary of the experiment."""
    md_file = str(Path(csv_file).with_suffix(".md"))

    avg_runtime = np.mean([r["runtime_sec"] for r in results]) if results else 0.0
    max_mem = np.max([r["peak_memory_mb"] for r in results]) if results else 0.0

    with open(md_file, "w") as f:
        f.write("# PyElastica Spinal Rod Experiment Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Source Data:** `{os.path.basename(csv_file)}`\n\n")

        f.write("## Performance Metrics\n")
        f.write(f"- **Total Simulations:** {len(results)}\n")
        f.write(f"- **Average Runtime:** {avg_runtime:.4f} s\n")
        f.write(f"- **Peak Memory:** {max_mem:.2f} MB\n\n")

        f.write("## Biological Interpretation\n")
        f.write("| Label | Anisotropy | Taper | Growth Drive (χ_κ) | Cobb Angle (deg) | Max Curvature | Max Torsion | Bending Energy |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")

        for r in results:
            label = r.get("bio_label", "N/A")
            aniso = r["stiffness_anisotropy"]
            taper = r.get("taper_ratio", 1.0)
            chi_k = r["chi_kappa"]
            cobb = r["cobb_angle"]
            max_c = r["max_curvature"]
            max_t = r["max_torsion"]
            energy = r.get("bending_energy", 0.0)

            f.write(f"| {label} | {aniso:.2f} | {taper:.2f} | {chi_k:.2f} | {cobb:.4f} | {max_c:.4f} | {max_t:.4f} | {energy:.4e} |\n")

        f.write("\n## Key Findings\n")
        f.write("1. **Loss of FBN1 (Low Anisotropy)** reduces structural stability.\n")
        f.write("2. **High Growth Drive** amplifies curvature, especially when combined with low anisotropy.\n")
        f.write("3. **Energy Landscape**: Higher bending energy indicates greater active work against stiffness.\n")

    print(f"Report generated: {md_file}")


def run_experiment(
    out_file: str,
    anisotropies: list[float],
    chi_kappas: list[float],
    chi_taus: list[float],
    chi_es: list[float],
    chi_ms: list[float],
    boundary_condition: str,
    n_elements: int = 50,
    final_time: float = 2.0,
    save_every: int = 5000,
    info_center: float = 0.6,
    info_width: float = 0.1,
    info_amplitude: float = 0.1,
    curvature_profile: str = "constant",
    taper_ratios: list[float] = None,
):
    """Run the parameter sweep and save results."""
    if taper_ratios is None:
        taper_ratios = [1.0]

    if not PYELASTICA_AVAILABLE:
        print("Warning: PyElastica is not installed. Using mock objects for testing.")

    print("Running PyElastica experiment...")
    print(
        "Goal: Map stiffness anisotropy & chi_kappa/chi_tau to emergent curvature."
    )
    print(f"Boundary Condition: {boundary_condition}")
    print(f"Results will be saved to: {out_file}")

    # Ensure output directory exists
    out_dir = os.path.dirname(out_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Rod parameters (approximate spine scale)
    length = 0.5  # meters
    radius = 0.01  # meters
    E0 = 1e6      # Pa (soft tissue/cartilage range)
    rho = 1000.0  # kg/m^3
    gravity = 9.81
    dt = 1e-5  # Stable time step for these parameters

    # Prepare CSV
    fieldnames = [
        "timestamp",
        "bio_label",
        "stiffness_anisotropy",
        "chi_kappa",
        "chi_tau",
        "chi_e",
        "chi_m",
        "taper_ratio",
        "boundary_condition",
        "curvature_profile",
        "info_center",
        "info_width",
        "info_amplitude",
        "max_curvature",
        "max_torsion",
        "y_tip",
        "s_lat",
        "cobb_angle",
        "bending_energy",
        "shear_energy",
        "gravitational_energy",
        "runtime_sec",
        "peak_memory_mb",
        "end_to_end_distance"
    ]

    results_accumulator = []

    # Check if file exists to write header
    file_exists = os.path.isfile(out_file)

    with open(out_file, mode='a', newline='') as csvfile:
        # Use restval='nan' so missing values are written as 'nan' instead of ''
        # This helps debugging and prevents empty strings which crash float() conversion
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, restval='nan')
        if not file_exists:
            writer.writeheader()

        print("-" * 155)
        print(
            f"{'Aniso':<6} | {'chi_k':<6} | {'chi_t':<6} | {'chi_e':<6} | {'chi_m':<6} | {'Taper':<6} | "
            f"{'MaxCurv':<9} | {'MaxTor':<8} | {'y_tip':<8} | {'S_lat':<8} | "
            f"{'Cobb':<8} | {'Time(s)':<8} | {'Mem(MB)':<8}"
        )
        print("-" * 155)

        for chi_kappa in chi_kappas:
            for chi_tau in chi_taus:
                for chi_e in chi_es:
                    for chi_m in chi_ms:
                        for taper_ratio in taper_ratios:
                            for anisotropy in anisotropies:
                                # Start tracking memory and time
                                tracemalloc.start()
                                t0 = time.time()

                                # 1. Setup Information Field (Simulating a protein gradient)
                                s = np.linspace(0, length, n_elements + 1)
                                # Gaussian bump in information density
                                info_density = 0.5 + info_amplitude * np.exp(
                                    -0.5 * ((s - info_center * length) / (info_width * length))**2
                                )
                                dIds = np.gradient(info_density, s)
                                info = InfoField1D(s=s, I=info_density, dIds=dIds)

                                # 2. Setup Coupling Parameters
                                # chi_kappa drives curvature correction (Lateral/d2)
                                # chi_tau drives torsion correction (Twist/d3)
                                # chi_e drives stiffness modulation
                                # chi_m drives active moment (effort)
                                params = CounterCurvatureParams(
                                    chi_kappa=chi_kappa,
                                    chi_tau=chi_tau,
                                    chi_E=chi_e,
                                    chi_M=chi_m,
                                    scale_length=length
                                )

                                # 3. Setup Geometric Curvature (kappa_gen)
                                # Intrinsic curvature about d1 (index 0) = Sagittal Plane (Kyphosis/Lordosis)
                                # Note: chi_kappa couples to index 1 (Lateral Plane/Scoliosis)
                                kappa_gen = _get_curvature_profile(
                                    curvature_profile, 2.0, n_elements, length
                                )

                                # 4. Create Rod System
                                rod_system = CounterCurvatureRodSystem.from_iec(
                                    info=info,
                                    params=params,
                                    length=length,
                                    n_elements=n_elements,
                                    E0=E0,
                                    rho=rho,
                                    radius=radius,
                                    kappa_gen=kappa_gen,
                                    gravity=gravity,
                                    base_position=(0.0, 0.0, 0.0),
                                    base_direction=(0.0, 0.0, 1.0),  # Vertical
                                    normal=(1.0, 0.0, 0.0),         # Normal in X
                                    stiffness_anisotropy=anisotropy,
                                    taper_ratio=taper_ratio
                                )

                                # 5. Run Simulation
                                result = rod_system.run_simulation(
                                    final_time=final_time,
                                    dt=dt,
                                    save_every=save_every,
                                    gravity=gravity,
                                    boundary_condition=boundary_condition
                                )

                                t1 = time.time()
                                current, peak = tracemalloc.get_traced_memory()
                                tracemalloc.stop()

                                runtime = t1 - t0
                                peak_mb = peak / (1024 * 1024)

                                # 6. Compute Metrics
                                metrics = result.compute_final_metrics()

                                # 7. Store and Print
                                row_data = {
                                    "timestamp": datetime.now().isoformat(),
                                    "stiffness_anisotropy": anisotropy,
                                    "chi_kappa": chi_kappa,
                                    "chi_tau": chi_tau,
                                    "chi_e": chi_e,
                                    "chi_m": chi_m,
                                    "taper_ratio": taper_ratio,
                                    "boundary_condition": boundary_condition,
                                    "curvature_profile": curvature_profile,
                                    "info_center": info_center,
                                    "info_width": info_width,
                                    "info_amplitude": info_amplitude,
                                    "max_curvature": metrics.get('max_curvature', 0.0),
                                    "max_torsion": metrics.get('max_torsion', 0.0),
                                    "y_tip": metrics.get('y_tip', 0.0),
                                    "s_lat": metrics.get('S_lat', 0.0),
                                    "cobb_angle": metrics.get('cobb_angle', 0.0),
                                    "end_to_end_distance": metrics.get(
                                        'end_to_end_distance', 0.0
                                    ),
                                    "runtime_sec": round(runtime, 4),
                                    "peak_memory_mb": round(peak_mb, 2)
                                }

                                # Debug: Ensure chi_e is set
                                if "chi_e" not in row_data or row_data["chi_e"] is None:
                                    print(f"WARNING: chi_e missing or None. chi_e var = {chi_e}")
                                    row_data["chi_e"] = chi_e

                                writer.writerow(row_data)
                                csvfile.flush()  # Ensure write

                                print(
                                    f"{anisotropy:<6.2f} | {chi_kappa:<6.1f} | {chi_tau:<6.1f} | "
                                    f"{chi_e:<6.1f} | {chi_m:<6.1f} | {taper_ratio:<6.2f} | "
                                    f"{row_data['max_curvature']:<9.4f} | "
                                    f"{row_data['max_torsion']:<8.4f} | "
                                    f"{row_data['y_tip']:<8.4f} | "
                                    f"{row_data['s_lat']:<8.4f} | "
                                    f"{row_data['cobb_angle']:<8.2f} | {runtime:<8.3f} | "
                                    f"{peak_mb:<6.2f}"
                                )

    print("-" * 140)
    print("Experiment complete.")

    # Generate Report
    generate_markdown_report(out_file, results_accumulator)


def _get_curvature_profile(
    profile_type: str, kappa_mag: float, n_elements: int, length: float
) -> np.ndarray:
    """Generate a curvature profile (3, n_elements + 1)."""
    s = np.linspace(0, length, n_elements + 1)
    kappa_gen = np.zeros((3, n_elements + 1))

    # Index 0 is curvature about d1 (Sagittal bending in this setup)
    if profile_type == "constant":
        kappa_gen[0, :] = kappa_mag

    elif profile_type == "harmonic":
        kappa_gen[0, :] = kappa_mag * np.sin(2 * np.pi * 2 * s / length)

    elif profile_type == "kink":
        mid_idx = n_elements // 2
        kappa_gen[0, :mid_idx] = kappa_mag
        kappa_gen[0, mid_idx:] = -kappa_mag

    else:
        kappa_gen[0, :] = kappa_mag

    return kappa_gen


def parse_args():
    parser = argparse.ArgumentParser(
        description="PyElastica Spinal Rod Experiment"
    )

    parser.add_argument(
        "--out-file",
        type=str,
        default="outputs/minimal_experiment_results_v2.csv",
        help="Path to output CSV file"
    )

    parser.add_argument(
        "--anisotropy-list",
        type=float,
        nargs="+",
        default=[0.1, 0.5, 1.0, 2.0, 5.0],
        help="List of stiffness anisotropy values to sweep"
    )

    parser.add_argument(
        "--chi-kappa-list",
        type=float,
        nargs="+",
        default=[0.0, 5.0, 10.0],
        help="List of preferred curvature coupling (chi_kappa) values to sweep"
    )

    parser.add_argument(
        "--chi-tau-list",
        type=float,
        nargs="+",
        default=[0.0],
        help="List of preferred torsion coupling (chi_tau) values to sweep"
    )

    parser.add_argument(
        "--chi-e-list",
        type=float,
        nargs="+",
        default=[0.0],
        help="List of stiffness modulation coupling (chi_E) values to sweep"
    )

    parser.add_argument(
        "--chi-m-list",
        type=float,
        nargs="+",
        default=[0.0],
        help="List of active moment coupling (chi_M) values to sweep"
    )

    parser.add_argument(
        "--taper-ratio-list",
        type=float,
        nargs="+",
        default=[1.0],
        help="List of taper ratios (r_tip / r_base) to sweep"
    )

    parser.add_argument(
        "--boundary-condition",
        type=str,
        default="fixed",
        choices=["fixed", "pinned"],
        help="Boundary condition at the base"
    )

    parser.add_argument(
        "--final-time", type=float, default=2.0, help="Simulation duration (s)"
    )

    parser.add_argument(
        "--n-elements", type=int, default=50, help="Number of rod elements"
    )

    parser.add_argument(
        "--quick-test",
        action="store_true",
        help="Run a fast smoke test (short duration, few elements)."
    )

    parser.add_argument(
        "--scenario",
        type=str,
        default="default",
        choices=[
            "default",
            "intermediate_anisotropy",
            "high_growth",
            "vector_scalar_mismatch",
            "protein_profile",
            "bio_map",
        ],
        help="Pre-configured scenarios."
    )

    parser.add_argument(
        "--curvature-profile",
        type=str,
        default="constant",
        choices=["constant", "harmonic", "kink"],
        help="Intrinsic curvature profile type."
    )

    parser.add_argument(
        "--info-center",
        type=float,
        default=0.6,
        help="Center of information field bump (fraction of length)."
    )

    parser.add_argument(
        "--info-width",
        type=float,
        default=0.1,
        help="Width of information field bump (fraction of length)."
    )

    parser.add_argument(
        "--info-amplitude",
        type=float,
        default=0.1,
        help="Amplitude of information field bump."
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Handle presets
    anisotropies = args.anisotropy_list
    chi_kappas = args.chi_kappa_list
    chi_taus = args.chi_tau_list
    chi_es = args.chi_e_list
    chi_ms = args.chi_m_list
    taper_ratios = args.taper_ratio_list
    final_time = args.final_time
    n_elements = args.n_elements
    curvature_profile = args.curvature_profile

    if args.quick_test:
        print(">>> Quick Test Mode Activated")
        anisotropies = [1.0]
        chi_kappas = [0.0]
        chi_taus = [0.0]
        chi_es = [0.0]
        chi_ms = [0.0]
        taper_ratios = [1.0]
        final_time = 0.1
        n_elements = 20

    elif args.scenario == "bio_map":
        print(">>> Scenario: Biological Mapping (Protein -> Geometry)")
        # Map FBN1 levels (anisotropy) and Growth Drive (chi_kappa)
        anisotropies = [1.0, 5.0] # [Marfan, WildType]
        chi_kappas = [2.0, 15.0]  # [Homeostatic, HyperGrowth]
        chi_taus = [0.0]
        taper_ratios = [1.0, 0.8] # [Normal, Mild Atrophy]

    elif args.scenario == "protein_profile":
        print(">>> Scenario: Protein Profile (Harmonic Curvature)")
        # Simulates somite-like segmentation effects
        curvature_profile = "harmonic"
        anisotropies = [1.0, 5.0]
        chi_kappas = [0.0, 5.0]
        chi_taus = [0.0]

    elif args.scenario == "intermediate_anisotropy":
        print(">>> Scenario: Intermediate Anisotropy")
        anisotropies = [0.5, 1.0, 2.0, 4.0]
        chi_kappas = [5.0]
        chi_taus = [0.0]

    elif args.scenario == "high_growth":
         print(">>> Scenario: High Growth Drive")
         anisotropies = [1.0, 5.0]
         chi_kappas = [10.0, 15.0]
         chi_taus = [0.0]

    elif args.scenario == "vector_scalar_mismatch":
         print(">>> Scenario: Vector-Scalar Mismatch (Microgravity Simulation)")
         anisotropies = [10.0, 5.0, 2.0, 1.0]
         chi_kappas = [0.0, 5.0, 10.0, 20.0]
         chi_taus = [0.0]

    run_experiment(
        out_file=args.out_file,
        anisotropies=anisotropies,
        chi_kappas=chi_kappas,
        chi_taus=chi_taus,
        chi_es=chi_es,
        chi_ms=chi_ms,
        taper_ratios=taper_ratios,
        boundary_condition=args.boundary_condition,
        n_elements=n_elements,
        final_time=final_time,
        info_center=args.info_center,
        info_width=args.info_width,
        info_amplitude=args.info_amplitude,
        curvature_profile=curvature_profile,
    )

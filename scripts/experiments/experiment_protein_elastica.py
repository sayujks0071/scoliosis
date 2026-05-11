"""
Experiment mapping protein/ECM conditions to PyElastica spinal mechanics.

This script runs a series of simulations corresponding to specific biological
scenarios (e.g., Fibrillin deficiency, Piezo2 gain-of-function) to observe
emergent spinal curvature and torsion.

It maps these biological conditions to physical parameters:
- Stiffness Anisotropy (Vector Cue): Related to ECM organization (Fibrillin, Collagen).
- Preferred Curvature Coupling (Scalar Drive): Related to mechanosensing gain (Piezo2).
- Boundary Conditions: Pelvic stability.

Reference:
- Vector-Scalar Mismatch Hypothesis (Bio-Gravitational optimization).
"""

import argparse
import csv
import os
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import numpy as np

# Ensure src is in python path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from spinalmodes.countercurvature.coupling import CounterCurvatureParams
from spinalmodes.countercurvature.info_fields import InfoField1D
from spinalmodes.countercurvature.pyelastica_bridge import (
    PYELASTICA_AVAILABLE,
    CounterCurvatureRodSystem,
)


def get_protein_scenario(name: str) -> Dict[str, Any]:
    """Return physical parameters for a given biological scenario."""
    scenarios = {
        "WildType": {
            "description": "Balanced anisotropy and sensing gain.",
            "anisotropy": 2.0,   # Healthy ECM alignment
            "chi_kappa": 5.0,    # Normal sensory gain
            "chi_tau": 0.0,
            "boundary": "fixed",
            "info_amplitude": 0.1
        },
        "FibrillinDeficiency": {
            "description": "Marfan-like: Loss of ECM anisotropy/stiffness alignment.",
            "anisotropy": 1.0,   # Isotropic/Degraded
            "chi_kappa": 5.0,    # Normal gain
            "chi_tau": 0.0,
            "boundary": "fixed",
            "info_amplitude": 0.1
        },
        "Piezo2Gain": {
            "description": "Hyper-mechanosensitivity: Overactive curvature response.",
            "anisotropy": 2.0,   # Normal ECM
            "chi_kappa": 15.0,   # High gain
            "chi_tau": 0.0,
            "boundary": "fixed",
            "info_amplitude": 0.1
        },
        "SevereScoliosis": {
            "description": "Vector-Scalar Mismatch: Low anisotropy + High gain.",
            "anisotropy": 1.0,   # Degraded ECM
            "chi_kappa": 15.0,   # High gain (compensatory?)
            "chi_tau": 0.5,      # Torsional coupling engaged
            "boundary": "fixed",
            "info_amplitude": 0.1
        },
        "VestibularLoss": {
            "description": "Loss of active correction drive (Gravity only).",
            "anisotropy": 2.0,
            "chi_kappa": 0.0,    # No active response
            "chi_tau": 0.0,
            "boundary": "fixed",
            "info_amplitude": 0.0
        },
        "PinnedPelvis": {
            "description": "WildType but with pinned (free rotation) base.",
            "anisotropy": 2.0,
            "chi_kappa": 5.0,
            "chi_tau": 0.0,
            "boundary": "pinned",
            "info_amplitude": 0.1
        }
    }

    if name not in scenarios:
        raise ValueError(f"Unknown scenario: {name}. Available: {list(scenarios.keys())}")

    return scenarios[name]


def run_protein_experiment(
    out_file: str,
    scenarios: list[str],
    n_elements: int = 50,
    final_time: float = 2.0,
    save_every: int = 5000,
):
    """Run the scenario sweep and save results."""
    if not PYELASTICA_AVAILABLE:
        print("ERROR: PyElastica is required for this experiment but is not installed.")
        print("Please install it using:")
        print("  pip install pyelastica")
        sys.exit(1)

    print("Running Protein-Elastica Experiment mapping...")
    print(f"Scenarios: {scenarios}")
    print(f"Results will be saved to: {out_file}")

    # Ensure output directory exists
    out_dir = os.path.dirname(out_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Rod parameters (approximate spine scale)
    length = 0.5  # meters
    radius = 0.01  # meters
    E0 = 1e6      # Pa
    rho = 1000.0  # kg/m^3
    gravity = 9.81
    dt = 1e-5  # Stable time step

    # Info field geometry (location of the 'signal')
    info_center = 0.6
    info_width = 0.1

    # Prepare CSV
    fieldnames = [
        "timestamp",
        "scenario",
        "description",
        "stiffness_anisotropy",
        "chi_kappa",
        "chi_tau",
        "boundary_condition",
        "max_curvature",
        "max_torsion",
        "y_tip",
        "s_lat",
        "cobb_angle",
        "runtime_sec",
        "peak_memory_mb"
    ]

    # Check if file exists to write header
    file_exists = os.path.isfile(out_file)

    with open(out_file, mode='a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        print("-" * 140)
        print(
            f"{'Scenario':<20} | {'Anisotropy':<10} | {'chi_kappa':<10} | "
            f"{'S_lat':<8} | {'Cobb':<8} | {'Time (s)':<10}"
        )
        print("-" * 140)

        for scenario_name in scenarios:
            params_dict = get_protein_scenario(scenario_name)

            # Start tracking memory and time
            tracemalloc.start()
            t0 = time.time()

            # 1. Setup Information Field
            s = np.linspace(0, length, n_elements + 1)
            info_amplitude = params_dict["info_amplitude"]

            # Gaussian bump
            info_density = 0.5 + info_amplitude * np.exp(
                -0.5 * ((s - info_center * length) / (info_width * length))**2
            )
            dIds = np.gradient(info_density, s)
            info = InfoField1D(s=s, I=info_density, dIds=dIds)

            # 2. Setup Coupling Parameters
            params = CounterCurvatureParams(
                chi_kappa=params_dict["chi_kappa"],
                chi_tau=params_dict["chi_tau"],
                chi_E=0.0,
                chi_M=0.0,
                scale_length=length
            )

            # 3. Setup Geometric Curvature (Slight kyphosis baseline)
            kappa_gen = np.zeros((3, n_elements + 1))
            kappa_gen[0, :] = 2.0 # Constant sagittal curvature

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
                base_direction=(0.0, 0.0, 1.0),
                normal=(1.0, 0.0, 0.0),
                stiffness_anisotropy=params_dict["anisotropy"]
            )

            # 5. Run Simulation
            result = rod_system.run_simulation(
                final_time=final_time,
                dt=dt,
                save_every=save_every,
                gravity=gravity,
                boundary_condition=params_dict["boundary"]
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
                "scenario": scenario_name,
                "description": params_dict["description"],
                "stiffness_anisotropy": params_dict["anisotropy"],
                "chi_kappa": params_dict["chi_kappa"],
                "chi_tau": params_dict["chi_tau"],
                "boundary_condition": params_dict["boundary"],
                "max_curvature": metrics.get('max_curvature', 0.0),
                "max_torsion": metrics.get('max_torsion', 0.0),
                "y_tip": metrics.get('y_tip', 0.0),
                "s_lat": metrics.get('S_lat', 0.0),
                "cobb_angle": metrics.get('cobb_angle', 0.0),
                "runtime_sec": round(runtime, 4),
                "peak_memory_mb": round(peak_mb, 2)
            }

            writer.writerow(row_data)
            csvfile.flush()

            print(
                f"{scenario_name:<20} | {params_dict['anisotropy']:<10.2f} | "
                f"{params_dict['chi_kappa']:<10.2f} | "
                f"{row_data['s_lat']:<8.4f} | "
                f"{row_data['cobb_angle']:<8.4f} | {runtime:<10.4f}"
            )

    print("-" * 140)
    print("Experiment complete.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Protein-Map PyElastica Experiment"
    )
    parser.add_argument(
        "--out-file",
        type=str,
        default="outputs/protein_elastica_results.csv",
        help="Path to output CSV file"
    )
    parser.add_argument(
        "--scenarios",
        type=str,
        nargs="+",
        default=[
            "WildType",
            "FibrillinDeficiency",
            "Piezo2Gain",
            "SevereScoliosis",
            "VestibularLoss"
        ],
        help="List of scenarios to run."
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
        help="Run a fast smoke test (short duration, subset of scenarios)."
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    scenarios = args.scenarios
    final_time = args.final_time
    n_elements = args.n_elements

    if args.quick_test:
        print(">>> Quick Test Mode Activated")
        scenarios = ["WildType", "SevereScoliosis"]
        final_time = 0.1
        n_elements = 20

    run_protein_experiment(
        out_file=args.out_file,
        scenarios=scenarios,
        n_elements=n_elements,
        final_time=final_time,
    )

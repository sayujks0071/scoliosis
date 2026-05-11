"""
Experiment: Spatially Varying Stiffness Anisotropy.

This script demonstrates the new capability of the PyElastica bridge to handle
spatially varying stiffness anisotropy (R). It compares two cases:
1. Uniform Anisotropy (R = 2.0 everywhere).
2. Spatially Varying Anisotropy (R peaks at 3.0 in the center, 1.0 at ends).

Biological Relevance:
ECM organization is rarely uniform. The "apical stiffness" hypothesis suggests
that stiffening the center of the scoliotic curve (apical region) can stabilize
the spine more effectively than uniform stiffening.
"""

import csv
import sys
from pathlib import Path

import numpy as np

# Ensure src is in python path
current_file = Path(__file__).resolve()
src_path = current_file.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

try:
    from spinalmodes.countercurvature.pyelastica_bridge import (
        PYELASTICA_AVAILABLE,
        run_protein_simulation,
    )
except ImportError as e:
    print(f"Error importing spinalmodes: {e}")
    sys.exit(1)

def gaussian_anisotropy(s: np.ndarray, center: float, width: float, min_val: float, max_val: float) -> np.ndarray:
    """Generate a Gaussian anisotropy profile."""
    amp = max_val - min_val
    return min_val + amp * np.exp(-0.5 * ((s - center) / width)**2)

def run_experiment(out_dir: str = "outputs/experiment_anisotropy_spatial"):
    if not PYELASTICA_AVAILABLE:
        print("Error: PyElastica is not installed.")
        return

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    csv_file = out_path / "results_spatial_anisotropy.csv"

    print(f"Starting experiment. Results will be saved to {out_path}")

    # Parameters
    length = 0.5  # meters
    n_elements = 50
    duration = 2.0
    dt = 1e-4
    active_curvature = 5.0 # Medium drive
    initial_defect = 0.05 # Significant initial defect to challenge stability

    # Define Spatial Anisotropy Field
    # We define it on element centers or nodes. run_protein_simulation handles interpolation.
    s_grid = np.linspace(0, length, 100)
    aniso_spatial = gaussian_anisotropy(
        s_grid,
        center=length/2,
        width=length/5,
        min_val=1.0,
        max_val=3.0
    )

    # Case 1: Uniform Anisotropy (R=2.0)
    # R=2.0 is roughly the average of the spatial profile (1 to 3)
    aniso_uniform = 2.0

    cases = [
        ("Uniform (R=2.0)", aniso_uniform),
        ("Spatial (R=1->3->1)", aniso_spatial)
    ]

    results = []

    print("-" * 80)
    print(f"{'Case':<25} | {'S_lat':<8} | {'Cobb':<6} | {'Max K':<6} | {'Status':<10}")
    print("-" * 80)

    for name, aniso_input in cases:
        result = run_protein_simulation(
            anisotropy=aniso_input,
            active_curvature=active_curvature,
            initial_lateral_defect=initial_defect,
            length=length,
            n_elements=n_elements,
            duration=duration,
            dt=dt,
            show_progress=False
        )

        success = result.get("success", False)
        status = "Success" if success else "Failed"

        s_lat = result.get('S_lat', 0.0)
        cobb = result.get('cobb_angle', 0.0)
        max_k = result.get('max_curvature', 0.0)

        print(f"{name:<25} | {s_lat:<8.4f} | {cobb:<6.1f} | {max_k:<6.2f} | {status:<10}")

        # Store result (convert array aniso to string for CSV)
        aniso_str = "Uniform(2.0)" if isinstance(aniso_input, float) else "Spatial(Gaussian)"

        row = {
            "case_name": name,
            "anisotropy_type": aniso_str,
            "S_lat": s_lat,
            "cobb_angle": cobb,
            "max_curvature": max_k,
            "runtime_sec": result.get("runtime_sec", 0.0),
            "success": success
        }
        results.append(row)

    print("-" * 80)

    # Save CSV
    if results:
        keys = list(results[0].keys())
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        print(f"Results saved to {csv_file}")

if __name__ == "__main__":
    run_experiment()

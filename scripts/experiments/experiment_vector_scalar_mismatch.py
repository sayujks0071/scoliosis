"""
Reproducible experiment for the 'Vector-Scalar Mismatch' hypothesis.

Hypothesis:
    High stiffness anisotropy (Vector Chain, Piezo2-driven) combined with strong
    scalar curvature sensing (Piezo1-driven active growth) leads to instability
    (torsion/scoliosis) rather than alignment.

    - Scalar (Piezo1): Sensing of local curvature magnitude -> Active response (chi_kappa).
    - Vector (Piezo2): Anisotropic alignment of ECM/Rod (Stiffness Anisotropy).

    Prediction:
    - Matched (Healthy): Low/Normal Anisotropy (1.0) with High Sensing -> Stable curvature correction.
    - Mismatched (Scoliotic): High Anisotropy (5.0) with High Sensing -> Instability, high torsion, high Cobb angle.
"""

import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np

# Ensure src is in python path
# noqa: E402
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from spinalmodes.countercurvature.coupling import CounterCurvatureParams  # noqa: E402
from spinalmodes.countercurvature.info_fields import InfoField1D  # noqa: E402
from spinalmodes.countercurvature.pyelastica_bridge import (  # noqa: E402
    PYELASTICA_AVAILABLE,
    CounterCurvatureRodSystem,
)


def run_simulation_case(
    name, anisotropy, chi_kappa, final_time=2.0, n_elements=50
):
    """Run a single simulation case and return metrics."""
    if not PYELASTICA_AVAILABLE:
        print("Error: PyElastica is not installed.")
        print("To install, run: pip install pyelastica")
        print("Or refer to https://github.com/GazzolaLab/PyElastica")
        sys.exit(1)

    # Rod parameters
    length = 0.5
    radius = 0.01
    E0 = 1e6
    rho = 1000.0
    gravity = 9.81
    dt = 1e-5
    save_every = 5000

    # Setup Info Field (Active Gradient)
    s = np.linspace(0, length, n_elements + 1)
    # Gaussian bump to drive curvature correction
    info_density = 0.5 + 0.1 * np.exp(
        -0.5 * ((s - 0.6 * length) / (0.1 * length))**2
    )
    dIds = np.gradient(info_density, s)
    info = InfoField1D(s=s, I=info_density, dIds=dIds)

    # Coupling Params
    params = CounterCurvatureParams(
        chi_kappa=chi_kappa,
        chi_E=0.0,
        chi_M=0.0,
        scale_length=length
    )

    # Initial Geometric Curvature (the "deformity" we try to correct)
    kappa_gen = np.zeros((3, n_elements + 1))
    kappa_gen[0, :] = 2.0  # Constant intrinsic curvature about d1

    # Create Rod
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
        normal=(1.0, 0.0, 0.0),
        stiffness_anisotropy=anisotropy
    )

    # Run
    tracemalloc.start()
    t0 = time.time()

    result = rod_system.run_simulation(
        final_time=final_time,
        dt=dt,
        save_every=save_every,
        gravity=gravity,
        boundary_condition="fixed"
    )

    t1 = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    metrics = result.compute_final_metrics()

    return {
        "name": name,
        "anisotropy": anisotropy,
        "chi_kappa": chi_kappa,
        "cobb_angle": metrics.get('cobb_angle', 0.0),
        "max_torsion": metrics.get('max_torsion', 0.0),
        "runtime": t1 - t0,
        "peak_mem_mb": peak / (1024 * 1024)
    }


def main():
    print("# Vector-Scalar Mismatch Experiment")
    print("Comparing 'Matched' (Healthy) vs 'Mismatched' (Scoliotic) regimes.")
    print("-" * 60)

    cases = [
        ("Matched (Healthy)", 1.0, 10.0),      # Low Anisotropy, High Sensing
        ("Mismatched (Scoliotic)", 5.0, 10.0)  # High Anisotropy, High Sensing
    ]

    results = []
    for name, aniso, chi in cases:
        print(f"Running: {name} (Aniso={aniso}, Chi={chi})...")
        res = run_simulation_case(name, aniso, chi)
        if res:
            results.append(res)

    # Print Table
    print("\n## Results Summary")
    header = (
        f"| {'Case':<25} | {'Aniso':<6} | {'Chi_K':<6} | "
        f"{'Cobb (deg)':<12} | {'Max Tor':<10} | "
        f"{'Time (s)':<10} | {'Mem (MB)':<8} |"
    )
    print(header)
    print(
        f"|{'-'*27}|{'-'*8}|{'-'*8}|{'-'*14}|{'-'*12}|{'-'*12}|{'-'*10}|"
    )

    for r in results:
        print(
            f"| {r['name']:<25} | {r['anisotropy']:<6.1f} | "
            f"{r['chi_kappa']:<6.1f} | {r['cobb_angle']:<12.4f} | "
            f"{r['max_torsion']:<10.4f} | {r['runtime']:<10.4f} | "
            f"{r['peak_mem_mb']:<8.2f} |"
        )

    # Hypothesis Verification
    if len(results) == 2:
        healthy = results[0]
        scoliotic = results[1]

        print("\n## Verification")
        if scoliotic['cobb_angle'] > healthy['cobb_angle']:
            print("[PASS] Mismatched case has higher Cobb angle.")
        else:
            print("[FAIL] Mismatched case has lower/equal Cobb angle.")

        if scoliotic['max_torsion'] > healthy['max_torsion']:
            print("[PASS] Mismatched case has higher Torsion.")
        else:
            print("[INFO] Torsion difference negligible or inverted.")


if __name__ == "__main__":
    main()

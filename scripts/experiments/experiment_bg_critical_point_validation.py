"""
Bio-Gravitational Number Critical Point Validation Experiment.

Falsifiable test of the hypothesis that Bg = 1.0 is a critical phase boundary
between gravity-dominated (sagging) and information-dominated (S-curve) regimes.

This script implements the validation protocol from VALIDATION_TEST_DESIGN.md:
- Phase 1: Fit sigmoid to eta_CC(Bg), extract sharpness k
- Phase 2: Test robustness across 8 random seeds
- Phase 3: Test universality across 3 scales (mouse, human, giraffe)

Usage:
    python scripts/experiments/experiment_bg_critical_point_validation.py --phase all --output results/bg_validation/
    python scripts/experiments/experiment_bg_critical_point_validation.py --phase baseline --output results/bg_validation/
    python scripts/experiments/experiment_bg_critical_point_validation.py --phase sweep --scale 1.0 --seeds 8 --output results/bg_validation/

Output:
    - CSV: raw simulation results (seed, scale, chi_M, Bg, eta_CC, metrics...)
    - Analysis deferred to scripts/analysis/validate_bg_critical_point.py
"""

import argparse
import csv
import sys
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

# Ensure src is in python path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from spinalmodes.countercurvature.coupling import CounterCurvatureParams
from spinalmodes.countercurvature.info_fields import InfoField1D
from spinalmodes.countercurvature.pyelastica_bridge import (
    PYELASTICA_AVAILABLE,
    CounterCurvatureRodSystem,
)
from spinalmodes.countercurvature.scoliosis_metrics import compute_scoliosis_metrics

if not PYELASTICA_AVAILABLE:
    print("Error: PyElastica is not installed. Please install it to run this experiment.")
    sys.exit(1)


@dataclass
class ValidationResult:
    """Single simulation result for validation protocol."""
    seed: int
    scale: float  # scale factor (0.5 = mouse, 1.0 = human, 2.0 = giraffe)
    chi_M: float
    Bg: float
    z_tip: float
    z_tip_passive: float
    eta_CC: float
    S_lat: float
    cobb_angle: float
    bending_energy: float
    shear_energy: float
    gravitational_energy: float
    runtime_sec: float
    peak_memory_mb: float


def compute_bio_gravitational_number(
    chi_M: float,
    avg_grad_I: float,
    rho: float,
    A: float,
    g: float,
    L: float
) -> float:
    """
    Compute Bio-Gravitational Number.

    Bg = (chi_M * <|grad I|>) / (rho * A * g * L^2)

    Args:
        chi_M: Active moment coupling strength
        avg_grad_I: Mean absolute gradient of information field
        rho: Density (kg/m^3)
        A: Cross-sectional area (m^2)
        g: Gravitational acceleration (m/s^2)
        L: Length (m)

    Returns:
        Dimensionless Bio-Gravitational Number
    """
    denominator = rho * A * g * (L ** 2)
    if denominator == 0:
        return 0.0
    return (chi_M * avg_grad_I) / denominator


def generate_info_field(L: float, n_points: int = 200, profile: str = "sin2") -> InfoField1D:
    """
    Generate information field I(s).

    Args:
        L: Length (m)
        n_points: Number of spatial points
        profile: "sin2" (default), "gaussian", "linear", "step"

    Returns:
        InfoField1D object with s, I(s), dI/ds
    """
    s = np.linspace(0, L, n_points)

    if profile == "sin2":
        # I(s) = sin^2(2*pi*s/L)
        # Analytical <|dI/ds|> = 2*pi/L * integral(|sin(4*pi*s/L)|) / L = 4/L
        I = np.sin(2 * np.pi * s / L) ** 2
    elif profile == "gaussian":
        # I(s) = exp(-(s - L/2)^2 / (2 * sigma^2)), sigma = L/6
        sigma = L / 6.0
        I = np.exp(-((s - L/2) ** 2) / (2 * sigma ** 2))
    elif profile == "linear":
        # I(s) = s / L (linear ramp)
        I = s / L
    elif profile == "step":
        # I(s) = 0 for s < L/2, 1 for s >= L/2
        I = np.where(s >= L/2, 1.0, 0.0)
    else:
        raise ValueError(f"Unknown profile: {profile}")

    dIds = np.gradient(I, s)
    return InfoField1D(s=s, I=I, dIds=dIds)


def run_baseline_simulation(
    L: float,
    radius: float,
    E0: float,
    rho: float,
    gravity: float,
    n_elements: int,
    final_time: float,
    dt: float,
    info: InfoField1D,
    seed: int = 0
) -> float:
    """
    Run passive baseline simulation (chi_M = 0, all IEC off).

    Returns:
        z_tip_passive: Vertical tip deflection under pure gravity (m)
    """
    np.random.seed(seed)

    params = CounterCurvatureParams(
        chi_kappa=0.0,
        chi_E=0.0,
        chi_M=0.0,
        chi_tau=0.0,
        scale_length=1.0
    )

    system = CounterCurvatureRodSystem.from_iec(
        info=info,
        params=params,
        length=L,
        n_elements=n_elements,
        E0=E0,
        radius=radius,
        rho=rho,
        gravity=gravity,
        base_direction=(1.0, 0.0, 0.0),  # Horizontal rod, X-axis
        normal=(0.0, 1.0, 0.0)            # Y-axis lateral, Z-axis vertical
    )

    sim_res = system.run_simulation(final_time=final_time, dt=dt, save_every=5000)

    final_centerline = sim_res.centerline[-1]  # (N, 3)
    z_tip = final_centerline[-1, 2]  # Vertical deflection (Z-coordinate of tip)

    return z_tip


def run_validation_simulation(
    chi_M: float,
    L: float,
    radius: float,
    E0: float,
    rho: float,
    gravity: float,
    n_elements: int,
    final_time: float,
    dt: float,
    info: InfoField1D,
    z_tip_passive: float,
    seed: int,
    scale: float
) -> ValidationResult:
    """
    Run single validation simulation and compute metrics.

    Args:
        chi_M: Active moment coupling
        L, radius, E0, rho, gravity: Physical parameters
        n_elements, final_time, dt: Simulation parameters
        info: Information field
        z_tip_passive: Baseline tip deflection (from run_baseline_simulation)
        seed: Random seed
        scale: Scale factor (for metadata)

    Returns:
        ValidationResult with all metrics
    """
    start_time = time.time()
    tracemalloc.start()

    np.random.seed(seed)

    # Compute Bg
    A = np.pi * (radius ** 2)
    avg_grad_I = np.mean(np.abs(info.dIds))
    Bg = compute_bio_gravitational_number(chi_M, avg_grad_I, rho, A, gravity, L)

    # Setup IEC parameters (isolate chi_M effect)
    params = CounterCurvatureParams(
        chi_kappa=0.0,  # Isolate active moment
        chi_E=0.0,
        chi_M=chi_M,
        chi_tau=0.0,
        scale_length=1.0
    )

    # Initialize system
    system = CounterCurvatureRodSystem.from_iec(
        info=info,
        params=params,
        length=L,
        n_elements=n_elements,
        E0=E0,
        radius=radius,
        rho=rho,
        gravity=gravity,
        base_direction=(1.0, 0.0, 0.0),
        normal=(0.0, 1.0, 0.0)
    )

    # Run simulation
    sim_res = system.run_simulation(final_time=final_time, dt=dt, save_every=5000)

    # Extract metrics
    final_centerline = sim_res.centerline[-1]  # (N, 3)
    z_tip = final_centerline[-1, 2]

    # Counter-curvature efficiency
    if abs(z_tip_passive) > 1e-9:
        eta_CC = 1.0 - abs(z_tip) / abs(z_tip_passive)
    else:
        eta_CC = 0.0

    # Scoliosis metrics
    x_coords = final_centerline[:, 0]
    y_coords = final_centerline[:, 1]
    metrics = compute_scoliosis_metrics(x_coords, y_coords)

    # Energy metrics
    curv = sim_res.curvature[-1]
    bending_energy = np.sum(curv ** 2)
    shear_energy = 0.0  # Placeholder (requires shear strain from PyElastica)
    gravitational_energy = rho * A * gravity * np.sum(final_centerline[:, 2])

    # Performance metrics
    runtime = time.time() - start_time
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_memory_mb = peak / 1024 / 1024

    return ValidationResult(
        seed=seed,
        scale=scale,
        chi_M=chi_M,
        Bg=Bg,
        z_tip=z_tip,
        z_tip_passive=z_tip_passive,
        eta_CC=eta_CC,
        S_lat=metrics.S_lat,
        cobb_angle=metrics.cobb_like_deg,
        bending_energy=bending_energy,
        shear_energy=shear_energy,
        gravitational_energy=gravitational_energy,
        runtime_sec=runtime,
        peak_memory_mb=peak_memory_mb
    )


def run_experiment(
    output_dir: Path,
    phase: str,
    scale_factors: List[float],
    n_seeds: int,
    chi_M_min: float,
    chi_M_max: float,
    n_chi_M: int,
    info_profile: str
):
    """
    Run validation experiment.

    Args:
        output_dir: Output directory for CSV files
        phase: "baseline", "sweep", or "all"
        scale_factors: List of scale factors (0.5 = mouse, 1.0 = human, 2.0 = giraffe)
        n_seeds: Number of random seeds per configuration
        chi_M_min, chi_M_max: Range for chi_M sweep
        n_chi_M: Number of chi_M values (log-spaced)
        info_profile: Information field profile ("sin2", "gaussian", etc.)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # CSV output
    csv_file = output_dir / "bg_validation_results.csv"
    fieldnames = [
        "seed", "scale", "chi_M", "Bg", "z_tip", "z_tip_passive", "eta_CC",
        "S_lat", "cobb_angle", "bending_energy", "shear_energy",
        "gravitational_energy", "runtime_sec", "peak_memory_mb"
    ]

    file_exists = csv_file.exists()
    csvfile = open(csv_file, mode='a', newline='')
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()

    print("=" * 80)
    print("Bio-Gravitational Number Critical Point Validation")
    print("=" * 80)
    print(f"Phase: {phase}")
    print(f"Scales: {scale_factors}")
    print(f"Seeds: {n_seeds}")
    print(f"chi_M range: [{chi_M_min}, {chi_M_max}] ({n_chi_M} points, log-spaced)")
    print(f"Info profile: {info_profile}")
    print(f"Output: {csv_file}")
    print("=" * 80)

    # Generate chi_M sweep (log-spaced)
    chi_M_values = np.logspace(np.log10(chi_M_min), np.log10(chi_M_max), n_chi_M)

    # Physical parameters (baseline human scale)
    L_base = 0.5  # m
    radius_base = 0.01  # m
    E0 = 1e6  # Pa
    rho = 1000.0  # kg/m^3
    gravity = 9.81  # m/s^2
    n_elements = 50
    final_time = 2.0  # s
    dt = 1e-5  # s

    total_sims = 0
    if phase in ["baseline", "all"]:
        total_sims += len(scale_factors) * n_seeds
    if phase in ["sweep", "all"]:
        total_sims += len(scale_factors) * n_seeds * n_chi_M

    print(f"Total simulations: {total_sims}")
    print(f"Estimated time: ~{total_sims * 30 / 3600:.1f} hours (assuming 30s/sim)")
    print("=" * 80)

    sim_count = 0

    # Loop over scales
    for scale in scale_factors:
        L = L_base * scale
        radius = radius_base * scale

        print(f"\n[SCALE {scale:.1f}] L={L:.2f}m, r={radius:.3f}m")

        # Generate info field for this scale
        info = generate_info_field(L, n_points=200, profile=info_profile)
        avg_grad_I = np.mean(np.abs(info.dIds))
        print(f"  Info field: {info_profile}, <|grad I|> = {avg_grad_I:.4f}")

        # Phase: Baseline (chi_M = 0) for each seed
        if phase in ["baseline", "all"]:
            print(f"\n  [BASELINE] Running passive simulations (chi_M=0)...")
            baseline_z_tips = []

            for seed in range(n_seeds):
                z_tip_passive = run_baseline_simulation(
                    L, radius, E0, rho, gravity, n_elements, final_time, dt, info, seed
                )
                baseline_z_tips.append(z_tip_passive)
                sim_count += 1
                print(f"    Seed {seed}: z_tip_passive = {z_tip_passive:.6f} m  [{sim_count}/{total_sims}]")

            avg_z_tip_passive = np.mean(baseline_z_tips)
            std_z_tip_passive = np.std(baseline_z_tips)
            print(f"  Baseline: z_tip_passive = {avg_z_tip_passive:.6f} ± {std_z_tip_passive:.6f} m")

        # Phase: Sweep (chi_M > 0)
        if phase in ["sweep", "all"]:
            print(f"\n  [SWEEP] Running chi_M sweep...")

            # Use mean baseline from this scale
            if phase == "sweep":
                # If running sweep only, compute baseline on-the-fly
                z_tip_passive_mean = run_baseline_simulation(
                    L, radius, E0, rho, gravity, n_elements, final_time, dt, info, seed=0
                )
            else:
                z_tip_passive_mean = avg_z_tip_passive

            for chi_M in chi_M_values:
                A = np.pi * (radius ** 2)
                Bg_est = compute_bio_gravitational_number(chi_M, avg_grad_I, rho, A, gravity, L)

                for seed in range(n_seeds):
                    result = run_validation_simulation(
                        chi_M, L, radius, E0, rho, gravity, n_elements, final_time, dt,
                        info, z_tip_passive_mean, seed, scale
                    )

                    # Write to CSV
                    writer.writerow({
                        "seed": result.seed,
                        "scale": result.scale,
                        "chi_M": result.chi_M,
                        "Bg": result.Bg,
                        "z_tip": result.z_tip,
                        "z_tip_passive": result.z_tip_passive,
                        "eta_CC": result.eta_CC,
                        "S_lat": result.S_lat,
                        "cobb_angle": result.cobb_angle,
                        "bending_energy": result.bending_energy,
                        "shear_energy": result.shear_energy,
                        "gravitational_energy": result.gravitational_energy,
                        "runtime_sec": result.runtime_sec,
                        "peak_memory_mb": result.peak_memory_mb
                    })
                    csvfile.flush()

                    sim_count += 1

                    if sim_count % 10 == 0 or chi_M == chi_M_values[-1]:
                        print(f"    chi_M={chi_M:.2f}, Bg={Bg_est:.4f}, seed={seed}: "
                              f"eta_CC={result.eta_CC:.4f}, z_tip={result.z_tip:.6f}m  "
                              f"[{sim_count}/{total_sims}, {result.runtime_sec:.1f}s]")

    csvfile.close()

    print("\n" + "=" * 80)
    print(f"Experiment complete. Results saved to: {csv_file}")
    print(f"Total simulations: {sim_count}")
    print(f"Next step: Run analysis script to extract critical point and test hypotheses.")
    print(f"  python scripts/analysis/validate_bg_critical_point.py --input {csv_file}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Bio-Gravitational Number Critical Point Validation"
    )
    parser.add_argument(
        "--phase",
        choices=["baseline", "sweep", "all"],
        default="all",
        help="Experiment phase: baseline (chi_M=0), sweep (chi_M>0), or all"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/bg_validation/",
        help="Output directory for CSV files"
    )
    parser.add_argument(
        "--scales",
        type=float,
        nargs="+",
        default=[0.5, 1.0, 2.0],
        help="Scale factors (0.5=mouse, 1.0=human, 2.0=giraffe)"
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=8,
        help="Number of random seeds per configuration"
    )
    parser.add_argument(
        "--chi-M-min",
        type=float,
        default=0.1,
        help="Minimum chi_M value"
    )
    parser.add_argument(
        "--chi-M-max",
        type=float,
        default=50.0,
        help="Maximum chi_M value"
    )
    parser.add_argument(
        "--n-chi-M",
        type=int,
        default=30,
        help="Number of chi_M values (log-spaced)"
    )
    parser.add_argument(
        "--info-profile",
        choices=["sin2", "gaussian", "linear", "step"],
        default="sin2",
        help="Information field profile"
    )

    args = parser.parse_args()

    output_dir = Path(args.output)

    run_experiment(
        output_dir=output_dir,
        phase=args.phase,
        scale_factors=args.scales,
        n_seeds=args.seeds,
        chi_M_min=args.chi_M_min,
        chi_M_max=args.chi_M_max,
        n_chi_M=args.n_chi_M,
        info_profile=args.info_profile
    )


if __name__ == "__main__":
    main()

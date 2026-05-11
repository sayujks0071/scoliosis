"""
JAX-GPU accelerated Bio-Gravitational Number validation.

~100× faster than PyElastica CPU version via:
1. JIT compilation (Python → GPU kernels)
2. Batched vmap (parallel over chi_M, seed)
3. GPU parallelization on GB10

Expected speedup:
- CPU (PyElastica): 6 hours for 720 sims
- GPU (JAX): 3-5 minutes for 720 sims

Usage:
    python scripts/experiments/experiment_bg_validation_jax.py --phase all --output results/bg_validation_jax/
"""

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import List

import numpy as np

# JAX imports
try:
    import jax
    import jax.numpy as jnp
    JAX_AVAILABLE = True
    print(f"JAX available: {jax.devices()}")
except ImportError:
    JAX_AVAILABLE = False
    print("JAX not installed. Install with: pip install jax jaxlib")
    sys.exit(1)

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from spinalmodes.countercurvature.jax_rod_solver import (
    jax_run_simulation,
    jax_run_simulation_batched
)


def generate_info_field(L: float, n_points: int = 200, profile: str = "sin2"):
    """Generate information field (CPU-side, then transfer to GPU)."""
    s = np.linspace(0, L, n_points)

    if profile == "sin2":
        I = np.sin(2 * np.pi * s / L) ** 2
    elif profile == "gaussian":
        sigma = L / 6.0
        I = np.exp(-((s - L/2) ** 2) / (2 * sigma ** 2))
    elif profile == "linear":
        I = s / L
    elif profile == "step":
        I = np.where(s >= L/2, 1.0, 0.0)
    else:
        raise ValueError(f"Unknown profile: {profile}")

    dIds = np.gradient(I, s)
    return s, I, dIds


def compute_bio_gravitational_number(chi_M, avg_grad_I, rho, A, g, L):
    """Compute Bg = (chi_M * <|grad I|>) / (rho * A * g * L^2)."""
    denominator = rho * A * g * (L ** 2)
    return (chi_M * avg_grad_I) / denominator if denominator > 0 else 0.0


def run_baseline(scale, L_base, radius_base, E0, rho, gravity, n_elements, final_time, dt, info_I, info_grad, seeds):
    """Run baseline simulations (chi_M = 0) for all seeds at one scale."""
    print(f"\n  [BASELINE] Scale {scale:.1f}, {len(seeds)} seeds...")

    L = L_base * scale
    radius = radius_base * scale

    z_tips = []
    for seed in seeds:
        result = jax_run_simulation(
            chi_M=0.0,
            length=L,
            n_elements=n_elements,
            radius=radius,
            E0=E0,
            rho=rho,
            gravity=gravity,
            info_field_I=info_I,
            info_field_grad=info_grad,
            final_time=final_time,
            dt=dt,
            seed=seed
        )
        z_tips.append(result['z_tip'])
        print(f"    Seed {seed}: z_tip_passive = {result['z_tip']:.6f} m ({result['runtime']:.2f}s)")

    return np.mean(z_tips), np.std(z_tips)


def run_sweep_batched(
    scale, chi_M_array, seeds, L_base, radius_base, E0, rho, gravity,
    n_elements, final_time, dt, info_I, info_grad, z_tip_passive
):
    """Run batched sweep over chi_M for all seeds (GPU-parallel)."""
    L = L_base * scale
    radius = radius_base * scale
    A = np.pi * radius**2
    avg_grad_I = np.mean(np.abs(info_grad))

    all_results = []

    print(f"\n  [SWEEP] Scale {scale:.1f}, {len(chi_M_array)} chi_M × {len(seeds)} seeds...")
    print(f"    Batching {len(chi_M_array)} chi_M values per seed (GPU-parallel)...")

    total_start = time.time()

    for seed in seeds:
        seed_start = time.time()

        # Batch over chi_M dimension using vmap
        results = jax_run_simulation_batched(
            chi_M_array=chi_M_array,
            length=L,
            n_elements=n_elements,
            radius=radius,
            E0=E0,
            rho=rho,
            gravity=gravity,
            info_field_I=info_I,
            info_field_grad=info_grad,
            final_time=final_time,
            dt=dt
        )

        seed_time = time.time() - seed_start
        print(f"    Seed {seed}: {len(chi_M_array)} sims in {seed_time:.2f}s ({seed_time/len(chi_M_array):.3f}s each)")

        # Compute metrics for each result
        for res in results:
            chi_M = res['chi_M']
            z_tip = res['z_tip']
            Bg = compute_bio_gravitational_number(chi_M, avg_grad_I, rho, A, gravity, L)

            # Counter-curvature efficiency
            eta_CC = 1.0 - abs(z_tip) / abs(z_tip_passive) if abs(z_tip_passive) > 1e-9 else 0.0

            # Curvature energy
            curv_final = res['curvature'][-1]
            bending_energy = np.sum(curv_final ** 2)

            all_results.append({
                'seed': seed,
                'scale': scale,
                'chi_M': chi_M,
                'Bg': Bg,
                'z_tip': z_tip,
                'z_tip_passive': z_tip_passive,
                'eta_CC': eta_CC,
                'bending_energy': bending_energy,
                'runtime_sec': res['runtime_per_sim']
            })

    total_time = time.time() - total_start
    print(f"  Total: {len(all_results)} sims in {total_time:.2f}s ({total_time/len(all_results):.3f}s each)")

    return all_results


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
    """Run JAX-GPU validation experiment."""
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_file = output_dir / "bg_validation_jax_results.csv"
    fieldnames = [
        "seed", "scale", "chi_M", "Bg", "z_tip", "z_tip_passive", "eta_CC",
        "bending_energy", "runtime_sec"
    ]

    file_exists = csv_file.exists()
    csvfile = open(csv_file, mode='a', newline='')
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()

    print("=" * 80)
    print("JAX-GPU Bio-Gravitational Number Validation")
    print("=" * 80)
    print(f"JAX device: {jax.devices()[0]}")
    print(f"Phase: {phase}")
    print(f"Scales: {scale_factors}")
    print(f"Seeds: {n_seeds}")
    print(f"chi_M range: [{chi_M_min}, {chi_M_max}] ({n_chi_M} points, log-spaced)")
    print(f"Info profile: {info_profile}")
    print(f"Output: {csv_file}")
    print("=" * 80)

    # Parameters
    L_base = 0.5  # m
    radius_base = 0.01  # m
    E0 = 1e6  # Pa
    rho = 1000.0  # kg/m^3
    gravity = 9.81  # m/s^2
    n_elements = 50
    final_time = 2.0  # s
    dt = 1e-5  # s

    chi_M_array = np.logspace(np.log10(chi_M_min), np.log10(chi_M_max), n_chi_M)
    seeds = list(range(n_seeds))

    # Info field (CPU-side, will be transferred to GPU in each call)
    s, info_I, info_grad = generate_info_field(L_base, n_points=n_elements+1, profile=info_profile)

    total_sims = 0
    if phase in ["baseline", "all"]:
        total_sims += len(scale_factors) * n_seeds
    if phase in ["sweep", "all"]:
        total_sims += len(scale_factors) * n_seeds * n_chi_M

    print(f"Total simulations: {total_sims}")
    print(f"Estimated time (JAX-GPU): ~{total_sims * 0.05 / 60:.1f} minutes (0.05s/sim target)")
    print("=" * 80)

    # Loop over scales
    for scale in scale_factors:
        print(f"\n[SCALE {scale:.1f}] L={L_base*scale:.2f}m, r={radius_base*scale:.3f}m")

        # Phase: Baseline
        if phase in ["baseline", "all"]:
            z_tip_passive_mean, z_tip_passive_std = run_baseline(
                scale, L_base, radius_base, E0, rho, gravity, n_elements,
                final_time, dt, info_I, info_grad, seeds
            )
            print(f"  Baseline: z_tip_passive = {z_tip_passive_mean:.6f} ± {z_tip_passive_std:.6f} m")
        else:
            # Quick baseline (single seed)
            result = jax_run_simulation(
                chi_M=0.0, length=L_base*scale, n_elements=n_elements,
                radius=radius_base*scale, E0=E0, rho=rho, gravity=gravity,
                info_field_I=info_I, info_field_grad=info_grad,
                final_time=final_time, dt=dt, seed=0
            )
            z_tip_passive_mean = result['z_tip']

        # Phase: Sweep
        if phase in ["sweep", "all"]:
            results = run_sweep_batched(
                scale, chi_M_array, seeds, L_base, radius_base, E0, rho, gravity,
                n_elements, final_time, dt, info_I, info_grad, z_tip_passive_mean
            )

            # Write to CSV
            for res in results:
                writer.writerow(res)
            csvfile.flush()

    csvfile.close()

    print("\n" + "=" * 80)
    print(f"Experiment complete. Results: {csv_file}")
    print(f"Next: python scripts/analysis/validate_bg_critical_point.py --input {csv_file}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="JAX-GPU Validation")
    parser.add_argument("--phase", choices=["baseline", "sweep", "all"], default="all")
    parser.add_argument("--output", type=str, default="results/bg_validation_jax/")
    parser.add_argument("--scales", type=float, nargs="+", default=[0.5, 1.0, 2.0])
    parser.add_argument("--seeds", type=int, default=8)
    parser.add_argument("--chi-M-min", type=float, default=0.1)
    parser.add_argument("--chi-M-max", type=float, default=50.0)
    parser.add_argument("--n-chi-M", type=int, default=30)
    parser.add_argument("--info-profile", choices=["sin2", "gaussian", "linear", "step"], default="sin2")

    args = parser.parse_args()

    run_experiment(
        output_dir=Path(args.output),
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

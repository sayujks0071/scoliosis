"""
Experiment: Optimization Failure — Exploding Gradient Map.

This script implements Phase 1, Week 3 of the Gravity Optimization research schedule.
It maps the "Exploding Gradient" region where high information-to-curvature coupling
(chi_kappa) combined with low stiffness anisotropy leads to instability (scoliosis).

Key innovation: Sensory noise injection into the information gradient.
    grad_I_noisy = grad_I + eta, where eta ~ N(0, sigma_noise)

This models imprecise mechanosensing (e.g. PIEZO2 dysfunction, proprioceptive
error) that degrades the quality of the shape-maintenance gradient signal.

Hypothesis:
    Scoliosis emerges as an "Exploding Gradient" when:
    1. The Learning Rate (chi_kappa) exceeds structural damping (anisotropy)
    2. Sensory noise (sigma) degrades gradient fidelity below a critical threshold
    3. The combination creates a wedge-shaped instability region in
       (chi_kappa, sigma_noise) space

Measurable outputs:
    - Phase diagram of Cobb Angle in (chi_kappa, sigma_noise) space
    - Critical noise threshold sigma_c(chi_kappa) for scoliosis onset
    - Torsion emergence as a secondary instability marker
    - Comparison: noisy vs noise-free gradient descent convergence

References:
    - Research Schedule Phase 1, Week 3: "Optimization Failure"
    - Hypothesis Register: H_2026_02_08_EnergyPhase
"""

import argparse
import csv
import os
import sys
import time
import tracemalloc
from datetime import datetime

__version__ = "1.0.1"
from pathlib import Path
from typing import Dict, List

import numpy as np

sys.path.append(str(Path(__file__).parent.parent / "src"))

from spinalmodes.countercurvature.coupling import CounterCurvatureParams
from spinalmodes.countercurvature.info_fields import InfoField1D
from spinalmodes.countercurvature.pyelastica_bridge import (
    CounterCurvatureRodSystem,
    compute_U_CC,
    verify_pyelastica_installation,
)

# --- Mutation Parameter Map ---
# Digital Twin parameters for specific genetic defects.
# chi_kappa: Learning Rate (Information Sensitivity)
# anisotropy: Structural Stiffness Anisotropy (EI_major / EI_minor)
# sigma_noise: Sensory Noise Level (Gradient Corruption)
#
# Baseline: chi=10.0, aniso=1.5, sigma=0.1
MUTATION_PARAMETERS: Dict[str, Dict[str, float]] = {
    "WT": {"chi_kappa": 10.0, "anisotropy": 1.5, "sigma_noise": 0.1},
    "PIEZO2": {"chi_kappa": 20.0, "anisotropy": 1.5, "sigma_noise": 2.0},  # High Noise (Blindness)
    "LBX1": {"chi_kappa": 5.0, "anisotropy": 1.0, "sigma_noise": 0.5},    # Low Tone + Low Anisotropy
    "FBN1": {"chi_kappa": 10.0, "anisotropy": 0.5, "sigma_noise": 0.1},   # Loss of Stiffness (Marfan)
    "POC5": {"chi_kappa": 10.0, "anisotropy": 1.5, "sigma_noise": 1.5},   # Ciliary Defect (Noise)
    "PTK7": {"chi_kappa": 10.0, "anisotropy": 1.0, "sigma_noise": 0.1},   # Loss of Polarity (Anisotropy)
}


def create_noisy_info_field(
    s: np.ndarray,
    info_center_frac: float = 0.5,
    info_width_frac: float = 0.1,
    info_amplitude: float = 0.5,
    sigma_noise: float = 0.0,
    rng: np.random.Generator = None,
) -> InfoField1D:
    """Create an information field with optional gradient noise.

    The base field is a Gaussian bump (representing HOX-encoded shape programme).
    Noise is injected into the gradient dI/ds to model imprecise mechanosensing.

    Parameters
    ----------
    s : np.ndarray
        Arc-length grid.
    info_center_frac : float
        Center of Gaussian bump as fraction of length.
    info_width_frac : float
        Width of Gaussian bump as fraction of length.
    info_amplitude : float
        Amplitude of the information bump.
    sigma_noise : float
        Standard deviation of additive Gaussian noise on dI/ds.
    rng : np.random.Generator
        Random number generator for reproducibility.

    Returns
    -------
    InfoField1D
        Information field with noisy gradient.
    """
    length = s[-1] - s[0]
    center = info_center_frac * length
    width = info_width_frac * length

    # Base information field (clean signal)
    I = 0.5 + info_amplitude * np.exp(-0.5 * ((s - center) / width) ** 2)
    dIds_clean = np.gradient(I, s)

    # Inject sensory noise into the gradient
    if sigma_noise > 0.0 and rng is not None:
        noise = rng.normal(0.0, sigma_noise, size=dIds_clean.shape)
        dIds = dIds_clean + noise
    else:
        dIds = dIds_clean

    return InfoField1D(s=s, I=I, dIds=dIds)


def run_single_simulation(
    mutation_name: str,
    chi_kappa: float,
    sigma_noise: float,
    anisotropy: float,
    trial: int,
    writer: csv.DictWriter,
    csvfile,
    n_elements: int = 50,
    final_time: float = 2.0,
    seed: int = 42,
    length: float = 0.5,
):
    """Run a single simulation instance."""

    # Rod parameters
    radius = 0.01     # metres
    E0 = 1e6          # Pa
    rho = 1000.0      # kg/m^3
    gravity = 9.81
    dt = 1e-5

    rng = np.random.default_rng(seed + trial * 1000 + hash(
        (mutation_name, chi_kappa, sigma_noise)
    ) % 10000)

    tracemalloc.start()
    t0 = time.time()

    # Create noisy information field
    s = np.linspace(0, length, n_elements + 1)
    info = create_noisy_info_field(
        s, sigma_noise=sigma_noise, rng=rng
    )

    # Coupling: pure curvature drive (no active moments)
    params = CounterCurvatureParams(
        chi_kappa=chi_kappa,
        chi_tau=0.0,
        chi_E=0.0,
        chi_M=0.0,
        scale_length=length,
    )

    # Baseline sagittal curvature
    kappa_gen = np.zeros((3, n_elements + 1))
    kappa_gen[0, :] = 2.0  # Sagittal kyphosis

    # Create and run
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
        stiffness_anisotropy=anisotropy,
    )

    result = rod_system.run_simulation(
        final_time=final_time,
        dt=dt,
        save_every=5000,
        gravity=gravity,
        boundary_condition="fixed",
        progress_bar=False,
    )

    t1 = time.time()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Compute metrics
    sim_metrics = result.compute_final_metrics()
    cost = compute_U_CC(result, info, params, gravity, rho, E0)

    row = {
        "timestamp": datetime.now().isoformat(),
        "mutation": mutation_name,
        "chi_kappa": chi_kappa,
        "sigma_noise": sigma_noise,
        "anisotropy": anisotropy,
        "trial": trial,
        "cobb_angle": sim_metrics.get("cobb_angle", 0.0),
        "max_torsion": sim_metrics.get("max_torsion", 0.0),
        "S_lat": sim_metrics.get("S_lat", 0.0),
        "max_curvature": sim_metrics.get("max_curvature", 0.0),
        "U_CC": cost["U_CC"],
        "U_gravity": cost["U_gravity"],
        "U_elastic": cost["U_elastic"],
        "U_info": cost["U_info"],
        "info_gain_ratio": cost["info_gain_ratio"],
        "runtime_sec": round(t1 - t0, 4),
        "peak_memory_mb": round(peak / (1024 * 1024), 2),
    }
    writer.writerow(row)
    csvfile.flush()

    print(
        f"{mutation_name:<8} | {chi_kappa:<6.1f} | {sigma_noise:<6.2f} | {anisotropy:<6.1f} | "
        f"{row['cobb_angle']:<8.2f} | {row['max_torsion']:<9.4f} | "
        f"{row['S_lat']:<8.4f}"
    )


def run_optimization_failure_sweep(
    out_file: str,
    chi_kappas: List[float],
    sigma_noises: List[float],
    n_trials: int = 3,
    n_elements: int = 50,
    final_time: float = 2.0,
    seed: int = 42,
    run_mutations: bool = False,
):
    """Run the optimization failure parameter sweep."""
    verify_pyelastica_installation(exit_on_fail=True)

    print("=" * 100)
    print("EXPERIMENT: Optimization Failure — Exploding Gradient Map")
    print("=" * 100)
    if run_mutations:
        print(f"Running Mutation Scenarios: {list(MUTATION_PARAMETERS.keys())}")
    else:
        print(f"Sweeping chi_kappa: {chi_kappas}")
        print(f"Sweeping sigma_noise: {sigma_noises}")
    print(f"Trials per point: {n_trials}")
    print(f"Output: {out_file}")
    print("=" * 100)

    # Prepare output
    out_dir = os.path.dirname(out_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    fieldnames = [
        "timestamp", "mutation", "chi_kappa", "sigma_noise", "anisotropy", "trial",
        "cobb_angle", "max_torsion", "S_lat", "max_curvature",
        "U_CC", "U_gravity", "U_elastic", "U_info", "info_gain_ratio",
        "runtime_sec", "peak_memory_mb",
    ]

    file_exists = os.path.isfile(out_file)
    with open(out_file, mode="a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        print(
            f"{'Mutation':<8} | {'Chi':<6} | {'Sigma':<6} | {'Aniso':<6} | "
            f"{'Cobb':<8} | {'Torsion':<9} | {'S_lat':<8}"
        )
        print("-" * 90)

        count = 0
        total = 0

        if run_mutations:
            # Run specific mutation scenarios
            total = len(MUTATION_PARAMETERS) * n_trials
            for mutation, params in MUTATION_PARAMETERS.items():
                for trial in range(n_trials):
                    count += 1
                    run_single_simulation(
                        mutation_name=mutation,
                        chi_kappa=params["chi_kappa"],
                        sigma_noise=params["sigma_noise"],
                        anisotropy=params["anisotropy"],
                        trial=trial,
                        writer=writer,
                        csvfile=csvfile,
                        n_elements=n_elements,
                        final_time=final_time,
                        seed=seed
                    )

        else:
            # Run generic parameter sweep
            total = len(chi_kappas) * len(sigma_noises) * n_trials
            anisotropy = 1.5
            for chi_kappa in chi_kappas:
                for sigma_noise in sigma_noises:
                    for trial in range(n_trials):
                        count += 1
                        run_single_simulation(
                            mutation_name="Sweep",
                            chi_kappa=chi_kappa,
                            sigma_noise=sigma_noise,
                            anisotropy=anisotropy,
                            trial=trial,
                            writer=writer,
                            csvfile=csvfile,
                            n_elements=n_elements,
                            final_time=final_time,
                            seed=seed
                        )

    print("=" * 100)
    print(f"Experiment complete. {count}/{total} simulations finished.")
    generate_report(out_file)


def generate_report(csv_file: str):
    """Generate a Markdown report from the sweep results."""
    md_file = str(Path(csv_file).with_suffix(".md"))

    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("No data to report.")
        return

    with open(md_file, "w") as f:
        f.write("# Optimization Failure: Exploding Gradient Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Source:** `{os.path.basename(csv_file)}`\n\n")

        # --- Mutation Analysis ---
        f.write("## Mutation Analysis (Digital Twins)\n\n")
        f.write("| Mutation | chi_kappa | sigma_noise | Aniso | Mean Cobb | Std Cobb | n_scoliotic |\n")
        f.write("|---|---|---|---|---|---|---|\n")

        # Filter for mutation rows
        mutation_rows = [r for r in rows if r["mutation"] != "Sweep"]
        if mutation_rows:
            from collections import defaultdict
            mut_groups = defaultdict(list)
            for r in mutation_rows:
                mut_groups[r["mutation"]].append(r)

            for mut, r_list in mut_groups.items():
                cobbs = [float(r["cobb_angle"]) for r in r_list]
                p = r_list[0]
                mean_c = np.mean(cobbs)
                std_c = np.std(cobbs)
                n_scol = sum(1 for c in cobbs if c > 10.0)
                f.write(f"| {mut} | {p['chi_kappa']} | {p['sigma_noise']} | {p['anisotropy']} | {mean_c:.2f} | {std_c:.2f} | {n_scol}/{len(cobbs)} |\n")
        else:
            f.write("| No mutation data available. |\n")

        # --- Sweep Analysis ---
        f.write("\n## Parameter Sweep Analysis\n\n")
        sweep_rows = [r for r in rows if r["mutation"] == "Sweep"]
        if sweep_rows:
            f.write("| chi_kappa | sigma_noise | mean_Cobb | std_Cobb | n_scoliotic |\n")
            f.write("|-----------|-------------|-----------|----------|-------------|\n")

            from collections import defaultdict
            groups = defaultdict(list)
            for r in sweep_rows:
                key = (float(r["chi_kappa"]), float(r["sigma_noise"]))
                groups[key].append(float(r["cobb_angle"]))

            for (ck, sn), cobbs in sorted(groups.items()):
                mean_c = np.mean(cobbs)
                std_c = np.std(cobbs)
                n_scol = sum(1 for c in cobbs if c > 10.0)
                f.write(f"| {ck:.2f} | {sn:.3f} | {mean_c:.2f} | {std_c:.2f} | {n_scol}/{len(cobbs)} |\n")

    print(f"Report generated: {md_file}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Optimization Failure: Exploding Gradient Experiment"
    )
    parser.add_argument(
        "--out-file", type=str,
        default="outputs/optimization_failure/exploding_gradient.csv",
    )
    parser.add_argument("--quick-test", action="store_true")
    parser.add_argument("--run-mutations", action="store_true", help="Run specific mutation scenarios")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-trials", type=int, default=None)
    parser.add_argument("--n-elements", type=int, default=None)
    parser.add_argument("--final-time", type=float, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.quick_test:
        chi_kappas = [0.0, 10.0, 20.0]
        sigma_noises = [0.0, 0.5, 1.0]
        n_trials = args.n_trials if args.n_trials is not None else 2
        n_elements = args.n_elements if args.n_elements is not None else 20
        final_time = args.final_time if args.final_time is not None else 0.1
    else:
        chi_kappas = [0.0, 2.0, 5.0, 10.0, 15.0, 20.0]
        sigma_noises = [0.0, 0.1, 0.2, 0.5, 1.0, 2.0]
        n_trials = args.n_trials if args.n_trials is not None else 5
        n_elements = args.n_elements if args.n_elements is not None else 50
        final_time = args.final_time if args.final_time is not None else 2.0

    run_optimization_failure_sweep(
        out_file=args.out_file,
        chi_kappas=chi_kappas,
        sigma_noises=sigma_noises,
        n_trials=n_trials,
        n_elements=n_elements,
        final_time=final_time,
        seed=args.seed,
        run_mutations=args.run_mutations,
    )

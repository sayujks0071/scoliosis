"""Perform sensitivity analysis and uncertainty quantification for the IEC model.

This script varies model parameters (stiffness, coupling, gravity) within
a ±10% range and computes the standard deviation of the output metrics
(D_geo_norm, Cobb angle).

Usage:
    python3 -m spinalmodes.experiments.countercurvature.sensitivity_analysis
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

from spinalmodes.countercurvature import (
    CounterCurvatureParams,
    InfoField1D,
    compute_countercurvature_metric,
    geodesic_curvature_deviation,
    make_uniform_grid,
)
from spinalmodes.countercurvature.coupling import (
    compute_active_moments,
    compute_effective_stiffness,
    compute_rest_curvature,
)
from spinalmodes.iec import solve_beam_static


def create_spinal_info_field(s: np.ndarray, length: float) -> InfoField1D:
    s_norm = s / length
    lumbar = 0.7 * np.exp(-((s_norm - 0.25) ** 2) / (2 * 0.1**2))
    cervical = 0.5 * np.exp(-((s_norm - 0.8) ** 2) / (2 * 0.08**2))
    I = lumbar + cervical + 0.3
    return InfoField1D.from_array(s, I)


def run_single_sim(params_dict, length=0.4, n_nodes=100):
    s = make_uniform_grid(length, n_nodes)
    info_field = create_spinal_info_field(s, length)

    # Extract params
    chi_k = params_dict["chi_kappa"]
    chi_e = params_dict["chi_E"]
    e0 = params_dict["E0"]
    g = params_dict["gravity"]
    i_moment = params_dict["I_moment"]
    rho_a = params_dict["rho_A"]

    gravity_load = rho_a * g

    # Cooperative/Target state
    params_cc = CounterCurvatureParams(chi_kappa=chi_k, chi_E=chi_e, chi_M=0.0)
    kappa_rest = compute_rest_curvature(info_field, params_cc, np.zeros_like(s))
    e_eff = compute_effective_stiffness(info_field, params_cc, e0)
    m_info = compute_active_moments(info_field, params_cc)

    _, kappa_sim = solve_beam_static(
        s, kappa_rest, e_eff, m_info, I_moment=i_moment, distributed_load=gravity_load
    )

    # Passive baseline (for D_geo)
    params_passive = CounterCurvatureParams(chi_kappa=0, chi_E=0, chi_M=0)
    kappa_rest_p = compute_rest_curvature(info_field, params_passive, np.zeros_like(s))
    e_p = np.full_like(s, e0)
    _, kappa_p = solve_beam_static(
        s, kappa_rest_p, e_p, np.zeros_like(s), I_moment=i_moment, distributed_load=gravity_load
    )

    # Metric
    g_eff = compute_countercurvature_metric(info_field, beta1=1.0, beta2=0.5)
    metrics = geodesic_curvature_deviation(s, kappa_p, kappa_sim, g_eff)

    return metrics["D_geo_norm"]


def run_sensitivity_analysis(n_samples=100, perturbation=0.1, output_dir="outputs/experiments/sensitivity"):
    baseline = {
        "chi_kappa": 0.05,
        "chi_E": 0.1,
        "E0": 1e9,
        "gravity": 9.81,
        "I_moment": 1e-8,
        "rho_A": 0.1, # kg/m
    }

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    results = []

    print(f"Running Monte Carlo Sensitivity Analysis ({n_samples} samples)...")
    for i in tqdm(range(n_samples)):
        perturbed = {k: v * (1 + np.random.uniform(-perturbation, perturbation)) for k, v in baseline.items()}
        d_geo_norm = run_single_sim(perturbed)
        results.append(d_geo_norm)

    df = pd.DataFrame(results, columns=["D_geo_norm"])
    stats = df.describe()

    mean = stats.loc["mean", "D_geo_norm"]
    std = stats.loc["std", "D_geo_norm"]

    print(f"\nSensitivity Results (±{perturbation*100}% perturbation):")
    print(f"  D_geo_norm = {mean:.4f} ± {std:.4f}")

    # Save results
    df.to_csv(Path(output_dir) / "sensitivity_results.csv", index=False)

    # Plot histogram
    plt.figure(figsize=(8, 6))
    plt.hist(results, bins=20, color="skyblue", edgecolor="black", alpha=0.7)
    plt.axvline(mean, color="red", linestyle="dashed", linewidth=2, label=f"Mean: {mean:.4f}")
    plt.axvline(mean + std, color="green", linestyle="dotted", linewidth=1.5, label=f"SD: ±{std:.4f}")
    plt.axvline(mean - std, color="green", linestyle="dotted", linewidth=1.5)
    plt.title(f"Uncertainty Quantification for D̂_geo\n(±{perturbation*100}% parameter variation)")
    plt.xlabel("D̂_geo (normalized geodesic deviation)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(alpha=0.3)

    fig_path = Path(output_dir) / "sensitivity_histogram.png"
    plt.savefig(fig_path, dpi=300)
    print(f"✅ Saved histogram to {fig_path}")


if __name__ == "__main__":
    run_sensitivity_analysis()

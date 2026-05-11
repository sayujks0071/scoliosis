"""Example: Computing countercurvature metric and geodesic deviation.

This script demonstrates how to compute the biological countercurvature metric
g_eff(s) and the geodesic curvature deviation D_geo from simulation outputs.

Usage:
    python -m spinalmodes.experiments.countercurvature.example_countercurvature_metrics
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from spinalmodes.countercurvature import (
    CounterCurvatureParams,
    InfoField1D,
    compute_countercurvature_metric,
    geodesic_curvature_deviation,
    make_uniform_grid,
)
from spinalmodes.countercurvature.coupling import (
    compute_effective_stiffness,
    compute_rest_curvature,
)
from spinalmodes.iec import solve_beam_static


def main():
    """Demonstrate countercurvature metric computation."""
    print("📐 Computing countercurvature metric and geodesic deviation...")
    print()

    # Setup: create a simple rod with information field
    length = 0.4  # metres
    n_nodes = 100
    s = make_uniform_grid(length, n_nodes)

    # Create information field (e.g., neural control)
    s_norm = s / length
    I = 0.5 + 0.3 * np.exp(-((s_norm - 0.3) ** 2) / (2 * 0.1**2))  # Gaussian bump
    info = InfoField1D.from_array(s, I)

    # Case 1: Passive (no information coupling)
    params_passive = CounterCurvatureParams(chi_kappa=0.0, chi_E=0.0, chi_M=0.0)
    kappa_gen = np.zeros_like(s)
    kappa_rest_passive = compute_rest_curvature(info, params_passive, kappa_gen)
    E_passive = np.full_like(s, 1e9)
    M_passive = np.zeros_like(s)

    theta_passive, kappa_passive = solve_beam_static(
        s, kappa_rest_passive, E_passive, M_passive, I_moment=1e-8, distributed_load=50.0
    )

    # Case 2: Information-driven (with coupling)
    params_info = CounterCurvatureParams(chi_kappa=0.04, chi_E=0.1, chi_M=0.0)
    kappa_rest_info = compute_rest_curvature(info, params_info, kappa_gen)
    E_info = compute_effective_stiffness(info, params_info, 1e9, model="linear")
    M_info = np.zeros_like(s)

    theta_info, kappa_info = solve_beam_static(
        s, kappa_rest_info, E_info, M_info, I_moment=1e-8, distributed_load=50.0
    )

    # Compute countercurvature metric g_eff(s)
    g_eff = compute_countercurvature_metric(info, beta1=1.0, beta2=0.5)

    # Compute geodesic curvature deviation
    deviation_results = geodesic_curvature_deviation(
        s, kappa_passive, kappa_info, g_eff
    )

    print("Results:")
    print(f"  D_geo = {deviation_results['D_geo']:.6f} 1/m")
    print(f"  D_geo_norm = {deviation_results['D_geo_norm']:.6f} (dimensionless)")
    print(f"  Base energy = {deviation_results['base_energy']:.6e} 1/m²")
    print()

    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Panel A: Information field
    ax = axes[0, 0]
    ax.plot(s, info.I, "g-", linewidth=2, label="I(s)")
    ax_twin = ax.twinx()
    ax_twin.plot(s, info.dIds, "orange", linewidth=2, linestyle="--", label="∂I/∂s")
    ax.set_xlabel("Arc-length s (m)")
    ax.set_ylabel("Information density I(s)", color="g")
    ax_twin.set_ylabel("Information gradient ∂I/∂s", color="orange")
    ax.set_title("(A) Information Field")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left")
    ax_twin.legend(loc="upper right")

    # Panel B: Countercurvature metric
    ax = axes[0, 1]
    ax.plot(s, g_eff, "purple", linewidth=2, label="g_eff(s)")
    ax.axhline(1.0, color="k", linestyle=":", alpha=0.5, label="Flat metric (g=1)")
    ax.set_xlabel("Arc-length s (m)")
    ax.set_ylabel("Countercurvature metric g_eff(s)")
    ax.set_title("(B) Biological Countercurvature Metric")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_yscale("log")

    # Panel C: Curvature profiles
    ax = axes[1, 0]
    ax.plot(s, kappa_passive, "b-", linewidth=2, label="κ_passive(s)")
    ax.plot(s, kappa_info, "r-", linewidth=2, label="κ_info(s)")
    ax.axhline(0, color="k", linestyle=":", alpha=0.5)
    ax.set_xlabel("Arc-length s (m)")
    ax.set_ylabel("Curvature κ (1/m)")
    ax.set_title("(C) Curvature Profiles")
    ax.legend()
    ax.grid(alpha=0.3)

    # Panel D: Metrics summary
    ax = axes[1, 1]
    ax.axis("off")
    metrics_text = f"""
    Geodesic Curvature Deviation:
    
    D_geo = {deviation_results['D_geo']:.6f} 1/m
    D_geo_norm = {deviation_results['D_geo_norm']:.6f}
    
    Base energy = {deviation_results['base_energy']:.6e} 1/m²
    
    Interpretation:
    - D_geo measures distance between passive
      and info-driven curvature in the
      countercurvature metric g_eff(s)
    - Large D_geo → strong information-driven
      reshaping of geometry
    """
    ax.text(0.1, 0.5, metrics_text, fontsize=10, family="monospace", va="center")

    plt.tight_layout()

    # Save figure
    output_dir = Path("outputs/experiments/countercurvature_metrics")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_path = output_dir / "countercurvature_metrics_example.png"
    plt.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ Saved figure to {fig_path}")

    # Save data
    import pandas as pd

    df = pd.DataFrame(
        {
            "s": s,
            "I": info.I,
            "dIds": info.dIds,
            "g_eff": g_eff,
            "kappa_passive": kappa_passive,
            "kappa_info": kappa_info,
            "delta_kappa": kappa_info - kappa_passive,
        }
    )
    csv_path = output_dir / "countercurvature_metrics_data.csv"
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved data to {csv_path}")

    print()
    print("✅ Example complete!")
    print()
    print("   The countercurvature metric g_eff(s) encodes how information")
    print("   processing reshapes the effective geometry experienced by the rod.")
    print("   The geodesic deviation D_geo quantifies how far information-driven")
    print("   curvature departs from the gravity-selected mode.")


if __name__ == "__main__":
    main()


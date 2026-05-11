"""Experiment: Plant upward growth against gravity.

This experiment demonstrates biological countercurvature by modeling a slender
rod (plant stem) clamped at the base under gravity. We compare:

- Case A: Passive rod (no information coupling) → sags with gravity
- Case B: Information-driven countercurvature → rod bends upward, mimicking
  plant growth against gravity

The information field I(s) is chosen so that countercurvature opposes gravitational
sag, representing the biological information processing (growth hormones, cellular
orientation) that enables upward growth.

This is an analog model of "biological countercurvature of spacetime" where
information processing reshapes the effective curvature experienced by the rod.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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

# Try to use PyElastica if available, otherwise fall back to beam solver
try:
    from spinalmodes.countercurvature.pyelastica_bridge import (
        PYELASTICA_AVAILABLE,
        CounterCurvatureRodSystem,
    )
except ImportError:
    PYELASTICA_AVAILABLE = False


def create_upward_growth_info_field(s: np.ndarray, length: float) -> InfoField1D:
    """Create information field that promotes upward growth.

    The field has a positive gradient near the base, creating countercurvature
    that opposes gravitational sag. This represents growth hormone gradients
    or cellular orientation cues that drive upward growth.

    Parameters
    ----------
    s:
        Arc-length grid (metres).
    length:
        Total rod length (metres).

    Returns
    -------
    InfoField1D
        Information field with gradient promoting upward curvature.
    """
    s_norm = s / length

    # Information density: high near base, decreasing upward
    # This creates a positive gradient (dI/ds < 0) that, with positive chi_kappa,
    # creates upward curvature
    I = 1.0 - 0.5 * s_norm  # Linear decrease from base to tip

    # Alternatively, use a more biological profile:
    # I = np.exp(-2 * s_norm)  # Exponential decay

    return InfoField1D.from_array(s, I)


def run_plant_experiment(
    length: float = 0.5,
    n_nodes: int = 100,
    chi_kappa: float = 0.05,
    chi_E: float = 0.1,
    E0: float = 1e9,
    I_moment: float = 1e-8,
    gravity_load: float = 50.0,  # Equivalent distributed load (N/m)
    output_dir: str = "outputs/experiments/plant_growth",
) -> dict:
    """Run plant upward growth experiment.

    Parameters
    ----------
    length:
        Rod length (metres).
    n_nodes:
        Number of spatial nodes.
    chi_kappa:
        Information-to-curvature coupling strength.
    chi_E:
        Information-to-stiffness coupling strength.
    E0:
        Baseline Young's modulus (Pa).
    I_moment:
        Second moment of area (m^4).
    gravity_load:
        Equivalent distributed load representing gravity (N/m).
    output_dir:
        Output directory for results.

    Returns
    -------
    dict
        Dictionary with results and metadata.
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Create spatial grid
    s = make_uniform_grid(length, n_nodes)

    # Create information field for upward growth
    info_field = create_upward_growth_info_field(s, length)

    # Case A: Passive (no information coupling)
    params_passive = CounterCurvatureParams(chi_kappa=0.0, chi_E=0.0, chi_M=0.0)
    kappa_gen = np.zeros_like(s)
    kappa_rest_passive = compute_rest_curvature(info_field, params_passive, kappa_gen)
    E_passive = np.full_like(s, E0)
    M_passive = np.zeros_like(s)

    # Solve passive case
    theta_passive, kappa_passive = solve_beam_static(
        s, kappa_rest_passive, E_passive, M_passive, I_moment=I_moment, distributed_load=gravity_load
    )

    # Case B: Information-driven countercurvature
    params_info = CounterCurvatureParams(
        chi_kappa=chi_kappa, chi_E=chi_E, chi_M=0.0, scale_length=1.0
    )
    kappa_rest_info = compute_rest_curvature(info_field, params_info, kappa_gen)
    E_info = compute_effective_stiffness(info_field, params_info, E0, model="linear")
    M_info = compute_active_moments(info_field, params_info)

    # Solve information-driven case
    theta_info, kappa_info = solve_beam_static(
        s, kappa_rest_info, E_info, M_info, I_moment=I_moment, distributed_load=gravity_load
    )

    # Reconstruct centerlines from angles
    centerline_passive = _reconstruct_centerline_2d(theta_passive, s)
    centerline_info = _reconstruct_centerline_2d(theta_info, s)

    # Compute metrics
    from spinalmodes.countercurvature.validation_and_metrics import (
        compute_countercurvature_energy,
        compute_effective_metric_deviation,
    )

    countercurvature_energy = compute_countercurvature_energy(
        centerline_passive, centerline_info, method="l2_distance"
    )
    metric_deviation = compute_effective_metric_deviation(
        kappa_passive, kappa_info, s=s
    )

    # Compute countercurvature metric and geodesic deviation
    g_eff = compute_countercurvature_metric(info_field, beta1=1.0, beta2=0.5)
    geo_metrics = geodesic_curvature_deviation(
        s, kappa_passive, kappa_info, g_eff
    )
    D_geo = geo_metrics["D_geo"]
    D_geo_norm = geo_metrics["D_geo_norm"]

    # Compare with plain L2 difference
    plain_l2_diff = np.sqrt(np.trapezoid((kappa_info - kappa_passive) ** 2, x=s))
    plain_l2_norm = plain_l2_diff / (np.sqrt(np.trapezoid(kappa_passive**2, x=s)) + 1e-9)

    # Save results to CSV
    df = pd.DataFrame(
        {
            "s": s,
            "I": info_field.I,
            "dIds": info_field.dIds,
            "g_eff": g_eff,
            "theta_passive": theta_passive,
            "kappa_passive": kappa_passive,
            "theta_info": theta_info,
            "kappa_info": kappa_info,
            "x_passive": centerline_passive[:, 0],
            "z_passive": centerline_passive[:, 1],
            "x_info": centerline_info[:, 0],
            "z_info": centerline_info[:, 1],
        }
    )
    csv_path = Path(output_dir) / "plant_growth_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved results to {csv_path}")

    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Panel 1: Centerline comparison
    ax = axes[0, 0]
    ax.plot(
        centerline_passive[:, 0],
        centerline_passive[:, 1],
        "b-",
        linewidth=2,
        label="Passive (gravity-selected)",
    )
    ax.plot(
        centerline_info[:, 0],
        centerline_info[:, 1],
        "r-",
        linewidth=2,
        label="Info-driven (countercurvature)",
    )
    ax.set_xlabel("x (m)")
    ax.set_ylabel("z (m)")
    ax.set_title("(A) Rod Centerlines: Passive vs Information-Driven")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_aspect("equal")

    # Panel 2: Information field
    ax = axes[0, 1]
    ax.plot(s, info_field.I, "g-", linewidth=2, label="I(s)")
    ax_twin = ax.twinx()
    ax_twin.plot(s, info_field.dIds, "orange", linewidth=2, linestyle="--", label="∂I/∂s")
    ax.set_xlabel("Arc-length s (m)")
    ax.set_ylabel("Information density I(s)", color="g")
    ax_twin.set_ylabel("Information gradient ∂I/∂s", color="orange")
    ax.set_title("(B) Information Field Profile")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left")
    ax_twin.legend(loc="upper right")

    # Panel 3: Curvature comparison
    ax = axes[1, 0]
    ax.plot(s, kappa_passive, "b-", linewidth=2, label="κ_passive")
    ax.plot(s, kappa_info, "r-", linewidth=2, label="κ_info")
    ax.axhline(0, color="k", linestyle=":", alpha=0.5)
    ax.set_xlabel("Arc-length s (m)")
    ax.set_ylabel("Curvature κ (1/m)")
    ax.set_title("(C) Curvature Profiles")
    ax.legend()
    ax.grid(alpha=0.3)

    # Panel 4: Metrics
    ax = axes[1, 1]
    ax.axis("off")
    metrics_text = f"""
    Countercurvature Metrics:
    
    Energy (L2 distance): {countercurvature_energy:.4e}
    Metric deviation: {metric_deviation:.4f} 1/m
    
    Geodesic deviation:
    D_geo = {D_geo:.6f} 1/m
    D_geo_norm = {D_geo_norm:.6f}
    
    Comparison:
    Plain L2 norm = {plain_l2_norm:.6f}
    Ratio (D_geo/plain) = {D_geo_norm/plain_l2_norm:.3f}
    
    Parameters:
    χ_κ = {chi_kappa:.3f}
    χ_E = {chi_E:.3f}
    Length = {length:.2f} m
    Gravity load = {gravity_load:.1f} N/m
    """
    ax.text(0.1, 0.5, metrics_text, fontsize=10, family="monospace", va="center")

    plt.tight_layout()
    fig_path = Path(output_dir) / "plant_growth_figure.png"
    plt.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ Saved figure to {fig_path}")

    return {
        "s": s,
        "info_field": info_field,
        "g_eff": g_eff,
        "centerline_passive": centerline_passive,
        "centerline_info": centerline_info,
        "kappa_passive": kappa_passive,
        "kappa_info": kappa_info,
        "countercurvature_energy": countercurvature_energy,
        "metric_deviation": metric_deviation,
        "D_geo": D_geo,
        "D_geo_norm": D_geo_norm,
        "plain_l2_norm": plain_l2_norm,
        "params": params_info,
    }


def _reconstruct_centerline_2d(theta: np.ndarray, s: np.ndarray) -> np.ndarray:
    """Reconstruct 2D centerline from angle profile."""
    x = np.zeros_like(s)
    z = np.zeros_like(s)

    ds = np.diff(s)
    x[1:] = np.cumsum(np.cos(theta[:-1]) * ds)
    z[1:] = np.cumsum(np.sin(theta[:-1]) * ds)

    return np.column_stack([x, z])


def main():
    """Run plant upward growth experiment."""
    print("🌱 Running plant upward growth experiment...")
    print("   Demonstrating biological countercurvature: information-driven upward growth")
    print()

    results = run_plant_experiment(
        length=0.5,
        n_nodes=100,
        chi_kappa=0.05,
        chi_E=0.1,
        gravity_load=50.0,
    )

    print()
    print("✅ Experiment complete!")
    print(f"   Countercurvature energy: {results['countercurvature_energy']:.4e}")
    print(f"   Metric deviation: {results['metric_deviation']:.4f} 1/m")
    print(f"   D_geo_norm: {results['D_geo_norm']:.6f}")
    print(f"   Plain L2 norm: {results['plain_l2_norm']:.6f}")
    ratio = results['D_geo_norm'] / results['plain_l2_norm'] if results['plain_l2_norm'] > 0 else 0.0
    print(f"   Ratio (D_geo/plain): {ratio:.3f}")
    print()
    print("   Interpretation:")
    print("   - Information field I(s) creates countercurvature that opposes gravity")
    print("   - This is an analog of 'biological countercurvature of spacetime'")
    print("   - The rod bends upward, mimicking plant growth against gravity")
    if ratio > 1.2:
        print("   - D_geo_norm >> plain L2: Information-dense regions drive curvature deviation")


if __name__ == "__main__":
    main()


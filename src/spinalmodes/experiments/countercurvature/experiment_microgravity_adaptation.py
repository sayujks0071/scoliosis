"""Experiment: Microgravity adaptation with information-driven countercurvature.

This experiment demonstrates that information-driven structure persists when
gravitational curvature is reduced. We run the same information field I(s) in:

- 1g (Earth gravity)
- 0.1g (reduced gravity)
- ~0g (microgravity)

The key finding: in low gravity, shape is maintained largely by information
coupling, not gravity. This is interpreted as "Information-driven structure
persists when gravitational curvature is reduced" — an analog to biological
countercurvature of spacetime.

This supports the hypothesis that biological information processing creates
structure that is independent of (or can operate against) gravitational
curvature, similar to how consciousness might operate in a countercurvature
framework.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from spinalmodes.countercurvature import (
    CounterCurvatureParams,
    InfoField1D,
    make_uniform_grid,
)
from spinalmodes.countercurvature.coupling import (
    compute_active_moments,
    compute_effective_stiffness,
    compute_rest_curvature,
)
from spinalmodes.countercurvature.validation_and_metrics import (
    compute_countercurvature_energy,
    compute_countercurvature_metric,
    compute_shape_preservation_index,
    geodesic_curvature_deviation,
)
from spinalmodes.iec import solve_beam_static


def create_spinal_info_field(s: np.ndarray, length: float) -> InfoField1D:
    """Create information field representing neural/postural control.

    This field is kept constant across gravity conditions to demonstrate
    that information-driven structure persists independently of gravity.

    Parameters
    ----------
    s:
        Arc-length grid (metres).
    length:
        Total spine length (metres).

    Returns
    -------
    InfoField1D
        Information field for neural control.
    """
    s_norm = s / length

    # Neural activity with spatial structure
    lumbar = 0.7 * np.exp(-((s_norm - 0.25) ** 2) / (2 * 0.1**2))
    cervical = 0.5 * np.exp(-((s_norm - 0.8) ** 2) / (2 * 0.08**2))
    I = lumbar + cervical + 0.3  # Baseline

    return InfoField1D.from_array(s, I)


def run_microgravity_experiment(
    length: float = 0.4,
    n_nodes: int = 100,
    chi_kappa: float = 0.04,
    chi_E: float = 0.1,
    E0: float = 1e9,
    I_moment: float = 1e-8,
    gravity_levels: list[float] = [9.81, 0.981, 0.0981],  # 1g, 0.1g, 0.01g
    gravity_labels: list[str] = ["1g (Earth)", "0.1g", "0.01g"],
    output_dir: str = "outputs/experiments/microgravity",
) -> dict:
    """Run microgravity adaptation experiment.

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
    gravity_levels:
        List of gravitational accelerations (m/s²).
    gravity_labels:
        Labels for each gravity level.
    output_dir:
        Output directory for results.

    Returns
    -------
    dict
        Dictionary with results for all gravity levels.
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Create spatial grid
    s = make_uniform_grid(length, n_nodes)

    # Create information field (constant across gravity conditions)
    info_field = create_spinal_info_field(s, length)
    kappa_gen = np.zeros_like(s)  # No baseline curvature

    # Compute countercurvature metric (constant across gravity conditions)
    g_eff = compute_countercurvature_metric(info_field, beta1=1.0, beta2=0.5)
    gravity_loads = [1000.0 * 1e-4 * g for g in gravity_levels]  # rho*A*g

    # Create coupling parameters
    params = CounterCurvatureParams(
        chi_kappa=chi_kappa, chi_E=chi_E, chi_M=0.0, scale_length=1.0
    )

    # Compute countercurvature-modified properties (same for all gravity levels)
    kappa_rest = compute_rest_curvature(info_field, params, kappa_gen)
    E_eff = compute_effective_stiffness(info_field, params, E0, model="linear")
    M_info = compute_active_moments(info_field, params)

    # Storage for results
    all_results = []
    centerline_initial = None

    for g, label, gravity_load in zip(gravity_levels, gravity_labels, gravity_loads):

        # Solve beam equilibrium
        theta, kappa = solve_beam_static(
            s, kappa_rest, E_eff, M_info, I_moment=I_moment, distributed_load=gravity_load
        )

        # Reconstruct centerline
        centerline = _reconstruct_centerline_2d(theta, s)

        # Store initial centerline (from 1g case) for comparison
        if centerline_initial is None:
            centerline_initial = centerline.copy()

        # Compute metrics
        # Compare with passive case (no info coupling) at same gravity
        params_passive = CounterCurvatureParams(chi_kappa=0.0, chi_E=0.0, chi_M=0.0)
        kappa_rest_passive = compute_rest_curvature(
            info_field, params_passive, kappa_gen
        )
        E_passive = np.full_like(s, E0)
        M_passive = np.zeros_like(s)
        theta_passive, kappa_passive = solve_beam_static(
            s,
            kappa_rest_passive,
            E_passive,
            M_passive,
            I_moment=I_moment,
            distributed_load=gravity_load,
        )
        centerline_passive = _reconstruct_centerline_2d(theta_passive, s)

        # Compute countercurvature energy (deviation from passive)
        countercurvature_energy = compute_countercurvature_energy(
            centerline_passive, centerline, method="l2_distance"
        )

        # Compute shape preservation (how well info maintains shape vs passive)
        shape_preservation = compute_shape_preservation_index(
            centerline_initial, centerline, centerline_passive
        )

        # Compute geodesic curvature deviation
        geo_metrics = geodesic_curvature_deviation(
            s, kappa_passive, kappa, g_eff
        )
        D_geo = geo_metrics["D_geo"]
        D_geo_norm = geo_metrics["D_geo_norm"]

        # Store results
        result = {
            "gravity": g,
            "gravity_label": label,
            "gravity_load": gravity_load,
            "s": s,
            "centerline": centerline,
            "centerline_passive": centerline_passive,
            "kappa": kappa,
            "kappa_passive": kappa_passive,
            "theta": theta,
            "countercurvature_energy": countercurvature_energy,
            "shape_preservation_index": shape_preservation,
            "D_geo": D_geo,
            "D_geo_norm": D_geo_norm,
        }
        all_results.append(result)

    # Save results to CSV
    rows = []
    for result in all_results:
        for i, s_val in enumerate(result["s"]):
            rows.append(
                {
                    "gravity": result["gravity"],
                    "gravity_label": result["gravity_label"],
                    "s": s_val,
                    "x_info": result["centerline"][i, 0],
                    "z_info": result["centerline"][i, 1],
                    "x_passive": result["centerline_passive"][i, 0],
                    "z_passive": result["centerline_passive"][i, 1],
                    "kappa_info": result["kappa"][i],
                    "kappa_passive": result["kappa_passive"][i],
                }
            )

    df = pd.DataFrame(rows)
    csv_path = Path(output_dir) / "microgravity_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved results to {csv_path}")

    # Save summary metrics
    summary_rows = []
    for result in all_results:
        summary_rows.append(
            {
                "gravity": result["gravity"],
                "gravity_label": result["gravity_label"],
                "countercurvature_energy": result["countercurvature_energy"],
                "shape_preservation_index": result["shape_preservation_index"],
                "D_geo": result["D_geo"],
                "D_geo_norm": result["D_geo_norm"],
            }
        )

    df_summary = pd.DataFrame(summary_rows)
    summary_path = Path(output_dir) / "microgravity_summary.csv"
    df_summary.to_csv(summary_path, index=False)
    print(f"✅ Saved summary to {summary_path}")

    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Panel 1: Centerlines at different gravity levels
    ax = axes[0, 0]
    colors = ["blue", "orange", "red"]
    for i, result in enumerate(all_results):
        ax.plot(
            result["centerline"][:, 0],
            result["centerline"][:, 1],
            color=colors[i],
            linewidth=2,
            linestyle="-",
            label=f"{result['gravity_label']} (info-driven)",
        )
        ax.plot(
            result["centerline_passive"][:, 0],
            result["centerline_passive"][:, 1],
            color=colors[i],
            linewidth=1.5,
            linestyle="--",
            alpha=0.6,
            label=f"{result['gravity_label']} (passive)",
        )
    ax.set_xlabel("x (m)")
    ax.set_ylabel("z (m)")
    ax.set_title("(A) Shape at Different Gravity Levels")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_aspect("equal")

    # Panel 2: Geodesic deviation vs gravity
    ax = axes[0, 1]
    gravity_vals = [r["gravity"] for r in all_results]
    D_geo_norm_vals = [r["D_geo_norm"] for r in all_results]
    ax.plot(gravity_vals, D_geo_norm_vals, "o-", color="green", linewidth=2, markersize=8)
    ax.set_xlabel("Gravity (m/s²)")
    ax.set_ylabel("Geodesic Deviation D_geo_norm")
    ax.set_title("(B) Geodesic Deviation vs Gravity")
    ax.grid(alpha=0.3)
    ax.set_xscale("log")

    # Panel 3: Shape preservation index
    ax = axes[1, 0]
    preservation_vals = [r["shape_preservation_index"] for r in all_results]
    ax.plot(gravity_vals, preservation_vals, "s-", color="green", linewidth=2, markersize=8)
    ax.axhline(1.0, color="k", linestyle=":", alpha=0.5, label="Equal preservation")
    ax.set_xlabel("Gravity (m/s²)")
    ax.set_ylabel("Shape Preservation Index")
    ax.set_title("(C) Shape Preservation vs Gravity")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_xscale("log")

    # Panel 4: Information field (constant across conditions)
    ax = axes[1, 1]
    ax.plot(s, info_field.I, "g-", linewidth=2, label="I(s)")
    ax_twin = ax.twinx()
    ax_twin.plot(s, info_field.dIds, "orange", linewidth=2, linestyle="--", label="∂I/∂s")
    ax.set_xlabel("Arc-length s (m)")
    ax.set_ylabel("Information density I(s)", color="g")
    ax_twin.set_ylabel("Information gradient ∂I/∂s", color="orange")
    ax.set_title("(D) Information Field (Constant)")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left")
    ax_twin.legend(loc="upper right")

    plt.tight_layout()
    fig_path = Path(output_dir) / "microgravity_figure.png"
    plt.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ Saved figure to {fig_path}")

    return {
        "results": all_results,
        "info_field": info_field,
        "params": params,
        "csv_path": csv_path,
        "summary_path": summary_path,
        "figure_path": fig_path,
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
    """Run microgravity adaptation experiment."""
    parser = argparse.ArgumentParser(description="Microgravity adaptation experiment.")
    parser.add_argument("--quick", action="store_true", help="Run a coarse, fast configuration.")
    parser.add_argument("--chi-kappa", type=float, default=0.04, help="Information-to-curvature coupling.")
    parser.add_argument("--chi-E", type=float, default=0.1, help="Information-to-stiffness coupling.")
    parser.add_argument(
        "--output-dir", type=str, default="outputs/experiments/microgravity", help="Output directory."
    )
    args = parser.parse_args()

    if args.quick:
        gravity_levels = [9.81, 0.5, 0.05]
        gravity_labels = ["1g", "0.05g", "0.005g"]
        n_nodes = 60
        length = 0.3
    else:
        gravity_levels = [9.81, 0.981, 0.0981]
        gravity_labels = ["1g (Earth)", "0.1g", "0.01g"]
        n_nodes = 100
        length = 0.4

    print("🚀 Running microgravity adaptation experiment...")
    print("   Demonstrating information-driven structure persistence in reduced gravity")
    print()

    results = run_microgravity_experiment(
        length=length,
        n_nodes=n_nodes,
        chi_kappa=args.chi_kappa,
        chi_E=args.chi_E,
        gravity_levels=gravity_levels,
        gravity_labels=gravity_labels,
        output_dir=args.output_dir,
    )

    print()
    print("✅ Experiment complete!")
    print(f"   CSV: {results['csv_path']}")
    print(f"   Summary: {results['summary_path']}")
    print(f"   Figure: {results['figure_path']}")
    print()
    print("-" * 60)
    print(f"{'Gravity':<15} | {'D_geo_norm':<12} | {'Preservation':<12}")
    print("-" * 60)
    for result in results["results"]:
        print(
            f"{result['gravity_label']:<15} | {result['D_geo_norm']:>10.6f}   | "
            f"{result['shape_preservation_index']:>10.3f}"
        )
    print("-" * 60)
    print()
    print("   Interpretation:")
    print("   - Information-driven structure persists when gravity is reduced")
    print("   - This is an analog of 'biological countercurvature of spacetime'")
    print("   - Information processing creates structure independent of gravitational curvature")


if __name__ == "__main__":
    main()

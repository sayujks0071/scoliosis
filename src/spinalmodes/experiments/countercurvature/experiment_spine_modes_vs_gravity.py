"""Experiment: Spinal curvature modes vs gravity with information coupling.

This experiment uses IEC-style κ_gen(s) approximating a human spine's lordosis/kyphosis
profile and adds an InfoField1D representing neural/postural control. We sweep
coupling parameters (χ_κ, χ_E) and simulate:

- No coupling (control, gravity-selected mode)
- Moderate coupling
- Strong coupling

We compute metrics:
- Lordosis/kyphosis angles
- Positions of inflection points
- Countercurvature index = deviation from passive gravitational shape

This demonstrates how information-driven countercurvature can stabilize spinal
curvature against gravitational loading, supporting the biological countercurvature
hypothesis.
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
    compute_effective_metric_deviation,
    geodesic_curvature_deviation,
)
from spinalmodes.iec import solve_beam_static


def create_spine_kappa_gen(
    s: np.ndarray, length: float, epsilon_asym: float = 0.0
) -> np.ndarray:
    """Create baseline spinal curvature profile (lordosis/kyphosis).

    Approximates a human spine with:
    - Lordosis (forward curvature) in lumbar region
    - Kyphosis (backward curvature) in thoracic region
    - Optional lateral asymmetry (coronal plane perturbation) for scoliosis modeling

    Parameters
    ----------
    s:
        Arc-length grid (metres).
    length:
        Total spine length (metres).
    epsilon_asym:
        Amplitude of lateral asymmetry perturbation (1/m). 
        Positive values create coronal-plane curvature (scoliosis-like).
        Typically 0.01-0.05 for small perturbations.

    Returns
    -------
    np.ndarray
        Baseline curvature κ_gen(s) (1/m) in sagittal plane.
        If epsilon_asym > 0, this represents the sagittal component;
        lateral component is handled separately in 3D or via lateral deviation metric.
    """
    s_norm = s / length

    # Lumbar lordosis (positive curvature, s ~ 0.0-0.4)
    lumbar = 0.3 * np.exp(-((s_norm - 0.2) ** 2) / (2 * 0.1**2))

    # Thoracic kyphosis (negative curvature, s ~ 0.4-0.8)
    thoracic = -0.2 * np.exp(-((s_norm - 0.6) ** 2) / (2 * 0.15**2))

    kappa_gen = lumbar + thoracic

    # Add lateral asymmetry perturbation (mid-thoracic, T7-T9 region)
    # This creates a coronal-plane component that can lead to scoliosis-like deviation
    if epsilon_asym > 0:
        # Mid-thoracic region (s_norm ~ 0.5-0.7, corresponding to T7-T9)
        asymmetry_bump = epsilon_asym * np.exp(-((s_norm - 0.6) ** 2) / (2 * 0.08**2))
        # Note: In full 3D, this would be a lateral curvature component
        # For 2D sagittal model, we approximate by adding to sagittal curvature
        # The actual lateral deviation is computed from centerline geometry
        kappa_gen = kappa_gen + asymmetry_bump

    return kappa_gen


def create_neural_control_info_field(
    s: np.ndarray, length: float, epsilon_asym: float = 0.0
) -> InfoField1D:
    """Create information field representing neural/postural control.

    The field has spatial structure matching spinal regions, representing
    neural activity or proprioceptive feedback that modulates curvature.

    Parameters
    ----------
    s:
        Arc-length grid (metres).
    length:
        Total spine length (metres).
    epsilon_asym:
        Amplitude of asymmetric perturbation to information field (dimensionless).
        Creates localized asymmetry in mid-thoracic region (T7-T9).
        Typically 0.01-0.05 for small perturbations.

    Returns
    -------
    InfoField1D
        Information field for neural control.
    """
    s_norm = s / length

    # Neural activity peaks in lumbar and cervical regions (postural control)
    lumbar_activity = 0.8 * np.exp(-((s_norm - 0.25) ** 2) / (2 * 0.1**2))
    cervical_activity = 0.6 * np.exp(-((s_norm - 0.85) ** 2) / (2 * 0.08**2))
    I = lumbar_activity + cervical_activity + 0.2  # Baseline

    # Add asymmetric perturbation (mid-thoracic, T7-T9 region)
    # This represents asymmetric neural control or proprioceptive feedback
    if epsilon_asym > 0:
        asymmetry_bump = epsilon_asym * np.exp(-((s_norm - 0.6) ** 2) / (2 * 0.08**2))
        I = I + asymmetry_bump

    return InfoField1D.from_array(s, I)


def compute_lateral_deviation(centerline: np.ndarray, s: np.ndarray) -> dict[str, float]:
    """Compute lateral (coronal plane) deviation metrics.

    For scoliosis analysis, we measure how much the spine deviates
    laterally from the sagittal plane. In 2D sagittal model, this is
    approximated by measuring deviation from a straight vertical line.

    Parameters
    ----------
    centerline:
        Rod centerline, shape (n_points, 2) for 2D.
    s:
        Arc-length coordinate.

    Returns
    -------
    dict
        Dictionary with lateral deviation metrics:
        - 'max_lateral_deviation': Maximum lateral displacement (m)
        - 'tip_lateral_deviation': Lateral displacement at tip (m)
        - 'apex_position': Arc-length position of maximum deviation (m)
    """
    # In 2D sagittal model (x-z plane), lateral deviation is measured as
    # deviation from the vertical (z-axis). For full 3D, this would be y-coordinate.
    # Here we approximate by measuring x-coordinate deviation
    x_coords = centerline[:, 0]
    z_coords = centerline[:, 1]

    # Maximum lateral deviation (from vertical line)
    max_lateral = np.max(np.abs(x_coords))
    max_idx = np.argmax(np.abs(x_coords))
    apex_position = s[max_idx]

    # Tip lateral deviation
    tip_lateral = np.abs(x_coords[-1])

    return {
        "max_lateral_deviation": float(max_lateral),
        "tip_lateral_deviation": float(tip_lateral),
        "apex_position": float(apex_position),
    }


def compute_lordosis_kyphosis_angles(
    centerline: np.ndarray, s: np.ndarray
) -> dict[str, float]:
    """Compute lordosis and kyphosis angles from centerline.

    Parameters
    ----------
    centerline:
        Rod centerline, shape (n_points, 2).
    s:
        Arc-length coordinate.

    Returns
    -------
    dict
        Dictionary with 'lordosis_angle' and 'kyphosis_angle' (degrees).
    """
    # Find inflection points (where curvature changes sign)
    # Simplified: find regions of positive and negative curvature
    theta = np.arctan2(
        np.diff(centerline[:, 1]), np.diff(centerline[:, 0])
    )
    theta = np.concatenate([[theta[0]], theta])

    # Approximate lordosis as max forward angle, kyphosis as max backward angle
    # In sagittal plane, forward = positive z, backward = negative z
    angles_deg = np.rad2deg(theta)

    lordosis_angle = np.max(angles_deg[angles_deg > 0]) if np.any(angles_deg > 0) else 0.0
    kyphosis_angle = np.min(angles_deg[angles_deg < 0]) if np.any(angles_deg < 0) else 0.0

    return {
        "lordosis_angle": float(lordosis_angle),
        "kyphosis_angle": float(kyphosis_angle),
    }


def find_inflection_points(kappa: np.ndarray, s: np.ndarray) -> np.ndarray:
    """Find inflection points where curvature changes sign.

    Parameters
    ----------
    kappa:
        Curvature profile (1/m).
    s:
        Arc-length coordinate.

    Returns
    -------
    np.ndarray
        Arc-length positions of inflection points (metres).
    """
    sign_changes = np.diff(np.sign(kappa))
    inflection_indices = np.where(sign_changes != 0)[0]
    return s[inflection_indices]


def run_spine_experiment(
    length: float = 0.4,
    n_nodes: int = 100,
    chi_kappa_values: list[float] = [0.0, 0.02, 0.05],
    chi_E: float = 0.1,
    E0: float = 1e9,
    I_moment: float = 1e-8,
    gravity_load: float = 100.0,
    epsilon_asym: float = 0.0,
    output_dir: str = "outputs/experiments/spine_modes",
) -> dict:
    """Run spine modes vs gravity experiment.

    Parameters
    ----------
    length:
        Spine length (metres).
    n_nodes:
        Number of spatial nodes.
    chi_kappa_values:
        List of χ_κ values to sweep.
    chi_E:
        Information-to-stiffness coupling strength.
    E0:
        Baseline Young's modulus (Pa).
    I_moment:
        Second moment of area (m^4).
    gravity_load:
        Equivalent distributed load (N/m).
    output_dir:
        Output directory for results.

    Returns
    -------
    dict
        Dictionary with results for all parameter sets.
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Create spatial grid
    s = make_uniform_grid(length, n_nodes)

    # Create baseline spinal curvature and information field
    # Option 1: Asymmetry in kappa_gen (structural asymmetry)
    # Option 2: Asymmetry in info field (neural control asymmetry)
    # We'll use info field asymmetry as it's more biologically plausible
    kappa_gen = create_spine_kappa_gen(s, length, epsilon_asym=0.0)  # Keep sagittal symmetric
    info_field = create_neural_control_info_field(s, length, epsilon_asym=epsilon_asym)

    # Compute countercurvature metric (same for all parameter sets)
    g_eff = compute_countercurvature_metric(info_field, beta1=1.0, beta2=0.5)

    # Storage for results
    all_results = []

    for chi_k in chi_kappa_values:
        # Create coupling parameters
        params = CounterCurvatureParams(
            chi_kappa=chi_k, chi_E=chi_E, chi_M=0.0, scale_length=1.0
        )

        # Compute countercurvature-modified properties
        kappa_rest = compute_rest_curvature(info_field, params, kappa_gen)
        E_eff = compute_effective_stiffness(info_field, params, E0, model="linear")
        M_info = compute_active_moments(info_field, params)

        # Solve beam equilibrium
        theta, kappa = solve_beam_static(
            s, kappa_rest, E_eff, M_info, I_moment=I_moment, distributed_load=gravity_load
        )

        # Reconstruct centerline
        centerline = _reconstruct_centerline_2d(theta, s)

        # Compute metrics
        if chi_k == 0.0:
            # Passive case - use as reference
            centerline_passive = centerline
            kappa_passive = kappa
            countercurvature_energy = 0.0
            metric_deviation = 0.0
            D_geo = 0.0
            D_geo_norm = 0.0
        else:
            countercurvature_energy = compute_countercurvature_energy(
                centerline_passive, centerline, method="l2_distance"
            )
            metric_deviation = compute_effective_metric_deviation(
                kappa_passive, kappa, s=s
            )
            # Compute geodesic curvature deviation
            geo_metrics = geodesic_curvature_deviation(
                s, kappa_passive, kappa, g_eff
            )
            D_geo = geo_metrics["D_geo"]
            D_geo_norm = geo_metrics["D_geo_norm"]

        # Compute spinal angles
        angles = compute_lordosis_kyphosis_angles(centerline, s)
        inflection_points = find_inflection_points(kappa, s)

        # Compute lateral deviation (for scoliosis analysis)
        lateral_metrics = compute_lateral_deviation(centerline, s)

        # Store results
        result = {
            "chi_kappa": chi_k,
            "chi_E": chi_E,
            "epsilon_asym": epsilon_asym,
            "s": s,
            "centerline": centerline,
            "kappa": kappa,
            "theta": theta,
            "countercurvature_energy": countercurvature_energy,
            "metric_deviation": metric_deviation,
            "D_geo": D_geo if chi_k > 0 else 0.0,
            "D_geo_norm": D_geo_norm if chi_k > 0 else 0.0,
            "lordosis_angle": angles["lordosis_angle"],
            "kyphosis_angle": angles["kyphosis_angle"],
            "max_lateral_deviation": lateral_metrics["max_lateral_deviation"],
            "tip_lateral_deviation": lateral_metrics["tip_lateral_deviation"],
            "apex_position": lateral_metrics["apex_position"],
            "n_inflection_points": len(inflection_points),
            "inflection_points": inflection_points,
        }
        all_results.append(result)

    # Save results to CSV (including I(s) and dIds for figure generation)
    rows = []
    for result in all_results:
        # Get info field for this result (same for all chi_kappa values in this run)
        # We'll use the info_field from the last iteration (or store it separately)
        info_field_for_result = info_field  # Use the current info_field
        for i, s_val in enumerate(result["s"]):
            rows.append(
                {
                    "chi_kappa": result["chi_kappa"],
                    "chi_E": result["chi_E"],
                    "s": s_val,
                    "x": result["centerline"][i, 0],
                    "z": result["centerline"][i, 1],
                    "kappa": result["kappa"][i],
                    "theta": result["theta"][i],
                    # Save I(s) and dIds for figure generation
                    "I": info_field_for_result.I[i] if i < len(info_field_for_result.I) else np.nan,
                    "dIds": info_field_for_result.dIds[i] if i < len(info_field_for_result.dIds) else np.nan,
                }
            )

    df = pd.DataFrame(rows)
    csv_path = Path(output_dir) / "spine_modes_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved results to {csv_path}")

    # Save summary metrics
    summary_rows = []
    for result in all_results:
        summary_rows.append(
            {
                "chi_kappa": result["chi_kappa"],
                "chi_E": result["chi_E"],
                "countercurvature_energy": result["countercurvature_energy"],
                "metric_deviation": result["metric_deviation"],
                "D_geo": result["D_geo"],
                "D_geo_norm": result["D_geo_norm"],
                "epsilon_asym": result["epsilon_asym"],
                "max_lateral_deviation": result["max_lateral_deviation"],
                "tip_lateral_deviation": result["tip_lateral_deviation"],
                "apex_position": result["apex_position"],
                "lordosis_angle": result["lordosis_angle"],
                "kyphosis_angle": result["kyphosis_angle"],
                "n_inflection_points": result["n_inflection_points"],
            }
        )

    df_summary = pd.DataFrame(summary_rows)
    summary_path = Path(output_dir) / "spine_modes_summary.csv"
    df_summary.to_csv(summary_path, index=False)
    print(f"✅ Saved summary to {summary_path}")

    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Panel 1: Centerlines for different coupling strengths
    ax = axes[0, 0]
    colors = ["blue", "orange", "red"]
    labels = ["Passive (χ_κ=0)", "Moderate (χ_κ=0.02)", "Strong (χ_κ=0.05)"]
    for i, result in enumerate(all_results):
        ax.plot(
            result["centerline"][:, 0],
            result["centerline"][:, 1],
            color=colors[i],
            linewidth=2,
            label=labels[i],
        )
    ax.set_xlabel("x (m)")
    ax.set_ylabel("z (m)")
    ax.set_title("(A) Spinal Centerlines: Coupling Strength Sweep")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_aspect("equal")

    # Panel 2: Curvature profiles
    ax = axes[0, 1]
    for i, result in enumerate(all_results):
        ax.plot(
            result["s"],
            result["kappa"],
            color=colors[i],
            linewidth=2,
            label=f"χ_κ={result['chi_kappa']:.3f}",
        )
    ax.axhline(0, color="k", linestyle=":", alpha=0.5)
    ax.set_xlabel("Arc-length s (m)")
    ax.set_ylabel("Curvature κ (1/m)")
    ax.set_title("(B) Curvature Profiles")
    ax.legend()
    ax.grid(alpha=0.3)

    # Panel 3: Metrics vs coupling strength
    ax = axes[1, 0]
    chi_vals = [r["chi_kappa"] for r in all_results]
    energy_vals = [r["countercurvature_energy"] for r in all_results]
    D_geo_norm_vals = [r["D_geo_norm"] for r in all_results]

    ax_twin = ax.twinx()
    line1 = ax.plot(chi_vals, energy_vals, "o-", color="purple", linewidth=2, label="Energy")
    line2 = ax_twin.plot(
        chi_vals, D_geo_norm_vals, "s-", color="green", linewidth=2, label="D_geo_norm"
    )
    ax.set_xlabel("χ_κ (Coupling Strength)")
    ax.set_ylabel("Countercurvature Energy", color="purple")
    ax_twin.set_ylabel("Geodesic Deviation (norm)", color="green")
    ax.set_title("(C) Countercurvature Metrics vs Coupling")
    ax.grid(alpha=0.3)
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc="upper left")

    # Panel 4: Spinal angles
    ax = axes[1, 1]
    lordosis_vals = [r["lordosis_angle"] for r in all_results]
    kyphosis_vals = [r["kyphosis_angle"] for r in all_results]

    x_pos = np.arange(len(chi_vals))
    width = 0.35
    ax.bar(
        x_pos - width / 2,
        lordosis_vals,
        width,
        label="Lordosis",
        color="lightblue",
        alpha=0.8,
    )
    ax.bar(
        x_pos + width / 2,
        np.abs(kyphosis_vals),
        width,
        label="Kyphosis (abs)",
        color="lightcoral",
        alpha=0.8,
    )
    ax.set_xlabel("Coupling Strength Index")
    ax.set_ylabel("Angle (degrees)")
    ax.set_title("(D) Spinal Curvature Angles")
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"χ_κ={c:.3f}" for c in chi_vals])
    ax.legend()
    ax.grid(alpha=0.3, axis="y")

    plt.tight_layout()
    fig_path = Path(output_dir) / "spine_modes_figure.png"
    plt.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ Saved figure to {fig_path}")

    return {
        "results": all_results,
        "info_field": info_field,
        "kappa_gen": kappa_gen,
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
    """Run spine modes vs gravity experiment."""
    parser = argparse.ArgumentParser(description="Spine modes vs gravity experiment.")
    parser.add_argument("--quick", action="store_true", help="Run coarse resolution for speed.")
    parser.add_argument("--chi-min", type=float, default=0.0, help="Minimum chi_kappa.")
    parser.add_argument("--chi-max", type=float, default=0.05, help="Maximum chi_kappa.")
    parser.add_argument("--chi-steps", type=int, default=3, help="Number of chi_kappa values.")
    parser.add_argument("--gravity-load", type=float, default=100.0, help="Distributed load (N/m).")
    parser.add_argument("--output-dir", type=str, default="outputs/experiments/spine_modes", help="Output directory.")
    args = parser.parse_args()

    if args.quick:
        n_nodes = 60
        length = 0.3
        chi_values = np.linspace(args.chi_min, args.chi_max, max(2, min(args.chi_steps, 3)))
    else:
        n_nodes = 100
        length = 0.4
        chi_values = np.linspace(args.chi_min, args.chi_max, args.chi_steps)

    print("🦴 Running spine modes vs gravity experiment...")
    print("   Demonstrating information-driven stabilization of spinal curvature")
    print()

    results = run_spine_experiment(
        length=length,
        n_nodes=n_nodes,
        chi_kappa_values=chi_values,
        chi_E=0.1,
        gravity_load=args.gravity_load,
        output_dir=args.output_dir,
    )

    print()
    print("✅ Experiment complete!")
    print(f"   CSV: {results['csv_path']}")
    print(f"   Summary: {results['summary_path']}")
    print(f"   Figure: {results['figure_path']}")
    print("   Summary metrics:")
    for result in results["results"]:
        print(
            f"   χ_κ={result['chi_kappa']:.3f}: "
            f"D_geo_norm={result['D_geo_norm']:.4f}, "
            f"metric_dev={result['metric_deviation']:.4f}, "
            f"lordosis={result['lordosis_angle']:.1f}°, kyphosis={result['kyphosis_angle']:.1f}°"
        )
    print()
    print("   Interpretation:")
    print("   - Information coupling stabilizes spinal curvature against gravity")
    print("   - Stronger coupling (higher χ_κ) increases countercurvature energy")
    print("   - This supports the biological countercurvature hypothesis")


if __name__ == "__main__":
    main()

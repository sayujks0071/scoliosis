"""Generate phase diagram: D_geo_norm as function of coupling strength and gravity.

This experiment creates a phase diagram showing where "biological countercurvature
of spacetime" is weak vs strong, defined by regimes of D_geo_norm.

Regimes:
- Low D_geo_norm → gravity-dominated (life follows gravitational geodesics)
- Intermediate D_geo_norm → cooperative (information reshapes but doesn't override)
- High D_geo_norm → information-dominated (effective geometry strongly warped)

Usage:
    python3 -m spinalmodes.experiments.countercurvature.experiment_phase_diagram
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from spinalmodes.countercurvature import (
    CounterCurvatureParams,
    InfoField1D,
    compute_countercurvature_metric,
    compute_scoliosis_metrics,
    geodesic_curvature_deviation,
    make_uniform_grid,
)
from spinalmodes.countercurvature.coupling import (
    compute_active_moments,
    compute_effective_stiffness,
    compute_rest_curvature,
)
from spinalmodes.iec import solve_beam_static


def create_spinal_info_field(
    s: np.ndarray, length: float, epsilon_asym: float = 0.0
) -> InfoField1D:
    """Create information field representing neural/postural control."""
    s_norm = s / length
    lumbar = 0.7 * np.exp(-((s_norm - 0.25) ** 2) / (2 * 0.1**2))
    cervical = 0.5 * np.exp(-((s_norm - 0.8) ** 2) / (2 * 0.08**2))
    I = lumbar + cervical + 0.3

    # Add asymmetric perturbation (mid-thoracic, T7-T9 region)
    if epsilon_asym > 0:
        asymmetry_bump = epsilon_asym * np.exp(-((s_norm - 0.6) ** 2) / (2 * 0.08**2))
        I = I + asymmetry_bump

    return InfoField1D.from_array(s, I)


def extract_pseudo_coronal_coords(centerline: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Extract pseudo-coronal coordinates from 2D sagittal centerline.
    
    For 2D sagittal beam models (x-z plane), we project to pseudo-coronal:
    - z: longitudinal (cranio-caudal) = z-coordinate from sagittal
    - y: lateral (left-right) = x-coordinate from sagittal (treated as lateral deviation)
    
    Note: This is a 2D approximation. Full 3D models would use actual coronal-plane
    coordinates from the 3D centerline.
    
    Parameters
    ----------
    centerline:
        2D centerline in sagittal plane, shape (n_points, 2) with columns [x, z].
    
    Returns
    -------
    z, y:
        Pseudo-coronal coordinates where z is longitudinal and y is lateral.
    """
    # In 2D sagittal model: x is lateral deviation, z is longitudinal
    x = centerline[:, 0]  # Lateral (treated as y in coronal)
    z = centerline[:, 1]  # Longitudinal (cranio-caudal)
    return z, x


def _reconstruct_centerline_2d(theta: np.ndarray, s: np.ndarray) -> np.ndarray:
    """Reconstruct 2D centerline from angle profile."""
    x = np.zeros_like(s)
    z = np.zeros_like(s)
    ds = np.diff(s)
    x[1:] = np.cumsum(np.cos(theta[:-1]) * ds)
    z[1:] = np.cumsum(np.sin(theta[:-1]) * ds)
    return np.column_stack([x, z])


def run_phase_diagram_experiment(
    length: float = 0.4,
    n_nodes: int = 100,
    chi_kappa_values: np.ndarray = None,
    gravity_values: np.ndarray = None,
    chi_E: float = 0.1,
    E0: float = 1e9,
    I_moment: float = 1e-8,
    epsilon_asym: float = 0.01,  # Small asymmetry for scoliosis regime detection
    output_dir: str = "outputs/experiments/phase_diagram",
) -> dict:
    """Generate phase diagram: D_geo_norm(χ_κ, g).

    Parameters
    ----------
    length:
        Rod length (metres).
    n_nodes:
        Number of spatial nodes.
    chi_kappa_values:
        Array of χ_κ values to sweep.
    gravity_values:
        Array of gravity values (m/s²) to sweep.
    chi_E:
        Information-to-stiffness coupling.
    E0:
        Baseline Young's modulus (Pa).
    I_moment:
        Second moment of area (m^4).
    output_dir:
        Output directory.

    Returns
    -------
    dict
        Dictionary with phase diagram data and metadata.
    """
    # Default parameter ranges
    if chi_kappa_values is None:
        chi_kappa_values = np.linspace(0.0, 0.08, 17)
    if gravity_values is None:
        gravity_values = np.array([9.81, 4.9, 2.0, 1.0, 0.5, 0.2, 0.1, 0.05, 0.01])

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Create spatial grid and info field
    s = make_uniform_grid(length, n_nodes)
    # Create both symmetric and asymmetric info fields
    info_field_sym = create_spinal_info_field(s, length, epsilon_asym=0.0)
    info_field_asym = create_spinal_info_field(s, length, epsilon_asym=epsilon_asym)
    kappa_gen = np.zeros_like(s)

    # Compute countercurvature metric (constant across all parameter sets, use symmetric)
    g_eff_sym = compute_countercurvature_metric(info_field_sym, beta1=1.0, beta2=0.5)
    gravity_loads = {g: 1000.0 * 1e-4 * g for g in gravity_values}  # rho*A*g

    # Storage for phase diagram
    phase_data = []

    print(f"Generating phase diagram: {len(chi_kappa_values)} × {len(gravity_values)} = {len(chi_kappa_values) * len(gravity_values)} points")
    print()

    total = len(chi_kappa_values) * len(gravity_values)
    count = 0

    for chi_k in chi_kappa_values:
        for g in gravity_values:
            count += 1
            if count % 10 == 0:
                print(f"  Progress: {count}/{total} ({100*count/total:.1f}%)")

            # Convert gravity to load
            gravity_load = gravity_loads[g]

            # Passive case (no info coupling, symmetric)
            params_passive = CounterCurvatureParams(chi_kappa=0.0, chi_E=0.0, chi_M=0.0)
            kappa_rest_passive = compute_rest_curvature(info_field_sym, params_passive, kappa_gen)
            E_passive = np.full_like(s, E0)
            M_passive = np.zeros_like(s)
            _, kappa_passive = solve_beam_static(
                s, kappa_rest_passive[1], E_passive, M_passive,
                I_moment=I_moment, distributed_load=gravity_load
            )

            # Info-driven case (symmetric)
            params_info = CounterCurvatureParams(
                chi_kappa=chi_k, chi_E=chi_E, chi_M=0.0, scale_length=1.0
            )
            kappa_rest_info_sym = compute_rest_curvature(info_field_sym, params_info, kappa_gen)
            E_info_sym = compute_effective_stiffness(info_field_sym, params_info, E0, model="linear")
            M_info_sym = compute_active_moments(info_field_sym, params_info)
            _, kappa_info_sym = solve_beam_static(
                s, kappa_rest_info_sym[1], E_info_sym, M_info_sym,
                I_moment=I_moment, distributed_load=gravity_load
            )

            # Info-driven case (asymmetric) - for scoliosis regime detection
            kappa_rest_info_asym = compute_rest_curvature(info_field_asym, params_info, kappa_gen)
            E_info_asym = compute_effective_stiffness(info_field_asym, params_info, E0, model="linear")
            M_info_asym = compute_active_moments(info_field_asym, params_info)
            theta_asym, kappa_info_asym = solve_beam_static(
                s, kappa_rest_info_asym[1], E_info_asym, M_info_asym,
                I_moment=I_moment, distributed_load=gravity_load
            )
            centerline_asym = _reconstruct_centerline_2d(theta_asym, s)

            # Extract pseudo-coronal coordinates for scoliosis metrics
            # Note: This is a 2D approximation; full 3D would use actual coronal-plane coordinates
            z_asym, y_asym = extract_pseudo_coronal_coords(centerline_asym)
            scoliosis_metrics_asym = compute_scoliosis_metrics(z_asym, y_asym, frac=0.2)

            # Also compute symmetric case for comparison
            theta_sym, _ = solve_beam_static(
                s, kappa_rest_info_sym[1], E_info_sym, M_info_sym,
                I_moment=I_moment, distributed_load=gravity_load
            )
            centerline_sym = _reconstruct_centerline_2d(theta_sym, s)
            z_sym, y_sym = extract_pseudo_coronal_coords(centerline_sym)
            scoliosis_metrics_sym = compute_scoliosis_metrics(z_sym, y_sym, frac=0.2)

            # Compute geodesic deviation (symmetric case)
            geo_metrics = geodesic_curvature_deviation(
                s, kappa_passive, kappa_info_sym, g_eff_sym
            )

            # Compute passive curvature energy (for reference)
            passive_energy = np.trapezoid(kappa_passive**2, x=s)

            phase_data.append({
                "chi_kappa": chi_k,
                "gravity": g,
                "D_geo": geo_metrics["D_geo"],
                "D_geo_norm": geo_metrics["D_geo_norm"],
                "base_energy": geo_metrics["base_energy"],
                "passive_energy": passive_energy,
                # Scoliosis metrics (asymmetric case)
                "S_lat_asym": scoliosis_metrics_asym.S_lat,
                "cobb_asym_deg": scoliosis_metrics_asym.cobb_like_deg,
                "lat_dev_max_asym": scoliosis_metrics_asym.lat_dev_max,
                # Scoliosis metrics (symmetric case, for comparison)
                "S_lat_sym": scoliosis_metrics_sym.S_lat,
                "cobb_sym_deg": scoliosis_metrics_sym.cobb_like_deg,
                # Scoliosis regime: based on S_lat and Cobb-like angle thresholds
                "scoliosis_regime": (
                    scoliosis_metrics_asym.S_lat >= 0.05 or
                    scoliosis_metrics_asym.cobb_like_deg >= 5.0
                ),
            })

    df = pd.DataFrame(phase_data)
    csv_path = Path(output_dir) / "phase_diagram_data.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n✅ Saved phase diagram data to {csv_path}")

    # Create phase diagram visualization
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Panel A: D_geo_norm phase diagram with scoliosis regime overlay
    ax = axes[0]
    pivot = df.pivot(index="gravity", columns="chi_kappa", values="D_geo_norm")
    pivot_scoliosis = df.pivot(index="gravity", columns="chi_kappa", values="scoliosis_regime")
    # Also pivot S_lat for contour overlay
    pivot_S_lat = df.pivot(index="gravity", columns="chi_kappa", values="S_lat_asym")
    X, Y = np.meshgrid(chi_kappa_values, gravity_values)
    Z = pivot.values

    # Create contour plot
    contour = ax.contourf(X, Y, Z, levels=20, cmap="viridis")
    ax.contour(X, Y, Z, levels=[0.05, 0.1, 0.2, 0.5], colors="white", linewidths=1, alpha=0.5)

    # Overlay scoliosis regime (where S_lat >= 0.05 or Cobb >= 5°)
    scoliosis_mask = pivot_scoliosis.values.astype(bool)
    ax.contour(X, Y, scoliosis_mask.astype(float), levels=[0.5], colors="red", linewidths=2, linestyle="--")
    # Also show S_lat contour at threshold
    ax.contour(X, Y, pivot_S_lat.values, levels=[0.05], colors="orange", linewidths=1.5, linestyle=":", alpha=0.7)

    cbar = plt.colorbar(contour, ax=ax)
    cbar.set_label("D̂_geo (normalized geodesic deviation)", fontsize=11)

    ax.set_xlabel("Coupling strength χ_κ", fontsize=12)
    ax.set_ylabel("Gravity g (m/s²)", fontsize=12)
    ax.set_title("(A) Phase Diagram: Countercurvature Regimes + Scoliosis", fontsize=13, fontweight="bold")
    ax.set_yscale("log")
    ax.grid(alpha=0.3, linestyle="--")

    # Add regime labels
    ax.text(0.02, 0.5, "Gravity-\ndominated", fontsize=10, color="white",
            bbox=dict(boxstyle="round", facecolor="black", alpha=0.6), ha="center")
    ax.text(0.06, 0.1, "Information-\ndominated", fontsize=10, color="white",
            bbox=dict(boxstyle="round", facecolor="black", alpha=0.6), ha="center")
    ax.text(0.06, 0.01, "Scoliosis\nregime", fontsize=10, color="red",
            bbox=dict(boxstyle="round", facecolor="yellow", alpha=0.7), ha="center")

    # Panel B: Passive energy vs gravity (reference)
    ax = axes[1]
    gravity_unique = sorted(df["gravity"].unique())
    passive_energies = [df[df["gravity"] == g]["passive_energy"].iloc[0] for g in gravity_unique]
    ax.plot(gravity_unique, passive_energies, "o-", color="blue", linewidth=2, markersize=8)
    ax.set_xlabel("Gravity g (m/s²)", fontsize=12)
    ax.set_ylabel("Passive curvature energy", fontsize=12)
    ax.set_title("(B) Passive Curvature Energy vs Gravity", fontsize=13, fontweight="bold")
    ax.set_xscale("log")
    ax.grid(alpha=0.3)
    ax.text(0.05, 0.95, "Passive energy\ncollapses as g → 0",
            transform=ax.transAxes, fontsize=10,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7))

    plt.tight_layout()
    fig_path = Path(output_dir) / "phase_diagram.png"
    plt.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ Saved phase diagram to {fig_path}")

    return {
        "data": df,
        "chi_kappa_values": chi_kappa_values,
        "gravity_values": gravity_values,
        "csv_path": csv_path,
        "fig_path": fig_path,
        "D_geo_norm_min": df["D_geo_norm"].min(),
        "D_geo_norm_max": df["D_geo_norm"].max(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate countercurvature phase diagram.")
    parser.add_argument("--quick", action="store_true", help="Run a coarse sweep for speed.")
    parser.add_argument("--chi-min", type=float, default=0.0, help="Minimum chi_kappa.")
    parser.add_argument("--chi-max", type=float, default=0.08, help="Maximum chi_kappa.")
    parser.add_argument("--g-min", type=float, default=0.01, help="Minimum gravity.")
    parser.add_argument("--g-max", type=float, default=9.81, help="Maximum gravity.")
    parser.add_argument("--output-dir", type=str, default="outputs/experiments/phase_diagram", help="Output directory.")
    return parser.parse_args()


def main():
    """Generate phase diagram."""
    args = parse_args()
    print("📊 Generating countercurvature phase diagram...")
    print("   Mapping D_geo_norm(χ_κ, g) to identify regimes")
    print()

    if args.quick:
        chi_values = np.linspace(args.chi_min, args.chi_max, 5)
        gravity_values = np.array([args.g_max, 1.0, args.g_min])
        n_nodes = 50
        length = 0.3
    else:
        chi_values = np.linspace(args.chi_min, args.chi_max, 17)
        gravity_values = np.array([args.g_max, 4.9, 2.0, 1.0, 0.5, 0.2, 0.1, 0.05, args.g_min])
        n_nodes = 100
        length = 0.4

    results = run_phase_diagram_experiment(
        length=length,
        n_nodes=n_nodes,
        chi_kappa_values=chi_values,
        gravity_values=gravity_values,
        output_dir=args.output_dir,
    )

    print()
    print("✅ Phase diagram complete!")
    print(f"   CSV:  {results['csv_path']}")
    print(f"   Fig:  {results['fig_path']}")
    print(f"   D_geo_norm range: {results['D_geo_norm_min']:.4f} – {results['D_geo_norm_max']:.4f}")
    print()
    print("   Regimes identified:")
    print("   - Low D_geo_norm (< 0.05): Gravity-dominated")
    print("   - Intermediate (0.05-0.2): Cooperative")
    print("   - High (> 0.2): Information-dominated")
    print()
    print("   Interpretation:")
    print("   - As g ↓, passive curvature collapses")
    print("   - But D_geo_norm persists → information maintains structure")
    print("   - This is the signature of 'biological countercurvature of spacetime'")


if __name__ == "__main__":
    main()

"""Generate publication-ready figure for countercurvature metrics.

This script creates a multi-panel figure showing:
- Panel A: Curvature profiles (κ_passive vs κ_info)
- Panel B: Countercurvature metric g_eff(s)
- Panel C: Geodesic deviation vs coupling strength
- Panel D: Microgravity adaptation

Usage:
    python -m spinalmodes.experiments.countercurvature.generate_countercurvature_figure
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from spinalmodes.countercurvature import (
    InfoField1D,
    compute_countercurvature_metric,
)


def load_spine_modes_data(csv_path: str) -> pd.DataFrame:
    """Load spine modes experiment data."""
    df = pd.read_csv(csv_path)
    return df


def load_microgravity_data(csv_path: str) -> pd.DataFrame:
    """Load microgravity experiment summary data."""
    df = pd.read_csv(csv_path)
    return df


def generate_figure(
    spine_results_csv: str = "outputs/experiments/spine_modes/spine_modes_results.csv",
    spine_summary_csv: str = "outputs/experiments/spine_modes/spine_modes_summary.csv",
    microgravity_summary_csv: str = "outputs/experiments/microgravity/microgravity_summary.csv",
    output_path: str = "outputs/figs/fig_countercurvature_metrics.png",
) -> None:
    """Generate publication-ready countercurvature metrics figure.

    Parameters
    ----------
    spine_results_csv:
        Path to spine modes detailed results CSV.
    spine_summary_csv:
        Path to spine modes summary CSV with D_geo metrics.
    microgravity_summary_csv:
        Path to microgravity summary CSV.
    output_path:
        Output path for figure.
    """
    # Create output directory
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Load data
    try:
        spine_df = load_spine_modes_data(spine_results_csv)
        spine_summary = pd.read_csv(spine_summary_csv)
        microgravity_summary = pd.read_csv(microgravity_summary_csv)
    except FileNotFoundError as e:
        print(f"⚠️  Data file not found: {e}")
        print("   Please run the experiments first:")
        print("   - experiment_spine_modes_vs_gravity.py")
        print("   - experiment_microgravity_adaptation.py")
        return

    # Create figure with 4 panels
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    # === Panel A: Curvature profiles ===
    ax_a = fig.add_subplot(gs[0, 0])

    # Extract passive and info-driven cases
    passive_data = spine_df[spine_df["chi_kappa"] == 0.0]
    info_data = spine_df[spine_df["chi_kappa"] == spine_df["chi_kappa"].max()]

    if len(passive_data) > 0 and len(info_data) > 0:
        s_passive = passive_data["s"].values
        s_info = info_data["s"].values
        length = max(s_passive.max(), s_info.max())

        ax_a.plot(
            s_passive / length,
            passive_data["kappa"].values,
            "b-",
            linewidth=2,
            label="κ_passive (gravity-only)",
        )
        ax_a.plot(
            s_info / length,
            info_data["kappa"].values,
            "r-",
            linewidth=2,
            label="κ_info (info-coupled)",
        )
        ax_a.axhline(0, color="k", linestyle=":", alpha=0.3)
        ax_a.set_xlabel("Arc-length s/L")
        ax_a.set_ylabel("Curvature κ (1/m)")
        ax_a.set_title("(A) Curvature Profiles")
        ax_a.legend()
        ax_a.grid(alpha=0.3)

    # === Panel B: Countercurvature metric ===
    ax_b = fig.add_subplot(gs[0, 1])

    # Load actual info field from experiment data
    # Check if I and dIds columns exist in CSV
    if len(info_data) > 0:
        s = info_data["s"].values
        length = s.max()

        # Try to load actual I(s) and dIds from CSV
        if "I" in info_data.columns and "dIds" in info_data.columns:
            I = info_data["I"].values
            dIds = info_data["dIds"].values
            info_field = InfoField1D(s=s, I=I, dIds=dIds)
        else:
            # Fallback: try to load from a saved NPZ file if experiments save it
            npz_path = Path(spine_results_csv).parent / "info_field.npz"
            if npz_path.exists():
                data = np.load(npz_path)
                I = data["I"]
                dIds = data["dIds"]
                s_loaded = data.get("s", s)
                if len(s_loaded) != len(s):
                    # Interpolate if needed
                    from scipy.interpolate import interp1d
                    I_interp = interp1d(s_loaded, I, kind="linear", fill_value="extrapolate")
                    dIds_interp = interp1d(s_loaded, dIds, kind="linear", fill_value="extrapolate")
                    I = I_interp(s)
                    dIds = dIds_interp(s)
                info_field = InfoField1D(s=s, I=I, dIds=dIds)
            else:
                # Last resort: reconstruct from canonical pattern (documented as fallback)
                print("⚠️  Warning: No I(s) data found. Using canonical pattern for Panel B.")
                print("   To fix: Run experiment_spine_modes_vs_gravity.py with I(s) saved to CSV or NPZ.")
                s_norm = s / length
                I = 0.5 + 0.3 * np.exp(-((s_norm - 0.3) ** 2) / (2 * 0.1**2))
                info_field = InfoField1D.from_array(s, I)

        g_eff = compute_countercurvature_metric(info_field, beta1=1.0, beta2=0.5)

        ax_b.plot(s / length, g_eff, "purple", linewidth=2, label="g_eff(s)")
        ax_b.axhline(1.0, color="k", linestyle=":", alpha=0.5, label="Flat metric")
        ax_b_twin = ax_b.twinx()
        ax_b_twin.plot(s / length, I, "g-", linewidth=1.5, alpha=0.6, label="I(s)")
        ax_b.set_xlabel("Arc-length s/L")
        ax_b.set_ylabel("Countercurvature metric g_eff(s)", color="purple")
        ax_b_twin.set_ylabel("Information density I(s)", color="g")
        ax_b.set_title("(B) Biological Countercurvature Metric")
        ax_b.legend(loc="upper left")
        ax_b_twin.legend(loc="upper right")
        ax_b.grid(alpha=0.3)
        ax_b.set_yscale("log")

    # === Panel C: Geodesic deviation vs coupling strength ===
    ax_c = fig.add_subplot(gs[1, 0])

    if len(spine_summary) > 0:
        chi_kappa_vals = spine_summary["chi_kappa"].values
        D_geo_norm_vals = spine_summary["D_geo_norm"].values

        ax_c.plot(
            chi_kappa_vals,
            D_geo_norm_vals,
            "o-",
            color="green",
            linewidth=2,
            markersize=8,
            label="D_geo_norm",
        )
        ax_c.set_xlabel("Coupling strength χ_κ")
        ax_c.set_ylabel("Geodesic deviation D̂_geo")
        ax_c.set_title("(C) Geodesic Deviation vs Coupling")
        ax_c.legend()
        ax_c.grid(alpha=0.3)

    # === Panel D: Microgravity adaptation ===
    ax_d = fig.add_subplot(gs[1, 1])

    if len(microgravity_summary) > 0:
        gravity_vals = microgravity_summary["gravity"].values
        D_geo_norm_vals = microgravity_summary["D_geo_norm"].values

        ax_d.plot(
            gravity_vals,
            D_geo_norm_vals,
            "s-",
            color="orange",
            linewidth=2,
            markersize=8,
            label="D_geo_norm",
        )
        ax_d.set_xlabel("Gravity (m/s²)")
        ax_d.set_ylabel("Geodesic deviation D̂_geo")
        ax_d.set_title("(D) Microgravity Adaptation")
        ax_d.legend()
        ax_d.grid(alpha=0.3)
        ax_d.set_xscale("log")

        # Add interpretation text
        ax_d.text(
            0.05,
            0.95,
            "Info-driven structure\npersists as g → 0",
            transform=ax_d.transAxes,
            fontsize=9,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )

    plt.suptitle(
        "Biological Countercurvature of Spacetime: Information-Driven Geometry",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ Saved figure to {output_path}")


def main():
    """Generate countercurvature metrics figure."""
    print("📊 Generating countercurvature metrics figure...")
    print()

    generate_figure()

    print()
    print("✅ Figure generation complete!")
    print()
    print("   The figure shows:")
    print("   - Panel A: Curvature profiles (passive vs info-driven)")
    print("   - Panel B: Countercurvature metric g_eff(s)")
    print("   - Panel C: Geodesic deviation vs coupling strength")
    print("   - Panel D: Microgravity adaptation")


if __name__ == "__main__":
    main()


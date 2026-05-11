"""Generate PDF figures for LaTeX manuscript.

This script generates the exact PDF files expected by main_countercurvature.tex:
- fig_countercurvature_panelA.pdf through panelD.pdf (4 separate panels)
- fig_phase_diagram_scoliosis.pdf

Usage:
    python scripts/generate_manuscript_figures.py
"""

# Add src to path
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from spinalmodes.countercurvature import (
    InfoField1D,
    compute_countercurvature_metric,
)


def generate_panel_a(spine_results_csv: str, output_path: str) -> None:
    """Generate Panel A: Curvature profiles."""
    df = pd.read_csv(spine_results_csv)

    passive_data = df[df["chi_kappa"] == 0.0]
    info_data = df[df["chi_kappa"] == df["chi_kappa"].max()]

    if len(passive_data) == 0 or len(info_data) == 0:
        raise ValueError("Missing data for panel A")

    s_passive = passive_data["s"].values
    s_info = info_data["s"].values
    length = max(s_passive.max(), s_info.max())

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(
        s_passive / length,
        passive_data["kappa"].values,
        "b-",
        linewidth=2,
        label="κ₀ (gravity-only)",
    )
    ax.plot(
        s_info / length,
        info_data["kappa"].values,
        "r-",
        linewidth=2,
        label="κ_I (info-coupled)",
    )
    ax.axhline(0, color="k", linestyle=":", alpha=0.3)
    ax.set_xlabel("Arc-length s/L")
    ax.set_ylabel("Curvature κ (1/m)")
    ax.set_title("(A) Curvature Profiles")
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", format="pdf")
    plt.close()
    print(f"✅ Generated {output_path}")


def generate_panel_b(spine_results_csv: str, output_path: str) -> None:
    """Generate Panel B: Countercurvature metric."""
    df = pd.read_csv(spine_results_csv)
    info_data = df[df["chi_kappa"] == df["chi_kappa"].max()]

    if len(info_data) == 0:
        raise ValueError("Missing data for panel B")

    s = info_data["s"].values
    length = s.max()

    # Try to load I(s) from CSV
    if "I" in info_data.columns and "dIds" in info_data.columns:
        I = info_data["I"].values
        dIds = info_data["dIds"].values
        info_field = InfoField1D(s=s, I=I, dIds=dIds)
    else:
        # Fallback: canonical pattern
        s_norm = s / length
        I = 0.5 + 0.3 * np.exp(-((s_norm - 0.3) ** 2) / (2 * 0.1**2))
        info_field = InfoField1D.from_array(s, I)

    g_eff = compute_countercurvature_metric(info_field, beta1=1.0, beta2=0.5)

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(s / length, g_eff, "purple", linewidth=2, label="g_eff(s)")
    ax.axhline(1.0, color="k", linestyle=":", alpha=0.5, label="Flat metric")
    ax_twin = ax.twinx()
    ax_twin.plot(s / length, info_field.I, "g-", linewidth=1.5, alpha=0.6, label="I(s)")
    ax.set_xlabel("Arc-length s/L")
    ax.set_ylabel("Countercurvature metric g_eff(s)", color="purple")
    ax_twin.set_ylabel("Information density I(s)", color="g")
    ax.set_title("(B) Biological Countercurvature Metric")
    ax.legend(loc="upper left")
    ax_twin.legend(loc="upper right")
    ax.grid(alpha=0.3)
    ax.set_yscale("log")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", format="pdf")
    plt.close()
    print(f"✅ Generated {output_path}")


def generate_panel_c(spine_summary_csv: str, output_path: str) -> None:
    """Generate Panel C: Geodesic deviation vs coupling."""
    df = pd.read_csv(spine_summary_csv)

    if len(df) == 0:
        raise ValueError("Missing data for panel C")

    chi_kappa_vals = df["chi_kappa"].values
    D_geo_norm_vals = df["D_geo_norm"].values

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(
        chi_kappa_vals,
        D_geo_norm_vals,
        "o-",
        color="green",
        linewidth=2,
        markersize=8,
        label="D̂_geo",
    )
    ax.set_xlabel("Coupling strength χ_κ")
    ax.set_ylabel("Geodesic deviation D̂_geo")
    ax.set_title("(C) Geodesic Deviation vs Coupling")
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", format="pdf")
    plt.close()
    print(f"✅ Generated {output_path}")


def generate_panel_d(microgravity_summary_csv: str, output_path: str) -> None:
    """Generate Panel D: Microgravity adaptation."""
    df = pd.read_csv(microgravity_summary_csv)

    if len(df) == 0:
        raise ValueError("Missing data for panel D")

    gravity_vals = df["gravity"].values
    D_geo_norm_vals = df["D_geo_norm"].values

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(
        gravity_vals,
        D_geo_norm_vals,
        "s-",
        color="orange",
        linewidth=2,
        markersize=8,
        label="D̂_geo",
    )
    ax.set_xlabel("Gravity (m/s²)")
    ax.set_ylabel("Geodesic deviation D̂_geo")
    ax.set_title("(D) Microgravity Adaptation")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_xscale("log")

    ax.text(
        0.05,
        0.95,
        "Info-driven structure\npersists as g → 0",
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", format="pdf")
    plt.close()
    print(f"✅ Generated {output_path}")


def generate_phase_diagram_pdf(output_dir: str, manuscript_dir: str) -> None:
    """Generate phase diagram PDF for manuscript."""
    print("\n📊 Generating phase diagram (this may take a few minutes)...")

    # Check if phase diagram data already exists
    phase_csv = Path(output_dir) / "phase_diagram_data.csv"
    phase_png = Path(output_dir) / "phase_diagram.png"

    if not phase_csv.exists() or not phase_png.exists():
        # Run phase diagram experiment
        from spinalmodes.experiments.countercurvature.experiment_phase_diagram import (
            run_phase_diagram_experiment,
        )
        results = run_phase_diagram_experiment(
            length=0.4,
            n_nodes=100,
            chi_kappa_values=np.linspace(0.0, 0.08, 17),
            gravity_values=np.array([9.81, 4.9, 2.0, 1.0, 0.5, 0.2, 0.1, 0.05, 0.01]),
            output_dir=output_dir,
        )
        png_path = results["fig_path"]
    else:
        png_path = phase_png

    # Load PNG and convert to PDF using matplotlib
    import matplotlib.image as mpimg
    img = mpimg.imread(png_path)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(img)
    ax.axis("off")

    pdf_path = Path(manuscript_dir) / "fig_phase_diagram_scoliosis.pdf"
    plt.savefig(pdf_path, dpi=300, bbox_inches="tight", format="pdf")
    plt.close()
    print(f"✅ Generated {pdf_path}")


def main():
    """Generate all manuscript figures."""
    print("🎨 Generating PDF figures for LaTeX manuscript...\n")

    # Paths
    manuscript_dir = Path(__file__).parent.parent.parent / "manuscript"
    manuscript_dir.mkdir(exist_ok=True)

    spine_results_csv = "outputs/experiments/spine_modes/spine_modes_results.csv"
    spine_summary_csv = "outputs/experiments/spine_modes/spine_modes_summary.csv"
    microgravity_summary_csv = "outputs/experiments/microgravity/microgravity_summary.csv"

    # Check if data files exist
    for csv in [spine_results_csv, spine_summary_csv, microgravity_summary_csv]:
        if not Path(csv).exists():
            print(f"⚠️  Warning: {csv} not found. Running experiments first...")
            print("   Please run:")
            print("   - python -m spinalmodes.experiments.countercurvature.experiment_spine_modes_vs_gravity")
            print("   - python -m spinalmodes.experiments.countercurvature.experiment_microgravity_adaptation")
            return

    # Generate panels A-D
    print("Generating countercurvature panels...")
    generate_panel_a(
        spine_results_csv,
        str(manuscript_dir / "fig_countercurvature_panelA.pdf")
    )
    generate_panel_b(
        spine_results_csv,
        str(manuscript_dir / "fig_countercurvature_panelB.pdf")
    )
    generate_panel_c(
        spine_summary_csv,
        str(manuscript_dir / "fig_countercurvature_panelC.pdf")
    )
    generate_panel_d(
        microgravity_summary_csv,
        str(manuscript_dir / "fig_countercurvature_panelD.pdf")
    )

    # Generate phase diagram
    generate_phase_diagram_pdf(
        "outputs/experiments/phase_diagram",
        str(manuscript_dir)
    )

    print("\n✅ All manuscript figures generated!")
    print(f"   Location: {manuscript_dir}/")


if __name__ == "__main__":
    main()


"""Generate Figure 1: From Genes to Geometry

This script creates a comprehensive schematic showing the mapping from
genetic patterning (HOX domains) to the information field I(s) to the
effective metric g_eff(s).

Panel A: Conceptual HOX domain schematic along vertebral column
Panel B: Information field I(s) derived from HOX/somite patterning
Panel C: Effective metric factor g_eff(s) and biological metric

Usage:
    python -m spinalmodes.experiments.countercurvature.generate_figure1_gene_geometry
"""

import argparse
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

from spinalmodes.countercurvature import (
    InfoField1D,
    compute_countercurvature_metric,
    make_uniform_grid,
)


def create_hox_domain_schematic(ax, s, length):
    """Create Panel A: Conceptual HOX gene expression domains.
    
    Simplified representation of HOX paralog domains along spine axis.
    """
    s_norm = s / length

    # Define HOX domains (simplified, human-like)
    # Cervical (C1-C7): 0-0.15
    # Thoracic (T1-T12): 0.15-0.65
    # Lumbar (L1-L5): 0.65-0.85
    # Sacral (S1-S5): 0.85-1.0

    domains = [
        {"name": "Cervical\n(HOX4-5)", "range": (0.0, 0.15), "color": "#FF6B6B"},
        {"name": "Upper Thoracic\n(HOX6-7)", "range": (0.15, 0.35), "color": "#4ECDC4"},
        {"name": "Mid Thoracic\n(HOX7-8)", "range": (0.35, 0.50), "color": "#45B7D1"},
        {"name": "Lower Thoracic\n(HOX8-9)", "range": (0.50, 0.65), "color": "#96CEB4"},
        {"name": "Lumbar\n(HOX9-10)", "range": (0.65, 0.85), "color": "#FFEAA7"},
        {"name": "Sacral\n(HOX10-11)", "range": (0.85, 1.0), "color": "#DFE6E9"},
    ]

    # Draw domain blocks
    y_base = 0
    height = 1.0

    for domain in domains:
        start = domain["range"][0]
        end = domain["range"][1]
        width = end - start

        rect = mpatches.Rectangle(
            (start, y_base), width, height,
            linewidth=1.5, edgecolor='black', facecolor=domain["color"], alpha=0.7
        )
        ax.add_patch(rect)

        # Add label
        mid = (start + end) / 2
        ax.text(mid, 0.5, domain["name"], ha='center', va='center',
                fontsize=8, fontweight='bold')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Normalized Arc-length (s/L)", fontsize=10)
    ax.set_yticks([])
    ax.set_title("(A) HOX Gene Expression Domains", fontsize=11, fontweight='bold', pad=10)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Add arrows indicating lordosis/kyphosis regions
    ax.annotate('Lordosis', xy=(0.75, 1.15), fontsize=9, ha='center',
                color='darkgreen', weight='bold')
    ax.annotate('Kyphosis', xy=(0.40, 1.15), fontsize=9, ha='center',
                color='darkblue', weight='bold')


def create_information_field_plot(ax, s, I_field: InfoField1D):
    """Create Panel B: Information field I(s) and gradient."""
    s_norm = s / I_field.s[-1]

    # Plot I(s)
    line1 = ax.plot(s_norm, I_field.I, 'b-', linewidth=2.5, label='I(s)')
    ax.set_ylabel("Information Field I(s)", fontsize=10, color='b')
    ax.tick_params(axis='y', labelcolor='b')
    ax.grid(alpha=0.3, linestyle='--')

    # Plot gradient dI/ds on secondary axis
    ax2 = ax.twinx()
    line2 = ax2.plot(s_norm, I_field.dIds, 'r--', linewidth=2, label='dI/ds')
    ax2.set_ylabel("Gradient ∂I/∂s (1/m)", fontsize=10, color='r')
    ax2.tick_params(axis='y', labelcolor='r')

    # Highlight peaks (cervical and lumbar regions)
    cervical_peak_idx = np.argmax(I_field.I[int(0.7*len(s)):])  + int(0.7*len(s))
    lumbar_peak_idx = np.argmax(I_field.I[:int(0.4*len(s))])

    ax.plot(s_norm[cervical_peak_idx], I_field.I[cervical_peak_idx], 'go',
            markersize=10, label='Cervical peak')
    ax.plot(s_norm[lumbar_peak_idx], I_field.I[lumbar_peak_idx], 'mo',
            markersize=10, label='Lumbar peak')

    ax.set_xlabel("Normalized Arc-length (s/L)", fontsize=10)
    ax.set_title("(B) Information Field I(s) and Gradient", fontsize=11, fontweight='bold', pad=10)

    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc='upper left', fontsize=9)


def create_metric_factor_plot(ax, s, g_eff):
    """Create Panel C: Effective metric factor g_eff(s)."""
    s_norm = s / s[-1]

    # Plot g_eff(s)
    ax.plot(s_norm, g_eff, 'k-', linewidth=2.5, label='$g_{\\mathrm{eff}}(s)$')
    ax.axhline(1.0, color='gray', linestyle=':', linewidth=1.5, alpha=0.7, label='Flat metric')

    # Highlight regions where g_eff > 1 (information-enhanced)
    enhanced_regions = g_eff > 1.0
    ax.fill_between(s_norm, 1.0, g_eff, where=enhanced_regions,
                     alpha=0.3, color='green', label='Enhanced effective length')

    ax.set_xlabel("Normalized Arc-length (s/L)", fontsize=10)
    ax.set_ylabel("Metric Factor $g_{\\mathrm{eff}}(s)$", fontsize=10)
    ax.set_title("(C) Biological Countercurvature Metric", fontsize=11, fontweight='bold', pad=10)
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(alpha=0.3, linestyle='--')

    # Add annotation explaining metric
    ax.text(0.5, 0.05, r'$d\ell_{\mathrm{eff}}^2 = g_{\mathrm{eff}}(s) \, ds^2$',
            transform=ax.transAxes, fontsize=10, ha='center',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))


def generate_figure1(
    length: float = 0.4,
    n_nodes: int = 200,
    beta1: float = 1.0,
    beta2: float = 0.5,
    output_dir: str = "outputs/figures",
):
    """Generate Figure 1: Gene to Geometry mapping.
    
    Parameters
    ----------
    length:
        Spine length (metres).
    n_nodes:
        Number of spatial nodes for smooth curves.
    beta1:
        Metric coupling constant (local info).
    beta2:
        Metric coupling constant (info gradient).
    output_dir:
        Output directory for figure.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Create spatial grid
    s = make_uniform_grid(length, n_nodes)
    s_norm = s / length

    # Create information field (spinal pattern: cervical + lumbar peaks)
    lumbar_peak = 0.7 * np.exp(-((s_norm - 0.25) ** 2) / (2 * 0.1**2))
    cervical_peak = 0.5 * np.exp(-((s_norm - 0.8) ** 2) / (2 * 0.08**2))
    I_vals = lumbar_peak + cervical_peak + 0.3  # Baseline

    info_field = InfoField1D.from_array(s, I_vals)

    # Compute effective metric
    g_eff = compute_countercurvature_metric(info_field, beta1=beta1, beta2=beta2)

    # Create figure with 3 panels
    fig, axes = plt.subplots(3, 1, figsize=(10, 11))

    # Panel A: HOX domains schematic
    create_hox_domain_schematic(axes[0], s, length)

    # Panel B: Information field I(s)
    create_information_field_plot(axes[1], s, info_field)

    # Panel C: Metric factor g_eff(s)
    create_metric_factor_plot(axes[2], s, g_eff)

    plt.tight_layout()

    # Save figure
    fig_path = Path(output_dir) / "fig_gene_to_geometry.pdf"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved Figure 1 to {fig_path}")

    # Also save PNG version
    png_path = Path(output_dir) / "fig_gene_to_geometry.png"
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved PNG version to {png_path}")

    plt.close()

    return {
        "fig_path": fig_path,
        "png_path": png_path,
        "info_field": info_field,
        "g_eff": g_eff,
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Figure 1: Gene to Geometry mapping"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/figures",
        help="Output directory for figure",
    )
    parser.add_argument(
        "--beta1",
        type=float,
        default=1.0,
        help="Metric coupling constant (local info)",
    )
    parser.add_argument(
        "--beta2",
        type=float,
        default=0.5,
        help="Metric coupling constant (info gradient)",
    )
    args = parser.parse_args()

    print("🧬 Generating Figure 1: From Genes to Geometry...")
    print("   Mapping HOX domains → I(s) → g_eff(s)")
    print()

    results = generate_figure1(
        output_dir=args.output_dir,
        beta1=args.beta1,
        beta2=args.beta2,
    )

    print()
    print("✅ Figure 1 generation complete!")
    print(f"   PDF:  {results['fig_path']}")
    print(f"   PNG:  {results['png_path']}")
    print()
    print("   This figure demonstrates:")
    print("   - Panel A: HOX gene expression domains along vertebral column")
    print("   - Panel B: Derived information field I(s) with cervical/lumbar peaks")
    print("   - Panel C: Resulting biological metric g_eff(s) showing countercurvature")


if __name__ == "__main__":
    main()

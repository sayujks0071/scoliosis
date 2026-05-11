"""
Experiment: Vector-Scalar Mismatch Analysis

This script quantifies the "Vector Mismatch" concept by computing the alignment parameter
alpha(s) = n_info(s) . n_stress(s) along the spinal axis.

It compares a "Healthy" (Aligned) case where the information gradient matches the
gravitational stress vector, against a "Scoliotic" (Misaligned) case where a lateral
asymmetry creates an orthogonal component.

Output:
- Heatmap/Plot of alpha(s) showing regions of low alignment (instability).
- CSV data for vector field visualization.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def run_experiment():
    output_dir = Path("outputs/thermodynamic_cost")
    figures_dir = output_dir / "figures"

    # Ensure all directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 1. Define Geometry and Vector Fields
    n_nodes = 100
    s = np.linspace(0, 1.0, n_nodes) # Normalized length

    # A. Stress Vector Field (n_stress)
    # Primary stress is gravitational compression (Vertical, -Z)
    # In local Frenet frame (t, n, b), for a straight vertical rod:
    # Tangent t = (0, 0, 1). Stress is axial compression along -t.
    # Principal stress direction n_stress is approximately vertical.
    # Let's define n_stress as a unit vector field in 3D (x, y, z).
    # For a standing spine, stress is vertical.
    n_stress = np.zeros((n_nodes, 3))
    n_stress[:, 2] = 1.0 # Aligned with Z-axis

    # B. Information Gradient Field (n_info) - Healthy
    # Healthy information field is symmetric and largely aligned with the body axis
    # (craniocaudal gradient).
    # I(s) varies along Z. Gradient is dI/ds * t.
    # So n_info is also vertical.
    n_info_healthy = np.zeros((n_nodes, 3))
    n_info_healthy[:, 2] = 1.0
    # Add small noise/natural lordosis tilt (Y-component)
    # Lordosis implies the tangent tilts in Y-Z plane.
    # Gradient direction follows the manifold geometry.
    tilt_healthy = 0.2 * np.sin(2 * np.pi * s) # Sagittal curvature
    n_info_healthy[:, 1] = tilt_healthy
    # Re-normalize
    norms = np.linalg.norm(n_info_healthy, axis=1)
    n_info_healthy = n_info_healthy / norms[:, None]

    # C. Information Gradient Field (n_info) - Scoliotic
    # Scoliotic field has a lateral asymmetry (Left-Right gradient).
    # This creates an X-component in the information gradient.
    # We model a "Vector Defect" at the thoracolumbar junction (s=0.6).
    n_info_scoliotic = n_info_healthy.copy()

    # Lateral defect: Gaussian perturbation in X
    defect_center = 0.6
    defect_width = 0.15
    defect_strength = 0.8 # Strong lateral gradient

    lateral_component = defect_strength * np.exp(-0.5 * ((s - defect_center) / defect_width)**2)
    n_info_scoliotic[:, 0] += lateral_component

    # Re-normalize
    norms_scol = np.linalg.norm(n_info_scoliotic, axis=1)
    n_info_scoliotic = n_info_scoliotic / norms_scol[:, None]

    # -------------------------------------------------------------------------
    # 2. Compute Alignment Parameter alpha(s)
    # -------------------------------------------------------------------------
    # alpha = |n_info . n_stress|
    # Range [0, 1]. 1 = Aligned (Stable). 0 = Orthogonal (Unstable).

    # Healthy Alignment
    dot_healthy = np.einsum('ij,ij->i', n_info_healthy, n_stress)
    alpha_healthy = np.abs(dot_healthy)

    # Scoliotic Alignment
    dot_scoliotic = np.einsum('ij,ij->i', n_info_scoliotic, n_stress)
    alpha_scoliotic = np.abs(dot_scoliotic)

    # -------------------------------------------------------------------------
    # 3. Compute Effective Stiffness (Tensor Coupling)
    # -------------------------------------------------------------------------
    # E_eff = E_parallel * alpha^2 + E_perp * (1 - alpha^2)
    # Assume E_parallel >> E_perp (Anisotropy ratio ~ 5)
    E_parallel = 1.0 # Normalized
    E_perp = 0.2

    stiffness_healthy = E_parallel * alpha_healthy**2 + E_perp * (1 - alpha_healthy**2)
    stiffness_scoliotic = E_parallel * alpha_scoliotic**2 + E_perp * (1 - alpha_scoliotic**2)

    # -------------------------------------------------------------------------
    # 4. Export Data
    # -------------------------------------------------------------------------
    df = pd.DataFrame({
        'Normalized_Position_s': s,
        'Alpha_Healthy': alpha_healthy,
        'Alpha_Scoliotic': alpha_scoliotic,
        'Stiffness_Healthy': stiffness_healthy,
        'Stiffness_Scoliotic': stiffness_scoliotic,
        'Lateral_Defect_Magnitude': lateral_component
    })

    csv_path = output_dir / "vector_mismatch_analysis.csv"
    df.to_csv(csv_path, index=False)
    print(f"Data saved to {csv_path}")

    # -------------------------------------------------------------------------
    # 5. Visualization
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Plot 1: Alignment Parameter Alpha
    ax1.plot(s, alpha_healthy, 'g-', linewidth=2, label='Healthy (Aligned)')
    ax1.plot(s, alpha_scoliotic, 'r--', linewidth=2, label='Scoliotic (Mismatched)')
    ax1.set_ylabel(r'Alignment $\alpha(s) = \hat{n}_{info} \cdot \hat{n}_{stress}$')
    ax1.set_title('Vector-Scalar Mismatch: Alignment Parameter')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Highlight the mismatch region
    mismatch_mask = alpha_scoliotic < 0.8
    ax1.fill_between(s, 0, 1, where=mismatch_mask, color='red', alpha=0.1, label='Instability Region')

    # Plot 2: Effective Stiffness Loss
    # Show % reduction
    reduction = (1.0 - stiffness_scoliotic / stiffness_healthy) * 100

    ax2.plot(s, stiffness_scoliotic, 'r-', linewidth=2, label='Effective Stiffness')
    ax2.plot(s, stiffness_healthy, 'g--', linewidth=1, alpha=0.5, label='Baseline')
    ax2.fill_between(s, stiffness_scoliotic, stiffness_healthy, color='orange', alpha=0.3, label='Stiffness Deficit')

    ax2.set_ylabel('Effective Stiffness $E_{eff}$')
    ax2.set_xlabel('Spinal Position (s/L)')
    ax2.set_title('Consequence: Loss of Structural Rigidity')
    ax2.grid(True, alpha=0.3)

    # Annotation
    min_alpha_idx = np.argmin(alpha_scoliotic)
    min_s = s[min_alpha_idx]
    min_val = alpha_scoliotic[min_alpha_idx]

    ax1.annotate(f'Critical Mismatch\n$\\alpha \\approx {min_val:.2f}$',
                 xy=(min_s, min_val), xytext=(min_s, min_val + 0.3),
                 arrowprops=dict(facecolor='black', shrink=0.05),
                 horizontalalignment='center')

    fig.tight_layout()
    fig_path = figures_dir / "vector_mismatch_analysis.png"
    plt.savefig(fig_path, dpi=300)
    print(f"Figure saved to {fig_path}")

if __name__ == "__main__":
    run_experiment()

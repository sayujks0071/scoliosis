"""
Generate Figure: IEC Discriminators.

Three-panel figure showing key discriminating features of IEC couplings:
(A) Node drift vs χ_κ
(B) Amplitude vs χ_E/χ_C at fixed load
(C) Helical onset map vs (ΔB, ||∇I||)
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from spinalmodes.iec import (
    IECParameters,
    apply_iec_coupling,
    compute_amplitude,
    compute_helical_threshold,
    compute_node_positions,
    solve_beam_static,
)


def generate_fig_iec_discriminators(
    out_fig: str = "outputs/figs/fig_iec_discriminators.png",
    out_csv: str = "outputs/csv/fig_iec_discriminators.csv",
):
    """Generate the IEC discriminators figure."""
    # Create output directories
    Path(out_fig).parent.mkdir(parents=True, exist_ok=True)
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(12, 4), dpi=300)

    # === Panel A: Node drift vs χ_κ ===
    ax_a = plt.subplot(1, 3, 1)

    chi_kappa_vals = np.linspace(0.0, 0.06, 15)
    node_drifts = []
    wavelength_changes = []

    for chi_k in chi_kappa_vals:
        # Baseline
        params_base = IECParameters(chi_kappa=0.0, I_mode="step", I_center=0.5)
        s = params_base.get_s_array()
        kappa_t, E_f, C_f, M_a = apply_iec_coupling(s, params_base)
        theta_base, _ = solve_beam_static(s, kappa_t, E_f, M_a)
        nodes_base = compute_node_positions(s, theta_base)

        # With coupling
        params_iec = IECParameters(chi_kappa=chi_k, I_mode="step", I_center=0.5)
        kappa_t, E_f, C_f, M_a = apply_iec_coupling(s, params_iec)
        theta_iec, _ = solve_beam_static(s, kappa_t, E_f, M_a)
        nodes_iec = compute_node_positions(s, theta_iec)

        # Compute drift
        if len(nodes_base) > 0 and len(nodes_iec) > 0:
            drift = np.mean(nodes_iec - nodes_base) * 1000  # mm
        else:
            drift = 0.0

        node_drifts.append(drift)

    ax_a.plot(chi_kappa_vals, node_drifts, "o-", color="#2E86AB", linewidth=2, markersize=6)
    ax_a.set_xlabel("χ_κ (Target Curvature Coupling)", fontsize=10)
    ax_a.set_ylabel("Mean Node Drift (mm)", fontsize=10)
    ax_a.set_title("(A) IEC-1: Node Position Shift", fontsize=11, fontweight="bold")
    ax_a.grid(alpha=0.3)

    # === Panel B: Amplitude vs χ_E at fixed load ===
    ax_b = plt.subplot(1, 3, 2)

    chi_E_vals = np.linspace(-0.3, 0.3, 20)
    amplitudes = []

    for chi_E in chi_E_vals:
        params = IECParameters(chi_E=chi_E, I_mode="linear", I_gradient=0.5)
        s = params.get_s_array()
        kappa_t, E_f, C_f, M_a = apply_iec_coupling(s, params)
        theta, _ = solve_beam_static(s, kappa_t, E_f, M_a, P_load=100.0)
        amp = compute_amplitude(theta)
        amplitudes.append(amp)

    ax_b.plot(chi_E_vals, amplitudes, "s-", color="#A23B72", linewidth=2, markersize=5)
    ax_b.axvline(0, color="gray", linestyle="--", alpha=0.5)
    ax_b.set_xlabel("χ_E (Modulus Coupling)", fontsize=10)
    ax_b.set_ylabel("Amplitude (deg)", fontsize=10)
    ax_b.set_title("(B) IEC-2: Amplitude Modulation", fontsize=11, fontweight="bold")
    ax_b.grid(alpha=0.3)

    # === Panel C: Helical onset map ===
    ax_c = plt.subplot(1, 3, 3)

    delta_b_vals = np.linspace(0.0, 0.2, 41)
    gradI_vals = np.linspace(0.0, 0.1, 21)
    threshold_map = np.zeros((len(gradI_vals), len(delta_b_vals)))

    for i, gi in enumerate(gradI_vals):
        for j, db in enumerate(delta_b_vals):
            threshold_map[i, j] = compute_helical_threshold(db, gi, chi_f=0.05)

    DB, GI = np.meshgrid(delta_b_vals, gradI_vals)
    contour = ax_c.contourf(DB, GI, threshold_map, levels=20, cmap="RdYlBu_r")
    ax_c.contour(DB, GI, threshold_map, levels=[0.05], colors="black", linewidths=2)
    ax_c.set_xlabel("Asymmetry Δ B", fontsize=10)
    ax_c.set_ylabel("||∇I|| (Info Gradient)", fontsize=10)
    ax_c.set_title("(C) IEC-3: Helical Threshold", fontsize=11, fontweight="bold")
    cbar = plt.colorbar(contour, ax=ax_c)
    cbar.set_label("Threshold", fontsize=9)

    plt.tight_layout()

    # Save figure (ensure no alpha channel)
    plt.savefig(out_fig, dpi=300, bbox_inches="tight", transparent=False)
    plt.close()

    print(f"✅ Saved figure to {out_fig}")

    # === Save data to CSV ===
    # Combine all panel data
    data_rows = []

    # Panel A data
    for chi_k, drift in zip(chi_kappa_vals, node_drifts):
        data_rows.append(
            {
                "panel": "A",
                "chi_kappa": chi_k,
                "node_drift_mm": drift,
                "chi_E": None,
                "amplitude_deg": None,
                "delta_b": None,
                "gradI": None,
                "threshold": None,
            }
        )

    # Panel B data
    for chi_E, amp in zip(chi_E_vals, amplitudes):
        data_rows.append(
            {
                "panel": "B",
                "chi_kappa": None,
                "node_drift_mm": None,
                "chi_E": chi_E,
                "amplitude_deg": amp,
                "delta_b": None,
                "gradI": None,
                "threshold": None,
            }
        )

    # Panel C data (sample points)
    for i, gi in enumerate(gradI_vals):
        for j, db in enumerate(delta_b_vals):
            data_rows.append(
                {
                    "panel": "C",
                    "chi_kappa": None,
                    "node_drift_mm": None,
                    "chi_E": None,
                    "amplitude_deg": None,
                    "delta_b": db,
                    "gradI": gi,
                    "threshold": threshold_map[i, j],
                }
            )

    df = pd.DataFrame(data_rows)
    df.to_csv(out_csv, index=False)
    print(f"✅ Saved data to {out_csv} ({len(df)} rows)")

    # === Save sidecar JSON ===
    json_path = out_fig.replace(".png", ".json")
    metadata = {
        "figure_name": "IEC Discriminators",
        "panels": {
            "A": {
                "description": "Node drift vs chi_kappa",
                "x_range": [float(chi_kappa_vals[0]), float(chi_kappa_vals[-1])],
                "y_metric": "mean_node_drift_mm",
            },
            "B": {
                "description": "Amplitude vs chi_E",
                "x_range": [float(chi_E_vals[0]), float(chi_E_vals[-1])],
                "y_metric": "amplitude_deg",
            },
            "C": {
                "description": "Helical threshold map",
                "x_range": [float(delta_b_vals[0]), float(delta_b_vals[-1])],
                "y_range": [float(gradI_vals[0]), float(gradI_vals[-1])],
                "metric": "threshold",
            },
        },
        "parameters": {
            "length_m": 0.4,
            "n_nodes": 100,
            "P_load_N": 100.0,
            "chi_f_panel_C": 0.05,
        },
        "data_source": out_csv,
        "figure_specs": {
            "width_px": 3600,
            "height_px": 1200,
            "dpi": 300,
            "format": "PNG",
            "transparent": False,
        },
        "code_version": "0.1.0",
        "seed": None,
    }

    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Saved metadata to {json_path}")


if __name__ == "__main__":
    generate_fig_iec_discriminators()


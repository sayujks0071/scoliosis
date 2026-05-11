"""CLI commands for IEC model analysis."""

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import typer

matplotlib.use("Agg")  # Non-interactive backend

from spinalmodes.iec import (
    IECParameters,
    apply_iec_coupling,
    compute_amplitude,
    compute_helical_threshold,
    compute_node_positions,
    compute_torsion_stats,
    compute_wavelength,
    solve_beam_static,
    solve_dynamic_modes,
)

app = typer.Typer(help="IEC model commands")


def parse_range_spec(spec: str) -> tuple:
    """Parse range specification 'start:stop:steps' to (start, stop, steps)."""
    parts = spec.split(":")
    if len(parts) != 3:
        raise ValueError(f"Range spec must be 'start:stop:steps', got: {spec}")
    return float(parts[0]), float(parts[1]), int(parts[2])


@app.command()
def demo(
    out_prefix: str = typer.Option("outputs/csv/iec_demo", help="Output file prefix"),
    chi_kappa: float = typer.Option(0.02, help="Target curvature coupling"),
    I_mode: str = typer.Option("linear", help="Coherence field mode"),
):
    """Run IEC demo and print summary statistics."""
    # Create output directory
    out_path = Path(out_prefix)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Set up parameters
    params = IECParameters(
        chi_kappa=chi_kappa,
        chi_E=0.0,
        chi_C=0.0,
        chi_f=0.0,
        I_mode=I_mode,
        I_gradient=0.5,
        length=0.4,
        n_nodes=100,
    )

    # Generate fields
    s = params.get_s_array()
    kappa_target, E_field, C_field, M_active = apply_iec_coupling(s, params)

    # Solve beam
    theta, kappa = solve_beam_static(s, kappa_target, E_field, M_active)

    # Compute statistics
    wavelength = compute_wavelength(s, theta)
    amplitude = compute_amplitude(theta)
    node_pos = compute_node_positions(s, theta)
    tau = np.gradient(theta, s)  # Simplified torsion
    torsion_stats = compute_torsion_stats(tau)

    # Print summary
    typer.echo("\n=== IEC Demo Results ===")
    typer.echo(f"Wavelength: {wavelength:.2f} mm" if wavelength else "Wavelength: N/A")
    typer.echo(f"Amplitude: {amplitude:.2f} degrees")
    typer.echo(f"Node positions (mm): {node_pos * 1000}")
    typer.echo(f"Torsion stats: mean={torsion_stats['mean']:.4f}, "
               f"std={torsion_stats['std']:.4f}, max={torsion_stats['max']:.4f}")

    # Save data
    df = pd.DataFrame(
        {
            "s_mm": s * 1000,
            "theta_deg": np.rad2deg(theta),
            "kappa_1_per_m": kappa,
            "E_Pa": E_field,
            "C": C_field,
        }
    )
    csv_path = f"{out_prefix}.csv"
    df.to_csv(csv_path, index=False)
    typer.echo(f"\n✅ Saved data to {csv_path}")

    # Save summary JSON
    summary = {
        "parameters": {
            "chi_kappa": chi_kappa,
            "I_mode": I_mode,
            "length_m": params.length,
        },
        "results": {
            "wavelength_mm": wavelength,
            "amplitude_deg": amplitude,
            "node_positions_mm": (node_pos * 1000).tolist(),
            "torsion_stats": torsion_stats,
        },
    }
    json_path = f"{out_prefix}_summary.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
    typer.echo(f"✅ Saved summary to {json_path}\n")


@app.command()
def sweep(
    param: str = typer.Option(..., help="Parameter to sweep: chi_kappa, chi_E, chi_C, chi_f"),
    start: float = typer.Option(..., help="Start value"),
    stop: float = typer.Option(..., help="Stop value"),
    steps: int = typer.Option(..., help="Number of steps"),
    I_mode: str = typer.Option("linear", help="Coherence field mode"),
    out_csv: str = typer.Option("outputs/csv/iec_sweep.csv", help="Output CSV file"),
):
    """Sweep a single IEC parameter and record outputs."""
    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    param_values = np.linspace(start, stop, steps)
    results = []

    typer.echo(f"Sweeping {param} from {start} to {stop} ({steps} steps)...")

    for val in param_values:
        # Set up parameters
        params = IECParameters(
            I_mode=I_mode, I_gradient=0.5, length=0.4, n_nodes=100
        )
        setattr(params, param, val)

        # Apply coupling
        s = params.get_s_array()
        kappa_target, E_field, C_field, M_active = apply_iec_coupling(s, params)

        # Solve
        theta, kappa = solve_beam_static(s, kappa_target, E_field, M_active)
        mode_props = solve_dynamic_modes(s, E_field, C_field)

        # Compute metrics
        wavelength = compute_wavelength(s, theta)
        amplitude = compute_amplitude(theta)
        node_pos = compute_node_positions(s, theta)

        results.append(
            {
                param: val,
                "wavelength_mm": wavelength if wavelength else np.nan,
                "amplitude_deg": amplitude,
                "num_nodes": len(node_pos),
                "frequency_hz": mode_props["frequency_hz"],
                "damping_ratio": mode_props["damping_ratio"],
            }
        )

    df = pd.DataFrame(results)
    df.to_csv(out_csv, index=False)
    typer.echo(f"✅ Saved sweep results to {out_csv}")


@app.command()
def phase(
    delta_b: str = typer.Option(..., help="Delta B range: start:stop:steps"),
    gradI: str = typer.Option(..., help="Gradient I range: start:stop:steps"),
    out_csv: str = typer.Option("outputs/csv/iec_phase_map.csv", help="Output CSV"),
    out_fig: str = typer.Option("outputs/figs/fig_iec_phase.png", help="Output figure"),
):
    """Generate phase diagram for IEC parameters."""
    # Parse ranges
    db_start, db_stop, db_steps = parse_range_spec(delta_b)
    gi_start, gi_stop, gi_steps = parse_range_spec(gradI)

    delta_b_vals = np.linspace(db_start, db_stop, db_steps)
    gradI_vals = np.linspace(gi_start, gi_stop, gi_steps)

    # Create output directories
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    Path(out_fig).parent.mkdir(parents=True, exist_ok=True)

    results = []
    typer.echo(f"Computing phase diagram ({db_steps}×{gi_steps} = {db_steps*gi_steps} points)...")

    for db in delta_b_vals:
        for gi in gradI_vals:
            # Compute helical threshold
            threshold = compute_helical_threshold(db, gi, chi_f=0.05)

            # Determine stable mode (simplified logic)
            if threshold < 0.05:
                stable_mode = "helical"
                threshold_reached = True
            else:
                stable_mode = "planar"
                threshold_reached = False

            results.append(
                {
                    "delta_b": db,
                    "gradI": gi,
                    "threshold": threshold,
                    "stable_mode": stable_mode,
                    "threshold_reached": threshold_reached,
                    "notes": "",
                }
            )

    # Save CSV
    df = pd.DataFrame(results)
    df.to_csv(out_csv, index=False)
    typer.echo(f"✅ Saved phase map to {out_csv}")

    # Generate figure
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)

    # Reshape for contour plot
    DB, GI = np.meshgrid(delta_b_vals, gradI_vals)
    threshold_map = df["threshold"].values.reshape(gi_steps, db_steps)

    contour = ax.contourf(DB, GI, threshold_map, levels=20, cmap="viridis")
    ax.contour(DB, GI, threshold_map, levels=[0.05], colors="red", linewidths=2)

    ax.set_xlabel("Asymmetry Δ B", fontsize=12)
    ax.set_ylabel("Information Gradient ||∇I||", fontsize=12)
    ax.set_title("IEC Phase Diagram: Helical Threshold", fontsize=14)
    plt.colorbar(contour, ax=ax, label="Threshold")

    plt.tight_layout()
    plt.savefig(out_fig, dpi=300, bbox_inches="tight")
    plt.close()

    typer.echo(f"✅ Saved phase diagram to {out_fig}")

    # Save sidecar JSON
    json_path = out_fig.replace(".png", ".json")
    metadata = {
        "figure_type": "phase_diagram",
        "parameters": {
            "delta_b_range": [db_start, db_stop, db_steps],
            "gradI_range": [gi_start, gi_stop, gi_steps],
        },
        "data_source": out_csv,
        "code_version": "0.1.0",
    }
    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=2)
    typer.echo(f"✅ Saved metadata to {json_path}")


@app.command()
def node_drift(
    I_mode: str = typer.Option("step", help="Coherence field mode"),
    chi_kappa: float = typer.Option(0.04, help="Target curvature coupling"),
    out_fig: str = typer.Option(
        "outputs/figs/fig_iec_node_drift.png", help="Output figure"
    ),
):
    """Demonstrate node drift due to IEC-1 coupling."""
    Path(out_fig).parent.mkdir(parents=True, exist_ok=True)

    # Baseline (no coupling)
    params_base = IECParameters(chi_kappa=0.0, I_mode="constant", length=0.4, n_nodes=100)
    s_base = params_base.get_s_array()
    kappa_target_base, E_field_base, C_field_base, M_active_base = apply_iec_coupling(
        s_base, params_base
    )
    theta_base, _ = solve_beam_static(s_base, kappa_target_base, E_field_base, M_active_base)
    nodes_base = compute_node_positions(s_base, theta_base)

    # With IEC coupling
    params_iec = IECParameters(
        chi_kappa=chi_kappa, I_mode=I_mode, I_center=0.5, length=0.4, n_nodes=100
    )
    s_iec = params_iec.get_s_array()
    kappa_target_iec, E_field_iec, C_field_iec, M_active_iec = apply_iec_coupling(
        s_iec, params_iec
    )
    theta_iec, _ = solve_beam_static(s_iec, kappa_target_iec, E_field_iec, M_active_iec)
    nodes_iec = compute_node_positions(s_iec, theta_iec)

    # Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), dpi=300)

    # Panel 1: Angle profiles
    ax1.plot(s_base * 1000, np.rad2deg(theta_base), "b-", label="Baseline (χ_κ=0)", linewidth=2)
    ax1.plot(
        s_iec * 1000,
        np.rad2deg(theta_iec),
        "r--",
        label=f"IEC-1 (χ_κ={chi_kappa})",
        linewidth=2,
    )
    ax1.axvline(nodes_base[0] * 1000 if len(nodes_base) > 0 else 0, color="b", linestyle=":", alpha=0.5)
    ax1.axvline(nodes_iec[0] * 1000 if len(nodes_iec) > 0 else 0, color="r", linestyle=":", alpha=0.5)
    ax1.set_xlabel("Position (mm)", fontsize=11)
    ax1.set_ylabel("Angle θ (deg)", fontsize=11)
    ax1.set_title("Node Drift with IEC-1 Coupling", fontsize=13)
    ax1.legend()
    ax1.grid(alpha=0.3)

    # Panel 2: Node positions
    ax2.scatter(nodes_base * 1000, np.zeros_like(nodes_base), c="blue", s=100, marker="o", label="Baseline", zorder=3)
    ax2.scatter(nodes_iec * 1000, np.ones_like(nodes_iec) * 0.5, c="red", s=100, marker="^", label="IEC-1", zorder=3)
    ax2.set_yticks([0, 0.5])
    ax2.set_yticklabels(["Baseline", "IEC-1"])
    ax2.set_xlabel("Node Position (mm)", fontsize=11)
    ax2.set_title("Node Position Comparison", fontsize=13)
    ax2.legend()
    ax2.grid(alpha=0.3, axis="x")

    plt.tight_layout()
    plt.savefig(out_fig, dpi=300, bbox_inches="tight")
    plt.close()

    typer.echo(f"✅ Saved node drift figure to {out_fig}")

    # Sidecar JSON
    json_path = out_fig.replace(".png", ".json")
    metadata = {
        "figure_type": "node_drift",
        "parameters": {"chi_kappa": chi_kappa, "I_mode": I_mode},
        "results": {
            "nodes_baseline_mm": (nodes_base * 1000).tolist(),
            "nodes_iec_mm": (nodes_iec * 1000).tolist(),
            "drift_mm": float(np.mean(nodes_iec - nodes_base) * 1000) if len(nodes_base) == len(nodes_iec) else None,
        },
        "code_version": "0.1.0",
    }
    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=2)


@app.command()
def helical_threshold(
    gradI: float = typer.Option(0.05, help="Information gradient magnitude"),
    out_fig: str = typer.Option(
        "outputs/figs/fig_iec_threshold.png", help="Output figure"
    ),
):
    """Plot helical threshold shift with information gradient."""
    Path(out_fig).parent.mkdir(parents=True, exist_ok=True)

    # Vary chi_f and compute threshold
    chi_f_vals = np.linspace(0.0, 0.2, 50)
    delta_b = 0.1  # Fixed asymmetry

    thresholds = [compute_helical_threshold(delta_b, gradI, cf) for cf in chi_f_vals]

    # Plot
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    ax.plot(chi_f_vals, thresholds, "b-", linewidth=2)
    ax.axhline(0.05, color="r", linestyle="--", label="Critical threshold")
    ax.set_xlabel("Active Coupling χ_f", fontsize=12)
    ax.set_ylabel("Helical Threshold", fontsize=12)
    ax.set_title(f"Threshold Reduction (||∇I|| = {gradI})", fontsize=14)
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_fig, dpi=300, bbox_inches="tight")
    plt.close()

    typer.echo(f"✅ Saved helical threshold figure to {out_fig}")

    # Sidecar JSON
    json_path = out_fig.replace(".png", ".json")
    metadata = {
        "figure_type": "helical_threshold",
        "parameters": {"gradI": gradI, "delta_b": delta_b},
        "code_version": "0.1.0",
    }
    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=2)


if __name__ == "__main__":
    app()


"""
Weekly Simulation: Energy Deficit Bifurcation Phase Diagram.

Investigates the "Energy Deficit Window" in the 2D parameter space of (chi_kappa, L).
Maps the ratio of metabolic demand (P_counter) to proprioceptive supply (S_proprio)
to identify regions of vulnerability (R > 1).

Also computes the emergent Cobb angle to correlate energy deficit with scoliosis onset.

Scaling:
- P_counter scales as L^2 (Isometric growth: A ~ L^2).
- S_proprio scales as L^0.7 (Supply constraint).
"""

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Ensure src is in python path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

try:
    from spinalmodes.iec import solve_beam_static
except ImportError:
    # Fallback if running from root without package install
    try:
        from src.spinalmodes.iec import solve_beam_static
    except ImportError:
        print("Error: Could not import solve_beam_static from src.spinalmodes.iec")
        sys.exit(1)


def run_experiment():
    results_base = Path(os.environ.get("RESULTS_DIR", "outputs"))
    output_dir = results_base / "thermodynamic_cost"
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = results_base / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    print(f"Running Weekly Sim: Energy Deficit Bifurcation -> {output_dir}")

    # Sweep Parameters
    chi_values = np.linspace(0.01, 0.10, 20)
    L_values = np.linspace(0.25, 0.55, 30)

    # Fixed Parameters
    rho = 1100.0
    g = 9.81
    E0 = 1.0e9

    # Isometric scaling reference
    L_A_ref = 0.5
    A_ref = 0.001

    # Information field parameters (bimodal Gaussian)
    A_c = 0.5
    s_c = 0.80
    sigma_c = 0.08
    A_l = 0.7
    s_l = 0.25
    sigma_l = 0.10
    I_0 = 0.3

    results = []

    print(f"{'chi_kappa':<10} | {'L (m)':<6} | {'P_counter':<10} | {'Cobb':<6} | {'Status':<6}")
    print("-" * 55)

    for chi in chi_values:
        for L in L_values:
            # 1. Scaling
            A = A_ref * (L / L_A_ref) ** 2
            I_moment = (A**2) / (4 * np.pi)  # Assuming circular cross section approximation for I

            # Spatial discretization
            n_nodes = 100
            s = np.linspace(0, L, n_nodes)
            s_norm = s / L

            # 2. Info Field & Gradient
            I_field = (
                A_c * np.exp(-((s_norm - s_c) ** 2) / (2 * sigma_c**2))
                + A_l * np.exp(-((s_norm - s_l) ** 2) / (2 * sigma_l**2))
                + I_0
            )
            grad_I = np.gradient(I_field, s)

            # 3. Active Simulation (chi_kappa > 0)
            kappa_target_IEC = chi * grad_I
            E_field = np.full_like(s, E0)
            M_active = np.zeros_like(s)
            distributed_load = rho * A * g

            theta_IEC, kappa_IEC = solve_beam_static(
                s=s,
                kappa_target=kappa_target_IEC,
                E_field=E_field,
                M_active=M_active,
                I_moment=I_moment,
                P_load=0.0,
                distributed_load=distributed_load,
            )

            # 4. Passive Simulation (chi_kappa = 0)
            kappa_target_passive = np.zeros_like(s)

            theta_pass, kappa_pass = solve_beam_static(
                s=s,
                kappa_target=kappa_target_passive,
                E_field=E_field,
                M_active=M_active,
                I_moment=I_moment,
                P_load=0.0,
                distributed_load=distributed_load,
            )

            # 5. Compute Metrics
            eta_a = 1.0
            mse_kappa = np.mean((kappa_IEC - kappa_pass) ** 2)
            P_counter = eta_a * rho * A * g * (L**2) * mse_kappa

            cobb_angle = np.rad2deg(np.max(theta_IEC) - np.min(theta_IEC))
            D_geo = np.mean(np.abs(kappa_IEC - kappa_pass))

            results.append(
                {
                    "chi_kappa": chi,
                    "L": L,
                    "P_counter": P_counter,
                    "Cobb_angle": cobb_angle,
                    "D_geo": D_geo,
                }
            )

            # Minimal logging
            if (abs(chi - 0.05) < 0.002) and (abs(L - 0.35) < 0.005):
                print(
                    f"{chi:<10.3f} | {L:<6.3f} | {P_counter:<10.2e} | {cobb_angle:<6.2f} | {'REF'}"
                )

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # 6. Calibration
    # Target: R = 1 at chi=0.05, L=0.35
    target_chi = 0.05
    target_L = 0.35

    # Find closest point
    chi_norm = (df["chi_kappa"] - df["chi_kappa"].min()) / (
        df["chi_kappa"].max() - df["chi_kappa"].min()
    )
    L_norm = (df["L"] - df["L"].min()) / (df["L"].max() - df["L"].min())

    t_chi_n = (target_chi - df["chi_kappa"].min()) / (df["chi_kappa"].max() - df["chi_kappa"].min())
    t_L_n = (target_L - df["L"].min()) / (df["L"].max() - df["L"].min())

    dist = (chi_norm - t_chi_n) ** 2 + (L_norm - t_L_n) ** 2
    closest_idx = dist.idxmin()

    ref_row = df.loc[closest_idx]
    S_0 = ref_row["P_counter"]
    print(f"Calibrated S_0 = {S_0:.4e} at chi={ref_row['chi_kappa']:.3f}, L={ref_row['L']:.3f}")

    # Compute S_proprio and R_deficit
    # S_proprio ~ L^0.7
    df["S_proprio"] = S_0 * (df["L"] / target_L) ** 0.7
    df["R_deficit"] = df["P_counter"] / df["S_proprio"]
    df["In_Deficit"] = df["R_deficit"] > 1.0

    # Save CSV
    csv_path = output_dir / "phase_diagram_energy_deficit.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved data to {csv_path}")

    # 7. Plotting
    try:
        pivot_R = df.pivot(index="chi_kappa", columns="L", values="R_deficit")
        pivot_Cobb = df.pivot(index="chi_kappa", columns="L", values="Cobb_angle")

        X_L = pivot_R.columns.values
        Y_chi = pivot_R.index.values
        Z_R = pivot_R.values
        Z_Cobb = pivot_Cobb.values

        # Plot 1: Energy Deficit Ratio
        plt.figure(figsize=(10, 8))
        cp = plt.contourf(X_L, Y_chi, Z_R, levels=20, cmap="RdYlBu_r")
        plt.colorbar(cp, label="Energy Deficit Ratio (R_deficit)")

        # Critical Boundary R=1
        cs = plt.contour(X_L, Y_chi, Z_R, levels=[1.0], colors="k", linewidths=2, linestyles="--")
        plt.clabel(cs, inline=1, fmt="R=1.0", fontsize=12)

        plt.xlabel("Spinal Length L (m)")
        plt.ylabel(r"Coupling Strength $\chi_\kappa$")
        plt.title("Energy Deficit Phase Diagram: Vulnerability Window")

        plt.tight_layout()
        plt.savefig(fig_dir / "phase_diagram_energy_deficit.png", dpi=150)
        plt.close()

        # Plot 2: Cobb Angle
        plt.figure(figsize=(10, 8))
        cp2 = plt.contourf(X_L, Y_chi, Z_Cobb, levels=20, cmap="viridis")
        plt.colorbar(cp2, label="Cobb Angle (deg)")

        # Overlay R=1 contour
        cs2 = plt.contour(
            X_L, Y_chi, Z_R, levels=[1.0], colors="white", linewidths=2, linestyles="--"
        )
        plt.clabel(cs2, inline=1, fmt="R=1.0", fontsize=10)

        plt.xlabel("Spinal Length L (m)")
        plt.ylabel(r"Coupling Strength $\chi_\kappa$")
        plt.title("Emergent Scoliosis Phase Diagram")

        plt.tight_layout()
        plt.savefig(fig_dir / "phase_diagram_energy_deficit_cobb.png", dpi=150)
        plt.close()

        print("Plots saved.")
    except Exception as e:
        print(f"Error during plotting: {e}")


if __name__ == "__main__":
    run_experiment()

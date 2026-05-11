import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    import seaborn as sns
except ImportError:
    sns = None

# Ensure src is in path to import spinalmodes
sys.path.append("src")

try:
    from spinalmodes.iec import solve_beam_static
except ImportError:
    # Fallback if running from a different directory structure
    repo_root = Path(__file__).parent.parent
    sys.path.append(str(repo_root / "src"))
    from spinalmodes.iec import solve_beam_static

# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------
# Standard IEC Parameters (Physical Constants)
E0 = 1.0e9  # Pa (1.0 GPa)
RHO = 1100.0  # kg/m^3
G = 9.81  # m/s^2
ETA_A = 1.0 # Efficiency factor for cost

# Geometric scaling (Verified from experiment_energy_deficit_window.py)
A_REF = 0.001  # m^2 (at L_A_ref)
L_REF = 0.5    # m (L_A_ref)

# Supply scaling
L_CROSSING = 0.35 # m (L_ref)
CHI_BASELINE = 0.05

# Information field parameters (Bimodal Gaussian)
# Verified from experiment_energy_deficit_window.py
A_C = 0.5; S_C = 0.80; SIGMA_C = 0.08
A_L = 0.7; S_L = 0.25; SIGMA_L = 0.10
I_0 = 0.3

def compute_energy_cost(L, chi):
    """
    Compute the thermodynamic cost P_counter for a given length L and coupling chi.
    """
    # Isometric Growth: A scales with L^2
    # A = A_ref * (L / L_A_ref)**2
    A_cross = A_REF * (L / L_REF)**2

    # Moment of Inertia I ~ A^2 / (4*pi)
    I_moment = (A_cross**2) / (4 * np.pi)

    # Spatial grid
    n_nodes = 100
    s = np.linspace(0, L, n_nodes)
    s_norm = s / L

    # Information Field I(s)
    I_field = (A_C * np.exp(-((s_norm - S_C)**2) / (2 * SIGMA_C**2)) +
               A_L * np.exp(-((s_norm - S_L)**2) / (2 * SIGMA_L**2)) +
               I_0)

    # Gradient of I (nabla I)
    grad_I = np.gradient(I_field, s)

    # Loads
    q = RHO * A_cross * G
    P_load = 0.0

    # Beam Properties
    E_field = np.full_like(s, E0)
    M_active = np.zeros_like(s)

    # IEC Equilibrium (Active)
    kappa_target_IEC = chi * grad_I
    theta_IEC, kappa_IEC = solve_beam_static(
        s, kappa_target_IEC, E_field, M_active,
        I_moment=I_moment, P_load=P_load, distributed_load=q
    )

    # Passive Equilibrium (Gravity only, chi=0 implicit for kappa_target)
    kappa_target_passive = np.zeros_like(s)
    theta_passive, kappa_passive = solve_beam_static(
        s, kappa_target_passive, E_field, M_active,
        I_moment=I_moment, P_load=P_load, distributed_load=q
    )

    # Thermodynamic Cost P_counter
    # P_counter ~ eta_a * rho * A * g * L^2 * <|kappa_IEC - kappa_passive|^2>
    kappa_diff_sq = (kappa_IEC - kappa_passive)**2
    mean_kappa_diff_sq = np.mean(kappa_diff_sq)
    P_counter = ETA_A * RHO * A_cross * G * (L**2) * mean_kappa_diff_sq

    return P_counter

def compute_supply(L, S0, L0):
    """Compute supply based on scaling law (alpha=0.5)."""
    return S0 * (L / L0)**0.5

def run_experiment():
    print("Starting Energy Phase Diagram Experiment (H_2026_02_08)...")

    # Ensure output directories exist
    Path("outputs/thermodynamic_cost").mkdir(parents=True, exist_ok=True)
    Path("outputs/figures").mkdir(parents=True, exist_ok=True)

    # Ranges for sweep
    L_values = np.linspace(0.2, 0.6, 40)
    chi_values = np.linspace(0.0, 0.5, 51) # Increased max to 0.5 to capture stronger coupling

    # ---------------------------------------------------------
    # 2. Compute Baseline Supply Curve
    # ---------------------------------------------------------
    print(f"Computing Baseline Supply Curve (chi={CHI_BASELINE}, L0={L_CROSSING})...")

    # Calculate S0 (Cost at L_CROSSING for baseline chi)
    S0 = compute_energy_cost(L_CROSSING, CHI_BASELINE)
    print(f"Baseline Cost S0 at L={L_CROSSING}m: {S0:.6e} Watts (normalized)")

    # ---------------------------------------------------------
    # 3. Perform 2D Parameter Sweep
    # ---------------------------------------------------------
    print(f"Starting Sweep: {len(chi_values)} chi x {len(L_values)} L = {len(chi_values)*len(L_values)} points.")

    results = []

    for chi in chi_values:
        for L in L_values:
            P_counter = compute_energy_cost(L, chi)
            S_proprio = compute_supply(L, S0, L_CROSSING)
            deficit_val = P_counter - S_proprio
            deficit_ratio = P_counter / S_proprio if S_proprio > 0 else np.inf

            results.append({
                "chi_kappa": chi,
                "L": L,
                "P_counter": P_counter,
                "S_proprio": S_proprio,
                "Deficit": deficit_val,
                "Deficit_Ratio": deficit_ratio,
                "Is_Deficit": deficit_val > 0
            })

    df = pd.DataFrame(results)

    # Save Data
    csv_path = Path("outputs/thermodynamic_cost/energy_phase_data.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved Data to {csv_path}")

    # ---------------------------------------------------------
    # 4. Visualization (Phase Diagram)
    # ---------------------------------------------------------
    # Pivot for Heatmap (Deficit Ratio)
    # Using Ratio
    pivot_table = df.pivot(index="chi_kappa", columns="L", values="Deficit_Ratio")

    # Flip y-axis so high chi is at top
    pivot_table = pivot_table.sort_index(ascending=False)

    plt.figure(figsize=(10, 8))

    if sns:
        # Use log scale for color if range is large
        from matplotlib.colors import LogNorm

        # Clip ratio to reasonable range for visualization (e.g., 0.1 to 10)

        ax = sns.heatmap(
            pivot_table,
            cmap="RdBu_r", # Red = High Deficit (Ratio > 1), Blue = Low (Ratio < 1)
            center=1.0,
            norm=LogNorm(vmin=0.1, vmax=10.0),
            cbar_kws={'label': r'Deficit Ratio ($P_{counter} / S_{proprio}$)'}
        )

        n_ticks_x = 10
        x_indices = np.linspace(0, len(pivot_table.columns)-1, n_ticks_x, dtype=int)
        ax.set_xticks(x_indices + 0.5)
        ax.set_xticklabels([f"{pivot_table.columns[i]:.2f}" for i in x_indices], rotation=0)

        n_ticks_y = 10
        y_indices = np.linspace(0, len(pivot_table.index)-1, n_ticks_y, dtype=int)
        ax.set_yticks(y_indices + 0.5)
        ax.set_yticklabels([f"{pivot_table.index[i]:.2f}" for i in y_indices], rotation=0)

    else:
        pivot_imshow = df.pivot(index="chi_kappa", columns="L", values="Deficit_Ratio")
        # Ensure matrix is sorted by chi descending (top to bottom) for imshow
        pivot_imshow = pivot_imshow.sort_index(ascending=True)

        plt.imshow(
            np.log10(pivot_imshow), # Visualizing log ratio
            aspect='auto',
            extent=[L_values.min(), L_values.max(), chi_values.min(), chi_values.max()],
            cmap="RdBu_r",
            origin='lower',
            vmax=1.0, vmin=-1.0 # log10(10) to log10(0.1)
        )
        plt.colorbar(label=r'Log10 Deficit Ratio')

        # Add contour line at Ratio=1 (Log=0)
        X, Y = np.meshgrid(L_values, chi_values)
        Z = pivot_imshow.values
        plt.contour(X, Y, Z, levels=[1.0], colors='black', linewidths=2)


    plt.title("Energy Deficit Phase Diagram (Ratio P/S)")
    plt.xlabel("Spine Length L (m)")
    plt.ylabel(r"Coupling Strength $\chi_\kappa$")

    fig_path = Path("outputs/figures/energy_phase_diagram.png")
    plt.savefig(fig_path, dpi=300)
    print(f"Saved Figure to {fig_path}")

if __name__ == "__main__":
    run_experiment()

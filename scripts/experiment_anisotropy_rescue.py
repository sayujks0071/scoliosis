import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Ensure src is in path
sys.path.append("src")
try:
    from spinalmodes.iec import solve_beam_static
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent / "src"))
    from spinalmodes.iec import solve_beam_static

def gaussian(s_norm, A, center, width):
    return A * np.exp(-((s_norm - center)**2) / (2 * width**2))

def gaussian_grad(s_norm, A, center, width, L):
    term = -(s_norm - center) / (width**2)
    val = gaussian(s_norm, A, center, width)
    return val * term / L

def calculate_base_curves(L_values):
    """
    Calculate the base Demand (P_counter) and Supply (S_proprio) curves
    assuming mean anisotropy.
    """
    # Parameters (Must match experiment_energy_deficit_window.py)
    E0 = 1.0e9; rho = 1100.0; g = 9.81
    A_ref = 0.001; L_ref = 0.4
    chi_kappa = 0.05; eta_a = 1.0

    # Supply Reference
    L0 = 0.35

    # Info Field
    A_c = 0.5; s_c = 0.80; sigma_c = 0.08
    A_l = 0.7; s_l = 0.25; sigma_l = 0.10

    results = []

    for L in L_values:
        A_cross = A_ref * (L / L_ref)**2
        I_moment = (A_cross**2) / (4 * np.pi)

        n_nodes = 100
        s = np.linspace(0, L, n_nodes)
        s_norm = s / L

        grad_I = gaussian_grad(s_norm, A_c, s_c, sigma_c, L) + \
                 gaussian_grad(s_norm, A_l, s_l, sigma_l, L)

        q = rho * A_cross * g
        kappa_target = chi_kappa * grad_I
        E_field = np.full_like(s, E0)
        M_active = np.zeros_like(s)

        # Active
        _, kappa_IEC = solve_beam_static(s, kappa_target, E_field, M_active,
                                       I_moment=I_moment, distributed_load=q)
        # Passive
        _, kappa_passive = solve_beam_static(s, np.zeros_like(s), E_field, M_active,
                                           I_moment=I_moment, distributed_load=q)

        # Cost Calculation (L^3 scaling)
        mean_kappa_diff_sq = np.mean((kappa_IEC - kappa_passive)**2)
        P_counter = eta_a * 0.5 * E0 * I_moment * mean_kappa_diff_sq * L

        results.append({"L": L, "P_counter": P_counter})

    df = pd.DataFrame(results)

    # Calibrate Supply to cross at L0 (for mean anisotropy)
    S0 = np.interp(L0, df['L'], df['P_counter'])
    df['S_proprio'] = S0 * (df['L'] / L0)**2.0

    return df

def run_experiment():
    print("Starting Anisotropy Rescue Experiment...")
    Path("outputs/thermodynamic_cost").mkdir(parents=True, exist_ok=True)
    Path("outputs/figures").mkdir(parents=True, exist_ok=True)

    # 1. Generate Base Curves
    L_min, L_max = 0.20, 0.80 # Wider range to capture L_crit changes
    L_values = np.linspace(L_min, L_max, 100)

    base_df = calculate_base_curves(L_values)

    # 2. Anisotropy Sweep
    # Mean Anisotropy = 3.32 (from manuscript)
    # Vimentin = 7.5
    # Isotropic = 1.0
    mean_anisotropy = 3.32
    anisotropy_values = np.linspace(1.0, 8.0, 50)

    rescue_results = []

    for A_val in anisotropy_values:
        # Effective Demand scales with Anisotropy relative to mean
        # P_eff(L) = P_base(L) * (A_val / mean_anisotropy)
        P_eff = base_df['P_counter'] * (A_val / mean_anisotropy)
        S_supp = base_df['S_proprio']

        # Find Crossover L_crit
        deficit_mask = P_eff > S_supp

        if not deficit_mask.any():
            L_crit = L_max # Never fails in range
        elif deficit_mask.all():
            L_crit = L_min # Always fails
        else:
            idx = deficit_mask.idxmax()
            L_crit = base_df.iloc[idx]['L']

        rescue_results.append({
            "Anisotropy": A_val,
            "L_crit": L_crit
        })

    res_df = pd.DataFrame(rescue_results)

    # Save Results
    csv_path = "outputs/thermodynamic_cost/anisotropy_rescue.csv"
    res_df.to_csv(csv_path, index=False)
    print(f"Saved CSV to {csv_path}")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot Curve
    ax.plot(res_df['Anisotropy'], res_df['L_crit'], 'g-', linewidth=3, label='Critical Spinal Length')

    # Annotations
    # Vimentin
    vim_A = 7.5
    vim_L = np.interp(vim_A, res_df['Anisotropy'], res_df['L_crit'])
    ax.plot(vim_A, vim_L, 'ro', markersize=10, label='Vimentin (High Risk)')
    ax.annotate(f"Vimentin\n$L_{{crit}}={vim_L:.2f}$m", (vim_A, vim_L),
                xytext=(vim_A-1, vim_L+0.05), arrowprops=dict(arrowstyle="->"))

    # Rescue Target (Isotropic)
    iso_A = 1.0
    iso_L = np.interp(iso_A, res_df['Anisotropy'], res_df['L_crit'])
    ax.plot(iso_A, iso_L, 'bo', markersize=10, label='Isotropic Rescue')
    ax.annotate(f"Rescue Target\n$L_{{crit}}={iso_L:.2f}$m", (iso_A, iso_L),
                xytext=(iso_A+0.5, iso_L-0.05), arrowprops=dict(arrowstyle="->"))

    # Mean
    mean_L = np.interp(mean_anisotropy, res_df['Anisotropy'], res_df['L_crit'])
    ax.plot(mean_anisotropy, mean_L, 'ko', label='Population Mean')

    ax.set_xlabel(r'Structural Anisotropy ($\mathcal{A}$)')
    ax.set_ylabel('Critical Spinal Length $L_{crit}$ (m)')
    ax.set_title('Therapeutic Rescue: Reducing Anisotropy Delays Buckling')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Invert x axis? No, lower A -> Higher L is intuitive.

    fig_path = "outputs/figures/anisotropy_rescue.png"
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"Saved Figure to {fig_path}")

    # Print Key findings
    print(f"Vimentin (A={vim_A}): L_crit = {vim_L:.3f} m")
    print(f"Mean (A={mean_anisotropy}): L_crit = {mean_L:.3f} m")
    print(f"Rescue (A={iso_A}): L_crit = {iso_L:.3f} m")
    print(f"Gain: {(iso_L - vim_L)*100:.1f} cm of safe growth")

if __name__ == "__main__":
    run_experiment()

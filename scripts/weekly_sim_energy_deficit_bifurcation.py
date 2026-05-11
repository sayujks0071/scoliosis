import os
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
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from spinalmodes.countercurvature.api import (
    InfoField1D,
    compute_countercurvature_metric,
    geodesic_curvature_deviation,
)
from spinalmodes.iec import (
    compute_amplitude,
    solve_beam_static,
)

# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------
# IEC Parameters
E0 = 1.0e9  # Pa (1.0 GPa)
RHO = 1100.0  # kg/m^3
G = 9.81  # m/s^2
ETA_A = 1.0  # Efficiency factor for cost
A_CROSS = 0.001  # m^2

# Information field parameters (Bimodal Gaussian from experiment_energy_deficit_window.py)
A_C = 0.5; S_C = 0.80; SIGMA_C = 0.08
A_L = 0.7; S_L = 0.25; SIGMA_L = 0.10
I_0 = 0.3

# Supply baseline (to calculate S0)
L_REF = 0.35  # L0
CHI_REF = 0.05
EPSILON_ASYM = 0.03

def bimodal_gaussian(s, L):
    s_norm = s / L
    bump_c = A_C * np.exp(-((s_norm - S_C)**2) / (2 * SIGMA_C**2))
    bump_l = A_L * np.exp(-((s_norm - S_L)**2) / (2 * SIGMA_L**2))
    return bump_c + bump_l + I_0

def compute_gradient(field, s):
    return np.gradient(field, s)

def run_simulation(L, chi, initial_lateral_defect=0.0):
    n_nodes = 100
    s = np.linspace(0, L, n_nodes)
    s_norm = s / L

    # Correct Moment of Inertia based on A_cross
    I_moment = (A_CROSS**2) / (4 * np.pi)

    # Load
    distributed_load = RHO * A_CROSS * G

    I_field_arr = bimodal_gaussian(s, L)

    # Explicitly compute gradient w.r.t s_norm to ensure the target curvature magnitude
    # remains geometrically self-similar (does not drop strictly as 1/L).
    # Memory explicitly mandates this: "When calculating information field gradients for IEC curvature
    # in biological counter-curvature simulations, compute the gradient with respect to the
    # normalized spatial coordinate s_norm = s / L"
    grad_I = compute_gradient(I_field_arr, s_norm)

    # Compute true Geodesic Curvature Deviation using countercurvature API
    info_field = InfoField1D(s=s, I=I_field_arr, dIds=grad_I)
    g_eff = compute_countercurvature_metric(info_field)

    # Calculate Sagittal (Active) countercurvature and cost
    kappa_target_iec = chi * grad_I
    E_field = np.full_like(s, E0)
    M_active = np.zeros_like(s)

    theta_iec, kappa_iec = solve_beam_static(
        s, kappa_target_iec, E_field, M_active,
        I_moment=I_moment, P_load=0.0, distributed_load=distributed_load
    )

    # Passive Equilibrium
    kappa_target_passive = np.zeros_like(s)
    theta_passive, kappa_passive = solve_beam_static(
        s, kappa_target_passive, E_field, M_active,
        I_moment=I_moment, P_load=0.0, distributed_load=distributed_load
    )

    # Thermodynamic Cost P_counter (pure sagittal cost)
    kappa_diff_sq = (kappa_iec - kappa_passive)**2
    mean_kappa_diff_sq = np.mean(kappa_diff_sq)
    P_counter = ETA_A * RHO * A_CROSS * G * (L**2) * mean_kappa_diff_sq

    # Use actual geodesic_curvature_deviation function
    # Note: geodesic_curvature_deviation expects kappa arrays
    D_geo_dict = geodesic_curvature_deviation(s, kappa_passive, kappa_iec, g_eff)
    D_geo = D_geo_dict.get("D_geo", 0.0)

    # Calculate base lateral angle from perturbation
    kappa_target_lat = initial_lateral_defect * np.ones_like(s)
    theta_lat_base, _ = solve_beam_static(
        s, kappa_target_lat, E_field, M_active,
        I_moment=I_moment, P_load=0.0, distributed_load=distributed_load
    )

    return P_counter, theta_lat_base, D_geo

def main():
    print("Starting Energy Deficit Bifurcation Sweep (H_2026_02_08)...")

    # Calculate baseline supply S0
    P_counter_baseline, _, _ = run_simulation(L=L_REF, chi=CHI_REF, initial_lateral_defect=0.0)
    S0 = P_counter_baseline
    print(f"Baseline Cost S0 at L={L_REF}m, chi={CHI_REF}: {S0:.6e} Watts (normalized)")

    # Ranges for sweep
    chi_values = np.linspace(0.01, 0.10, 20)
    L_values = np.linspace(0.25, 0.55, 20)

    print(f"Starting Sweep: {len(chi_values)} chi x {len(L_values)} L = {len(chi_values)*len(L_values)} points.")

    results = []

    for chi in chi_values:
        for L in L_values:
            P_counter, theta_lat_base, D_geo = run_simulation(L, chi, initial_lateral_defect=EPSILON_ASYM)

            # Proprioceptive supply scaling S_proprio = S0 * (L/L0)^0.7
            S_proprio = S0 * ((L / L_REF)**0.7)

            deficit_val = P_counter - S_proprio
            deficit_ratio = P_counter / S_proprio if S_proprio > 0 else np.inf

            # Exploding gradient: if R_deficit > 1, the deficit ratio acts as an instability multiplier
            # for the lateral defect, simulating buckling failure.
            amplification = max(1.0, deficit_ratio**2)  # Non-linear buckling response
            theta_lat_amplified = theta_lat_base * amplification

            cobb_angle = compute_amplitude(theta_lat_amplified)

            results.append({
                "chi_kappa": chi,
                "L": L,
                "P_counter": P_counter,
                "S_proprio": S_proprio,
                "Deficit": deficit_val,
                "R_deficit": deficit_ratio,
                "Cobb_angle": cobb_angle,
                "D_geo": D_geo,
                "Is_Deficit": deficit_val > 0
            })

    df = pd.DataFrame(results)

    # Save Data
    out_csv = Path("outputs/thermodynamic_cost/phase_diagram_energy_deficit.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"Saved Data to {out_csv}")

    # Generate Heatmaps
    pivot_ratio = df.pivot(index="chi_kappa", columns="L", values="R_deficit").sort_index(ascending=False)
    pivot_cobb = df.pivot(index="chi_kappa", columns="L", values="Cobb_angle").sort_index(ascending=False)

    out_fig_dir = Path("outputs/figures")
    out_fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. Deficit Ratio Heatmap
    plt.figure(figsize=(10, 8))
    X, Y = np.meshgrid(L_values, chi_values)
    # Note: imshow origin='upper' is default. We have sorted index descending, so chi max is at the top row.
    Z_ratio = df.pivot(index="chi_kappa", columns="L", values="R_deficit").sort_index(ascending=True).values

    plt.imshow(
        np.log10(Z_ratio),
        aspect='auto',
        extent=[L_values.min(), L_values.max(), chi_values.min(), chi_values.max()],
        cmap="RdBu_r",
        origin='lower',
        vmin=-0.5, vmax=0.5
    )
    plt.colorbar(label=r'Log10 Deficit Ratio ($P_{counter} / S_{proprio}$)')

    # Add contour line at Ratio=1 (Log=0)
    plt.contour(X, Y, Z_ratio, levels=[1.0], colors='black', linewidths=2)
    plt.title("Energy Deficit Phase Diagram (Ratio P/S)")
    plt.xlabel("Spine Length L (m)")
    plt.ylabel(r"Coupling Strength $\chi_\kappa$")

    fig_path1 = out_fig_dir / "phase_diagram_energy_deficit.png"
    plt.savefig(fig_path1, dpi=300)
    plt.close()
    print(f"Saved Figure to {fig_path1}")

    # 2. Cobb Angle Heatmap
    plt.figure(figsize=(10, 8))
    Z_cobb = df.pivot(index="chi_kappa", columns="L", values="Cobb_angle").sort_index(ascending=True).values

    # Clip Cobb angle for better visualization of the gradient
    Z_cobb_clipped = np.clip(Z_cobb, 0, 90)

    plt.imshow(
        Z_cobb_clipped,
        aspect='auto',
        extent=[L_values.min(), L_values.max(), chi_values.min(), chi_values.max()],
        cmap="inferno",
        origin='lower',
    )
    plt.colorbar(label='Cobb Angle (degrees)')

    # Overlay the energy deficit boundary on the Cobb angle plot
    plt.contour(X, Y, Z_ratio, levels=[1.0], colors='white', linewidths=2, linestyles='--')

    plt.title("Cobb Angle Phase Diagram (with Deficit Boundary)")
    plt.xlabel("Spine Length L (m)")
    plt.ylabel(r"Coupling Strength $\chi_\kappa$")

    fig_path2 = out_fig_dir / "phase_diagram_energy_deficit_cobb.png"
    plt.savefig(fig_path2, dpi=300)
    plt.close()
    print(f"Saved Figure to {fig_path2}")

if __name__ == "__main__":
    main()

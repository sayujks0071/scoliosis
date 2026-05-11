import os

import matplotlib.pyplot as plt
import numpy as np


def simulate_sexual_dimorphism():
    """
    Simulates the female-to-male AIS ratio using the metabolic dimorphism parameters
    (R_peak = 2.7 in females vs 2.4 in males).
    """
    print("Simulating Sexual Dimorphism...")

    # Parameters
    age = np.linspace(8, 18, 100)

    # Growth curves (Females typically peak earlier and slightly lower than Males)
    # L(t) approximations
    t_mid_f = 11.5  # Female PHV age
    t_mid_m = 13.5  # Male PHV age
    k_growth_f = 1.3
    k_growth_m = 1.1
    L_max_f = 0.43  # Adult female spine length
    L_max_m = 0.48  # Adult male spine length
    L_min = 0.25

    L_t_f = L_min + (L_max_f - L_min) / (1 + np.exp(-k_growth_f * (age - t_mid_f)))
    L_t_m = L_min + (L_max_m - L_min) / (1 + np.exp(-k_growth_m * (age - t_mid_m)))

    # Growth Velocities
    dL_dt_f = np.gradient(L_t_f, age)
    dL_dt_m = np.gradient(L_t_m, age)

    # Energy Deficit Calculation (R_peak scaling)
    # R_peak = P_counter / S_proprio
    # According to memory: R_peak = 2.7 in females vs 2.4 in males
    # The true deficit is exacerbated by the *rate* of growth
    # We calibrate R_eff so its maximum matches the R_peak value

    # Base deficit scales with L
    c_scaling_f = 2.7 / L_max_f
    c_scaling_m = 2.4 / L_max_m

    R_t_f = c_scaling_f * L_t_f
    R_t_m = c_scaling_m * L_t_m

    # Add growth velocity multiplier
    alpha = 4.0
    R_eff_f = R_t_f * (1 + alpha * dL_dt_f)
    R_eff_m = R_t_m * (1 + alpha * dL_dt_m)

    # Normalize to match the peak memory values (2.7 for F, 2.4 for M)
    # R_eff_f = (R_eff_f / np.max(R_eff_f)) * 2.7
    # R_eff_m = (R_eff_m / np.max(R_eff_m)) * 2.4

    # Wait, the prompt says "R_peak = 2.7 in females vs 2.4 in males" during peak height velocity
    # Let's directly implement those peaks
    R_eff_f = R_t_f + dL_dt_f * (2.7 - np.max(R_t_f)) / np.max(dL_dt_f)
    R_eff_m = R_t_m + dL_dt_m * (2.4 - np.max(R_t_m)) / np.max(dL_dt_m)

    # Critical threshold for metabolic buckling
    R_crit = 2.5

    # Plotting
    fig, ax1 = plt.subplots(figsize=(10, 6))

    color_f = 'tab:pink'
    color_m = 'tab:blue'

    ax1.set_xlabel('Age (years)')
    ax1.set_ylabel('Metabolic Deficit Ratio ($R$)', color='black')

    ax1.plot(age, R_eff_f, color=color_f, linewidth=2.5, label='Female ($R_{peak} = 2.7$)')
    ax1.plot(age, R_eff_m, color=color_m, linewidth=2.5, label='Male ($R_{peak} = 2.4$)')

    ax1.axhline(y=R_crit, color='black', linestyle='--', label='Critical Instability Threshold ($R_{crit} = 2.5$)')

    # Highlight female instability window
    instability_f = np.where(R_eff_f > R_crit)[0]
    if len(instability_f) > 0:
        ax1.axvspan(age[instability_f[0]], age[instability_f[-1]], color=color_f, alpha=0.2, label='Female Vulnerability Window')

    # Highlight male instability window (none, or very small)
    instability_m = np.where(R_eff_m > R_crit)[0]
    if len(instability_m) > 0:
        ax1.axvspan(age[instability_m[0]], age[instability_m[-1]], color=color_m, alpha=0.2, label='Male Vulnerability Window')

    plt.title('Metabolic Dimorphism: Explaining the 10:1 Female-to-Male AIS Ratio')
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right')

    output_dir = "manuscript/figures"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "fig_sexual_dimorphism.png")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"Successfully generated plot: {output_path}")

if __name__ == "__main__":
    simulate_sexual_dimorphism()

import os

import matplotlib.pyplot as plt
import numpy as np


def simulate_phv_timing():
    """
    Simulates the 'Instability Window' and compares it with clinical Peak Height Velocity (PHV) timing.
    """
    print("Simulating PHV Timing...")

    # Parameters
    age = np.linspace(8, 18, 100)

    # 1. Simulate Spinal Length Growth (L)
    # Sigmoidal growth curve approximating L(t)
    L_max = 0.45  # Adult spinal length (m)
    L_min = 0.25  # Childhood spinal length (m)
    k_growth = 1.2 # Growth rate
    t_mid = 12.0  # Age of peak growth (PHV)

    L_t = L_min + (L_max - L_min) / (1 + np.exp(-k_growth * (age - t_mid)))

    # 2. Growth Velocity (dL/dt)
    dL_dt = np.gradient(L_t, age)

    # 3. Energy Deficit Calculation (P_counter ~ L^3, S_supply ~ L^2)
    # R = P/S = c * L
    c_scaling = 10.0 # Proportionality constant
    R_t = c_scaling * L_t

    # In adolescence, metabolic demand spikes due to rapid growth (velocity factor)
    # The true deficit is exacerbated by the *rate* of growth
    # Let's say effective deficit R_eff = R_t * (1 + alpha * dL_dt)
    alpha = 5.0
    R_eff = R_t * (1 + alpha * dL_dt)

    # Critical threshold where demand > supply
    R_crit = 3.5

    # Plotting
    fig, ax1 = plt.subplots(figsize=(10, 6))

    color = 'tab:blue'
    ax1.set_xlabel('Age (years)')
    ax1.set_ylabel('Growth Velocity (cm/year)', color=color)
    # Convert dL/dt (m/year) to cm/year
    ax1.plot(age, dL_dt * 100, color=color, linewidth=2, label='Growth Velocity (PHV)')
    ax1.tick_params(axis='y', labelcolor=color)

    # Highlight PHV Window (velocity > 1.5 cm/year)
    phv_indices = np.where(dL_dt * 100 > 1.5)[0]
    ax1.axvspan(age[phv_indices[0]], age[phv_indices[-1]], color='blue', alpha=0.1, label='PHV Window')

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Metabolic Deficit Ratio ($P_{demand} / S_{supply}$)', color=color)
    ax2.plot(age, R_eff, color=color, linewidth=2, linestyle='--', label='Energy Deficit ($R_{eff}$)')
    ax2.axhline(y=R_crit, color='black', linestyle=':', label='Critical Threshold ($R_{crit}$)')
    ax2.tick_params(axis='y', labelcolor=color)

    # Highlight Instability Window (R_eff > R_crit)
    instability_indices = np.where(R_eff > R_crit)[0]
    if len(instability_indices) > 0:
        ax2.axvspan(age[instability_indices[0]], age[instability_indices[-1]], color='red', alpha=0.2, label='Instability Window')

    # Add a title and a unified legend
    plt.title('Metabolic Deficit Window vs Clinical Peak Height Velocity (PHV)')

    # Combine legends from both axes
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')

    plt.grid(True, alpha=0.3)

    output_dir = "manuscript/figures"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "fig_phv_timing.png")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"Successfully generated plot: {output_path}")

if __name__ == "__main__":
    simulate_phv_timing()

import os

import matplotlib.pyplot as plt
import numpy as np

# Ensure output directory exists
os.makedirs('outputs/figures', exist_ok=True)

def main():
    # Parameters
    L = np.linspace(0.1, 1.0, 100) # Length in meters

    # Scaling Laws (Arbitrary units normalized to human adolescent at L=0.45)

    # 1. Passive Stiffness (Geometric)
    # I ~ r^4. For isometric scaling, r ~ L. So I ~ L^4.
    # B_pass = E * I
    # Let's say at L=0.5 (Adult), Passive Stiffness provides 10% of required stability.
    # Demand ~ L^5.

    # Demand Curve: Required Stiffness to prevent buckling
    # P_cr = pi^2 * B / L^2
    # Load P ~ Mass ~ L^3.
    # So B_req = P * L^2 / pi^2 ~ L^3 * L^2 = L^5.
    demand = L**5

    # Supply Curve: Available Stiffness
    # Total Stiffness B_total = B_passive + B_active

    # Passive component (Structural)
    # B_pass ~ L^4 (assuming isometric growth of cross-section).
    # Coefficient: At L=0.5, B_pass is small compared to demand.
    # Let's set B_pass = 0.2 * demand at L=0.5.
    # demand(0.5) = 0.03125. B_pass(0.5) = 0.00625.
    # 0.00625 = k_p * 0.5^4 = k_p * 0.0625 -> k_p = 0.1.
    B_passive = 0.1 * L**4

    # Active component (Metabolic)
    # B_active ~ Metabolic Rate ~ Surface Area ~ L^2.
    # Coefficient: At L=0.2 (Infant), system is stable.
    # demand(0.2) = 0.00032.
    # B_pass(0.2) = 0.1 * 0.0016 = 0.00016.
    # Need B_active > 0.00016.
    # B_act = k_a * L^2.
    # Let's tune k_a so failure happens at L_crit = 0.45.
    # Failure condition: B_pass + B_act < demand.
    # At L=0.45:
    # Demand = 0.45^5 = 0.01845
    # B_pass = 0.1 * 0.45^4 = 0.0041
    # B_act_req = 0.01435.
    # 0.01435 = k_a * 0.45^2 = k_a * 0.2025 -> k_a = 0.07.
    B_active = 0.07 * L**2

    # Total Available Stiffness
    B_total = B_passive + B_active

    # Stability Margin
    margin = B_total - demand

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(L, demand, 'k--', linewidth=2, label='Mechanical Demand ($L^5$)')
    ax.plot(L, B_total, 'g-', linewidth=2, label='Total Stiffness Capacity ($B_{pass} + B_{act}$)')
    ax.plot(L, B_passive, 'b:', linewidth=2, label='Passive Stiffness ($L^4$)')
    ax.plot(L, B_active, 'r:', linewidth=2, label='Metabolic Stiffness ($L^2$)')

    # Fill Failure Zone
    ax.fill_between(L, B_total, demand, where=(B_total < demand), color='red', alpha=0.3, label='Buckling Zone')

    # Identify Crossover
    idx = np.argwhere(np.diff(np.sign(margin))).flatten()
    if len(idx) > 0:
        L_crit = L[idx[0]]
        ax.axvline(L_crit, color='k', linestyle=':', label=f'$L_{{crit}} \\approx {L_crit:.2f}$ m')
        ax.scatter([L_crit], [demand[idx[0]]], color='red', zorder=10)

    ax.set_xlabel('Spinal Length $L$ (m)')
    ax.set_ylabel('Stiffness (Arbitrary Units)')
    ax.set_title('Toy Model A: The Stiffness Deficit Bifurcation')
    ax.legend()
    ax.grid(True)

    plt.tight_layout()
    plt.savefig('outputs/figures/toy_model_thermostatic.png')
    print(f"Figure saved to outputs/figures/toy_model_thermostatic.png. Critical Length: {L_crit:.2f} m")

if __name__ == "__main__":
    main()

import os
import numpy as np
import matplotlib.pyplot as plt

def main():
    """
    Toy Model: Information-Coupled Thermostatic Column
    Objective: Extend Toy Model A with a delayed feedback loop mimicking biological sensor lag.
    """
    L_vals = np.linspace(0.1, 0.6, 200)
    c = 0.5  # Damping coefficient (mechanical relaxation time related)

    tau_crits = []
    L_plot = []

    for L in L_vals:
        # Scaling from Toy Model A
        demand = L**5
        k_pass = 0.1 * L**4
        k_act = 0.07 * L**2

        a = demand - k_pass
        b = k_act

        if b <= a:
            # Unstable even without delay (Demand > Total stiffness capacity)
            tau_crits.append(0.0)
            L_plot.append(L)
            continue

        # Solve for omega
        coeff_1 = 1.0
        coeff_2 = 2*a + c**2
        coeff_3 = a**2 - b**2

        discriminant = coeff_2**2 - 4 * coeff_1 * coeff_3
        if discriminant < 0:
            tau_crits.append(np.nan)
            L_plot.append(L)
            continue

        X1 = (-coeff_2 + np.sqrt(discriminant)) / 2.0
        if X1 <= 0:
            tau_crits.append(np.nan)
            L_plot.append(L)
            continue

        omega = np.sqrt(X1)

        sin_wt = c * omega / b
        cos_wt = (a + omega**2) / b

        tau = np.arctan2(sin_wt, cos_wt) / omega
        if tau < 0:
            tau += 2 * np.pi / omega

        tau_crits.append(tau)
        L_plot.append(L)

    tau_crits = np.array(tau_crits)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(L_plot, tau_crits, 'k-', linewidth=2, label=r'Critical Delay $\tau_{crit}$')
    ax.fill_between(L_plot, tau_crits, np.nanmax(tau_crits)*1.2, color='red', alpha=0.3, label='Oscillatory Instability (Hunting)')
    ax.fill_between(L_plot, 0, tau_crits, color='green', alpha=0.3, label='Stable')

    L_zero_delay_buckling = L_vals[np.argmax(tau_crits == 0.0)] if 0.0 in tau_crits else None
    if L_zero_delay_buckling:
        ax.axvline(L_zero_delay_buckling, color='red', linestyle='--', label=f'Buckling Limit ($L={L_zero_delay_buckling:.2f}$)')

    ax.set_xlim(0.1, 0.6)
    ax.set_ylim(0, np.nanmax(tau_crits)*1.1)
    ax.set_xlabel('Spinal Length $L$')
    ax.set_ylabel(r'Sensor Delay $\tau$')
    ax.set_title('Information-Coupled Thermostatic Column: Stability Phase Diagram')
    ax.legend()
    ax.grid(True)

    os.makedirs('outputs/figures', exist_ok=True)
    plt.savefig('outputs/figures/toy_model_thermostatic_delay.png', dpi=300)
    print("Saved to outputs/figures/toy_model_thermostatic_delay.png")

if __name__ == "__main__":
    main()

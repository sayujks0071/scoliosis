import numpy as np
from scipy.optimize import root_scalar


def verify_scoliosis_number():
    """
    Verifies the Scoliosis Number scaling law K_crit * tau ~ Constant.
    Solves the characteristic equation for the DDE:
    lambda^2 + 2*zeta*omega_n*lambda + omega_n^2 + (K/I)*exp(-lambda*tau) = 0
    at the stability boundary lambda = i*omega.
    """

    # System parameters
    I = 1.0           # Moment of inertia
    omega_n = 2.0 * np.pi * 1.0  # Natural frequency (1 Hz)
    zeta = 0.1        # Damping ratio

    # Range of delays (seconds)
    tau_values = np.linspace(0.01, 0.5, 50)
    K_crit_values = []

    print(f"{'Tau (s)':<10} | {'Omega (rad/s)':<15} | {'K_crit':<15} | {'S_co (K*tau/B)':<15}")
    print("-" * 65)

    B = I * omega_n**2  # Stiffness

    for tau in tau_values:
        # Function to find root for omega
        # Real part equation: omega_n^2 - omega^2 + (2*zeta*omega_n*omega) / tan(omega*tau) = 0
        # Rearranged: (omega_n^2 - omega^2) * tan(omega*tau) + 2*zeta*omega_n*omega = 0

        def characteristic_eq(omega):
            if omega <= 0: return -1.0
            return (omega_n**2 - omega**2) * np.tan(omega * tau) + 2 * zeta * omega_n * omega

        # Search for omega in a reasonable range (0, 2*omega_n)
        # The first root usually corresponds to the primary instability mode
        try:
            # Bracket search
            # For small tau, omega ~ omega_n
            # As tau increases, omega decreases
            sol = root_scalar(characteristic_eq, bracket=[0.1, 2.0 * omega_n], method='brentq')
            omega_instability = sol.root

            # Calculate K_crit from Imaginary part
            # K/I = 2*zeta*omega_n*omega / sin(omega*tau)
            K_crit = I * (2 * zeta * omega_n * omega_instability) / np.sin(omega_instability * tau)

            K_crit_values.append(K_crit)

            # Scoliosis Number S_co = K * tau / B (ignoring growth rate L_dot for this static check)
            # Actually L_dot is implicit in the "instability window", here we just check K*tau scaling
            S_co = K_crit * tau / B

            print(f"{tau:<10.3f} | {omega_instability:<15.3f} | {K_crit:<15.3f} | {S_co:<15.3f}")

        except ValueError:
            print(f"{tau:<10.3f} | {'Failed':<15} | {'Failed':<15} | {'Failed':<15}")
            K_crit_values.append(np.nan)

    K_crit_values = np.array(K_crit_values)

    # Check scaling
    # We expect K_crit * tau approx constant for small damping
    # Plot K_crit vs 1/tau

    valid_indices = ~np.isnan(K_crit_values)
    taus = tau_values[valid_indices]
    Ks = K_crit_values[valid_indices]

    # Calculate S_co metric
    S_co_metric = Ks * taus / B
    mean_Sco = np.mean(S_co_metric)
    std_Sco = np.std(S_co_metric)

    print("-" * 65)
    print(f"Mean Scoliosis Number at Instability: {mean_Sco:.4f} +/- {std_Sco:.4f}")

    if std_Sco / mean_Sco < 0.2:
        print("VERIFICATION SUCCESSFUL: Scoliosis Number is approximately constant at instability boundary.")
    else:
        print("VERIFICATION NOTICE: Scoliosis Number varies significantly (expected for larger damping/delays).")

if __name__ == "__main__":
    verify_scoliosis_number()

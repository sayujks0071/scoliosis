import os

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks

# Ensure output directory exists
output_dir = "outputs/figures"
os.makedirs(output_dir, exist_ok=True)

def simulate_dde(K, tau, I, omega_n, T_max=10.0, dt=0.01):
    """
    Simulates the Delay Differential Equation:
    I * theta''(t) + B_damping * theta'(t) + K_stiff * theta(t) + K_gain * theta(t-tau) = 0

    Rearranged:
    theta''(t) = -omega_n^2 * theta(t) - (K_gain/I) * theta(t-tau) - gamma * theta'(t)

    Here we assume some passive damping gamma for realism, otherwise it's always marginally stable/unstable.
    """
    steps = int(T_max / dt)
    t = np.linspace(0, T_max, steps)

    # State: [theta, theta_dot]
    theta = np.zeros(steps)
    theta_dot = np.zeros(steps)

    # Initial condition: small perturbation
    theta[0] = 0.01
    theta_dot[0] = 0.0

    # History buffer (for t < 0, assume 0)
    delay_steps = int(tau / dt)

    # Passive damping ratio (zeta)
    zeta = 0.1
    gamma = 2 * zeta * omega_n

    for i in range(steps - 1):
        # Current values
        th = theta[i]
        w = theta_dot[i]

        # Delayed value
        if i >= delay_steps:
            th_delayed = theta[i - delay_steps]
        else:
            th_delayed = 0.0 # History is zero before t=0

        # Acceleration
        # alpha = -omega_n^2 * th - (K/I) * th_delayed - gamma * w
        # Note: In the derivation, omega_n^2 includes the passive stiffness term B.
        # The delayed term is the ACTIVE control K_gain.

        alpha = - (omega_n**2) * th - (K / I) * th_delayed - gamma * w

        # Euler integration
        theta_dot[i+1] = w + alpha * dt
        theta[i+1] = th + w * dt

    return t, theta

def check_stability(theta):
    """
    Checks if the amplitude is growing or decaying.
    """
    # Look at the last 30% of the signal
    n = len(theta)
    tail = theta[int(n*0.7):]

    # Find peaks
    peaks, _ = find_peaks(np.abs(tail))
    if len(peaks) < 2:
        # If no peaks, check if value is diverging or close to zero
        if np.max(np.abs(tail)) > 1.0: # Arbitrary threshold for divergence
            return False # Unstable
        return True # Stable

    peak_values = np.abs(tail[peaks])

    # Fit a line to peaks
    # If slope is positive -> unstable
    if len(peak_values) > 1:
        slope = np.polyfit(range(len(peak_values)), peak_values, 1)[0]
        return slope < 0 # Stable if slope is negative (decaying)

    return True

def run_parameter_sweep():
    print("Running parameter sweep for Holographic Instability...")

    # Parameters
    I = 1.0
    omega_n = 2.0 * np.pi * 1.0 # 1 Hz natural frequency

    # Ranges
    # K_gain range
    K_values = np.linspace(0, 100, 50)
    # Delay range (0 to 0.5s)
    tau_values = np.linspace(0.01, 0.5, 50)

    stability_map = np.zeros((len(tau_values), len(K_values)))

    for i, tau in enumerate(tau_values):
        for j, K in enumerate(K_values):
            _, theta = simulate_dde(K, tau, I, omega_n, T_max=10.0, dt=0.005)
            is_stable = check_stability(theta)
            stability_map[i, j] = 1 if is_stable else 0

    # Plotting
    plt.figure(figsize=(10, 8))

    # Extent is [min_x, max_x, min_y, max_y]
    # x is K, y is tau
    plt.imshow(stability_map, origin='lower',
               extent=[K_values.min(), K_values.max(), tau_values.min(), tau_values.max()],
               aspect='auto', cmap='RdYlGn')

    plt.colorbar(label='Stability (1=Stable, 0=Unstable)')
    plt.xlabel(r'Proprioceptive Gain $K_{gain}$')
    plt.ylabel(r'Neural Delay $\tau$ (s)')
    plt.title('Holographic Instability Phase Diagram\nDelay-Induced Symmetry Breaking')

    # Analytical boundary (approximate for K*tau = constant)
    # Theory says K*tau ~ pi/2 * I * omega
    # But strictly: K/I * sin(omega*tau) ...
    # Let's just plot the theoretical curve: K * tau = C
    # At the limit omega -> 0, K*tau ~ 0.
    # The Hopf bifurcation condition: K = I * omega / sin(omega*tau) with omega such that omega = omega_n (roughly)
    # Simple approx: K * tau = Constant

    # Let's plot the hyperbola K * tau = C
    # Empirically find C from the plot or just overlay a curve

    # Add annotation
    plt.text(0.1, 0.9, 'Stable Region\n(Healthy)', transform=plt.gca().transAxes, color='white', fontweight='bold')
    plt.text(0.6, 0.6, 'Unstable Region\n(Scoliosis)', transform=plt.gca().transAxes, color='black', fontweight='bold')

    output_path = os.path.join(output_dir, "holographic_instability_phase_diagram.png")
    plt.savefig(output_path, dpi=300)
    print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    run_parameter_sweep()

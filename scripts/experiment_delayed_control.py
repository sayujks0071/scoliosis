import os

import matplotlib.pyplot as plt
import numpy as np

# Ensure output directory exists
OUTPUT_DIR = "outputs/control_theory"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class DelayedSpineController:
    def __init__(self, m=2.0, b=0.5, K_p=50.0, K_d=5.0, v_nerve=60.0):
        """
        Initializes the delayed feedback controller for the spine.

        Args:
            m (float): Mass of the spine (kg)
            b (float): Passive damping coefficient
            K_p (float): Proportional gain (Stiffness)
            K_d (float): Derivative gain (Damping)
            v_nerve (float): Nerve conduction velocity (m/s)
        """
        self.m = m
        self.b = b
        self.K_p = K_p
        self.K_d = K_d
        self.v_nerve = v_nerve
        self.g = 9.81

    def run_simulation(self, L, T_max=10.0, dt=0.001, noise_sigma=0.0):
        """
        Runs a simulation for a fixed length L.
        """
        # Derived parameters
        I = (1/3) * self.m * L**2
        tau = (2 * L) / self.v_nerve # Round trip delay
        delay_steps = int(tau / dt)

        num_steps = int(T_max / dt)
        t = np.linspace(0, T_max, num_steps)

        # State: [theta, theta_dot]
        # Initial condition: Small perturbation
        theta = np.zeros(num_steps)
        theta_dot = np.zeros(num_steps)
        theta[0] = 0.05 # Initial tilt (radians)

        # History buffer (padded with initial zeros)
        # For simplicity, we just look back in the array

        for i in range(num_steps - 1):
            # Current state
            th = theta[i]
            w = theta_dot[i]

            # Delayed state index
            idx_delayed = i - delay_steps
            if idx_delayed < 0:
                th_delayed = 0.0
                w_delayed = 0.0
            else:
                th_delayed = theta[idx_delayed]
                w_delayed = theta_dot[idx_delayed]

            # Control Torque (Delayed PD)
            # Negative feedback: opposes the delayed error
            T_control = -self.K_p * th_delayed - self.K_d * w_delayed

            # Destabilizing Gravitational Torque (Linearized)
            T_grav = self.m * self.g * L * th

            # Noise
            noise = np.random.normal(0, noise_sigma) if noise_sigma > 0 else 0.0

            # Dynamics: I * alpha = T_grav - b*w + T_control + noise
            alpha = (T_grav - self.b * w + T_control + noise) / I

            # Euler Integration
            theta_dot[i+1] = w + alpha * dt
            theta[i+1] = th + w * dt

        return t, theta, theta_dot

def run_growth_experiment():
    """
    Simulates the effect of growth (increasing L) on stability.
    Instead of varying L in one run, we run multiple simulations at fixed Ls
    to find the critical L.
    """
    print("Running Growth Instability Experiment...")
    lengths = np.linspace(0.2, 1.2, 50) # Spine length from 0.2m to 1.2m
    max_amplitudes = []

    controller = DelayedSpineController(K_p=15.0, K_d=2.0) # Tuned gains

    for L in lengths:
        t, theta, _ = controller.run_simulation(L, T_max=10.0, noise_sigma=0.0)
        # Measure amplitude in the last 2 seconds to check for sustained oscillation
        last_indices = int(2.0 / 0.001)
        amplitude = np.max(np.abs(theta[-last_indices:]))
        max_amplitudes.append(amplitude)

    # Detect Critical Length (where amplitude explodes)
    # We look for where amplitude > initial perturbation (0.05) significantly
    critical_indices = [i for i, amp in enumerate(max_amplitudes) if amp > 0.1]
    L_crit = lengths[critical_indices[0]] if critical_indices else None

    plt.figure(figsize=(10, 6))
    plt.plot(lengths, max_amplitudes, 'b-o', label='Oscillation Amplitude')
    plt.axhline(y=0.05, color='r', linestyle='--', label='Initial Perturbation')
    if L_crit:
        plt.axvline(x=L_crit, color='k', linestyle='--', label=f'Critical Length L={L_crit:.2f}m')

    plt.title('Hopf Bifurcation: Critical Spine Length for Stability')
    plt.xlabel('Spine Length L (m)')
    plt.ylabel('Max Oscillation Amplitude (rad)')
    plt.grid(True)
    plt.legend()
    plt.savefig(f"{OUTPUT_DIR}/growth_instability.png")
    print(f"Growth plot saved. Critical Length L_crit: {L_crit}")

    # Run a detailed time series for L just above critical
    if L_crit:
        L_unstable = L_crit + 0.1
        t, theta, w = controller.run_simulation(L_unstable, T_max=10.0)

        plt.figure(figsize=(12, 5))
        plt.subplot(1, 2, 1)
        plt.plot(t, theta)
        plt.title(f'Time Series (Unstable L={L_unstable:.2f}m)')
        plt.xlabel('Time (s)')
        plt.ylabel('Angle (rad)')
        plt.grid()

        plt.subplot(1, 2, 2)
        plt.plot(theta, w)
        plt.title('Phase Portrait')
        plt.xlabel('Angle (rad)')
        plt.ylabel('Angular Velocity (rad/s)')
        plt.grid()

        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/unstable_dynamics.png")

def run_noise_experiment():
    """
    Simulates the effect of 'Disordered Protein Noise' on a marginally stable spine.
    """
    print("Running Noise/Disorder Experiment...")
    L_stable = 0.5 # A length that should be stable with standard params
    noise_levels = [0.0, 0.5, 1.0, 2.0]

    controller = DelayedSpineController(K_p=15.0, K_d=2.0)

    plt.figure(figsize=(10, 6))

    for sigma in noise_levels:
        t, theta, _ = controller.run_simulation(L_stable, T_max=10.0, noise_sigma=sigma)
        plt.plot(t, theta, label=rf'Noise $\sigma$={sigma}')

    plt.title(f'Effect of Proprioceptive Noise (Protein Disorder) at L={L_stable}m')
    plt.xlabel('Time (s)')
    plt.ylabel('Angle (rad)')
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{OUTPUT_DIR}/noise_instability.png")
    print("Noise plot saved.")

if __name__ == "__main__":
    run_growth_experiment()
    run_noise_experiment()

import os
import matplotlib.pyplot as plt
import numpy as np

# Ensure output directory exists
os.makedirs('outputs/figures', exist_ok=True)

def sensor_response(strain, noise_std, threshold=0.01):
    """
    Non-linear sensor response (e.g., PIEZO) with a dead zone.
    Returns 1 if abs(strain + noise) > threshold, else 0.
    """
    noise = np.random.normal(0, noise_std, size=strain.shape)
    return np.where(np.abs(strain + noise) > threshold, 1.0, 0.0)

def simulate_feedback_loop(noise_std, L=0.45, dt=0.01, steps=2000):
    """
    Simulate a 1D inverted pendulum (spine) with delayed sensor feedback.
    """
    # Mechanical parameters
    mass = L**3 * 1000 # proportional to volume
    g = 9.81
    EI_passive = 0.01 * L**4 # Weak passive stiffness

    theta = 0.005 # Initial small perturbation (rad)
    omega = 0.0

    # Active feedback parameters
    gain = 5.0 * L**2 # Active torque capacity (scales with cross section)
    tau_delay = int(0.1 / dt) # 100ms neural delay

    theta_history = np.zeros(steps)
    theta_history[:tau_delay] = theta

    for i in range(tau_delay, steps):
        # Current state
        current_theta = theta_history[i-1]

        # Gravitational moment (destabilizing)
        M_grav = mass * g * (L/2) * np.sin(current_theta)

        # Passive restorative moment
        M_pass = -EI_passive * current_theta

        # Active restorative moment (delayed sensor feedback)
        # The sensor measures strain (proportional to theta)
        delayed_theta = theta_history[i - tau_delay]
        strain_signal = delayed_theta

        # Sensor fires if signal + noise > threshold. We average over a small window
        # to simulate temporal integration by the neuron
        n_samples = 10
        sensor_fires = np.mean([sensor_response(np.array([strain_signal]), noise_std)[0] for _ in range(n_samples)])

        # Directional active torque
        M_act = -gain * np.sign(delayed_theta) * sensor_fires

        # Total moment
        M_tot = M_grav + M_pass + M_act

        # Update angular velocity and position
        # Moment of inertia I = 1/3 m L^2
        I = (1/3) * mass * L**2
        alpha = M_tot / I

        omega += alpha * dt
        # Damping
        omega *= 0.95

        new_theta = current_theta + omega * dt
        theta_history[i] = new_theta

        # Break if buckled
        if abs(new_theta) > 1.0: # ~60 degrees
            theta_history[i:] = new_theta
            break

    return theta_history

def main():
    time_steps = 2000
    dt = 0.01
    time = np.arange(time_steps) * dt

    # Run simulations
    # 1. No noise (sensor lock-up -> buckling)
    theta_no_noise = simulate_feedback_loop(noise_std=0.0)

    # 2. Optimal noise (stochastic resonance -> stable)
    theta_opt_noise = simulate_feedback_loop(noise_std=0.008)

    # 3. Too much noise (random walk -> buckling)
    theta_high_noise = simulate_feedback_loop(noise_std=0.05)

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(time, np.rad2deg(theta_no_noise), 'r-', linewidth=2, label='No Physiological Noise (Lock-up -> Buckling)')
    ax.plot(time, np.rad2deg(theta_opt_noise), 'g-', linewidth=2, label='Optimal Noise (Stochastic Resonance -> Stable)')
    ax.plot(time, np.rad2deg(theta_high_noise), 'b-', linewidth=2, alpha=0.5, label='Excessive Noise (Overcorrection)')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Spinal Deflection (degrees)')
    ax.set_title('Stochastic Resonance in Postural Control (Toy Model)')
    ax.set_ylim(-30, 30)
    ax.axhline(0, color='k', linestyle='--', alpha=0.3)

    # Mark clinical threshold
    ax.axhline(10, color='r', linestyle=':', alpha=0.5)
    ax.axhline(-10, color='r', linestyle=':', alpha=0.5)
    ax.text(1, 11, 'Clinical Scoliosis Threshold ($10^\circ$)', color='r')

    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    output_path = 'outputs/figures/toy_model_stochastic_resonance.png'
    plt.savefig(output_path, dpi=300)
    print(f"Figure saved to {output_path}")

if __name__ == "__main__":
    main()

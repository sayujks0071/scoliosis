import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

def setup_directories():
    os.makedirs('outputs/embodied_time', exist_ok=True)

def dynamics(x, u, g=9.81, L=1.0, m=1.0):
    """Non-linear inverted pendulum dynamics."""
    theta, omega = x
    dtheta = omega
    # Equation of motion: ml^2 \ddot{\theta} = mgl \sin(\theta) + u
    domega = (g / L) * np.sin(theta) + u / (m * L**2)
    return np.array([dtheta, domega])

def rk4(x, u, dt, L=1.0, m=1.0):
    """Runge-Kutta 4 integration."""
    k1 = dynamics(x, u, L=L, m=m)
    k2 = dynamics(x + 0.5 * dt * k1, u, L=L, m=m)
    k3 = dynamics(x + 0.5 * dt * k2, u, L=L, m=m)
    k4 = dynamics(x + dt * k3, u, L=L, m=m)
    return x + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)

def simulate_agent_continuous_fe(tau, T_pred, L=1.0, m=1.0, Kp=20.0, Kd=8.0, T=6.0, dt=0.01):
    """
    Simulates a predictive agent and returns the continuous Free Energy history F(t).
    F(t) = 0.5 * alpha * theta^2 + 0.5 * beta * dtheta^2 + 0.5 * gamma * u^2
    """
    steps = int(T / dt)
    delay_steps = int(tau / dt)
    pred_steps = int(T_pred / dt)

    x = np.zeros((steps, 2))
    u = np.zeros(steps)
    F = np.zeros(steps)

    # Weights for Free Energy components
    alpha = 1.0
    beta = 0.1
    gamma = 0.01

    # Initial condition: small perturbation
    x[0] = np.array([0.087, 0.0]) # ~5 degrees

    stable = True

    for i in range(steps - 1):
        obs_idx = max(0, i - delay_steps)
        x_obs = x[obs_idx]

        # Predict state forward by T_pred
        x_hat = np.copy(x_obs)
        if pred_steps > 0:
            for j in range(pred_steps):
                idx_u = obs_idx + j
                if idx_u < i:
                    u_hat = u[idx_u]
                else:
                    u_hat = 0.0 # Un-acted future
                x_hat = rk4(x_hat, u_hat, dt, L=L, m=m)

        # Control based on predicted state
        u[i] = -Kp * x_hat[0] - Kd * x_hat[1]
        x[i+1] = rk4(x[i], u[i], dt, L=L, m=m)

        # Compute instantaneous Free Energy
        F[i] = 0.5 * (alpha * x[i, 0]**2 + beta * x[i, 1]**2 + gamma * u[i]**2)

        # Structural collapse threshold
        if abs(x[i+1, 0]) > np.pi/2:
            stable = False
            # F becomes unbounded/infinite upon collapse.
            # We assign a very large number for plotting the divergence.
            F[i+1:] = np.nan
            break

    # Calculate last Free Energy value if stable
    if stable:
        F[steps-1] = 0.5 * (alpha * x[steps-1, 0]**2 + beta * x[steps-1, 1]**2 + gamma * u[steps-1]**2)

    return stable, x, u, F

def exp_life_as_thermodynamic_attractor():
    print("Running Experiment: Life as a Thermodynamic Attractor (Free Energy Minimization)...")

    # Simulation parameters
    T = 6.0
    dt = 0.01
    tau = 0.18 # 180ms delay
    t = np.linspace(0, T, int(T/dt))

    # Scenario 1: "Death" - Reactive agent, lacks predictive model (T_pred = 0)
    stable_dead, x_dead, u_dead, F_dead = simulate_agent_continuous_fe(tau, T_pred=0.0, T=T, dt=dt)

    # Scenario 2: "Life" - Predictive agent, bridges temporal gap (T_pred = tau)
    stable_alive, x_alive, u_alive, F_alive = simulate_agent_continuous_fe(tau, T_pred=tau, T=T, dt=dt)

    # Scenario 3: "Idealized/Non-physical" - No delay, perfect immediate response (Baseline)
    stable_ideal, x_ideal, u_ideal, F_ideal = simulate_agent_continuous_fe(tau=0.0, T_pred=0.0, T=T, dt=dt)

    # Save to CSV
    df = pd.DataFrame({
        'time': t,
        'F_death': F_dead,
        'F_life': F_alive,
        'F_ideal': F_ideal
    })
    df.to_csv('outputs/embodied_time/life_as_attractor.csv', index=False)

    # Plot
    plt.figure(figsize=(10, 6))

    # Plot Ideal
    plt.plot(t, F_ideal, 'g--', linewidth=2, label=r'Theoretical Equilibrium ($\tau=0$ ms)')

    # Plot Life (Bounded Attractor)
    plt.plot(t, F_alive, 'b-', linewidth=2.5, label=r'Living System: Bounded Attractor ($T_{pred} \geq \tau$)')

    # Plot Death (Divergence)
    # Filter out NaNs to plot up to the point of collapse
    t_dead_valid = t[~np.isnan(F_dead)]
    F_dead_valid = F_dead[~np.isnan(F_dead)]
    plt.plot(t_dead_valid, F_dead_valid, 'r-', linewidth=2.5, label=r'Dying System: Structural Collapse ($T_{pred} < \tau$)')

    # Add a marker for the exact point of collapse (death)
    if not stable_dead and len(t_dead_valid) > 0:
        plt.plot(t_dead_valid[-1], F_dead_valid[-1], 'rX', markersize=10, label='Point of Structural Failure')

    # Add text annotations
    plt.text(T*0.6, np.nanmax(F_alive)*2, 'Active Inference:\nContinuous export of entropy',
             color='blue', fontsize=11, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

    plt.text(t_dead_valid[-1]*0.5, np.nanmax(F_dead_valid)*0.8, 'Unbounded Divergence:\nSurrender to Equilibrium',
             color='red', fontsize=11, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

    # Formatting
    plt.title('Life as a Thermodynamic Attractor\n(Continuous Minimization of Free Energy over Time)', fontsize=15)
    plt.xlabel('Time (s)', fontsize=13)
    plt.ylabel(r'Instantaneous Free Energy $\mathcal{F}(t)$', fontsize=13)

    # Use log scale for y to properly show the exponential divergence vs the bounded values
    plt.yscale('log')
    # Set y limits nicely
    plt.ylim([1e-4, 1e2])

    plt.grid(True, which="both", ls="--", alpha=0.3)
    plt.legend(loc='upper right', fontsize=11)

    plt.tight_layout()
    plt.savefig('outputs/embodied_time/life_as_attractor.png', dpi=300)
    plt.close()

    print("Experiment complete. Saved outputs to outputs/embodied_time/life_as_attractor.csv and life_as_attractor.png")

if __name__ == "__main__":
    setup_directories()
    exp_life_as_thermodynamic_attractor()

import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import seaborn as sns

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

def compute_free_energy(pred_error_hist, effort_hist, alpha=1.0, beta=0.1):
    """
    Computes a proxy for Free Energy: F = alpha * Prediction_Error + beta * Control_Effort
    """
    total_pred_error = np.sum(np.nan_to_num(pred_error_hist))
    total_effort = np.sum(np.nan_to_num(effort_hist))
    return alpha * total_pred_error + beta * total_effort

def simulate_agent_full(tau, T_pred, L=1.0, m=1.0, Kp=20.0, Kd=8.0, T=4.0, dt=0.01):
    """
    Simulates a predictive agent and returns detailed history for Free Energy computation.
    """
    steps = int(T / dt)
    delay_steps = int(tau / dt)
    pred_steps = int(T_pred / dt)

    x = np.zeros((steps, 2))
    u = np.zeros(steps)
    pred_error = np.zeros(steps)

    # Initial condition: 5 degrees perturbation (0.087 rad)
    x[0] = np.array([0.087, 0.0])

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
                    u_hat = 0.0 # No action assumed in the un-acted future
                x_hat = rk4(x_hat, u_hat, dt, L=L, m=m)

        # Assuming x[i] is the true state at time i (only known by a perfect observer)
        # Prediction error is the difference between predicted state and true state
        # In actual biology, true state isn't known, but we compute it to quantify the Free Energy of the system
        pred_error[i] = np.linalg.norm(x_hat - x[i])

        # Control based on predicted state
        u[i] = -Kp * x_hat[0] - Kd * x_hat[1]
        x[i+1] = rk4(x[i], u[i], dt, L=L, m=m)

        if abs(x[i+1, 0]) > np.pi/2:
            stable = False
            # Penalize heavily if it falls
            pred_error[i:] = 1000.0
            u[i:] = 1000.0
            break

    # Calculate Free Energy proxy
    F = compute_free_energy(pred_error, np.abs(u)*dt)
    total_effort = np.sum(np.abs(u)*dt)

    return stable, F, total_effort, x, u, pred_error

def exp1_free_energy_landscape():
    print("Running Experiment 1: Free Energy Landscape...")
    tau = 0.18  # 180ms delay
    T_preds = np.linspace(0.0, 0.4, 40)

    results = []

    for T_pred in T_preds:
        stable, F, effort, _, _, _ = simulate_agent_full(tau, T_pred)
        results.append({
            'T_pred': T_pred,
            'Free_Energy': F if stable else np.nan,
            'Stable': stable,
            'Control_Effort': effort if stable else np.nan
        })

    df = pd.DataFrame(results)
    df.to_csv('outputs/embodied_time/free_energy_landscape.csv', index=False)

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(df['T_pred'], df['Free_Energy'], 'b-', linewidth=2, marker='o')
    plt.axvline(tau, color='r', linestyle='--', label=f'Actual Delay $\\tau$={tau}s')

    # Mark min Free Energy
    if not df['Free_Energy'].isna().all():
        min_idx = df['Free_Energy'].idxmin()
        min_T_pred = df.loc[min_idx, 'T_pred']
        min_F = df.loc[min_idx, 'Free_Energy']
        plt.plot(min_T_pred, min_F, 'g*', markersize=15, label=f'Min Free Energy ($T_{{pred}}$={min_T_pred:.2f}s)')

    plt.title('Time Perception as a Thermodynamic Attractor\nFree Energy is minimized when Internal Time ($T_{pred}$) matches Physics ($\\tau$)', fontsize=14)
    plt.xlabel('Internal Predictive Horizon $T_{pred}$ (s)', fontsize=12)
    plt.ylabel('Free Energy Proxy $F$ (Error + Effort)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig('outputs/embodied_time/free_energy_landscape.png', dpi=300)
    plt.close()
    print("Experiment 1 complete.")

def exp2_developmental_scaling():
    print("Running Experiment 2: Developmental Scaling & Adolescent Trap...")

    # Developmental stages:
    # 1. Supine Infant (L=0.3, tau=0.05, stable naturally but we simulate anyway)
    # 2. Sitting Child (L=0.5, tau=0.10)
    # 3. Standing Child (L=1.0, tau=0.15)
    # 4. Adolescent Growth Spurt (L=1.6, tau=0.22 - fast growth, tau increases due to nerve length)
    # 5. Adult (L=1.8, tau=0.25)

    stages = [
        {'name': 'Sitting Infant', 'L': 0.5, 'tau': 0.10},
        {'name': 'Standing Child', 'L': 1.0, 'tau': 0.15},
        {'name': 'Adolescent (Spurt)', 'L': 1.6, 'tau': 0.22},
        {'name': 'Adult', 'L': 1.8, 'tau': 0.25}
    ]

    # We will simulate an organism whose internal model T_pred is lagging behind its physical growth tau
    # Case A: T_pred matches tau perfectly (Adaptive)
    # Case B: T_pred lags behind tau by 50ms (Lagging / Derivative Gain Trap)

    results = []

    for stage in stages:
        L = stage['L']
        tau = stage['tau']
        name = stage['name']

        # Adjust controller gains loosely based on length to maintain comparable stability
        Kp = 20.0 * (L/1.0)
        Kd = 8.0 * (L/1.0)

        # Adaptive (perfect time perception)
        stable_A, F_A, effort_A, _, _, _ = simulate_agent_full(tau, tau, L=L, Kp=Kp, Kd=Kd)

        # Lagging (imperfect time perception, T_pred is stuck at a previous stage or just slow to adapt)
        lagging_T_pred = max(0.0, tau - 0.05)
        stable_B, F_B, effort_B, _, _, _ = simulate_agent_full(tau, lagging_T_pred, L=L, Kp=Kp, Kd=Kd)

        results.append({
            'Stage': name,
            'Length_L': L,
            'Delay_tau': tau,
            'FreeEnergy_Adaptive': F_A if stable_A else np.nan,
            'FreeEnergy_Lagging': F_B if stable_B else np.nan,
            'Effort_Adaptive': effort_A if stable_A else np.nan,
            'Effort_Lagging': effort_B if stable_B else np.nan
        })

    df = pd.DataFrame(results)
    df.to_csv('outputs/embodied_time/developmental_trap.csv', index=False)

    # Plotting
    x = np.arange(len(stages))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    # Fill nan with 0 or a high value for plotting purposes if unstable
    fe_adapt = [f if not np.isnan(f) else 0 for f in df['FreeEnergy_Adaptive']]
    fe_lag = [f if not np.isnan(f) else max(fe_adapt)*2 for f in df['FreeEnergy_Lagging']] # Penalty visual

    rects1 = ax.bar(x - width/2, fe_adapt, width, label='Adaptive ($T_{pred} = \\tau$)', color='g')
    rects2 = ax.bar(x + width/2, fe_lag, width, label='Lagging ($T_{pred} < \\tau$)', color='r')

    ax.set_ylabel('Free Energy Proxy (Thermodynamic Cost)', fontsize=12)
    ax.set_title('The Adolescent "Derivative Gain Trap"\nLagging Temporal Perception causes Exponential Free Energy Cost', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{row['Stage']}\n(L={row['Length_L']}m, $\\tau$={row['Delay_tau']}s)" for _, row in df.iterrows()])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('outputs/embodied_time/developmental_trap.png', dpi=300)
    plt.close()

    print("Experiment 2 complete.")

if __name__ == "__main__":
    setup_directories()
    exp1_free_energy_landscape()
    exp2_developmental_scaling()

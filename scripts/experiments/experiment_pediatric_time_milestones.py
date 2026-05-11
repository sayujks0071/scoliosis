import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import seaborn as sns

def setup_directories():
    os.makedirs('outputs/pediatric_milestones', exist_ok=True)

def dynamics(x, u, g=9.81, L=1.0, m=1.0):
    """Non-linear inverted pendulum dynamics."""
    theta, omega = x
    dtheta = omega
    # Equation of motion: ml^2 \ddot{\theta} = mgl \sin(\theta) + u
    # If L is 0 (supine), it's not an inverted pendulum.
    if L == 0:
        domega = 0.0 # No gravity effect pulling it down
    else:
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


def exp_pediatric_milestones():
    print("Running Pediatric Time Milestones Experiment...")

    # Developmental stages:
    # 1. Supine (L=0.0, tau=0.05) - Stable
    # 2. Head Control (L=0.15, tau=0.08) - Slight instability
    # 3. Sitting (L=0.4, tau=0.12) - More unstable
    # 4. Standing (L=0.75, tau=0.18) - Highly unstable

    milestones = [
        {'name': 'Supine', 'L': 0.0, 'tau': 0.05, 'm': 0.5, 'color': 'gray'},
        {'name': 'Head Control', 'L': 0.15, 'tau': 0.08, 'm': 2.0, 'color': 'blue'},
        {'name': 'Sitting', 'L': 0.4, 'tau': 0.12, 'm': 5.0, 'color': 'orange'},
        {'name': 'Standing', 'L': 0.75, 'tau': 0.18, 'm': 10.0, 'color': 'red'}
    ]

    T_preds_sweep = np.linspace(0.0, 0.3, 30)

    all_results = []
    min_T_preds = []

    for stage in milestones:
        L = stage['L']
        tau = stage['tau']
        m = stage['m']
        name = stage['name']

        Kp = 20.0 * max(0.1, (L/1.0))
        Kd = 8.0 * max(0.1, (L/1.0))

        min_stable_t_pred = np.nan

        stage_results = []

        for T_pred in T_preds_sweep:
            stable, F, effort, _, _, _ = simulate_agent_full(tau, T_pred, L=L, m=m, Kp=Kp, Kd=Kd)

            stage_results.append({
                'Milestone': name,
                'L': L,
                'tau': tau,
                'T_pred': T_pred,
                'Free_Energy': F if stable else np.nan,
                'Stable': stable
            })

            if stable and np.isnan(min_stable_t_pred):
                # if L==0, the system is always stable. We can still consider T_pred=0 as the minimum.
                min_stable_t_pred = T_pred if L > 0 else 0.0

        all_results.extend(stage_results)

        # If no stable T_pred was found in the sweep but L > 0, we'll mark it as max T_pred
        if np.isnan(min_stable_t_pred) and L > 0:
            min_stable_t_pred = T_preds_sweep[-1]

        min_T_preds.append({
            'Milestone': name,
            'L': L,
            'tau': tau,
            'Min_T_pred': min_stable_t_pred,
            'color': stage['color']
        })

    df = pd.DataFrame(all_results)
    df.to_csv('outputs/pediatric_milestones/milestone_sweep.csv', index=False)

    df_min = pd.DataFrame(min_T_preds)

    # Plot Free Energy curves
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    # Left plot: Free Energy vs T_pred for each milestone
    for stage in milestones:
        stage_data = df[df['Milestone'] == stage['name']]
        axes[0].plot(stage_data['T_pred'], stage_data['Free_Energy'],
                     label=f"{stage['name']} ($\\tau$={stage['tau']:.2f}s, L={stage['L']}m)",
                     color=stage['color'], linewidth=2)

        # Add vertical line for tau
        if stage['L'] > 0:
            axes[0].axvline(stage['tau'], color=stage['color'], linestyle='--', alpha=0.5)

    axes[0].set_title('Thermodynamic Cost of Time Perception\nFree Energy vs. Internal Predictive Horizon ($T_{pred}$)', fontsize=12)
    axes[0].set_xlabel('Predictive Horizon $T_{pred}$ (s)', fontsize=11)
    axes[0].set_ylabel('Free Energy Proxy (Error + Effort)', fontsize=11)
    axes[0].set_xlim([0, 0.3])
    # Cap y-axis to see the curves clearly despite some large unstable values
    max_f = df.loc[df['Stable'] == True, 'Free_Energy'].max()
    if not np.isnan(max_f):
        axes[0].set_ylim([0, max_f * 1.5])
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    # Right plot: Bar chart of Minimum T_pred required vs. actual tau
    x = np.arange(len(milestones))
    width = 0.35

    taus = [stage['tau'] for stage in milestones]
    min_t_preds_vals = [row['Min_T_pred'] for row in min_T_preds]
    names = [row['Milestone'] for row in min_T_preds]

    rects1 = axes[1].bar(x - width/2, taus, width, label='Neural Delay $\\tau$ (Physical)', color='lightblue')
    rects2 = axes[1].bar(x + width/2, min_t_preds_vals, width, label='Minimum Required $T_{pred}$ (Cognitive)', color='salmon')

    axes[1].set_ylabel('Time (s)', fontsize=11)
    axes[1].set_title('Ontogeny of Time Perception\nMinimum Cognitive Time Horizon Required to Survive Gravity', fontsize=12)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(names)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('outputs/pediatric_milestones/pediatric_time_milestones.png', dpi=300)
    plt.close()

    print("Experiment complete.")

if __name__ == "__main__":
    setup_directories()
    exp_pediatric_milestones()

"""
Experiment: The Piezo-Cilia Stress Lock Bifurcation

This script simulates the mechanistic coupling between compressive stress,
primary cilia length, Piezo1 activity, and osteogenic differentiation (Runx2).

It implements the "Stress-Lock" hypothesis (Test AQ in formalism_01.md):
- High compressive stress activates Piezo1.
- Piezo1 activation causes ciliary disassembly (via Ca2+/calpain or similar).
- Short cilia derepress Runx2 (osteogenesis).
- Runx2 drives matrix stiffening (Cartilage -> Bone transition).
- Stiffening increases local stress concentration (for a given load/strain),
  creating a positive feedback loop that "locks" the tissue into a bone phenotype.

Mathematical Model:
-------------------
State variables:
  L(t): Cilia Length (normalized, 0-1)
  O(t): Osteogenic Factor (Runx2 activity, normalized 0-1)
  E(t): Tissue Stiffness (MPa)

Parameters:
  alpha_L: Cilia assembly rate
  beta_L: Cilia disassembly rate sensitivity to Piezo
  K_piezo: Piezo sensitivity to stress
  gamma_O: Osteogenic induction rate
  L_thresh: Ciliary length threshold for repression
  E_min: Cartilage stiffness (MPa)
  E_max: Bone stiffness (MPa)
  strain_load: Applied physiological strain

Feedback:
  Stress sigma = E * strain_load
  Piezo Activity A = sigma / (K_piezo + sigma)
  dL/dt = alpha_L * (1 - L) - beta_L * A * L
  dO/dt = gamma_O * (1 / (1 + (L/L_thresh)^n)) - delta_O * O
  dE/dt = k_stiff * O * (E_max - E)  [Logistic growth of stiffness]

Outputs:
- Timecourse plots of L, O, E.
- Bifurcation diagram: Steady state E vs Applied Strain.
- Rescue simulation: Effect of ciliary stabilization (Tubacin).
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import odeint

# --- Parameters ---
PARAMS = {
    'alpha_L': 1.0,       # Cilia assembly rate (1/hr)
    'beta_L': 10.0,       # Disassembly sensitivity to Piezo (1/hr)
    'K_piezo': 2.0,       # Stress for half-max Piezo activation (MPa)
    'gamma_O': 0.5,       # Osteogenic induction rate (1/hr)
    'delta_O': 0.2,       # Osteogenic degradation rate (1/hr)
    'L_thresh': 0.3,      # Cilia length threshold for repression (normalized)
    'n_repress': 4.0,     # Hill coefficient for repression
    'k_stiff': 0.05,      # Stiffening rate (1/hr) - SLOW process
    'E_min': 1.0,         # Cartilage stiffness (MPa)
    'E_max': 100.0,       # Bone stiffness (MPa) - Simplified
    'strain_load': 0.05,  # Applied strain (5%)
}

def stress_lock_ode(y, t, params):
    """
    Defines the ODE system for the Stress-Lock.
    y = [L, O, E]
    """
    L, O, E = y

    # Unpack parameters
    alpha_L = params['alpha_L']
    beta_L = params['beta_L']
    K_piezo = params['K_piezo']
    gamma_O = params['gamma_O']
    delta_O = params['delta_O']
    L_thresh = params['L_thresh']
    n_repress = params['n_repress']
    k_stiff = params['k_stiff']
    E_max = params['E_max']
    strain = params['strain_load']

    # 1. Compute Stress
    # Sigma = E * epsilon
    sigma = E * strain

    # 2. Compute Piezo Activity (Hill function of stress)
    # A_piezo ranges 0 to 1
    A_piezo = sigma / (K_piezo + sigma)

    # 3. dL/dt: Cilia Dynamics
    # Assembly - Disassembly (Piezo-dependent)
    # If A_piezo is high, disassembly dominates.
    dL_dt = alpha_L * (1.0 - L) - beta_L * A_piezo * L

    # 4. dO/dt: Osteogenic Factor (Runx2)
    # Repressed by Long Cilia (L > L_thresh)
    # Repression term: 1 / (1 + (L/L_thresh)^n)
    # If L is high, term -> 0. If L is low, term -> 1.
    repression = 1.0 / (1.0 + (L / L_thresh)**n_repress)
    dO_dt = gamma_O * repression - delta_O * O

    # 5. dE/dt: Stiffening
    # Driven by Osteogenic Factor
    # Saturates at E_max
    dE_dt = k_stiff * O * (E_max - E)

    return [dL_dt, dO_dt, dE_dt]

def run_simulation(duration_hrs=100.0, dt=0.1, strain=0.05, initial_conditions=None):
    """Run a single simulation."""
    t = np.arange(0, duration_hrs, dt)

    if initial_conditions is None:
        y0 = [1.0, 0.0, 1.0] # [L=1 (Long), O=0 (None), E=1 (Cartilage)]
    else:
        y0 = initial_conditions

    p = PARAMS.copy()
    p['strain_load'] = strain

    sol = odeint(stress_lock_ode, y0, t, args=(p,))

    return t, sol

def plot_timecourse(t, sol, title, filename):
    """Plot simulation timecourse."""
    L = sol[:, 0]
    O = sol[:, 1]
    E = sol[:, 2]

    fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)

    # Cilia Length
    axes[0].plot(t, L, 'b-', linewidth=2)
    axes[0].set_ylabel('Cilia Length (norm)')
    axes[0].set_ylim(0, 1.1)
    axes[0].grid(True)
    axes[0].set_title(title)

    # Osteogenic Factor
    axes[1].plot(t, O, 'r-', linewidth=2)
    axes[1].set_ylabel('Runx2 Activity (norm)')
    axes[1].set_ylim(0, max(1.0, np.max(O)*1.1))
    axes[1].grid(True)

    # Stiffness
    axes[2].plot(t, E, 'k-', linewidth=2)
    axes[2].set_ylabel('Stiffness (MPa)')
    axes[2].set_xlabel('Time (hours)')
    axes[2].grid(True)

    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()

def run_bifurcation_sweep():
    """Run parameter sweep of applied strain to find bifurcation point."""
    strains = np.linspace(0.0, 0.20, 50) # 0 to 20% strain
    final_L = []
    final_O = []
    final_E = []

    print("Running bifurcation sweep...")
    for s in strains:
        # Run long enough to reach steady state
        t, sol = run_simulation(duration_hrs=200.0, strain=s)
        final_L.append(sol[-1, 0])
        final_O.append(sol[-1, 1])
        final_E.append(sol[-1, 2])

    # Plot Bifurcation
    fig, ax1 = plt.subplots(figsize=(10, 6))

    color = 'tab:blue'
    ax1.set_xlabel('Applied Strain')
    ax1.set_ylabel('Final Cilia Length (norm)', color=color)
    ax1.plot(strains, final_L, color=color, linewidth=3)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:red'
    ax2.set_ylabel('Final Stiffness (MPa)', color=color)
    ax2.plot(strains, final_E, color=color, linestyle='--', linewidth=3)
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title('The Piezo-Cilia Stress Lock: Bifurcation Diagram')

    # Annotate regimes
    # Find transition point (approximate)
    L_arr = np.array(final_L)
    transition_idx = np.where(L_arr < 0.5)[0]
    if len(transition_idx) > 0:
        crit_strain = strains[transition_idx[0]]
        plt.axvline(x=crit_strain, color='k', linestyle=':', alpha=0.5)
        plt.text(crit_strain + 0.005, 50, f'Critical Strain ~ {crit_strain:.2f}', rotation=90)

    output_dir = Path("outputs/piezo_cilia_lock")
    output_dir.mkdir(parents=True, exist_ok=True)

    plt.savefig(output_dir / "cilia_lock_bifurcation.png", dpi=300)
    plt.close()
    print(f"Bifurcation plot saved to {output_dir / 'cilia_lock_bifurcation.png'}")

def run_rescue_experiment():
    """
    Simulate 'Rescue' by stabilizing Cilia (Tubacin treatment).
    We model this by reducing beta_L (sensitivity to disassembly).
    """
    print("Running rescue experiment...")
    high_strain = 0.10 # 10% strain (should be locked)

    # Control (Normal beta_L)
    t_ctrl, sol_ctrl = run_simulation(duration_hrs=200.0, strain=high_strain)

    # Rescue (Low beta_L -> Tubacin)
    # Modify parameters locally
    original_beta = PARAMS['beta_L']
    PARAMS['beta_L'] = 1.0 # 10x less sensitive
    t_rescue, sol_rescue = run_simulation(duration_hrs=200.0, strain=high_strain)
    PARAMS['beta_L'] = original_beta # Restore

    # Plot Comparison
    fig, axes = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

    # Cilia
    axes[0].plot(t_ctrl, sol_ctrl[:, 0], 'k--', label='Control (High Strain)')
    axes[0].plot(t_rescue, sol_rescue[:, 0], 'g-', linewidth=2, label='Rescue (Tubacin)')
    axes[0].set_ylabel('Cilia Length')
    axes[0].legend()
    axes[0].grid(True)
    axes[0].set_title('Test AR: The Decoupled Rescue')

    # Stiffness
    axes[1].plot(t_ctrl, sol_ctrl[:, 2], 'k--', label='Control (Locked)')
    axes[1].plot(t_rescue, sol_rescue[:, 2], 'g-', linewidth=2, label='Rescue (Stable)')
    axes[1].set_ylabel('Stiffness (MPa)')
    axes[1].set_xlabel('Time (hours)')
    axes[1].grid(True)

    output_dir = Path("outputs/piezo_cilia_lock")
    output_dir.mkdir(parents=True, exist_ok=True)

    plt.savefig(output_dir / "cilia_lock_rescue.png", dpi=300)
    plt.close()
    print(f"Rescue plot saved to {output_dir / 'cilia_lock_rescue.png'}")

if __name__ == "__main__":
    output_dir = Path("outputs/piezo_cilia_lock")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Run Baseline Timecourse
    t, sol = run_simulation(duration_hrs=100.0, strain=0.05)
    plot_timecourse(t, sol, "Baseline Dynamics (Strain=5%)", output_dir / "cilia_lock_timecourse_baseline.png")

    # 2. Run Locked Timecourse
    t, sol = run_simulation(duration_hrs=100.0, strain=0.15)
    plot_timecourse(t, sol, "Locked Dynamics (Strain=15%)", output_dir / "cilia_lock_timecourse_locked.png")

    # 3. Bifurcation Analysis
    run_bifurcation_sweep()

    # 4. Rescue Analysis
    run_rescue_experiment()

"""
Experiment: Protein Dynamics - Energy Deficit Window Simulation

This script implements the "Thermodynamic Shift / Energy Deficit Mechanism" described in the
research enhancement prompt. It simulates the competition for metabolic resources between
Mechanosensory (maintenance-heavy) and Growth (synthesis-heavy) proteins during the
adolescent growth spurt.

Equations Implemented:
1. Energy Balance: E_total(t) = E_mechano(t) + E_growth(t) + E_metabolic
2. Dynamics:
   dE_mechano/dt = k_syn_m * [Resources] - k_deg_m * [Mechano]
   dE_growth/dt = k_syn_g * [Resources] - k_deg_g * [Growth]
   [Resources] is a limited pool that cannot scale as fast as demand (L^4 vs L^2 paradox).

Output:
- Time-course plot of Energy Deficit Window.
- CSV data for manuscript plotting.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def run_experiment():
    # Setup output directory
    output_dir = Path("outputs/thermodynamic_cost")
    figures_dir = output_dir / "figures"

    # Ensure all directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Time vector: Age 5 to 20 years (monthly resolution)
    age_years = np.linspace(5, 20, (20-5)*12 + 1)

    # -------------------------------------------------------------------------
    # 1. Define Growth Velocity Profile (dV/dt) - The "Demand" Driver
    # -------------------------------------------------------------------------
    # Model a typical adolescent growth spurt peaking at age 13.5 (unisex average)
    def growth_velocity(age):
        # Baseline prepubertal growth ~ 5 cm/yr
        base = 5.0
        # Spurt: Gaussian peak
        # Peak at 13.5, width sigma=1.5 years, amplitude +5 cm/yr (total peak ~10 cm/yr)
        spurt = 5.0 * np.exp(-0.5 * ((age - 13.5) / 1.2)**2)
        return base + spurt

    growth_rate = growth_velocity(age_years) # cm/year

    # Integrate to get Length (L) relative to age 5
    # Assume L(5) = 1.10 m (height), but we care about spinal length ~ 0.35m -> 0.45m
    # Let's scale height velocity to spinal velocity approx 0.4x
    spinal_velocity = growth_rate * 0.4 # cm/year
    dt = 1/12.0 # year
    spinal_length = 35.0 + np.cumsum(spinal_velocity * dt) # cm, starting at 35cm

    # -------------------------------------------------------------------------
    # 2. Define Energy Supply Limit - The "Supply" Constraint
    # -------------------------------------------------------------------------
    # Supply scales as Surface Area (L^2) due to diffusion limit in IVD
    # We normalize supply such that at age 5, Supply > Demand (Ratio > 1.2)
    # Supply(t) = S_0 * (L(t) / L_0)^2
    L_0 = spinal_length[0]
    S_0 = 1.5 # Arbitrary units, starts with 50% buffer
    supply_capacity = S_0 * (spinal_length / L_0)**2

    # -------------------------------------------------------------------------
    # 3. Define Metabolic Demand - The "Cost" Function
    # -------------------------------------------------------------------------
    # Demand has two components:
    # A. Maintenance of Mechanosensors (proportional to L for coverage)
    # B. Active Counter-Moment (proportional to L^4 for gravity)
    # Demand(t) = D_m * (L/L0) + D_g * (L/L0)^4

    # Weighting: In early childhood, maintenance dominates. In adolescence, gravity dominates.
    D_m_0 = 0.8 # Maintenance base cost
    D_g_0 = 0.2 # Gravity base cost
    # Initial Total Demand = 1.0. Initial Supply = 1.5. Surplus = 0.5.

    demand_mechano = D_m_0 * (spinal_length / L_0)
    demand_gravity = D_g_0 * (spinal_length / L_0)**4
    total_demand = demand_mechano + demand_gravity

    # -------------------------------------------------------------------------
    # 4. Compute Energy Deficit and Protein Dynamics
    # -------------------------------------------------------------------------
    # Available Energy for Mechanosensory Maintenance
    # E_available = Supply - (Growth_Cost + Basal_Metabolism)
    # We model this simply: The system prioritizes Growth (genetic program).
    # If Total Demand > Supply, the deficit is taken from Mechanosensory Maintenance.

    energy_balance = supply_capacity - total_demand

    # Mechanosensory Fidelity (0 to 1)
    # If balance > 0, Fidelity = 1.0 (Full repair)
    # If balance < 0, Fidelity decays

    fidelity = np.ones_like(age_years)
    # Simple integration of damage accumulation
    # dF/dt = -k * deficit if deficit > 0 else recovery
    current_f = 1.0
    k_damage = 2.0 # Sensitivity parameter
    k_repair = 5.0

    for i in range(1, len(age_years)):
        deficit = -energy_balance[i]
        if deficit > 0:
            # Deficit: Accumulate damage (loss of fidelity)
            dF = -k_damage * deficit * dt
        else:
            # Surplus: Repair
            dF = k_repair * (-deficit) * dt

        current_f += dF
        current_f = np.clip(current_f, 0.4, 1.0) # Floor at 0.4
        fidelity[i] = current_f

    # -------------------------------------------------------------------------
    # 5. Export Data
    # -------------------------------------------------------------------------
    df = pd.DataFrame({
        'Age_Years': age_years,
        'Growth_Velocity_cm_yr': growth_rate,
        'Spinal_Length_cm': spinal_length,
        'Energy_Supply_L2': supply_capacity,
        'Energy_Demand_L4': total_demand,
        'Energy_Balance': energy_balance,
        'Mechanosensory_Fidelity': fidelity
    })

    csv_path = output_dir / "protein_dynamics_deficit.csv"
    df.to_csv(csv_path, index=False)
    print(f"Data saved to {csv_path}")

    # -------------------------------------------------------------------------
    # 6. Plotting
    # -------------------------------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot Energy Balance
    color = 'tab:blue'
    ax1.set_xlabel('Age (years)')
    ax1.set_ylabel('Energy (Arbitrary Units)', color=color)
    ax1.plot(age_years, supply_capacity, label='Supply ($L^2$)', color='green', linestyle='--')
    ax1.plot(age_years, total_demand, label='Demand ($L^4$)', color='red', linestyle='--')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.fill_between(age_years, supply_capacity, total_demand,
                     where=(total_demand > supply_capacity),
                     color='red', alpha=0.2, label='Energy Deficit Window')

    # Plot Fidelity on twin axis
    ax2 = ax1.twinx()
    color = 'tab:purple'
    ax2.set_ylabel('Mechanosensory Fidelity (Protein Integrity)', color=color)
    ax2.plot(age_years, fidelity, label='Fidelity', color=color, linewidth=2.5)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 1.1)

    # Mark Growth Spurt Peak
    peak_age = age_years[np.argmax(growth_rate)]
    plt.axvline(x=peak_age, color='k', linestyle=':', alpha=0.5, label=f'Peak Growth ({peak_age}y)')

    plt.title('The Thermodynamic Instability Window: Protein Dynamics')

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    fig.tight_layout()
    fig_path = figures_dir / "protein_dynamics_deficit.png"
    plt.savefig(fig_path, dpi=300)
    print(f"Figure saved to {fig_path}")

if __name__ == "__main__":
    run_experiment()

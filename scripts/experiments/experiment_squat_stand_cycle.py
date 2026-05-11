#!/usr/bin/env python3
"""
Dynamic Squat-to-Stand Cycle Simulation
=======================================

Models the dynamic transition with time-varying gravity orientation AND time-varying
information field to explicitly calculate energy dissipation terms per cycle.

Author: Dr. Sayuj Krishnan S
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np

# Ensure src is in path
sys.path.append(os.getcwd())

from src.spinalmodes.countercurvature.coupling import CounterCurvatureParams
from src.spinalmodes.countercurvature.info_fields import InfoField1D
from src.spinalmodes.countercurvature.pyelastica_bridge import (
    CounterCurvatureRodSystem,
    compute_U_CC,
)
from scripts.experiments.experiment_utils import StandardExperimentParser

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
# Reusing standard rod parameters
L = 1.0
E0 = 1e6
radius = 0.02
rho = 1000.0
gravity_magnitude = 9.81

# Base biology parameters representing optimal, healthy youth
BASE_PARAMS = CounterCurvatureParams(
    chi_E=0.0,
    chi_kappa=4.0,  # Intrinsic curvature gain
    chi_M=15.0,     # Strong active muscle correction
    chi_tau=0.0,
    scale_length=L
)

def define_squat_stand_trajectory(T_cycle: float = 4.0, dt: float = 0.1, n_elements: int = 50) -> List[Dict]:
    """
    Defines the quasi-static steps for a single squat-to-stand cycle.

    T_cycle=4s.
    theta(t) transitions from 90° (standing, gravity parallel) to 0° (deep squat, gravity perpendicular)
    and back to 90°.
    I(s,t) morphs from S-curve (standing) to C-curve (squat) field.

    Returns a list of dicts containing parameters for each time step.
    """
    n_steps = int(T_cycle / dt)
    times = np.linspace(0, T_cycle, n_steps)

    trajectory = []

    # Grid for information field
    s = np.linspace(0, L, n_elements + 1)

    # Base fields
    # S-curve: standing (sin^2)
    I_standing = np.sin(2 * np.pi * s / L)**2
    # C-curve: squatting (sin)
    I_squatting = np.sin(np.pi * s / L)

    for t in times:
        # Phase goes 0 -> 1 -> 0 over the cycle
        # Standing (t=0, t=T) -> Phase = 0
        # Deep Squat (t=T/2) -> Phase = 1
        phase = 0.5 * (1 - np.cos(2 * np.pi * t / T_cycle))

        # Theta: 90 (standing) -> 0 (squat)
        theta_deg = 90.0 * (1.0 - phase)

        # Morph info field
        I_current = (1 - phase) * I_standing + phase * I_squatting
        dIds = np.gradient(I_current, s)
        info = InfoField1D(s=s, I=I_current, dIds=dIds)

        trajectory.append({
            "time": t,
            "phase": phase,
            "theta_deg": theta_deg,
            "info": info
        })

    return trajectory


def compute_cycle_dissipation(trajectory: List[Dict], n_elements: int = 50) -> Dict[str, float]:
    """
    Computes thermodynamic dissipation terms per cycle using quasi-static stepping.

    η_p: scales with |∂κ/∂t|² during transition
    η_a: scales with (κ - κ_passive)²
    Γ_m: basal cost + activation
    """
    print(f"    Running quasi-static cycle simulation ({len(trajectory)} steps)...")

    total_eta_p_cost = 0.0
    total_eta_a_cost = 0.0
    total_gamma_m_cost = 0.0

    # We will accumulate the integral over time (dt is implicit or handled as diffs)
    dt = trajectory[1]["time"] - trajectory[0]["time"]

    prev_kappa = None

    # Empirical coefficients for dissipation terms
    eta_p_coeff = 1.0e-2
    eta_a_coeff = 1.0e-3
    gamma_m_base = 5.0

    for step in trajectory:
        theta_rad = np.radians(step["theta_deg"])
        base_dir = np.array([np.cos(theta_rad), 0.0, np.sin(theta_rad)])
        normal_dir = np.array([0.0, 1.0, 0.0])

        # Instantiate system (quasi-static approximation: run a short simulation to equilibrium)
        system = CounterCurvatureRodSystem.from_iec(
            info=step["info"],
            params=BASE_PARAMS,
            length=L,
            n_elements=n_elements,
            E0=E0,
            radius=radius,
            rho=rho,
            gravity=gravity_magnitude,
            base_direction=tuple(base_dir),
            normal=tuple(normal_dir)
        )

        # Quick relaxation to equilibrium
        sim_res = system.run_simulation(final_time=0.1, dt=1e-4, save_every=100)

        # Get local curvature
        kappa = sim_res.kappa[-1] # (n_nodes, 3)
        bending_k = kappa[:, 1] # Sagittal

        # 1. Active Maintenance (η_a)
        # (kappa - kappa_passive)^2. Assume kappa_passive ~ 0 for simplicity here.
        eta_a_term = np.sum(bending_k**2) * eta_a_coeff * dt
        total_eta_a_cost += eta_a_term

        # 2. Basal Maintenance (Γ_m)
        # SIRT1/PGC-1a upregulated by phase transition and load
        gamma_m_term = (gamma_m_base + 10.0 * np.mean(np.abs(bending_k))) * dt
        total_gamma_m_cost += gamma_m_term

        # 3. Proprioceptive Rate (η_p)
        if prev_kappa is not None:
            dk_dt = (bending_k - prev_kappa) / dt
            eta_p_term = np.sum(dk_dt**2) * eta_p_coeff * dt
            total_eta_p_cost += eta_p_term

        prev_kappa = bending_k

    return {
        "eta_p_cost": total_eta_p_cost,
        "eta_a_cost": total_eta_a_cost,
        "gamma_m_cost": total_gamma_m_cost,
        "total_cost": total_eta_p_cost + total_eta_a_cost + total_gamma_m_cost
    }


def coupling_decay_model(cycles_per_day: int, chi_0: float = 1.0) -> float:
    """
    Phenomenological exponential decay of coupling strength, reset periodically.
    χ(t) = χ₀·exp(−Δt/τ_decay)

    Averages over a 24-hour period based on N cycles.
    """
    if cycles_per_day <= 0:
        return 0.0

    tau_decay = 2.0 # hours
    T_day = 24.0 # hours

    interval = T_day / cycles_per_day

    # Average coupling over the interval
    # chi_avg = (1 / T_int) * int_0^T_int chi_0 * exp(-t/tau) dt
    chi_avg = (chi_0 * tau_decay / interval) * (1.0 - np.exp(-interval / tau_decay))

    return chi_avg


def run_cycle_frequency_sweep(output_dir: Path, n_elements: int = 50, quick: bool = False):
    """
    Sweeps N=[1,2,5,10,20,50,100] cycles/day and computes time-averaged coupling.
    """
    print(f"Running Frequency Sweep (Quick mode: {quick})")

    if quick:
        freqs = [1, 10, 50]
    else:
        freqs = [1, 2, 5, 10, 20, 50, 100]

    chi_0 = BASE_PARAMS.chi_M
    results = []

    for n in freqs:
        chi_avg = coupling_decay_model(n, chi_0=chi_0)
        retention = chi_avg / chi_0
        results.append({
            "cycles_per_day": n,
            "chi_avg": chi_avg,
            "retention_frac": retention
        })

    # Plot
    plt.figure(figsize=(8, 5))
    ns = [r["cycles_per_day"] for r in results]
    ret = [r["retention_frac"] * 100 for r in results]

    plt.plot(ns, ret, 'bo-', linewidth=2)
    plt.axhline(90, color='r', linestyle='--', label='90% Optimal')
    plt.axvline(3, color='k', linestyle=':', label='Chair sitter (~3/day)')
    plt.axvline(50, color='g', linestyle=':', label='Floor sitter (~50/day)')

    plt.xlabel('Squat-Stand Cycles per Day')
    plt.ylabel('Time-Averaged Coupling Retention (%)')
    plt.title('Coupling Strength vs Cycling Frequency')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "coupling_preservation_curve.png", dpi=300)
    plt.close()

    # Save CSV
    keys = results[0].keys()
    with open(output_dir / "frequency_sweep.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)


def compare_chair_vs_floor(output_dir: Path, n_elements: int = 50, quick: bool = False):
    """
    Compares chair sitting (shallow squat, N=3) vs floor sitting (deep squat, N=50).
    """
    print("Running Chair vs Floor Comparison")

    # In quick mode, we reduce temporal resolution
    dt = 1.0 if quick else 0.2

    # 1. Floor sitting (Deep Squat)
    # T=4s, full 90 -> 0 transition
    trajectory_floor = define_squat_stand_trajectory(T_cycle=4.0, dt=dt, n_elements=n_elements)
    cost_floor = compute_cycle_dissipation(trajectory_floor, n_elements=n_elements)

    # Multiply by daily frequency (N=50)
    total_cost_floor = {k: v * 50 for k, v in cost_floor.items() if k != "total_cost"}
    total_cost_floor["total_cost"] = sum(total_cost_floor.values())

    # 2. Chair sitting (Shallow Squat)
    # T=2s, 90 -> 45 transition only
    trajectory_chair_raw = define_squat_stand_trajectory(T_cycle=2.0, dt=dt, n_elements=n_elements)
    # Modify theta to only go to 45 deg (shallow)
    for step in trajectory_chair_raw:
        if step["theta_deg"] < 45.0:
            step["theta_deg"] = 45.0 + (45.0 - step["theta_deg"]) # Bounce back roughly

    cost_chair = compute_cycle_dissipation(trajectory_chair_raw, n_elements=n_elements)

    # Multiply by daily frequency (N=3)
    total_cost_chair = {k: v * 3 for k, v in cost_chair.items() if k != "total_cost"}
    total_cost_chair["total_cost"] = sum(total_cost_chair.values())

    # Save results
    results = [
        {"lifestyle": "Chair Sitter", "cycles": 3, "type": "Shallow", **total_cost_chair},
        {"lifestyle": "Floor Sitter", "cycles": 50, "type": "Deep", **total_cost_floor}
    ]

    with open(output_dir / "chair_vs_floor_dissipation.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    # Plot breakdown
    labels = [r'Proprioceptive ($\eta_p$)', r'Active Maint. ($\eta_a$)', r'Basal/Metabolic ($\Gamma_m$)']
    chair_vals = [total_cost_chair["eta_p_cost"], total_cost_chair["eta_a_cost"], total_cost_chair["gamma_m_cost"]]
    floor_vals = [total_cost_floor["eta_p_cost"], total_cost_floor["eta_a_cost"], total_cost_floor["gamma_m_cost"]]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(x - width/2, chair_vals, width, label='Chair (N=3/day)')
    ax.bar(x + width/2, floor_vals, width, label='Floor (N=50/day)')

    ax.set_ylabel('Total Daily Dissipation (arb. units)')
    ax.set_title('Thermodynamic Cost Comparison: Chair vs Floor Sitting')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_dir / "dissipation_breakdown.png", dpi=300)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Longevity Squat-Stand Cycle Simulation")
    parser.add_argument("--quick", action="store_true", help="Run a quick smoke test")
    args = parser.parse_args()

    print("=" * 70)
    print("  SQUAT-TO-STAND THERMODYNAMIC CYCLE SIMULATION")
    print("=" * 70)

    output_dir = Path("outputs/thermodynamic_cost/squat_stand_cycle")
    output_dir.mkdir(parents=True, exist_ok=True)

    n_elements = 20 if args.quick else 50

    start_time = time.time()

    # 1. Frequency Sweep (Coupling Decay)
    run_cycle_frequency_sweep(output_dir, n_elements=n_elements, quick=args.quick)

    # 2. Chair vs Floor Comparison (Dissipation breakdown)
    compare_chair_vs_floor(output_dir, n_elements=n_elements, quick=args.quick)

    elapsed = time.time() - start_time
    print(f"\n✅ Simulation complete in {elapsed:.2f}s.")
    print(f"Results saved to {output_dir}")

if __name__ == "__main__":
    main()

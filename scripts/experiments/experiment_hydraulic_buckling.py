"""
Experiment: Hydraulic Buckling — The Inflamed Torsion Pathway.

This script simulates the effect of microgravity-induced hydraulic swelling on
the torsional stiffness of the spine, leading to buckling (Scoliosis).

Core Hypothesis (H_2026_09_01_HydraulicMismatch):
    - Gravity drives lymphatic drainage (Pump).
    - Microgravity causes stagnation and disc swelling (Swelling).
    - Swelling decouples annular fibers, reducing Torsional Stiffness ($GJ$).
    - Reduced $GJ$ causes "Proprioceptive Mismatch": The control system applies
      torques expecting a stiff rod, but the rod is soft, leading to instability.

Dynamics:
    dS/dt = k_in * (1 - S) - k_pump * gravity * S

    GJ(S) = GJ_0 * (1 - alpha * S)

Where:
    S: Swelling state (0 to 1).
    alpha: Sensitivity of stiffness to swelling (e.g., 0.8 = 80% loss).
"""

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from spinalmodes.countercurvature.pyelastica_bridge import (
    CounterCurvatureParams,
    CounterCurvatureRodSystem,
    InfoField1D,
    compute_U_CC,
)

DEFAULT_FIGURES_DIR = Path("outputs/figures")
DEFAULT_REPORTS_DIR = Path("reports")

@dataclass
class HydraulicState:
    """Tracks the hydraulic state of the spinal rod."""
    swelling: float = 0.0  # 0.0 = Normal, 1.0 = Max Swelling
    k_in: float = 0.1      # Inflow rate (Osmotic drive)
    k_pump: float = 0.5    # Pump efficiency (Gravity dependent)
    alpha: float = 0.8     # Stiffness sensitivity (Max 80% loss)

    def update(self, dt: float, gravity: float, pump_assist: float = 0.0) -> float:
        """
        Update swelling state based on gravity and pump assist.

        dS/dt = k_in * (1 - S) - (k_pump * g + pump_assist) * S

        Args:
            dt: Time step.
            gravity: Current gravity (m/s^2).
            pump_assist: Artificial pumping (e.g., vibration/compression).

        Returns:
            New swelling state.
        """
        # Normalized gravity effect (assuming 9.81 is max efficiency)
        g_norm = gravity / 9.81
        pump_term = (self.k_pump * g_norm + pump_assist) * self.swelling
        inflow_term = self.k_in * (1.0 - self.swelling)

        dS = (inflow_term - pump_term) * dt
        self.swelling = np.clip(self.swelling + dS, 0.0, 1.0)
        return self.swelling

    @property
    def stiffness_modifier(self) -> float:
        """Return the multiplicative factor for Torsional Stiffness (GJ)."""
        return 1.0 - (self.alpha * self.swelling)


def run_hydraulic_cycle(
    swelling_state: HydraulicState,
    gravity: float,
    pump_assist: float = 0.0,
    cycle_duration: float = 1.0, # Hours in simulation time
    dt_sim: float = 1e-4, # Physics timestep
    n_elements: int = 30,
    length: float = 0.5,
    active_curvature: float = 1.0,
) -> Dict[str, float]:
    """
    Run a simulation cycle with hydraulic coupling.

    Args:
        swelling_state: Current hydraulic state object.
        gravity: Gravity value.
        pump_assist: Artificial pump value.
        cycle_duration: Duration of this cycle (hours).

    Returns:
        Dictionary of metrics (Cobb, Torsion, Swelling, Energy).
    """
    # 1. Update Swelling State (Macro-step)
    # We assume swelling evolves slower than physics, so we update it once per cycle
    # or we could update it every physics step. For now, update once per cycle for stability.
    # Time unit for swelling is Hours.
    swelling = swelling_state.update(dt=cycle_duration, gravity=gravity, pump_assist=pump_assist)
    stiffness_mod = swelling_state.stiffness_modifier

    # 2. Setup Rod System
    # Standard parameters
    s = np.linspace(0, length, n_elements + 1)
    # Info field (Gaussian bump)
    I = 0.5 + 0.5 * np.exp(-0.5 * ((s - 0.5 * length) / (0.1 * length)) ** 2)
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    params = CounterCurvatureParams(
        chi_kappa=active_curvature * 5.0, # Scaling
        chi_tau=0.0,
        chi_E=0.0,
        chi_M=0.0,
        scale_length=length,
    )

    # Initial shape: Slight kyphosis
    kappa_gen = np.zeros((3, n_elements + 1))
    kappa_gen[0, :] = 2.0  # Sagittal kyphosis

    # Create Rod
    rod_system = CounterCurvatureRodSystem.from_iec(
        info=info, params=params, length=length, n_elements=n_elements,
        E0=1e6, rho=1000.0, radius=0.01, kappa_gen=kappa_gen,
        gravity=gravity, stiffness_anisotropy=2.0, # Default Anisotropy
    )

    # 3. Apply Hydraulic Damage (Modify Torsional Stiffness)
    # rod.bend_matrix is (3, 3, n_elems-1)
    # index [2, 2] is Torsion (d3) in PyElastica's local frame?
    # Wait, PyElastica convention:
    # d3 is tangent.
    # Bend matrix is usually defined in material frame d1, d2, d3.
    # Stored as (3, 3, n_elem-1).
    # Diagonal elements are B11, B22, B33.
    # B33 corresponds to torsion (twist about d3).

    # Apply modifier to B33
    rod_system.rod.bend_matrix[2, 2, :] *= stiffness_mod

    # 4. Run Physics Simulation
    # We run for a short physical time to find equilibrium
    # The 'cycle_duration' passed to update() is biological time (hours)
    # The simulation time is mechanical relaxation time (seconds)
    relaxation_time = 0.5

    result = rod_system.run_simulation(
        final_time=relaxation_time,
        dt=dt_sim,
        save_every=5000,
        gravity=gravity,
        boundary_condition="fixed",
        progress_bar=False,
    )

    # 5. Compute Metrics
    sim_metrics = result.compute_final_metrics()

    # Energy Calculation
    # Note: compute_U_CC assumes straight rod stiffness.
    # So U_elastic_straight will use the *original* stiffness if passed directly.
    # But PyElastica computes energy using the *modified* stiffness.
    # This difference is the "Proprioceptive Mismatch".

    energies = compute_U_CC(result, info, params, gravity=gravity, rho=1000.0, E0=1e6)

    # Proprioceptive Mismatch Energy = U_elastic (Actual) - U_elastic_straight (Expected/Reference)
    # Note: U_elastic_straight in compute_U_CC uses the rod parameters passed to it.
    # If we want U_elastic_straight to represent the "Healthy" state, we should NOT pass the modified stiffness.
    # compute_U_CC calculates B_base from E0. It doesn't know about our manual modification to bend_matrix.
    # So 'U_elastic_straight' returned by compute_U_CC IS the "Healthy Reference" energy (assuming anisotropy=2.0).
    # And 'U_elastic' (from result.final_energies) IS the "Actual Soft" energy.

    U_actual = energies["U_elastic"]
    U_expected = energies["U_elastic_straight"]
    mismatch = U_actual - U_expected

    return {
        "swelling": swelling,
        "stiffness_mod": stiffness_mod,
        "cobb_angle": sim_metrics.get("cobb_angle", 0.0),
        "max_torsion": sim_metrics.get("max_torsion", 0.0),
        "S_lat": sim_metrics.get("S_lat", 0.0),
        "U_actual": U_actual,
        "U_expected": U_expected,
        "mismatch_energy": mismatch,
    }


def run_experiment(
    duration_hours: float = 72.0,
    dt_hours: float = 1.0,
    quick_test: bool = False,
    figures_dir: Path = DEFAULT_FIGURES_DIR,
    reports_dir: Path = DEFAULT_REPORTS_DIR,
):
    """
    Run the full hydraulic buckling experiment across 3 scenarios.

    Args:
        duration_hours: Total biological time to simulate.
        dt_hours: Time step for swelling update.
        quick_test: If True, reduce duration and resolution for testing.
    """
    if quick_test:
        duration_hours = 6.0
        dt_hours = 2.0
        n_elements = 10
    else:
        n_elements = 30

    figures_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(f"EXPERIMENT: Hydraulic Buckling (Duration={duration_hours}h)")
    print("=" * 80)

    scenarios = [
        {"name": "Earth (1G)", "gravity": 9.81, "pump": 0.0, "color": "green"},
        {"name": "Space (0G)", "gravity": 0.0, "pump": 0.0, "color": "red"},
        {"name": "Rescue (0G+Pump)", "gravity": 0.0, "pump": 5.0, "color": "blue"}, # Pump compensates
    ]

    results = {}

    for scen in scenarios:
        name = scen["name"]
        g = scen["gravity"]
        p = scen["pump"]
        print(f"Running Scenario: {name} (g={g}, pump={p})")

        # Reset State
        state = HydraulicState(swelling=0.1) # Start healthy (low swelling)

        time_points = []
        data_points = []

        t = 0.0
        while t <= duration_hours:
            metrics = run_hydraulic_cycle(
                swelling_state=state,
                gravity=g,
                pump_assist=p,
                cycle_duration=dt_hours,
                n_elements=n_elements,
            )

            # Record
            metrics["time"] = t
            data_points.append(metrics)
            time_points.append(t)

            t += dt_hours

            # Print progress
            if not quick_test and t % 12 == 0:
                print(f"  t={t:3.0f}h | S={metrics['swelling']:.2f} | Cobb={metrics['cobb_angle']:.1f}")

        results[name] = data_points

    # --- Analysis & Plotting ---
    print("\nGenerating Plots...")

    fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

    # 1. Swelling Dynamics
    ax = axes[0]
    for scen in scenarios:
        name = scen["name"]
        data = results[name]
        t = [d["time"] for d in data]
        s = [d["swelling"] for d in data]
        ax.plot(t, s, label=name, color=scen["color"], linewidth=2)

    ax.set_ylabel("Swelling State (S)")
    ax.set_title("Hydraulic Swelling Dynamics")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Stiffness Modifier (Effective GJ)
    ax = axes[1]
    for scen in scenarios:
        name = scen["name"]
        data = results[name]
        t = [d["time"] for d in data]
        mod = [d["stiffness_mod"] for d in data] # 1.0 = Normal, <1.0 = Soft
        ax.plot(t, mod, label=name, color=scen["color"], linestyle="--")

    ax.set_ylabel("Torsional Stiffness Factor")
    ax.set_title("Mechanical Degradation")
    ax.grid(True, alpha=0.3)

    # 3. Cobb Angle (Buckling)
    ax = axes[2]
    for scen in scenarios:
        name = scen["name"]
        data = results[name]
        t = [d["time"] for d in data]
        cobb = [d["cobb_angle"] for d in data]
        ax.plot(t, cobb, label=name, color=scen["color"], linewidth=2)

    ax.set_ylabel("Cobb Angle (deg)")
    ax.set_xlabel("Time in Microgravity (Hours)")
    ax.set_title("Resulting Spinal Curvature")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = figures_dir / "hydraulic_buckling_dynamics.png"
    plt.savefig(plot_path)
    print(f"Saved Plot: {plot_path}")

    # --- Generate Report ---
    report_path = reports_dir / "hydraulic_buckling_report.md"
    plot_reference = Path(os.path.relpath(plot_path, start=report_path.parent))
    with open(report_path, "w") as f:
        f.write("# Hydraulic Buckling Experiment Report\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Hypothesis: The Inflamed Torsion Pathway\n")
        f.write("Microgravity leads to hydraulic stagnation (swelling), which degrades annular fibers.\n")
        f.write("This reduction in Torsional Stiffness ($GJ$) causes the spine to buckle under active muscle tone.\n\n")

        f.write("## Results Summary\n\n")
        f.write("| Scenario | Final Swelling | Final Stiffness | Final Cobb Angle | Mismatch Energy |\n")
        f.write("|----------|----------------|-----------------|------------------|-----------------|\n")

        for scen in scenarios:
            name = scen["name"]
            last = results[name][-1]
            f.write(f"| {name} | {last['swelling']:.2f} | {last['stiffness_mod']:.2f} | {last['cobb_angle']:.1f} | {last['mismatch_energy']:.2e} |\n")

        f.write("\n## Proprioceptive Mismatch\n")
        f.write("The 'Mismatch Energy' represents the difference between the actual elastic energy stored in the soft rod ")
        f.write("and the energy the organism 'expects' (based on a healthy stiffness reference).\n")
        f.write("A large positive mismatch indicates the system is 'softer than expected', leading to gain errors.\n\n")

        f.write(f"![Dynamics]({plot_reference.as_posix()})\n")

    print(f"Saved Report: {report_path}")
    plt.close(fig)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick-test", action="store_true", help="Run fast simulation for testing")
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=DEFAULT_FIGURES_DIR,
        help="Directory for generated figures.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS_DIR,
        help="Directory for generated reports.",
    )
    args = parser.parse_args()

    run_experiment(
        quick_test=args.quick_test,
        figures_dir=args.figures_dir,
        reports_dir=args.reports_dir,
    )

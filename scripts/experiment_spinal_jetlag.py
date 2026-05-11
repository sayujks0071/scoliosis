"""
Experiment: Spinal Jetlag — Time-Dependent Learning Rate Simulation.

This script implements Phase 2, Weeks 5-7 of the Gravity Optimization schedule.
It introduces time-varying information-curvature coupling modulated by a circadian
clock, and simulates desynchronization ("jetlag") effects on spinal alignment.

Core model:
    chi_kappa(t) = chi_0 * (1 + A * cos(omega * t + phi))

where:
    - chi_0: baseline coupling strength
    - A: circadian amplitude (modulation depth, 0 to 1)
    - omega: circadian angular frequency (2*pi / T_circadian)
    - phi: phase offset between gravity loading and clock

When gravity acts as a Zeitgeber, the mechanical loading schedule entrains the
circadian clock (phi -> 0, constructive interference). In "jetlag" conditions
(e.g. microgravity, bed rest, shift work), the clock drifts (phi -> pi),
creating destructive interference that suppresses the shape-maintenance signal.

Experimental conditions:
    1. Entrained (phi=0): Clock and gravity in phase — optimal adaptation
    2. Free-running (phi varies): Clock drifts — gradual geometric degradation
    3. Jetlagged (phi=pi): Anti-phase — worst-case, rapid scoliosis onset
    4. Microgravity (g->0): Gravity Zeitgeber removed, clock amplitude decays

Hypothesis (H_2026_02_17_SpinalJetlag):
    Phase coherence (phi ~ 0) maximises adaptation.
    Destructive interference (phi ~ pi) suppresses shape correction.
    Microgravity removes the Zeitgeber, causing amplitude decay and geometric drift.

References:
    - Research Schedule Phase 2, Weeks 5-7
    - Hypothesis Register: H_2026_02_17 series
    - "Spinal Jetlag" concept from weekly synthesis 2026-02
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime

__version__ = "1.0.1"
from pathlib import Path
from typing import Dict, List

import numpy as np

sys.path.append(str(Path(__file__).parent.parent / "src"))

from spinalmodes.countercurvature.coupling import CounterCurvatureParams
from spinalmodes.countercurvature.info_fields import InfoField1D
from spinalmodes.countercurvature.pyelastica_bridge import (
    CounterCurvatureRodSystem,
    compute_U_CC,
    verify_pyelastica_installation,
)

# ---------------------------------------------------------------------------
# Circadian coupling model
# ---------------------------------------------------------------------------

def chi_kappa_circadian(
    t: float,
    chi_0: float,
    amplitude: float,
    T_circadian: float = 24.0,
    phi: float = 0.0,
) -> float:
    """Compute time-varying chi_kappa with circadian modulation.

    Parameters
    ----------
    t : float
        Time (in hours for biological interpretation, seconds for simulation).
    chi_0 : float
        Baseline coupling strength.
    amplitude : float
        Modulation depth (0 = constant, 1 = full modulation).
    T_circadian : float
        Circadian period (same units as t).
    phi : float
        Phase offset between gravity loading and clock (radians).
        phi=0 : entrained (constructive)
        phi=pi : jetlagged (destructive)

    Returns
    -------
    float
        Instantaneous chi_kappa value.
    """
    omega = 2.0 * np.pi / T_circadian
    return chi_0 * (1.0 + amplitude * np.cos(omega * t + phi))


def entrainment_strength(
    K_ent: float,
    gravity: float,
    g_ref: float = 9.81,
) -> float:
    """Compute gravitational entrainment strength.

    The gravity vector acts as a Zeitgeber that entrains the spinal clock.
    Entrainment strength scales with the gravity ratio.

    Parameters
    ----------
    K_ent : float
        Coupling constant for gravity-clock entrainment.
    gravity : float
        Current gravitational acceleration.
    g_ref : float
        Reference gravity (Earth surface).

    Returns
    -------
    float
        Effective entrainment strength E_mech.
    """
    return K_ent * (gravity / g_ref)


def clock_amplitude_decay(
    A_0: float,
    E_mech: float,
    t: float,
    tau_decay: float = 48.0,
) -> float:
    """Model circadian amplitude decay when entrainment is weak.

    In the absence of gravitational Zeitgeber (microgravity), the clock
    amplitude decays exponentially towards a free-running baseline.

    Parameters
    ----------
    A_0 : float
        Initial circadian amplitude.
    E_mech : float
        Entrainment strength (0 = no entrainment).
    t : float
        Time since loss of entrainment.
    tau_decay : float
        Decay time constant (same units as t).

    Returns
    -------
    float
        Current circadian amplitude.
    """
    # Steady-state amplitude maintained by entrainment
    A_steady = A_0 * min(E_mech, 1.0)
    # Decay from initial to steady-state
    return A_steady + (A_0 - A_steady) * np.exp(-t / tau_decay)


# ---------------------------------------------------------------------------
# Multi-cycle simulation
# ---------------------------------------------------------------------------

def run_jetlag_cycle(
    chi_kappa_t: float,
    gravity: float,
    length: float = 0.5,
    n_elements: int = 50,
    E0: float = 1e6,
    rho: float = 1000.0,
    radius: float = 0.01,
    cycle_duration: float = 0.5,
    dt: float = 1e-5,
) -> Dict[str, float]:
    """Run a single quasi-static cycle with given instantaneous chi_kappa.

    Each cycle represents a "snapshot" of the mechanical state at a particular
    phase of the circadian rhythm. The rod relaxes to quasi-static equilibrium
    under the current coupling strength and gravity.

    Parameters
    ----------
    chi_kappa_t : float
        Instantaneous information-curvature coupling.
    gravity : float
        Gravitational acceleration for this cycle.
    length : float
        Rod length (metres).
    n_elements : int
        Number of elements.
    E0 : float
        Young's modulus (Pa).
    rho : float
        Density (kg/m^3).
    radius : float
        Rod radius (metres).
    cycle_duration : float
        Simulation time per cycle (seconds).
    dt : float
        Time step.

    Returns
    -------
    dict
        Metrics for this cycle (cobb_angle, S_lat, torsion, U_CC, etc.)
    """
    s = np.linspace(0, length, n_elements + 1)
    I = 0.5 + 0.5 * np.exp(-0.5 * ((s - 0.5 * length) / (0.1 * length)) ** 2)
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    params = CounterCurvatureParams(
        chi_kappa=chi_kappa_t,
        chi_tau=0.0,
        chi_E=0.0,
        chi_M=0.0,
        scale_length=length,
    )

    kappa_gen = np.zeros((3, n_elements + 1))
    kappa_gen[0, :] = 2.0  # Sagittal kyphosis

    rod_system = CounterCurvatureRodSystem.from_iec(
        info=info, params=params, length=length, n_elements=n_elements,
        E0=E0, rho=rho, radius=radius, kappa_gen=kappa_gen,
        gravity=gravity, stiffness_anisotropy=2.0,
    )

    result = rod_system.run_simulation(
        final_time=cycle_duration, dt=dt, save_every=5000,
        gravity=gravity, boundary_condition="fixed", progress_bar=False,
    )

    sim_metrics = result.compute_final_metrics()
    cost = compute_U_CC(result, info, params, gravity, rho, E0)

    return {
        "cobb_angle": sim_metrics.get("cobb_angle", 0.0),
        "max_torsion": sim_metrics.get("max_torsion", 0.0),
        "S_lat": sim_metrics.get("S_lat", 0.0),
        "max_curvature": sim_metrics.get("max_curvature", 0.0),
        "U_CC": cost["U_CC"],
        "U_info": cost["U_info"],
        "info_gain_ratio": cost["info_gain_ratio"],
    }


def run_spinal_jetlag_experiment(
    out_file: str,
    conditions: List[Dict],
    n_cycles: int = 24,
    T_circadian: float = 24.0,
    n_elements: int = 30,
    cycle_duration: float = 0.5,
):
    """Run the full spinal jetlag multi-condition experiment.

    Parameters
    ----------
    out_file : str
        Path to output CSV.
    conditions : list of dict
        Each dict specifies a condition:
        {name, chi_0, amplitude, phi, gravity, K_ent}
    n_cycles : int
        Number of circadian cycles to simulate.
    T_circadian : float
        Circadian period (hours, used for cycling chi_kappa).
    n_elements : int
        Rod elements.
    cycle_duration : float
        Mechanical relaxation time per cycle (seconds).
    """
    verify_pyelastica_installation(exit_on_fail=True)

    print("=" * 100)
    print("EXPERIMENT: Spinal Jetlag — Time-Dependent Learning Rate")
    print("=" * 100)
    print(f"Conditions: {len(conditions)}")
    print(f"Cycles per condition: {n_cycles}")
    print(f"Circadian period: {T_circadian} hours")
    print(f"Output: {out_file}")
    print("=" * 100)

    out_dir = os.path.dirname(out_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    fieldnames = [
        "timestamp", "condition", "cycle", "t_hours",
        "chi_kappa_t", "amplitude_t", "phi",
        "gravity", "cobb_angle", "max_torsion", "S_lat",
        "max_curvature", "U_CC", "U_info", "info_gain_ratio",
        "runtime_sec",
    ]

    file_exists = os.path.isfile(out_file)
    with open(out_file, mode="a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        for cond in conditions:
            name = cond["name"]
            chi_0 = cond["chi_0"]
            A_0 = cond["amplitude"]
            phi = cond["phi"]
            grav = cond["gravity"]
            K_ent = cond.get("K_ent", 1.0)

            print(f"\n--- Condition: {name} ---")
            print(f"    chi_0={chi_0}, A={A_0}, phi={phi:.2f}, g={grav}, K_ent={K_ent}")

            # Compute entrainment
            E_mech = entrainment_strength(K_ent, grav)

            for cycle in range(n_cycles):
                t0_wall = time.time()

                # Current time in hours
                t_hours = cycle * (T_circadian / n_cycles)

                # Clock amplitude (may decay in microgravity)
                A_t = clock_amplitude_decay(A_0, E_mech, t_hours)

                # Instantaneous coupling
                chi_t = chi_kappa_circadian(t_hours, chi_0, A_t, T_circadian, phi)

                # Run mechanical cycle
                metrics = run_jetlag_cycle(
                    chi_kappa_t=chi_t,
                    gravity=grav,
                    n_elements=n_elements,
                    cycle_duration=cycle_duration,
                )

                t1_wall = time.time()

                row = {
                    "timestamp": datetime.now().isoformat(),
                    "condition": name,
                    "cycle": cycle,
                    "t_hours": round(t_hours, 2),
                    "chi_kappa_t": round(chi_t, 4),
                    "amplitude_t": round(A_t, 4),
                    "phi": round(phi, 4),
                    "gravity": grav,
                    "cobb_angle": round(metrics["cobb_angle"], 4),
                    "max_torsion": round(metrics["max_torsion"], 6),
                    "S_lat": round(metrics["S_lat"], 6),
                    "max_curvature": round(metrics["max_curvature"], 4),
                    "U_CC": round(metrics["U_CC"], 6),
                    "U_info": round(metrics["U_info"], 6),
                    "info_gain_ratio": round(metrics["info_gain_ratio"], 6),
                    "runtime_sec": round(t1_wall - t0_wall, 3),
                }
                writer.writerow(row)
                csvfile.flush()

                if cycle % 4 == 0:
                    print(
                        f"  cycle {cycle:3d} | t={t_hours:6.1f}h | "
                        f"chi_k={chi_t:7.3f} | A={A_t:.3f} | "
                        f"Cobb={metrics['cobb_angle']:6.2f} | "
                        f"S_lat={metrics['S_lat']:.4f}"
                    )

    print("\n" + "=" * 100)
    print("Experiment complete.")
    generate_jetlag_report(out_file)


def generate_jetlag_report(csv_file: str):
    """Generate a Markdown report from the jetlag experiment."""
    md_file = str(Path(csv_file).with_suffix(".md"))

    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("No data to report.")
        return

    with open(md_file, "w") as f:
        f.write("# Spinal Jetlag Experiment Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Model\n\n")
        f.write("$$\\chi_{\\kappa}(t) = \\chi_0 \\cdot (1 + A(t) \\cdot \\cos(\\omega t + \\phi))$$\n\n")
        f.write("- **Entrained** (phi=0): Clock and gravity in phase\n")
        f.write("- **Free-running**: Clock drifts gradually\n")
        f.write("- **Jetlagged** (phi=pi): Anti-phase, destructive interference\n")
        f.write("- **Microgravity**: Zeitgeber removed, amplitude decays\n\n")

        # Summary per condition
        from collections import defaultdict
        cond_data = defaultdict(list)
        for r in rows:
            cond_data[r["condition"]].append(r)

        f.write("## Summary by Condition\n\n")
        f.write("| Condition | Cycles | Final Cobb | Max Cobb | Mean S_lat | Mean U_CC |\n")
        f.write("|-----------|--------|------------|----------|------------|----------|\n")

        for cond_name, cond_rows in cond_data.items():
            n = len(cond_rows)
            final_cobb = float(cond_rows[-1]["cobb_angle"])
            max_cobb = max(float(r["cobb_angle"]) for r in cond_rows)
            mean_slat = np.mean([float(r["S_lat"]) for r in cond_rows])
            mean_ucc = np.mean([float(r["U_CC"]) for r in cond_rows])
            f.write(
                f"| {cond_name} | {n} | {final_cobb:.2f} | {max_cobb:.2f} | "
                f"{mean_slat:.4f} | {mean_ucc:.4f} |\n"
            )

        # Time series for each condition
        f.write("\n## Time Series (every 4th cycle)\n\n")
        for cond_name, cond_rows in cond_data.items():
            f.write(f"\n### {cond_name}\n\n")
            f.write("| Cycle | t (h) | chi_kappa | Amplitude | Cobb | S_lat |\n")
            f.write("|-------|-------|-----------|-----------|------|-------|\n")
            for r in cond_rows[::4]:
                f.write(
                    f"| {r['cycle']} | {r['t_hours']} | "
                    f"{float(r['chi_kappa_t']):.3f} | {float(r['amplitude_t']):.3f} | "
                    f"{float(r['cobb_angle']):.2f} | {float(r['S_lat']):.4f} |\n"
                )

        # Key findings
        f.write("\n## Key Predictions\n\n")
        f.write("1. **Phase Coherence**: Entrained condition should show lowest Cobb angles\n")
        f.write("2. **Destructive Interference**: Jetlagged (phi=pi) should show highest Cobb angles\n")
        f.write("3. **Microgravity Drift**: Clock amplitude decays → progressive geometric error\n")
        f.write("4. **Critical Phase**: Scoliosis onset at phi > pi/2 (90 degrees of mismatch)\n")

    print(f"Report generated: {md_file}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Spinal Jetlag: Time-Dependent Learning Rate Experiment"
    )
    parser.add_argument(
        "--out-file", type=str,
        default="outputs/spinal_jetlag/jetlag_cycles.csv",
    )
    parser.add_argument("--quick-test", action="store_true")
    parser.add_argument("--n-cycles", type=int, default=24)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.quick_test:
        conditions = [
            {"name": "entrained", "chi_0": 10.0, "amplitude": 0.5,
             "phi": 0.0, "gravity": 9.81, "K_ent": 1.0},
            {"name": "jetlagged", "chi_0": 10.0, "amplitude": 0.5,
             "phi": np.pi, "gravity": 9.81, "K_ent": 1.0},
        ]
        n_cycles = 8
        n_elements = 20
        cycle_duration = 0.1
    else:
        conditions = [
            # 1. Entrained: phi=0, full gravity, strong entrainment
            {"name": "entrained", "chi_0": 10.0, "amplitude": 0.5,
             "phi": 0.0, "gravity": 9.81, "K_ent": 1.0},

            # 2. Mild phase shift (45 degrees)
            {"name": "phase_shift_45", "chi_0": 10.0, "amplitude": 0.5,
             "phi": np.pi / 4, "gravity": 9.81, "K_ent": 1.0},

            # 3. Moderate phase shift (90 degrees)
            {"name": "phase_shift_90", "chi_0": 10.0, "amplitude": 0.5,
             "phi": np.pi / 2, "gravity": 9.81, "K_ent": 1.0},

            # 4. Fully jetlagged: phi=pi, anti-phase
            {"name": "jetlagged", "chi_0": 10.0, "amplitude": 0.5,
             "phi": np.pi, "gravity": 9.81, "K_ent": 1.0},

            # 5. Microgravity: g ~ 0, weak entrainment, amplitude decays
            {"name": "microgravity", "chi_0": 10.0, "amplitude": 0.5,
             "phi": 0.0, "gravity": 0.01, "K_ent": 1.0},

            # 6. Microgravity + jetlag: worst case
            {"name": "microgravity_jetlag", "chi_0": 10.0, "amplitude": 0.5,
             "phi": np.pi, "gravity": 0.01, "K_ent": 1.0},

            # 7. Control: no circadian modulation (A=0)
            {"name": "constant_chi", "chi_0": 10.0, "amplitude": 0.0,
             "phi": 0.0, "gravity": 9.81, "K_ent": 1.0},

            # 8. High coupling + jetlag (pathological)
            {"name": "high_chi_jetlag", "chi_0": 20.0, "amplitude": 0.5,
             "phi": np.pi, "gravity": 9.81, "K_ent": 1.0},
        ]
        n_cycles = args.n_cycles
        n_elements = 30
        cycle_duration = 0.5

    run_spinal_jetlag_experiment(
        out_file=args.out_file,
        conditions=conditions,
        n_cycles=n_cycles,
        n_elements=n_elements,
        cycle_duration=cycle_duration,
    )

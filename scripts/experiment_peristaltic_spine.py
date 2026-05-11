"""
Experiment: Peristaltic Spine — Spatiotemporal Phase Dynamics.

This script implements Phase 2b of the Gravity Optimization schedule.
It extends the "Spinal Jetlag" concept (temporal mismatch) to "Spinal Peristalsis"
(spatiotemporal mismatch), modelling the spine as a chain of coupled oscillators.

Core Hypothesis (H_2026_03_14_Peristaltic_Buckling):
    Buckling is driven by "Phase Frustration" between the metabolic clock wave
    (segmentation/growth) and the mechanical load.
    A traveling stiffness wave (peristalsis) or a standing wave of disorder
    can resonate with buckling modes.

Model:
    chi_kappa(s, t) = chi_0 * (1 + A * cos(k * s - omega * t + phi))

Parameters:
    - k (wavenumber): Spatial frequency of the metabolic/stiffness variation.
        k=0: Global synchronization (Jetlag model).
        k > 0: Spatial desynchronization.
    - omega (frequency): Temporal frequency.
        omega=0: Frozen spatial disorder (Standing wave).
        omega > 0: Traveling wave.
    - v (wave speed): v = omega / k.

References:
    - Research Schedule Phase 2b
    - "Spinal Jetlag" (Phase 2a)
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np

# Ensure src is in path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Check for PyElastica before importing heavily
try:
    import elastica as ea
    PYELASTICA_AVAILABLE = True
except ImportError:
    PYELASTICA_AVAILABLE = False

from spinalmodes.countercurvature.coupling import CounterCurvatureParams
from spinalmodes.countercurvature.info_fields import InfoField1D
from spinalmodes.countercurvature.pyelastica_bridge import (
    CounterCurvatureRodSystem,
    SimulationResult,
    compute_U_CC,
    verify_pyelastica_installation,
)

# ---------------------------------------------------------------------------
# Peristaltic Wave Callback
# ---------------------------------------------------------------------------

if PYELASTICA_AVAILABLE:
    class PeristalticWaveCallback(ea.CallBackBaseClass):
        """Updates chi_kappa spatially based on a wave equation."""

        def __init__(self, system_wrapper: CounterCurvatureRodSystem, wave_params: Dict[str, float], step_skip: int = 1):
            super().__init__()
            self.system_wrapper = system_wrapper
            self.wp = wave_params
            self.every = step_skip
            # Store initial base magnitude (assuming scalar start)
            self.chi_0 = float(system_wrapper.params.chi_kappa)
            self.s = system_wrapper.info_field.s  # Spatial grid (n_nodes,)

        def make_callback(self, system, time, current_step):
            if current_step % self.every == 0:
                k = self.wp.get('k', 0.0)
                omega = self.wp.get('omega', 0.0)
                phi = self.wp.get('phi', 0.0)
                A = self.wp.get('amplitude', 0.0)

                # Wave Equation: modulation(s,t) = 1 + A * cos(k*s - omega*t + phi)
                # s is array, time is scalar
                phase = k * self.s - omega * time + phi
                modulation = 1.0 + A * np.cos(phase)

                # Compute new spatially varying chi_kappa
                new_chi = self.chi_0 * modulation

                # Update params
                # We assume CounterCurvatureParams supports array inputs (updated in Phase 2a refactor)
                new_params = self.system_wrapper.params._replace(chi_kappa=new_chi)

                # Apply to rod
                self.system_wrapper.update_rest_curvature(new_params)

# ---------------------------------------------------------------------------
# Simulation Runner
# ---------------------------------------------------------------------------

def run_peristaltic_cycle(
    wave_params: Dict[str, float],
    gravity: float = 9.81,
    chi_0: float = 10.0,
    length: float = 0.5,
    n_elements: int = 40,
    E0: float = 1e6,
    rho: float = 1000.0,
    radius: float = 0.01,
    duration: float = 1.0,
    dt: float = 1e-5,
) -> Dict[str, float]:
    """Run a dynamic simulation with a peristaltic stiffness/curvature wave.

    Args:
        wave_params: Dict with k, omega, phi, amplitude.
        gravity: Gravity acceleration.
        chi_0: Baseline coupling strength.
        length: Rod length.
        n_elements: Number of elements.
        duration: Simulation time.

    Returns:
        Dict of final metrics.
    """

    # 1. Setup Info Field (Generic Gaussian bump to define the "Information Spine")
    s = np.linspace(0, length, n_elements + 1)
    I = 0.5 + 0.5 * np.exp(-0.5 * ((s - 0.5 * length) / (0.1 * length)) ** 2)
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # 2. Initial Params (Scalar start)
    params = CounterCurvatureParams(
        chi_kappa=chi_0,
        chi_tau=0.0,
        chi_E=0.0,
        chi_M=0.0,
        scale_length=length,
    )

    # 3. Geometric Setup
    kappa_gen = np.zeros((3, n_elements + 1))
    kappa_gen[1, :] = 2.0  # Natural Kyphosis
    kappa_gen[0, :] = 0.1  # Small Lateral Defect to seed buckling

    rod_system = CounterCurvatureRodSystem.from_iec(
        info=info, params=params, length=length, n_elements=n_elements,
        E0=E0, rho=rho, radius=radius, kappa_gen=kappa_gen,
        gravity=gravity, stiffness_anisotropy=2.0,
    )

    # 4. Prepare PyElastica System
    # We need to manually construct the system to attach our custom callback
    # Reuse the logic inside run_simulation but we need to inject the callback
    # Since run_simulation doesn't accept arbitrary callbacks easily, we will modify
    # how we call it or use a custom runner.
    # Actually, pyelastica_bridge.run_simulation assumes CircadianParams for modulation.
    # We need to bypass that or trick it.
    # BUT: run_simulation is convenient.
    # Let's inspect pyelastica_bridge.py again.
    # It has a localized class CCCallback.
    # It takes `circadian_params` (dataclass).

    # EASIER APPROACH: Use the PyElastica system construction directly here,
    # mirroring `CounterCurvatureRodSystem.run_simulation`.

    final_time = duration

    class PeristalticSystem(ea.BaseSystemCollection, ea.Constraints, ea.Forcing, ea.Damping, ea.CallBacks):
        pass

    system = PeristalticSystem()
    system.append(rod_system.rod)

    # Fixed BC
    system.constrain(rod_system.rod).using(
        ea.OneEndFixedBC,
        constrained_position_idx=(0,),
        constrained_director_idx=(0,)
    )

    # Gravity
    system.add_forcing_to(rod_system.rod).using(ea.GravityForces, acc_gravity=np.array([0.0, 0.0, -gravity]))

    # Damping
    system.dampen(rod_system.rod).using(ea.AnalyticalLinearDamper, damping_constant=5.0, time_step=dt)

    # Diagnostics
    results = {"time": [], "centerline": [], "kappa": []}
    class DiagnosticCallback(ea.CallBackBaseClass):
        def __init__(self, step_skip, res_dict):
            super().__init__()
            self.every = step_skip
            self.res = res_dict
        def make_callback(self, system, time, current_step):
            if current_step % self.every == 0:
                self.res["time"].append(time)
                self.res["centerline"].append(system.position_collection.copy().T)
                self.res["kappa"].append(system.kappa.copy().T)

    save_every = max(1, int(duration/dt/50)) # Save 50 frames
    system.collect_diagnostics(rod_system.rod).using(DiagnosticCallback, step_skip=save_every, res_dict=results)

    # PERISTALTIC CALLBACK
    system.collect_diagnostics(rod_system.rod).using(
        PeristalticWaveCallback,
        system_wrapper=rod_system,
        wave_params=wave_params,
        step_skip=1 # Update every step
    )

    system.finalize()
    timestepper = ea.PositionVerlet()
    ea.integrate(timestepper, system, final_time, int(final_time/dt), progress_bar=False)

    # 5. Process Results
    # Create a SimulationResult object manually to reuse compute methods
    # Need to pad kappa
    kappa_raw = np.array(results["kappa"])
    if len(kappa_raw) > 0:
        n_time, n_internal, n_dim = kappa_raw.shape
        padded_kappa = np.zeros((n_time, n_elements + 1, n_dim))
        padded_kappa[:, 1:-1, :] = kappa_raw
        padded_kappa[:, 0, :] = kappa_raw[:, 0, :]
        padded_kappa[:, -1, :] = kappa_raw[:, -1, :]
    else:
        padded_kappa = np.zeros((0, n_elements+1, 3))

    sim_result = SimulationResult(
        time=np.array(results["time"]),
        centerline=np.array(results["centerline"]),
        kappa=padded_kappa,
        info_field=info,
        final_energies={} # Skip for now
    )

    metrics = sim_result.compute_final_metrics()

    # Add energies
    cost = compute_U_CC(sim_result, info, params, gravity, rho, E0)
    metrics.update(cost)

    return metrics


# ---------------------------------------------------------------------------
# Experiment Driver
# ---------------------------------------------------------------------------

def run_experiment(
    out_file: str,
    k_list: List[float],
    speed_list: List[float],
    n_cycles: int = 2,
    chi_0: float = 10.0,
    amplitude: float = 0.1,
):
    verify_pyelastica_installation()

    print("="*80)
    print("EXPERIMENT: Peristaltic Spine (Phase 2b)")
    print(f"Output: {out_file}")
    print(f"Wavenumbers: {k_list}")
    print(f"Speeds: {speed_list}")
    print("="*80)

    out_dir = os.path.dirname(out_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    fieldnames = [
        "timestamp", "k", "omega", "speed", "chi_0", "amplitude",
        "cobb_angle", "max_curvature", "S_lat", "U_CC", "U_info", "runtime_sec"
    ]

    # Calculate omega from speed and k
    # v = omega / k => omega = v * k
    # If k=0, omega defines temporal frequency directly?
    # For k=0, speed is undefined. We assume speed=0 means omega=0 unless specified.

    with open(out_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for k in k_list:
            for speed in speed_list:
                omega = speed * k

                # Special case: if k=0 and speed>0, this is meaningless for a traveling wave,
                # but might imply global oscillation (Jetlag).
                # For this experiment, we strictly define traveling wave v = w/k.

                print(f"Running: k={k:.2f}, v={speed:.2f} -> omega={omega:.2f}")

                t0 = time.time()

                wave_params = {
                    "k": k,
                    "omega": omega,
                    "phi": 0.0,
                    "amplitude": amplitude
                }

                # Run for enough time to see dynamics
                # If speed > 0, run for 2 cycles of the wave: T = 2*pi/omega
                if omega > 0:
                    period = 2 * np.pi / omega
                    duration = n_cycles * period
                else:
                    duration = 1.0 # Default static duration

                # Limit max duration for sanity
                duration = min(duration, 5.0)

                metrics = run_peristaltic_cycle(
                    wave_params=wave_params,
                    chi_0=chi_0,
                    duration=duration
                )

                t1 = time.time()

                row = {
                    "timestamp": datetime.now().isoformat(),
                    "k": k,
                    "omega": omega,
                    "speed": speed,
                    "chi_0": chi_0,
                    "amplitude": amplitude,
                    "cobb_angle": round(metrics.get("cobb_angle", 0), 4),
                    "max_curvature": round(metrics.get("max_curvature", 0), 4),
                    "S_lat": round(metrics.get("S_lat", 0), 4),
                    "U_CC": round(metrics.get("U_CC", 0), 4),
                    "U_info": round(metrics.get("U_info", 0), 4),
                    "runtime_sec": round(t1 - t0, 3)
                }
                writer.writerow(row)
                f.flush()

                print(f"  Result: Cobb={row['cobb_angle']}, S_lat={row['S_lat']}")

    print("Experiment Complete.")

def parse_args():
    parser = argparse.ArgumentParser(description="Peristaltic Spine Experiment")
    parser.add_argument("--out-file", default="outputs/peristaltic_spine/peristaltic_waves.csv")
    parser.add_argument("--wavenumber-list", type=str, default="0.0,6.28", help="Comma separated list of k")
    parser.add_argument("--speed-list", type=str, default="0.0,1.0", help="Comma separated list of speeds")
    parser.add_argument("--n-cycles", type=int, default=2)
    parser.add_argument("--quick-test", action="store_true")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    if args.quick_test:
        ks = [0.0, 6.28]
        vs = [0.0]
        n_cyc = 1
    else:
        ks = [float(x) for x in args.wavenumber_list.split(",")]
        vs = [float(x) for x in args.speed_list.split(",")]
        n_cyc = args.n_cycles

    run_experiment(args.out_file, ks, vs, n_cycles=n_cyc)

import os
import sys
import time
import tracemalloc
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import elastica as ea

    from spinalmodes.countercurvature.coupling import CounterCurvatureParams
    from spinalmodes.countercurvature.info_fields import InfoField1D
    from spinalmodes.countercurvature.pyelastica_bridge import (
        PYELASTICA_AVAILABLE,
        CounterCurvatureRodSystem,
        PinnedBC,
        SimulationResult,
        compute_U_CC,
    )
except ImportError as e:
    print(f"Error importing simulation module: {e}")
    sys.exit(1)

if not PYELASTICA_AVAILABLE:
    print("PyElastica is not available. Exiting.")
    sys.exit(1)


class LocomotorGravity(ea.NoForces):
    """
    Custom Forcing class to simulate locomotor resonance.
    Applies an oscillating vertical acceleration (gravity) to simulate walking/running.
    """
    def __init__(self, base_gravity: float = 9.81, amplitude: float = 0.5, frequency: float = 2.0):
        super().__init__()
        self.base_gravity = base_gravity
        self.amplitude = amplitude
        self.frequency = frequency

    def apply_forces(self, system, time: float = 0.0):
        # Oscillating gravity: g(t) = g0 * (1 + A * sin(2 * pi * f * t))
        g_t = self.base_gravity * (1.0 + self.amplitude * np.sin(2.0 * np.pi * self.frequency * time))
        # Apply force: F = m * a
        system.external_forces[2, :] -= system.mass * g_t


def run_locomotor_simulation(
    frequency: float,
    amplitude: float = 0.5,
    anisotropy: float = 5.0,
    active_curvature: float = 2.0,
    length: float = 0.4, # ~Adolescent spine length
    n_elements: int = 40,
    duration: float = 3.0,
    dt: float = 1e-4,
    gravity: float = 9.81,
    initial_lateral_defect: float = 0.05,
    natural_kyphosis: float = 2.0,
):
    """Runs a single locomotor resonance simulation."""
    tracemalloc.start()
    t0 = time.time()

    chi_kappa = active_curvature * 5.0

    try:
        s = np.linspace(0, length, n_elements + 1)
        info_center = 0.5 * length
        info_width = 0.1 * length
        I = 0.5 + 0.5 * np.exp(-0.5 * ((s - info_center) / info_width)**2)
        dIds = np.gradient(I, s)
        info = InfoField1D(s=s, I=I, dIds=dIds)

        params = CounterCurvatureParams(
            chi_kappa=chi_kappa,
            chi_tau=0.0,
            chi_E=0.0,
            chi_M=0.0,
            scale_length=length
        )

        kappa_gen = np.zeros((3, n_elements + 1))
        kappa_gen[1, :] = natural_kyphosis
        if initial_lateral_defect != 0.0:
            kappa_gen[0, :] = initial_lateral_defect

        rod_system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=length,
            n_elements=n_elements,
            kappa_gen=kappa_gen,
            stiffness_anisotropy=anisotropy,
            E0=1e6, # Base stiffness
            radius=0.01,
            rho=1000.0,
        )

        # Setup custom simulation collection to inject LocomotorGravity
        class ResonantSystem(ea.BaseSystemCollection, ea.Constraints, ea.Forcing, ea.Damping, ea.CallBacks):
            pass

        system = ResonantSystem()
        system.append(rod_system.rod)

        # Fixed at bottom (sacrum)
        system.constrain(rod_system.rod).using(
            ea.OneEndFixedBC,
            constrained_position_idx=(0,),
            constrained_director_idx=(0,)
        )

        # Apply Locomotor Gravity
        system.add_forcing_to(rod_system.rod).using(
            LocomotorGravity,
            base_gravity=gravity,
            amplitude=amplitude,
            frequency=frequency
        )

        # Apply damping
        system.dampen(rod_system.rod).using(ea.AnalyticalLinearDamper, damping_constant=0.5, time_step=dt)

        # Callback
        class SaveCallback(ea.CallBackBaseClass):
            def __init__(self, step_skip, results):
                super().__init__()
                self.every = step_skip
                self.results = results
            def make_callback(self, system, time, current_step):
                if current_step % self.every == 0:
                    self.results["time"].append(time)
                    self.results["centerline"].append(system.position_collection.copy().T)
                    self.results["kappa"].append(system.kappa.copy().T)

        results = {"time": [], "centerline": [], "kappa": []}
        save_every = max(1, int(duration/dt/50)) # Save 50 points
        system.collect_diagnostics(rod_system.rod).using(SaveCallback, step_skip=save_every, results=results)

        system.finalize()
        timestepper = ea.PositionVerlet()
        ea.integrate(timestepper, system, duration, int(duration/dt), progress_bar=False)

        # Pad kappa
        kappa_raw = np.array(results["kappa"])
        if len(kappa_raw) > 0:
            n_time, n_internal, n_dim = kappa_raw.shape
            padded_kappa = np.zeros((n_time, n_internal + 2, n_dim))
            padded_kappa[:, 1:-1, :] = kappa_raw
            padded_kappa[:, 0, :] = kappa_raw[:, 0, :]
            padded_kappa[:, -1, :] = kappa_raw[:, -1, :]
        else:
            padded_kappa = np.empty((0, n_elements + 1, 3))

        final_energies = {}
        if hasattr(rod_system.rod, "compute_bending_energy"):
            final_energies["bending_energy"] = float(rod_system.rod.compute_bending_energy())
        if hasattr(rod_system.rod, "compute_shear_energy"):
            final_energies["shear_energy"] = float(rod_system.rod.compute_shear_energy())
        if hasattr(rod_system.rod, "compute_translational_energy"):
            final_energies["translational_energy"] = float(rod_system.rod.compute_translational_energy())
        if hasattr(rod_system.rod, "compute_rotational_energy"):
            final_energies["rotational_energy"] = float(rod_system.rod.compute_rotational_energy())
        if hasattr(rod_system.rod, "mass") and hasattr(rod_system.rod, "position_collection"):
            z_pos = rod_system.rod.position_collection[2, :]
            final_energies["gravitational_energy"] = float(np.sum(rod_system.rod.mass * gravity * z_pos))

        sim_res = SimulationResult(
            time=np.array(results["time"]),
            centerline=np.array(results["centerline"]),
            kappa=padded_kappa,
            info_field=info,
            final_energies=final_energies
        )

        metrics = sim_res.compute_final_metrics()

        # We also want the max dynamic deviation during the run, not just final.
        # Max lateral deviation over time
        centerlines = np.array(results["centerline"]) # (T, N, 3)
        # S_lat = max lateral distance from centerline axis (x=0, y=0) over all nodes, we just take max X deviation
        max_dynamic_lat = np.max(np.abs(centerlines[:, :, 0]))

        success = True
        error_msg = ""

    except Exception as e:
        success = False
        error_msg = str(e)
        metrics = {}
        max_dynamic_lat = 0.0

    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    t1 = time.time()

    return {
        "frequency": frequency,
        "runtime_sec": t1 - t0,
        "peak_memory_mb": peak / (1024 * 1024),
        "success": success,
        "error": error_msg,
        "max_dynamic_lat": float(max_dynamic_lat),
        **metrics
    }


def run_experiment():
    print("Running Locomotor Resonance Catastrophe Experiment...")
    frequencies = np.linspace(0.5, 4.0, 36) # 0.5 to 4.0 Hz
    results = []

    out_dir = Path("outputs/locomotor_resonance")
    out_dir.mkdir(parents=True, exist_ok=True)

    for f in frequencies:
        print(f"  Testing Frequency: {f:.2f} Hz")
        res = run_locomotor_simulation(frequency=f)
        if res["success"]:
            print(f"    -> Cobb: {res.get('cobb_angle', 0):.2f}°, Max Dynamic Lat: {res['max_dynamic_lat']:.4f}m")
            results.append(res)
        else:
            print(f"    -> FAILED: {res['error']}")

    df = pd.DataFrame(results)
    csv_path = out_dir / "locomotor_resonance_metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved metrics to {csv_path}")

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(df["frequency"], df["cobb_angle"], 'b-o', label='Final Cobb Angle')

    # Highlight normal human walking freq (1.5 - 2.5 Hz)
    plt.axvspan(1.5, 2.5, color='orange', alpha=0.3, label='Human Walking Freq Range')

    plt.title("Locomotor Resonance Catastrophe in Adolescent Spine")
    plt.xlabel("Locomotor Frequency (Hz)")
    plt.ylabel("Cobb Angle (°)")
    plt.legend()
    plt.grid(True)

    plot_path = out_dir / "locomotor_resonance_peak.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path}")

if __name__ == "__main__":
    run_experiment()

"""PyElastica integration layer for countercurvature simulations.

This module provides factory utilities that construct Cosserat rod systems whose rest
curvature, stiffness and active moments are modulated by information fields.  The design
follows the biological countercurvature hypothesis: information gradients act as local
corrections to the mechanical metric, effectively biasing the rod against gravity-driven
modes.

Key Concepts:
- Vector Signal: Stiffness Anisotropy (ECM alignment).
- Scalar Signal: Active Growth/Curvature (Piezo/Ion flux).
- Mismatch: When Vector and Scalar signals dissociate (e.g. Microgravity).
"""

from __future__ import annotations

import time
import tracemalloc
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type, Union

__version__ = "1.0.1"
import math

import numpy as np
import scipy.integrate
from numpy.typing import NDArray

from .coupling import (
    CounterCurvatureParams,
    compute_active_moments,
    compute_effective_stiffness,
    compute_rest_curvature,
)
from .info_fields import InfoField1D
from .scoliosis_metrics import compute_scoliosis_metrics

ArrayF64 = NDArray[np.float64]

# Try to import PyElastica, but make it optional
try:
    import elastica as ea
    PYELASTICA_AVAILABLE = True
except ImportError:
    PYELASTICA_AVAILABLE = False
    # Dummy classes for testing/mocking
    class MockRod:
        def __init__(self, n_elements, length):
            self.n_elems = n_elements
            self.rest_lengths = np.ones(n_elements) * (length / n_elements)
            self.shear_matrix = np.zeros((3, 3, n_elements))
            self.bend_matrix = np.zeros((3, 3, n_elements - 1))
            self.rest_kappa = np.zeros((3, n_elements - 1))
            self.position_collection = np.zeros((3, n_elements + 1))
            self.velocity_collection = np.zeros((3, n_elements + 1))
            self.kappa = np.zeros((3, n_elements - 1))
            self.mass = np.ones(n_elements + 1) # Dummy mass

        def compute_bending_energy(self): return 0.0
        def compute_shear_energy(self): return 0.0
        def compute_translational_energy(self): return 0.0
        def compute_rotational_energy(self): return 0.0

    class ea:
        class CosseratRod:
            @staticmethod
            def straight_rod(n_elements, base_length, **kwargs):
                return MockRod(n_elements, base_length)
        class NoForces: pass
        class CallBackBaseClass: pass
        class ConstraintBase: pass
        class OneEndFixedBC: pass
        class GravityForces: pass
        class AnalyticalLinearDamper: pass
        class BaseSystemCollection:
            def append(self, *args, **kwargs): pass
            def constrain(self, *args, **kwargs): return self
            def using(self, *args, **kwargs): return self
            def add_forcing_to(self, *args, **kwargs): return self
            def dampen(self, *args, **kwargs): return self
            def collect_diagnostics(self, *args, **kwargs): return self
            def finalize(self): pass
        class Constraints: pass
        class Forcing: pass
        class Damping: pass
        class CallBacks: pass
        class PositionVerlet: pass
        @staticmethod
        def integrate(*args, **kwargs): pass

@dataclass
class CircadianParams:
    """Parameters for circadian modulation of curvature coupling.

    Attributes:
        period: Clock period in seconds (default 24h).
        amplitude: Relative amplitude of oscillation A (0 to 1).
        phase: Phase offset phi in radians.
        gravity_period: External gravity cycle period. If None, matches `period`.
    """
    period: float = 24.0 * 3600.0
    amplitude: float = 0.5
    phase: float = 0.0
    gravity_period: Optional[float] = None

@dataclass
class SimulationResult:
    time: ArrayF64
    centerline: ArrayF64
    kappa: ArrayF64
    info_field: InfoField1D
    final_energies: Optional[Dict[str, float]] = None

    @property
    def curvature(self) -> ArrayF64:
        """Returns the bending curvature (norm of kappa[0,1])."""
        # kappa is (time, n_nodes, 3).
        # We assume d1, d2 are bending, d3 is torsion.
        # Norm of first two components.
        return np.linalg.norm(self.kappa[..., :2], axis=-1)

    @property
    def torsion(self) -> ArrayF64:
        """Returns the torsion (kappa[2])."""
        return self.kappa[..., 2]

    def compute_final_metrics(self) -> Dict[str, float]:
        """Compute scalar metrics for the final state of the simulation.

        This method processes the emergent geometry from the Cosserat rod
        simulation to output clinically-relevant macroscopic shape metrics.

        Returns:
            Dict containing:
                - max_curvature: Maximum curvature magnitude.
                - max_torsion: Maximum torsion magnitude.
                - end_to_end_distance: Distance between first and last node.
                - S_lat: Lateral scoliosis index (from scoliosis_metrics).
                - cobb_angle: Cobb-like angle (from scoliosis_metrics).
                - z_tip: Tip deflection in Z (vertical).
                - ... energies ...
        """
        if len(self.time) == 0:
            return {}

        # Extract final state arrays
        pos = self.centerline[-1] # Shape: (n_nodes, 3)
        kappa = self.kappa[-1]    # Shape: (n_nodes, 3)

        # Compute basic geometry (compression/buckling indicator)
        end_to_end = np.linalg.norm(pos[-1] - pos[0])

        # Parse intrinsic curvature/torsion metrics
        # kappa array shape is (n_nodes, 3).
        # Components: kappa[0]=lateral bending, kappa[1]=sagittal bending, kappa[2]=torsion
        bending_mag = np.linalg.norm(kappa[:, :2], axis=1)
        max_curvature = float(np.max(bending_mag))

        torsion_mag = np.abs(kappa[:, 2])
        max_torsion = float(np.max(torsion_mag))

        # Scoliosis (Clinical) metrics mapping
        # PyElastica rod orientation assumed vertical:
        # - Longitudinal axis = Z (index 2).
        # - Coronal/Lateral plane = X (index 0).
        # - Sagittal plane = Y (index 1).
        z_coord = pos[:, 2]
        x_coord = pos[:, 0]

        scol_metrics = compute_scoliosis_metrics(z_coord, x_coord)

        metrics = {
            "max_curvature": max_curvature,
            "max_torsion": max_torsion,
            "end_to_end_distance": float(end_to_end),
            "S_lat": scol_metrics.S_lat,
            "cobb_angle": scol_metrics.cobb_like_deg,
            "z_tip": float(pos[-1, 2]),
            "x_tip": float(pos[-1, 0]),
            "y_tip": float(pos[-1, 1]),
        }

        if self.final_energies:
            metrics.update(self.final_energies)

        return metrics

def _check_pyelastica() -> None:
    """Internal check for PyElastica availability."""
    if not PYELASTICA_AVAILABLE:
        msg = (
            "PyElastica is not installed but is required for this module.\n"
            "Please install it using:\n"
            "  pip install pyelastica\n"
            "Or visit: https://github.com/GazzolaLab/PyElastica"
        )
        raise ImportError(msg)
    else:
        # Consistency check with scripts/check_pyelastica.py
        # Ensure we can access basic attributes to verify full load
        try:
            _ = getattr(ea, "__version__", "unknown")
        except AttributeError:
            pass # Older versions or specific builds might not expose this


def verify_pyelastica_installation(exit_on_fail: bool = True) -> bool:
    """
    Public utility to verify PyElastica installation for scripts.

    Args:
        exit_on_fail: If True, prints error and exits with sys.exit(1).
                      If False, returns False on failure.

    Returns:
        bool: True if installed, False otherwise.
    """
    try:
        _check_pyelastica()
        return True
    except ImportError as e:
        if exit_on_fail:
            print(f"ERROR: {e}")
            import sys
            sys.exit(1)
        return False

class ActiveMuscleTorques(ea.NoForces):
    """Applies a static distributed active moment (muscle torque)."""
    def __init__(self, torques: ArrayF64):
        super().__init__()
        self.torques = torques  # (3, n_elements)

    def apply_torques(self, system, time: float = 0.0):
        system.external_torques += self.torques

class PinnedBC(ea.ConstraintBase):
    """
    Boundary Condition that pins the position of selected nodes (fixes position)
    but allows free rotation (does not constrain directors).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        if not args:
             raise ValueError("PinnedBC requires fixed position argument (passed via constrained_position_idx).")
        self.fixed_position = np.array(args[0])

    def constrain_values(self, *args, **kwargs):
        # Expecting rod as first arg from partial application, but we use *args to be safe
        if args:
            rod = args[0]
            if hasattr(self, 'fixed_position'):
                rod.position_collection[..., 0] = self.fixed_position

    def constrain_rates(self, *args, **kwargs):
         if args:
            rod = args[0]
            rod.velocity_collection[..., 0] = 0.0

class CounterCurvatureRodSystem:
    """
    A PyElastica-based rod system configured for biological counter-curvature simulations.

    This class bridges the information-field theory (IEC) to the Cosserat rod physics engine.
    It maps biological inputs (protein concentrations, ECM organization) to mechanical
    properties like stiffness anisotropy and rest curvature.

    Coordinate System (Vertical Rod):
    - Rod aligns with Z-axis (d3 = Tangent = Z).
    - Normal (d1) aligns with Y-axis. Bending about d1 is in X-Z plane (Lateral Bending).
      Therefore, kappa[0] (d1 curvature) corresponds to Lateral Curvature (Scoliosis).
    - Binormal (d2) aligns with -X-axis. Bending about d2 is in Y-Z plane (Sagittal Bending).
      Therefore, kappa[1] (d2 curvature) corresponds to Sagittal Curvature (Kyphosis/Lordosis).

    Units:
    - Length: meters (m)
    - Time: seconds (s)
    - Mass: kilograms (kg)
    - Force: Newtons (N)
    - Stiffness: Pascals (Pa)
    """
    def __init__(
        self,
        rod: ea.CosseratRod,
        info_field: InfoField1D,
        params: CounterCurvatureParams,
        active_torques: Optional[ArrayF64] = None,
        kappa_gen: Optional[ArrayF64] = None
    ):
        self.rod = rod
        self.info_field = info_field
        self.params = params
        self.n_elements = rod.n_elems
        self.length = np.sum(rod.rest_lengths)
        self.active_torques = active_torques
        self.kappa_gen = kappa_gen

    @classmethod
    def from_iec(
        cls,
        info: InfoField1D,
        params: CounterCurvatureParams,
        length: float,
        n_elements: int,
        *,
        E0: float = 1e6,
        nu: float = 0.5,
        rho: float = 1000.0,
        radius: float = 0.01,
        kappa_gen: Optional[ArrayF64] = None,
        gravity: float = 9.81,
        base_position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        base_direction: tuple[float, float, float] = (0.0, 0.0, 1.0),
        normal: tuple[float, float, float] = (0.0, 1.0, 0.0),
        stiffness_anisotropy: Union[float, ArrayF64] = 1.0,
        taper_ratio: float = 1.0,
    ) -> "CounterCurvatureRodSystem":
        _check_pyelastica()

        # Create rod
        rod = ea.CosseratRod.straight_rod(
            n_elements=n_elements,
            start=np.array(base_position),
            direction=np.array(base_direction),
            normal=np.array(normal),
            base_length=length,
            base_radius=radius,
            density=rho,
            youngs_modulus=E0,
            shear_modulus=E0 / (2.0 * (1.0 + nu)),
        )

        # Apply geometric tapering (muscle atrophy / developmental gradient)
        if taper_ratio != 1.0:
            # Generate scaling profile r(s) = r_base * (1 + (taper-1) * s/L)
            s_nodes = np.linspace(0, length, n_elements + 1)
            # Element centers
            s_elements = 0.5 * (s_nodes[:-1] + s_nodes[1:])
            # Internal nodes (Voronoi domains)
            s_voronoi = s_nodes[1:-1]

            # Scaling function
            def get_scale(s_val):
                return 1.0 + (taper_ratio - 1.0) * (s_val / length)

            scale_elems = get_scale(s_elements)
            scale_voro = get_scale(s_voronoi)

            # 1. Update Radius (elements)
            rod.radius[:] *= scale_elems

            # 2. Update Mass (nodes)
            # Recompute element mass based on new radius
            # m_elem = rho * pi * r^2 * L_elem
            m_elems_new = rho * np.pi * (rod.radius ** 2) * rod.rest_lengths

            # Distribute to nodes (simple lumped mass)
            rod.mass[:] = 0.0
            rod.mass[:-1] += 0.5 * m_elems_new
            rod.mass[1:] += 0.5 * m_elems_new

            # 3. Update Mass Second Moment of Inertia (elements)
            # J propto m * r^2 propto r^2 * r^2 = r^4
            # Scale existing J by (r_new / r_old)^4
            scale_J = scale_elems ** 4
            for k in range(n_elements):
                rod.mass_second_moment_of_inertia[..., k] *= scale_J[k]
                if hasattr(rod, "inv_mass_second_moment_of_inertia"):
                    rod.inv_mass_second_moment_of_inertia[..., k] /= scale_J[k]

            # 4. Update Shear Matrix (elements)
            # S propto A propto r^2
            scale_S = scale_elems ** 2
            for k in range(n_elements):
                rod.shear_matrix[..., k] *= scale_S[k]

            # 5. Update Bend Matrix (internal nodes)
            # B propto I propto r^4
            scale_B = scale_voro ** 4
            for k in range(n_elements - 1):
                rod.bend_matrix[..., k] *= scale_B[k]

        # Compute effective stiffness E_eff based on information field
        E_eff = compute_effective_stiffness(info, params, E0)

        # Interpolate E_eff to element centers for shear matrix modification
        # s_rod (nodes): [0, ..., L]
        # s_elements (centers): midpoints of nodes
        s_rod = np.linspace(0, length, n_elements + 1)
        s_elements = 0.5 * (s_rod[:-1] + s_rod[1:])
        E_eff_elements = np.interp(s_elements, info.s, E_eff)

        # Scale shear matrix (3, 3, n_elements)
        # Assuming isotropic scaling of shear modulus with Young's modulus
        # shear_matrix ~ G ~ E. So we scale by E_eff_elements / E0
        scaling_shear = E_eff_elements / E0
        for k in range(n_elements):
            rod.shear_matrix[..., k] *= scaling_shear[k]

        # Interpolate E_eff to Voronoi domains (internal nodes) for bend matrix modification
        # Voronoi domains are at s_rod[1:-1]
        s_internal = s_rod[1:-1]
        E_eff_internal = np.interp(s_internal, info.s, E_eff)

        # Scale bend matrix (3, 3, n_elements - 1)
        # bend_matrix ~ E * I. So we scale by E_eff_internal / E0
        scaling_bend = E_eff_internal / E0
        for k in range(n_elements - 1):
            rod.bend_matrix[..., k] *= scaling_bend[k]

        # Apply stiffness anisotropy
        # bend_matrix[0, 0] corresponds to stiffness about d1 (Normal).
        # In this setup with normal=(0,1,0), d1 aligns with Y-axis.
        # Bending about Y-axis (d1) occurs in the X-Z plane (Lateral Bending).
        # bend_matrix[1, 1] corresponds to stiffness about d2 (Binormal).
        # d2 aligns with -X-axis. Bending about X-axis occurs in the Y-Z plane (Sagittal Bending).

        # We want `anisotropy` to scale the Lateral stiffness (resisting scoliosis).
        # So we scale bend_matrix[0, 0].

        # Handle scalar or array anisotropy
        anisotropy_arr = None
        if isinstance(stiffness_anisotropy, (float, int)):
            if stiffness_anisotropy != 1.0:
                rod.bend_matrix[0, 0, :] *= stiffness_anisotropy
        else:
            # Assume array-like
            aniso = np.asarray(stiffness_anisotropy, dtype=float)
            if aniso.ndim != 1:
                raise ValueError("Stiffness anisotropy array must be 1D.")

            # Interpolate to internal nodes (Voronoi domains) if size mismatch
            # bend_matrix is (3, 3, n_elements - 1)
            target_size = n_elements - 1
            if aniso.shape[0] != target_size:
                # Map input grid (assumed 0 to L) to internal nodes
                # s_internal defined earlier: midpoints of internal nodes
                # s_rod is linspace(0, L, n_elements + 1)
                # s_internal = s_rod[1:-1]
                s_source = np.linspace(0, length, aniso.shape[0])
                anisotropy_arr = np.interp(s_internal, s_source, aniso)
            else:
                anisotropy_arr = aniso

            # Apply array anisotropy to bend_matrix[0, 0, :]
            rod.bend_matrix[0, 0, :] *= anisotropy_arr

        # Create instance to use update_rest_curvature
        # We pass kappa_gen=None initially to constructor, then set it.
        # But we need active_torques first.

        # Compute active moments (scalar field on nodes) if chi_M != 0 or chi_tau != 0
        active_torques = None
        if params.chi_M != 0.0 or params.chi_tau != 0.0:
            active_torques = np.zeros((3, n_elements))

            # Sagittal bending moment (from scalar growth drive)
            if params.chi_M != 0.0:
                M_active_nodes = compute_active_moments(info, params)
                M_active_elems = np.interp(s_elements, info.s, M_active_nodes)
                active_torques[1, :] = M_active_elems

            # Torsion moment (from chiral packing or twisting drive)
            if params.chi_tau != 0.0:
                # Torsion drive maps to moments about the tangent axis (d3)
                # T_active ~ chi_tau * I
                T_active_nodes = params.chi_tau * info.I
                T_active_elems = np.interp(s_elements, info.s, T_active_nodes)
                active_torques[2, :] = T_active_elems

        system = cls(rod=rod, info_field=info, params=params, active_torques=active_torques, kappa_gen=kappa_gen)

        # Initial setting of rest curvature
        system.update_rest_curvature(params)

        return system

    def update_rest_curvature(self, params: CounterCurvatureParams) -> None:
        """Update the rod's rest curvature based on current parameters."""
        kappa_gen_val = self.kappa_gen if self.kappa_gen is not None else 0.0
        kappa_rest = compute_rest_curvature(self.info_field, params, kappa_gen_val)

        s_rod = np.linspace(0, self.length, self.n_elements + 1)
        s_internal = s_rod[1:-1]

        rest_kappa = np.zeros((3, self.n_elements - 1))
        for i in range(3):
            rest_kappa[i, :] = np.interp(s_internal, self.info_field.s, kappa_rest[i, :])

        self.rod.rest_kappa[:] = rest_kappa
        self.params = params

    def __repr__(self) -> str:
        """Return a string representation of the rod system configuration."""
        # Estimate anisotropy from first element's bend matrix if possible
        anisotropy_str = "1.0"
        if hasattr(self.rod, "bend_matrix") and self.rod.bend_matrix.shape[2] > 0:
            # Check if uniform
            b00 = self.rod.bend_matrix[0, 0, :]
            b11 = self.rod.bend_matrix[1, 1, :]
            # Avoid division by zero
            ratio = np.zeros_like(b00)
            mask = b11 != 0
            ratio[mask] = b00[mask] / b11[mask]

            if np.allclose(ratio, ratio[0]):
                anisotropy_str = f"{ratio[0]:.2f}"
            else:
                anisotropy_str = f"Range[{np.min(ratio):.2f}-{np.max(ratio):.2f}]"

        return (
            f"<CounterCurvatureRodSystem elements={self.n_elements} "
            f"length={self.length:.2f} "
            f"chi_kappa={self.params.chi_kappa:.2f} "
            f"anisotropy={anisotropy_str}>"
        )

    def get_configuration(self) -> Dict[str, Any]:
        """Return a dictionary of the system configuration for logging."""
        # Calculate anisotropy
        anisotropy_val = 1.0
        if hasattr(self.rod, "bend_matrix") and self.rod.bend_matrix.shape[2] > 0:
            b00 = self.rod.bend_matrix[0, 0, :]
            b11 = self.rod.bend_matrix[1, 1, :]
            # Avoid division by zero
            ratio = np.zeros_like(b00)
            mask = b11 != 0
            ratio[mask] = b00[mask] / b11[mask]

            if np.allclose(ratio, ratio[0]):
                anisotropy_val = float(ratio[0])
            else:
                # Return mean if varying, or keep as array? simpler to return mean for scalar field
                anisotropy_val = float(np.mean(ratio))

        return {
            "n_elements": self.n_elements,
            "length": self.length,
            "chi_kappa": self.params.chi_kappa,
            "chi_tau": self.params.chi_tau,
            "chi_E": self.params.chi_E,
            "chi_M": self.params.chi_M,
            "stiffness_anisotropy": anisotropy_val
        }

    def run_simulation(
        self,
        final_time: float,
        dt: float,
        *,
        save_every: int = 100,
        gravity: float = 9.81,
        damping_constant: float = 0.5,
        bc_cls: Optional[Type] = None,
        bc_kwargs: Optional[Dict[str, Any]] = None,
        boundary_condition: str = "fixed",
        progress_bar: bool = True,
        circadian_params: Optional[CircadianParams] = None,
    ) -> SimulationResult:
        _check_pyelastica()

        class CCSystem(ea.BaseSystemCollection, ea.Constraints, ea.Forcing, ea.Damping, ea.CallBacks):
            pass

        system = CCSystem()
        system.append(self.rod)

        # Constraints
        if bc_cls is not None:
            kwargs = bc_kwargs or {}
            system.constrain(self.rod).using(bc_cls, **kwargs)
        else:
            # Configure based on string description
            if boundary_condition == "fixed":
                system.constrain(self.rod).using(
                    ea.OneEndFixedBC,
                    constrained_position_idx=(0,),
                    constrained_director_idx=(0,)
                )
            elif boundary_condition == "pinned":
                # Pinned: Position fixed at node 0, Directors free
                system.constrain(self.rod).using(
                    PinnedBC,
                    constrained_position_idx=(0,),
                    constrained_director_idx=()
                )
            else:
                raise ValueError(f"Unknown boundary_condition: {boundary_condition}. Use 'fixed' or 'pinned'.")

        # Gravity
        system.add_forcing_to(self.rod).using(ea.GravityForces, acc_gravity=np.array([0.0, 0.0, -gravity]))

        # Active Moments (if any)
        if self.active_torques is not None:
             system.add_forcing_to(self.rod).using(ActiveMuscleTorques, torques=self.active_torques)

        # Damping
        system.dampen(self.rod).using(ea.AnalyticalLinearDamper, damping_constant=damping_constant, time_step=dt)

        # Callback for diagnostics
        class CCCallback(ea.CallBackBaseClass):
            def __init__(self, step_skip, results):
                super().__init__()
                self.every = step_skip
                self.results = results
            def make_callback(self, system, time, current_step):
                if current_step % self.every == 0:
                    self.results["time"].append(time)
                    self.results["centerline"].append(system.position_collection.copy().T)
                    # Save full kappa vector (3, n_elems-1) -> transpose to (n_elems-1, 3)
                    self.results["kappa"].append(system.kappa.copy().T)

        results = {"time": [], "centerline": [], "kappa": []}
        system.collect_diagnostics(self.rod).using(CCCallback, step_skip=save_every, results=results)

        # Circadian Callback
        if circadian_params:
            class CircadianModulationCallback(ea.CallBackBaseClass):
                def __init__(self, system_wrapper, c_params, step_skip=1):
                    super().__init__()
                    self.system_wrapper = system_wrapper
                    self.c_params = c_params
                    self.every = step_skip
                    self.chi_0 = system_wrapper.params.chi_kappa

                def make_callback(self, system, time, current_step):
                    if current_step % self.every == 0:
                        # chi_kappa(t) = chi_0 * (1 + A * cos(omega * t + phi))
                        omega = 2 * math.pi / self.c_params.period
                        modulation = 1.0 + self.c_params.amplitude * math.cos(omega * time + self.c_params.phase)

                        # Apply to chi_kappa
                        # We use _replace on named tuple to get new params
                        new_chi_kappa = self.chi_0 * modulation
                        new_params = self.system_wrapper.params._replace(chi_kappa=new_chi_kappa)

                        self.system_wrapper.update_rest_curvature(new_params)

            # Update every step for smooth physics
            system.collect_diagnostics(self.rod).using(
                CircadianModulationCallback,
                system_wrapper=self,
                c_params=circadian_params,
                step_skip=1
            )

        system.finalize()
        timestepper = ea.PositionVerlet()
        ea.integrate(timestepper, system, final_time, int(final_time/dt), progress_bar=progress_bar)

        # Pad kappa to match n_nodes (n_elems + 1)
        # kappa is (time, n_elems-1, 3)
        # We want (time, n_elems+1, 3)
        kappa_raw = np.array(results["kappa"])
        if len(kappa_raw) > 0:
            n_time, n_internal, n_dim = kappa_raw.shape
            padded_kappa = np.zeros((n_time, n_internal + 2, n_dim))
            padded_kappa[:, 1:-1, :] = kappa_raw
            # Edge padding: repeat first/last valid values to avoid zero artifacts
            padded_kappa[:, 0, :] = kappa_raw[:, 0, :]
            padded_kappa[:, -1, :] = kappa_raw[:, -1, :]
        else:
            padded_kappa = np.empty((0, self.n_elements + 1, 3))

        # Compute final energies
        final_energies = {}
        if hasattr(self.rod, "compute_bending_energy"):
            final_energies["bending_energy"] = float(self.rod.compute_bending_energy())
        if hasattr(self.rod, "compute_shear_energy"):
            final_energies["shear_energy"] = float(self.rod.compute_shear_energy())
        if hasattr(self.rod, "compute_translational_energy"):
            final_energies["translational_energy"] = float(self.rod.compute_translational_energy())
        if hasattr(self.rod, "compute_rotational_energy"):
            final_energies["rotational_energy"] = float(self.rod.compute_rotational_energy())

        # Gravitational Potential Energy
        if hasattr(self.rod, "mass") and hasattr(self.rod, "position_collection"):
            # Potential Energy = m * g * h
            # Gravity is in -Z direction usually for gravity vector (0,0,-g), so U = m*g*z
            z_pos = self.rod.position_collection[2, :]
            final_energies["gravitational_energy"] = float(np.sum(self.rod.mass * gravity * z_pos))

        return SimulationResult(
            time=np.array(results["time"]),
            centerline=np.array(results["centerline"]),
            kappa=padded_kappa,
            info_field=self.info_field,
            final_energies=final_energies
        )


def run_protein_simulation(
    anisotropy: Union[float, ArrayF64],
    active_curvature: float,
    torsion_drive: float = 0.0,
    stiffness_modulation: float = 0.0,
    initial_lateral_defect: float = 0.0,
    natural_kyphosis: float = 2.0,
    length: float = 1.0,
    radius: float = 0.01,
    E0: float = 1e6,
    rho: float = 1000.0,
    n_elements: int = 50,
    duration: float = 2.0,
    dt: float = 1e-4,
    gravity: float = 9.81,
    boundary_condition: str = "fixed",
    show_progress: bool = True,
    scale_factor_kappa: float = 5.0,
    scale_factor_tau: float = 5.0,
    scale_factor_E: float = 0.5,
) -> Dict[str, Any]:
    """
    Run a mechanical simulation driven by protein-derived metrics using PyElastica.

    This function serves as the primary bridge between biological data (protein metrics)
    and mechanical simulation (Cosserat rod). It maps abstract structural metrics to
    concrete mechanical parameters of the CounterCurvatureRodSystem.

    Mapping Logic:
    - Anisotropy (A) -> Stiffness Anisotropy (B_lat / B_sag). Higher A means the rod is stiffer
      in the lateral plane, resisting scoliosis-like buckling.
    - Active Curvature (C) -> Coupling Strength (chi_kappa). Higher C drives stronger sagittal
      curvature (lordosis/kyphosis) via the Information Field.
    - Lateral Defect (D) -> Initial perturbation (kappa_0). Small lateral defects seed potential
      instabilities.

    Args:
        anisotropy: Degree of stiffness anisotropy (1.0 = isotropic).
                   Scalar or 1D array matching n_elements.
                   Ratio of Lateral Bending Stiffness / Sagittal Bending Stiffness.
        active_curvature: Magnitude of active curvature drive (scalar signal).
                          Maps to chi_kappa via scale_factor_kappa.
        torsion_drive: Magnitude of active torsion drive.
                       Maps to chi_tau via scale_factor_tau.
        stiffness_modulation: Degree of stiffness modulation (blockiness).
                              Maps to chi_E via scale_factor_E.
        initial_lateral_defect: Magnitude of initial lateral curvature (perturbation) in 1/m.
                                Seeds symmetry breaking.
        natural_kyphosis: Magnitude of natural sagittal curvature (kyphosis) in 1/m.
                          Sets the baseline sagittal profile.
        length: Length of the rod (m). Default 1.0.
        rho: Rod density (kg/m^3). Default 1000.0.
        n_elements: Number of elements in the rod. Default 50.
        duration: Simulation duration (s). Default 2.0.
        dt: Time step (s). Default 1e-4.
        gravity: Gravitational acceleration (m/s^2). Default 9.81.
        boundary_condition: "fixed" (cantilever) or "pinned" (hinged).
        show_progress: Whether to show the PyElastica progress bar.
        scale_factor_kappa: Scaling factor for active_curvature -> chi_kappa. Default 5.0.
        scale_factor_tau: Scaling factor for torsion_drive -> chi_tau. Default 5.0.
        scale_factor_E: Scaling factor for stiffness_modulation -> chi_E. Default 0.5.

    Returns:
        Dictionary containing:
        - Geometric metrics: max_curvature, max_torsion, end_to_end_distance, z_tip.
        - Scoliosis metrics: S_lat, cobb_angle.
        - Energy metrics: U_CC, U_elastic, U_info, info_gain_ratio.
        - Performance metrics: runtime_sec, peak_memory_mb.
        - success (bool) and error (str).

    Note on Resource Profiling:
        This function internally uses `tracemalloc` to measure peak memory usage during the simulation.
        If the caller is also using `tracemalloc`, nested usage behavior may vary.
    """
    if not PYELASTICA_AVAILABLE:
        return {
            "error": "PyElastica not available.",
            "success": False
        }

    # Map inputs to model parameters
    chi_kappa = active_curvature * scale_factor_kappa
    chi_tau = torsion_drive * scale_factor_tau
    chi_E = stiffness_modulation * scale_factor_E

    tracemalloc.start()
    t0 = time.time()

    try:
        if n_elements < 2:
            raise ValueError("n_elements must be at least 2")

        # 1. Setup Information Field
        # Use a generic Gaussian info field representing a localized signal
        s = np.linspace(0, length, n_elements + 1)
        # Center bump
        info_center = 0.5 * length
        info_width = 0.1 * length
        I = 0.5 + 0.5 * np.exp(-0.5 * ((s - info_center) / info_width)**2)
        dIds = np.gradient(I, s)
        info = InfoField1D(s=s, I=I, dIds=dIds)

        # 2. Setup Parameters
        params = CounterCurvatureParams(
            chi_kappa=chi_kappa,
            chi_tau=chi_tau,
            chi_E=chi_E,
            chi_M=0.0,
            scale_length=length
        )

        # 3. Create System with constant intrinsic curvature base
        kappa_gen = np.zeros((3, n_elements + 1))
        # Sagittal Kyphosis (Index 1: Normal curvature, Y-Z plane bending)
        kappa_gen[1, :] = natural_kyphosis
        # Lateral Defect (Index 0: Binormal curvature, X-Z plane bending)
        if initial_lateral_defect != 0.0:
            kappa_gen[0, :] = initial_lateral_defect

        rod_system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=length,
            n_elements=n_elements,
            E0=E0,
            rho=rho,
            radius=radius,
            kappa_gen=kappa_gen,
            gravity=gravity,
            stiffness_anisotropy=anisotropy
        )

        # 4. Run Simulation
        result = rod_system.run_simulation(
            final_time=duration,
            dt=dt,
            save_every=max(1, int(duration/dt/10)),
            boundary_condition=boundary_condition,
            progress_bar=show_progress
        )

        sim_metrics = result.compute_final_metrics()

        # Compute thermodynamic cost metrics
        energy_metrics = compute_U_CC(
            result, info, params, gravity=gravity, rho=rho, E0=E0,
            radius=radius, anisotropy=anisotropy
        )
        sim_metrics.update(energy_metrics)

        success = True
        error_msg = ""

    except Exception as e:
        success = False
        error_msg = str(e)
        sim_metrics = {}

    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    t1 = time.time()

    # Handle array input for anisotropy in output dict
    anisotropy_out = anisotropy
    if isinstance(anisotropy, np.ndarray):
        anisotropy_out = f"Array(mean={np.mean(anisotropy):.2f})"

    output = {
        "input_anisotropy": anisotropy_out,
        "input_active_curvature": active_curvature,
        "mapped_chi_kappa": chi_kappa,
        "mapped_chi_tau": chi_tau,
        "runtime_sec": t1 - t0,
        "peak_memory_mb": peak / (1024 * 1024),
        "success": success,
        "error": error_msg,
    }
    output.update(sim_metrics)

    return output


def compute_U_CC(
    result: SimulationResult,
    info: InfoField1D,
    params: CounterCurvatureParams,
    gravity: float = 9.81,
    rho: float = 1000.0,
    E0: float = 1e6,
    radius: float = 0.01,
    anisotropy: Union[float, ArrayF64] = 1.0,
) -> Dict[str, float]:
    """Compute the Total Potential Energy cost function U_CC.

    The organism minimises U_CC = U_gravity + U_elastic_straight - U_info, where:

    - U_gravity: gravitational potential energy (m * g * h, summed over nodes)
    - U_elastic_straight: elastic energy required to bend the rod from a straight
      configuration to the current shape (penalizing deformation).
    - U_info: energy reduction achieved by aligning curvature with the information field.
      Specifically, the coupling term: integral( B * kappa * kappa_rest_info ds ).

    This formulation explicitly separates the "Cost of Deformation" (U_elastic_straight)
    from the "Benefit of Alignment" (U_info).

    Parameters
    ----------
    result : SimulationResult
        Completed simulation result containing centerline, kappa, and energies.
    info : InfoField1D
        Information field used in the simulation.
    params : CounterCurvatureParams
        Coupling parameters (chi_kappa, chi_E, chi_M, etc.).
    gravity : float
        Gravitational acceleration (m/s^2).
    rho : float
        Rod density (kg/m^3).
    E0 : float
        Baseline Young's modulus (Pa).
    radius : float
        Rod radius (m), used to compute area moment of inertia.
    anisotropy : float or ArrayF64
        Stiffness anisotropy factor applied to lateral bending mode.

    Returns
    -------
    dict
        Dictionary containing:
        - U_gravity: Gravitational potential energy
        - U_elastic: PyElastica's computed elastic energy (relative to rest curvature)
        - U_elastic_straight: Elastic energy relative to straight configuration
        - U_info: Information alignment energy benefit
        - U_CC: Total cost function (U_gravity + U_elastic_straight - U_info)
        - U_kinetic: Translational + rotational kinetic energy
        - info_gain_ratio: U_info / (U_gravity + U_elastic_straight), dimensionless
    """
    if len(result.time) == 0:
        return {
            "U_gravity": 0.0, "U_elastic": 0.0, "U_info": 0.0,
            "U_CC": 0.0, "U_kinetic": 0.0, "info_gain_ratio": 0.0,
        }

    energies = result.final_energies or {}

    # --- U_gravity ---
    U_gravity = energies.get("gravitational_energy", 0.0)

    # --- U_elastic (PyElastica) ---
    U_pyelastica = energies.get("bending_energy", 0.0) + energies.get("shear_energy", 0.0)

    # --- U_kinetic ---
    U_trans = energies.get("translational_energy", 0.0)
    U_rot = energies.get("rotational_energy", 0.0)
    U_kinetic = U_trans + U_rot

    # --- Construct Stiffness Field ---
    s = info.s

    # 1. Effective Young's Modulus
    E_eff = compute_effective_stiffness(info, params, E0) # (n_nodes,)

    # 2. Area Moment of Inertia I = pi * r^4 / 4
    I_area = np.pi * (radius**4) / 4.0

    # 3. Base Bending Stiffness B = E_eff * I_area
    B_base = E_eff * I_area # (n_nodes,)

    # 4. Handle Anisotropy
    anisotropy_arr = np.ones_like(B_base)
    if isinstance(anisotropy, (float, int)):
        anisotropy_arr[:] = float(anisotropy)
    else:
        # Interpolate array anisotropy if needed
        aniso_input = np.asarray(anisotropy, dtype=float)
        if aniso_input.shape != s.shape:
             # simple linear interp if sizes differ
             s_input = np.linspace(s[0], s[-1], aniso_input.shape[0])
             anisotropy_arr = np.interp(s, s_input, aniso_input)
        else:
             anisotropy_arr = aniso_input

    # Stiffness Matrix Components (Diagonal approximation)
    # B_11 (about d1, Lateral bending) = B_base * anisotropy
    B_11 = B_base * anisotropy_arr
    # B_22 (about d2, Sagittal bending) = B_base
    B_22 = B_base
    # B_33 (torsion) = GJ = E*I/(1+nu). Assuming nu=0.5
    nu = 0.5
    B_33 = B_base / (1.0 + nu)

    # 5. Get Curvature (n_nodes, 3)
    kappa = result.kappa[-1] # Final step

    # Handle grid mismatch between kappa and info.s
    # kappa comes from the rod simulation grid, while info.s is the target grid for integration.
    if kappa.shape[0] != s.shape[0]:
        n_rod_nodes = kappa.shape[0]
        # Assume linear mapping over the same domain [s[0], s[-1]]
        s_rod = np.linspace(s[0], s[-1], n_rod_nodes)

        # Interpolate kappa components to info.s grid
        kappa_interp = np.zeros((s.shape[0], 3))
        for i in range(3):
            kappa_interp[:, i] = np.interp(s, s_rod, kappa[:, i])

        kappa = kappa_interp

    # 6. Compute U_elastic_straight (Energy relative to straight rod)
    # Integral 0.5 * (B11*k0^2 + B22*k1^2 + B33*k2^2) ds
    # kappa indices: 0=Lateral(d1), 1=Sagittal(d2), 2=Torsion(d3)
    energy_density_straight = 0.5 * (
        B_11 * kappa[:, 0]**2 +
        B_22 * kappa[:, 1]**2 +
        B_33 * kappa[:, 2]**2
    )
    U_elastic_straight = scipy.integrate.trapezoid(energy_density_straight, s)

    # 7. Compute U_info_coupling
    # Need kappa_rest_info (rest curvature due solely to information)
    # compute_rest_curvature returns (3, n_nodes). We need (n_nodes, 3)
    kappa_rest_info_arr = compute_rest_curvature(info, params, kappa_gen=0.0)
    kappa_rest_info = kappa_rest_info_arr.T

    # Energy density = B * kappa * kappa_rest (interaction term)
    energy_density_info = (
        B_11 * kappa[:, 0] * kappa_rest_info[:, 0] +
        B_22 * kappa[:, 1] * kappa_rest_info[:, 1] +
        B_33 * kappa[:, 2] * kappa_rest_info[:, 2]
    )
    U_info_coupling = scipy.integrate.trapezoid(energy_density_info, s)

    # --- U_CC ---
    # U_CC = U_gravity + U_elastic_straight - U_info_coupling
    # U_CC represents the organism's thermodynamic cost function, minimizing deformation while aligning with information
    U_CC = U_gravity + U_elastic_straight - U_info_coupling

    # --- Info Gain Ratio ---
    denom = abs(U_gravity) + abs(U_elastic_straight)
    info_gain_ratio = U_info_coupling / denom if denom > 1e-15 else 0.0

    return {
        "U_gravity": float(U_gravity),
        "U_elastic": float(U_pyelastica),
        "U_elastic_straight": float(U_elastic_straight),
        "U_info": float(U_info_coupling),
        "U_CC": float(U_CC),
        "U_kinetic": float(U_kinetic),
        "info_gain_ratio": float(info_gain_ratio),
    }


__all__ = [
    "CounterCurvatureRodSystem",
    "SimulationResult",
    "PYELASTICA_AVAILABLE",
    "ActiveMuscleTorques",
    "run_protein_simulation",
    "compute_U_CC",
    "CircadianParams",
]

if __name__ == "__main__":
    print(">>> PyElastica Bridge: Running Self-Test...")
    if not PYELASTICA_AVAILABLE:
        print("SKIPPED: PyElastica not available.")
    else:
        try:
            # Run a quick, low-res simulation
            print("    Initializing minimal protein simulation (N=20, T=0.1s)...")
            res = run_protein_simulation(
                anisotropy=2.0,
                active_curvature=1.0,
                n_elements=20,
                duration=0.1,
                show_progress=False
            )

            if res.get("success"):
                print("PASSED: Simulation completed successfully.")
                print(f"    Metrics: Cobb={res.get('cobb_angle',0):.2f}, MaxCurv={res.get('max_curvature',0):.4f}")
                print(f"    Runtime: {res.get('runtime_sec',0):.4f}s")
            else:
                print(f"FAILED: {res.get('error')}")
                import sys
                sys.exit(1)
        except Exception as e:
            print(f"CRITICAL FAILURE: {e}")
            import traceback
            traceback.print_exc()
            import sys
            sys.exit(1)

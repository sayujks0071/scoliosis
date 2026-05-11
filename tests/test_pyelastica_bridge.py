"""Smoke tests for PyElastica countercurvature bridge.

Tests that PyElastica integration works and produces reasonable results
compared to the beam solver.
"""

import numpy as np
import pytest

from spinalmodes.countercurvature.coupling import CounterCurvatureParams
from spinalmodes.countercurvature.info_fields import InfoField1D
from spinalmodes.countercurvature.pyelastica_bridge import (
    PYELASTICA_AVAILABLE,
    CounterCurvatureRodSystem,
)
from spinalmodes.iec import solve_beam_static


@pytest.mark.skipif(not PYELASTICA_AVAILABLE, reason="PyElastica not available")
def test_pyelastica_gravity_only_sag():
    """Test that PyElastica rod sags under gravity (no info coupling).

    Compare tip deflection to beam solver for a simple cantilever.
    """
    # Simple straight rod, no information coupling
    length = 0.4  # meters
    n_elements = 50
    n_points = n_elements + 1

    # Uniform info field (no coupling effect)
    s = np.linspace(0, length, n_points)
    I = np.ones(n_points) * 0.5
    dIds = np.zeros(n_points)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # Zero coupling parameters (gravity only)
    params = CounterCurvatureParams(
        chi_kappa=0.0, chi_E=0.0, chi_M=0.0, scale_length=length
    )

    # Material properties
    E0 = 1e9  # Pa
    rho = 1000.0  # kg/m³
    radius = 0.01  # m
    gravity = 9.81  # m/s²

    # Create rod system
    rod_system = CounterCurvatureRodSystem.from_iec(
        info=info,
        params=params,
        length=length,
        n_elements=n_elements,
        E0=E0,
        rho=rho,
        radius=radius,
        gravity=gravity,
        base_position=(0.0, 0.0, 0.0),
        base_direction=(1.0, 0.0, 0.0),  # Pointing in +x (horizontal)
        normal=(0.0, 1.0, 0.0),
    )

    # Run simulation to equilibrium
    # Critical time step check:
    # c = sqrt(E/rho) = sqrt(1e9/1000) = 1000 m/s
    # dl = L/n = 0.4/50 = 0.008 m
    # dt_crit = dl/c = 8e-6 s
    # We use dt = 5e-6 s to be safe.
    final_time = 1.0  # seconds (enough to reach quasi-static with damping)
    dt = 5e-6  # seconds

    # Save less frequently to avoid huge memory usage/output
    save_every = int(0.01 / dt)  # Save every 0.01 seconds

    result = rod_system.run_simulation(
        final_time=final_time, dt=dt, save_every=save_every, gravity=gravity
    )

    # Get final tip position (last node, last time step)
    tip_final = result.centerline[-1, -1, :]  # (x, y, z)
    tip_z_final = tip_final[2]  # z-coordinate (should sag downward, negative)

    # Compare to beam solver
    # For a cantilever with uniform load (gravity), tip deflection is:
    # δ = (ρ * g * A * L^4) / (8 * E * I)
    # where A = π * r^2, I = π * r^4 / 4
    s_beam = np.linspace(0, length, 100)
    kappa_target = np.zeros_like(s_beam)
    E_field = np.ones_like(s_beam) * E0
    M_active = np.zeros_like(s_beam)
    I_moment = np.pi * radius**4 / 4  # Second moment of area
    distributed_load = rho * np.pi * radius**2 * gravity  # N/m

    theta_beam, kappa_beam = solve_beam_static(
        s_beam,
        kappa_target,
        E_field,
        M_active,
        I_moment=I_moment,
        P_load=0.0,
        distributed_load=distributed_load,
    )

    # Tip deflection from beam solver (integrate curvature)
    # For small deflections: y(L) ≈ ∫∫ κ(s) ds ds
    from scipy.integrate import cumulative_trapezoid

    dy_ds = cumulative_trapezoid(kappa_beam, s_beam, initial=0.0)
    y_beam = cumulative_trapezoid(dy_ds, s_beam, initial=0.0)
    # Beam solver convention: positive load gives positive deflection.
    # But gravity acts in -z, so physical deflection is negative.
    tip_z_beam = -y_beam[-1]

    # PyElastica tip should be close to beam solver
    # Allow 20% tolerance due to different discretization and dynamics
    relative_error = abs(tip_z_final - tip_z_beam) / (abs(tip_z_beam) + 1e-6)
    assert relative_error < 0.2, (
        f"PyElastica tip deflection {tip_z_final:.6f} m "
        f"differs from beam solver {tip_z_beam:.6f} m "
        f"by {relative_error*100:.1f}%"
    )

    # Tip should sag downward (negative z)
    assert tip_z_final < 0, f"Tip should sag downward, got z={tip_z_final:.6f} m"


@pytest.mark.skipif(not PYELASTICA_AVAILABLE, reason="PyElastica not available")
def test_pyelastica_with_info_coupling():
    """Test that information coupling modifies rod shape.

    With χ_κ > 0, rod should deviate from pure gravity sag.
    """
    length = 0.4
    n_elements = 50
    n_points = n_elements + 1

    # Information field with gradient (promotes upward curvature)
    s = np.linspace(0, length, n_points)
    I = 0.5 + 0.3 * (s / length)  # Increasing from base to tip
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # Non-zero coupling - make it strong enough to overcome gravity
    # With chi_kappa=1.0 and dI/ds approx 0.75, kappa_rest approx 0.3
    # Deflection ~ 0.5 * 0.3 * 0.16 = 0.024 m = 2.4 cm.
    # Gravity sag is ~1.2 mm. So this should clearly lift it up.
    params = CounterCurvatureParams(
        chi_kappa=1.0, chi_E=0.0, chi_M=0.0, scale_length=length
    )

    # Material properties
    E0 = 1e9
    rho = 1000.0
    radius = 0.01
    gravity = 9.81

    # Create rod system
    rod_system = CounterCurvatureRodSystem.from_iec(
        info=info,
        params=params,
        length=length,
        n_elements=n_elements,
        E0=E0,
        rho=rho,
        radius=radius,
        gravity=gravity,
        base_position=(0.0, 0.0, 0.0),
        base_direction=(1.0, 0.0, 0.0),  # Pointing in +x (horizontal)
        normal=(0.0, 1.0, 0.0),
    )

    # Run simulation
    # Use stable time step (see calculation in test_pyelastica_gravity_only_sag)
    final_time = 1.0
    dt = 5e-6
    save_every = int(0.01 / dt)

    result = rod_system.run_simulation(
        final_time=final_time, dt=dt, save_every=save_every, gravity=gravity
    )

    # Check that we got results
    assert len(result.time) > 0
    assert result.centerline.shape[0] == len(result.time)
    assert result.centerline.shape[1] == n_points
    assert result.centerline.shape[2] == 3

    # With positive χ_κ and positive dI/ds, rod should curve upward
    # (less sag than gravity-only case)
    tip_final = result.centerline[-1, -1, :]
    tip_z_info = tip_final[2]

    # Compare to zero-coupling case (run separately)
    params_zero = CounterCurvatureParams(
        chi_kappa=0.0, chi_E=0.0, chi_M=0.0, scale_length=length
    )
    rod_system_zero = CounterCurvatureRodSystem.from_iec(
        info=info,
        params=params_zero,
        length=length,
        n_elements=n_elements,
        E0=E0,
        rho=rho,
        radius=radius,
        gravity=gravity,
        base_position=(0.0, 0.0, 0.0),
        base_direction=(1.0, 0.0, 0.0),  # Pointing in +x (horizontal)
        normal=(0.0, 1.0, 0.0),
    )
    result_zero = rod_system_zero.run_simulation(
        final_time=final_time, dt=dt, save_every=save_every, gravity=gravity
    )
    tip_zero = result_zero.centerline[-1, -1, :]
    tip_z_zero = tip_zero[2]

    # With info coupling, tip should be higher (less sag)
    # This is a qualitative check - exact values depend on coupling strength
    assert tip_z_info > tip_z_zero, (
        f"With info coupling, tip z={tip_z_info:.6f} should be higher "
        f"than without {tip_z_zero:.6f}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


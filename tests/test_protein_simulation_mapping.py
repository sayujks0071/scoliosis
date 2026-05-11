"""
Tests for the protein-driven PyElastica simulation mapping.

This test file verifies that the `run_protein_simulation` function correctly
maps biological parameters (anisotropy, active curvature) to mechanical outcomes,
and ensures that the simulation infrastructure is robust.
"""

import numpy as np
import pytest

from spinalmodes.countercurvature.pyelastica_bridge import (
    PYELASTICA_AVAILABLE,
    run_protein_simulation,
)


@pytest.mark.skipif(not PYELASTICA_AVAILABLE, reason="PyElastica not installed")
def test_run_protein_simulation_basic():
    """
    Test a minimal run of the protein simulation to ensure it completes
    and returns the expected dictionary structure.
    """
    result = run_protein_simulation(
        anisotropy=1.0,
        active_curvature=0.5,
        n_elements=10,
        duration=0.05, # Very short duration for speed
        dt=1e-4,
        show_progress=False,
    )

    assert result["success"], f"Simulation failed: {result.get('error')}"

    # Check for required keys
    expected_keys = [
        "max_curvature",
        "max_torsion",
        "S_lat",
        "cobb_angle",
        "U_CC",
        "U_info",
        "info_gain_ratio",
        "runtime_sec"
    ]
    for key in expected_keys:
        assert key in result, f"Missing key in result: {key}"

    # Basic physical sanity checks
    assert result["max_curvature"] >= 0.0
    assert result["U_CC"] is not None


@pytest.mark.skipif(not PYELASTICA_AVAILABLE, reason="PyElastica not installed")
def test_anisotropy_configuration():
    """
    Test that the anisotropy parameter is correctly applied to the bending matrix.
    We check the CounterCurvatureRodSystem internals directly.
    """
    from spinalmodes.countercurvature.pyelastica_bridge import (
        CounterCurvatureParams,
        CounterCurvatureRodSystem,
        InfoField1D,
    )

    # Setup minimal system
    length = 1.0
    n_elements = 10
    s = np.linspace(0, length, n_elements + 1)
    info = InfoField1D(s=s, I=np.zeros_like(s), dIds=np.zeros_like(s))
    params = CounterCurvatureParams(chi_kappa=0.0, chi_E=0.0, chi_M=0.0, scale_length=length)

    # 1. Isotropic
    sys_iso = CounterCurvatureRodSystem.from_iec(
        info=info, params=params, length=length, n_elements=n_elements,
        stiffness_anisotropy=1.0
    )
    # Check bend matrix diagonal ratio
    # bend_matrix shape: (3, 3, n_elements-1)
    # d1 (index 0,0) / d2 (index 1,1) should be 1.0
    b00_iso = sys_iso.rod.bend_matrix[0, 0, 0]
    b11_iso = sys_iso.rod.bend_matrix[1, 1, 0]
    assert np.isclose(b00_iso / b11_iso, 1.0), "Isotropic system should have ratio 1.0"

    # 2. Anisotropic
    target_aniso = 5.0
    sys_aniso = CounterCurvatureRodSystem.from_iec(
        info=info, params=params, length=length, n_elements=n_elements,
        stiffness_anisotropy=target_aniso
    )
    b00_aniso = sys_aniso.rod.bend_matrix[0, 0, 0]
    b11_aniso = sys_aniso.rod.bend_matrix[1, 1, 0]

    print(f"B00: {b00_aniso}, B11: {b11_aniso}")

    # Check that lateral stiffness (B00) is scaled up
    assert np.isclose(b00_aniso / b11_aniso, target_aniso), \
        f"Anisotropic system should have ratio {target_aniso}"

    # Check that sagittal stiffness (B11) is unchanged relative to isotropic (assuming E0 constant)
    assert np.isclose(b11_aniso, b11_iso), "Sagittal stiffness should remain baseline"


@pytest.mark.skipif(not PYELASTICA_AVAILABLE, reason="PyElastica not installed")
def test_active_curvature_scaling():
    """
    Test that increasing active curvature parameter increases the resulting curvature.
    """
    res_low = run_protein_simulation(
        anisotropy=1.0,
        active_curvature=0.1,
        n_elements=20,
        duration=0.1,
        show_progress=False
    )

    res_high = run_protein_simulation(
        anisotropy=1.0,
        active_curvature=1.0,
        n_elements=20,
        duration=0.1,
        show_progress=False
    )

    assert res_high["max_curvature"] > res_low["max_curvature"], \
        "Higher active curvature input did not produce higher output curvature."

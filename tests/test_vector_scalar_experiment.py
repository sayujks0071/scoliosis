"""
Test for the Vector-Scalar Mismatch experiment configuration.
Ensures the specific parameters (High Anisotropy + High chi_kappa) run without error.
"""
import numpy as np
import pytest

from spinalmodes.countercurvature.coupling import CounterCurvatureParams
from spinalmodes.countercurvature.info_fields import InfoField1D
from spinalmodes.countercurvature.pyelastica_bridge import (
    PYELASTICA_AVAILABLE,
    CounterCurvatureRodSystem,
)


@pytest.mark.skipif(not PYELASTICA_AVAILABLE, reason="PyElastica not available")
def test_vector_scalar_mismatch_configuration():
    """Run a short simulation of the 'Mismatched' case to ensure stability."""
    # Parameters from the experiment script
    length = 0.5
    n_elements = 20  # Reduced from 50
    radius = 0.01
    E0 = 1e6
    rho = 1000.0
    gravity = 9.81

    # Mismatched parameters
    anisotropy = 5.0
    chi_kappa = 10.0

    # Info Field
    s = np.linspace(0, length, n_elements + 1)
    info_density = 0.5 + 0.1 * np.exp(
        -0.5 * ((s - 0.6 * length) / (0.1 * length))**2
    )
    dIds = np.gradient(info_density, s)
    info = InfoField1D(s=s, I=info_density, dIds=dIds)

    params = CounterCurvatureParams(
        chi_kappa=chi_kappa,
        chi_E=0.0,
        chi_M=0.0,
        scale_length=length
    )

    kappa_gen = np.zeros((3, n_elements + 1))
    kappa_gen[0, :] = 2.0

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
        base_position=(0.0, 0.0, 0.0),
        base_direction=(0.0, 0.0, 1.0),
        normal=(1.0, 0.0, 0.0),
        stiffness_anisotropy=anisotropy
    )

    # Run for a very short time
    result = rod_system.run_simulation(
        final_time=0.01,
        dt=1e-5,
        save_every=100,
        gravity=gravity,
        boundary_condition="fixed"
    )

    metrics = result.compute_final_metrics()

    # Check that we got results
    assert "cobb_angle" in metrics
    assert "max_torsion" in metrics
    # Sanity checks
    assert metrics['max_curvature'] >= 0.0

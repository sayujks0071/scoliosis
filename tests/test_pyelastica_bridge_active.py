"""Unit tests for PyElastica bridge integration."""

import numpy as np
import pytest

from src.spinalmodes.countercurvature.coupling import CounterCurvatureParams
from src.spinalmodes.countercurvature.info_fields import InfoField1D
from src.spinalmodes.countercurvature.pyelastica_bridge import (
    PYELASTICA_AVAILABLE,
    ActiveMuscleTorques,
    CounterCurvatureRodSystem,
)


@pytest.mark.skipif(not PYELASTICA_AVAILABLE, reason="PyElastica not available")
class TestPyElasticaBridge:
    def test_active_muscle_torques_initialization(self):
        """Test that ActiveMuscleTorques can be initialized."""
        torques = np.zeros((3, 10))
        amt = ActiveMuscleTorques(torques)
        assert np.array_equal(amt.torques, torques)

    def test_system_initialization_with_active_moments(self):
        """Test that system correctly processes chi_M."""
        L = 1.0
        n_points = 51 # n_elements + 1
        s = np.linspace(0, L, n_points)
        I = s # Linear gradient
        dIds = np.ones_like(s)
        info = InfoField1D(s=s, I=I, dIds=dIds)

        # chi_M != 0
        params = CounterCurvatureParams(chi_M=1.0, scale_length=1.0)

        system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=L,
            n_elements=50,
            gravity=0.0
        )

        assert system.active_torques is not None
        # Shape should be (3, 50)
        assert system.active_torques.shape == (3, 50)
        # Gradient is 1.0. chi_M=1.0. Moment should be 1.0 (interp)
        # Torques are around y axis (index 1)
        assert np.allclose(system.active_torques[0, :], 0.0)
        assert np.allclose(system.active_torques[2, :], 0.0)
        # Check mean value is approx 1.0
        assert np.allclose(system.active_torques[1, :], 1.0)

    def test_run_simulation_completes(self):
        """Test that run_simulation completes without error."""
        L = 0.1
        n_points = 11
        s = np.linspace(0, L, n_points)
        info = InfoField1D(s=s, I=np.zeros_like(s), dIds=np.zeros_like(s))
        params = CounterCurvatureParams()

        system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=L,
            n_elements=10,
            gravity=0.0
        )

        # Very short run
        result = system.run_simulation(final_time=0.001, dt=1e-5)

        assert result.time is not None
        assert result.centerline is not None

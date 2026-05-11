import numpy as np
import pytest

from src.spinalmodes.countercurvature.coupling import CounterCurvatureParams
from src.spinalmodes.countercurvature.info_fields import InfoField1D
from src.spinalmodes.countercurvature.pyelastica_bridge import (
    PYELASTICA_AVAILABLE,
    CounterCurvatureRodSystem,
)


@pytest.mark.skipif(not PYELASTICA_AVAILABLE, reason="PyElastica not installed")
def test_boundary_conditions_effect():
    """
    Test that 'pinned' boundary condition results in larger deflection than 'fixed'
    under gravity for a horizontal rod.
    """
    # Setup
    L = 1.0
    n_elements = 10
    s = np.linspace(0, L, n_elements + 1)
    info = InfoField1D(s=s, I=np.zeros_like(s), dIds=np.zeros_like(s))
    params = CounterCurvatureParams()

    # Create system (horizontal, gravity down)
    # Fixed
    sys_fixed = CounterCurvatureRodSystem.from_iec(
        info=info, params=params, length=L, n_elements=n_elements,
        base_direction=(1.0, 0.0, 0.0), normal=(0.0, 0.0, 1.0),
        E0=1e5, rho=1000, radius=0.02
    )

    # We expect run_simulation to accept boundary_condition
    # This call might fail if the argument is not yet supported
    try:
        res_fixed = sys_fixed.run_simulation(
            final_time=0.5, dt=1e-4, gravity=1.0,
            boundary_condition="fixed"
        )

        # Pinned
        sys_pinned = CounterCurvatureRodSystem.from_iec(
            info=info, params=params, length=L, n_elements=n_elements,
            base_direction=(1.0, 0.0, 0.0), normal=(0.0, 0.0, 1.0),
            E0=1e5, rho=1000, radius=0.02
        )
        res_pinned = sys_pinned.run_simulation(
            final_time=0.5, dt=1e-4, gravity=1.0,
            boundary_condition="pinned"
        )

        # Calculate tip deflection (Z-axis, gravity is -Z)
        # Rod is along X. Gravity -Z. Rod should bend down (-Z).

        # res.centerline shape: (time, 3, n_nodes)
        # We want last time step, Z component (index 2), last node (index -1)
        tip_fixed_z = res_fixed.centerline[-1, 2, -1]
        tip_pinned_z = res_pinned.centerline[-1, 2, -1]

        print(f"Fixed Tip Z: {tip_fixed_z}")
        print(f"Pinned Tip Z: {tip_pinned_z}")

        # Pinned should deflect MORE (more negative Z)
        # So tip_pinned_z < tip_fixed_z (e.g. -0.5 < -0.1)
        assert tip_pinned_z < tip_fixed_z

    except TypeError as e:
        pytest.fail(f"API update required: {e}")

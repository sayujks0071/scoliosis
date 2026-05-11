"""
Smoke test for the end-to-end countercurvature pipeline.

This test validates that the full mathematical pipeline works:
    Info field → Metric → Coupling → Solver → Deviation
"""
import numpy as np
import pytest

from spinalmodes.countercurvature.api import (
    CounterCurvatureParams,
    InfoField1D,
    compute_countercurvature_metric,
    geodesic_curvature_deviation,
)
from spinalmodes.iec import solve_beam_static


def test_pipeline_end_to_end():
    """Smoke test: minimal spine simulation -> metrics check."""
    # 1. Setup: Create a dummy information field
    s = np.linspace(0, 0.4, 20)
    I = np.exp(-((s - 0.2) ** 2) / 0.01)  # Simple Gaussian bump
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # 2. Couplings: Compute metric and params
    g_eff = compute_countercurvature_metric(info)
    params = CounterCurvatureParams(chi_kappa=0.05)

    # 3. Solver: Run fast 2D beam (mocking kappa_rest via info gradient)
    kappa_rest = params.chi_kappa * dIds

    # Solve with standard properties
    theta, kappa_sol = solve_beam_static(
        s,
        kappa_target=kappa_rest,
        E_field=np.ones_like(s) * 1e9,
        M_active=np.zeros_like(s),
    )

    # 4. Metrics: Compute deviation from flat passive state
    metrics = geodesic_curvature_deviation(
        s,
        kappa_passive=np.zeros_like(s),  # Flat reference
        kappa_info=kappa_sol,
        g_eff=g_eff,
    )

    # 5. Assertions
    # We expect some deviation because chi_kappa > 0
    assert metrics["D_geo_norm"] > 0.0, "Should deviate from passive"
    assert np.isfinite(metrics["D_geo_norm"]), "Deviation should be finite"
    # g_eff should be positive definite
    assert np.all(g_eff > 0.0), "Metric must be positive definite"
    # Additional sanity checks
    assert len(kappa_sol) == len(s), "Curvature array length mismatch"
    assert len(theta) == len(s), "Angle array length mismatch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

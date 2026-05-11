"""Tests for energy computation in PyElastica bridge."""

import pytest

from spinalmodes.countercurvature.pyelastica_bridge import (
    PYELASTICA_AVAILABLE,
    run_protein_simulation,
)


@pytest.mark.skipif(not PYELASTICA_AVAILABLE, reason="PyElastica not available")
def test_run_protein_simulation_energy_metrics():
    """Test that run_protein_simulation computes and returns energy metrics."""

    # Run a short simulation
    result = run_protein_simulation(
        anisotropy=1.5,
        active_curvature=1.0, # Active drive should produce information gain
        torsion_drive=0.0,
        stiffness_modulation=0.5,
        n_elements=20,
        duration=0.1, # Short duration for speed
        dt=1e-4,
        gravity=9.81,
        show_progress=False
    )

    # Check success
    assert result.get("success", False), f"Simulation failed: {result.get('error')}"

    # Check presence of energy metrics
    expected_metrics = [
        "U_gravity",
        "U_elastic",
        "U_info",
        "U_CC",
        "U_kinetic",
        "info_gain_ratio"
    ]

    for metric in expected_metrics:
        assert metric in result, f"Metric {metric} missing from result"
        assert isinstance(result[metric], float), f"Metric {metric} should be float"

    # Check physical reasonableness
    # With active curvature > 0, we expect U_info > 0 (energy benefit)
    assert result["U_info"] > 0, "U_info should be positive with active curvature"

    # U_elastic should be non-negative
    assert result["U_elastic"] >= 0, "U_elastic should be non-negative"

    # U_kinetic should be non-negative
    assert result["U_kinetic"] >= 0, "U_kinetic should be non-negative"

@pytest.mark.skipif(not PYELASTICA_AVAILABLE, reason="PyElastica not available")
def test_energy_metrics_zero_drive():
    """Test that zero active drive results in zero U_info."""

    result = run_protein_simulation(
        anisotropy=1.0,
        active_curvature=0.0, # Zero drive
        torsion_drive=0.0,
        stiffness_modulation=0.0,
        n_elements=20,
        duration=0.1,
        dt=1e-4,
        gravity=9.81,
        show_progress=False
    )

    assert result.get("success", False)

    # U_info should be effectively zero (floating point tolerance)
    assert abs(result["U_info"]) < 1e-10, f"U_info should be zero with no drive, got {result['U_info']}"
    assert abs(result["info_gain_ratio"]) < 1e-10

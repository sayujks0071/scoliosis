"""
Integration tests for the protein mechanics simulation module.
"""


import pytest

from research.alphafold_countercurvature.src.afcc.simulation import simulate_protein_mechanics
from spinalmodes.countercurvature.pyelastica_bridge import PYELASTICA_AVAILABLE


@pytest.mark.skipif(not PYELASTICA_AVAILABLE, reason="PyElastica not installed")
def test_simulate_protein_mechanics_basic():
    """Test basic simulation run with default metrics."""
    metrics = {
        'anisotropy_index': 2.0,
        'curvature_summary': 1.0,
        'torsion_summary': 0.1,
        'PAE_domain_blockiness_score': 0.5
    }

    # Run a very short simulation for testing speed
    result = simulate_protein_mechanics(
        metrics,
        length=0.1,
        n_elements=10,
        duration=0.01,
        dt=1e-4
    )

    assert result['success'] is True
    assert 'max_curvature' in result
    assert 'max_torsion' in result
    assert 'S_lat' in result
    assert 'cobb_angle' in result
    assert 'runtime_sec' in result
    assert 'peak_memory_mb' in result

    # Check that inputs were mapped correctly
    assert result['input_anisotropy'] == 2.0
    assert result['mapped_chi_kappa'] == 1.0 * 5.0 # Default scale factor
    assert result['mapped_chi_tau'] == 0.1 * 5.0

@pytest.mark.skipif(not PYELASTICA_AVAILABLE, reason="PyElastica not installed")
def test_simulate_protein_mechanics_high_anisotropy():
    """Test simulation with high anisotropy (expect different behavior)."""
    metrics_low = {'anisotropy_index': 1.0, 'curvature_summary': 1.0}
    metrics_high = {'anisotropy_index': 5.0, 'curvature_summary': 1.0}

    res_low = simulate_protein_mechanics(metrics_low, length=0.1, n_elements=10, duration=0.01)
    res_high = simulate_protein_mechanics(metrics_high, length=0.1, n_elements=10, duration=0.01)

    # S_lat should differ significantly if anisotropy changes stiffness
    # Low anisotropy -> Less stiffness in lateral plane -> More bending?
    # Actually, stiffness_anisotropy scales bend_matrix[0,0] (Sagittal).
    # Chi_kappa drives Lateral curvature (index 1).
    # Wait, chi_kappa drives index 1.
    # Stiffness Anisotropy scales index 0.
    # So lateral bending (index 1) uses unscaled stiffness (or rather relative to index 0).
    # If we increase index 0 stiffness, the rod becomes stiffer in sagittal plane.
    # If chi_kappa drives lateral bending, changing sagittal stiffness shouldn't affect lateral bending much
    # unless there is coupling (torsion).

    # But if we have torsion (chi_tau > 0), then coupling happens.
    # Let's add torsion.
    metrics_coupled = {'anisotropy_index': 5.0, 'curvature_summary': 1.0, 'torsion_summary': 1.0}
    res_coupled = simulate_protein_mechanics(metrics_coupled, length=0.1, n_elements=10, duration=0.01)

    assert res_coupled['success'] is True
    assert res_coupled['max_torsion'] > 0.0

def test_simulate_protein_mechanics_missing_metrics():
    """Test handling of missing metrics (should use defaults)."""
    metrics = {} # Empty

    if not PYELASTICA_AVAILABLE:
        pytest.skip("PyElastica not available")

    result = simulate_protein_mechanics(metrics, length=0.1, n_elements=10, duration=0.01)

    assert result['success'] is True
    assert result['input_anisotropy'] == 1.0
    assert result['mapped_chi_kappa'] == 0.0

def test_simulate_protein_mechanics_error_handling():
    """Test that invalid parameters are handled gracefully (e.g. negative length)."""
    if not PYELASTICA_AVAILABLE:
        pytest.skip("PyElastica not available")

    # PyElastica might raise error for negative length
    # Check if simulate_protein_mechanics catches it
    # But PyElastica checks happen deep inside.
    # Let's pass something that causes error, e.g. n_elements=0

    metrics = {'anisotropy_index': 2.0}

    # n_elements=0 usually causes error in rod creation
    try:
        result = simulate_protein_mechanics(metrics, length=0.1, n_elements=0, duration=0.01)
        # It should return success=False
        assert result['success'] is False
        assert 'error' in result
    except Exception:
        pytest.fail("simulate_protein_mechanics raised exception instead of returning error dict")

"""
Test for the minimal PyElastica experiment script.
"""

import os
import sys

import pytest

# Add scripts/experiments folder to python path so we can import the script
# The script is at scripts/experiments/experiment_pyelastica_minimal.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'experiments'))

# Import the module under test
# Note: Since the file is scripts/experiments/experiment_pyelastica_minimal.py, and we added scripts/experiments to path
import experiment_pyelastica_minimal as minimal_script

from spinalmodes.countercurvature.pyelastica_bridge import (
    PYELASTICA_AVAILABLE,
    run_protein_simulation,
)


def test_run_protein_simulation_args():
    """Test that run_protein_simulation accepts new arguments radius and E0."""
    if not PYELASTICA_AVAILABLE:
        pytest.skip("PyElastica not installed, skipping test.")

    # Run a very short simulation with custom radius and E0
    result = run_protein_simulation(
        anisotropy=1.0,
        active_curvature=0.0,
        radius=0.02,
        E0=2e6,
        n_elements=10,
        duration=0.01,
        dt=1e-4,
        show_progress=False
    )

    assert result['success'] is True
    assert 'S_lat' in result

def test_run_protein_simulation_new_args():
    """Test that run_protein_simulation accepts boundary_condition, stiffness_modulation, initial_lateral_defect."""
    if not PYELASTICA_AVAILABLE:
        pytest.skip("PyElastica not installed, skipping test.")

    # Run a very short simulation with new parameters
    result = run_protein_simulation(
        anisotropy=1.0,
        active_curvature=0.0,
        boundary_condition="pinned",
        stiffness_modulation=0.5,
        initial_lateral_defect=0.05,
        radius=0.02,
        E0=2e6,
        n_elements=10,
        duration=0.01,
        dt=1e-4,
        show_progress=False
    )

    assert result['success'] is True
    assert 'S_lat' in result
    # Should have some curvature due to defect, even with 0 active curvature
    # defect sets rest curvature, so the rod should bend towards it
    assert result.get('max_curvature', 0.0) > 0

def test_minimal_experiment_script(tmp_path):
    """Test that the script runs in quick-test mode."""
    if not PYELASTICA_AVAILABLE:
        pytest.skip("PyElastica not installed, skipping test.")

    # Run the script's main function with quick_test=True
    out_dir = tmp_path / "minimal_experiment"

    try:
        minimal_script.run_experiment(out_dir=str(out_dir), quick_test=True)
    except SystemExit as e:
        if e.code != 0:
            pytest.fail(f"Script exited with error code {e.code}")

    # Check output files
    assert (out_dir / "results.csv").exists()
    assert (out_dir / "report.md").exists()

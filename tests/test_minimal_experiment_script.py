
import csv

# Import the module unconditionally.
# It should be importable since we added scripts to sys.path
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent / "scripts" / "experiments"))
import experiment_minimal_elastica


@pytest.mark.skipif(
    not experiment_minimal_elastica.PYELASTICA_AVAILABLE,
    reason="PyElastica not installed"
)
def test_run_experiment_integration(tmp_path):
    """
    Test that the minimal experiment script runs and produces expected output.
    Uses a very short simulation time and few elements for speed.
    """

    out_file = tmp_path / "test_results.csv"

    # Minimal configuration
    anisotropies = [1.0]
    chi_kappas = [0.0]
    chi_taus = [1.0] # Test non-zero torsion
    chi_es = [0.0]
    chi_ms = [0.0]
    boundary_condition = "fixed"
    n_elements = 10
    final_time = 0.01 # Very short time

    experiment_minimal_elastica.run_experiment(
        out_file=str(out_file),
        anisotropies=anisotropies,
        chi_kappas=chi_kappas,
        chi_taus=chi_taus,
        chi_es=chi_es,
        chi_ms=chi_ms,
        boundary_condition=boundary_condition,
        n_elements=n_elements,
        final_time=final_time,
        save_every=100
    )

    assert out_file.exists()

    with open(out_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    row = rows[0]

    # Check if new column exists
    assert "chi_tau" in row
    assert float(row["chi_tau"]) == 1.0

    # Check if metrics are present
    assert "max_curvature" in row
    assert "max_torsion" in row

    # Check for NaN (basic stability check)
    assert row["max_curvature"] != "nan"

@pytest.mark.skipif(
    not experiment_minimal_elastica.PYELASTICA_AVAILABLE,
    reason="PyElastica not installed"
)
def test_run_experiment_custom_info(tmp_path):
    """
    Test that custom info field parameters are passed correctly and recorded.
    """
    out_file = tmp_path / "test_custom_info.csv"

    experiment_minimal_elastica.run_experiment(
        out_file=str(out_file),
        anisotropies=[1.0],
        chi_kappas=[0.0],
        chi_taus=[0.0],
        chi_es=[0.0],
        chi_ms=[0.0],
        boundary_condition="fixed",
        n_elements=10,
        final_time=0.01,
        info_center=0.5,
        info_width=0.2,
        info_amplitude=0.3,
        save_every=100
    )

    assert out_file.exists()

    with open(out_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    row = rows[0]

    assert float(row["info_center"]) == 0.5
    assert float(row["info_width"]) == 0.2
    assert float(row["info_amplitude"]) == 0.3

@pytest.mark.skipif(
    not experiment_minimal_elastica.PYELASTICA_AVAILABLE,
    reason="PyElastica not installed"
)
def test_run_experiment_curvature_profiles(tmp_path):
    """
    Test that the curvature profile argument is accepted and recorded.
    """
    out_file = tmp_path / "test_profiles.csv"

    # Use harmonic profile
    experiment_minimal_elastica.run_experiment(
        out_file=str(out_file),
        anisotropies=[1.0],
        chi_kappas=[0.0],
        chi_taus=[0.0],
        chi_es=[0.0],
        chi_ms=[0.0],
        boundary_condition="fixed",
        n_elements=10,
        final_time=0.01,
        save_every=100,
        curvature_profile="harmonic"
    )

    assert out_file.exists()

    with open(out_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    row = rows[0]

    assert "curvature_profile" in row
    assert row["curvature_profile"] == "harmonic"

@pytest.mark.skipif(
    not experiment_minimal_elastica.PYELASTICA_AVAILABLE,
    reason="PyElastica not installed"
)
def test_run_experiment_active_coupling(tmp_path):
    """
    Test that non-zero active coupling parameters (chi_E, chi_M) are accepted.
    """
    out_file = tmp_path / "test_active.csv"

    experiment_minimal_elastica.run_experiment(
        out_file=str(out_file),
        anisotropies=[1.0],
        chi_kappas=[0.0],
        chi_taus=[0.0],
        chi_es=[0.5],
        chi_ms=[1.0],
        boundary_condition="fixed",
        n_elements=10,
        final_time=0.01,
        save_every=100
    )

    assert out_file.exists()

    with open(out_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    row = rows[0]

    assert float(row["chi_e"]) == 0.5
    assert float(row["chi_m"]) == 1.0

@pytest.mark.skipif(
    not experiment_minimal_elastica.PYELASTICA_AVAILABLE,
    reason="PyElastica not installed"
)
def test_run_experiment_tapering(tmp_path):
    """
    Test that taper_ratios argument is accepted and recorded.
    """
    out_file = tmp_path / "test_taper.csv"

    experiment_minimal_elastica.run_experiment(
        out_file=str(out_file),
        anisotropies=[1.0],
        chi_kappas=[0.0],
        chi_taus=[0.0],
        chi_es=[0.0],
        chi_ms=[0.0],
        taper_ratios=[0.5, 1.0],
        boundary_condition="fixed",
        n_elements=10,
        final_time=0.01,
        save_every=100
    )

    assert out_file.exists()

    with open(out_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2

    tapers = [float(r["taper_ratio"]) for r in rows]
    assert 0.5 in tapers
    assert 1.0 in tapers

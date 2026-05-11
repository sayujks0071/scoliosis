
import csv
import sys
from pathlib import Path

import pytest

# Ensure scripts/experiments is in path
sys.path.append(str(Path(__file__).parent.parent / "scripts" / "experiments"))

import experiment_protein_simulation_pyelastica

from spinalmodes.countercurvature.pyelastica_bridge import PYELASTICA_AVAILABLE


@pytest.mark.skipif(
    not PYELASTICA_AVAILABLE,
    reason="PyElastica not installed"
)
def test_run_protein_experiment_integration(tmp_path):
    """
    Test that the protein physics experiment script runs and produces expected output.
    """

    out_file = tmp_path / "test_protein_results.csv"

    # Use specific scenario to limit run time
    anisotropies = [2.0]
    active_curvatures = [0.5]

    # Run with short time and few elements
    experiment_protein_simulation_pyelastica.run_experiment(
        out_file=str(out_file),
        anisotropies=anisotropies,
        active_curvatures=active_curvatures,
        n_elements=10,
        duration=0.01,
        dt=1e-4
    )

    assert out_file.exists()

    with open(out_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    row = rows[0]

    # Verify scenario data
    # bio_label logic: 2.0 anisotropy, 0.5 active -> "Anisotropy=2.0 | Homeostatic (Low Gain)"
    assert "Anisotropy=2.0" in row["bio_label"]
    assert float(row["input_anisotropy"]) == 2.0

    # Verify metrics
    assert "max_curvature" in row
    assert float(row["max_curvature"]) >= 0.0
    assert "runtime_sec" in row
    assert "peak_memory_mb" in row

@pytest.mark.skipif(
    not PYELASTICA_AVAILABLE,
    reason="PyElastica not installed"
)
def test_run_protein_experiment_multiple_scenarios(tmp_path):
    """
    Test running multiple scenarios.
    """
    out_file = tmp_path / "test_multi_results.csv"

    anisotropies = [1.0, 5.0]
    active_curvatures = [0.5]

    experiment_protein_simulation_pyelastica.run_experiment(
        out_file=str(out_file),
        anisotropies=anisotropies,
        active_curvatures=active_curvatures,
        n_elements=10,
        duration=0.01
    )

    with open(out_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    bio_labels = {r["bio_label"] for r in rows}
    # Anisotropy 1.0 -> Marfan
    # Anisotropy 5.0 -> WildType
    assert any("Marfan" in l for l in bio_labels)
    assert any("WildType" in l for l in bio_labels)

"""
Integration test for the protein simulation experiment script.

This test ensures that `scripts/experiments/experiment_protein_simulation_pyelastica.py`
can be executed successfully and produces the expected artifacts.
"""

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Path to the experiment script
REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "experiments" / "experiment_protein_simulation_pyelastica.py"

def test_experiment_script_execution(tmp_path):
    """
    Test that the experiment script runs without error in quick-test mode
    and generates valid output files.
    """
    if not SCRIPT_PATH.exists():
        pytest.fail(f"Experiment script not found at {SCRIPT_PATH}")

    # Ensure output directory is clean-ish
    output_csv = tmp_path / "results.csv"

    # Construct command
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--quick-test",
        "--out-file", str(output_csv)
    ]

    # Run the script
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
        cwd=REPO_ROOT,
    )

    # Check for successful execution
    assert result.returncode == 0, f"Script failed with error:\n{result.stderr}"

    # Verify artifacts
    assert output_csv.exists(), "Output CSV was not created."

    # Verify CSV content
    with open(output_csv, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) > 0, "CSV is empty."

        # Check for key columns
        expected_columns = [
            "bio_label", "input_anisotropy", "cobb_angle", "u_cc", "runtime_sec"
        ]
        for col in expected_columns:
            assert col in rows[0], f"Column {col} missing in CSV."

    # Verify Markdown report
    md_file = output_csv.with_suffix(".md")
    assert md_file.exists(), "Markdown report was not created."

    # Check stdout for success message
    assert "Experiment Summary" in result.stdout or "Parameters" in result.stdout

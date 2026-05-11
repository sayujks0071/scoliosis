"""
Test for Hydraulic Buckling Experiment.

Verifies that the experiment script runs successfully and produces expected artifacts.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def test_hydraulic_buckling_execution(tmp_path):
    """
    Run the experiment script with --quick-test flag.
    Verify:
    1. Exit code is 0 (Success).
    2. Output artifacts exist.
    """
    script_path = REPO_ROOT / "scripts" / "experiments" / "experiment_hydraulic_buckling.py"
    figures_dir = tmp_path / "figures"
    reports_dir = tmp_path / "reports"

    # Run script
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--quick-test",
            "--figures-dir",
            str(figures_dir),
            "--reports-dir",
            str(reports_dir),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    # Check execution
    if result.returncode != 0:
        print("Script execution failed:")
        print(result.stdout)
        print(result.stderr)
    assert result.returncode == 0, "Experiment script failed to execute."

    # Check artifacts
    assert (figures_dir / "hydraulic_buckling_dynamics.png").exists(), "Plot not generated."
    assert (reports_dir / "hydraulic_buckling_report.md").exists(), "Report not generated."

    # Check if report contains content
    report_content = (reports_dir / "hydraulic_buckling_report.md").read_text()
    assert "Hydraulic Buckling Experiment Report" in report_content
    assert "## Results Summary" in report_content
    assert "## Proprioceptive Mismatch" in report_content

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmpdir:
        test_hydraulic_buckling_execution(Path(tmpdir))
    print("Test Passed: Hydraulic Buckling Experiment verified.")

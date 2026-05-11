import csv
import sys
from pathlib import Path

import pytest

# Add scripts directory to path to import experiment scripts
scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.append(str(scripts_dir))

try:
    from experiment_optimization_failure import run_optimization_failure_sweep
except ImportError:
    pytest.fail(f"Could not import experiment_optimization_failure from {scripts_dir}")

def test_optimization_failure_experiment_quick_run(tmp_path):
    """Test that the optimization failure experiment runs end-to-end with minimal parameters."""
    output_file = tmp_path / "failure_output.csv"

    chi_kappas = [0.0, 5.0]
    sigma_noises = [0.0, 0.5]
    n_trials = 1

    run_optimization_failure_sweep(
        out_file=str(output_file),
        chi_kappas=chi_kappas,
        sigma_noises=sigma_noises,
        n_trials=n_trials,
        n_elements=10,       # Low resolution
        final_time=0.1,      # Short duration
        seed=42
    )

    # Verify CSV output
    assert output_file.exists()
    assert output_file.stat().st_size > 0

    with open(output_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        # 2 chi * 2 sigma * 1 trial = 4 rows
        assert len(rows) == 4

        # Check some fields
        assert "cobb_angle" in rows[0]
        assert "U_CC" in rows[0]
        assert "chi_kappa" in rows[0]
        assert "sigma_noise" in rows[0]

    # Verify Markdown report generation
    md_file = output_file.with_suffix(".md")
    assert md_file.exists()
    with open(md_file, "r") as f:
        content = f.read()
        assert "Optimization Failure: Exploding Gradient Report" in content
        assert "chi_kappa" in content

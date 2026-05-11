import csv
import sys
from pathlib import Path

import pytest

# Add scripts directory to path to import experiment scripts
# Assuming this test is run from repo root or tests/, scripts is one level up or sibling
scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.append(str(scripts_dir))

# Import the module. Note: experiment scripts usually have if __name__ == "__main__": blocks
try:
    from experiment_spinal_jetlag import run_spinal_jetlag_experiment
except ImportError:
    pytest.fail(f"Could not import experiment_spinal_jetlag from {scripts_dir}")

def test_spinal_jetlag_experiment_quick_run(tmp_path):
    """Test that the spinal jetlag experiment runs end-to-end with minimal parameters."""
    output_file = tmp_path / "jetlag_output.csv"

    conditions = [
        {"name": "test_entrained", "chi_0": 5.0, "amplitude": 0.5, "phi": 0.0, "gravity": 9.81, "K_ent": 1.0},
        {"name": "test_jetlagged", "chi_0": 5.0, "amplitude": 0.5, "phi": 3.14, "gravity": 9.81, "K_ent": 1.0},
    ]

    # Run minimal experiment
    run_spinal_jetlag_experiment(
        out_file=str(output_file),
        conditions=conditions,
        n_cycles=2,         # Minimal cycles
        T_circadian=24.0,
        n_elements=10,      # Low resolution
        cycle_duration=0.1, # Short duration
    )

    # Verify CSV output
    assert output_file.exists()
    assert output_file.stat().st_size > 0

    with open(output_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        # 2 conditions * 2 cycles = 4 rows
        assert len(rows) == 4

        # Check some fields
        assert "cobb_angle" in rows[0]
        assert "U_CC" in rows[0]
        assert rows[0]["condition"] == "test_entrained"
        assert rows[2]["condition"] == "test_jetlagged"

    # Verify Markdown report generation
    md_file = output_file.with_suffix(".md")
    assert md_file.exists()
    with open(md_file, "r") as f:
        content = f.read()
        assert "Spinal Jetlag Experiment Report" in content
        assert "test_entrained" in content

from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "experiment_energy_deficit_window.py"

def test_energy_deficit_output(tmp_path):
    """
    Verify that the energy deficit experiment generates the expected output files
    and that the data follows the qualitative trends required by the hypothesis.
    """
    csv_path = tmp_path / "energy_deficit_window.csv"
    png_path = tmp_path / "energy_deficit_window.png"

    # Run the experiment script
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--output-csv",
            str(csv_path),
            "--output-figure",
            str(png_path),
            "--skip-manuscript-figure",
        ],
        check=True,
        cwd=REPO_ROOT,
    )

    assert csv_path.exists(), "CSV output not found."
    assert png_path.exists(), "PNG output not found."

    # Analyze CSV data
    df = pd.read_csv(csv_path)

    # Check columns
    expected_cols = ["L", "P_counter", "S_proprio_alpha05", "S_proprio_alpha10", "Cobb_angle", "D_geo"]
    for col in expected_cols:
        assert col in df.columns, f"Missing column {col}"

    # Check scaling trends
    # P_counter should scale roughly as L^2
    # We check if P_counter increases with L
    assert df["P_counter"].iloc[-1] > df["P_counter"].iloc[0], "P_counter should increase with L."

    # Check if Demand (P_counter) grows faster than Supply (S_proprio)
    # Ratio P/S at start vs end
    ratio_start = df["P_counter"].iloc[0] / df["S_proprio_alpha05"].iloc[0]
    ratio_end = df["P_counter"].iloc[-1] / df["S_proprio_alpha05"].iloc[-1]

    assert ratio_end > ratio_start, "Demand should outpace Supply (Energy Deficit Window logic)."

    # Check L_crit existence
    # We expect a crossing, or at least a trend towards crossing if not crossed in range
    # In our simulation we found L_crit ~ 0.35, which is inside [0.25, 0.55]

    # Find crossing
    diff = df["P_counter"] - df["S_proprio_alpha05"]
    has_crossing = np.any(np.diff(np.sign(diff)))
    assert has_crossing, "Should find a crossing point (L_crit) between Demand and Supply."

    # Check Cobb Angle consistency
    # Under fixed curvature assumption, Cobb angle should scale linearly with L?
    # Or if kappa is constant, Angle = kappa * L.
    # So Angle should increase linearly.
    assert df["Cobb_angle"].iloc[-1] > df["Cobb_angle"].iloc[0], "Cobb angle should increase with L under fixed curvature."

if __name__ == "__main__":
    # Manually run the test function if executed as script
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_energy_deficit_output(Path(tmpdir))
        print("Test passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

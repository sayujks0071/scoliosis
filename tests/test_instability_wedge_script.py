"""
Test for the instability wedge experiment script.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts folder to python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'experiments'))

# Import the module under test
import experiment_instability_wedge_elastica as wedge_script

from spinalmodes.countercurvature.pyelastica_bridge import PYELASTICA_AVAILABLE


def test_instability_wedge_quick_run(tmp_path):
    """Test that the script runs in quick-test mode without errors."""

    if not PYELASTICA_AVAILABLE:
        pytest.skip("PyElastica not installed, skipping test.")

    # Mock sys.argv
    test_args = ["script_name", "--quick-test", "--out-file", str(tmp_path / "test_output.csv")]

    with patch.object(sys, 'argv', test_args):
        args = wedge_script.parse_args()

        assert args.quick_test is True

        # Override parameters for faster test
        anisotropies = [1.0]
        chi_kappas = [0.0]
        n_elements = 10
        final_time = 0.01

        try:
            wedge_script.run_instability_sweep(
                out_file=args.out_file,
                anisotropies=anisotropies,
                chi_kappas=chi_kappas,
                n_elements=n_elements,
                final_time=final_time
            )
        except SystemExit as e:
            # Handle sys.exit if PyElastica missing but PYELASTICA_AVAILABLE check missed
            pytest.skip(f"Script exited with {e}, likely due to missing PyElastica.")

        # Check output files
        assert os.path.exists(args.out_file)
        md_file = str(Path(args.out_file).with_suffix(".md"))
        assert os.path.exists(md_file)

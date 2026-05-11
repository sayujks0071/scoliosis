import sys
import unittest
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("Bio")

# Add alphafold_analysis to path
# Adjusted path to point to legacy archive where the script resides
sys.path.append(str(Path(__file__).parent.parent / "archive/alphafold_analysis_legacy"))

from analyze_bcc_structures import calculate_backbone_curvature


class TestCurvatureOptimization(unittest.TestCase):
    def test_calculate_backbone_curvature(self):
        # Setup data
        N = 100
        coords = np.random.rand(N, 3)
        window = 7

        # Calculate using the NEW vectorized function
        c_new, m_new, s_new = calculate_backbone_curvature(coords, window)

        # Calculate using MANUAL loop (original logic)
        curvatures = []
        for i in range(window, len(coords) - window):
            window_coords = coords[i-window:i+window+1]
            centroid = np.mean(window_coords, axis=0)
            distances = np.linalg.norm(window_coords - centroid, axis=1)
            mean_dist = np.mean(distances)
            if mean_dist > 1e-6:
                curvatures.append(1.0 / mean_dist)
            else:
                curvatures.append(0.0)

        c_orig = np.array(curvatures)
        m_orig = np.mean(c_orig)
        s_orig = np.std(c_orig)

        # Verify
        np.testing.assert_allclose(c_new, c_orig, rtol=1e-5, err_msg="Curvatures array mismatch")
        self.assertAlmostEqual(m_new, m_orig, places=5, msg="Mean curvature mismatch")
        self.assertAlmostEqual(s_new, s_orig, places=5, msg="Std curvature mismatch")

    def test_calculate_backbone_curvature_masked(self):
        # Setup data
        N = 100
        coords = np.random.rand(N, 3)
        mask = np.random.rand(N) > 0.5
        window = 7

        # Calculate using the NEW vectorized function with mask
        c_new, m_new, s_new = calculate_backbone_curvature(coords, window, mask=mask)

        # Calculate using MANUAL loop (original logic)
        curvatures = []
        for i in range(window, len(coords) - window):
            if not mask[i - window:i + window + 1].all():
                continue

            window_coords = coords[i-window:i+window+1]
            centroid = np.mean(window_coords, axis=0)
            distances = np.linalg.norm(window_coords - centroid, axis=1)
            mean_dist = np.mean(distances)
            if mean_dist > 1e-6:
                curvatures.append(1.0 / mean_dist)
            else:
                curvatures.append(0.0)

        if len(curvatures) > 0:
            c_orig = np.array(curvatures)
            m_orig = np.mean(c_orig)
            s_orig = np.std(c_orig)

            # Verify
            np.testing.assert_allclose(c_new, c_orig, rtol=1e-5, err_msg="Curvatures array mismatch (masked)")
            self.assertAlmostEqual(m_new, m_orig, places=5, msg="Mean curvature mismatch (masked)")
            self.assertAlmostEqual(s_new, s_orig, places=5, msg="Std curvature mismatch (masked)")
        else:
            self.assertEqual(len(c_new), 0)

if __name__ == '__main__':
    unittest.main()

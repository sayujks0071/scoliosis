import unittest

import numpy as np

from research.alphafold_countercurvature.src.afcc.metrics import MetricsAnalyzer


class TestTorsionCorrectness(unittest.TestCase):
    def test_torsion_math(self):
        analyzer = MetricsAnalyzer()
        # Define 4 points defining a torsion angle of 90 degrees
        # A=(1,0,0), B=(0,0,0), C=(0,1,0), D=(0,1,1)
        # Bond vectors:
        # b1 = B-A = (-1, 0, 0)
        # b2 = C-B = (0, 1, 0)
        # b3 = D-C = (0, 0, 1)

        # n1 = b1 x b2 = (-1,0,0) x (0,1,0) = (0,0,-1)
        # n2 = b2 x b3 = (0,1,0) x (0,0,1) = (1,0,0)

        # cos_phi = (n1 . n2) / (|n1||n2|) = 0 / 1 = 0 -> phi = 90 deg (pi/2)

        # Sign check: dot(b1, n2) = (-1,0,0) . (1,0,0) = -1
        # Sign is negative.
        # So torsion should be -pi/2

        coords = np.array([
            [1,0,0],
            [0,0,0],
            [0,1,0],
            [0,1,1]
        ], dtype=float)

        res = analyzer.calculate_torsion(coords)

        # Expected: [NaN, -pi/2, NaN] assuming length 4
        # Wait, result size is len(coords).
        # result[1:-2] = torsion.
        # Indices: 0, 1, 2, 3.
        # Torsion is defined for the bond B-C (index 1).
        # result[1] should be the value.

        # Note: In the code:
        # result = np.full(len(coords), np.nan)
        # result[1:-2] = torsion
        # If len=4, 1:-2 is 1:2, so index 1 only. Correct.

        torsion_val = res[1]
        self.assertAlmostEqual(torsion_val, -np.pi/2, places=5)

if __name__ == '__main__':
    unittest.main()

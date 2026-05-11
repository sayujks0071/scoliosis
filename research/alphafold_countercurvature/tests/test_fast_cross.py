
import unittest

import numpy as np

from research.alphafold_countercurvature.src.afcc.metrics import MetricsAnalyzer


class TestFastCrossProduct(unittest.TestCase):
    def test_random_vectors(self):
        """Test that _cross_product_fast produces results identical to np.cross."""
        N = 1000
        a = np.random.randn(N, 3)
        b = np.random.randn(N, 3)

        expected = np.cross(a, b)

        # This should fail if the method is missing or incorrect
        result = MetricsAnalyzer._cross_product_fast(a, b)

        np.testing.assert_allclose(result, expected, rtol=1e-5)

if __name__ == '__main__':
    unittest.main()

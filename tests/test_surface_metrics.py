
import unittest

import numpy as np
from afcc.metrics import MetricsAnalyzer


class TestSurfaceMetrics(unittest.TestCase):
    def setUp(self):
        self.analyzer = MetricsAnalyzer()

    def test_isolated_cluster_high_conf(self):
        np.random.seed(42)
        # Cluster 1: 25 points (buried)
        c1 = np.random.rand(25, 3)
        n1 = ['ALA'] * 25
        p1 = [90.0] * 25

        # Cluster 2: 1 point far away (exposed)
        c2 = np.array([[20.0, 20.0, 20.0]])
        n2 = ['ARG'] # Charged
        p2 = [90.0]

        coords = np.vstack([c1, c2])
        resnames = np.array(n1 + n2)
        plddts = np.array(p1 + p2)

        metrics = self.analyzer.analyze_structure(coords=coords, resnames=resnames, plddt_scores=plddts)

        # Fraction exposed. Total 26.
        # c1 is dense, likely 0 exposed. c2 is 1 exposed.
        # exposed_count approx 1. fraction = 1/26 ~ 0.038
        self.assertGreater(metrics['exposed_surface_proxy'], 0.0)
        self.assertLess(metrics['exposed_surface_proxy'], 0.5)

        # Charged score: of the exposed (1), 1 is charged.
        # Note: If any from c1 leak as exposed (surface of ball), they are ALA (uncharged).
        # So score might be < 1.0 if c1 has surface points.
        # But for this test, let's just check it's non-zero.
        self.assertGreater(metrics['charged_patch_score'], 0.0)

    def test_low_confidence_exclusion(self):
        """
        1 point far away (exposed).
        But Low Confidence (pLDDT=50).
        Should be ignored for charged patch calculation (requires HC).
        """
        coords = np.array([[20.0, 20.0, 20.0]])
        resnames = np.array(['ARG'])
        plddts = np.array([50.0]) # Low confidence

        metrics = self.analyzer.analyze_structure(coords=coords, resnames=resnames, plddt_scores=plddts)

        # analyze_structure logic:
        # plddt_mask = (plddts >= 70)
        # exposed calculation uses all coords for neighbor count, but we check if result masks/counts apply.
        # exposed_fraction uses all points.
        # charged_patch_score uses mask_hc & mask_exposed.

        # exposed_fraction: 1 point, 0 neighbors -> exposed. Fraction 1.0.
        self.assertEqual(metrics['exposed_surface_proxy'], 1.0)

        # charged_patch_score: mask_hc is False. exposed_hc_count = 0. score = 0.0.
        self.assertEqual(metrics['charged_patch_score'], 0.0)

    def test_empty(self):
        coords = np.array([])
        resnames = np.array([])
        plddts = np.array([])
        metrics = self.analyzer.analyze_structure(coords=coords, resnames=resnames, plddt_scores=plddts)
        self.assertEqual(metrics['exposed_surface_proxy'], 0.0)
        self.assertEqual(metrics['charged_patch_score'], 0.0)

if __name__ == '__main__':
    unittest.main()

import unittest
from pathlib import Path

import numpy as np
from Bio.PDB.Atom import Atom
from Bio.PDB.Chain import Chain
from Bio.PDB.Model import Model
from Bio.PDB.Residue import Residue
from Bio.PDB.Structure import Structure

from research.alphafold_countercurvature.src.afcc.afdb import AlphaFoldFetcher
from research.alphafold_countercurvature.src.afcc.metrics import MetricsAnalyzer


class TestAFCCPipeline(unittest.TestCase):

    def setUp(self):
        self.analyzer = MetricsAnalyzer()

    def create_dummy_structure(self, coords):
        # Helper to create a simple structure
        s = Structure("test")
        m = Model(0)
        c = Chain("A")
        s.add(m)
        m.add(c)

        for i, coord in enumerate(coords):
            res = Residue((" ", i, " "), "GLY", " ")
            atom = Atom("CA", coord, 10.0, 1.0, " ", "CA", i, "C")
            res.add(atom)
            c.add(res)
        return s

    def test_rg_calculation(self):
        # 3 points forming a triangle
        coords = np.array([[0,0,0], [1,0,0], [0,1,0]], dtype=float)

        # Test directly with coords array as per new API
        rg = self.analyzer.calculate_rg(coords)

        # Center of mass = (1/3, 1/3, 0)
        # Distances sq from COM:
        # (0-1/3)^2 + (0-1/3)^2 = 2/9
        # (1-1/3)^2 + (0-1/3)^2 = 4/9 + 1/9 = 5/9
        # (0-1/3)^2 + (1-1/3)^2 = 1/9 + 4/9 = 5/9
        # Mean sq dist = (2/9 + 5/9 + 5/9) / 3 = 12/27 = 4/9
        # Sqrt(4/9) = 2/3 = 0.666...

        self.assertAlmostEqual(rg, 0.6666666, places=5)

    def test_anisotropy_linear(self):
        # Linear structure
        coords = np.array([[0,0,0], [1,0,0], [2,0,0]], dtype=float)

        # Test directly with coords array as per new API
        metrics = self.analyzer.calculate_anisotropy(coords)

        # Should be highly anisotropic (l3 >> l1, l2)
        # l1, l2 should be near 0 (planar/linear)

        self.assertGreater(metrics['anisotropy_ratio'], 10.0)

    def test_afdb_fetcher_init(self):
        # Just check it initializes without error
        fetcher = AlphaFoldFetcher(Path("."), Path("manifest.csv"), dry_run="full")
        self.assertEqual(fetcher.dry_run_mode, "full")

    def test_pae_metrics(self):
        # Create a synthetic case with 2 domains
        N = 30
        pae = np.zeros((N, N))
        plddt = np.array([50]*N)

        # Seg 1: 0-10 (10 residues) -> High confidence
        plddt[0:10] = 90
        # Seg 2: 20-30 (10 residues) -> High confidence
        plddt[20:30] = 90

        # Fill blocks
        # Intra 1: 2.0
        pae[0:10, 0:10] = 2.0
        # Intra 2: 4.0
        pae[20:30, 20:30] = 4.0

        # Inter 1-2: 10.0
        pae[0:10, 20:30] = 10.0
        # Inter 2-1: 8.0
        pae[20:30, 0:10] = 8.0

        metrics = self.analyzer.calculate_pae_metrics(pae, plddt)

        # Expected:
        # Intra means: [2.0, 4.0] -> mean = 3.0
        # Inter means: [10.0, 8.0] -> mean = 9.0
        # Blockiness = 9.0 / 3.0 = 3.0

        self.assertEqual(metrics['predicted_domain_segments'], 2)
        self.assertAlmostEqual(metrics['pae_blockiness'], 3.0, places=5)

if __name__ == '__main__':
    unittest.main()

import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np

from research.alphafold_countercurvature.src.afcc.structure import StructureParser


class TestParserOptimization(unittest.TestCase):
    def setUp(self):
        self.parser = StructureParser()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.pdb_path = Path(self.tmp_dir.name) / "test.pdb"

        # Create a dummy PDB file
        with open(self.pdb_path, "w") as f:
            f.write("ATOM      1  N   ALA A   1      10.000  10.000  10.000  1.00 90.00           N\n")
            f.write("ATOM      2  CA  ALA A   1      11.000  11.000  11.000  1.00 90.00           C\n")
            f.write("ATOM      3  C   ALA A   1      12.000  12.000  12.000  1.00 90.00           C\n")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_cache_creation_is_uncompressed(self):
        # Initial parse - should create cache
        coords, plddt, resnames = self.parser.fast_parse_pdb_arrays(self.pdb_path)

        # Verify data correctness
        expected_coords = np.array([[11.0, 11.0, 11.0]])
        expected_plddt = np.array([90.0])
        expected_resnames = np.array(['ALA'])

        np.testing.assert_array_equal(coords, expected_coords)
        np.testing.assert_array_equal(plddt, expected_plddt)
        np.testing.assert_array_equal(resnames, expected_resnames)

        cache_path = self.pdb_path.with_suffix('.pdb.cache.npz')
        self.assertTrue(cache_path.exists(), "Cache file should be created")

        # Check compression type
        with zipfile.ZipFile(cache_path, 'r') as zf:
            for info in zf.infolist():
                # zipfile.ZIP_STORED = 0 (uncompressed)
                # zipfile.ZIP_DEFLATED = 8 (compressed)
                # We expect ZIP_STORED (0) after optimization
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED, f"File {info.filename} is compressed (type {info.compress_type}), expected uncompressed (0)")

    def test_legacy_compressed_read(self):
        # Manually create a compressed cache file
        coords = np.array([[11.0, 11.0, 11.0]])
        plddt = np.array([90.0])
        resnames = np.array(['ALA'])

        cache_path = self.pdb_path.with_suffix('.pdb.cache.npz')
        np.savez_compressed(cache_path, coords=coords, plddt=plddt, resnames=resnames)

        # Ensure timestamp is newer than PDB so it reads the cache
        # (Actually fast_parse_pdb_arrays checks: if cache_path.stat().st_mtime >= pdb_path.stat().st_mtime)
        # Writing to cache_path just now should make it newer than pdb_path written in setUp

        # Parse - should read from cache
        coords_read, plddt_read, resnames_read = self.parser.fast_parse_pdb_arrays(self.pdb_path)

        np.testing.assert_array_equal(coords_read, coords)
        np.testing.assert_array_equal(plddt_read, plddt)
        np.testing.assert_array_equal(resnames_read, resnames)

if __name__ == '__main__':
    unittest.main()

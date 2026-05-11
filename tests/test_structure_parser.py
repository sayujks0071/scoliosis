import json
import os

import numpy as np
import pytest

from research.alphafold_countercurvature.src.afcc.structure import StructureParser


def test_fast_parse_pdb_arrays_standard(tmp_path):
    """Test fast parsing of standard ATOM records."""
    pdb_content = """
ATOM      1  N   MET A   1     -48.324 -15.228   4.203  1.00 31.92           N
ATOM      2  CA  MET A   1     -49.692 -14.663   4.267  1.00 31.92           C
ATOM      3  C   MET A   1     -49.650 -13.259   3.682  1.00 31.92           C
ATOM      4  O   MET A   1     -48.567 -12.692   3.614  1.00 31.92           O
ATOM      5  N   ALA A   2     -50.768 -12.807   3.126  1.00 35.28           N
ATOM      6  CA  ALA A   2     -50.888 -11.781   2.071  1.00 35.28           C
"""
    pdb_file = tmp_path / "test.pdb"
    pdb_file.write_text(pdb_content.strip())

    parser = StructureParser()
    coords, plddt, resnames = parser.fast_parse_pdb_arrays(pdb_file)

    assert coords is not None
    assert len(coords) == 2
    assert len(plddt) == 2
    assert len(resnames) == 2

    # Check MET
    assert np.allclose(coords[0], [-49.692, -14.663, 4.267])
    assert plddt[0] == 31.92
    assert resnames[0] == "MET"

    # Check ALA
    assert np.allclose(coords[1], [-50.888, -11.781, 2.071])
    assert plddt[1] == 35.28
    assert resnames[1] == "ALA"

def test_fast_parse_pdb_arrays_altloc(tmp_path):
    """Test handling of alternate locations (should keep ' ' or 'A')."""
    pdb_content = """
ATOM      1  CA  MET A   1      10.000  10.000  10.000  1.00 50.00           C
ATOM      2  CA AMET A   2      20.000  20.000  20.000  0.50 60.00           C
ATOM      3  CA BMET A   2      21.000  21.000  21.000  0.50 60.00           C
"""
    # Note: AltLoc is col 17 (index 16). ' ' for atom 1. 'A' for atom 2. 'B' for atom 3.
    # We expect to keep 1 and 2, drop 3.

    pdb_file = tmp_path / "test_alt.pdb"
    pdb_file.write_text(pdb_content.strip())

    parser = StructureParser()
    coords, plddt, resnames = parser.fast_parse_pdb_arrays(pdb_file)

    assert len(coords) == 2
    assert coords[0][0] == 10.0
    assert coords[1][0] == 20.0

def test_fast_parse_pdb_arrays_missing_file(tmp_path):
    parser = StructureParser()
    coords, _, _ = parser.fast_parse_pdb_arrays(tmp_path / "nonexistent.pdb")
    assert coords is None

@pytest.fixture
def parser():
    return StructureParser()

def test_parse_pae_json(tmp_path, parser):
    """Test parsing standard JSON PAE file."""
    pae_data = [[0, 10], [10, 0]]
    json_content = [{"predicted_aligned_error": pae_data}]

    pae_file = tmp_path / "test.json"
    with open(pae_file, 'w') as f:
        json.dump(json_content, f)

    # First parse: should read JSON and create .npy cache
    arr = parser.parse_pae(pae_file)
    assert arr is not None
    assert arr.shape == (2, 2)
    assert arr[0, 1] == 10
    assert arr.dtype == np.uint8

    # Check cache creation
    cache_npy = pae_file.with_suffix('.pae.npy')
    assert cache_npy.exists()

    # Verify cache content
    cached_arr = np.load(cache_npy)
    assert np.array_equal(cached_arr, arr)

def test_parse_pae_cache_usage(tmp_path, parser):
    """Test that NPY cache is used if available."""
    pae_file = tmp_path / "test.json"
    # Create dummy JSON (should not be read if cache exists)
    with open(pae_file, 'w') as f:
        f.write("INVALID JSON")

    # Create valid NPY cache
    cache_npy = pae_file.with_suffix('.pae.npy')
    data = np.array([[5, 5], [5, 5]], dtype=np.uint8)
    np.save(cache_npy, data)

    # Ensure timestamps are correct (cache >= source)
    # Touch json then cache
    os.utime(pae_file, (1000, 1000))
    os.utime(cache_npy, (1001, 1001))

    arr = parser.parse_pae(pae_file)
    assert np.array_equal(arr, data)

def test_parse_pae_legacy_upgrade(tmp_path, parser):
    """Test upgrade from .npz to .npy."""
    pae_file = tmp_path / "test.json"
    with open(pae_file, 'w') as f:
        f.write("INVALID JSON") # Should not be read

    # Create legacy .npz cache
    cache_npz = pae_file.with_suffix('.pae.npz')
    data = np.array([[1, 2], [3, 4]], dtype=np.int64) # Legacy uses int64
    np.savez_compressed(cache_npz, pae=data)

    # Ensure timestamps
    os.utime(pae_file, (1000, 1000))
    os.utime(cache_npz, (1001, 1001))

    # Parse: should load NPZ and save NPY
    arr = parser.parse_pae(pae_file)
    assert np.array_equal(arr, data)

    # Check NPY creation
    cache_npy = pae_file.with_suffix('.pae.npy')
    assert cache_npy.exists()

    # Check it was converted to uint8
    npy_data = np.load(cache_npy)
    assert npy_data.dtype == np.uint8
    assert np.array_equal(npy_data, data)

def test_parse_pae_corrupted_cache(tmp_path, parser):
    """Test fallback if cache is corrupted."""
    pae_data = [[0, 1], [1, 0]]
    json_content = [{"predicted_aligned_error": pae_data}]

    pae_file = tmp_path / "test.json"
    with open(pae_file, 'w') as f:
        json.dump(json_content, f)

    # Create corrupted NPY
    cache_npy = pae_file.with_suffix('.pae.npy')
    with open(cache_npy, 'wb') as f:
        f.write(b"CORRUPTED DATA")

    os.utime(pae_file, (1000, 1000))
    os.utime(cache_npy, (1001, 1001))

    # Should fall back to JSON
    arr = parser.parse_pae(pae_file)
    assert arr is not None
    assert np.array_equal(arr, np.array(pae_data))

    # Should overwrite corrupted cache with valid one
    valid_cache = np.load(cache_npy)
    assert np.array_equal(valid_cache, arr)

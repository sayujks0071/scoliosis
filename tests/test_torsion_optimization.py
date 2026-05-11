
import numpy as np
import pytest

pytest.importorskip("Bio")

from research.alphafold_countercurvature.src.afcc.metrics import MetricsAnalyzer


def test_torsion_optimization_correctness():
    """
    Verifies that the optimized calculate_torsion produces identical results
    to the legacy/unoptimized version (conceptually).
    Since we don't have the unoptimized version code available here as a separate function,
    we rely on checking against a known-correct calculation or simply ensuring
    the math holds up.

    Actually, to be rigorous, I will implement the unoptimized logic here and compare.
    """

    # 1. Generate data
    np.random.seed(42)
    N = 100
    coords = np.cumsum(np.random.randn(N, 3), axis=0)

    analyzer = MetricsAnalyzer()

    # 2. Run current implementation (which will be optimized)
    torsion_optimized = analyzer.calculate_torsion(coords)

    # 3. Run "legacy" implementation (unoptimized logic)
    bond_vectors = coords[1:] - coords[:-1]
    normals = np.cross(bond_vectors[:-1], bond_vectors[1:])

    n1 = normals[:-1]
    n2 = normals[1:]
    b1 = bond_vectors[:-2]

    n1_norm = np.linalg.norm(n1, axis=1)
    n2_norm = np.linalg.norm(n2, axis=1)

    with np.errstate(divide='ignore', invalid='ignore'):
        cos_phi = np.einsum('ij,ij->i', n1, n2) / (n1_norm * n2_norm)
        cos_phi = np.clip(cos_phi, -1.0, 1.0)
        phi = np.arccos(cos_phi)

        sign_check = np.einsum('ij,ij->i', b1, n2)
        sign = np.sign(sign_check)

    torsion_legacy = phi * sign

    # Pad result to match size of coords
    legacy_result = np.full(len(coords), np.nan)
    legacy_result[1:-2] = torsion_legacy

    # 4. Compare
    # NaNs should be in same places
    np.testing.assert_array_equal(np.isnan(torsion_optimized), np.isnan(legacy_result))

    # Values should be close
    mask = ~np.isnan(torsion_optimized)
    np.testing.assert_allclose(torsion_optimized[mask], legacy_result[mask], rtol=1e-6, atol=1e-6)

if __name__ == "__main__":
    test_torsion_optimization_correctness()

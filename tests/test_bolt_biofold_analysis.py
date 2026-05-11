
import numpy as np
from afcc.metrics import MetricsAnalyzer


def test_compute_curvature_torsion():
    analyzer = MetricsAnalyzer()

    # Test linear chain (curvature 0)
    coords = np.array([
        [0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0], [4, 0, 0],
        [5, 0, 0], [6, 0, 0], [7, 0, 0], [8, 0, 0], [9, 0, 0]
    ])

    curv = analyzer.calculate_curvature(coords)
    # Curvature should be near 0 (ignoring NaN padding)
    valid_curv = curv[~np.isnan(curv)]
    assert np.all(np.abs(valid_curv) < 1e-6)

    # Test bent chain (90 degree turn)
    coords_bent = np.array([
        [0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0],
        [3, 1, 0], [3, 2, 0], [3, 3, 0], [3, 4, 0]
    ])
    curv = analyzer.calculate_curvature(coords_bent)
    # Peak curvature should be significant
    assert np.nanmax(curv) > 0.1

def test_compute_geometry_metrics():
    analyzer = MetricsAnalyzer()
    coords = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [3.0, 0.0, 0.0]
    ])

    # Use calculate_anisotropy directly
    metrics = analyzer.calculate_anisotropy(coords)
    assert metrics['anisotropy_ratio'] > 3.0 # Highly anisotropic
    assert metrics['radius_of_gyration'] > 0.0
    assert 'principal_axis' in metrics

def test_compute_pae_metrics():
    analyzer = MetricsAnalyzer()
    # Mock PAE and pLDDT
    # 2 domains: 0-9 and 10-19 (defined by high pLDDT segments)
    plddts = np.array([90.0]*10 + [90.0]*10) # Continuous high confidence?
    # To force two segments, maybe put a gap?
    # But calculate_pae_metrics logic relies on segments logic inside it?
    # No, it calculates segments from plddt inside.
    # If pLDDT is all high, it's one big segment.
    # Let's put a low conf region in middle
    plddts = np.array([90.0]*10 + [50.0]*5 + [90.0]*10)

    pae = np.zeros((25, 25))
    # Fill intra (low PAE)
    pae[0:10, 0:10] = 5.0
    pae[15:25, 15:25] = 5.0
    # Fill inter (high PAE)
    pae[0:10, 15:25] = 20.0
    pae[15:25, 0:10] = 20.0

    metrics = analyzer.calculate_pae_metrics(pae, plddts)

    # We expect blockiness > 1 (inter > intra)
    assert metrics['predicted_domain_segments'] == 2
    assert metrics['pae_blockiness'] > 1.5

"""Tests for scoliosis metrics and regime classification."""

import numpy as np

from spinalmodes.countercurvature.scoliosis_metrics import (
    RegimeThresholds,
    classify_scoliotic_regime,
    compute_scoliosis_metrics,
)


def _make_curve(offset: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """Utility: build a synthetic z-y curve with optional lateral offset."""
    z = np.linspace(0.0, 1.0, 200)
    y = offset * np.sin(2 * np.pi * z)  # zero gives straight line, >0 gives C-shape
    return z, y


def test_cobb_and_s_lat_for_straight_vs_curved():
    """Straight curve should yield near-zero scoliosis metrics; curved should not."""
    z_straight, y_straight = _make_curve(offset=0.0)
    z_curved, y_curved = _make_curve(offset=0.05)

    metrics_straight = compute_scoliosis_metrics(z_straight, y_straight, frac=0.2)
    metrics_curved = compute_scoliosis_metrics(z_curved, y_curved, frac=0.2)

    assert metrics_straight.S_lat < 1e-3
    assert metrics_straight.cobb_like_deg < 1.0

    assert metrics_curved.S_lat > metrics_straight.S_lat
    assert metrics_curved.cobb_like_deg > metrics_straight.cobb_like_deg


def test_classification_flags_change_with_asymmetry():
    """Classification should flip when asymmetry increases while D_geo_norm is large."""
    # Use lower Cobb threshold since sine waves produce small Cobb angles
    thresholds = RegimeThresholds(
        D_geo_small=0.05, D_geo_large=0.2, S_lat_scoliotic=0.02, cobb_scoliotic_deg=0.5
    )

    # Symmetric baseline metrics: small scoliosis measures
    z_sym, y_sym = _make_curve(offset=0.0)
    metrics_sym = compute_scoliosis_metrics(z_sym, y_sym, frac=0.2)

    # For low D_geo_norm test: use small asymmetry so metrics_asym still has low S_lat
    # This allows gravity_dominated classification to pass
    z_asym_low, y_asym_low = _make_curve(offset=0.01)  # Small offset
    metrics_asym_low = compute_scoliosis_metrics(z_asym_low, y_asym_low, frac=0.2)

    # Low D_geo_norm -> gravity_dominated expected
    flags_low = classify_scoliotic_regime(
        D_geo_norm_sym=0.01,
        metrics_sym=metrics_sym,
        metrics_asym=metrics_asym_low,
        thresholds=thresholds,
    )
    assert flags_low["scoliotic_regime"] is False
    assert flags_low["gravity_dominated"] is True, "Low D_geo_norm should classify as gravity-dominated"

    # For high D_geo_norm test: use larger asymmetry to trigger scoliotic regime
    # Create a piecewise linear curve that produces a measurable Cobb angle
    z_asym_high = np.linspace(0.0, 1.0, 200)
    # Piecewise linear with clear bend produces different slopes at top and bottom
    y_asym_high = np.where(z_asym_high < 0.5, 0.05 * z_asym_high, 0.05 * (1 - z_asym_high))
    metrics_asym_high = compute_scoliosis_metrics(z_asym_high, y_asym_high, frac=0.2)

    # High D_geo_norm with asymmetric metrics -> scoliosis regime expected
    flags_high = classify_scoliotic_regime(
        D_geo_norm_sym=0.25,
        metrics_sym=metrics_sym,
        metrics_asym=metrics_asym_high,
        thresholds=thresholds,
    )
    # Both conditions must be true independently
    assert flags_high["scoliotic_regime"] is True, "High D_geo_norm with asymmetry should classify as scoliotic"
    assert flags_high["gravity_dominated"] is False, "High D_geo_norm should not be gravity-dominated"

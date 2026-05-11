"""Regression tests for countercurvature metrics.

Tests g_eff, D_geo, D_geo_norm, and shape preservation metrics.
"""

import numpy as np
import pytest

from spinalmodes.countercurvature.info_fields import InfoField1D
from spinalmodes.countercurvature.validation_and_metrics import (
    compute_countercurvature_metric,
    compute_shape_preservation_index,
    geodesic_curvature_deviation,
)


def test_g_eff_linear_info_field():
    """Test g_eff with a simple linear I(s).

    For linear I(s), g_eff should be monotone and symmetric when centered.
    """
    length = 1.0
    n_points = 101
    s = np.linspace(0, length, n_points)

    # Linear info field: I(s) = s
    I = s
    dIds = np.ones_like(s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    g_eff = compute_countercurvature_metric(info, beta1=1.0, beta2=0.5)

    # g_eff should be positive everywhere
    assert np.all(g_eff > 0), "g_eff must be positive"

    # For linear I with positive gradient, g_eff should increase
    # (since I_centered increases and dI_norm is constant positive)
    assert g_eff[-1] > g_eff[0], "g_eff should increase for increasing I(s)"

    # Check that g_eff is smooth (no discontinuities)
    diff = np.diff(g_eff)
    assert np.all(np.isfinite(diff)), "g_eff should be finite everywhere"


def test_g_eff_centered_bump():
    """Test g_eff with a centered Gaussian bump.

    For a symmetric bump centered at s=0.5, g_eff should be symmetric.
    """
    length = 1.0
    n_points = 101
    s = np.linspace(0, length, n_points)

    # Gaussian bump centered at s=0.5
    center = 0.5
    width = 0.1
    I = np.exp(-((s - center) ** 2) / (2 * width**2))
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    g_eff = compute_countercurvature_metric(info, beta1=1.0, beta2=0.5)

    # g_eff should peak near center
    peak_idx = np.argmax(g_eff)
    peak_s = s[peak_idx]
    assert abs(peak_s - center) < 0.1, "g_eff peak should be near bump center"

    # For symmetric bump, g_eff should be approximately symmetric
    # (allowing for small numerical differences, but not large asymmetries)
    # Note: If this test fails, it indicates the countercurvature metric computation
    # may have asymmetry issues that need investigation.
    mid = n_points // 2
    left_half = g_eff[:mid]
    right_half = g_eff[mid + 1 :][::-1]  # Reverse to compare, drop center element
    max_diff = np.max(np.abs(left_half - right_half))
    assert max_diff < 0.1, f"g_eff should be symmetric for symmetric input, max diff={max_diff:.6f} > 0.1"


def test_g_eff_beta_parameters():
    """Test that changing beta1/beta2 has expected qualitative effects."""
    length = 1.0
    n_points = 101
    s = np.linspace(0, length, n_points)

    # Info field with both amplitude and gradient
    I = 0.5 + 0.3 * np.sin(2 * np.pi * s)
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # Increase beta1 (amplitude weight)
    g_eff_beta1_high = compute_countercurvature_metric(
        info, beta1=2.0, beta2=0.5
    )
    g_eff_beta1_low = compute_countercurvature_metric(info, beta1=0.5, beta2=0.5)

    # Higher beta1 should give larger variation in g_eff
    var_high = np.var(g_eff_beta1_high)
    var_low = np.var(g_eff_beta1_low)
    assert var_high > var_low, "Higher beta1 should increase g_eff variation"

    # Increase beta2 (gradient weight)
    g_eff_beta2_high = compute_countercurvature_metric(
        info, beta1=1.0, beta2=1.0
    )
    g_eff_beta2_low = compute_countercurvature_metric(info, beta1=1.0, beta2=0.1)

    # Higher beta2 should emphasize regions with large gradients
    # (check that max/min ratio increases)
    ratio_high = np.max(g_eff_beta2_high) / np.min(g_eff_beta2_high)
    ratio_low = np.max(g_eff_beta2_low) / np.min(g_eff_beta2_low)
    assert ratio_high > ratio_low, "Higher beta2 should increase g_eff range"


def test_d_geo_zero_when_identical():
    """Test that D_geo is zero when kappa_passive = kappa_info."""
    length = 1.0
    n_points = 101
    s = np.linspace(0, length, n_points)

    # Same curvature profiles
    kappa = 0.1 * np.sin(2 * np.pi * s)
    kappa_passive = kappa
    kappa_info = kappa

    # Uniform g_eff (no weighting)
    g_eff = np.ones_like(s)

    result = geodesic_curvature_deviation(
        s, kappa_passive, kappa_info, g_eff, eps=1e-9
    )

    assert abs(result["D_geo"]) < 1e-6, (
        f"D_geo should be zero for identical profiles, got {result['D_geo']}"
    )
    assert abs(result["D_geo_sq"]) < 1e-12, "D_geo_sq should be zero"


def test_d_geo_scaled_curvature():
    """Test D_geo with kappa_info = (1+ε) * kappa_passive."""
    length = 1.0
    n_points = 101
    s = np.linspace(0, length, n_points)

    # Base curvature
    kappa_passive = 0.1 * np.sin(2 * np.pi * s)
    epsilon = 0.1
    kappa_info = (1.0 + epsilon) * kappa_passive

    # Uniform g_eff
    g_eff = np.ones_like(s)

    result = geodesic_curvature_deviation(
        s, kappa_passive, kappa_info, g_eff, eps=1e-9
    )

    # D_geo should be proportional to epsilon
    # D_geo^2 = ∫ g_eff * (ε * kappa_passive)^2 ds
    expected_D_geo_sq = epsilon**2 * np.trapezoid(g_eff * kappa_passive**2, s)
    expected_D_geo = np.sqrt(expected_D_geo_sq)

    relative_error = abs(result["D_geo"] - expected_D_geo) / (
        expected_D_geo + 1e-9
    )
    assert relative_error < 0.01, (
        f"D_geo should match expected value for scaled curvature. "
        f"Got {result['D_geo']:.6f}, expected {expected_D_geo:.6f}"
    )


def test_d_geo_norm_behavior():
    """Test that D_geo_norm behaves sensibly."""
    length = 1.0
    n_points = 101
    s = np.linspace(0, length, n_points)

    # Different curvature profiles
    kappa_passive = 0.1 * np.sin(2 * np.pi * s)
    kappa_info = 0.15 * np.sin(2 * np.pi * s)  # 50% larger

    # Uniform g_eff
    g_eff = np.ones_like(s)

    result = geodesic_curvature_deviation(
        s, kappa_passive, kappa_info, g_eff, eps=1e-9
    )

    # D_geo_norm should be dimensionless and positive
    assert result["D_geo_norm"] > 0, "D_geo_norm should be positive"
    assert np.isfinite(result["D_geo_norm"]), "D_geo_norm should be finite"

    # For 50% difference, D_geo_norm should be around 0.5
    # (allowing for integration effects)
    assert 0.3 < result["D_geo_norm"] < 0.7, (
        f"D_geo_norm should be around 0.5 for 50% difference, "
        f"got {result['D_geo_norm']:.3f}"
    )


def test_shape_preservation_straight_rod():
    """Test shape preservation index for a straight rod (trivial case)."""
    length = 1.0
    n_points = 101
    s = np.linspace(0, length, n_points)

    # Straight rod: all points on x-axis
    centerline_initial = np.column_stack([s, np.zeros_like(s)])
    centerline_final = centerline_initial.copy()
    centerline_passive = centerline_initial.copy()

    index = compute_shape_preservation_index(
        centerline_initial, centerline_final, centerline_passive
    )

    # For a straight rod, shape preservation should be high
    # (it maintains its shape perfectly)
    assert index > 0.9, (
        f"Straight rod should have high shape preservation, got {index:.3f}"
    )


def test_shape_preservation_curved_rod():
    """Test shape preservation for a curved rod."""
    length = 1.0
    n_points = 101
    s = np.linspace(0, length, n_points)

    # Curved rod: circular arc
    radius = 0.5
    theta = s / radius
    x = radius * np.sin(theta)
    z = radius * (1.0 - np.cos(theta))
    centerline_final = np.column_stack([x, z])

    # Passive case deviates more (smaller radius -> larger curvature)
    radius_passive = 0.4
    theta_passive = s / radius_passive
    x_passive = radius_passive * np.sin(theta_passive)
    z_passive = radius_passive * (1.0 - np.cos(theta_passive))
    centerline_passive = np.column_stack([x_passive, z_passive])

    # Initial reference: straight
    centerline_initial = np.column_stack([s, np.zeros_like(s)])

    index = compute_shape_preservation_index(
        centerline_initial, centerline_final, centerline_passive
    )

    # Shape preservation should be finite and positive
    assert np.isfinite(index), "Shape preservation index should be finite"
    assert index > 0, "Shape preservation index should be positive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Scoliosis-related asymmetry perturbations and metrics for countercurvature experiments.

This module provides:

- Localized thoracic "bump" functions to break left–right symmetry

- Simple lateral scoliosis indices from Cosserat rod centerline

- A Cobb-like angle in the coronal plane

- A helper to classify "scoliotic regime" in the (χ_κ, g) phase diagram

**Scientific Note**: The scoliosis metrics (S_lat, Cobb-like angle) are defined
for coronal-plane coordinates (z, y) where z is longitudinal and y is lateral.
In 2D sagittal beam models, we use a "pseudo-coronal" projection where the
sagittal x-coordinate is treated as lateral deviation. This is an approximation;
full 3D Cosserat rod models would provide actual coronal-plane coordinates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np

# -------------------------------------------------------------------------
# 1) Asymmetry generators
# -------------------------------------------------------------------------


def normalized_s_coordinate(s: np.ndarray) -> np.ndarray:
    """
    Normalize arc-length coordinate s to s_hat ∈ [0, 1].

    Parameters
    ----------
    s : np.ndarray
        Physical arc-length coordinate.

    Returns
    -------
    s_hat : np.ndarray
        Normalized coordinate in [0, 1].
    """
    if s.ndim != 1:
        raise ValueError("s must be a 1D array.")
    L = float(s[-1] - s[0])
    if L <= 0:
        raise ValueError("s must be strictly increasing.")
    return (s - s[0]) / L


def thoracic_bump(
    s_hat: np.ndarray,
    center_hat: float = 0.6,
    width_hat: float = 0.12,
) -> np.ndarray:
    """
    Localized Gaussian bump in the mid-thoracic region on normalized s_hat ∈ [0, 1].

    center_hat ~ 0.6 corresponds roughly to mid thoracic levels.
    width_hat  controls the spread (fraction of total length).

    Parameters
    ----------
    s_hat : np.ndarray
        Normalized coordinate in [0, 1].
    center_hat : float
        Center of the bump in normalized coordinates.
    width_hat : float
        Approximate full width at half maximum (FWHM) in normalized units.

    Returns
    -------
    bump : np.ndarray
        Dimensionless bump, peak ≈ 1 at center_hat.
    """
    if s_hat.ndim != 1:
        raise ValueError("s_hat must be 1D.")
    # Convert FWHM-like width to sigma: FWHM ≈ 2.355 σ
    sigma = width_hat / 2.355
    return np.exp(-0.5 * ((s_hat - center_hat) / sigma) ** 2)


def apply_info_asymmetry(
    s: np.ndarray,
    I_sym: np.ndarray,
    epsilon_asym: float = 0.05,
    center_hat: float = 0.6,
    width_hat: float = 0.12,
) -> np.ndarray:
    """
    Add a small thoracic asymmetry to an otherwise symmetric information field I(s).

    I_asym(s) = I_sym(s) + ε * ΔI * G(s_hat),

    where ΔI = max(I_sym) - min(I_sym) and G is a Gaussian bump in the thoracic region.

    Parameters
    ----------
    s : np.ndarray
        Arc-length grid (1D).
    I_sym : np.ndarray
        Symmetric information field on s.
    epsilon_asym : float
        Relative perturbation amplitude (e.g. 0.05 = 5%).
    center_hat : float
        Center of thoracic bump in normalized coordinates.
    width_hat : float
        Approximate FWHM of bump in normalized coordinates.

    Returns
    -------
    I_asym : np.ndarray
        Asymmetric information field.
    """
    if not (s.shape == I_sym.shape):
        raise ValueError("s and I_sym must have the same shape.")
    s_hat = normalized_s_coordinate(s)
    G = thoracic_bump(s_hat, center_hat=center_hat, width_hat=width_hat)
    dI = float(np.max(I_sym) - np.min(I_sym))
    return I_sym + epsilon_asym * dI * G


def build_lateral_curvature_bump(
    s: np.ndarray,
    epsilon_lat: float = 0.02,
    center_hat: float = 0.6,
    width_hat: float = 0.12,
) -> np.ndarray:
    """
    Build a small lateral curvature bump κ_lat(s) localized to the thoracic region.

    This is intended to seed a scoliosis-like perturbation in the coronal plane.

    Parameters
    ----------
    s : np.ndarray
        Arc-length grid (1D).
    epsilon_lat : float
        Peak lateral curvature amplitude (1/m). Choose small values (e.g. 0.01–0.05).
    center_hat : float
        Center of thoracic bump in normalized coordinates.
    width_hat : float
        Approximate FWHM of bump in normalized coordinates.

    Returns
    -------
    kappa_lat : np.ndarray
        Lateral curvature bump κ_lat(s).
    """
    s_hat = normalized_s_coordinate(s)
    G = thoracic_bump(s_hat, center_hat=center_hat, width_hat=width_hat)
    return epsilon_lat * G


# -------------------------------------------------------------------------
# 2) Scoliosis metrics in coronal plane
# -------------------------------------------------------------------------


@dataclass
class ScoliosisMetrics:
    """
    Scoliosis-like metrics in the coronal plane for a single configuration.

    Attributes
    ----------
    S_lat : float
        Dimensionless lateral scoliosis index = max |y| / L_eff.
    y_tip : float
        Lateral displacement at the cranial end of the rod.
    lat_dev_max : float
        Maximum absolute lateral displacement along the rod.
    cobb_like_deg : float
        Cobb-like angle (degrees) computed from top and bottom segments.
    """

    S_lat: float
    y_tip: float
    lat_dev_max: float
    cobb_like_deg: float


def compute_lateral_scoliosis_index(
    z: np.ndarray,
    y: np.ndarray,
) -> Tuple[float, float, float]:
    """
    Compute basic lateral scoliosis index based on centerline coordinates.

    Parameters
    ----------
    z : np.ndarray
        Longitudinal coordinate (e.g., cranio-caudal axis) in coronal plane.
    y : np.ndarray
        Lateral coordinate (left–right) in coronal plane.

    Returns
    -------
    S_lat : float
        Dimensionless lateral scoliosis index = max |y| / L_eff,
        where L_eff is the effective longitudinal span in z.
    y_tip : float
        Lateral displacement at the cranial (last) point.
    lat_dev_max : float
        Maximum absolute lateral displacement along the rod.
    """
    if not (z.shape == y.shape):
        raise ValueError("z and y must have the same shape.")
    y_tip = float(y[-1])
    lat_dev_max = float(np.max(np.abs(y)))
    L_eff = float(np.max(z) - np.min(z))
    if L_eff <= 0:
        raise ValueError("z must span a positive length for S_lat.")
    S_lat = lat_dev_max / L_eff
    return S_lat, y_tip, lat_dev_max


def cobb_like_angle(
    z: np.ndarray,
    y: np.ndarray,
    frac: float = 0.2,
) -> float:
    """
    Approximate a Cobb-like angle in the coronal plane.

    Fits straight lines to the top and bottom 'frac' fractions of the rod
    in (z, y) and returns the angle between them.

    Parameters
    ----------
    z : np.ndarray
        Longitudinal coordinate.
    y : np.ndarray
        Lateral coordinate.
    frac : float
        Fraction of points at the top and bottom to use for line fits (0 < frac < 0.5).

    Returns
    -------
    angle_deg : float
        Cobb-like angle between top and bottom segments, in degrees.
        Returns 0.0 if linear fit fails (e.g., insufficient data or collinear points).
    """
    if not (z.shape == y.shape):
        raise ValueError("z and y must have the same shape.")
    if not (0.0 < frac < 0.5):
        raise ValueError("frac must be in (0, 0.5).")
    N = len(z)
    k = max(3, int(frac * N))

    try:
        # Bottom segment
        z_bottom = z[:k]
        y_bottom = y[:k]
        m_bottom, _ = np.polyfit(z_bottom, y_bottom, deg=1)

        # Top segment
        z_top = z[-k:]
        y_top = y[-k:]
        m_top, _ = np.polyfit(z_top, y_top, deg=1)

        theta_bottom = np.arctan(m_bottom)
        theta_top = np.arctan(m_top)
        cobb_rad = np.abs(theta_top - theta_bottom)
        return float(np.degrees(cobb_rad))
    except np.linalg.LinAlgError:
        # Fit failed (e.g., collinear points, numerical instability)
        return 0.0


def compute_scoliosis_metrics(
    z: np.ndarray,
    y: np.ndarray,
    frac: float = 0.2,
) -> ScoliosisMetrics:
    """
    Compute a bundle of scoliosis-like metrics in the coronal plane.

    Parameters
    ----------
    z : np.ndarray
        Longitudinal coordinate.
    y : np.ndarray
        Lateral coordinate.
    frac : float
        Fraction of points used for Cobb-like angle.

    Returns
    -------
    metrics : ScoliosisMetrics
        Named bundle of lateral index and Cobb-like angle.
    """
    S_lat, y_tip, lat_dev_max = compute_lateral_scoliosis_index(z, y)
    cobb_deg = cobb_like_angle(z, y, frac=frac)
    return ScoliosisMetrics(
        S_lat=S_lat,
        y_tip=y_tip,
        lat_dev_max=lat_dev_max,
        cobb_like_deg=cobb_deg,
    )


# -------------------------------------------------------------------------
# 3) Regime classification for phase diagrams
# -------------------------------------------------------------------------


@dataclass
class RegimeThresholds:
    """
    Thresholds used to classify regimes in (χ_κ, g) space.

    Attributes
    ----------
    D_geo_small : float
        Threshold below which geodesic deviation is considered "small".
    D_geo_large : float
        Threshold above which geodesic deviation is considered "large".
    S_lat_scoliotic : float
        Minimum S_lat indicating significant lateral deviation.
    cobb_scoliotic_deg : float
        Minimum Cobb-like angle increase considered scoliosis-like.
    """

    D_geo_small: float = 0.1
    D_geo_large: float = 0.3
    S_lat_scoliotic: float = 0.05
    cobb_scoliotic_deg: float = 5.0


def classify_scoliotic_regime(
    D_geo_norm_sym: float,
    metrics_sym: ScoliosisMetrics,
    metrics_asym: ScoliosisMetrics,
    thresholds: RegimeThresholds | None = None,
) -> Dict[str, bool]:
    """
    Classify gravity-dominated, cooperative, and scoliosis-like regimes.

    Parameters
    ----------
    D_geo_norm_sym : float
        Normalized geodesic curvature deviation for the symmetric configuration.
    metrics_sym : ScoliosisMetrics
        Scoliosis metrics for the symmetric (ε_asym = 0) configuration.
    metrics_asym : ScoliosisMetrics
        Scoliosis metrics for the asymmetric (ε_asym > 0) configuration.
    thresholds : RegimeThresholds, optional
        Thresholds for classification.

    Returns
    -------
    flags : dict
        {
            "gravity_dominated": bool,
            "cooperative": bool,
            "scoliotic_regime": bool,
        }
    """
    if thresholds is None:
        thresholds = RegimeThresholds()

    # Differences between asymmetric and symmetric runs
    delta_S_lat = metrics_asym.S_lat - metrics_sym.S_lat
    delta_cobb = metrics_asym.cobb_like_deg - metrics_sym.cobb_like_deg

    gravity_dominated = (
        D_geo_norm_sym < thresholds.D_geo_small
        and metrics_asym.S_lat < thresholds.S_lat_scoliotic
        and delta_cobb < thresholds.cobb_scoliotic_deg
    )

    scoliotic_regime = (
        D_geo_norm_sym > thresholds.D_geo_large
        and metrics_asym.S_lat >= thresholds.S_lat_scoliotic
        and delta_cobb >= thresholds.cobb_scoliotic_deg
    )

    cooperative = not gravity_dominated and not scoliotic_regime

    return {
        "gravity_dominated": gravity_dominated,
        "cooperative": cooperative,
        "scoliotic_regime": scoliotic_regime,
    }


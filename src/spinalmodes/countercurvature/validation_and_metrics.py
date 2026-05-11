"""Validation utilities for countercurvature analog models.

This module provides metrics that quantify how information-driven countercurvature
deviates from passive gravitational equilibria. These metrics interpret the
information-driven corrections as effective "metric deviations" in the analog
spacetime model.

The key metrics are:
- Countercurvature energy: Integrated deviation between passive and info-driven shapes
- Effective metric deviation: L2 norm of curvature corrections
- Shape preservation index: How well information maintains structure against gravity
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import numpy as np
from numpy.typing import NDArray

from .info_fields import InfoField1D

if TYPE_CHECKING:
    from .pyelastica_bridge import SimulationResult

ArrayF64 = NDArray[np.float64]


def compute_countercurvature_metric(
    info: InfoField1D,
    beta1: float = 1.0,
    beta2: float = 0.5,
    eps: float = 1e-9,
) -> ArrayF64:
    """Compute the 1D "biological countercurvature" metric g_eff(s) along the rod."""
    s = info.s
    I = info.I
    dIds = info.dIds

    if I.ndim != 1 or dIds.ndim != 1 or s.ndim != 1:
        raise ValueError("InfoField1D arrays must be 1D.")

    if not (I.shape == dIds.shape == s.shape):
        raise ValueError("InfoField1D arrays must have the same shape.")

    # Normalize I to ~[0, 1]
    I_min = float(np.min(I))
    I_max = float(np.max(I))
    I_norm = (I - I_min) / (I_max - I_min + eps)

    # Centered, so "excess" information is relative to mean
    I_centered = I_norm - float(np.mean(I_norm))

    # Normalize gradient magnitude to ~[0, 1]
    #
    # Important for interpretability/testing:
    # For symmetric information bumps I(s), the metric factor g_eff(s) should be
    # symmetric as well. Using the *signed* gradient would introduce an
    # antisymmetric contribution to φ(s), making exp(2φ) asymmetric. We therefore
    # use |∂I/∂s| as the default "gradient strength" term.
    max_grad = float(np.max(np.abs(dIds))) + eps
    dI_norm = np.abs(dIds) / max_grad

    # Build φ(s) (dimensionless)
    phi = beta1 * I_centered + beta2 * dI_norm

    # Conformal metric factor: strictly positive
    g_eff = np.exp(2.0 * phi)
    return g_eff


def geodesic_curvature_deviation(
    s: ArrayF64,
    kappa_passive: ArrayF64,
    kappa_info: ArrayF64,
    g_eff: ArrayF64,
    eps: float = 1e-9,
) -> dict[str, float]:
    """Geodesic curvature deviation between passive and information-driven profiles."""
    if not (s.shape == kappa_passive.shape == kappa_info.shape == g_eff.shape):
        raise ValueError("All input arrays must have the same shape.")

    # Difference in curvature
    dkappa = kappa_info - kappa_passive

    # Weighted L2 distance in the countercurvature metric
    integrand = g_eff * dkappa**2
    D_geo_sq = float(np.trapezoid(integrand, s))
    D_geo = float(np.sqrt(max(D_geo_sq, 0.0)))

    # Baseline: passive curvature "energy" in g_eff
    base_integrand = g_eff * kappa_passive**2
    base_energy = float(np.trapezoid(base_integrand, s))

    # Normalized distance (dimensionless)
    D_geo_norm = D_geo / (np.sqrt(base_energy) + eps)

    return {
        "D_geo": D_geo,
        "D_geo_sq": D_geo_sq,
        "D_geo_norm": D_geo_norm,
        "base_energy": base_energy,
    }

def compute_comprehensive_metrics(
    result: "SimulationResult",
    passive_result: Optional["SimulationResult"] = None,
    g_eff: Optional[ArrayF64] = None,
) -> dict[str, float]:
    """Compute all quantitative metrics for a simulation result."""
    from .scoliosis_metrics import cobb_like_angle, compute_lateral_scoliosis_index

    # Extract final state
    centerline = result.centerline[-1]
    curvature = result.curvature[-1]
    s = result.info_field.s

    # 1. Curvature summary stats
    metrics = {
        "mean_curvature": float(np.mean(curvature)),
        "max_curvature": float(np.max(curvature)),
        "std_curvature": float(np.std(curvature)),
    }

    # 2. Tip deflection and inflection count
    tip_deflection = float(np.linalg.norm(centerline[-1] - centerline[0]))
    metrics["tip_deflection"] = tip_deflection

    # Inflection count
    dkappa = np.diff(curvature)
    inflections = np.sum(np.diff(np.sign(dkappa)) != 0)
    metrics["inflection_count"] = float(inflections)

    # 3. Geodesic deviation if passive result provided
    if passive_result is not None:
        kappa_passive = passive_result.curvature[-1]
        if g_eff is None:
            g_eff = np.ones_like(s)

        geo_dev = geodesic_curvature_deviation(s, kappa_passive, curvature, g_eff)
        metrics["D_geo_hat"] = geo_dev["D_geo_norm"]
        metrics["D_geo"] = geo_dev["D_geo"]

    # 4. Mode-selection score
    s_norm = s / s[-1]
    target_s = np.sin(2 * np.pi * s_norm) # Ideal S-shape
    target_c = np.ones_like(s) # Ideal C-shape

    score_s = np.corrcoef(curvature, target_s)[0, 1]
    score_c = np.corrcoef(curvature, target_c)[0, 1]
    metrics["mode_score_s"] = float(score_s)
    metrics["mode_score_c"] = float(score_c)

    # 5. Lateral metrics
    z = centerline[:, 2]
    y = centerline[:, 1]
    S_lat, y_tip, lat_dev_max = compute_lateral_scoliosis_index(z, y)
    metrics["S_lat"] = S_lat
    metrics["y_tip"] = y_tip
    metrics["cobb_angle"] = cobb_like_angle(z, y)

    return metrics


def compute_countercurvature_energy(
    centerline_passive: ArrayF64,
    centerline_info: ArrayF64,
    *,
    method: str = "l2_distance",
) -> float:
    """Compute the energy-like metric quantifying countercurvature deviation."""
    if centerline_passive.shape != centerline_info.shape:
        raise ValueError("Centerline shapes must match")
    if method == "l2_distance":
        diff = centerline_info - centerline_passive
        squared_distances = np.sum(diff**2, axis=-1)
        return float(np.trapezoid(squared_distances))
    return 0.0

def compute_effective_metric_deviation(
    kappa_passive: ArrayF64,
    kappa_info: ArrayF64,
    *,
    s: Optional[ArrayF64] = None,
) -> float:
    """Compute the L2 norm of curvature deviation as a metric deviation."""
    delta_kappa = kappa_info - kappa_passive
    if s is not None:
        return float(np.sqrt(np.trapezoid(delta_kappa**2, x=s)))
    return float(np.linalg.norm(delta_kappa) / np.sqrt(len(delta_kappa)))

def compute_shape_preservation_index(
    centerline_initial: ArrayF64,
    centerline_final: ArrayF64,
    centerline_passive: ArrayF64,
) -> float:
    """Compute how well information preserves shape against gravitational sag.

    Returns a dimensionless score in [0, 1] where:
    - 1 means "perfect preservation" (no additional deviation vs. the initial shape)
    - 0 means "no improvement over passive" (info-driven deviation matches passive)
    - values < 0 (info worse than passive) are clipped to 0
    """
    eps = 1e-12
    dev_info = float(np.mean(np.linalg.norm(centerline_final - centerline_initial, axis=-1)))
    dev_passive = float(np.mean(np.linalg.norm(centerline_passive - centerline_initial, axis=-1)))

    # Trivial identical-shape case: both deviations ~0 → perfect preservation.
    if dev_passive <= eps and dev_info <= eps:
        return 1.0

    # Normalized improvement relative to passive sag.
    score = 1.0 - (dev_info / (dev_passive + eps))
    return float(np.clip(score, 0.0, 1.0))

def compare_with_beam_solver(
    centerline_pyelastica: ArrayF64,
    theta_beam: ArrayF64,
    s: ArrayF64,
    *,
    tolerance: float = 0.01,
) -> dict[str, float | bool]:
    """Compare PyElastica results with existing beam/BVP solver."""
    return {"agrees": True} # Placeholder for now

__all__ = [
    "compute_countercurvature_metric",
    "geodesic_curvature_deviation",
    "compute_countercurvature_energy",
    "compute_effective_metric_deviation",
    "compute_shape_preservation_index",
    "compare_with_beam_solver",
    "compute_comprehensive_metrics",
]

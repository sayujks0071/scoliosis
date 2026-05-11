"""Common utilities and canonical configurations for countercurvature experiments.

This module provides shared builders for information fields, baseline curvature
profiles, and default parameter ranges to reduce duplication across experiments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from spinalmodes.countercurvature import (
    CounterCurvatureParams,
    InfoField1D,
)

ArrayF64 = NDArray[np.float64]


@dataclass
class ExperimentConfig:
    """Default configuration for countercurvature experiments."""

    # Geometry
    length: float = 0.4  # meters
    n_nodes: int = 100

    # Material properties
    E0: float = 1e9  # Pa
    rho: float = 1000.0  # kg/m³
    radius: float = 0.01  # m
    I_moment: float = 1e-8  # m^4

    # Coupling parameters
    chi_kappa_range: tuple[float, float] = (0.0, 0.08)
    chi_kappa_n_points: int = 17
    chi_E: float = 0.1
    chi_M: float = 0.0

    # Gravity
    gravity_values: ArrayF64 = None  # Will be set to default if None
    gravity_default: float = 9.81  # m/s²

    # Asymmetry
    epsilon_asym_range: tuple[float, float] = (0.0, 0.05)
    epsilon_asym_n_points: int = 11

    def __post_init__(self):
        """Set default gravity values if not provided."""
        if self.gravity_values is None:
            self.gravity_values = np.array(
                [9.81, 4.9, 2.0, 1.0, 0.5, 0.2, 0.1, 0.05, 0.01]
            )

    def get_chi_kappa_values(self) -> ArrayF64:
        """Get array of chi_kappa values to sweep."""
        return np.linspace(
            self.chi_kappa_range[0],
            self.chi_kappa_range[1],
            self.chi_kappa_n_points,
        )

    def get_epsilon_asym_values(self) -> ArrayF64:
        """Get array of epsilon_asym values to sweep."""
        return np.linspace(
            self.epsilon_asym_range[0],
            self.epsilon_asym_range[1],
            self.epsilon_asym_n_points,
        )


def create_spinal_info_field(
    s: ArrayF64, length: float, epsilon_asym: float = 0.0
) -> InfoField1D:
    """Create canonical spinal information field.

    Represents neural/postural control with peaks in lumbar and cervical regions.
    Optionally adds a mid-thoracic asymmetry bump for scoliosis modeling.

    Parameters
    ----------
    s:
        Arc-length coordinates (m).
    length:
        Total rod length (m).
    epsilon_asym:
        Asymmetry perturbation amplitude (dimensionless, typically 0.0-0.05).

    Returns
    -------
    InfoField1D
        Information field with I(s) and dIds.
    """
    s_norm = s / length
    lumbar = 0.7 * np.exp(-((s_norm - 0.25) ** 2) / (2 * 0.1**2))
    cervical = 0.5 * np.exp(-((s_norm - 0.8) ** 2) / (2 * 0.08**2))
    I = lumbar + cervical + 0.3

    # Add asymmetric perturbation (mid-thoracic, T7-T9 region)
    if epsilon_asym > 0:
        asymmetry_bump = epsilon_asym * np.exp(
            -((s_norm - 0.6) ** 2) / (2 * 0.08**2)
        )
        I = I + asymmetry_bump

    return InfoField1D.from_array(s, I)


def create_spine_kappa_gen(s: ArrayF64, length: float) -> ArrayF64:
    """Create canonical baseline spinal curvature profile (sagittal, symmetric).

    Parameters
    ----------
    s:
        Arc-length coordinates (m).
    length:
        Total rod length (m).

    Returns
    -------
    kappa_gen:
        Baseline geometric curvature κ_gen(s) in 1/m.
    """
    s_norm = s / length
    lumbar = 0.3 * np.exp(-((s_norm - 0.2) ** 2) / (2 * 0.1**2))
    thoracic = -0.2 * np.exp(-((s_norm - 0.6) ** 2) / (2 * 0.15**2))
    return lumbar + thoracic


def create_upward_growth_info_field(s: ArrayF64, length: float) -> InfoField1D:
    """Create information field that promotes upward growth (plant-like).

    Parameters
    ----------
    s:
        Arc-length coordinates (m).
    length:
        Total rod length (m).

    Returns
    -------
    InfoField1D
        Information field that creates upward-bending countercurvature.
    """
    s_norm = s / length
    # Information peaks at base (promotes upward curvature)
    I = 0.8 * np.exp(-((s_norm - 0.1) ** 2) / (2 * 0.15**2)) + 0.2
    return InfoField1D.from_array(s, I)


def build_countercurvature_system(
    config: ExperimentConfig,
    info_field: InfoField1D,
    chi_kappa: float,
    kappa_gen: Optional[ArrayF64] = None,
) -> tuple[CounterCurvatureParams, ArrayF64]:
    """Build countercurvature parameters and baseline curvature.

    Helper function to construct CounterCurvatureParams and kappa_gen
    from a config and info field.

    Parameters
    ----------
    config:
        Experiment configuration.
    info_field:
        Information field I(s).
    chi_kappa:
        Information-to-curvature coupling strength.
    kappa_gen:
        Optional baseline curvature. If None, uses canonical spinal profile.

    Returns
    -------
    params:
        CounterCurvatureParams with specified coupling strengths.
    kappa_gen:
        Baseline curvature profile.
    """
    if kappa_gen is None:
        kappa_gen = create_spine_kappa_gen(info_field.s, config.length)

    params = CounterCurvatureParams(
        chi_kappa=chi_kappa,
        chi_E=config.chi_E,
        chi_M=config.chi_M,
        scale_length=config.length,
    )

    return params, kappa_gen


__all__ = [
    "ExperimentConfig",
    "create_spinal_info_field",
    "create_spine_kappa_gen",
    "create_upward_growth_info_field",
    "build_countercurvature_system",
]


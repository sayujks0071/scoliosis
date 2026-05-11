"""Coupling rules converting information fields into mechanical countercurvature.

This module expresses the central hypothesis of the project in concrete numerical terms:
information processing along a biological rod imprints effective *countercurvature* onto
its mechanical state.  The functions provided here map gradients of information density
into rest curvature, stiffness and active moments that augment or oppose gravity-driven
bending when fed to a Cosserat rod solver (e.g. PyElastica).
"""

from __future__ import annotations

from typing import NamedTuple, Union

import numpy as np
from numpy.typing import NDArray

from .info_fields import InfoField1D

ArrayF64 = NDArray[np.float64]


class CounterCurvatureParams(NamedTuple):
    """Dimensioned parameters governing information–mechanics coupling.

    Attributes
    ----------
    chi_kappa:
        Coupling gain transforming information gradients (``∂I/∂s``) into corrections of
        the rod's rest curvature (units: 1/m per unit information gradient).
        Can be a scalar or an array matching the information grid size.
    chi_E:
        Coupling gain for stiffness modulation by the information density (dimensionless
        multiplier on the baseline Young's modulus).
        Can be a scalar or an array matching the information grid size.
    chi_M:
        Coupling gain converting information gradients into active internal moments
        (units: N·m per unit gradient).  This represents the "effort" expended by the
        living system to steer curvature against gravity.
        Can be a scalar or an array matching the information grid size.
    chi_tau:
        Coupling gain transforming information gradients (``∂I/∂s``) into rest torsion
        (units: 1/m per unit information gradient). This models the "twist" induced by
        anisotropic tissue organisation (e.g. PCP defects).
        Can be a scalar or an array matching the information grid size.
    scale_length:
        Optional length scale used when non-dimensionalising information gradients.  Set
        to ``1.0`` to operate directly in SI units.
    """

    chi_kappa: Union[float, ArrayF64] = 0.0
    chi_E: Union[float, ArrayF64] = 0.0
    chi_M: Union[float, ArrayF64] = 0.0
    chi_tau: Union[float, ArrayF64] = 0.0
    scale_length: float = 1.0

    def nondimensional_gradient(self, dIds: ArrayF64) -> ArrayF64:
        """Return a gradient scaled by ``scale_length`` if provided."""

        if self.scale_length <= 0.0:
            raise ValueError("scale_length must be positive.")
        return dIds * float(self.scale_length)


def _validate_shapes(info: InfoField1D, *arrays: ArrayF64) -> None:
    for array in arrays:
        # Allow broadcasting if array has compatible shape
        if array.ndim == 1 and array.shape != info.s.shape:
             raise ValueError(
                "1D arrays must share the same shape as the information grid."
            )
        elif array.ndim > 1 and array.shape[-1] != info.s.shape[0]:
             raise ValueError(
                "Multi-dimensional arrays must match the information grid in the last dimension."
            )


def compute_rest_curvature(
    info: InfoField1D, params: CounterCurvatureParams, kappa_gen: Union[float, ArrayF64]
) -> ArrayF64:
    """Compute information-biased rest curvature vector ``κ_rest``.

    Parameters
    ----------
    info:
        Information field describing ``I(s)`` and ``∂I/∂s`` along the rod.
    params:
        Coupling parameters mapping information gradients to curvature corrections.
    kappa_gen:
        Baseline geometric curvature (e.g. from evolutionary morphology).
        Can be a scalar (constant curvature), a 1D array (planar curvature profile),
        or a (3, N) array (full 3D curvature profile).

    Returns
    -------
    numpy.ndarray
        The rest curvature profile ``κ_rest(s)`` of shape ``(3, n_points)``.
        Index 0: Binormal curvature (bending)
        Index 1: Normal curvature (bending, main plane)
        Index 2: Tangent curvature (torsion)

    Notes
    -----
    ``κ_rest`` incorporates both planar curvature coupling (``χ_κ``) and torsional coupling
    (``χ_τ``). The gradient term ``∂I/∂s`` drives these corrections:
    - ``κ_rest[1] += χ_κ * scale_length * ∂I/∂s``
    - ``κ_rest[2] += χ_τ * scale_length * ∂I/∂s``
    """

    n_points = info.s.shape[0]

    # Normalise kappa_gen to (3, n_points)
    k_gen_arr = np.zeros((3, n_points))

    kappa_gen = np.asarray(kappa_gen, dtype=float)
    if kappa_gen.ndim == 0:
        # Scalar: assume constant planar curvature in y-direction (index 1)
        k_gen_arr[1, :] = kappa_gen
    elif kappa_gen.ndim == 1:
        _validate_shapes(info, kappa_gen)
        # 1D array: assume planar curvature in y-direction
        k_gen_arr[1, :] = kappa_gen
    elif kappa_gen.ndim == 2:
        if kappa_gen.shape != (3, n_points):
             raise ValueError(f"kappa_gen shape {kappa_gen.shape} mismatch with (3, {n_points})")
        k_gen_arr = kappa_gen
    else:
        raise ValueError("kappa_gen must be scalar, 1D array, or (3, N) array.")

    grad = params.nondimensional_gradient(info.dIds)

    # Apply couplings
    # chi_kappa couples to index 1 (planar bending)
    k_gen_arr[1, :] += params.chi_kappa * grad

    # chi_tau couples to index 2 (torsion)
    k_gen_arr[2, :] += params.chi_tau * grad

    return k_gen_arr


def compute_effective_stiffness(
    info: InfoField1D, params: CounterCurvatureParams, E0: float, *, model: str = "linear"
) -> ArrayF64:
    """Compute the information-modulated stiffness field ``E_eff``.

    Parameters
    ----------
    info:
        Information field describing ``I(s)`` along the rod.
    params:
        Coupling parameters; only ``chi_E`` is used here.
    E0:
        Baseline Young's modulus of the rod (Pa).
    model:
        Functional form of the coupling.  ``"linear"`` implements ``E_eff = E0 * (1 + chi_E * I)``
        while ``"exponential"`` uses ``E_eff = E0 * exp(chi_E * I)``.

    Returns
    -------
    numpy.ndarray
        Spatially varying effective stiffness.

    Raises
    ------
    ValueError
        If an unsupported model is requested or shapes are inconsistent.
    """

    if E0 <= 0.0:
        raise ValueError("Baseline stiffness E0 must be positive.")
    I = np.asarray(info.I, dtype=float)

    if model == "linear":
        return E0 * (1.0 + params.chi_E * I)
    if model == "exponential":
        return E0 * np.exp(params.chi_E * I)
    raise ValueError(f"Unsupported stiffness coupling model: {model}")


def compute_active_moments(info: InfoField1D, params: CounterCurvatureParams) -> ArrayF64:
    """Return an information-driven active moment field ``M_info``.

    The active moment encodes the biological ``effort`` or internal actuation required to
    maintain countercurvature against gravity.  In our analog model it is a direct,
    gradient-driven term ``M_info = χ_M * scale_length * ∂I/∂s``.
    """

    grad = params.nondimensional_gradient(info.dIds)
    return params.chi_M * grad

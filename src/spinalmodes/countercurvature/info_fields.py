"""Information field data structures for countercurvature analog models.

The objects defined here describe scalar information densities distributed along the
arc-length of a Cosserat rod.  Within the biological countercurvature hypothesis these
fields encode the structured information processing (growth programmes, neural control,
feedback) that modulates the mechanical curvature landscape experienced by the rod.

They serve as inputs to the coupling rules in :mod:`spinalmodes.countercurvature.coupling`
which translate information gradients into rest curvature, stiffness and active moment
corrections—i.e. the effective ``countercurvature`` corrections to gravity-driven
mechanics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, NamedTuple, Sequence

import numpy as np
from numpy.typing import NDArray

ArrayF64 = NDArray[np.float64]


def _validate_monotonic_grid(s: ArrayF64) -> None:
    if s.ndim != 1:
        raise ValueError("Arc-length grid 's' must be one-dimensional.")
    if np.any(np.diff(s) <= 0.0):
        raise ValueError("Arc-length grid 's' must be strictly increasing.")


def make_uniform_grid(length: float, n_points: int) -> ArrayF64:
    """Create a uniformly spaced arc-length grid.

    Parameters
    ----------
    length:
        Physical length of the rod segment (metres).
    n_points:
        Number of sample points along the rod.

    Returns
    -------
    numpy.ndarray
        Array of shape ``(n_points,)`` spanning ``[0, length]``.
    """

    if n_points < 2:
        raise ValueError("At least two points are required to define a grid.")
    return np.linspace(0.0, float(length), int(n_points), dtype=float)


class InfoField1D(NamedTuple):
    """Static information field distributed along a rod.

    Parameters
    ----------
    s:
        One-dimensional arc-length grid (metres).
    I:
        Dimensionless information density evaluated on ``s``.
    dIds:
        Spatial derivative :math:`\\partial I/\\partial s` with the same shape as ``s``.

    Notes
    -----
    The tuple captures the minimum ingredients required to bias mechanical curvature in
    the Information–Elasticity Coupling (IEC) framework.  It is intentionally lightweight
    so it can be fed directly into NumPy-accelerated coupling functions.  The derivative
    is stored explicitly to make the ``χ_κ`` (countercurvature) coupling cheap and to keep
    the mechanical interpretation transparent: gradients of information create rest
    curvature corrections that oppose or steer gravity-driven bending.
    """

    s: ArrayF64
    I: ArrayF64
    dIds: ArrayF64

    """
    1D Information field I(s).

    Attributes
    ----------
    s : np.ndarray
        Spatial coordinate (arc length).
    I : np.ndarray
        Information content I(s) with the same shape as ``s``.
    dIds : np.ndarray
        Spatial derivative :math:`\\partial I/\\partial s` with the same shape as ``s``.
    """

    def as_dict(self) -> dict[str, ArrayF64]:
        """Return the field as a dictionary of arrays."""

        return {"s": self.s, "I": self.I, "dIds": self.dIds}

    @property
    def n_points(self) -> int:
        """Number of spatial sample points."""

        return int(self.s.size)

    @classmethod
    def from_callable(
        cls,
        s: ArrayF64,
        info_function: Callable[[ArrayF64], ArrayF64],
        *,
        derivative_function: Callable[[ArrayF64], ArrayF64] | None = None,
    ) -> "InfoField1D":
        """Build an information field by sampling a callable.

        Parameters
        ----------
        s:
            Arc-length grid (metres); must be strictly increasing.
        info_function:
            Callable returning ``I(s)`` when evaluated on the grid.
        derivative_function:
            Optional callable for ``∂I/∂s``.  If omitted, the derivative is computed using
            :func:`numpy.gradient` with respect to ``s``.

        Returns
        -------
        InfoField1D
            Populated information field ready for countercurvature coupling.
        """

        _validate_monotonic_grid(s)
        I = np.asarray(info_function(s), dtype=float)
        if I.shape != s.shape:
            raise ValueError("info_function must return an array with the same shape as 's'.")

        if derivative_function is None:
            dIds = np.gradient(I, s, edge_order=2)
        else:
            dIds = np.asarray(derivative_function(s), dtype=float)
            if dIds.shape != s.shape:
                raise ValueError(
                    "derivative_function must return an array with the same shape as 's'."
                )

        return cls(s=s, I=I, dIds=dIds)

    @classmethod
    def from_array(cls, s: ArrayF64, I: ArrayF64) -> "InfoField1D":
        """Construct an information field from explicit arrays.

        The derivative :math:`∂I/∂s` is computed using central differences.  Use this when
        experimental or precomputed information densities are supplied directly from the
        IEC model.
        """

        _validate_monotonic_grid(s)
        I_array = np.asarray(I, dtype=float)
        if I_array.shape != s.shape:
            raise ValueError("Input array 'I' must have the same shape as 's'.")
        dIds = np.gradient(I_array, s, edge_order=2)
        return cls(s=s, I=I_array, dIds=dIds)


@dataclass(frozen=True)
class InfoFieldTimeSeries:
    """Time-resolved information field sequence.

    This container allows experiments to prescribe dynamic countercurvature programmes
    ``I(s, t)`` where each time slice is represented by an :class:`InfoField1D`.  The class
    primarily stores metadata and provides lightweight interpolation hooks for future
    extensions.  For the initial implementation we support simple nearest-neighbour access
    through :meth:`get_field_at`.
    """

    times: ArrayF64
    fields: Sequence[InfoField1D]

    def __post_init__(self) -> None:
        object.__setattr__(self, "times", np.asarray(self.times, dtype=float))
        object.__setattr__(self, "fields", tuple(self.fields))

        if len(self.fields) != int(self.times.size):
            raise ValueError("Number of fields must match number of time stamps.")
        if any(field.n_points != self.fields[0].n_points for field in self.fields):
            raise ValueError("All InfoField1D objects must share the same spatial discretisation.")

    def get_field_at(self, time: float) -> InfoField1D:
        """Return the information field closest to ``time``.

        The method implements a minimal temporal interface sufficient for quasi-static
        countercurvature experiments where information updates occur on a slower timescale
        than mechanical relaxation.  More advanced interpolation can be added once the
        PyElastica bridge requires it.
        """

        idx = int(np.clip(np.searchsorted(self.times, time), 0, self.times.size - 1))
        return self.fields[idx]

    @property
    def n_times(self) -> int:
        """Number of time samples."""

        return int(self.times.size)

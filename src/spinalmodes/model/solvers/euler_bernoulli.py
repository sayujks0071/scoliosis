"""Lightweight Euler–Bernoulli beam utilities for validation and IEC demos."""

from __future__ import annotations

import numpy as np


def integrate_shape_from_curvature(s: np.ndarray, kappa: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Integrate curvature to angle and centerline in the small-slopes regime.

    For small slopes, curvature is approximated by the second derivative of the
    transverse deflection:

        y''(s) = κ(s)

    We integrate twice using a trapezoidal rule, and choose integration constants
    such that:

        y(0) = 0,  y(L) = 0

    (Dirichlet endpoints). This avoids spurious linear drift that would otherwise
    dominate amplitude/wavelength metrics when κ is oscillatory.
    """
    if s.ndim != 1 or kappa.ndim != 1 or s.shape != kappa.shape:
        raise ValueError("s and kappa must be 1D arrays with the same shape.")
    if s.size < 2:
        return np.asarray(s, dtype=float), np.zeros_like(s, dtype=float)

    x = (s - s[0]).astype(float)
    ds = np.diff(s).astype(float)

    # θ(s) = ∫ κ ds, with θ(0)=0
    theta = np.zeros_like(s, dtype=float)
    theta[1:] = np.cumsum(0.5 * (kappa[:-1] + kappa[1:]) * ds)

    # y0(s) = ∫ θ ds, with y0(0)=0 and y0'(0)=0
    y = np.zeros_like(s, dtype=float)
    y[1:] = np.cumsum(0.5 * (theta[:-1] + theta[1:]) * ds)

    # Enforce y(L)=0 by removing a linear trend: y <- y + C1*s, C1 = -y(L)/L
    L = float(x[-1]) if float(x[-1]) != 0.0 else 1.0
    c1 = -float(y[-1]) / L
    y = y + c1 * x
    return x, y


def analytic_sinusoid(s: np.ndarray, A: float, k: float) -> np.ndarray:
    """Analytic small-slope solution y(s) = A sin(ks)."""
    return A * np.sin(k * s)


def l2_error(a: np.ndarray, b: np.ndarray) -> float:
    """L2 error between two arrays."""
    return float(np.sqrt(np.mean((a - b) ** 2)))


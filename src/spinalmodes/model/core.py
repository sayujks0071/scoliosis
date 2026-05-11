"""Core dataclasses and helpers for the Information–Elasticity Coupling model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class Params:
    L: float = 1.0  # beam length (m)
    n: int = 801  # grid points
    chi_k: float = 0.0  # IEC-1: phase drift via dI/ds
    chi_E: float = 0.0  # IEC-2: amplitude/material scaling (applied in solver)
    g: float = 0.0  # gravitational load proxy
    seed: int = 1337


@dataclass(slots=True)
class State:
    s: np.ndarray  # arc-length grid [0..L]
    kappa0: np.ndarray  # baseline curvature κ0(s)
    I: np.ndarray | None = None  # information field I(s)
    E: np.ndarray | None = None  # local stiffness (optional)


def uniform_grid(L: float, n: int) -> np.ndarray:
    """Uniform grid on [0, L]."""
    return np.linspace(0.0, L, n, dtype=float)


def iec_kappa_target(st: State, p: Params) -> np.ndarray:
    """
    IEC-1 target curvature implements a **phase drift** of the baseline curvature
    profile induced by the information field.

    A convenient model for a phase drift (that preserves wavelength content) is a
    *global* reparameterization of the baseline curvature along arc-length:

        κ_target(s) = κ0(s + Δs(s)),

    where the shift Δs is derived from the information field magnitude. We use
    the RMS of I(s) to produce a non-zero drift for oscillatory fields while
    keeping the transformation wavelength-preserving:

        Δs = χ_k * rms(I).

    IEC-2 (χ_E) is applied in solver/load amplitude rather than adding a second derivative term here.
    """
    kappa0 = np.asarray(st.kappa0, dtype=float)
    if st.I is None or p.chi_k == 0.0:
        return np.copy(kappa0)

    s = np.asarray(st.s, dtype=float)
    I = np.asarray(st.I, dtype=float)
    if s.shape != kappa0.shape or I.shape != s.shape:
        raise ValueError("State arrays (s, kappa0, I) must have the same shape.")

    L = float(s[-1] - s[0])
    if L <= 0.0:
        return np.copy(kappa0)

    delta_s = float(p.chi_k) * float(np.sqrt(np.mean(I**2)))

    # Treat κ0 as periodic on [s0, s0+L] to avoid edge clipping artifacts.
    s0 = float(s[0])
    s_shifted = ((s - s0 + delta_s) % L) + s0

    # Periodic interpolation by extending the endpoint.
    s_ext = np.concatenate([s, [s0 + L]])
    k_ext = np.concatenate([kappa0, [kappa0[0]]])
    return np.interp(s_shifted, s_ext, k_ext).astype(float)


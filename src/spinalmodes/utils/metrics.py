"""Small metrics helpers for wavelength, phase, and amplitude computations."""

from __future__ import annotations

import numpy as np


def wavelength_via_fft(y: np.ndarray, s: np.ndarray) -> float:
    """Estimate dominant wavelength via FFT magnitude peak."""
    dy = y - np.mean(y)
    freqs = np.fft.rfftfreq(len(s), d=(s[1] - s[0]))
    amp = np.abs(np.fft.rfft(dy))
    if len(freqs) < 2:
        return float("inf")
    # ignore DC
    idx_peak = np.argmax(amp[1:]) + 1
    k = freqs[idx_peak]
    return (1.0 / k) if k > 0 else float("inf")


def phase_shift_via_xcorr(y1: np.ndarray, y2: np.ndarray, s: np.ndarray) -> float:
    """Phase shift Δφ in radians such that y2 ≈ y1 shifted."""
    y1c, y2c = y1 - y1.mean(), y2 - y2.mean()
    corr = np.correlate(y1c, y2c, mode="full")
    lag = corr.argmax() - (len(y1) - 1)
    ds = s[1] - s[0]
    wavelength = wavelength_via_fft(y1, s)
    if not np.isfinite(wavelength) or wavelength == 0:
        return 0.0
    return 2.0 * np.pi * (lag * ds) / wavelength


def amplitude(y: np.ndarray) -> float:
    """Half peak-to-peak amplitude."""
    return 0.5 * (np.max(y) - np.min(y))


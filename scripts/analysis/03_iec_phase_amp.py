import matplotlib

matplotlib.use("Agg")
"""Demonstrate IEC-1 phase drift and IEC-2 amplitude modulation metrics."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from spinalmodes.model.core import Params, State, iec_kappa_target, uniform_grid
from spinalmodes.model.solvers.euler_bernoulli import integrate_shape_from_curvature
from spinalmodes.utils.metrics import amplitude, phase_shift_via_xcorr, wavelength_via_fft
from spinalmodes.utils.provenance import write_provenance
from spinalmodes.utils.seeds import set_seed


def main() -> None:
    set_seed(1337)
    p = Params(L=1.0, n=3001, chi_k=0.04)
    s = uniform_grid(p.L, p.n)
    k = 10 * np.pi
    y0 = 0.02 * np.sin(k * s)
    kappa0 = -0.02 * (k**2) * np.sin(k * s)

    # IEC-1: phase drift with preserved wavelength
    I = np.sin(2 * np.pi * s)
    st = State(s=s, kappa0=kappa0, I=I)
    kappa_tgt = iec_kappa_target(st, p)
    _, y_iec1 = integrate_shape_from_curvature(s, kappa_tgt)
    lam0 = wavelength_via_fft(y0, s)
    lam1 = wavelength_via_fft(y_iec1, s)
    dlam_pct = 100 * (lam1 - lam0) / lam0
    dphi = phase_shift_via_xcorr(y0, y_iec1, s)

    Path("figures").mkdir(parents=True, exist_ok=True)
    plt.plot(s, y0, label="baseline")
    plt.plot(s, y_iec1, "--", label="IEC-1")
    plt.title(f"IEC-1: Δλ={dlam_pct:.2f}%  Δφ={dphi:.2f} rad")
    plt.xlabel("s")
    plt.ylabel("y")
    plt.legend()
    plt.savefig("figures/iec1_phase_drift.pdf", bbox_inches="tight")

    # IEC-2: amplitude modulation (scale curvature amplitude)
    A_scale = 0.75
    kappa2 = A_scale * kappa0
    st2 = State(s=s, kappa0=kappa2, I=None)
    _, y_iec2 = integrate_shape_from_curvature(s, kappa2)
    lam2 = wavelength_via_fft(y_iec2, s)
    a0, a2 = amplitude(y0), amplitude(y_iec2)
    dlam2_pct = 100 * (lam2 - lam0) / lam0
    plt.figure()
    plt.plot(s, y0, label="baseline")
    plt.plot(s, y_iec2, "--", label="IEC-2")
    plt.title(f"IEC-2: A/A0={a2/a0:.2f}  Δλ={dlam2_pct:.2f}%")
    plt.xlabel("s")
    plt.ylabel("y")
    plt.legend()
    plt.savefig("figures/iec2_amplitude.pdf", bbox_inches="tight")

    write_provenance(
        "figures/iec_phase_amp.provenance.json",
        1337,
        {"chi_k": p.chi_k, "A_scale": A_scale},
    )


if __name__ == "__main__":
    main()

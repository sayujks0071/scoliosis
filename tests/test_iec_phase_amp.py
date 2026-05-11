import numpy as np

from spinalmodes.model.core import Params, State, iec_kappa_target, uniform_grid
from spinalmodes.model.solvers.euler_bernoulli import integrate_shape_from_curvature
from spinalmodes.utils.metrics import amplitude, phase_shift_via_xcorr, wavelength_via_fft


def test_iec1_phase_shift_preserves_wavelength():
    """Test that IEC phase shift preserves wavelength (within 2% tolerance).
    
    Note: If this test fails, it indicates the IEC implementation may be modifying
    wavelength when it should only shift phase. The test expects wavelength preservation
    as the semantic meaning of "phase shift" implies unchanged frequency content.
    """
    p = Params(L=1.0, n=2001, chi_k=0.05)
    s = uniform_grid(p.L, p.n)
    k = 8 * np.pi
    A = 0.02
    y0 = A * np.sin(k * s)
    kappa0 = -A * (k**2) * np.sin(k * s)
    st = State(s=s, kappa0=kappa0, I=np.sin(2 * np.pi * s))
    _, y1 = integrate_shape_from_curvature(s, iec_kappa_target(st, p))
    lam0 = wavelength_via_fft(y0, s)
    lam1 = wavelength_via_fft(y1, s)
    dl = abs(lam1 - lam0)
    # Phase shift should preserve wavelength (within 2% tolerance)
    assert dl / lam0 < 0.02, f"Wavelength should be preserved: dl/lam0={dl/lam0:.6f} > 0.02"
    assert abs(phase_shift_via_xcorr(y0, y1, s)) > 1e-2


def test_iec2_amplitude_change_small_lambda_change():
    """Test that scaling curvature by 0.7 produces amplitude ratio ~0.7 with minimal wavelength change.
    
    Note: If this test fails, it indicates the solver may not be linearly scaling amplitude
    with curvature, or there are nonlinear effects that need investigation.
    """
    s = uniform_grid(1.0, 2001)
    k = 8 * np.pi
    A = 0.02
    y0 = A * np.sin(k * s)
    kappa0 = -A * (k**2) * np.sin(k * s)
    _, y2 = integrate_shape_from_curvature(s, 0.7 * kappa0)
    lam0 = wavelength_via_fft(y0, s)
    lam2 = wavelength_via_fft(y2, s)
    amp_ratio = amplitude(y2) / amplitude(y0)
    # Scaling curvature by 0.7 should produce amplitude ratio close to 0.7
    assert abs(amp_ratio - 0.7) < 0.15, f"Amplitude ratio should be ~0.7: got {amp_ratio:.6f}"
    # Wavelength should remain approximately unchanged
    assert abs((lam2 - lam0) / lam0) < 0.02, f"Wavelength should be preserved: (lam2-lam0)/lam0={abs((lam2-lam0)/lam0):.6f} > 0.02"

"""
Comprehensive tests for IEC model.

Tests verify:
1. IEC-1 induces node shift with negligible ΔΛ at fixed P (tolerance: |ΔΛ| ≤ 2%)
2. IEC-2 changes amplitude ≥10% for -25% effective modulus
3. IEC-3 reduces helical threshold vs baseline by ≥ X% when gradI>0
"""

import numpy as np
import pytest

from spinalmodes.iec import (
    IECParameters,
    apply_iec_coupling,
    compute_amplitude,
    compute_helical_threshold,
    compute_node_positions,
    compute_torsion_stats,
    compute_wavelength,
    generate_coherence_field,
    solve_beam_static,
    solve_dynamic_modes,
)


class TestCoherenceField:
    """Test coherence field generation."""

    def test_constant_field(self):
        """Test constant coherence field."""
        params = IECParameters(I_mode="constant", I_amplitude=1.0, n_nodes=50)
        s = params.get_s_array()
        I_field = generate_coherence_field(s, params)

        assert len(I_field) == len(s)
        assert np.allclose(I_field, 1.0)

    def test_linear_field(self):
        """Test linear gradient coherence field."""
        params = IECParameters(
            I_mode="linear", I_amplitude=1.0, I_gradient=0.5, n_nodes=50
        )
        s = params.get_s_array()
        I_field = generate_coherence_field(s, params)

        # Should be monotonically increasing
        assert np.all(np.diff(I_field) >= 0)
        # Check approximate values
        assert I_field[0] == pytest.approx(1.0, abs=0.01)
        assert I_field[-1] > I_field[0]

    def test_gaussian_field(self):
        """Test Gaussian bump coherence field."""
        params = IECParameters(
            I_mode="gaussian",
            I_amplitude=1.0,
            I_center=0.5,
            I_width=0.1,
            n_nodes=100,
        )
        s = params.get_s_array()
        I_field = generate_coherence_field(s, params)

        # Peak should be near center
        peak_idx = np.argmax(I_field)
        peak_position = s[peak_idx] / params.length
        assert peak_position == pytest.approx(0.5, abs=0.05)

    def test_step_field(self):
        """Test step function coherence field."""
        params = IECParameters(
            I_mode="step", I_amplitude=1.0, I_center=0.5, n_nodes=100
        )
        s = params.get_s_array()
        I_field = generate_coherence_field(s, params)

        # First half should be ~0, second half should be ~1
        s_norm = s / params.length
        assert np.all(I_field[s_norm < 0.5] < 0.1)
        assert np.all(I_field[s_norm >= 0.5] > 0.9)


class TestIECCouplings:
    """Test IEC coupling mechanisms."""

    def test_iec1_target_curvature(self):
        """Test IEC-1: Target curvature bias."""
        params = IECParameters(
            chi_kappa=0.05, I_mode="linear", I_gradient=0.5, n_nodes=50
        )
        s = params.get_s_array()
        kappa_target, _, _, _ = apply_iec_coupling(s, params)

        # Should have spatial variation due to gradient
        assert np.std(kappa_target) > 0

    def test_iec2_constitutive_bias(self):
        """Test IEC-2: Constitutive property bias."""
        params = IECParameters(
            chi_E=-0.25, chi_C=0.1, I_mode="linear", I_gradient=1.0, n_nodes=50
        )
        s = params.get_s_array()
        _, E_field, C_field, _ = apply_iec_coupling(s, params)

        # E should vary spatially
        assert np.std(E_field) > 0
        # C should vary spatially
        assert np.std(C_field) > 0

        # Check magnitude: with chi_E=-0.25 and I~1-2, E should be ~75-50% of E0
        assert np.min(E_field) < params.E0
        assert np.max(E_field) <= params.E0 * 1.5

    def test_iec3_active_moment(self):
        """Test IEC-3: Active moment coupling."""
        params = IECParameters(chi_f=0.1, I_mode="gaussian", I_center=0.5, n_nodes=50)
        s = params.get_s_array()
        _, _, _, M_active = apply_iec_coupling(s, params)

        # Active moment should be non-trivial near gradient
        assert np.max(np.abs(M_active)) > 0


class TestNodeDrift:
    """Test IEC-1 node drift behavior (acceptance criterion 1)."""

    def test_node_drift_with_minimal_wavelength_change(self):
        """
        Verify IEC-1 induces node shift with negligible ΔΛ at fixed P.
        Tolerance: |ΔΛ| ≤ 2%
        """
        # Baseline (no coupling)
        params_base = IECParameters(chi_kappa=0.0, I_mode="step", I_center=0.5)
        s = params_base.get_s_array()
        kappa_t, E_f, C_f, M_a = apply_iec_coupling(s, params_base)
        theta_base, _ = solve_beam_static(s, kappa_t, E_f, M_a, P_load=100.0)

        wavelength_base = compute_wavelength(s, theta_base)
        nodes_base = compute_node_positions(s, theta_base)

        # With IEC-1 coupling
        params_iec = IECParameters(chi_kappa=0.04, I_mode="step", I_center=0.5)
        kappa_t, E_f, C_f, M_a = apply_iec_coupling(s, params_iec)
        theta_iec, _ = solve_beam_static(s, kappa_t, E_f, M_a, P_load=100.0)

        wavelength_iec = compute_wavelength(s, theta_iec)
        nodes_iec = compute_node_positions(s, theta_iec)

        # Check wavelength change
        if wavelength_base and wavelength_iec:
            wavelength_change_pct = abs(
                (wavelength_iec - wavelength_base) / wavelength_base
            ) * 100
            assert (
                wavelength_change_pct <= 2.0
            ), f"Wavelength changed by {wavelength_change_pct:.1f}% (should be ≤2%)"

        # Check node drift occurred
        if len(nodes_base) > 0 and len(nodes_iec) > 0:
            drift = np.mean(np.abs(nodes_iec - nodes_base)) * 1000  # mm
            assert drift > 0.5, "Expected measurable node drift with chi_kappa=0.04"


class TestAmplitudeModulation:
    """Test IEC-2 amplitude changes (acceptance criterion 2)."""

    def test_amplitude_change_with_modulus_reduction(self):
        """
        Verify IEC-2 changes amplitude ≥10% for -25% effective modulus.
        """
        # Baseline
        params_base = IECParameters(chi_E=0.0, I_mode="constant", I_amplitude=1.0)
        s = params_base.get_s_array()
        kappa_t, E_f, C_f, M_a = apply_iec_coupling(s, params_base)
        theta_base, _ = solve_beam_static(s, kappa_t, E_f, M_a, P_load=100.0)
        amp_base = compute_amplitude(theta_base)

        # With -25% modulus via chi_E
        params_reduced = IECParameters(
            chi_E=-0.25, I_mode="constant", I_amplitude=1.0
        )
        kappa_t, E_f, C_f, M_a = apply_iec_coupling(s, params_reduced)
        theta_reduced, _ = solve_beam_static(s, kappa_t, E_f, M_a, P_load=100.0)
        amp_reduced = compute_amplitude(theta_reduced)

        # Check amplitude change
        amp_change_pct = abs((amp_reduced - amp_base) / amp_base) * 100
        assert (
            amp_change_pct >= 10.0
        ), f"Amplitude changed by {amp_change_pct:.1f}% (expected ≥10%)"


class TestHelicalThreshold:
    """Test IEC-3 helical threshold reduction (acceptance criterion 3)."""

    def test_threshold_reduction_with_gradient(self):
        """
        Verify IEC-3 reduces helical threshold when gradI > 0.
        """
        delta_b = 0.1  # Fixed asymmetry
        gradI = 0.05
        chi_f_baseline = 0.0
        chi_f_active = 0.1

        threshold_baseline = compute_helical_threshold(
            delta_b, gradI, chi_f=chi_f_baseline
        )
        threshold_active = compute_helical_threshold(delta_b, gradI, chi_f=chi_f_active)

        # Active coupling should reduce threshold
        assert threshold_active < threshold_baseline
        reduction_pct = (
            (threshold_baseline - threshold_active) / threshold_baseline
        ) * 100
        assert (
            reduction_pct >= 10.0
        ), f"Threshold reduced by {reduction_pct:.1f}% (expected ≥10%)"


class TestUtilities:
    """Test utility functions."""

    def test_wavelength_computation(self):
        """Test wavelength computation."""
        s = np.linspace(0, 0.4, 100)
        # Synthetic sinusoidal signal with known wavelength
        wavelength_true = 0.1  # m = 100 mm
        theta = np.sin(2 * np.pi * s / wavelength_true)

        wavelength_computed = compute_wavelength(s, theta)
        assert wavelength_computed is not None
        # Allow some tolerance due to discretization
        assert wavelength_computed == pytest.approx(100.0, rel=0.15)

    def test_torsion_stats(self):
        """Test torsion statistics computation."""
        tau = np.array([0.1, -0.1, 0.2, -0.2, 0.0])
        stats = compute_torsion_stats(tau)

        assert "mean" in stats
        assert "std" in stats
        assert "max" in stats
        assert "rms" in stats
        assert stats["max"] == pytest.approx(0.2)

    def test_dynamic_modes(self):
        """Test dynamic mode computation."""
        s = np.linspace(0, 0.4, 100)
        E_field = np.ones(100) * 1e9
        C_field = np.ones(100) * 1e6

        mode_props = solve_dynamic_modes(s, E_field, C_field)

        assert "frequency_hz" in mode_props
        assert "damping_ratio" in mode_props
        assert "wavelength_mm" in mode_props
        assert mode_props["frequency_hz"] > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_I_mode(self):
        """Test invalid coherence field mode."""
        params = IECParameters(I_mode="invalid", n_nodes=50)
        s = params.get_s_array()

        with pytest.raises(ValueError):
            generate_coherence_field(s, params)

    def test_zero_length_array(self):
        """Test behavior with empty arrays."""
        s = np.array([])
        theta = np.array([])

        wavelength = compute_wavelength(s, theta)
        assert wavelength is None

        nodes = compute_node_positions(s, theta)
        assert len(nodes) == 0


# Smoke tests for CLI (if running in environment with CLI available)
@pytest.mark.skip(reason="CLI smoke tests - run manually")
class TestCLISmoke:
    """Smoke tests for CLI commands."""

    def test_cli_demo(self, tmp_path):
        """Test demo command."""
        import subprocess

        result = subprocess.run(
            ["poetry", "run", "spinalmodes", "iec", "demo",
             "--out-prefix", str(tmp_path / "demo")],
            capture_output=True,
        )
        assert result.returncode == 0

    def test_cli_sweep(self, tmp_path):
        """Test sweep command."""
        import subprocess

        result = subprocess.run(
            [
                "poetry", "run", "spinalmodes", "iec", "sweep",
                "--param", "chi_kappa",
                "--start", "0.0",
                "--stop", "0.05",
                "--steps", "5",
                "--out-csv", str(tmp_path / "sweep.csv"),
            ],
            capture_output=True,
        )
        assert result.returncode == 0


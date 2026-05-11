import os
import sys

import numpy as np

# Add repo root to path so we can import scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.experiment_energy_phase_diagram import (
    A_REF,
    CHI_BASELINE,
    L_CROSSING,
    L_REF,
    compute_energy_cost,
    compute_supply,
)


def test_constants():
    """Verify that constants match the specific experimental design (Prompt 2 alignment)."""
    assert L_REF == 0.5
    assert A_REF == 0.001
    assert L_CROSSING == 0.35
    assert CHI_BASELINE == 0.05

def test_compute_energy_cost_smoke():
    """Smoke test to ensure compute_energy_cost runs without error and returns a float."""
    L = 0.35
    chi_kappa = 0.05
    cost = compute_energy_cost(L, chi_kappa)
    assert isinstance(cost, float) or isinstance(cost, np.floating)
    assert cost >= 0.0
    assert np.isfinite(cost)

def test_compute_energy_cost_zero_chi():
    """Test with zero intrinsic curvature (chi_kappa=0)."""
    L = 0.35
    chi_kappa = 0.0
    cost = compute_energy_cost(L, chi_kappa)
    # With chi=0, kappa_target=0.
    # Both active and passive solvers have same loads and parameters.
    # So kappa_IEC should equal kappa_passive.
    # So cost should be exactly 0.
    assert np.isclose(cost, 0.0)

def test_compute_supply():
    L0 = 0.35
    S0 = 10.0
    supply = compute_supply(L0, S0, L0)
    assert np.isclose(supply, S0)

    L = 0.7
    # supply = S0 * (L/L0)^0.5
    supply_expected = S0 * (0.7/0.35)**0.5 # S0 * sqrt(2)
    assert np.isclose(compute_supply(L, S0, L0), supply_expected)

def test_high_curvature_cost():
    """Test that higher chi results in higher cost (usually)."""
    L = 0.4
    cost_low = compute_energy_cost(L, 0.01)
    cost_high = compute_energy_cost(L, 0.1)
    assert cost_high > cost_low

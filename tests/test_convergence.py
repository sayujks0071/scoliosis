import numpy as np

from spinalmodes.model.solvers.euler_bernoulli import (
    analytic_sinusoid,
    integrate_shape_from_curvature,
    l2_error,
)


def run_error(n: int) -> float:
    L, A, k = 1.0, 0.01, 6 * np.pi
    s = np.linspace(0, L, n)
    y_true = analytic_sinusoid(s, A, k)
    kappa = -A * (k**2) * np.sin(k * s)
    _, y_num = integrate_shape_from_curvature(s, kappa)
    return l2_error(y_true, y_num)


def test_refinement_improves_accuracy():
    """Test that mesh refinement improves accuracy by at least 30%.
    
    Note: If this test fails, it indicates the solver may have poor convergence
    properties or the mesh is already well-converged. For a 4x refinement, 30%
    improvement is a reasonable expectation for a well-behaved solver.
    """
    coarse = run_error(401)
    fine = run_error(1601)
    # Refinement should improve accuracy: fine mesh error should be < 70% of coarse error
    # (4x refinement should yield at least 30% improvement for well-behaved solver)
    assert fine < coarse * 0.7, f"Fine mesh error ({fine}) should be < 70% of coarse error ({coarse * 0.7:.6f})"

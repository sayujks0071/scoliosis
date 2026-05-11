import numpy as np

from spinalmodes.model.core import Params, State, iec_kappa_target, uniform_grid
from spinalmodes.model.solvers.euler_bernoulli import integrate_shape_from_curvature


def test_boundary_conditions():
    p = Params(L=1.0, n=501)
    s = uniform_grid(p.L, p.n)
    kappa0 = np.zeros_like(s)
    st = State(s=s, kappa0=kappa0)
    x, y = integrate_shape_from_curvature(s, iec_kappa_target(st, p))
    assert abs(x[0]) < 1e-12
    assert abs(y[0]) < 1e-12


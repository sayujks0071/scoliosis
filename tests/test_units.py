from spinalmodes.model.core import Params


def test_params_have_positive_length_and_points():
    p = Params()
    assert p.L > 0
    assert p.n > 10


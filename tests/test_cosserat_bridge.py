import pytest

from spinalmodes.model.solvers.cosserat import available


@pytest.mark.skipif(not available(), reason="PyElastica not installed")
def test_cosserat_bridge_available():
    assert available() is True


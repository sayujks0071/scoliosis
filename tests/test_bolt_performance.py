import numpy as np
import timeit

def test_fast_boolean_diff():
    # Benchmark function inside the test suite to document the optimization
    mask_hc = np.random.rand(5000) * 100 >= 70

    def orig(mask_hc):
        bounded = np.empty(len(mask_hc) + 2, dtype=bool)
        bounded[0] = False
        bounded[-1] = False
        bounded[1:-1] = mask_hc

        d = np.diff(bounded.astype(np.int8))
        starts = np.where(d == 1)[0]
        ends = np.where(d == -1)[0]
        return starts, ends

    def new(mask_hc):
        bounded = np.empty(len(mask_hc) + 2, dtype=bool)
        bounded[0] = False
        bounded[-1] = False
        bounded[1:-1] = mask_hc

        diff = bounded[1:] != bounded[:-1]
        starts = np.where(diff & bounded[1:])[0]
        ends = np.where(diff & bounded[:-1])[0]
        return starts, ends

    s1, e1 = orig(mask_hc)
    s2, e2 = new(mask_hc)

    assert np.all(s1 == s2)
    assert np.all(e1 == e2)


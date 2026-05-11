import numpy as np
import timeit

plddt = np.random.rand(5000) * 100
mask_hc = plddt >= 70

def orig(mask_hc):
    bounded = np.empty(len(mask_hc) + 2, dtype=bool)
    bounded[0] = False
    bounded[-1] = False
    bounded[1:-1] = mask_hc

    d = np.diff(bounded.astype(np.int8))
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0]

    valid = (ends - starts) >= 10
    starts = starts[valid]
    ends = ends[valid]
    return starts, ends

def new(mask_hc):
    # padding trick
    padded = np.concatenate(([False], mask_hc, [False]))
    d = np.diff(padded)
    # in padded diff, True means 0->1 (start), False means 1->0 ? No, diff on bool is XOR.
    # diff of int8:
    padded_int = padded.astype(np.int8)
    d2 = padded_int[1:] - padded_int[:-1]
    starts = np.where(d2 == 1)[0]
    ends = np.where(d2 == -1)[0]

    valid = (ends - starts) >= 10
    return starts[valid], ends[valid]

print(timeit.timeit(lambda: orig(mask_hc), number=10000))
print(timeit.timeit(lambda: new(mask_hc), number=10000))

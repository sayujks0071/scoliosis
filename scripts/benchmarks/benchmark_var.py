import numpy as np
import timeit

def calc_rg_orig(coords):
    center_of_mass = np.mean(coords, axis=0)
    sq_dists = np.sum((coords - center_of_mass)**2, axis=1)
    return np.sqrt(np.mean(sq_dists))

def calc_rg_var_flat(coords):
    return np.sqrt(coords.var(axis=0).sum())

coords = np.random.rand(20000, 3)

print("orig time:", timeit.timeit(lambda: calc_rg_orig(coords), number=10000))
print("var_flat time:", timeit.timeit(lambda: calc_rg_var_flat(coords), number=10000))

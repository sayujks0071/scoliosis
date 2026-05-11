import numpy as np
import timeit

def calc_rg_orig(coords):
    center_of_mass = np.mean(coords, axis=0)
    sq_dists = np.sum((coords - center_of_mass)**2, axis=1)
    return np.sqrt(np.mean(sq_dists))

def calc_rg_var(coords):
    return np.sqrt(np.sum(np.var(coords, axis=0)))

def calc_rg_var_flat(coords):
    return np.sqrt(coords.var(axis=0).sum())

coords = np.random.rand(10000, 3)

print("orig:", calc_rg_orig(coords))
print("var:", calc_rg_var(coords))
print("var_flat:", calc_rg_var_flat(coords))

print("orig time:", timeit.timeit(lambda: calc_rg_orig(coords), number=1000))
print("var time:", timeit.timeit(lambda: calc_rg_var(coords), number=1000))
print("var_flat time:", timeit.timeit(lambda: calc_rg_var_flat(coords), number=1000))

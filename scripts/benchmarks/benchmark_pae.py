import numpy as np
import timeit

def orig(pae_matrix):
    pae_mean = np.sum(pae_matrix, dtype=np.uint64) / pae_matrix.size
    return pae_mean

def new(pae_matrix):
    pae_mean = pae_matrix.sum(dtype=np.uint64) / pae_matrix.size
    return pae_mean

def new2(pae_matrix):
    pae_mean = pae_matrix.mean()
    return pae_mean

pae_matrix = np.random.randint(0, 32, size=(2000, 2000), dtype=np.uint8)

print("orig time:", timeit.timeit(lambda: orig(pae_matrix), number=1000))
print("new time:", timeit.timeit(lambda: new(pae_matrix), number=1000))
print("new2 time:", timeit.timeit(lambda: new2(pae_matrix), number=1000))

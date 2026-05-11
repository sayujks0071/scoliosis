
import time

import numpy as np


def benchmark_b_len():
    print("Benchmarking b_len calculation (10k residues, 100 runs)")
    # Synthetic data
    N = 10000
    bv1 = np.random.rand(N, 3)
    bv2 = np.random.rand(N, 3)

    # Precompute lengths (simulating analyze_structure context)
    c_len = np.linalg.norm(bv1, axis=1)
    a_len = np.linalg.norm(bv2, axis=1)

    # Original
    start = time.time()
    for _ in range(100):
        vec_ac = bv1 + bv2
        b_len = np.linalg.norm(vec_ac, axis=1)
    end = time.time()
    print(f"Original (norm): {(end-start)*1000:.2f} ms")

    # Optimized
    start = time.time()
    for _ in range(100):
        dot = np.einsum('ij,ij->i', bv1, bv2)
        b_sq = c_len**2 + a_len**2 + 2 * dot
        b_len = np.sqrt(np.maximum(b_sq, 0))
    end = time.time()
    print(f"Optimized (einsum): {(end-start)*1000:.2f} ms")

if __name__ == "__main__":
    benchmark_b_len()

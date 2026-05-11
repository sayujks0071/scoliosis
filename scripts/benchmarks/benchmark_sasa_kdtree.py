
import time

import numpy as np
from scipy.spatial import cKDTree


def benchmark_sasa_kdtree():
    """
    Benchmarks KDTree neighbor search (SASA proxy) for different protein sizes
    to determine the optimal crossover point for parallelization.
    """
    threshold_dist = 10.0
    sizes = [500, 1000, 1500, 2000, 2500, 3000, 5000]
    iterations = 50

    print(f"Benchmarking KDTree (Leaf=64, R={threshold_dist}) over {iterations} iterations...")
    print(f"{'N_residues':<12} | {'Serial (ms)':<12} | {'Parallel (ms)':<12} | {'Winner':<10}")
    print("-" * 55)

    results = {}

    for N in sizes:
        # Simulate protein chain (random walkish to be realistic density)
        # Random coords in a box scaled by N^(1/3) to maintain density
        box_size = (N * 3.8)**(1/3) * 5 # Rough estimate
        coords = np.random.rand(N, 3) * box_size

        tree = cKDTree(coords, leafsize=64)

        # Warmup
        tree.query_ball_point(coords, r=threshold_dist, workers=1)

        # 1. Serial Benchmark
        start = time.time()
        for _ in range(iterations):
            tree.query_ball_point(coords, r=threshold_dist, workers=1)
        t_seq = (time.time() - start) * 1000 / iterations

        # 2. Parallel Benchmark
        start = time.time()
        for _ in range(iterations):
            tree.query_ball_point(coords, r=threshold_dist, workers=-1)
        t_par = (time.time() - start) * 1000 / iterations

        winner = "Serial" if t_seq < t_par else "Parallel"
        print(f"{N:<12} | {t_seq:<12.3f} | {t_par:<12.3f} | {winner:<10}")
        results[N] = winner

    print("-" * 55)

    # Find crossover
    crossover = None
    for i in range(len(sizes)-1):
        if results[sizes[i]] == "Serial" and results[sizes[i+1]] == "Parallel":
            crossover = (sizes[i] + sizes[i+1]) // 2
            break

    if crossover:
        print(f"⚡ Recommended crossover threshold: N > {crossover}")
    else:
        print("⚡ No clear crossover found in range.")

if __name__ == "__main__":
    benchmark_sasa_kdtree()

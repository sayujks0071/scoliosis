
import sys
import time
from pathlib import Path

import numpy as np

# Add scripts/data_management to path to import the actual function
sys.path.append(str(Path(__file__).parent / "data_management"))

try:
    from bolt_biofold_analysis import compute_surface_metrics
except ImportError:
    print("Could not import bolt_biofold_analysis. Ensure the script is running from repo root.")
    sys.exit(1)

def compute_surface_metrics_original_logic(coords: np.ndarray):
    """
    Original memory-hungry implementation logic for baseline comparison.
    (Copied from previous version of bolt_biofold_analysis.py)
    """
    try:
        # Compute distance matrix
        # Optimization: Use broadcasting for small N
        diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
        dists = np.sqrt(np.sum(diff**2, axis=-1))

        # Count neighbors (distance < 10.0)
        # Subtract 1 to exclude self
        neighbor_counts = np.sum(dists < 10.0, axis=1) - 1
        return neighbor_counts
    except MemoryError:
        return None

def main():
    print("Benchmarking Surface Metrics (Original Logic vs New Implementation)...")

    sizes = [1000, 3000, 5000]

    for N in sizes:
        print(f"\n--- N = {N} residues ---")
        # Generate random coords
        L = (N * 120)**(1/3)
        coords = np.random.rand(N, 3) * L

        # Dummy inputs for full function
        resnames = np.array(['ALA'] * N)
        plddts = np.array([90.0] * N)

        # Original Logic
        t0 = time.time()
        res_orig = compute_surface_metrics_original_logic(coords)
        t_orig = time.time() - t0

        if res_orig is None:
            print("Original: OOM (Out of Memory)")
            t_orig = -1.0
        else:
            print(f"Original Logic: {t_orig:.4f}s")

        # New Implementation (imported)
        # The function returns a dict, we need 'exposed_surface_proxy' which is derived from neighbor_counts
        # But we can't easily get raw neighbor_counts from the function return.
        # However, we can check execution time.

        t0 = time.time()
        # The imported function does more than just neighbor counts (it filters by pLDDT etc)
        # But since we pass high pLDDT (90), it should process everything.
        metrics = compute_surface_metrics(coords, resnames, plddts)
        t_new = time.time() - t0

        print(f"New Implementation: {t_new:.4f}s")

        if t_orig != -1.0:
            speedup = t_orig / t_new
            print(f"Speedup: {speedup:.2f}x")

            # Verify correctness implicitly?
            # The original logic computes raw neighbor counts.
            # The new implementation returns 'exposed_surface_proxy' = count of (neighbors < 20 AND pLDDT >= 70).
            # Here all pLDDT=90. So all residues are candidates.
            # exposed_surface_proxy is COUNT of such residues.

            # Let's reproduce the logic on res_orig
            exposed_mask_orig = (res_orig < 20)
            exposed_count_orig = np.sum(exposed_mask_orig)

            print(f"Original Count: {exposed_count_orig}")
            print(f"New Count: {metrics['exposed_surface_proxy']}")

            if exposed_count_orig == metrics['exposed_surface_proxy']:
                 print("Results match! ✅")
            else:
                 print("Results MISMATCH! ❌")

if __name__ == "__main__":
    main()

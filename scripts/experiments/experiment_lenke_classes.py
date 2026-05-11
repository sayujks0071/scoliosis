#!/usr/bin/env python3
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from scipy.linalg import eigh

def solve_buckling_eigenmodes(N=100, lenke_type=1):
    """
    Simplified generalized eigenvalue problem for multi-segment Cosserat rod
    (B y'')'' = lambda Q y

    Now models Lenke 1-6 explicitly by modulating regional parameters.
    """
    # z from 0 (sacrum) to 1 (T1)
    z = np.linspace(0, 1, N)
    dz = z[1] - z[0]

    # Base parameters
    B = np.ones(N) * 1.0  # Stiffness
    Q = np.ones(N) * 0.1  # Instability drive

    # Regional masks (approximate normalized spine locations)
    lumbar_idx = (z >= 0.0) & (z < 0.3)      # L5-L1
    tl_junction_idx = (z >= 0.3) & (z < 0.4) # T12-T11
    thoracic_idx = (z >= 0.4) & (z < 0.8)    # T10-T2
    proximal_t_idx = (z >= 0.8) & (z <= 1.0) # T1-C

    # Base regional stiffness differences
    B[thoracic_idx] *= 1.5 # Rib cage buttressing
    B[tl_junction_idx] *= 0.689 # Thoracolumbar vulnerability (31.1% reduction)
    B[lumbar_idx] *= 1.2 # Lumbar lordosis structural bulk

    # We modulate Q based on regional variations in tau, damping b, and asymmetric loading
    # to trigger specific Lenke patterns.
    # Q represents the effective destabilizing drive (Energy Deficit window overlap).

    if lenke_type == 1:
        # Type 1 (Main Thoracic): Minimal paraspinal muscle mass + max moment arm
        Q[thoracic_idx] *= 5.0
    elif lenke_type == 2:
        # Type 2 (Double Thoracic): Proximal thoracic and main thoracic destabilize
        Q[thoracic_idx] *= 4.0
        Q[proximal_t_idx] *= 4.0
    elif lenke_type == 3:
        # Type 3 (Double Major): Thoracic and lumbar simultaneously buckle
        Q[thoracic_idx] *= 4.0
        Q[lumbar_idx] *= 4.0
    elif lenke_type == 4:
        # Type 4 (Triple Major): Proximal thoracic, main thoracic, and lumbar
        Q[proximal_t_idx] *= 3.0
        Q[thoracic_idx] *= 3.0
        Q[lumbar_idx] *= 3.0
    elif lenke_type == 5:
        # Type 5 (Thoracolumbar/Lumbar): T-L junction vulnerability dominates
        Q[tl_junction_idx] *= 6.0
        Q[lumbar_idx] *= 3.0
    elif lenke_type == 6:
        # Type 6 (Thoracolumbar/Lumbar-Main Thoracic): Lumbar > Thoracic drive
        Q[thoracic_idx] *= 2.5
        Q[tl_junction_idx] *= 5.0
        Q[lumbar_idx] *= 5.0

    # Smooth the profiles
    B = np.convolve(B, np.ones(5)/5, mode='same')
    Q = np.convolve(Q, np.ones(5)/5, mode='same')

    # Construct finite difference matrices
    D2 = np.diag(-2 * np.ones(N)) + np.diag(np.ones(N-1), 1) + np.diag(np.ones(N-1), -1)
    D2 = D2 / (dz**2)

    B_matrix = np.diag(B)
    L_matrix = np.dot(D2, np.dot(B_matrix, D2))

    # Apply Boundary conditions (Clamped at z=0: y(0)=0, y'(0)=0)
    L_matrix = L_matrix[2:-2, 2:-2]
    Q_matrix = np.diag(Q)[2:-2, 2:-2]

    # Solve generalized eigenvalue problem: L y = lambda Q y
    eigenvalues, eigenvectors = eigh(L_matrix, Q_matrix)

    # Get lowest buckling mode (first eigenvector)
    idx = np.argsort(eigenvalues)
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    return z, eigenvalues[0], eigenvectors[:, 0], B, Q

def main():
    os.makedirs('outputs/experiments', exist_ok=True)
    os.makedirs('outputs/figures', exist_ok=True)

    fig, axes = plt.subplots(2, 3, figsize=(15, 10), sharey=True)
    axes = axes.flatten()

    all_modes = []

    for l_type in range(1, 7):
        z, eval, evec, B, Q = solve_buckling_eigenmodes(N=100, lenke_type=l_type)

        full_mode = np.zeros(100)
        full_mode[2:-2] = evec
        full_mode = full_mode / np.max(np.abs(full_mode)) # Normalize amplitude

        # Determine dominant direction to align visuals nicely
        if np.sum(full_mode) < 0:
             full_mode = -full_mode

        all_modes.append(full_mode)

        ax = axes[l_type-1]
        ax.plot(full_mode, z, linewidth=3, label=f'Eigenmode (Mode 1)')
        ax.plot(Q/np.max(Q), z, 'r--', alpha=0.5, label='Instability Drive Q')
        ax.axvline(0, color='k', linestyle=':', alpha=0.5)

        ax.set_title(f'Lenke Type {l_type}')
        if l_type % 3 == 1:
            ax.set_ylabel('Normalized Position (0=Sacrum, 1=T1)')
        if l_type > 3:
            ax.set_xlabel('Lateral Deviation')
        ax.grid(True, alpha=0.3)

    axes[0].legend(loc='upper left', fontsize='small')
    plt.suptitle('Multi-segment Cosserat Rod: Lenke Curve Morphologies', fontsize=16)
    plt.tight_layout()
    plt.savefig('outputs/figures/lenke_six_types.png')
    print("Saved outputs/figures/lenke_six_types.png")

    # Save data
    z = np.linspace(0, 1, 100)
    df = pd.DataFrame({'Normalized_Position': z})
    for l_type in range(1, 7):
        df[f'Lenke_Type_{l_type}'] = all_modes[l_type-1]

    df.to_csv('outputs/experiments/lenke_six_types.csv', index=False)
    print("Saved outputs/experiments/lenke_six_types.csv")

if __name__ == '__main__':
    main()

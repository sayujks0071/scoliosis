#!/usr/bin/env python3
"""
Toy Model: The Anisotropy-Stability Link
-----------------------------------------
Simulates the critical length L_crit for spinal stability as a function of protein anisotropy A.
Based on the derivation in docs/theory/toy_model_anisotropy.md.

Equations:
    G(L) = g0 * L^4  (Destabilizing Moment Demand)
    S(L) = s0 * L^2  (Metabolic Supply)
    C(P, A) = alpha * A * P  (Maintenance Cost of Sensor P)
    P_max = S(L) / (alpha * A)
    K(P) = k0 * P    (Stabilizing Stiffness)

    Stability Condition: G(L) < K(P_max)
    => g0 * L^4 < k0 * (s0 * L^2) / (alpha * A)
    => L^2 < (k0 * s0) / (g0 * alpha * A)
    => L_crit = sqrt( (k0 * s0) / (g0 * alpha * A) )

Parameters:
    g0 = 1.0  (Normalized Gravitational Constant)
    s0 = 1.0  (Normalized Supply Constant)
    k0 = 10.0 (Stiffness Gain)
    alpha = 1.0 (Cost Coefficient)
"""

import os

import matplotlib.pyplot as plt
import numpy as np

# Create output directory
os.makedirs("outputs/figures", exist_ok=True)

def calculate_critical_length(A, g0=1.0, s0=1.0, k0=10.0, alpha=1.0):
    """Calculates L_crit for a given anisotropy A."""
    numerator = k0 * s0
    denominator = g0 * alpha * A
    return np.sqrt(numerator / denominator)

def run_simulation():
    # Anisotropy range from Isotropic (1.0) to Vimentin (7.5)
    A_values = np.linspace(1.0, 10.0, 100)
    L_crit_values = calculate_critical_length(A_values)

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(A_values, L_crit_values, label=r'$L_{crit} \propto A^{-0.5}$', color='crimson', linewidth=3)

    # Annotate Key Proteins
    proteins = {
        'Isotropic': (1.0, 'Scalar (1.0)'),
        'Actin': (3.0, 'Actin (3.0)'),
        'Piezo2': (4.44, 'Piezo2 (4.44)'),
        'Vimentin': (7.5, 'Vimentin (7.5)')
    }

    for name, (A_val, label) in proteins.items():
        L_val = calculate_critical_length(A_val)
        plt.plot(A_val, L_val, 'o', color='black', markersize=8)
        plt.annotate(f"{label}\n$L_{{crit}}={L_val:.2f}$",
                     xy=(A_val, L_val),
                     xytext=(10, 10), textcoords='offset points',
                     fontsize=10, arrowprops=dict(arrowstyle="->"))

    plt.title('The Anisotropy-Stability Link: Why High-Aspect Proteins Fail First', fontsize=14)
    plt.xlabel('Protein Anisotropy ($A$)', fontsize=12)
    plt.ylabel('Critical Stable Length ($L_{crit}$)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()

    output_path = "outputs/figures/toy_model_anisotropy_bifurcation.png"
    plt.savefig(output_path, dpi=300)
    print(f"Simulation complete. Figure saved to {output_path}")

if __name__ == "__main__":
    run_simulation()

import os
import numpy as np
import matplotlib.pyplot as plt

def simulate_lattice(chi_kappa, seed):
    np.random.seed(seed)
    N = 10
    pos = np.zeros((2, N, 2))
    pos[0, :, 0] = -0.5
    pos[1, :, 0] = 0.5
    pos[0, :, 1] = np.arange(N)
    pos[1, :, 1] = np.arange(N)

    L0_L = np.ones(N-1) + np.random.normal(0, 1e-3, N-1)
    L0_R = np.ones(N-1) + np.random.normal(0, 1e-3, N-1)

    k_vert = 10.0
    k_horiz = 10.0
    k_diag = 5.0
    beta = 1.0
    dt = 0.005
    steps = 1000

    for step in range(steps):
        vec_L = pos[0, 1:] - pos[0, :-1]
        dist_L = np.linalg.norm(vec_L, axis=1)
        dir_L = vec_L / dist_L[:, None]

        vec_R = pos[1, 1:] - pos[1, :-1]
        dist_R = np.linalg.norm(vec_R, axis=1)
        dir_R = vec_R / dist_R[:, None]

        vec_H = pos[1, :] - pos[0, :]
        dist_H = np.linalg.norm(vec_H, axis=1)
        dir_H = vec_H / dist_H[:, None]

        vec_D1 = pos[1, 1:] - pos[0, :-1]
        dist_D1 = np.linalg.norm(vec_D1, axis=1)
        dir_D1 = vec_D1 / dist_D1[:, None]

        vec_D2 = pos[0, 1:] - pos[1, :-1]
        dist_D2 = np.linalg.norm(vec_D2, axis=1)
        dir_D2 = vec_D2 / dist_D2[:, None]

        f_L = k_vert * (dist_L - L0_L)
        f_R = k_vert * (dist_R - L0_R)
        f_H = k_horiz * (dist_H - 1.0)
        f_D1 = k_diag * (dist_D1 - np.sqrt(2))
        f_D2 = k_diag * (dist_D2 - np.sqrt(2))

        F = np.zeros((2, N, 2))
        F[0, :-1] += f_L[:, None] * dir_L
        F[0, 1:]  -= f_L[:, None] * dir_L
        F[1, :-1] += f_R[:, None] * dir_R
        F[1, 1:]  -= f_R[:, None] * dir_R

        F[0, :] += f_H[:, None] * dir_H
        F[1, :] -= f_H[:, None] * dir_H

        F[0, :-1] += f_D1[:, None] * dir_D1
        F[1, 1:]  -= f_D1[:, None] * dir_D1
        F[1, :-1] += f_D2[:, None] * dir_D2
        F[0, 1:]  -= f_D2[:, None] * dir_D2

        pos[:, 1:] += dt * F[:, 1:]

        dL0_L = chi_kappa * (f_R - f_L) - beta * (L0_L - 1.0)
        dL0_R = chi_kappa * (f_L - f_R) - beta * (L0_R - 1.0)

        L0_L = np.clip(L0_L + dt * dL0_L, 0.1, 2.0)
        L0_R = np.clip(L0_R + dt * dL0_R, 0.1, 2.0)

    return pos

def main():
    seeds = range(10)
    fig, axes = plt.subplots(1, 2, figsize=(10, 6))

    chi_stable = 0.05
    for s in seeds:
        pos = simulate_lattice(chi_stable, s)
        axes[0].plot(pos[0, :, 0], pos[0, :, 1], 'b-', alpha=0.3)
        axes[0].plot(pos[1, :, 0], pos[1, :, 1], 'b-', alpha=0.3)
        for i in range(10):
            axes[0].plot([pos[0, i, 0], pos[1, i, 0]], [pos[0, i, 1], pos[1, i, 1]], 'b-', alpha=0.3)
    axes[0].set_title(fr'Stable Lattice ($\chi_\kappa = {chi_stable}$)')
    axes[0].set_xlim(-5, 5)
    axes[0].set_ylim(0, 10)

    chi_unstable = 0.5
    for s in seeds:
        pos = simulate_lattice(chi_unstable, s)
        axes[1].plot(pos[0, :, 0], pos[0, :, 1], 'r-', alpha=0.3)
        axes[1].plot(pos[1, :, 0], pos[1, :, 1], 'r-', alpha=0.3)
        for i in range(10):
            axes[1].plot([pos[0, i, 0], pos[1, i, 0]], [pos[0, i, 1], pos[1, i, 1]], 'r-', alpha=0.3)
    axes[1].set_title(fr'Buckled Lattice ($\chi_\kappa = {chi_unstable}$)')
    axes[1].set_xlim(-5, 5)
    axes[1].set_ylim(0, 10)

    buckled_count = 0
    for s in range(100):
        pos = simulate_lattice(chi_unstable, s)
        tip_deflection = np.abs((pos[0, -1, 0] + pos[1, -1, 0])/2.0)
        if tip_deflection > 1.0:
            buckled_count += 1

    fig.suptitle(f'Holographic Instability Lattice\nConsistent Buckling: {buckled_count}/100 seeds', fontsize=14)
    os.makedirs('figures/main', exist_ok=True)
    plt.savefig('figures/main/toy_model_holographic_lattice.png', dpi=300)
    print("Saved to figures/main/toy_model_holographic_lattice.png")

if __name__ == "__main__":
    main()

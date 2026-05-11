import os

import matplotlib.pyplot as plt
import numpy as np
import scipy.linalg as la


def simulate_lenke_classes():
    """
    Simulates AIS curve patterns (Lenke classifications) as eigenmodes
    of the coupled Cosserat rod system based on regional variations in bending stiffness B(s),
    proprioceptive gain K(s), and local energy deficit R(s).

    Instead of arbitrary sine waves, this solves the generalized eigenvalue problem:
    (B y'')'' = lambda Q y
    where B is the regional stiffness and Q is the regional instability drive
    (proportional to delay/damping or energy deficit).
    """
    print("Simulating Lenke Curve Classes (Eigenmodes) via Generalized Eigenvalue Problem...")

    N = 100
    s = np.linspace(0, 1, N)
    ds = s[1] - s[0]

    # Construct 2nd derivative matrix D2
    D2 = np.zeros((N, N))
    for i in range(1, N-1):
        D2[i, i-1] = 1
        D2[i, i] = -2
        D2[i, i+1] = 1
    D2 = D2 / (ds**2)

    # Restrict to interior nodes for pinned-pinned boundary conditions
    D2_int = D2[1:-1, 1:-1]

    def solve_buckling_mode(EI, tau_proprio, b_damping, num_modes=1):
        """
        Solves (EI y'')'' = lambda (tau/b) y
        Finds the fundamental buckling modes.
        """
        Q = tau_proprio / b_damping
        B_int = np.diag(EI[1:-1])
        L = D2_int @ B_int @ D2_int
        Q_int = np.diag(Q[1:-1])

        # L and Q are symmetric and positive definite (for physical parameters)
        evals, evecs = la.eigh(L, Q_int)

        modes = []
        for i in range(num_modes):
            y = np.zeros(N)
            y[1:-1] = evecs[:, i]
            # Normalize to max amplitude 1
            y = y / np.max(np.abs(y))
            # Ensure consistent sign (positive peak)
            if y[np.argmax(np.abs(y))] < 0:
                y = -y
            modes.append(y)
        return modes

    def smooth_step(x, x0, width=0.05):
        return 0.5 * (1 + np.tanh((x - x0) / width))

    def window(x, x_start, x_end, width=0.05):
        return smooth_step(x, x_start, width) - smooth_step(x, x_end, width)

    # Define base mechanical properties
    EI_base = np.ones(N)
    # The rib cage buttressing effect increases stiffness in the thoracic spine (approx s=0.15 to 0.65)
    EI_base += 2.0 * window(s, 0.15, 0.65)
    # The lower lumbar and sacral region is also naturally stiffer
    EI_base += 1.5 * window(s, 0.8, 1.0)

    # Delay base represents mechanoreceptor density & baseline transport delays
    tau_base = np.ones(N)

    # Damping represents paraspinal muscle bulk, disc composition, facet joints
    # Lower damping in the thoracic region due to thinner paraspinal muscle mass
    b_base = np.ones(N)
    b_base -= 0.3 * window(s, 0.15, 0.65)
    # Higher damping in the lumbar region due to large multifidus / erector spinae
    b_base += 0.5 * window(s, 0.65, 0.95)

    # Asymmetric Loading Bias: Aortic pulsation offset (leftward offset -> pushing spine rightward in thoracic)
    # This bias sets the sign of the buckling mode.
    bias = 0.05 * np.sin(np.pi * s) * window(s, 0.2, 0.6)

    def apply_bias(mode, bias_region):
        """Ensures the mode's sign in the main deficit region aligns with the biological bias."""
        mask = (s > bias_region[0]) & (s < bias_region[1])
        if np.sum(mode[mask] * bias[mask]) < 0:
            return -mode
        return mode

    # --- Mode 1: Lenke Type 1 (Main Thoracic) ---
    # Deficit localized in the main thoracic region
    tau_1 = np.copy(tau_base)
    tau_1 += 5.0 * window(s, 0.25, 0.6)
    modes_1 = solve_buckling_mode(EI_base, tau_1, b_base)
    mode_1_curve = apply_bias(modes_1[0], (0.25, 0.6))

    # --- Mode 2: Lenke Type 2 (Double Thoracic) ---
    # Deficits in Proximal Thoracic and Main Thoracic regions
    tau_2 = np.copy(tau_base)
    tau_2 += 4.0 * window(s, 0.05, 0.25) # Proximal Thoracic
    tau_2 += 6.0 * window(s, 0.3, 0.6)   # Main Thoracic
    EI_2 = np.copy(EI_base)
    EI_2 += 10.0 * window(s, 0.25, 0.3)  # Stable node between the two
    modes_2 = solve_buckling_mode(EI_2, tau_2, b_base, num_modes=2)
    mode_2_curve = apply_bias(modes_2[1], (0.3, 0.6))

    # --- Mode 3: Lenke Type 3 (Double Major) ---
    # Deficits in both Thoracic and Lumbar regions, separated by a stiff/stable thoracolumbar junction
    EI_3 = np.copy(EI_base)
    EI_3 += 50.0 * window(s, 0.55, 0.65) # Extremely stiff junction to act as a node
    tau_3 = np.copy(tau_base)
    tau_3 += 8.0 * window(s, 0.2, 0.55)
    tau_3 += 8.0 * window(s, 0.65, 0.95)
    modes_3 = solve_buckling_mode(EI_3, tau_3, b_base, num_modes=2)
    mode_3_curve = apply_bias(modes_3[1], (0.2, 0.55))

    # --- Mode 4: Lenke Type 4 (Triple Major) ---
    # Deficits in Cervical/Upper Thoracic, Main Thoracic, and Lumbar regions
    EI_4 = np.copy(EI_base)
    EI_4 += 20.0 * window(s, 0.2, 0.3)
    EI_4 += 20.0 * window(s, 0.55, 0.65)
    tau_4 = np.copy(tau_base)
    tau_4 += 6.0 * window(s, 0.05, 0.2)
    tau_4 += 8.0 * window(s, 0.3, 0.55)
    tau_4 += 8.0 * window(s, 0.65, 0.95)
    modes_4 = solve_buckling_mode(EI_4, tau_4, b_base, num_modes=3)
    mode_4_curve = apply_bias(modes_4[2], (0.3, 0.55))

    # --- Mode 5: Lenke Type 5 (Thoracolumbar/Lumbar) ---
    # Deficit primarily in the lumbar region (shifts L_crit rightward)
    tau_5 = np.copy(tau_base)
    tau_5 += 8.0 * window(s, 0.6, 0.95)
    modes_5 = solve_buckling_mode(EI_base, tau_5, b_base)
    mode_5_curve = modes_5[0]

    # --- Mode 6: Lenke Type 6 (Thoracolumbar/Lumbar - Main Thoracic) ---
    # TL/L dominant, MT minor.
    EI_6 = np.copy(EI_base)
    EI_6 += 15.0 * window(s, 0.55, 0.65)
    tau_6 = np.copy(tau_base)
    tau_6 += 3.0 * window(s, 0.2, 0.55)  # Minor MT
    tau_6 += 8.0 * window(s, 0.65, 0.95) # Major TL/L
    modes_6 = solve_buckling_mode(EI_6, tau_6, b_base, num_modes=2)
    mode_6_curve = apply_bias(modes_6[1], (0.65, 0.95))


    # Plotting
    fig, axes = plt.subplots(2, 3, figsize=(15, 12), sharey=True)
    axes = axes.flatten()

    # Helper function to plot shaded deficit regions
    def shade_regions(ax, regions, color):
        for (start, end) in regions:
            ax.fill_betweenx(s, -1.2, 1.2, where=(s>start)&(s<end), color=color, alpha=0.1)

    # Lenke 1
    ax = axes[0]
    ax.plot(mode_1_curve, s, color='royalblue', linewidth=3)
    ax.set_title("Lenke 1: Main Thoracic")
    shade_regions(ax, [(0.25, 0.6)], 'royalblue')

    # Lenke 2
    ax = axes[1]
    ax.plot(mode_2_curve, s, color='purple', linewidth=3)
    ax.set_title("Lenke 2: Double Thoracic")
    shade_regions(ax, [(0.05, 0.25), (0.3, 0.6)], 'purple')

    # Lenke 3
    ax = axes[2]
    ax.plot(mode_3_curve, s, color='forestgreen', linewidth=3)
    ax.set_title("Lenke 3: Double Major")
    shade_regions(ax, [(0.2, 0.55), (0.65, 0.95)], 'forestgreen')

    # Lenke 4
    ax = axes[3]
    ax.plot(mode_4_curve, s, color='firebrick', linewidth=3)
    ax.set_title("Lenke 4: Triple Major")
    shade_regions(ax, [(0.05, 0.2), (0.3, 0.55), (0.65, 0.95)], 'firebrick')

    # Lenke 5
    ax = axes[4]
    ax.plot(mode_5_curve, s, color='darkorange', linewidth=3)
    ax.set_title("Lenke 5: Thoracolumbar/Lumbar")
    shade_regions(ax, [(0.6, 0.95)], 'darkorange')

    # Lenke 6
    ax = axes[5]
    ax.plot(mode_6_curve, s, color='teal', linewidth=3)
    ax.set_title("Lenke 6: TL/L - Main Thoracic")
    shade_regions(ax, [(0.2, 0.55), (0.65, 0.95)], 'teal')

    # Common formatting
    for i, ax in enumerate(axes):
        if i == 0:
            ax.invert_yaxis()
        ax.axvline(0, color='black', linestyle='-', linewidth=1)
        ax.set_xlim(-1.2, 1.2)
        ax.set_xlabel("Lateral Curvature Mode")
        if i % 3 == 0:
            ax.set_ylabel("Normalized Spine Length (Cranial -> Caudal)")

    plt.suptitle("Lenke Classifications as Coupled Cosserat Rod Eigenmodes\n(Shaded regions indicate localized metabolic energy deficits / increased neural delay)", fontsize=16)

    output_dir = "manuscript/figures"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "fig_lenke_classes.png")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_path, dpi=300)
    print(f"Successfully generated plot: {output_path}")

if __name__ == "__main__":
    simulate_lenke_classes()

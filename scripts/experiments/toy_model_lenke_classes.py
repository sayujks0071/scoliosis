import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_bvp

def simulate_lenke_toy_model():
    """
    Toy Model D: Lenke Classifications via Spatial Energy Deficit.

    This script implements a 1D simplified model demonstrating how spatial variation
    in the Energy Deficit D(s) and Bending Stiffness B(s) selects specific
    buckling eigenmodes corresponding to Lenke curve types.

    The model solves a simplified linearized beam equation:
    B(s) * y''''(s) + P * y''(s) = F_deficit(s) * y(s)

    Where F_deficit(s) acts as an effective destabilizing force proportional
    to the local energy deficit and perturbation.
    """
    print("Running Toy Model D: Lenke Classifications...")

    # Setup spatial grid
    N = 200
    s = np.linspace(0, 1, N) # Normalized spine length (0=T1, 1=L5)

    # Base parameters
    P = 10.0 # Axial load (gravity)

    def solve_mode(B_profile, D_profile, mode_guess):
        """Solves the boundary value problem for the given profiles."""
        def bvp_system(s_val, Y):
            # Y = [y, y', y'', y''']
            y, dy, d2y, d3y = Y

            # Interpolate profiles
            B = np.interp(s_val, s, B_profile)
            D = np.interp(s_val, s, D_profile)

            # Differential equation: B * y'''' + P * y'' - D * y = 0
            # Rearranged for y'''':
            d4y = (D * y - P * d2y) / B

            return np.vstack((dy, d2y, d3y, d4y))

        def bc(Ya, Yb):
            # Hinged-hinged boundary conditions
            # y(0)=0, y''(0)=0, y(1)=0, y''(1)=0
            return np.array([Ya[0], Ya[2], Yb[0], Yb[2]])

        # Initial guess
        Y0 = np.zeros((4, len(s)))
        Y0[0] = mode_guess
        Y0[2] = -np.pi**2 * mode_guess # Rough guess for second deriv

        # Solve
        res = solve_bvp(bvp_system, bc, s, Y0, tol=1e-4, max_nodes=1000)

        if res.success:
            return res.y[0]
        else:
            print("Warning: BVP solver failed to converge.")
            return mode_guess * 0

    # --- Mode 1: Lenke Type 5 (Thoracolumbar/Lumbar single C-curve) ---
    # Deficit localized in lower spine (s > 0.5)
    B_1 = np.ones_like(s) * 1.0
    D_1 = np.exp(-((s - 0.75)**2) / 0.05) * 50.0
    mode_guess_1 = np.sin(np.pi * s)
    y_1 = solve_mode(B_1, D_1, mode_guess_1)

    # --- Mode 2: Lenke Type 3 (Double major S-curve) ---
    # Deficit localized in two regions (thoracic and lumbar)
    B_2 = np.ones_like(s) * 1.0
    D_2 = (np.exp(-((s - 0.25)**2) / 0.05) + np.exp(-((s - 0.75)**2) / 0.05)) * 100.0
    mode_guess_2 = np.sin(2 * np.pi * s)
    y_2 = solve_mode(B_2, D_2, mode_guess_2)

    # --- Mode 3: Lenke Type 4 (Triple curve) ---
    # Complex deficit profile (cervical, thoracic, lumbar)
    B_3 = np.ones_like(s) * 1.0
    D_3 = (np.exp(-((s - 0.15)**2) / 0.02) + np.exp(-((s - 0.5)**2) / 0.02) + np.exp(-((s - 0.85)**2) / 0.02)) * 250.0
    mode_guess_3 = np.sin(3 * np.pi * s)
    y_3 = solve_mode(B_3, D_3, mode_guess_3)

    # Normalize curves for visualization
    def normalize(y):
        return y / (np.max(np.abs(y)) + 1e-10)

    y_1 = normalize(y_1)
    y_2 = normalize(y_2)
    y_3 = normalize(y_3)

    # Plotting
    fig, axes = plt.subplots(2, 3, figsize=(15, 10), sharey='row')

    # Plot spatial profiles
    axes[0, 0].plot(D_1, s, 'r-', label='Energy Deficit D(s)')
    axes[0, 0].set_title('Profile: Lumbar Deficit')
    axes[0, 0].set_ylabel('Normalized Spine Length (s/L)')
    axes[0, 0].invert_yaxis()
    axes[0, 0].legend()

    axes[0, 1].plot(D_2, s, 'r-', label='Energy Deficit D(s)')
    axes[0, 1].set_title('Profile: Double Deficit')
    axes[0, 1].invert_yaxis()

    axes[0, 2].plot(D_3, s, 'r-', label='Energy Deficit D(s)')
    axes[0, 2].set_title('Profile: Triple Deficit')
    axes[0, 2].invert_yaxis()

    # Plot resulting shapes
    axes[1, 0].plot(y_1, s, color='darkorange', linewidth=3)
    axes[1, 0].set_title('Resulting Shape\nLenke Type 5 (Single C, n=1)')
    axes[1, 0].set_xlabel('Lateral Curvature')
    axes[1, 0].set_ylabel('Normalized Spine Length (s/L)')
    axes[1, 0].invert_yaxis()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].axvline(x=0, color='black', linestyle='--', alpha=0.5)

    axes[1, 1].plot(y_2, s, color='royalblue', linewidth=3)
    axes[1, 1].set_title('Resulting Shape\nLenke Type 3 (Double S, n=2)')
    axes[1, 1].set_xlabel('Lateral Curvature')
    axes[1, 1].invert_yaxis()
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].axvline(x=0, color='black', linestyle='--', alpha=0.5)

    axes[1, 2].plot(y_3, s, color='forestgreen', linewidth=3)
    axes[1, 2].set_title('Resulting Shape\nLenke Type 4 (Triple, n=3)')
    axes[1, 2].set_xlabel('Lateral Curvature')
    axes[1, 2].invert_yaxis()
    axes[1, 2].grid(True, alpha=0.3)
    axes[1, 2].axvline(x=0, color='black', linestyle='--', alpha=0.5)

    plt.suptitle("Toy Model D: Spatial Deficit Localization Dictates Lenke Curve Type", fontsize=16)

    output_dir = "outputs/figures"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "toy_model_lenke_classes.png")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"Successfully generated plot: {output_path}")

if __name__ == "__main__":
    simulate_lenke_toy_model()

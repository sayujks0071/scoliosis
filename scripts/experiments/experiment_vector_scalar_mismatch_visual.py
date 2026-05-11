
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Ensure src is in python path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

try:
    from spinalmodes.countercurvature.pyelastica_bridge import (
        PYELASTICA_AVAILABLE,
        run_protein_simulation,
    )
except ImportError:
    print("Error: Could not import pyelastica_bridge. Ensure src is in path.")
    sys.exit(1)

def run_visual_experiment():
    if not PYELASTICA_AVAILABLE:
        print("PyElastica not installed. Skipping simulation.")
        return

    output_dir = "outputs/thermodynamic_cost/figures"
    os.makedirs(output_dir, exist_ok=True)

    print("Running Vector-Scalar Mismatch Visualization...")

    # Case 1: Healthy (Matched)
    # Scalar drive (growth) is high, but Vector system (anisotropy) is flexible/isotropic
    # allowing the rod to relax into a smooth curve if needed, but here we model
    # the ability to CORRECT.
    # Actually, the hypothesis is:
    # High Anisotropy + High Active Drive -> Instability (Buckling) because the rod
    # is too stiff in one plane to accommodate the active moment, forcing torsion.

    # Healthy: Anisotropy = 1.0 (Isotropic), Active = 5.0
    print("Simulating Healthy Case...")

    # Scoliotic: Anisotropy = 5.0 (Highly Anisotropic), Active = 5.0
    print("Simulating Scoliotic Case...")

    # Plotting
    fig = plt.figure(figsize=(14, 6))

    # Subplot 1: Healthy
    ax1 = fig.add_subplot(121, projection='3d')

    # Since run_protein_simulation hides the result object, I will reimplement the loop here
    # using the lower-level API to get the centerline.


    from spinalmodes.countercurvature.coupling import CounterCurvatureParams
    from spinalmodes.countercurvature.info_fields import InfoField1D
    from spinalmodes.countercurvature.pyelastica_bridge import CounterCurvatureRodSystem

    def simulate_and_get_shape(aniso, active_k):
        n_elements = 50
        length = 0.5 # m

        # Setup Info
        s = np.linspace(0, length, n_elements + 1)
        info_center = 0.5 * length
        info_width = 0.1 * length
        I = 0.5 + 0.5 * np.exp(-0.5 * ((s - info_center) / info_width)**2)
        dIds = np.gradient(I, s)
        info = InfoField1D(s=s, I=I, dIds=dIds)

        # Params
        params = CounterCurvatureParams(
            chi_kappa=active_k * 5.0, # Scale factor
            chi_tau=0.0,
            chi_E=0.0,
            scale_length=length
        )

        # Gen with kyphosis
        kappa_gen = np.zeros((3, n_elements + 1))
        kappa_gen[1, :] = 2.0 # Natural kyphosis

        rod_system = CounterCurvatureRodSystem.from_iec(
            info=info,
            params=params,
            length=length,
            n_elements=n_elements,
            stiffness_anisotropy=aniso,
            kappa_gen=kappa_gen
        )

        result = rod_system.run_simulation(
            final_time=2.0,
            dt=1e-4,
            save_every=500,
            progress_bar=False
        )

        return result.centerline[-1] # Final shape (n_nodes, 3)

    # Run simulations again to get shapes
    shape_healthy = simulate_and_get_shape(1.0, 5.0)
    shape_scoliotic = simulate_and_get_shape(5.0, 5.0)

    # Plot Healthy
    ax1.plot(shape_healthy[:, 0], shape_healthy[:, 1], shape_healthy[:, 2], 'g-', linewidth=3, label='Spine')
    ax1.set_title("Healthy: Matched (Aniso=1.0)\nStable Correction", fontsize=14)
    ax1.set_xlabel('Lateral (X)')
    ax1.set_ylabel('Sagittal (Y)')
    ax1.set_zlabel('Vertical (Z)')
    ax1.set_xlim(-0.1, 0.1)
    ax1.set_ylim(-0.1, 0.1)
    ax1.set_zlim(0, 0.5)
    ax1.view_init(elev=20, azim=45)

    # Plot Scoliotic
    ax2 = fig.add_subplot(122, projection='3d')
    ax2.plot(shape_scoliotic[:, 0], shape_scoliotic[:, 1], shape_scoliotic[:, 2], 'r-', linewidth=3, label='Spine')
    ax2.set_title("Scoliosis: Mismatched (Aniso=5.0)\nRotational Instability", fontsize=14, color='red')
    ax2.set_xlabel('Lateral (X)')
    ax2.set_ylabel('Sagittal (Y)')
    ax2.set_zlabel('Vertical (Z)')
    ax2.set_xlim(-0.1, 0.1)
    ax2.set_ylim(-0.1, 0.1)
    ax2.set_zlim(0, 0.5)
    ax2.view_init(elev=20, azim=45)

    # Calculate Cobb angle roughly
    # Approx max deflection angle
    def get_cobb(shape):
        # Tangent vectors
        t = np.diff(shape, axis=0)
        # Project to coronal plane (X-Z)
        t_coronal = t[:, [0, 2]]
        angles = np.arctan2(t_coronal[:, 0], t_coronal[:, 1])
        return np.degrees(np.max(angles) - np.min(angles))

    cobb_h = get_cobb(shape_healthy)
    cobb_s = get_cobb(shape_scoliotic)

    ax1.text2D(0.05, 0.95, f"Cobb: {cobb_h:.1f}°", transform=ax1.transAxes)
    ax2.text2D(0.05, 0.95, f"Cobb: {cobb_s:.1f}°", transform=ax2.transAxes, color='red', fontweight='bold')

    plt.suptitle("Vector-Scalar Mismatch: The Origin of 3D Deformity", fontsize=16)

    save_path = os.path.join(output_dir, "vector_scalar_mismatch.png")
    plt.savefig(save_path, dpi=300)
    print(f"Figure saved to {save_path}")

if __name__ == "__main__":
    run_visual_experiment()

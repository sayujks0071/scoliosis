import os

import matplotlib.pyplot as plt
import numpy as np

# Ensure output directory exists
OUTPUT_DIR = "/Users/mac/LIFE/life/manuscript/figures/bcc_theory"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_informational_manifold_figure():
    """
    Generates a 3D visualization of the 'Informational Manifold' showing
    regions of high curvature (attractors/memories) vs flat regions (entropy).
    """
    print("Generating Informational Manifold Figure...")

    # Grid setup
    x = np.linspace(-3, 3, 100)
    y = np.linspace(-3, 3, 100)
    X, Y = np.meshgrid(x, y)

    # Define the manifold surface Z = f(X, Y)
    # We create a "landscape" with deep wells (attractors) and peaks (repellers)
    # This represents the structured information space
    R = np.sqrt(X**2 + Y**2)
    Z_entropy = -0.1 * (X**2 + Y**2) # General entropic curvature (gravity well)
    Z_structure = 2.0 * np.exp(-(X**2 + Y**2)) # Central stable state
    Z_noise = 0.2 * np.sin(3*X) * np.cos(3*Y) # Local fluctuations

    Z = Z_structure + Z_noise

    # Plotting
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Plot surface
    surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none', alpha=0.8)

    # Add "Counter-Curvature" vectors
    # These vectors point UP, resisting the collapse
    step = 10
    X_vec = X[::step, ::step]
    Y_vec = Y[::step, ::step]
    Z_vec = Z[::step, ::step]
    U = np.zeros_like(X_vec)
    V = np.zeros_like(Y_vec)
    W = 0.5 * np.ones_like(Z_vec) # Upward force

    ax.quiver(X_vec, Y_vec, Z_vec, U, V, W, length=0.3, color='red', label=r'Counter-Curvature $\chi_C$')

    # Labels and styling
    ax.set_title('The Informational Manifold $\\Phi$\nCounter-Curvature Resisting Entropic Flattening', fontsize=14)
    ax.set_xlabel('State Variable $x_1$ (e.g., Firing Rate)')
    ax.set_ylabel('State Variable $x_2$ (e.g., Synaptic Weight)')
    ax.set_zlabel('Potential / Probability')

    # Custom legend
    import matplotlib.lines as mlines
    red_arrow = mlines.Line2D([], [], color='red', marker='^', linestyle='None',
                              markersize=10, label=r'Counter-Curvature Force $\chi_C$')
    ax.legend(handles=[red_arrow])

    plt.savefig(os.path.join(OUTPUT_DIR, "fig_bcc_manifold_3d.pdf"))
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_bcc_manifold_3d.png"), dpi=300)
    plt.close()
    print("Saved fig_bcc_manifold_3d")

def generate_curvature_field_2d():
    """
    Generates a 2D heatmap of the curvature field with streamplot showing
    information flow being 'bent' by the curvature.
    """
    print("Generating Curvature Field 2D Figure...")

    x = np.linspace(-3, 3, 100)
    y = np.linspace(-3, 3, 100)
    X, Y = np.meshgrid(x, y)

    # Define a scalar field (Curvature K)
    # Two attractors
    K1 = np.exp(-((X-1)**2 + (Y-1)**2))
    K2 = np.exp(-((X+1)**2 + (Y+1)**2))
    K = K1 + K2

    # Define flow field (gradient of K, representing information flow towards attractors)
    # But modified by a "rotational" counter-curvature term
    U = -np.gradient(K, axis=1) - 0.5*Y # Gradient + Rotation
    V = -np.gradient(K, axis=0) + 0.5*X

    fig, ax = plt.subplots(figsize=(10, 8))

    # Heatmap of Curvature Magnitude
    cp = ax.contourf(X, Y, K, levels=20, cmap='magma')
    fig.colorbar(cp, label=r'Curvature Magnitude $|\mathcal{R}|$')

    # Streamlines of Information Flow
    st = ax.streamplot(x, y, U, V, color='white', linewidth=1, density=1.5)

    ax.set_title('Information Flow in a Curved Manifold\nClosed Loops Indicate Self-Reference ($\\oint \\chi_C \\cdot dl \neq 0$)', fontsize=14)
    ax.set_xlabel('Manifold Dimension 1')
    ax.set_ylabel('Manifold Dimension 2')

    plt.savefig(os.path.join(OUTPUT_DIR, "fig_bcc_flow_field.pdf"))
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_bcc_flow_field.png"), dpi=300)
    plt.close()
    print("Saved fig_bcc_flow_field")

if __name__ == "__main__":
    generate_informational_manifold_figure()
    generate_curvature_field_2d()

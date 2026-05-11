
import os

import matplotlib.pyplot as plt
import numpy as np


def compute_creature_vars(x, y, t, mutations=None):
    """
    Computes the internal variables of the creature algorithm.
    mutations: dict of variable overrides, e.g., {'k': 0.0, 'd_fixed': 10.0}
    """
    if mutations is None:
        mutations = {}

    # k = 5 * cos(x / 14) * cos(y / 30)
    # acts like a spatial interference pattern or standing wave
    k_raw = 5 * np.cos(x / 14) * np.cos(y / 30)
    k = mutations.get('k', k_raw)

    # e = y / 8 - 13
    # Linear gradient in y, shifted
    e = y / 8 - 13

    # mag(k, e) is distance from origin in (k, e) space
    # d seems to be related to an inverse distance or potential well
    # JS: let d = pow(mag(k, e), 2) / 59 + 4;
    mag_ke_sq = k**2 + e**2
    d_calc = mag_ke_sq / 59 + 4
    d = mutations.get('d', d_calc)

    # angleTerm = atan2(k, e)
    # Angular component in (k, e) space
    angleTerm = np.arctan2(k, e)

    # q = 60 - 3 * sin(angleTerm * e)
    # A modulation term
    q = 60 - 3 * np.sin(angleTerm * e)

    # wave = k * (3 + 4 / d * sin(d * d - t * 2))
    # Time-dependent oscillation modulated by k and d
    # If phase_freeze is True, t=0 effectively in the wave calculation
    wave_term = np.sin(d * d - t * 2)
    if mutations.get('phase_freeze', False):
         wave_term = np.sin(d * d) # t=0

    wave = k * (3 + 4 / d * wave_term)

    # c = d / 2 + e / 99 - t / 18
    # Another phase/coordinate transform term
    t_c = 0 if mutations.get('phase_freeze', False) else t
    c = d / 2 + e / 99 - t_c / 18

    # Final coordinates
    # xCoord = (q + wave) * sin(c) + 200
    # yCoord = (q + d * 9) * cos(c) + 200
    xCoord = (q + wave) * np.sin(c)
    yCoord = (q + d * 9) * np.cos(c)

    return {
        'k': k,
        'e': e,
        'd': d,
        'angleTerm': angleTerm,
        'q': q,
        'wave': wave,
        'c': c,
        'xCoord': xCoord,
        'yCoord': yCoord
    }

def visualize_variable(x_input, y_input, variable_values, var_name, output_dir, suffix=""):
    os.makedirs(output_dir, exist_ok=True)

    # First: Scatter plot of the creature shape, colored by the variable
    final_x = variable_values['xCoord']
    final_y = variable_values['yCoord']

    # Use array for color if possible, otherwise scalar
    c_val = variable_values[var_name]
    if np.isscalar(c_val):
        c_val = np.full_like(final_x, c_val)

    plt.figure(figsize=(10, 8), facecolor='black')
    sc = plt.scatter(final_x, final_y, c=c_val, s=2, cmap='viridis', alpha=0.7)
    plt.colorbar(sc, label=var_name)
    plt.title(f"Morphology: {var_name} {suffix}", color='white')
    plt.axis('equal')
    plt.axis('off')
    filename = f"creature_map_{var_name}_{suffix.strip().replace(' ', '_')}.png" if suffix else f"creature_map_{var_name}.png"
    plt.savefig(os.path.join(output_dir, filename), facecolor='black')
    plt.close()

def visualize_morphology(variable_values, output_dir, label):
    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(10, 10), facecolor='black')
    plt.scatter(variable_values['xCoord'], variable_values['yCoord'], s=1, c='white', alpha=0.5)
    plt.axis('equal')
    plt.axis('off')
    plt.title(f"Morphology: {label}", color='white')
    filename = f"morphology_{label.replace(' ', '_')}.png"
    plt.savefig(os.path.join(output_dir, filename), facecolor='black')
    plt.close()

def run_baseline(x_input, y_input, t, output_dir):
    print("Running Baseline...")
    vars_dict = compute_creature_vars(x_input, y_input, t)
    visualize_morphology(vars_dict, output_dir, "Baseline")

    variables_to_plot = ['k', 'e', 'd', 'q', 'c', 'wave']
    for var in variables_to_plot:
        visualize_variable(x_input, y_input, vars_dict, var, output_dir, suffix="Baseline")

def run_scalar_overload(x_input, y_input, t, output_dir):
    print("Running Scalar Overload (High d)...")
    # Fix d to a high constant, simulating high scalar stress/swelling
    # Looking at code: d = (mag_ke**2) / 59 + 4. Let's try d=20 (5x baseline min)
    mutations = {'d': 20.0}
    vars_dict = compute_creature_vars(x_input, y_input, t, mutations=mutations)
    visualize_morphology(vars_dict, output_dir, "Scalar Overload")

def run_vector_loss(x_input, y_input, t, output_dir):
    print("Running Vector Loss (k=0)...")
    # Set k=0, simulating loss of orientation/interference pattern
    mutations = {'k': 0.0}
    vars_dict = compute_creature_vars(x_input, y_input, t, mutations=mutations)
    visualize_morphology(vars_dict, output_dir, "Vector Loss")

def run_phase_freeze(x_input, y_input, t, output_dir):
    print("Running Phase Freeze (t=0)...")
    # Freeze time effects
    mutations = {'phase_freeze': True}
    vars_dict = compute_creature_vars(x_input, y_input, t, mutations=mutations)
    visualize_morphology(vars_dict, output_dir, "Phase Freeze")

def main():
    output_dir = "outputs/js_creature_analysis"
    os.makedirs(output_dir, exist_ok=True)

    # Setup inputs
    i_vals = np.arange(10000)
    x_input = i_vals % 80
    y_input = i_vals / 43
    t = 0 # Baseline t

    # Run Baseline
    run_baseline(x_input, y_input, t, output_dir)

    # Run Sensitivity Tests
    run_scalar_overload(x_input, y_input, t, output_dir)
    run_vector_loss(x_input, y_input, t, output_dir)
    run_phase_freeze(x_input, y_input, t + np.pi, output_dir) # Use t>0 to see effect of freeze

    print(f"Analysis complete. Outputs saved to {output_dir}")

if __name__ == "__main__":
    main()

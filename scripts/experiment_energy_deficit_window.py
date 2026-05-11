import argparse
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.spinalmodes.iec import (
    compute_amplitude,
    solve_beam_static,
)


def bimodal_gaussian(s, L, Ac=0.5, sc=0.80, sigmac=0.08, Al=0.7, sl=0.25, sigmal=0.10, I0=0.3):
    s_norm = s / L
    bump_c = Ac * np.exp(-((s_norm - sc)**2) / (2 * sigmac**2))
    bump_l = Al * np.exp(-((s_norm - sl)**2) / (2 * sigmal**2))
    return bump_c + bump_l + I0

def compute_gradient(field, s):
    return np.gradient(field, s)

DEFAULT_OUTPUT_CSV = Path("outputs/thermodynamic_cost/energy_deficit_window.csv")
DEFAULT_OUTPUT_FIGURE = Path("outputs/figures/energy_deficit_window.png")
DEFAULT_MANUSCRIPT_FIGURE = Path("manuscript/figures/energy_deficit_window.png")


def main(
    output_csv: Path = DEFAULT_OUTPUT_CSV,
    output_figure: Path = DEFAULT_OUTPUT_FIGURE,
    manuscript_figure: Path | None = DEFAULT_MANUSCRIPT_FIGURE,
):
    # Setup parameters
    L_range = np.linspace(0.25, 0.55, 30)
    chi_kappa = 0.05
    E0 = 1.0e9
    rho = 1100.0
    A_cross = 0.001
    g = 9.81
    eta_a = 1.0
    distributed_load = rho * A_cross * g  # 1100 * 0.001 * 9.81 = 10.791 N/m

    # Store results
    results = []

    # First find P_counter at L0 = 0.35m
    L0 = 0.35
    s0 = np.linspace(0, L0, 100)
    I_field0 = bimodal_gaussian(s0, L0)
    # The gradient should be calculated properly, note that gradient scales with 1/L
    # if we take gradient with respect to s.
    grad_I0 = compute_gradient(I_field0, s0)
    kappa_target0 = chi_kappa * grad_I0
    E_field0 = np.full_like(s0, E0)
    M_active0 = np.zeros_like(s0)

    # Actually wait. If we just compute mean((kappa_iec - kappa_pas)**2), does that depend on L?
    # kappa_target is chi_kappa * dI/ds. I(s) depends on s/L. So dI/ds scales as 1/L.
    # Therefore kappa_target scales as 1/L.
    # So kappa_target^2 scales as 1/L^2.
    # Then P_counter = L^2 * (1/L^2) = constant? Let's check.
    # If P_counter must scale as L^2, perhaps kappa_target is constant with L? Or we just use chi_kappa * I(s) for kappa_target directly?
    # Wait, the prompt says "P_counter ~ \eta_a * \rho * A * g * L^2 * mean(|kappa_IEC - kappa_passive|^2)"
    # If kappa_target scales as 1/L, P_counter ~ constant.
    # But wait, kappa is curvature. If the shape is constant, curvature ~ 1/L.
    # Let's fix this: "under the fixed-curvature assumption" is mentioned in the prompt / manuscript.
    # If fixed curvature assumption, then kappa_target is independent of L.
    # Let's define the information field gradient dI/ds to have a fixed amplitude!
    # Or, the equation is P_counter ~ \eta_a * \rho * A * g * L^2 * <|kappa|^2>, and the manuscript says "scaling strictly as L^2".
    # This implies <|kappa|^2> is constant.
    # So we should compute grad_I based on normalized s_norm, so that max kappa is constant?
    pass

    for L in L_range:
        s = np.linspace(0, L, 100)
        s_norm = s / L

        # Information field
        I_field = bimodal_gaussian(s, L)

        # In order to maintain the fixed-curvature assumption mentioned in the manuscript:
        # "under the fixed-curvature assumption. In contrast, the proprioceptive supply capacity S_proprio follows a sublinear maturation trajectory"
        # If we use compute_gradient(I_field, s), we get 1/L scaling for curvature.
        # But if we use compute_gradient(I_field, s_norm) / L0, we keep curvature constant?
        # Let's just use a fixed kappa_target amplitude.
        # Actually, if we compute grad_I w.r.t s_norm, it's dimensionless.
        # Let's assume the gradient is taken with respect to normalized coordinate so it doesn't diminish with L.
        grad_I = compute_gradient(I_field, s_norm)

        # IEC parameters
        kappa_target = chi_kappa * grad_I # this way kappa_target amplitude is constant with L
        E_field = np.full_like(s, E0)
        M_active = np.zeros_like(s)

        # Solve full IEC model
        theta_iec, kappa_iec = solve_beam_static(
            s, kappa_target, E_field, M_active,
            I_moment=1e-8, P_load=0.0, distributed_load=distributed_load
        )

        # Solve passive model (chi_kappa = 0)
        theta_pas, kappa_pas = solve_beam_static(
            s, np.zeros_like(s), E_field, M_active,
            I_moment=1e-8, P_load=0.0, distributed_load=distributed_load
        )

        # Calculate P_counter
        # P_counter(L) = \eta_a * \rho * A * g * L^2 * mean(|kappa_IEC - kappa_passive|^2)
        mean_sq_diff = np.mean((kappa_iec - kappa_pas)**2)
        P_counter = eta_a * rho * A_cross * g * (L**2) * mean_sq_diff

        # Calculate Cobb angle (using amplitude of theta_iec)
        cobb_angle = compute_amplitude(theta_iec)

        # Calculate geodesic deviation D_geo
        D_geo = np.mean(np.abs(theta_iec - theta_pas))

        results.append({
            'L': L,
            'P_counter': P_counter,
            'mean_sq_diff': mean_sq_diff,
            'Cobb_angle': cobb_angle,
            'D_geo': D_geo
        })

    df = pd.DataFrame(results)

    # Calculate S_proprio
    # S0 is P_counter at L0 = 0.35
    row0 = df.iloc[(df['L'] - 0.35).abs().argsort()[:1]]
    S0 = row0['P_counter'].values[0]
    L0 = 0.35

    df['S_proprio_alpha05'] = S0 * ((df['L'] / L0) ** 0.5)
    df['S_proprio_alpha10'] = S0 * ((df['L'] / L0) ** 1.0)

    # Save CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)

    # Generate Figure
    plt.figure(figsize=(10, 6))

    L_array = df['L'].values
    P_array = df['P_counter'].values
    p = np.polyfit(np.log(L_array), np.log(P_array), 1)
    print(f"Scaling exponent: {p[0]:.2f}")

    plt.plot(df['L'], df['P_counter'], 'r-', linewidth=2, label=r'$P_{counter}(L)$ (Demand)')
    plt.plot(df['L'], df['S_proprio_alpha05'], 'b--', linewidth=2, label=r'$S_{proprio}$ ($\alpha=0.5$)')
    plt.plot(df['L'], df['S_proprio_alpha10'], 'b:', linewidth=2, label=r'$S_{proprio}$ ($\alpha=1.0$)')

    # Find intersection for alpha=0.5
    intersection_idx = np.where(df['P_counter'] > df['S_proprio_alpha05'])[0]
    if len(intersection_idx) > 0:
        L_crit_idx = intersection_idx[0]
        L_crit = df['L'].iloc[L_crit_idx]
        plt.axvline(L_crit, color='k', linestyle='--', alpha=0.5, label=f'$L_{{crit}} \\approx {L_crit:.2f}$ m')

        # Shade the energy deficit window
        plt.fill_between(df['L'].iloc[L_crit_idx:],
                         df['S_proprio_alpha05'].iloc[L_crit_idx:],
                         df['P_counter'].iloc[L_crit_idx:],
                         color='red', alpha=0.2, label='Energy Deficit Window')

    plt.xlabel('Spinal Length $L$ (m)')
    plt.ylabel('Metabolic Power / Supply (normalized)')
    plt.title('Thermodynamic Cost of Countercurvature')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Save figures
    output_figure.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_figure, dpi=300, bbox_inches='tight')
    print(f"Saved {output_figure}")

    if manuscript_figure is not None:
        manuscript_figure.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(manuscript_figure, dpi=300, bbox_inches='tight')
        print(f"Saved {manuscript_figure}")

    plt.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate the energy deficit window analysis.")
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=DEFAULT_OUTPUT_CSV,
        help="Path for the output CSV.",
    )
    parser.add_argument(
        "--output-figure",
        type=Path,
        default=DEFAULT_OUTPUT_FIGURE,
        help="Path for the output PNG figure.",
    )
    parser.add_argument(
        "--manuscript-figure",
        type=Path,
        default=DEFAULT_MANUSCRIPT_FIGURE,
        help="Path for the manuscript figure output.",
    )
    parser.add_argument(
        "--skip-manuscript-figure",
        action="store_true",
        help="Skip writing the manuscript figure copy.",
    )
    args = parser.parse_args()

    main(
        output_csv=args.output_csv,
        output_figure=args.output_figure,
        manuscript_figure=None if args.skip_manuscript_figure else args.manuscript_figure,
    )

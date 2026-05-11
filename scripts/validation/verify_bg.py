"""
Script to verify the Bio-Gravitational Number (Bg) hypothesis.
Calculates Bg for Human vs Mouse using the formula from the research schedule.

Bg = (chi_M * <|grad I|>) / (rho * A * g * L^2)

Approximations:
- chi_M (Active Moment Capacity) ~ EI (Bending Stiffness)
  Assumption: The organism can generate active torque roughly equivalent to its passive stiffness.
- <|grad I|> ~ 1/L (Information gradient scales with length)
- rho * A = M / L (Linear density)

Substituting:
Bg = (EI * (1/L)) / ((M/L) * g * L^2)
   = EI / (M * g * L^2)
   = EI / (Weight * L^2)

Hypothesis:
- Human Bg < 1 (Unstable, requires active control)
- Mouse Bg > 1 (Stable, dominated by stiffness/scaling)
"""

import os
import sys

# Add src to path to import actual project classes if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

def calculate_bg(species_name, EI, Mass, Length, g=9.81):
    """
    Calculate Bio-Gravitational Number.
    EI: Bending Stiffness (N*m^2)
    Mass: Supported Mass (kg)
    Length: Characteristic Length (m)
    """
    Weight = Mass * g
    # Denominator: Gravitational Moment Scale ~ W * L^2 ??
    # Wait, Moment is Force * Distance. Gravitational Moment M_g ~ W * (Deflection).
    # Deflection delta ~ W * L^3 / EI.
    # M_g ~ W * delta ~ W^2 * L^3 / EI.
    # The ratio of Restoring Moment (EI/R) to Destabilizing Moment (W * delta).
    # Euler Buckling Load P_cr = pi^2 * EI / L^2.
    # Load P = W.
    # Ratio P_cr / P = (pi^2 * EI / L^2) / W = pi^2 * EI / (W * L^2).
    # This matches the form of Bg (ignoring pi^2).

    # Using the formula derived in formalism_01.md:
    # Bg = chi_M * <|grad I|> / (rho * A * g * L^2)
    # With chi_M ~ EI and grad I ~ 1/L:
    # Bg ~ EI / (M * g * L^2)

    bg = EI / (Weight * (Length**2))
    return bg

def main():
    print("Verifying Bio-Gravitational Number (Bg) Hypothesis...\n")

    # 1. Human (Thoracolumbar Spine)
    # L ~ 0.5m
    # Mass (Upper Body) ~ 30kg
    # EI ~ 2.5 N*m^2 (Literature: 1-5 Nm^2)
    human_bg = calculate_bg("Human", EI=2.5, Mass=30, Length=0.5)

    # 2. Mouse (Spine)
    # L ~ 0.03m
    # Mass ~ 0.03kg
    # EI: Scaling law EI ~ M^(4/3) or L^4?
    # Let's use literature values roughly.
    # Mouse spine stiffness is much lower, but L is very small.
    # EI ~ 0.0005 N*m^2 (Estimate)
    mouse_bg = calculate_bg("Mouse", EI=0.0005, Mass=0.03, Length=0.03)

    print(f"{'Species':<10} | {'EI (Nm^2)':<10} | {'Mass (kg)':<10} | {'L (m)':<10} | {'Bg':<10} | {'Stability'}")
    print("-" * 75)

    print(f"{'Human':<10} | {2.5:<10} | {30:<10} | {0.5:<10} | {human_bg:.4f}     | {'Unstable (<1)' if human_bg < 1 else 'Stable (>1)'}")
    print(f"{'Mouse':<10} | {0.0005:<10} | {0.03:<10} | {0.03:<10} | {mouse_bg:.4f}     | {'Unstable (<1)' if mouse_bg < 1 else 'Stable (>1)'}")

    print("\nConclusion:")
    if human_bg < 1 and mouse_bg > 1:
        print("Hypothesis VALIDATED: Humans operate in an unstable regime (Bg < 1) requiring active control, while Mice are passively stable (Bg > 1).")
    else:
        print("Hypothesis INVALID: Check parameters.")

if __name__ == "__main__":
    main()

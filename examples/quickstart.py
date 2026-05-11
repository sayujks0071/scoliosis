"""
Quickstart example for the biological countercurvature framework.

This script:
1) Builds a simple information field I(s) on a 1D axis.
2) Maps it to a rest curvature κ_rest(s).
3) Solves a static beam under gravity with and without information coupling.
4) Computes the countercurvature metric g_eff(s) and geodesic curvature deviation D_geo.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from spinalmodes import solve_beam_static
from spinalmodes.countercurvature.api import (
    CounterCurvatureParams,
    InfoField1D,
    compute_countercurvature_metric,
    compute_effective_stiffness,
    compute_rest_curvature,
    geodesic_curvature_deviation,
)


def main() -> None:
    # 1) Simple 1D axis
    n_nodes = 80
    length = 0.4
    s = np.linspace(0.0, length, n_nodes)

    # 2) Gaussian information field centered in the middle
    center = 0.5 * length
    width = 0.1 * length
    I = np.exp(-0.5 * ((s - center) / width) ** 2)
    dIds = np.gradient(I, s)
    info = InfoField1D(s=s, I=I, dIds=dIds)

    # 3) Map information to rest curvature and stiffness
    cc_params = CounterCurvatureParams(chi_kappa=0.05, chi_E=0.1, chi_M=0.0)
    kappa_rest = compute_rest_curvature(info, cc_params, kappa_gen=np.zeros_like(s))
    E_info = compute_effective_stiffness(info, cc_params, E0=1e9)

    # 4) Solve beam under gravity: passive vs info-coupled
    kappa_zero = np.zeros_like(s)
    E_passive = np.ones_like(s) * 1e9
    M_zero = np.zeros_like(s)

    theta_passive, kappa_passive = solve_beam_static(
        s,
        kappa_zero,
        E_passive,
        M_zero,
        I_moment=1e-8,
        distributed_load=100.0,
    )

    theta_info, kappa_info = solve_beam_static(
        s,
        kappa_rest,
        E_info,
        M_zero,
        I_moment=1e-8,
        distributed_load=100.0,
    )

    # 5) Countercurvature metric and geodesic deviation
    g_eff = compute_countercurvature_metric(info, beta1=1.0, beta2=0.5)
    geo = geodesic_curvature_deviation(s, kappa_passive, kappa_info, g_eff)

    print("Quickstart results")
    print(f"  D_geo      = {geo['D_geo']:.6f}")
    print(f"  D_geo_norm = {geo['D_geo_norm']:.6f}")

    # 6) Plot curvature profiles
    fig = plt.figure(figsize=(6, 4))
    plt.plot(s, kappa_passive, label="κ_passive", linewidth=2)
    plt.plot(s, kappa_info, label="κ_info", linewidth=2)
    plt.xlabel("Arc-length s (m)")
    plt.ylabel("Curvature κ (1/m)")
    plt.title(f"Geodesic deviation (D̂_geo={geo['D_geo_norm']:.3f})")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()

    out_dir = Path("outputs/examples")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_path = out_dir / "quickstart_curvature.png"
    plt.savefig(fig_path, dpi=200)
    print(f"Saved plot to {fig_path}")


if __name__ == "__main__":
    main()

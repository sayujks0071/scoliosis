import matplotlib

matplotlib.use("Agg")
"""Toy countercurvature phase diagram mapping (alpha, chi_kappa)."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from spinalmodes.utils.provenance import write_provenance
from spinalmodes.utils.seeds import set_seed


def main() -> None:
    set_seed(1337)
    alpha = np.linspace(-2, 2, 81)
    chik = np.linspace(-0.2, 0.2, 81)
    A, C = np.meshgrid(alpha, chik, indexing="xy")
    criterion = (A * C < 0) & (np.abs(A * C) > 0.05)

    Path("figures").mkdir(parents=True, exist_ok=True)
    plt.imshow(
        criterion.astype(int),
        origin="lower",
        extent=[alpha.min(), alpha.max(), chik.min(), chik.max()],
        aspect="auto",
    )
    plt.xlabel(r"$\alpha$ (metric weighting)")
    plt.ylabel(r"$\chi_{\kappa}$ (IEC-1)")
    plt.title("Countercurvature Phase Diagram (toy)")
    plt.colorbar(label="criterion true(1)/false(0)")
    plt.savefig("figures/countercurvature_phase_diagram.pdf", bbox_inches="tight")
    write_provenance("figures/countercurvature_phase_diagram.provenance.json", 1337, {})


if __name__ == "__main__":
    main()

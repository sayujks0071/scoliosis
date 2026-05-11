"""AlphaGold (AlphaFold) dataset integration.

The user request mentioned "Google alpha gold" and later "google algpafold".
We interpret this as Google DeepMind **AlphaFold** outputs.

This module provides:
- A strict CSV loader for pre-extracted 1D profiles (s, I, kappa)
- A lightweight AlphaFold PDB reader that extracts:
  - Cα backbone coordinates (for geometric curvature κ(s))
  - pLDDT confidence stored in the PDB B-factor column (as an information proxy I(s))

No external biology libraries (e.g. BioPython) are required.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from spinalmodes.countercurvature import (
    CounterCurvatureParams,
    InfoField1D,
    compute_countercurvature_metric,
    compute_effective_metric_deviation,
    compute_rest_curvature,
    geodesic_curvature_deviation,
)

ArrayF64 = NDArray[np.float64]


@dataclass(frozen=True)
class AlphaGoldSample:
    """Single 1D sample for countercurvature analysis."""

    sample_id: str
    s_m: ArrayF64
    I: ArrayF64
    kappa_passive_1_per_m: ArrayF64
    metadata: dict[str, Any]

    def info_field(self) -> InfoField1D:
        return InfoField1D.from_array(self.s_m, self.I)


@dataclass(frozen=True)
class AlphaGoldDataset:
    """Collection of AlphaGold samples."""

    samples: tuple[AlphaGoldSample, ...]

    def __iter__(self) -> Iterable[AlphaGoldSample]:
        return iter(self.samples)


def _compute_discrete_curvature_from_polyline(points: ArrayF64, s: ArrayF64) -> ArrayF64:
    """Compute curvature magnitude κ(s) from a 3D polyline using finite differences.

    For a curve r(s), curvature magnitude is κ = ||dT/ds|| with T = dr/ds / ||dr/ds||.
    """
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("points must have shape (N, 3)")
    if s.ndim != 1 or s.shape[0] != points.shape[0]:
        raise ValueError("s must have shape (N,) matching points")
    if np.any(np.diff(s) <= 0.0):
        raise ValueError("s must be strictly increasing")

    dr_ds = np.gradient(points, s, axis=0, edge_order=2)
    speed = np.linalg.norm(dr_ds, axis=1)
    speed = np.maximum(speed, 1e-12)
    T = dr_ds / speed[:, None]
    dT_ds = np.gradient(T, s, axis=0, edge_order=2)
    kappa = np.linalg.norm(dT_ds, axis=1)
    return kappa.astype(float)


def load_alpha_gold_csv(path: str | Path) -> AlphaGoldDataset:
    """Load a pre-extracted AlphaGold dataset from CSV.

    Expected columns:
    - sample_id (string)
    - s_m (float): arc-length coordinate in meters
    - I (float): information proxy (dimensionless)
    - kappa_passive_1_per_m (float): baseline curvature in 1/m
    """
    df = pd.read_csv(path)
    required = {"sample_id", "s_m", "I", "kappa_passive_1_per_m"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in AlphaGold CSV: {sorted(missing)}")

    samples: list[AlphaGoldSample] = []
    for sample_id, g in df.groupby("sample_id", sort=False):
        g2 = g.sort_values("s_m")
        s = g2["s_m"].to_numpy(dtype=float)
        I = g2["I"].to_numpy(dtype=float)
        kappa = g2["kappa_passive_1_per_m"].to_numpy(dtype=float)
        samples.append(
            AlphaGoldSample(
                sample_id=str(sample_id),
                s_m=s,
                I=I,
                kappa_passive_1_per_m=kappa,
                metadata={"source": str(path), "format": "csv"},
            )
        )

    if not samples:
        raise ValueError("No samples found in CSV.")
    return AlphaGoldDataset(samples=tuple(samples))


def load_alphafold_pdb(
    pdb_path: str | Path,
    *,
    sample_id: Optional[str] = None,
    chain_id: Optional[str] = None,
) -> AlphaGoldSample:
    """Load an AlphaFold PDB and extract a 1D profile.

    - Uses **Cα atoms** to build a polyline.
    - Uses **B-factor** as pLDDT proxy (AlphaFold convention) for information I(s).

    Parameters
    ----------
    pdb_path:
        Path to a PDB file (e.g., from AlphaFold DB).
    sample_id:
        Optional identifier; defaults to stem of pdb file name.
    chain_id:
        Optional chain filter; if None, uses the first chain encountered.
    """
    pdb_path = Path(pdb_path)
    if sample_id is None:
        sample_id = pdb_path.stem

    if not pdb_path.exists():
        raise FileNotFoundError(str(pdb_path))

    coords: list[list[float]] = []
    plddt: list[float] = []
    residues: list[tuple[str, int]] = []
    chosen_chain: Optional[str] = None

    # Minimal PDB parser: parse ATOM lines for CA
    for line in pdb_path.read_text().splitlines():
        if not line.startswith("ATOM"):
            continue
        atom_name = line[12:16].strip()
        if atom_name != "CA":
            continue
        this_chain = line[21].strip() or " "
        if chain_id is not None and this_chain != chain_id:
            continue
        if chosen_chain is None:
            chosen_chain = this_chain
        if this_chain != chosen_chain:
            continue

        # Residue identity to keep ordering (resseq)
        resseq = int(line[22:26].strip())
        icode = line[26].strip()
        res_key = (this_chain, resseq if not icode else int(f"{resseq}"))  # stable-ish

        x = float(line[30:38].strip())
        y = float(line[38:46].strip())
        z = float(line[46:54].strip())
        b = float(line[60:66].strip())  # AlphaFold pLDDT convention

        coords.append([x, y, z])
        plddt.append(b)
        residues.append(res_key)

    if not coords:
        raise ValueError("No Cα atoms found in PDB (or chain filter excluded all atoms).")

    points = np.asarray(coords, dtype=float)
    # Convert Angstrom to meters for consistency with the codebase (1 Å = 1e-10 m)
    points_m = points * 1e-10

    # Arc-length parameterization
    d = np.linalg.norm(np.diff(points_m, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(d)]).astype(float)

    # Information proxy: normalize pLDDT (0..100) -> [0, 1]
    I = (np.asarray(plddt, dtype=float) / 100.0).astype(float)

    # Geometric curvature from polyline (baseline / "passive" κ)
    kappa = _compute_discrete_curvature_from_polyline(points_m, s)

    return AlphaGoldSample(
        sample_id=str(sample_id),
        s_m=s,
        I=I,
        kappa_passive_1_per_m=kappa,
        metadata={
            "source": str(pdb_path),
            "format": "pdb",
            "chain_id": chosen_chain,
            "info_proxy": "plddt_from_bfactor",
            "units": {"coords": "m", "s": "m", "kappa": "1/m"},
        },
    )


def compute_alpha_gold_countercurvature_metrics(
    sample: AlphaGoldSample,
    *,
    chi_kappa: float = 0.02,
    beta1: float = 1.0,
    beta2: float = 0.5,
) -> dict[str, Any]:
    """Compute countercurvature metrics for an AlphaGold sample.

    We interpret:
    - κ_passive(s): geometric curvature extracted from data (or provided by CSV)
    - I(s): information proxy (e.g., AlphaFold pLDDT or a user-provided field)

    Then we generate an information-biased curvature
        κ_info = κ_passive + χ_κ * ∂I/∂s
    and compute the geodesic deviation in the countercurvature metric g_eff(I, ∂I/∂s).
    """
    info = sample.info_field()
    g_eff = compute_countercurvature_metric(info, beta1=beta1, beta2=beta2)

    params = CounterCurvatureParams(
        chi_kappa=float(chi_kappa),
        chi_E=0.0,
        chi_M=0.0,
        scale_length=float(sample.s_m[-1]) if float(sample.s_m[-1]) > 0.0 else 1.0,
    )
    kappa_info = compute_rest_curvature(info, params, sample.kappa_passive_1_per_m)

    # Extract planar component (index 1) for scalar 1D metrics
    # compute_rest_curvature places the passive curvature in index 1.
    kappa_info_planar = kappa_info[1]

    geo = geodesic_curvature_deviation(
        sample.s_m,
        sample.kappa_passive_1_per_m,
        kappa_info_planar,
        g_eff,
    )
    metric_dev = compute_effective_metric_deviation(
        sample.kappa_passive_1_per_m, kappa_info_planar, s=sample.s_m
    )

    return {
        "sample_id": sample.sample_id,
        "n_points": int(sample.s_m.size),
        "inputs": {
            "chi_kappa": float(chi_kappa),
            "beta1": float(beta1),
            "beta2": float(beta2),
        },
        "summary": {
            **geo,
            "effective_metric_deviation": float(metric_dev),
            "s_total_m": float(sample.s_m[-1]),
            "I_mean": float(np.mean(sample.I)),
            "I_min": float(np.min(sample.I)),
            "I_max": float(np.max(sample.I)),
        },
        "metadata": sample.metadata,
    }


__all__ = [
    "AlphaGoldSample",
    "AlphaGoldDataset",
    "load_alpha_gold_csv",
    "load_alphafold_pdb",
    "compute_alpha_gold_countercurvature_metrics",
]


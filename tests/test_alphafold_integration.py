from __future__ import annotations

from pathlib import Path

import numpy as np

from spinalmodes.datasets.alpha_gold import (
    compute_alpha_gold_countercurvature_metrics,
    load_alphafold_pdb,
)


def test_load_alphafold_pdb_and_compute_metrics(tmp_path: Path) -> None:
    # Minimal PDB with 5 CA atoms in a gentle arc; B-factors are pLDDT-like values.
    pdb_text = "\n".join(
        [
            "ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00 90.00           C",
            "ATOM      2  CA  ALA A   2       1.500   0.000   0.200  1.00 80.00           C",
            "ATOM      3  CA  ALA A   3       3.000   0.000   0.800  1.00 70.00           C",
            "ATOM      4  CA  ALA A   4       4.500   0.000   1.800  1.00 60.00           C",
            "ATOM      5  CA  ALA A   5       6.000   0.000   3.200  1.00 50.00           C",
            "TER",
            "END",
        ]
    )
    pdb_path = tmp_path / "AF_TEST.pdb"
    pdb_path.write_text(pdb_text)

    sample = load_alphafold_pdb(pdb_path)
    assert sample.sample_id == "AF_TEST"
    assert sample.s_m.shape == (5,)
    assert sample.I.shape == (5,)
    assert sample.kappa_passive_1_per_m.shape == (5,)
    assert np.all(sample.s_m >= 0.0)
    assert np.all(np.diff(sample.s_m) > 0.0)
    # pLDDT normalization: 90 -> 0.9, 50 -> 0.5
    assert np.isclose(sample.I[0], 0.9)
    assert np.isclose(sample.I[-1], 0.5)

    metrics = compute_alpha_gold_countercurvature_metrics(sample, chi_kappa=0.02)
    assert metrics["sample_id"] == "AF_TEST"
    assert metrics["n_points"] == 5
    summary = metrics["summary"]
    for key in [
        "D_geo",
        "D_geo_sq",
        "D_geo_norm",
        "base_energy",
        "effective_metric_deviation",
        "s_total_m",
        "I_mean",
        "I_min",
        "I_max",
    ]:
        assert key in summary
        assert np.isfinite(summary[key])


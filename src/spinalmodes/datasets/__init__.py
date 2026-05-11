"""Dataset ingestion utilities for spinalmodes.

This package contains small, strict loaders for external datasets used to
evaluate the countercurvature / IEC hypotheses against measured or curated
biological profiles.
"""

from .alpha_gold import (
    AlphaGoldDataset,
    AlphaGoldSample,
    compute_alpha_gold_countercurvature_metrics,
    load_alpha_gold_csv,
)

__all__ = [
    "AlphaGoldDataset",
    "AlphaGoldSample",
    "compute_alpha_gold_countercurvature_metrics",
    "load_alpha_gold_csv",
]


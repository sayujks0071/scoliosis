"""Countercurvature modelling layer for spinalmodes."""

from . import api as api
from .api import *  # noqa: F401,F403
from .info_fields import make_uniform_grid
from .pyelastica_bridge import PYELASTICA_AVAILABLE, SimulationResult
from .scoliosis_metrics import (
    apply_info_asymmetry,
    build_lateral_curvature_bump,
    thoracic_bump,
)
from .validation_and_metrics import (
    compare_with_beam_solver,
    compute_countercurvature_energy,
    compute_effective_metric_deviation,
    compute_shape_preservation_index,
)

__all__ = [
    *api.__all__,  # type: ignore[name-defined]
    "make_uniform_grid",
    "compute_countercurvature_energy",
    "compute_effective_metric_deviation",
    "compute_shape_preservation_index",
    "compare_with_beam_solver",
    "thoracic_bump",
    "apply_info_asymmetry",
    "build_lateral_curvature_bump",
    "PYELASTICA_AVAILABLE",
    "SimulationResult",
]

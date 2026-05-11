"""Spinal modes: Counter-curvature and IEC model."""

import sys

if sys.version_info < (3, 10):
    raise RuntimeError("spinalmodes requires Python >= 3.10")

__version__ = "0.4.0"

from spinalmodes.iec import (
    IECParameters,
    apply_iec_coupling,
    generate_coherence_field,
    solve_beam_static,
)

__all__ = [
    "IECParameters",
    "apply_iec_coupling",
    "generate_coherence_field",
    "solve_beam_static",
]

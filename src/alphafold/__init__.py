"""
AlphaFold EBI API Client Package.

This package provides a synchronous Python client for interacting with the
AlphaFold Protein Structure Database (EBI) API, along with Pydantic models
for response validation.
"""

from .ebi_client import AlphaFoldEbiClient
from .models import (
    AnnotationResponse,
    PredictionEntry,
    StructureSummary,
    UniprotEntry,
    UniprotSummary,
)

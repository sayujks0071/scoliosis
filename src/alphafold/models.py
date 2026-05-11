from typing import List, Optional

from pydantic import BaseModel, Field

# --- Prediction Endpoint Models ---

class PredictionEntry(BaseModel):
    """
    Represents a single prediction entry from the /api/prediction/{uniprot_id} endpoint.
    """
    entryId: str
    gene: Optional[str] = None
    uniprotAccession: Optional[str] = None
    uniprotId: Optional[str] = None
    uniprotDescription: Optional[str] = None
    taxId: Optional[int] = None
    organismScientificName: Optional[str] = None
    uniprotSequence: Optional[str] = None
    modelCreatedDate: Optional[str] = None
    latestVersion: Optional[int] = None
    allVersions: Optional[List[int]] = None
    providerId: Optional[str] = None
    toolUsed: Optional[str] = None

    # URLs
    pdbUrl: Optional[str] = None
    cifUrl: Optional[str] = None
    bcifUrl: Optional[str] = None
    paeImageUrl: Optional[str] = None
    msaUrl: Optional[str] = None
    plddtDocUrl: Optional[str] = None
    paeDocUrl: Optional[str] = None

    # Metrics
    globalMetricValue: Optional[float] = None
    fractionPlddtVeryLow: Optional[float] = None
    fractionPlddtLow: Optional[float] = None
    fractionPlddtConfident: Optional[float] = None
    fractionPlddtVeryHigh: Optional[float] = None

    # Sequence info
    sequence: Optional[str] = None
    sequenceStart: Optional[int] = None
    sequenceEnd: Optional[int] = None
    uniprotStart: Optional[int] = None
    uniprotEnd: Optional[int] = None

    class Config:
        extra = "ignore"


# --- Summary Endpoint Models ---

class UniprotEntry(BaseModel):
    """Represents core UniProt entry details from the summary endpoint."""
    ac: str
    id: str
    uniprot_checksum: Optional[str] = None
    sequence_length: Optional[int] = None
    segment_start: Optional[int] = None
    segment_end: Optional[int] = None

class Entity(BaseModel):
    """Represents a biological entity (protein, polymer) in the structure."""
    entity_type: Optional[str] = None
    entity_poly_type: Optional[str] = None
    identifier: Optional[str] = None
    identifier_category: Optional[str] = None
    description: Optional[str] = None
    chain_ids: Optional[List[str]] = None

class StructureSummary(BaseModel):
    """Summary of a specific structure model available for the protein."""
    model_identifier: str
    model_category: Optional[str] = None
    model_url: Optional[str] = None
    model_format: Optional[str] = None
    model_type: Optional[str] = None
    model_page_url: Optional[str] = None
    provider: Optional[str] = None
    created: Optional[str] = None
    sequence_identity: Optional[float] = None
    uniprot_start: Optional[int] = None
    uniprot_end: Optional[int] = None
    coverage: Optional[float] = None
    confidence_type: Optional[str] = None
    confidence_avg_local_score: Optional[float] = None
    entities: Optional[List[Entity]] = None

class StructureBlock(BaseModel):
    """Wrapper for a structure summary block in the API response."""
    summary: StructureSummary

class UniprotSummary(BaseModel):
    """
    Represents the response from /api/uniprot/summary/{uniprot_id}.json
    """
    uniprot_entry: UniprotEntry
    structures: List[StructureBlock] = Field(default_factory=list)

    class Config:
        extra = "ignore"


# --- Annotations Endpoint Models ---

class AnnotationResponse(BaseModel):
    """
    Represents the response from /api/annotations/{uniprot_id}.json
    Currently the structure is dynamic/uncertain, so we allow extra fields.
    """
    # Based on limited info, we might expect keys like 'residues' or similar if data existed
    # For now, we use a pass-through model that captures everything

    class Config:
        extra = "allow"

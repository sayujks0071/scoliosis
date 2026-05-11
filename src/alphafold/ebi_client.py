from typing import Any, Dict, List, Optional

import requests

from .models import AnnotationResponse, PredictionEntry, UniprotSummary


class AlphaFoldEbiClient:
    """
    Synchronous REST Client for the AlphaFold EBI Database API.
    Base URL: https://alphafold.ebi.ac.uk
    """

    BASE_URL = "https://alphafold.ebi.ac.uk"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Check for 404
            if e.response.status_code == 404:
                return None
            raise e
        except requests.exceptions.RequestException as e:
            # Re-raise as is or wrap in a custom exception
            raise e

    def get_predictions(self, uniprot_id: str) -> List[PredictionEntry]:
        """
        Fetch predictions for a given UniProt ID.
        Endpoint: GET /api/prediction/{uniprot_id}
        """
        data = self._get(f"/api/prediction/{uniprot_id}")
        if not data:
            return []

        # The API returns a list of prediction objects
        return [PredictionEntry.model_validate(item) for item in data]

    def get_summary(self, uniprot_id: str) -> Optional[UniprotSummary]:
        """
        Fetch the summary for a given UniProt ID.
        Endpoint: GET /api/uniprot/summary/{uniprot_id}.json
        """
        # Note: The API documentation and behavior requires .json suffix for this endpoint
        data = self._get(f"/api/uniprot/summary/{uniprot_id}.json")
        if not data:
            return None

        return UniprotSummary.model_validate(data)

    def get_annotations(self, uniprot_id: str, type_param: str = "MUTAGEN") -> Optional[AnnotationResponse]:
        """
        Fetch annotations for a given UniProt ID.
        Endpoint: GET /api/annotations/{uniprot_id}.json

        Args:
            uniprot_id: The UniProt accession.
            type_param: The type of annotation to fetch (e.g., 'MUTAGEN').
                        The API currently seems to strictly require 'MUTAGEN'.
        """
        params = {"type": type_param}
        data = self._get(f"/api/annotations/{uniprot_id}.json", params=params)

        # If API returns None (404), we return None
        if data is None:
            return None

        # If empty dict is returned (which happens for empty annotations but 200 OK in curl,
        # but apparently 404 in requests), we model validate it.
        # But since requests seems to return 404 for empty annotations for P53,
        # this path might be unreachable if the server returns 404 for no data.
        return AnnotationResponse.model_validate(data)

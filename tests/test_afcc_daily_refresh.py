import os

# Import the module to be tested
# Ensure sys.path is correct for import
import sys
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
import afcc_daily_refresh


def test_get_top_candidates(tmp_path):
    # Create a dummy candidates file
    candidates_file = tmp_path / "candidates_master.csv"
    data = {
        'gene_symbol': ['GENE1', 'GENE2', 'GENE3'],
        'uniprot_id': ['P1', 'P2', 'P3'],
        'priority_score': [10, 30, 20],
        'organism': ['Human', 'Human', 'Human']
    }
    df = pd.DataFrame(data)
    df.to_csv(candidates_file, index=False)

    # Test
    top_df = afcc_daily_refresh.get_top_candidates(n=2, filepath=str(candidates_file))

    assert len(top_df) == 2
    assert top_df.iloc[0]['gene_symbol'] == 'GENE2'  # Highest score
    assert top_df.iloc[1]['gene_symbol'] == 'GENE3'  # Second highest

def test_generate_summary():
    # Create dummy results df
    data = {
        'gene_symbol': ['GENE1', 'GENE2'],
        'anisotropy_index': [5.0, 1.5],
        'plddt_mean': [80.0, 60.0],
        'morphology': ['Fibrous', 'Globular']
    }
    df = pd.DataFrame(data)
    today_str = "2023-01-01"

    summary = afcc_daily_refresh.generate_summary(df, [], today_str)

    assert "AFCC Daily Refresh: 2023-01-01" in summary
    assert "**Top Candidate**: GENE1" in summary
    assert "Tension Rods" in summary
    assert "Fibrous" in summary

@patch('afcc_daily_refresh.requests.get')
def test_fetch_afdb_data(mock_get, tmp_path):
    # Mock API response
    mock_response_api = MagicMock()
    mock_response_api.status_code = 200
    mock_response_api.json.return_value = [{
        'pdbUrl': 'http://example.com/pdb',
        'paeDocUrl': 'http://example.com/pae'
    }]

    # Mock File Download response
    mock_response_file = MagicMock()
    mock_response_file.status_code = 200
    mock_response_file.content = b"fake pdb content"

    mock_get.side_effect = [mock_response_api, mock_response_file, mock_response_file]

    # Override cache dir
    afcc_daily_refresh.CACHE_DIR = str(tmp_path)

    res = afcc_daily_refresh.fetch_afdb_data("P12345")

    assert res is not None
    assert "P12345.pdb" in res['pdb']
    assert "P12345.json" in res['pae']
    assert (tmp_path / "P12345.pdb").exists()
    assert (tmp_path / "P12345.json").exists()

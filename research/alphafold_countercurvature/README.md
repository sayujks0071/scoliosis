# AlphaFold Counter-Curvature (AFCC) Research Module

This module implements a reproducible pipeline to select, fetch, and analyze AlphaFold protein structures
focusing on the "Biological Countercurvature of Spacetime" framework.

## Mission
To identify and analyze structural proteins (HOX, PAX, and others) that exhibit mechanical robustness
features (anisotropy, stiffness proxies) relevant to axial support in gravity environments.

## Directory Structure
- `config/`: Configuration files for targets and scoring.
- `scripts/`: Step-by-step pipeline scripts (00-05).
- `src/afcc/`: Python source code.
- `data/`: Local data storage (raw downloads are gitignored).
- `reports/`: Generated analysis reports.

## Usage

### 1. Setup
Ensure you have activated the repository's virtual environment and installed dependencies:

```bash
source .venv/bin/activate
pip install -r research/alphafold_countercurvature/requirements.txt
```

### 2. Run Pipeline
The pipeline consists of numbered scripts in `scripts/`. Run them sequentially from the **repository root**:

```bash
# 1. Build candidate list
python research/alphafold_countercurvature/scripts/00_build_candidate_list.py

# 2. Map to UniProt
python research/alphafold_countercurvature/scripts/01_map_to_uniprot.py

# 3. Fetch AlphaFold Data
python research/alphafold_countercurvature/scripts/02_fetch_afdb.py

# 4. Parse Structures
python research/alphafold_countercurvature/scripts/03_parse_structures.py

# 5. Analyze Metrics
python research/alphafold_countercurvature/scripts/04_analyze_metrics.py

# 6. Generate Report
python research/alphafold_countercurvature/scripts/05_generate_report.py
```

## Data Sources
- **AlphaFold DB**: https://alphafold.ebi.ac.uk/ (Predictions & PAE)
- **UniProt**: https://www.uniprot.org/ (ID Mapping)

## Citation
Please verify all data usage against AlphaFold DB Terms of Use.

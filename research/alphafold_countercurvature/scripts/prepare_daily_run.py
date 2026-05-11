#!/usr/bin/env python3
"""
prepare_daily_run.py

Prepares the candidates.csv and uniprot_mapping.csv for the top N candidates
from the master candidates list.
"""

import sys
from pathlib import Path

import pandas as pd

# Define paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MASTER_CANDIDATES_PATH = REPO_ROOT / "data" / "candidates_master.csv"
AFCC_DIR = REPO_ROOT / "research" / "alphafold_countercurvature"
PROCESSED_DIR = AFCC_DIR / "data" / "processed"

def main():
    print(f"🚀 Preparing daily run from {MASTER_CANDIDATES_PATH}...")

    # Ensure processed directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Master List
    if not MASTER_CANDIDATES_PATH.exists():
        print(f"❌ Master candidates file not found: {MASTER_CANDIDATES_PATH}")
        sys.exit(1)

    df = pd.read_csv(MASTER_CANDIDATES_PATH)

    # 2. Sort and Pick Top N (Default 10)
    # Ensure priority_score is numeric
    df['priority_score'] = pd.to_numeric(df['priority_score'], errors='coerce').fillna(0)

    # Sort descending
    df_sorted = df.sort_values(by='priority_score', ascending=False)

    top_n = 10
    top_candidates = df_sorted.head(top_n)

    print(f"✅ Selected top {top_n} candidates:")
    print(top_candidates[['gene_symbol', 'priority_score', 'pathway_tags']].to_string(index=False))

    # 3. Create candidates.csv for AFCC pipeline
    # Expected columns by 04_analyze_metrics.py: gene_symbol, source, total_score
    candidates_df = pd.DataFrame()
    candidates_df['gene_symbol'] = top_candidates['gene_symbol']
    # Use the first pathway tag as source or just 'MasterList'
    # 04_analyze_metrics uses 'source' for grouping in reports.
    # Let's use the first tag if available, else 'MasterList'
    candidates_df['source'] = top_candidates['pathway_tags'].apply(
        lambda x: x.split(',')[0].strip() if isinstance(x, str) and x else "MasterList"
    )
    candidates_df['total_score'] = top_candidates['priority_score']

    candidates_out = PROCESSED_DIR / "candidates.csv"
    candidates_df.to_csv(candidates_out, index=False)
    print(f"📄 Wrote {candidates_out}")

    # 4. Create uniprot_mapping.csv for AFCC pipeline
    # Expected columns by 02_fetch_afdb.py: gene_symbol, uniprot_accession
    mapping_df = pd.DataFrame()
    mapping_df['gene_symbol'] = top_candidates['gene_symbol']
    mapping_df['uniprot_accession'] = top_candidates['uniprot_id']

    mapping_out = PROCESSED_DIR / "uniprot_mapping.csv"
    mapping_df.to_csv(mapping_out, index=False)
    print(f"📄 Wrote {mapping_out}")

    print("✨ Preparation complete.")

if __name__ == "__main__":
    main()

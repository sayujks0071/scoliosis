#!/usr/bin/env python3
"""
prepare_thermo_run.py

Prepares a focused run for the 6 thermodynamic cost proteins.
"""

import pandas as pd
from pathlib import Path
import sys

# Define paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MASTER_CANDIDATES_PATH = REPO_ROOT / "data" / "candidates_master.csv"
AFCC_DIR = REPO_ROOT / "research" / "alphafold_countercurvature"
PROCESSED_DIR = AFCC_DIR / "data" / "processed"

TARGET_GENES = ["PPARGC1A", "IGF1R", "GHR", "ARNTL", "DMD", "MYLK"]

def main():
    print(f"🚀 Preparing Thermodynamic Cost Run...")

    # Ensure processed directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Master List
    if not MASTER_CANDIDATES_PATH.exists():
        print(f"❌ Master candidates file not found: {MASTER_CANDIDATES_PATH}")
        sys.exit(1)

    df = pd.read_csv(MASTER_CANDIDATES_PATH)

    # 2. Filter for Target Genes
    target_df = df[df['gene_symbol'].isin(TARGET_GENES)].copy()

    if len(target_df) != len(TARGET_GENES):
        missing = set(TARGET_GENES) - set(target_df['gene_symbol'])
        print(f"⚠️ Warning: The following target genes were not found in master list: {missing}")

    print(f"✅ Found {len(target_df)} target candidates:")
    print(target_df[['gene_symbol', 'uniprot_id']].to_string(index=False))

    # 3. Create candidates.csv for AFCC pipeline
    candidates_df = pd.DataFrame()
    candidates_df['gene_symbol'] = target_df['gene_symbol']
    candidates_df['source'] = "Thermodynamic_Cost"
    candidates_df['total_score'] = 100

    candidates_out = PROCESSED_DIR / "candidates.csv"
    candidates_df.to_csv(candidates_out, index=False)
    print(f"📄 Wrote {candidates_out}")

    # 4. Create uniprot_mapping.csv for AFCC pipeline
    mapping_df = pd.DataFrame()
    mapping_df['gene_symbol'] = target_df['gene_symbol']
    mapping_df['uniprot_accession'] = target_df['uniprot_id']

    mapping_out = PROCESSED_DIR / "uniprot_mapping.csv"
    mapping_df.to_csv(mapping_out, index=False)
    print(f"📄 Wrote {mapping_out}")

    print("✨ Preparation complete.")

if __name__ == "__main__":
    main()

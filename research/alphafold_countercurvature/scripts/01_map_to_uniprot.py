#!/usr/bin/env python3
"""
01_map_to_uniprot.py

Maps candidate gene symbols to UniProt Accessions using the UniProt Async ID Mapping API.
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

# Add repo root to path
repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(repo_root))

from research.alphafold_countercurvature.src.afcc.uniprot import UniProtMapper

if os.environ.get("AFCC_BASE_DIR"):
    BASE_DIR = Path(os.environ["AFCC_BASE_DIR"])
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data" / "processed"
INPUT_FILE = DATA_DIR / "candidates.csv"
OUTPUT_FILE = DATA_DIR / "uniprot_mapping.csv"

def main():
    parser = argparse.ArgumentParser(description="Map gene symbols to UniProt IDs")
    parser.add_argument("--dry-run", action="store_true", help="Skip network calls")
    args = parser.parse_args()

    print("🧬 Mapping Genes to UniProt...")

    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE}")
        print("   Run 00_build_candidate_list.py first.")
        sys.exit(1)

    candidates = pd.read_csv(INPUT_FILE)
    genes = candidates['gene_symbol'].unique().tolist()

    print(f"   Found {len(genes)} unique genes.")

    mapper = UniProtMapper(
        dry_run=args.dry_run,
        cache_path=OUTPUT_FILE
    )

    # Run mapping (human = 9606)
    mapping_df = mapper.map_genes_to_uniprot(genes, organism_id="9606")

    # Merge back to verify coverage
    merged = candidates.merge(mapping_df, on='gene_symbol', how='left')

    missing = merged[merged['uniprot_accession'].isna()]
    if not missing.empty:
        print(f"\n⚠️  {len(missing)} genes failed to map:")
        print(missing['gene_symbol'].tolist())

    success = len(genes) - len(missing)
    print(f"\n✅ Successfully mapped {success}/{len(genes)} genes.")
    print(f"📄 Mapping stored in: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
setup_available_data.py

Selects candidates from the master list that have corresponding PDB files
in the local archive, ensuring we can run the analysis offline.
"""

import os
import sys
from pathlib import Path

import pandas as pd

# Add repo root to path
repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(repo_root))

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CANDIDATES_FILE = PROCESSED_DIR / "candidates.csv"
MASTER_FILE = repo_root / "data" / "candidates_master.csv"
ARCHIVE_DIR = repo_root / "archive"

def main():
    print("🔍 Matching Master Candidates with Archive Data...")

    # 1. Scan Archive
    available_genes = set()
    available_uniprots = set()

    print("   Scanning archive...")
    for root, dirs, files in os.walk(ARCHIVE_DIR):
        for file in files:
            if file.lower().endswith('.pdb'):
                stem = Path(file).stem.upper()
                # Determine if stem is gene or uniprot
                # Simple heuristic: Uniprot is usually 6 chars (alphanumeric), Gene can be anything.
                # But here we treat as both for matching
                available_genes.add(stem)
                available_uniprots.add(stem)

    print(f"   Found {len(available_genes)} unique identifiers in archive.")

    # 2. Load Master List
    if not MASTER_FILE.exists():
        print("❌ Master file missing.")
        sys.exit(1)

    df = pd.read_csv(MASTER_FILE)

    # 3. Filter
    def is_available(row):
        g = str(row['gene_symbol']).upper()
        u = str(row['uniprot_id']).upper()
        return (g in available_genes) or (u in available_uniprots)

    df['available'] = df.apply(is_available, axis=1)

    available_df = df[df['available']].copy()

    # Sort by priority
    available_df['priority_score'] = pd.to_numeric(available_df['priority_score'], errors='coerce').fillna(0)
    available_df = available_df.sort_values(by='priority_score', ascending=False)

    print(f"   Matched {len(available_df)} candidates available in archive.")

    # Take top 20
    top_n = available_df.head(20).copy()

    # Format for pipeline (same as prepare_inputs.py)
    top_n['total_score'] = top_n['priority_score']
    top_n['source'] = top_n['pathway_tags']
    for col in ['D', 'I', 'S', 'E', 'C', 'T', 'R', 'I_iso', 'O', 'E_exp']:
        top_n[col] = 0
    top_n['manual_review_needed'] = False
    top_n['notes'] = top_n['justification']

    cols = ['gene_symbol', 'source', 'total_score',
            'D', 'I', 'S', 'E', 'C', 'T', 'R', 'I_iso', 'O', 'E_exp',
            'manual_review_needed', 'notes']

    final_df = top_n[cols]

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(CANDIDATES_FILE, index=False)

    print(f"✅ Prepared {len(final_df)} available candidates in {CANDIDATES_FILE}")
    print("Top 5:")
    print(final_df[['gene_symbol', 'total_score']].head().to_string(index=False))

if __name__ == "__main__":
    main()

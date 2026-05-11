#!/usr/bin/env python3
"""
prepare_inputs.py

Reads the master candidate list, selects top N candidates, and formats them
for the AlphaFold Counter-Curvature analysis pipeline.
"""

import sys
from pathlib import Path

import pandas as pd

# Add repo root to path to import src if needed
repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(repo_root))

BASE_DIR = Path(__file__).resolve().parent.parent
MASTER_CANDIDATES_PATH = repo_root / "data" / "candidates_master.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "candidates.csv"

# Increased to 50 for clustering analysis
TOP_N = 10

def main():
    print("📋 Preparing Inputs from Master Candidate List...")

    if not MASTER_CANDIDATES_PATH.exists():
        print(f"❌ Master candidate list not found at {MASTER_CANDIDATES_PATH}")
        sys.exit(1)

    df = pd.read_csv(MASTER_CANDIDATES_PATH)

    # Clean and Sort
    # Ensure priority_score is numeric
    df['priority_score'] = pd.to_numeric(df['priority_score'], errors='coerce').fillna(0)

    # Sort by priority_score desc
    df_sorted = df.sort_values(by='priority_score', ascending=False)

    # Take top N
    top_candidates = df_sorted.head(TOP_N).copy()

    print(f"   Selected top {len(top_candidates)} candidates based on priority_score.")

    # Map columns to internal pipeline format
    # pipeline expects: gene_symbol, source, total_score, D, I, S, E, C, T, R, I_iso, O, E_exp
    # We map 'priority_score' -> 'total_score'
    # We map 'pathway_tags' -> 'source'

    # Create required columns with defaults
    top_candidates['total_score'] = top_candidates['priority_score']
    top_candidates['source'] = top_candidates['pathway_tags']

    # Fill missing columns required by downstream scripts (e.g. 06_bolt_report.py might look for these)
    # 00_build_candidate_list.py initializes these to 0
    # 'D': 0, 'I': 0, 'S': 0, 'E': 0, 'C': 0, 'T': 0, 'R': 0, 'I_iso': 0, 'O': 0, 'E_exp': 0

    for col in ['D', 'I', 'S', 'E', 'C', 'T', 'R', 'I_iso', 'O', 'E_exp']:
        top_candidates[col] = 0

    # Also need 'manual_review_needed' and 'notes'
    top_candidates['manual_review_needed'] = False
    top_candidates['notes'] = top_candidates['justification']

    # Select and reorder columns
    cols_to_keep = ['gene_symbol', 'source', 'total_score',
                    'D', 'I', 'S', 'E', 'C', 'T', 'R', 'I_iso', 'O', 'E_exp',
                    'manual_review_needed', 'notes']

    # Ensure all exist
    final_df = top_candidates[cols_to_keep]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(OUTPUT_FILE, index=False)

    print("✅ Input preparation complete.")
    print(f"📄 Saved {len(final_df)} candidates to: {OUTPUT_FILE}")
    print("\nTop 5 Selected:")
    print(final_df[['gene_symbol', 'source', 'total_score']].head().to_string(index=False))

if __name__ == "__main__":
    main()

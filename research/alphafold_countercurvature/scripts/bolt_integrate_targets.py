#!/usr/bin/env python3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
CANDIDATES_FILE = DATA_DIR / "candidates.csv"
BOLT_TARGETS_FILE = DATA_DIR / "bolt_targets.csv"

def main():
    print("⚡ Integrating Bolt Targets into Candidates List...")

    if not BOLT_TARGETS_FILE.exists():
        print(f"❌ {BOLT_TARGETS_FILE} not found.")
        return

    bolt_df = pd.read_csv(BOLT_TARGETS_FILE)
    print(f"   Loaded {len(bolt_df)} targets from bolt_targets.csv")

    candidates_df = pd.DataFrame()
    if CANDIDATES_FILE.exists():
        candidates_df = pd.read_csv(CANDIDATES_FILE)
        print(f"   Loaded {len(candidates_df)} existing candidates.")
    else:
        print("   candidates.csv not found, creating new.")
        candidates_df = pd.DataFrame(columns=['gene_symbol', 'source', 'total_score', 'manual_review_needed',
                                            'D', 'I', 'S', 'E', 'C', 'T', 'R', 'I_iso', 'O', 'E_exp'])

    # Ensure necessary columns exist
    if 'gene_symbol' not in candidates_df.columns:
        candidates_df['gene_symbol'] = []

    existing_genes = set(candidates_df['gene_symbol'])

    new_rows = []

    for _, row in bolt_df.iterrows():
        gene = row['gene_symbol']
        source = row['source']

        if gene in existing_genes:
            # Update existing
            idx = candidates_df.index[candidates_df['gene_symbol'] == gene].tolist()
            if idx:
                candidates_df.at[idx[0], 'total_score'] = 100.0
                print(f"   Updated {gene} score to 100.0")
        else:
            # Add new
            new_row = {
                'gene_symbol': gene,
                'source': source,
                'total_score': 100.0,
                'manual_review_needed': False,
                'D': 0, 'I': 0, 'S': 0, 'E': 0, 'C': 0, 'T': 0, 'R': 0,
                'I_iso': 0, 'O': 0, 'E_exp': 0
            }
            new_rows.append(new_row)
            print(f"   Added new target: {gene}")

    if new_rows:
        new_df = pd.DataFrame(new_rows)
        candidates_df = pd.concat([candidates_df, new_df], ignore_index=True)

    # Save
    candidates_df.to_csv(CANDIDATES_FILE, index=False)
    print(f"✅ Integrated targets. Saved to {CANDIDATES_FILE}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
prepare_custom_run.py

Prepares a custom candidates.csv for the Week 6 Gravity Expansion cycle.
"""

from pathlib import Path

import pandas as pd

# Define paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

def main():
    print("🚀 Preparing Custom Week 6 Run...")

    # Ensure processed directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Week 6 Gravity Expansion III Candidates
    genes = [
        "SELENON", "EMD", "TTN",
        "STOML3", "AQP4", "SSPOP",
        "FAT4", "ROCK1", "DZIP1",
        "MYLK", "PANX3", "FBLN5",
        "GDF5", "CNNM2", "BNC2"
    ]

    # Create DataFrame
    candidates_df = pd.DataFrame({
        'gene_symbol': genes,
        'source': ["Week6_Gravity_Expansion"] * len(genes),
        'total_score': [95] * len(genes)  # High priority for focused analysis
    })

    candidates_out = PROCESSED_DIR / "candidates.csv"
    candidates_df.to_csv(candidates_out, index=False)

    print(f"✅ Generated candidates.csv with {len(candidates_df)} entries.")
    print(f"📄 Wrote {candidates_out}")
    print(candidates_df.to_string(index=False))

if __name__ == "__main__":
    main()

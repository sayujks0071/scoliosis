#!/usr/bin/env python3
"""
bolt_setup_candidates.py

Sets up the focused target list for the Bolt-BioFold analysis cycle.
Creates a run-specific target file 'bolt_targets.csv' to avoid overwriting the master candidates list.
"""

from pathlib import Path

import pandas as pd

# Define paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

def main():
    print("⚡ Bolt-BioFold: Setting up Focused Target List...")

    # Ensure processed directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Default Seed List
    genes = [
        "LBX1",    # Scoliosis Driver
        "PTK7",    # Wnt / PCP
        "POC5",    # Centriolar / Scoliosis
        "ADGRG6",  # GPR126 / Scoliosis
        "PIEZO2",  # Mechanosensor
        "MESP2",   # Segmentation
        "HES7",    # Segmentation Clock
        "COL11A2"  # ECM
    ]

    # Create DataFrame for the focused list
    # Minimal schema needed for filtering
    targets_df = pd.DataFrame({
        'gene_symbol': genes,
        'source': ["Default_Seed_List"] * len(genes)
    })

    # Save to a separate file
    targets_out = PROCESSED_DIR / "bolt_targets.csv"
    targets_df.to_csv(targets_out, index=False)

    print(f"✅ Generated bolt_targets.csv with {len(targets_df)} entries.")
    print(f"📄 Wrote {targets_out}")
    print(targets_df.to_string(index=False))

    # Verification: Check if these are in the master candidates list
    candidates_file = PROCESSED_DIR / "candidates.csv"
    if candidates_file.exists():
        master_df = pd.read_csv(candidates_file)
        if 'gene_symbol' in master_df.columns:
            master_genes = set(master_df['gene_symbol'])
            missing = [g for g in genes if g not in master_genes]
            if missing:
                print("⚠️ Warning: The following targets are NOT in the master candidates.csv and might be skipped by the pipeline:")
                print(missing)
                print("   (You may need to add them to the master list manually or via 00_build_candidate_list.py)")
            else:
                print("✅ All targets are present in the master candidates.csv")

if __name__ == "__main__":
    main()

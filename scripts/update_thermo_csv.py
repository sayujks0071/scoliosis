#!/usr/bin/env python3
"""
update_thermo_csv.py

Updates the thermodynamic cost proteins CSV with fresh metrics from the AFCC pipeline.
"""

import pandas as pd
from pathlib import Path

# Define paths
REPO_ROOT = Path(__file__).resolve().parent.parent
METRICS_FILE = REPO_ROOT / "research" / "alphafold_countercurvature" / "data" / "processed" / "protein_metrics.csv"
OUTPUT_FILE = REPO_ROOT / "outputs" / "thermodynamic_cost" / "thermodynamic_cost_proteins.csv"

def main():
    print("🔄 Updating Thermodynamic Cost CSV...")

    if not METRICS_FILE.exists():
        print(f"❌ Metrics file not found: {METRICS_FILE}")
        return

    if not OUTPUT_FILE.exists():
        print(f"❌ Output file not found: {OUTPUT_FILE}")
        return

    # Load data
    metrics_df = pd.read_csv(METRICS_FILE)
    thermo_df = pd.read_csv(OUTPUT_FILE)

    # Set index to gene for easier updating
    thermo_df.set_index('gene', inplace=True)
    metrics_df.set_index('gene_symbol', inplace=True)

    # Columns to update
    # Map metrics_df columns to thermo_df columns
    col_map = {
        'anisotropy_index': 'anisotropy',
        'morphology': 'morphology',
        'radius_of_gyration': 'rg',
        'plddt_mean': 'plddt_mean',
        'n_residues': 'n_residues',
        'hinge_candidates': 'hinge_candidates',
        'disorder_fraction_proxy': 'disorder_fraction',
        'PAE_domain_blockiness_score': 'PAE_blockiness'
    }

    updated_count = 0
    for gene in metrics_df.index:
        if gene in thermo_df.index:
            print(f"   Updating {gene}...")
            for m_col, t_col in col_map.items():
                if m_col in metrics_df.columns:
                    thermo_df.at[gene, t_col] = metrics_df.at[gene, m_col]
            updated_count += 1
        else:
            print(f"⚠️  {gene} not found in target CSV (skipping add, only updating existing).")

    # Reset index
    thermo_df.reset_index(inplace=True)

    # Save
    thermo_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Updated {updated_count} proteins in {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

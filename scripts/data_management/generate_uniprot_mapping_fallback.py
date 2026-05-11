from pathlib import Path

import pandas as pd

# Paths
MASTER_FILE = Path("data/candidates_master.csv")
OUTPUT_FILE = Path("research/alphafold_countercurvature/data/processed/uniprot_mapping.csv")

def main():
    print(f"Reading from {MASTER_FILE}...")
    df = pd.read_csv(MASTER_FILE)

    # Select relevant columns
    # candidates_master.csv has 'gene_symbol' and 'uniprot_id'
    mapping_df = df[['gene_symbol', 'uniprot_id']].copy()
    mapping_df.rename(columns={'uniprot_id': 'uniprot_accession'}, inplace=True)

    # Remove duplicates
    mapping_df.drop_duplicates(inplace=True)

    # Write to file
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    mapping_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Generated {OUTPUT_FILE} with {len(mapping_df)} entries.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
03_parse_structures.py

Parses downloaded PDB/PAE files to ensure they are valid and extract basic properties.
This step is largely implicit in the next metrics step, but useful for validation.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(repo_root))

from research.alphafold_countercurvature.src.afcc.structure import StructureParser

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MANIFEST_FILE = DATA_DIR / "manifest.csv"

def main():
    print("🧬 Verifying and Parsing Structures...")

    if not MANIFEST_FILE.exists():
        print(f"❌ Manifest not found: {MANIFEST_FILE}")
        sys.exit(1)

    manifest = pd.read_csv(MANIFEST_FILE)
    downloaded = manifest[manifest['status'].isin(['downloaded', 'cached'])]

    if downloaded.empty:
        print("⚠️ No downloaded structures found.")
        sys.exit(0)

    parser = StructureParser()
    valid_count = 0

    for idx, row in downloaded.iterrows():
        pdb_path = Path(row['pdb_path'])
        gene = row['gene_symbol']

        # Check PDB
        structure = parser.parse_pdb(pdb_path, gene)
        if structure:
            # Check pLDDT extraction
            plddt = parser.extract_plddt(structure)
            mean_plddt = np.mean(plddt) if len(plddt) > 0 else 0

            # Check PAE
            has_pae = False
            if pd.notna(row['pae_path']):
                pae = parser.parse_pae(Path(row['pae_path']))
                has_pae = (pae is not None)

            print(f"   ✅ {gene}: {len(plddt)} residues, Mean pLDDT={mean_plddt:.1f}, PAE={has_pae}")
            valid_count += 1
        else:
            print(f"   ❌ {gene}: Failed to parse PDB")

    print(f"\nVerified {valid_count}/{len(downloaded)} structures.")

if __name__ == "__main__":
    main()

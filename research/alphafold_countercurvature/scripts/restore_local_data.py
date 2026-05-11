#!/usr/bin/env python3
"""
restore_local_data.py

Restores PDB files from the local archive for the selected candidates,
bypassing external AlphaFold DB fetching.
"""

import datetime
import hashlib
import os
import shutil
import sys
from pathlib import Path

import pandas as pd

# Add repo root to path
repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(repo_root))

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CANDIDATES_FILE = DATA_DIR / "processed" / "candidates.csv"
MASTER_FILE = repo_root / "data" / "candidates_master.csv"
RAW_DIR = DATA_DIR / "raw" / "afdb"
MANIFEST_FILE = DATA_DIR / "manifest.csv"
ARCHIVE_DIR = repo_root / "archive"

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    print("📦 Restoring Local AlphaFold Data from Archive...")

    if not CANDIDATES_FILE.exists():
        print(f"❌ Candidates file not found: {CANDIDATES_FILE}")
        sys.exit(1)

    # 1. Load Candidates and Master List to get UniProt IDs
    candidates = pd.read_csv(CANDIDATES_FILE)
    master = pd.read_csv(MASTER_FILE)

    # Merge to attach UniProt ID
    # Master has 'uniprot_id', candidates has 'gene_symbol'
    merged = candidates.merge(master[['gene_symbol', 'uniprot_id']], on='gene_symbol', how='left')

    # Index archive files
    print("   Scanning archive for PDB files...")
    archive_map = {} # gene_upper -> path
    for root, dirs, files in os.walk(ARCHIVE_DIR):
        for file in files:
            if file.lower().endswith('.pdb'):
                # key by filename stem (gene symbol usually)
                stem = Path(file).stem.upper()
                # Handle cases like AF-Q92508-F1-model_v4.pdb?
                # The archive files seen earlier were like 'PIEZO1.pdb', 'Q92834.pdb' (uniprot?), 'HOXA5.pdb'
                # So we map both gene and uniprot if possible.
                path = Path(root) / file
                archive_map[stem] = path

    print(f"   Found {len(archive_map)} PDB files in archive.")

    manifest_rows = []
    restored_count = 0

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for _, row in merged.iterrows():
        gene = row['gene_symbol']
        uid = row['uniprot_id'] # This corresponds to Uniprot Accession

        if pd.isna(uid):
            print(f"⚠️  No UniProt ID for {gene}")
            continue

        # Try to find file in archive
        # Try Gene Symbol
        found_path = archive_map.get(gene.upper())
        # Try UniProt
        if not found_path:
            found_path = archive_map.get(uid.upper())

        # If not found, try to look for AF filename patterns if key was Uniprot
        # But our archive seems to use Gene Symbols mainly.

        status = 'not_found_archive'
        final_pdb_path = ""
        sha = ""

        if found_path:
            # Prepare destination
            dest_dir = RAW_DIR / uid
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / f"{uid}.pdb"

            try:
                shutil.copy2(found_path, dest_file)
                status = 'downloaded' # Mimic fetcher status
                final_pdb_path = str(dest_file.relative_to(repo_root))
                # Make relative to repo root because that's what manifest usually has?
                # Let's check manifest.csv format from memory.
                # "research/alphafold_countercurvature/data/raw/afdb/..."
                # Yes, relative to repo root is fine, or absolute.
                # scripts/04 uses Path(row['pdb_path']).
                # If script runs from anywhere, absolute is safer, but repo-relative is cleaner.
                # Let's use repo-relative string.
                final_pdb_path = str(dest_file) # Use absolute path to be safe with the scripts

                sha = calculate_sha256(dest_file)
                restored_count += 1
                print(f"   ✅ Restored {gene} ({uid})")
            except Exception as e:
                print(f"   ❌ Failed to copy {gene}: {e}")
                status = 'failed_copy'
        else:
            print(f"   ⚠️  Could not find PDB for {gene} ({uid}) in archive")

        manifest_rows.append({
            'uniprot': uid,
            'gene_symbol': gene,
            'status': status,
            'pdb_path': final_pdb_path,
            'pae_path': '', # No PAE in archive
            'sha256_pdb': sha,
            'retrieved_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'notes': 'Restored from local archive'
        })

    # Save Manifest
    manifest_df = pd.DataFrame(manifest_rows)
    manifest_df.to_csv(MANIFEST_FILE, index=False)
    print(f"📄 Generated manifest with {len(manifest_df)} entries at {MANIFEST_FILE}")
    print(f"✅ Restored {restored_count}/{len(merged)} files.")

if __name__ == "__main__":
    main()

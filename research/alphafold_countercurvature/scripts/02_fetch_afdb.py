#!/usr/bin/env python3
"""
02_fetch_afdb.py

Downloads structure data (PDB, PAE) from AlphaFold DB for mapped UniProt IDs.
"""

import argparse
import os
import sys
import time
from pathlib import Path

import pandas as pd

repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(repo_root))

from research.alphafold_countercurvature.src.afcc.afdb import AlphaFoldFetcher

if os.environ.get("AFCC_BASE_DIR"):
    BASE_DIR = Path(os.environ["AFCC_BASE_DIR"])
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
INPUT_MAPPING = DATA_DIR / "processed" / "uniprot_mapping.csv"
MANIFEST_FILE = DATA_DIR / "manifest.csv"

def main():
    parser = argparse.ArgumentParser(description="Fetch AlphaFold Structures")
    parser.add_argument("--dry-run", choices=['none', 'metadata', 'full'], default='none',
                        help="Dry run mode: 'none' (real download), 'metadata' (check API only), 'full' (skip all network)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of proteins to fetch")
    args = parser.parse_args()

    # Support boolean flag --dry-run for backward compatibility/CLI habit (defaults to 'full' or 'metadata'?)
    # Actually argparse 'choices' handles the values. If user just wants "dry run", they might type just the flag if it was store_true.
    # But let's stick to explicit modes.

    print(f"🧬 Fetching AlphaFold Data (Mode: {args.dry_run})...")

    if not INPUT_MAPPING.exists():
        print(f"❌ Mapping file not found: {INPUT_MAPPING}")
        sys.exit(1)

    mapping = pd.read_csv(INPUT_MAPPING)

    # Filter for successfully mapped genes
    to_fetch = mapping[mapping['uniprot_accession'].notna()]

    if args.limit:
        to_fetch = to_fetch.head(args.limit)

    print(f"   Targets: {len(to_fetch)} proteins")

    fetcher = AlphaFoldFetcher(
        data_dir=DATA_DIR / "raw",
        manifest_path=MANIFEST_FILE,
        dry_run=args.dry_run
    )

    results = {'downloaded': 0, 'failed': 0, 'skipped': 0, 'not_found': 0}

    for idx, row in to_fetch.iterrows():
        gene = row['gene_symbol']
        uid = row['uniprot_accession']

        print(f"[{idx+1}/{len(to_fetch)}] Processing {gene}...")

        res = fetcher.fetch_protein(uid, gene)
        status = res.get('status', 'unknown')

        if status in ['downloaded', 'cached']:
             results['downloaded'] += 1
        elif status == 'not_found':
             results['not_found'] += 1
        elif status == 'skipped':
             results['skipped'] += 1
        else:
             results['failed'] += 1

        # Rate limit
        if args.dry_run == 'none' and status not in ['cached', 'skipped']:
             time.sleep(0.5)

    print("\n📊 Summary")
    print(f"   ✅ Downloaded/Cached: {results['downloaded']}")
    print(f"   ❌ Not Found: {results['not_found']}")
    print(f"   ⚠️  Failed: {results['failed']}")
    if results['skipped']:
        print(f"   ⏭️  Skipped: {results['skipped']}")

if __name__ == "__main__":
    main()

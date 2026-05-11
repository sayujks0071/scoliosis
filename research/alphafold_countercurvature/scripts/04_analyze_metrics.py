#!/usr/bin/env python3
"""
04_analyze_metrics.py

Computes geometric and confidence metrics for all downloaded structures.
"""

import json
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

# Suppress Bio.PDB warnings
warnings.filterwarnings("ignore")

repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(repo_root))

from research.alphafold_countercurvature.src.afcc.metrics import MetricsAnalyzer
from research.alphafold_countercurvature.src.afcc.structure import StructureParser


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super(NumpyEncoder, self).default(obj)

if os.environ.get("AFCC_BASE_DIR"):
    BASE_DIR = Path(os.environ["AFCC_BASE_DIR"])
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
MANIFEST_FILE = DATA_DIR / "manifest.csv"
OUTPUT_FILE = DATA_DIR / "processed" / "protein_metrics.csv"
CANDIDATES_FILE = DATA_DIR / "processed" / "candidates.csv"

def main():
    print("📏 Analyzing Structural Metrics...")

    force_refresh = "--force" in sys.argv
    if force_refresh:
        print("   ⚠️ Force refresh enabled: Ignoring cache.")

    if not MANIFEST_FILE.exists():
        print("❌ Manifest not found.")
        sys.exit(1)

    manifest = pd.read_csv(MANIFEST_FILE)
    downloaded = manifest[manifest['status'].isin(['downloaded', 'cached'])]

    # Load candidate info to get Source tags
    # ⚡ Bolt Optimization: Pre-index candidates for O(1) lookup
    candidates_dict = {}
    if CANDIDATES_FILE.exists():
        try:
            cand_df = pd.read_csv(CANDIDATES_FILE)
            if 'gene_symbol' in cand_df.columns:
                # Deduplicate keeping first to match legacy behavior
                cand_df = cand_df.drop_duplicates(subset=['gene_symbol'], keep='first')
                candidates_dict = cand_df.set_index('gene_symbol')[['source', 'total_score']].to_dict('index')
                print(f"   Loaded {len(candidates_dict)} candidates for fast lookup.")
        except Exception as e:
            print(f"⚠️ Error loading candidates file: {e}")

    # ⚡ Bolt Optimization: Incremental Processing & Fast IO
    # Check for existing results to avoid re-processing
    processed_keys = set()
    existing_df = None
    append_mode = False
    file_cols = []

    if OUTPUT_FILE.exists():
        try:
            # First read only headers to check schema stability
            headers = pd.read_csv(OUTPUT_FILE, nrows=0).columns.tolist()

            # Check for legacy columns needing migration
            needs_migration = False
            if 'anisotropy' in headers and 'anisotropy_index' not in headers: needs_migration = True
            if 'mean_plddt' in headers and 'plddt_mean' not in headers: needs_migration = True

            if not needs_migration:
                # ⚡ Bolt Optimization: Fast Read (Keys Only)
                # Avoids parsing thousands of float columns for existing records
                keys_df = pd.read_csv(OUTPUT_FILE, usecols=['gene_symbol', 'uniprot'])
                processed_keys = set(zip(keys_df['gene_symbol'], keys_df['uniprot']))
                file_cols = headers
                append_mode = True
                print(f"   Found {len(processed_keys)} existing records (Fast IO)")
            else:
                # Fallback to full read for migration
                existing_df = pd.read_csv(OUTPUT_FILE)
                rename_map = {}
                if 'anisotropy' in existing_df.columns and 'anisotropy_index' not in existing_df.columns:
                     rename_map['anisotropy'] = 'anisotropy_index'
                if 'mean_plddt' in existing_df.columns and 'plddt_mean' not in existing_df.columns:
                     rename_map['mean_plddt'] = 'plddt_mean'

                if rename_map:
                    print(f"   Migrating columns in existing file: {list(rename_map.keys())} -> {list(rename_map.values())}")
                    existing_df.rename(columns=rename_map, inplace=True)

                if 'gene_symbol' in existing_df.columns and 'uniprot' in existing_df.columns:
                    processed_keys = set(zip(existing_df['gene_symbol'], existing_df['uniprot']))
                print(f"   Found {len(processed_keys)} existing records (Full Read)")

        except Exception as e:
            print(f"⚠️ Error reading existing metrics: {e}. Starting fresh.")

    # Filter work list
    to_process = []
    for _, row in downloaded.iterrows():
        if (row['gene_symbol'], row['uniprot']) not in processed_keys:
            to_process.append(row)

    print(f"   Processing {len(to_process)} new structures (skipped {len(downloaded) - len(to_process)})...")

    results = []
    parser = StructureParser()
    analyzer = MetricsAnalyzer()

    for idx, row in enumerate(to_process):
        pdb_path = Path(row['pdb_path'])
        gene = row['gene_symbol']
        uid = row['uniprot']

        # ⚡ Bolt Optimization: Persistent JSON Cache for Metrics
        # Checks for {pdb_path}.metrics.json to avoid re-parsing and re-calculating geometry.
        # This persists even if protein_metrics.csv is deleted.
        metrics_cache_path = pdb_path.with_suffix('.metrics.json')
        metrics = None

        # Check freshness
        is_fresh = False
        if metrics_cache_path.exists() and not force_refresh:
            try:
                m_time = metrics_cache_path.stat().st_mtime
                pdb_time = pdb_path.stat().st_mtime

                pae_fresh = True
                pae_path_str = row.get('pae_path')
                if pae_path_str and isinstance(pae_path_str, str):
                    p_pae = Path(pae_path_str)
                    if p_pae.exists() and p_pae.stat().st_mtime > m_time:
                        pae_fresh = False

                if m_time >= pdb_time and pae_fresh:
                    with open(metrics_cache_path, 'r') as f:
                        metrics = json.load(f)
                    is_fresh = True
            except Exception:
                pass # Corrupt cache or error reading

        if not is_fresh:
            # Compute fresh metrics
            # ⚡ Bolt Optimization: Use fast parser (skips Bio.PDB Structure build)
            # This reduces parse time from ~1.2s to ~0.05s for large structures.
            coords, plddt, resnames = parser.fast_parse_pdb_arrays(pdb_path)

            if coords is None:
                # Fallback (or just skip if file missing/empty)
                print(f"⚠️ Failed to fast-parse {pdb_path}, trying legacy...")
                structure = parser.parse_pdb(pdb_path, gene)
                if not structure:
                    continue
                coords, plddt, resnames = parser.extract_coords_and_plddt(structure)
            else:
                structure = None

            # Load PAE if available
            pae_path = row.get('pae_path')
            pae_matrix = None
            if pae_path and isinstance(pae_path, str):
                 p = Path(pae_path)
                 if p.exists():
                     pae_matrix = parser.parse_pae(p)

            metrics = analyzer.analyze_structure(structure, plddt, coords=coords, resnames=resnames, pae_matrix=pae_matrix)

            # Save cache
            try:
                with open(metrics_cache_path, 'w') as f:
                    json.dump(metrics, f, cls=NumpyEncoder)
            except Exception as e:
                print(f"⚠️ Warning: Could not save metrics cache {metrics_cache_path}: {e}")

        # Merge basic info (Always merge, as it's not in the cached structural metrics)
        metrics['gene_symbol'] = gene
        metrics['uniprot'] = uid

        # Merge source info
        # ⚡ Bolt Optimization: O(1) Dictionary Lookup
        if gene in candidates_dict:
            info = candidates_dict[gene]
            metrics['source_category'] = info['source']
            metrics['dise_score'] = info['total_score']

        results.append(metrics)

        if (idx + 1) % 5 == 0:
            print(f"   ... {idx + 1} done")

    new_df = pd.DataFrame(results)

    # Handle Schema Evolution (New columns in results)
    if append_mode and not new_df.empty:
        new_cols = [c for c in new_df.columns if c not in file_cols]
        if new_cols:
            print(f"   ⚠️ New columns detected {new_cols}. Switching to full rewrite.")
            try:
                existing_df = pd.read_csv(OUTPUT_FILE)
                append_mode = False
            except Exception as e:
                print(f"   Error reading file for rewrite: {e}")

    # Save logic
    if append_mode and not new_df.empty:
        # ⚡ Bolt Optimization: Append Mode
        # Ensure correct column order matching file
        for c in file_cols:
            if c not in new_df.columns:
                new_df[c] = np.nan

        df_to_write = new_df[file_cols]
        df_to_write.to_csv(OUTPUT_FILE, mode='a', header=False, index=False)
        print(f"\n✅ Appended metrics for {len(new_df)} proteins to {OUTPUT_FILE}")

        # Preview (New Batch)
        print("\nPreview (New Batch - Top High Anisotropy):")
        if 'anisotropy_index' in new_df.columns:
             plddt_col = 'plddt_mean' if 'plddt_mean' in new_df.columns else 'mean_plddt'
             cols_to_show = ['gene_symbol', 'morphology', 'anisotropy_index']
             if plddt_col in new_df.columns:
                 cols_to_show.append(plddt_col)
             print(new_df.sort_values('anisotropy_index', ascending=False)[cols_to_show].head().to_string(index=False))

    else:
        # Full Rewrite Logic (Legacy/Fallback)
        if existing_df is not None and not new_df.empty:
            df = pd.concat([existing_df, new_df], ignore_index=True)
        elif not new_df.empty:
            df = new_df
        elif existing_df is not None:
            df = existing_df
        else:
            df = pd.DataFrame()

        if not df.empty:
            # Reorder columns
            cols_preferred = ['gene_symbol', 'uniprot', 'source_category', 'morphology',
                    'anisotropy_index', 'radius_of_gyration', 'plddt_mean', 'n_residues', 'dise_score']

            # Filter only columns that exist
            cols = [c for c in cols_preferred if c in df.columns]

            # Add remaining cols
            remaining = [c for c in df.columns if c not in cols]
            df = df[cols + remaining]

            OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(OUTPUT_FILE, index=False)

            print(f"\n✅ Metrics calculated for {len(df)} proteins.")
            print(f"📄 Saved to: {OUTPUT_FILE}")

            # Preview
            print("\nTop 5 High Anisotropy (All):")
            if 'anisotropy_index' in df.columns:
                 # Check which plddt column exists (legacy vs new)
                 plddt_col = 'plddt_mean' if 'plddt_mean' in df.columns else 'mean_plddt'
                 cols_to_show = ['gene_symbol', 'morphology', 'anisotropy_index']
                 if plddt_col in df.columns:
                     cols_to_show.append(plddt_col)

                 print(df.sort_values('anisotropy_index', ascending=False)[cols_to_show].head().to_string(index=False))
        else:
            if not append_mode: # Only print if we expected to write but didn't
                print("\n⚠️ No metrics to save.")

if __name__ == "__main__":
    main()

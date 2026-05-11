#!/usr/bin/env python3
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

# Add the source directory to sys.path to import metrics
# Assuming script is run from repo root or scripts/ dir
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
SRC_DIR = os.path.join(REPO_ROOT, 'research', 'alphafold_countercurvature', 'src')

if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

try:
    from afcc.metrics import MetricsAnalyzer
    from afcc.structure import StructureParser
except ImportError as e:
    print(f"Error importing afcc modules: {e}")
    # Fallback for testing if run from wrong dir
    try:
        sys.path.append(os.path.abspath('research/alphafold_countercurvature/src'))
        from afcc.metrics import MetricsAnalyzer
        from afcc.structure import StructureParser
    except ImportError:
        pass

# Configuration
CACHE_DIR = os.path.join(REPO_ROOT, "data", "afdb_cache")
OUTPUT_BASE = os.path.join(REPO_ROOT, "outputs", "afcc")
CANDIDATES_FILE = os.path.join(REPO_ROOT, "data", "candidates_master.csv")
REPORT_FILE = os.path.join(REPO_ROOT, "reports", "afcc_latest.md")

def ensure_dirs():
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(OUTPUT_BASE, exist_ok=True)

def fetch_afdb_data(uniprot_id: str) -> Optional[Dict[str, str]]:
    """Fetches PDB and PAE JSON for a given UniProt ID using the API."""
    api_url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"

    pdb_path = os.path.join(CACHE_DIR, f"{uniprot_id}.pdb")
    pae_path = os.path.join(CACHE_DIR, f"{uniprot_id}.json")

    # Check if files already exist
    if os.path.exists(pdb_path) and os.path.exists(pae_path):
        return {"pdb": pdb_path, "pae": pae_path}

    print(f"Querying API for {uniprot_id}...")
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code != 200:
             print(f"API Error for {uniprot_id}: {response.status_code}")
             return None
        data = response.json()
        if not data or not isinstance(data, list):
             print(f"Invalid API response for {uniprot_id}")
             return None

        # Take the first entry (usually the main one)
        entry = data[0]
        pdb_url = entry.get('pdbUrl')
        pae_url = entry.get('paeDocUrl')

        if not pdb_url:
             print(f"No PDB URL found for {uniprot_id}")
             return None

        # Download PDB
        print(f"Downloading PDB from {pdb_url}...")
        pdb_resp = requests.get(pdb_url, timeout=30)
        if pdb_resp.status_code == 200:
             with open(pdb_path, 'wb') as f:
                 f.write(pdb_resp.content)
        else:
             print(f"Failed to download PDB: {pdb_resp.status_code}")
             return None

        # Download PAE
        if pae_url:
            print(f"Downloading PAE from {pae_url}...")
            pae_resp = requests.get(pae_url, timeout=30)
            if pae_resp.status_code == 200:
                with open(pae_path, 'wb') as f:
                    f.write(pae_resp.content)
            else:
                print(f"Failed to download PAE: {pae_resp.status_code}")
                # Optional, proceed without PAE? The analysis seems to handle None PAE.

        return {"pdb": pdb_path, "pae": pae_path if os.path.exists(pae_path) else None}

    except Exception as e:
        print(f"Exception fetching data for {uniprot_id}: {e}")
        return None

def get_top_candidates(n: int = 10, filepath: str = CANDIDATES_FILE) -> pd.DataFrame:
    if not os.path.exists(filepath):
        print(f"Candidates file not found: {filepath}")
        # Return empty DataFrame with expected columns for safety
        return pd.DataFrame(columns=['gene_symbol', 'uniprot_id', 'organism', 'priority_score'])

    df = pd.read_csv(filepath)

    # If using custom file (like daily snapshot), it might not have priority_score or be pre-sorted
    # If priority_score exists, use it. Otherwise assume file order is intentional.
    if 'priority_score' in df.columns:
        df['priority_score'] = pd.to_numeric(df['priority_score'], errors='coerce').fillna(0)
        df_sorted = df.sort_values(by='priority_score', ascending=False)
        return df_sorted.head(n)
    else:
        # Assume file is already sorted or just take top N
        return df.head(n)

def generate_summary(results_df: pd.DataFrame, failures: List[str], today_str: str) -> str:
    if results_df.empty:
        return f"# AFCC Daily Refresh: {today_str}\n\nNo results generated.\n"

    top_aniso = results_df.sort_values(by='anisotropy_index', ascending=False).head(1).iloc[0]
    top_aniso_gene = top_aniso['gene_symbol']
    top_aniso_val = top_aniso['anisotropy_index']

    summary_md = f"# AFCC Daily Refresh: {today_str}\n\n"
    summary_md += "## Run Summary\n"
    summary_md += f"- **Candidates Processed**: {len(results_df)}\n"
    summary_md += f"- **Top Candidate**: {top_aniso_gene} (Anisotropy: {top_aniso_val:.2f})\n"

    if failures:
            summary_md += f"- **Failures**: {len(failures)}\n"

    summary_md += "\n## Top 5 High-Anisotropy Structures\n"
    summary_md += "| Gene | Anisotropy | pLDDT (Mean) | Morphology |\n"
    summary_md += "|------|------------|--------------|------------|\n"

    top5 = results_df.sort_values(by='anisotropy_index', ascending=False).head(5)
    for _, r in top5.iterrows():
        summary_md += f"| {r['gene_symbol']} | {r['anisotropy_index']:.2f} | {r['plddt_mean']:.1f} | {r['morphology']} |\n"

    summary_md += "\n## Key Observations\n"
    # Generate some insights
    fibrous_count = len(results_df[results_df['anisotropy_index'] > 4.0])
    low_conf_count = len(results_df[results_df['plddt_mean'] < 70])

    summary_md += f"- **Tension Rods**: Found {fibrous_count} candidates with Anisotropy > 4.0, suggesting fibrous/extended load-bearing structures.\n"
    summary_md += f"- **Structural Confidence**: {low_conf_count} candidates have low confidence (pLDDT < 70), indicating disorder or flexibility.\n"
    summary_md += f"- **Top Mover**: {top_aniso_gene} remains the most anisotropic structure in this batch.\n"

    return summary_md

def main():
    parser = argparse.ArgumentParser(description="AFCC Daily Refresh")
    parser.add_argument("--top-n", type=int, default=10, help="Number of top candidates to process")
    parser.add_argument("--candidates-file", type=str, default=CANDIDATES_FILE, help="Path to candidates CSV file")
    args = parser.parse_args()

    ensure_dirs()

    today_str = datetime.now().strftime("%Y-%m-%d")
    daily_output_dir = os.path.join(OUTPUT_BASE, today_str)
    os.makedirs(daily_output_dir, exist_ok=True)

    failure_file = os.path.join(daily_output_dir, "failure.md")
    metrics_file = os.path.join(daily_output_dir, "metrics.csv")
    summary_file = os.path.join(daily_output_dir, "summary.md")

    candidates = get_top_candidates(args.top_n, args.candidates_file)
    print(f"Processing top {len(candidates)} candidates for {today_str} from {args.candidates_file}...")

    struct_parser = StructureParser()
    analyzer = MetricsAnalyzer()

    results = []
    failures = []

    for _, row in candidates.iterrows():
        symbol = row['gene_symbol']
        uniprot = row['uniprot_id']

        print(f"Processing {symbol} ({uniprot})...")

        paths = fetch_afdb_data(uniprot)
        if not paths:
            failures.append(f"- **{symbol}** ({uniprot}): Data fetch failed.")
            continue

        pdb_path = Path(paths['pdb'])
        pae_path = Path(paths['pae']) if paths['pae'] else None

        coords, plddt, resnames = struct_parser.fast_parse_pdb_arrays(pdb_path)
        if coords is None:
             failures.append(f"- **{symbol}** ({uniprot}): PDB parsing failed.")
             continue

        pae_matrix = struct_parser.parse_pae(pae_path)

        metrics = analyzer.analyze_structure(
            coords=coords,
            plddt_scores=plddt,
            resnames=resnames,
            pae_matrix=pae_matrix
        )

        # Add metadata
        metrics['gene_symbol'] = symbol
        metrics['uniprot_id'] = uniprot
        metrics['organism'] = row.get('organism', 'Unknown')
        metrics['priority_score'] = row['priority_score']

        results.append(metrics)

    # Save metrics
    if results:
        results_df = pd.DataFrame(results)
        # Reorder columns to put identity first
        cols = ['gene_symbol', 'uniprot_id', 'priority_score', 'anisotropy_index', 'radius_of_gyration', 'plddt_mean', 'morphology'] + [c for c in results_df.columns if c not in ['gene_symbol', 'uniprot_id', 'priority_score', 'anisotropy_index', 'radius_of_gyration', 'plddt_mean', 'morphology']]
        results_df = results_df[cols]
        results_df.to_csv(metrics_file, index=False)
        print(f"Saved metrics to {metrics_file}")

        # Generate Daily Summary
        summary_md = generate_summary(results_df, failures, today_str)

        with open(summary_file, 'w') as f:
            f.write(summary_md)
        print(f"Saved summary to {summary_file}")

        # Update Rolling Dashboard
        with open(REPORT_FILE, 'a') as f:
            f.write(f"\n{summary_md}")
        print(f"Updated dashboard {REPORT_FILE}")

    else:
        print("No results generated.")

    if failures:
        with open(failure_file, 'w') as f:
            f.write("# Failures\n\n")
            for fail in failures:
                f.write(f"{fail}\n")
        print(f"Saved failures to {failure_file}")

if __name__ == "__main__":
    main()

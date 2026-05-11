#!/usr/bin/env python3
"""
afcc_daily_refresh.py

Orchestrates the daily refresh of AlphaFold Counter-Curvature metrics.
1. Selects top N candidates from master list.
2. Updates input files for the pipeline.
3. Runs fetch and analysis scripts.
4. Generates daily outputs and updates dashboard.
"""

import argparse
import datetime
import subprocess
import sys
from pathlib import Path

import pandas as pd

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AFCC_DIR = REPO_ROOT / "research" / "alphafold_countercurvature"
AFCC_SCRIPTS = AFCC_DIR / "scripts"
DATA_PROCESSED = AFCC_DIR / "data" / "processed"
CANDIDATES_MASTER = REPO_ROOT / "data" / "candidates_master.csv"
OUTPUTS_DIR = REPO_ROOT / "outputs" / "afcc"
REPORTS_FILE = REPO_ROOT / "reports" / "afcc_latest.md"

def setup_directories():
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

def load_candidates():
    print(f"📋 Loading candidates from {CANDIDATES_MASTER}...")
    if not CANDIDATES_MASTER.exists():
        print(f"❌ Candidate master file not found: {CANDIDATES_MASTER}")
        sys.exit(1)

    df = pd.read_csv(CANDIDATES_MASTER)

    # Ensure numeric priority_score
    df['priority_score'] = pd.to_numeric(df['priority_score'], errors='coerce').fillna(0)

    # Sort
    df_sorted = df.sort_values('priority_score', ascending=False)
    print(f"   Loaded {len(df_sorted)} candidates.")
    return df_sorted

def prepare_inputs(df, n=10):
    print(f"⚙️  Preparing input files in {DATA_PROCESSED}...")

    # Filter top N for fetching
    top_n_df = df.head(n)
    print(f"   Selected top {len(top_n_df)} candidates for fetching (Score range: {top_n_df['priority_score'].min()}-{top_n_df['priority_score'].max()})")

    # 1. uniprot_mapping.csv (gene_symbol, uniprot_accession)
    # Map 'uniprot_id' from master to 'uniprot_accession'
    mapping_df = top_n_df[['gene_symbol', 'uniprot_id']].copy()
    mapping_df.rename(columns={'uniprot_id': 'uniprot_accession'}, inplace=True)
    mapping_path = DATA_PROCESSED / "uniprot_mapping.csv"
    mapping_df.to_csv(mapping_path, index=False)
    print(f"   -> Wrote {mapping_path.name} (Top {n})")

    # 2. candidates.csv (gene_symbol, source, total_score, justification)
    # Write full list to prevent data loss
    cand_df = df.copy()
    cand_df['source'] = cand_df['pathway_tags']
    cand_df['total_score'] = cand_df['priority_score']
    # Select columns
    cols = ['gene_symbol', 'source', 'total_score', 'justification']
    # Add missing columns if any
    for col in cols:
        if col not in cand_df.columns:
            cand_df[col] = ""

    cand_path = DATA_PROCESSED / "candidates.csv"
    cand_df[cols].to_csv(cand_path, index=False)
    print(f"   -> Wrote {cand_path.name}")

    # Remove existing metrics to force refresh
    metrics_file = DATA_PROCESSED / "protein_metrics.csv"
    if metrics_file.exists():
        metrics_file.unlink()
        print(f"   -> Removed existing {metrics_file.name} to force refresh")

def run_pipeline():
    # 1. Fetch
    script_fetch = AFCC_SCRIPTS / "02_fetch_afdb.py"
    print(f"\n🚀 Running fetch script: {script_fetch.name}...")
    try:
        subprocess.check_call([sys.executable, str(script_fetch)])
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Fetch script warning: {e}")
        # We continue, as some might have failed but others succeeded

    # 2. Analyze
    script_analyze = AFCC_SCRIPTS / "04_analyze_metrics.py"
    print(f"\n🚀 Running analysis script: {script_analyze.name}...")
    try:
        subprocess.check_call([sys.executable, str(script_analyze)])
    except subprocess.CalledProcessError as e:
        print(f"❌ Analysis script failed: {e}")
        sys.exit(1)

def generate_outputs():
    today = datetime.date.today().isoformat()
    daily_dir = OUTPUTS_DIR / today
    daily_dir.mkdir(parents=True, exist_ok=True)

    metrics_source = DATA_PROCESSED / "protein_metrics.csv"
    if not metrics_source.exists():
        print("❌ Metrics file not found. Analysis may have failed.")
        # Create failure note
        with open(daily_dir / "failure.md", "w") as f:
            f.write(f"# Failure Report {today}\n\nMetrics file was not generated.")
        return None

    df = pd.read_csv(metrics_source)

    # Save daily metrics
    metrics_dest = daily_dir / "metrics.csv"
    df.to_csv(metrics_dest, index=False)
    print(f"\n💾 Saved daily metrics to {metrics_dest}")

    # Generate Summary
    summary_path = daily_dir / "summary.md"

    # Top 5 Anisotropy
    if 'anisotropy_index' in df.columns:
        top_aniso = df.sort_values('anisotropy_index', ascending=False).head(5)
    else:
        top_aniso = df.head(5) # Fallback

    lines = []
    lines.append(f"# AFCC Daily Refresh: {today}")
    lines.append("")
    lines.append("## Run Summary")
    lines.append(f"- **Candidates Processed**: {len(df)}")
    if not top_aniso.empty and 'anisotropy_index' in top_aniso.columns:
        lines.append(f"- **Top Candidate**: {top_aniso.iloc[0]['gene_symbol']} (Anisotropy: {top_aniso.iloc[0]['anisotropy_index']:.2f})")

    lines.append("")
    lines.append("## Top 5 High-Anisotropy Structures")
    lines.append("| Gene | Anisotropy | pLDDT (Mean) | Morphology |")
    lines.append("|------|------------|--------------|------------|")
    for _, row in top_aniso.iterrows():
        aniso = row.get('anisotropy_index', 0)
        plddt = row.get('plddt_mean', row.get('mean_plddt', 0))
        lines.append(f"| {row['gene_symbol']} | {aniso:.2f} | {plddt:.1f} | {row.get('morphology', 'N/A')} |")

    lines.append("")
    lines.append("## Key Observations")

    if 'anisotropy_index' in df.columns:
        high_aniso_count = len(df[df['anisotropy_index'] > 4.0])
        if high_aniso_count > 0:
            lines.append(f"- **Tension Rods**: Found {high_aniso_count} candidates with Anisotropy > 4.0, suggesting fibrous/extended load-bearing structures.")
        else:
            lines.append("- **Tension Rods**: No candidates with Anisotropy > 4.0 found.")

        plddt_col = 'plddt_mean' if 'plddt_mean' in df.columns else 'mean_plddt'
        if plddt_col in df.columns:
            low_conf_count = len(df[df[plddt_col] < 70])
            if low_conf_count > 0:
                lines.append(f"- **Structural Confidence**: {low_conf_count} candidates have low confidence (pLDDT < 70), indicating disorder or flexibility.")

        if not top_aniso.empty:
            lines.append(f"- **Top Mover**: {top_aniso.iloc[0]['gene_symbol']} remains the most anisotropic structure in this batch.")

    with open(summary_path, "w") as f:
        f.write("\n".join(lines))
    print(f"📄 Generated summary at {summary_path}")

    return summary_path, lines

def update_dashboard(summary_lines):
    if not REPORTS_FILE.exists():
        print(f"⚠️  Reports file {REPORTS_FILE} not found. Creating new.")
        REPORTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(REPORTS_FILE, "w") as f:
            f.write("# AFCC Dashboard\n\n")

    with open(REPORTS_FILE, "a") as f:
        f.write("\n\n" + "\n".join(summary_lines))
    print(f"📈 Updated dashboard at {REPORTS_FILE}")

def main():
    parser = argparse.ArgumentParser(description="AFCC Daily Refresh")
    parser.add_argument("--top-n", "-n", type=int, default=10, help="Number of top candidates to process")
    args = parser.parse_args()

    setup_directories()

    candidates = load_candidates()
    prepare_inputs(candidates, args.top_n)

    run_pipeline()

    res = generate_outputs()
    if res:
        summary_path, summary_lines = res
        update_dashboard(summary_lines)

if __name__ == "__main__":
    main()

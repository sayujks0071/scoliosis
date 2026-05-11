#!/usr/bin/env python3
"""
run_afcc_daily.py

Orchestrates the daily AlphaFold Counter-Curvature pipeline cycle.
1. Selects Top N candidates from master list.
2. Refreshes data (Uniprot mapping, PDB fetching).
3. Computes metrics (forcing re-computation for Top N).
4. Generates summary report.
5. Archives outputs to versioned directory.
"""

import datetime
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
AFCC_DIR = REPO_ROOT / "research" / "alphafold_countercurvature"
DATA_DIR = AFCC_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"

MASTER_CANDIDATES = REPO_ROOT / "data" / "candidates_master.csv"
PROCESSED_CANDIDATES = PROCESSED_DIR / "candidates.csv"
BOLT_TARGETS = PROCESSED_DIR / "bolt_targets.csv"
METRICS_FILE = PROCESSED_DIR / "protein_metrics.csv"
REPORT_SOURCE = PROCESSED_DIR / "bolt_biofold_results.md"

OUTPUTS_DIR = REPO_ROOT / "outputs" / "afcc"
DASHBOARD_FILE = REPO_ROOT / "reports" / "afcc_latest.md"

def run_step(script_name, description, output_dir):
    print(f"\n🚀 Running {script_name}: {description}...")
    script_path = SCRIPT_DIR / script_name
    try:
        result = subprocess.run([sys.executable, str(script_path)], check=True)
        print(f"✅ {script_name} completed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ {script_name} failed with exit code {e.returncode}.")

        # Write failure.md
        output_dir.mkdir(parents=True, exist_ok=True)
        failure_file = output_dir / "failure.md"
        with open(failure_file, "w") as f:
            f.write("# Failure Report\n\n")
            f.write(f"**Step Failed:** {script_name}\n")
            f.write(f"**Description:** {description}\n")
            f.write(f"**Exit Code:** {e.returncode}\n")
            f.write(f"**Timestamp:** {datetime.datetime.now().isoformat()}\n")

        print(f"📝 Failure note written to {failure_file}")
        sys.exit(e.returncode)

def main():
    today = datetime.date.today().strftime("%Y-%m-%d")
    daily_output_dir = OUTPUTS_DIR / today
    print(f"=== AFCC Daily Run: {today} ===")

    # 1. Select Top Candidates
    print("\n🔍 Selecting Top 10 Candidates...")
    if not MASTER_CANDIDATES.exists():
        print(f"❌ Master candidates file not found: {MASTER_CANDIDATES}")
        sys.exit(1)

    df = pd.read_csv(MASTER_CANDIDATES)
    # Sort by priority_score descending
    df_sorted = df.sort_values('priority_score', ascending=False)
    top_n = df_sorted.head(10).copy()

    # Ensure 'source' column exists for pipeline compatibility (using 'source' tag)
    # The pipeline scripts seem to use 'source' column in candidates.csv
    # candidates_master.csv doesn't have 'source', but usually 'bolt_setup_candidates.py' adds it.
    # We will add it manually.
    top_n['source'] = 'Top_Priority_Run'

    # We also need 'total_score' which maps to 'priority_score'
    if 'total_score' not in top_n.columns and 'priority_score' in top_n.columns:
        top_n['total_score'] = top_n['priority_score']

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Instead of destructive overwriting, we update the existing candidates.csv
    # or append to it if it doesn't exist.
    if PROCESSED_CANDIDATES.exists():
        existing_df = pd.read_csv(PROCESSED_CANDIDATES)
        # Ensure 'gene_symbol' exists in the original file
        if 'gene_symbol' in existing_df.columns:
            # We filter out the existing rows that match the top_n 'gene_symbol'
            # to replace them with the updated master candidate data
            existing_df = existing_df[~existing_df['gene_symbol'].isin(top_n['gene_symbol'])]
            updated_df = pd.concat([existing_df, top_n], ignore_index=True)
            updated_df.to_csv(PROCESSED_CANDIDATES, index=False)
            print(f"📄 Appended/Updated top 10 in {PROCESSED_CANDIDATES}")
        else:
            # Recreate with master columns if the existing schema is corrupted/wrong
            top_n.to_csv(PROCESSED_CANDIDATES, index=False)
            print(f"📄 Overwrote invalid {PROCESSED_CANDIDATES}")
    else:
        # Create a new candidates.csv if it does not exist
        top_n.to_csv(PROCESSED_CANDIDATES, index=False)
        print(f"📄 Wrote top 10 to {PROCESSED_CANDIDATES}")

    # Write to processed/bolt_targets.csv (used by 06 to filter report)
    # 06_bolt_report.py expects 'gene_symbol'
    top_n[['gene_symbol', 'source']].to_csv(BOLT_TARGETS, index=False)
    print(f"📄 Wrote targets to {BOLT_TARGETS}")

    print("   Targets:", ", ".join(top_n['gene_symbol'].tolist()))

    target_genes = top_n['gene_symbol'].tolist()

    # 2. Map to Uniprot
    run_step("01_map_to_uniprot.py", "Map Gene Symbols to UniProt IDs", daily_output_dir)

    # 3. Fetch Structures
    # 02_fetch_afdb.py
    run_step("02_fetch_afdb.py", "Fetch PDBs from AlphaFold DB", daily_output_dir)

    # Check for API fetch failures in the manifest
    manifest_file = DATA_DIR / "manifest.csv"
    if manifest_file.exists():
        manifest_df = pd.read_csv(manifest_file)
        failed_targets = manifest_df[(manifest_df['gene_symbol'].isin(target_genes)) & (manifest_df['status'] != 'downloaded') & (manifest_df['status'] != 'cached')]
        if not failed_targets.empty:
            print(f"⚠️ Detected API failures or missing structures for {len(failed_targets)} targets.")
            daily_output_dir.mkdir(parents=True, exist_ok=True)
            failure_file = daily_output_dir / "failure.md"
            with open(failure_file, "w") as f:
                f.write("# Failure Report\n\n")
                f.write("**Step Failed:** AlphaFold DB API Fetch\n")
                f.write("**Description:** Failed to download structures for the following candidates.\n")
                for _, row in failed_targets.iterrows():
                    f.write(f"- {row['gene_symbol']}: {row['status']}\n")
                f.write(f"\n**Timestamp:** {datetime.datetime.now().isoformat()}\n")
            print(f"📝 Failure note written to {failure_file}")

            # Remove failed targets from the target list for subsequent steps
            target_genes = [g for g in target_genes if g not in failed_targets['gene_symbol'].tolist()]

    # 4. Force Recompute Metrics
    print("\n🧹 Preparing Metrics Table (Forcing Refresh for Targets)...")

    if METRICS_FILE.exists():
        metrics_df = pd.read_csv(METRICS_FILE)
        initial_len = len(metrics_df)
        # Remove rows where gene_symbol is in our target list
        metrics_df = metrics_df[~metrics_df['gene_symbol'].isin(target_genes)]
        removed_count = initial_len - len(metrics_df)
        metrics_df.to_csv(METRICS_FILE, index=False)
        print(f"   Removed {removed_count} existing entries for targets to force re-computation.")
    else:
        print("   No existing metrics file found. proceeding.")

    # 5. Analyze Metrics
    run_step("04_analyze_metrics.py", "Compute Structural Metrics", daily_output_dir)

    # 6. Generate Report
    run_step("06_bolt_report.py", "Generate Summary Report", daily_output_dir)

    # 7. Archive Outputs
    daily_output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📦 Archiving outputs to {daily_output_dir}...")

    # Copy Summary
    if REPORT_SOURCE.exists():
        shutil.copy(REPORT_SOURCE, daily_output_dir / "summary.md")
        print("   Saved summary.md")
    else:
        print(f"⚠️ Report not found at {REPORT_SOURCE}")

    # Save Metrics subset
    if METRICS_FILE.exists():
        all_metrics = pd.read_csv(METRICS_FILE)
        # Filter for our targets
        target_metrics = all_metrics[all_metrics['gene_symbol'].isin(target_genes)]
        target_metrics.to_csv(daily_output_dir / "metrics.csv", index=False)
        print("   Saved metrics.csv")
    else:
        print("⚠️ Metrics file not found.")

    # 8. Update Dashboard
    print(f"\n📊 Updating Dashboard at {DASHBOARD_FILE}...")

    # Read summary for insights (simple extraction)
    # We'll just take the "Interpretation" section or make a simple bullet list

    dashboard_entry = f"\n## AFCC Daily Refresh: {today}\n\n"
    dashboard_entry += "## Run Summary\n"

    num_processed = len(target_metrics) if (METRICS_FILE.exists() and not target_metrics.empty) else len(target_genes)
    dashboard_entry += f"- **Candidates Processed**: {num_processed}\n"

    top_aniso_gene = "N/A"
    top_aniso_val = 0.0
    if METRICS_FILE.exists() and not target_metrics.empty and 'anisotropy_index' in target_metrics.columns:
        top_aniso = target_metrics.sort_values('anisotropy_index', ascending=False).iloc[0]
        top_aniso_gene = top_aniso['gene_symbol']
        top_aniso_val = top_aniso['anisotropy_index']
    dashboard_entry += f"- **Top Candidate**: {top_aniso_gene} (Anisotropy: {top_aniso_val:.2f})\n\n"

    dashboard_entry += "## Top 5 High-Anisotropy Structures\n"
    dashboard_entry += "| Gene | Anisotropy | pLDDT (Mean) | Morphology |\n"
    dashboard_entry += "|------|------------|--------------|------------|\n"

    if METRICS_FILE.exists() and not target_metrics.empty and 'anisotropy_index' in target_metrics.columns:
        top_5 = target_metrics.sort_values('anisotropy_index', ascending=False).head(5)
        for _, row in top_5.iterrows():
            gene = row['gene_symbol']
            aniso = row['anisotropy_index']
            plddt_col = 'plddt_mean' if 'plddt_mean' in row else 'mean_plddt'
            plddt = row.get(plddt_col, float('nan'))
            morphology = row.get('morphology', 'Unknown')
            dashboard_entry += f"| {gene} | {aniso:.2f} | {plddt:.1f} | {morphology} |\n"

    dashboard_entry += "\n## Key Observations\n"
    if METRICS_FILE.exists() and not target_metrics.empty:
        high_aniso_count = (target_metrics['anisotropy_index'] > 4.0).sum() if 'anisotropy_index' in target_metrics.columns else 0
        plddt_col = 'plddt_mean' if 'plddt_mean' in target_metrics.columns else 'mean_plddt'
        low_conf_count = (target_metrics[plddt_col] < 70).sum() if plddt_col in target_metrics.columns else 0

        dashboard_entry += f"- **Tension Rods**: Found {high_aniso_count} candidates with Anisotropy > 4.0, suggesting fibrous/extended load-bearing structures.\n"
        dashboard_entry += f"- **Structural Confidence**: {low_conf_count} candidates have low confidence (pLDDT < 70), indicating disorder or flexibility.\n"
        dashboard_entry += f"- **Top Mover**: {top_aniso_gene} remains the most anisotropic structure in this batch.\n"
    else:
        dashboard_entry += "- Metrics data not available to extract insights.\n"

    with open(DASHBOARD_FILE, "a") as f:
        f.write(dashboard_entry)

    print("✅ Dashboard updated.")
    print("\n🎉 AFCC Daily Run Complete!")

if __name__ == "__main__":
    main()

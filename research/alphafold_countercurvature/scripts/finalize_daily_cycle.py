import datetime
import shutil
import sys
from pathlib import Path

import pandas as pd

# Define paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
AFCC_DIR = REPO_ROOT / "research" / "alphafold_countercurvature"
PROCESSED_DIR = AFCC_DIR / "data" / "processed"
DATA_DIR = AFCC_DIR / "data"
OUTPUTS_DIR = AFCC_DIR / "outputs" / "afcc"
REPORTS_DIR = REPO_ROOT / "reports"

CANDIDATES_FILE = PROCESSED_DIR / "candidates.csv"
METRICS_FILE = PROCESSED_DIR / "protein_metrics.csv"
REPORT_FILE = PROCESSED_DIR / "bolt_biofold_results.md"
MANIFEST_FILE = DATA_DIR / "manifest.csv"
DASHBOARD_FILE = REPORTS_DIR / "afcc_latest.md"

def main():
    today = datetime.date.today().strftime("%Y-%m-%d")
    print(f"🔄 Finalizing Daily Cycle for {today}...")

    day_output_dir = OUTPUTS_DIR / today
    day_output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Archive Metrics for Current Candidates
    if not CANDIDATES_FILE.exists() or not METRICS_FILE.exists():
        print("❌ Missing input files (candidates.csv or protein_metrics.csv)")
        sys.exit(1)

    cand_df = pd.read_csv(CANDIDATES_FILE)
    metrics_df = pd.read_csv(METRICS_FILE)

    # Filter metrics for candidates
    # Using 'gene_symbol' as key
    target_genes = set(cand_df['gene_symbol'])
    filtered_metrics = metrics_df[metrics_df['gene_symbol'].isin(target_genes)]

    metrics_out = day_output_dir / "metrics.csv"
    filtered_metrics.to_csv(metrics_out, index=False)
    print(f"📦 Archived metrics to {metrics_out}")

    # 2. Archive Report
    if REPORT_FILE.exists():
        shutil.copy(REPORT_FILE, day_output_dir / "summary.md")
        print(f"📦 Archived report to {day_output_dir / 'summary.md'}")
    else:
        print("⚠️ Report file not found.")

    # 3. Check Failures
    failures = []
    if MANIFEST_FILE.exists():
        manifest = pd.read_csv(MANIFEST_FILE)
        # Check status for target genes
        for gene in target_genes:
            row = manifest[manifest['gene_symbol'] == gene]
            if not row.empty:
                status = row.iloc[0]['status']
                if status not in ['downloaded', 'cached']:
                    failures.append(f"- **{gene}**: {status}")
            else:
                 failures.append(f"- **{gene}**: Not in manifest")

    if failures:
        failure_path = day_output_dir / "failure.md"
        with open(failure_path, 'w') as f:
            f.write(f"# Failures for {today}\n\n")
            for fail in failures:
                f.write(fail + "\n")
        print(f"⚠️  Failures recorded in {failure_path}")

    # 4. Update Dashboard
    print(f"📝 Updating dashboard {DASHBOARD_FILE}...")

    # Calculate stats
    n_processed = len(target_genes)
    n_downloaded = len(target_genes) - len(failures)

    # Top Anisotropy
    top_aniso_str = "N/A"
    if not filtered_metrics.empty:
         aniso_col = 'anisotropy_index' if 'anisotropy_index' in filtered_metrics.columns else 'anisotropy'
         if aniso_col in filtered_metrics.columns:
             # Sort descending
             sorted_m = filtered_metrics.sort_values(by=aniso_col, ascending=False)
             top = sorted_m.iloc[0]
             top_aniso_str = f"**{top['gene_symbol']}** ({top[aniso_col]:.2f})"

    # Clusters (Simplistic logic or from metrics if available)
    # Just list high anisotropy ones
    high_aniso = []
    if not filtered_metrics.empty and aniso_col in filtered_metrics.columns:
        high_aniso = filtered_metrics[filtered_metrics[aniso_col] > 4.0]['gene_symbol'].tolist()

    summary_block = f"""
## {today}: Daily Refresh (Top {n_processed} Candidates)

**Summary:**
- **Processed:** {n_processed} candidates selected.
- **Downloaded:** {n_downloaded}/{n_processed} ({len(failures)} missing/failed).
- **Analysis:** Metrics computed for {len(filtered_metrics)} structures.

**Key Findings:**
- **Top Anisotropy:** {top_aniso_str}
- **High Anisotropy (>4.0):** {', '.join(high_aniso) if high_aniso else 'None'}

**Outputs:**
- [Metrics CSV](research/alphafold_countercurvature/outputs/afcc/{today}/metrics.csv)
- [Summary Report](research/alphafold_countercurvature/outputs/afcc/{today}/summary.md)
"""
    if failures:
        summary_block += f"- [Failure Log](research/alphafold_countercurvature/outputs/afcc/{today}/failure.md)\n"

    with open(DASHBOARD_FILE, 'a') as f:
        f.write("\n" + summary_block)

    print("✅ Cycle Finalized Successfully.")

if __name__ == "__main__":
    main()

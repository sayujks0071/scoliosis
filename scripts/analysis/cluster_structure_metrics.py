#!/usr/bin/env python3
"""
Cluster Structure Metrics
=========================

Clusters proteins based on structural metrics (Anisotropy, PAE Blockiness)
from the AFCC pipeline.

Usage:
    python scripts/cluster_structure_metrics.py [metrics_csv]

Clusters:
    0: Tension Rods (High Anisotropy > 3.5, Low Blockiness < 4.0)
    1: Blocky Scaffolds (High Blockiness > 5.0)
    2: Globular/Mixed (Everything else)
"""

import sys
from pathlib import Path

import pandas as pd

# Default path to latest metrics
DEFAULT_METRICS_PATH = Path("outputs/afcc/current_metrics.csv")
OUTPUT_DIR = Path("reports/structure_clusters")
OUTPUT_FILE = OUTPUT_DIR / "latest_clusters.md"

def cluster_proteins(csv_path):
    print(f"Loading metrics from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: File not found at {csv_path}")
        sys.exit(1)

    # Column mapping for flexibility
    col_map = {
        "Identity": "gene_symbol",
        "Anisotropy": "anisotropy_index",
        "PAE_blockiness": "PAE_domain_blockiness_score"
    }
    df.rename(columns=col_map, inplace=True)

    # Parse Identity if needed (e.g. "PIEZO2 (Q9H5I5)" -> "PIEZO2")
    if "gene_symbol" in df.columns and df["gene_symbol"].astype(str).str.contains(r"\(").any():
        df["gene_symbol"] = df["gene_symbol"].astype(str).apply(lambda x: x.split(" (")[0] if " (" in x else x)

    # Ensure required columns exist
    required_cols = ["gene_symbol", "anisotropy_index", "PAE_domain_blockiness_score"]
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: Missing column '{col}' in CSV. Available: {list(df.columns)}")
            sys.exit(1)

    # Cluster Logic
    def assign_cluster(row):
        aniso = row["anisotropy_index"]
        block = row["PAE_domain_blockiness_score"]

        # Handle missing values if any (though standard pandas float handles NaN)
        if pd.isna(aniso) or pd.isna(block):
            return "2: Globular/Mixed (Incomplete Data)"

        if aniso > 3.5 and block < 4.0:
            return "0: Tension Rods"
        elif block > 5.0:
            return "1: Blocky Scaffolds"
        else:
            return "2: Globular/Mixed"

    df["Cluster"] = df.apply(assign_cluster, axis=1)

    # Generate Report
    report_lines = []
    report_lines.append("# Structure Clusters Analysis\n")
    report_lines.append(f"**Source Data**: `{csv_path}`\n")

    # Summary Table
    report_lines.append("## Cluster Summary\n")
    summary = df["Cluster"].value_counts().sort_index()
    for cluster, count in summary.items():
        report_lines.append(f"- **{cluster}**: {count} proteins")

    report_lines.append("\n## Detailed Assignments\n")
    report_lines.append("| Gene | Cluster | Anisotropy | Blockiness | Source |")
    report_lines.append("|---|---|---|---|---|")

    # Sort by Cluster then Anisotropy (desc)
    df_sorted = df.sort_values(by=["Cluster", "anisotropy_index"], ascending=[True, False])

    for _, row in df_sorted.iterrows():
        source = row.get("source_category", "Unknown")
        line = f"| **{row['gene_symbol']}** | {row['Cluster']} | {row['anisotropy_index']:.2f} | {row['PAE_domain_blockiness_score']:.2f} | {source} |"
        report_lines.append(line)
        print(line) # Print to stdout as well

    # Write to file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(report_lines))

    print(f"\nAnalysis complete. Report saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_METRICS_PATH
    cluster_proteins(csv_path)

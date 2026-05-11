import datetime
import os

import pandas as pd

# Paths
REPO_ROOT = os.getcwd()
BASE_DIR = os.path.join(REPO_ROOT, "research/alphafold_countercurvature")
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
METRICS_FILE = os.path.join(PROCESSED_DIR, "protein_metrics.csv")
OUTPUT_BASE = os.path.join(REPO_ROOT, "outputs/afcc")
REPORTS_DIR = os.path.join(REPO_ROOT, "reports")

# Date for versioning
today = datetime.datetime.now().strftime("%Y-%m-%d")
OUTPUT_DIR = os.path.join(OUTPUT_BASE, today)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True) # Ensure reports dir exists

# 1. Copy metrics
dest_metrics = os.path.join(OUTPUT_DIR, "metrics.csv")
df = pd.read_csv(METRICS_FILE)
df.to_csv(dest_metrics, index=False)
print(f"Copied metrics to {dest_metrics}")

# 2. Generate summary.md
summary_path = os.path.join(OUTPUT_DIR, "summary.md")
n_structures = len(df)
avg_anisotropy = df['anisotropy'].mean()
avg_plddt = df['mean_plddt'].mean()
top_ani = df.sort_values(by="anisotropy", ascending=False).iloc[0]

# Count morphologies
morph_counts = df['morphology'].value_counts()
morph_table = "| Morphology | Count |\n|---|---|\n"
for morph, count in morph_counts.items():
    morph_table += f"| {morph} | {count} |\n"

# High Anisotropy Table
high_ani = df[df['anisotropy'] > 2.0][['gene_symbol', 'anisotropy', 'morphology', 'source_category']]
ani_table = "| gene_symbol | anisotropy | morphology | source_category |\n|---|---|---|---|\n"
for _, row in high_ani.iterrows():
    ani_table += f"| {row['gene_symbol']} | {row['anisotropy']:.2f} | {row['morphology']} | {row['source_category']} |\n"

summary_content = f"""# AFCC Analysis Summary: {today}

## Overview
- **Structures Analyzed:** {n_structures}
- **Mean Anisotropy:** {avg_anisotropy:.2f}
- **Mean pLDDT:** {avg_plddt:.2f}

## Top Anisotropy Candidate
- **Gene:** {top_ani['gene_symbol']}
- **Score:** {top_ani['anisotropy']:.2f}
- **Morphology:** {top_ani['morphology']}
- **Source:** {top_ani['source_category']}

## Morphology Distribution
{morph_table}

## Key Candidates (Anisotropy > 2.0)
{ani_table}
"""

with open(summary_path, "w") as f:
    f.write(summary_content)

print(f"Generated {summary_path}")

# 3. Update dashboard (reports/afcc_latest.md)
dashboard_path = os.path.join(REPORTS_DIR, "afcc_latest.md")
dashboard_entry = f"""
## {today} Refresh
- Analyzed {n_structures} top candidates.
- Highest anisotropy: **{top_ani['gene_symbol']}** ({top_ani['anisotropy']:.2f}).
- Metrics saved to `outputs/afcc/{today}/metrics.csv`.
"""

# Append or create
if os.path.exists(dashboard_path):
    with open(dashboard_path, "a") as f:
        f.write(dashboard_entry)
else:
    with open(dashboard_path, "w") as f:
        f.write(f"# AFCC Rolling Dashboard\n{dashboard_entry}")

print(f"Updated {dashboard_path}")

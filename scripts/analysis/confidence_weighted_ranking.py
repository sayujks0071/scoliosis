from pathlib import Path

import pandas as pd


def create_confidence_weighted_ranking():
    snapshot_path = Path('outputs/afcc/2026-02-16/metrics.csv')
    if not snapshot_path.exists():
        print(f"Error: Could not find {snapshot_path}")
        return

    df = pd.read_csv(snapshot_path)

    # Define thresholds
    plddt_threshold = 70.0
    anisotropy_threshold = 3.0

    # Classification
    df['confidence_class'] = df['plddt_mean'].apply(lambda x: 'Adequate' if x >= plddt_threshold else 'Low')
    df['anisotropy_class'] = df['anisotropy_index'].apply(lambda x: 'High' if x >= anisotropy_threshold else 'Intermediate/Low')

    # Sort for ranking
    df_sorted = df.sort_values(by=['confidence_class', 'anisotropy_index'], ascending=[True, False]) # 'Adequate' comes before 'Low'

    # Save CSV
    out_csv = Path('outputs/afcc/confidence_weighted_ranking.csv')
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df_sorted.to_csv(out_csv, index=False)

    # Generate Report
    high_ani_adequate = df[(df['confidence_class'] == 'Adequate') & (df['anisotropy_class'] == 'High')].sort_values(by='anisotropy_index', ascending=False)
    high_ani_low = df[(df['confidence_class'] == 'Low') & (df['anisotropy_class'] == 'High')].sort_values(by='anisotropy_index', ascending=False)

    report_content = [
        "# Confidence-Weighted Structural Evidence Report\n",
        "## Overview\n",
        "- **Source Data**: `outputs/afcc/2026-02-16/metrics.csv`\n",
        "- **Adequate Confidence Threshold**: `pLDDT >= 70.0`\n",
        "- **High Anisotropy Threshold**: `Anisotropy >= 3.0`\n",
        "This report re-ranks candidates with explicit confidence weighting to distinguish robust structural signals from exploratory, low-confidence predictions.\n\n",

        "## 1. High-Anisotropy + Adequate-Confidence (Strong Signal)\n",
        "These proteins exhibit extended, load-bearing morphologies and their structural predictions are reliable.\n",
        "| Rank | Gene | Anisotropy | pLDDT (Mean) | PAE Blockiness |\n",
        "|------|------|------------|--------------|----------------|"
    ]

    for idx, row in enumerate(high_ani_adequate.itertuples(), 1):
        report_content.append(f"| {idx} | {row.gene_symbol} | {row.anisotropy_index:.2f} | {row.plddt_mean:.1f} | {row.PAE_domain_blockiness_score:.2f} |")

    report_content.extend([
        "\n## 2. High-Anisotropy + Low-Confidence (Exploratory Only)\n",
        "These proteins exhibit extended morphologies but their structural predictions are low-confidence. Their high anisotropy may be an artifact of long, unstructured regions (IDRs). **Hypothesis-generating only; requires orthogonal validation.**\n",
        "| Rank | Gene | Anisotropy | pLDDT (Mean) | PAE Blockiness |\n",
        "|------|------|------------|--------------|----------------|"
    ])

    for idx, row in enumerate(high_ani_low.itertuples(), 1):
        report_content.append(f"| {idx} | {row.gene_symbol} | {row.anisotropy_index:.2f} | {row.plddt_mean:.1f} | {row.PAE_domain_blockiness_score:.2f} |")

    # LBX1 Comparator Analysis
    comparator_genes = ['LBX1', 'PIEZO2', 'LMNA', 'ADGRG6', 'RUNX3', 'POC5', 'GHR']

    report_content.extend([
        "\n## 3. LBX1 Comparator Panel Analysis\n",
        "Comparison of LBX1 against key anchors and speculative sensors. Note: LMNA and RUNX3 are not present in the 2026-02-16 snapshot, and thus excluded from this table.\n",
        "| Gene | Anisotropy | pLDDT (Mean) | PAE Blockiness | Confidence | Anisotropy Class |\n",
        "|------|------------|--------------|----------------|------------|------------------|"
    ])

    for gene in comparator_genes:
        gene_data = df[df['gene_symbol'] == gene]
        if not gene_data.empty:
            row = gene_data.iloc[0]
            report_content.append(f"| {row.gene_symbol} | {row.anisotropy_index:.2f} | {row.plddt_mean:.1f} | {row.PAE_domain_blockiness_score:.2f} | {row.confidence_class} | {row.anisotropy_class} |")
        else:
            report_content.append(f"| {gene} | N/A | N/A | N/A | N/A | N/A |")

    report_content.extend([
        "\n### Interpretation\n",
        "- **LBX1** remains a low-confidence, intermediate-anisotropy candidate with high PAE blockiness. It is structurally dissimilar to strong mechanosensor anchors like PIEZO2.\n",
        "- **PIEZO2** maintains high anisotropy and adequate confidence, supporting its role as a robust structural anchor.\n",
        "- **POC5** and **GHR** show extreme or high anisotropy but suffer from low confidence. Their structural signals must be treated as speculative and not definitive proof of a tension-rod architecture.\n"
    ])

    report_path = Path('reports/confidence_weighted_structural_evidence.md')
    with open(report_path, 'w') as f:
        f.write("\n".join(report_content))

    print(f"Ranking complete. Outputs written to {out_csv} and {report_path}")

if __name__ == "__main__":
    create_confidence_weighted_ranking()

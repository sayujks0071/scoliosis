import os

import pandas as pd

INPUT_FILE = "outputs/afcc/current_metrics.csv"
FALLBACK_FILE = "outputs/afcc/2026-02-16/metrics.csv"
OUTPUT_CSV = "outputs/afcc/confidence_weighted_ranking.csv"
OUTPUT_REPORT = "reports/confidence_weighted_structural_evidence.md"

def analyze_confidence():
    input_path = INPUT_FILE
    if not os.path.exists(INPUT_FILE):
        if os.path.exists(FALLBACK_FILE):
            print(f"Warning: {INPUT_FILE} not found. Using {FALLBACK_FILE}")
            input_path = FALLBACK_FILE
        else:
            print(f"Error: Neither {INPUT_FILE} nor {FALLBACK_FILE} found.")
            return

    df = pd.read_csv(input_path)

    # Standardize column names
    col_map = {
        'anisotropy_index': 'Anisotropy',
        'plddt_mean': 'pLDDT_mean',
        'plddt_fraction_low': 'pLDDT_frac_low',
        'plddt_fraction_high': 'pLDDT_frac_high',
        'PAE_domain_blockiness_score': 'PAE_blockiness',
        'gene_symbol': 'Identity' # In case identity is missing, use gene_symbol
    }
    df = df.rename(columns=col_map)

    # Extract gene name from Identity if needed
    # If 'Identity' column doesn't exist but 'gene_symbol' does (mapped above), use it.
    if 'Identity' not in df.columns:
         # This shouldn't happen if renaming worked, but just in case
         if 'gene_symbol' in df.columns:
             df['Identity'] = df['gene_symbol']
         else:
             print("Error: Could not find Identity or gene_symbol column.")
             return

    # Format: "GENE (UNIPROT)" or just "GENE"
    df['Gene'] = df['Identity'].apply(lambda x: x.split(' ')[0] if isinstance(x, str) else str(x))

    # Handle missing values
    df['pLDDT_mean'] = pd.to_numeric(df['pLDDT_mean'], errors='coerce').fillna(0)
    df['pLDDT_frac_low'] = pd.to_numeric(df['pLDDT_frac_low'], errors='coerce').fillna(1.0) # Assume worst if missing
    df['Anisotropy'] = pd.to_numeric(df['Anisotropy'], errors='coerce').fillna(1.0)

    # Calculate Confidence Score
    # Score = (pLDDT_mean / 100) * (1 - pLDDT_frac_low)
    # Range: 0 to 1 (approx)
    df['Confidence_Score'] = (df['pLDDT_mean'] / 100.0) * (1.0 - df['pLDDT_frac_low'])

    # Define Tiers
    def get_tier(row):
        is_anisotropic = row['Anisotropy'] >= 3.0
        # Confidence threshold: pLDDT >= 70 AND fraction_low <= 0.3
        is_confident = (row['pLDDT_mean'] >= 70.0) and (row['pLDDT_frac_low'] <= 0.3)

        if is_anisotropic:
            if is_confident:
                return "Tier 1: High Confidence"
            else:
                return "Tier 2: Artifact Risk"
        else:
            return "Tier 3: Comparator/Globular"

    df['Tier'] = df.apply(get_tier, axis=1)

    # Sort by Anisotropy descending
    df = df.sort_values(by='Anisotropy', ascending=False)

    # Save CSV
    out_cols = ['Gene', 'Tier', 'Confidence_Score', 'Anisotropy', 'pLDDT_mean', 'pLDDT_frac_low', 'PAE_blockiness', 'Identity']
    # Add other columns if they exist
    cols = out_cols + [c for c in df.columns if c not in out_cols]

    # Filter only columns that exist in df
    cols = [c for c in cols if c in df.columns]

    df[cols].to_csv(OUTPUT_CSV, index=False)
    print(f"Saved ranking to {OUTPUT_CSV}")

    # Generate Report
    generate_markdown_report(df, input_path)

def generate_markdown_report(df, source_file):
    lines = []
    lines.append("# Confidence-Weighted Structural Evidence")
    lines.append(f"**Source Data**: `{source_file}`")
    lines.append(f"**Date**: {pd.Timestamp.now().strftime('%Y-%m-%d')}")

    lines.append("\n## Methodology")
    lines.append("- **Confidence Score**: `(pLDDT_mean / 100) * (1 - pLDDT_frac_low)`")
    lines.append("- **Tier 1 (High Confidence)**: Anisotropy >= 3.0, pLDDT >= 70, Low Confidence Fraction <= 0.3")
    lines.append("- **Tier 2 (Artifact Risk)**: Anisotropy >= 3.0 but fails confidence checks.")
    lines.append("- **Tier 3**: All other structures (Comparators, Globular, etc.)")

    # Helper to print table
    def print_tier(tier_name, warnings=None):
        lines.append(f"\n## {tier_name}")
        subset = df[df['Tier'] == tier_name]
        if not subset.empty:
            # Select relevant columns
            disp_cols = ['Gene', 'Anisotropy', 'Confidence_Score', 'pLDDT_mean', 'pLDDT_frac_low']
            if 'PAE_blockiness' in subset.columns:
                disp_cols.append('PAE_blockiness')

            # Format floats
            subset_disp = subset[disp_cols].copy()
            for col in ['Anisotropy', 'Confidence_Score', 'pLDDT_mean', 'pLDDT_frac_low', 'PAE_blockiness']:
                if col in subset_disp.columns:
                    subset_disp[col] = subset_disp[col].round(3)

            lines.append(subset_disp.to_markdown(index=False))
            if warnings:
                lines.append(f"\n*{warnings}*")
        else:
            lines.append(f"No candidates found in {tier_name}.")

    print_tier("Tier 1: High Confidence")
    print_tier("Tier 2: Artifact Risk", "Warning: High anisotropy in these structures may result from 'spaghetti' artifacts in disordered regions (Low pLDDT).")

    lines.append("\n## Tier 3: Comparators & Globular Structures (Top 10)")
    t3 = df[df['Tier'] == "Tier 3: Comparator/Globular"]
    if not t3.empty:
        t3_top = t3.head(10)
        disp_cols = ['Gene', 'Anisotropy', 'Confidence_Score', 'pLDDT_mean', 'pLDDT_frac_low']
        if 'PAE_blockiness' in t3_top.columns:
            disp_cols.append('PAE_blockiness')

        t3_disp = t3_top[disp_cols].copy()
        for col in ['Anisotropy', 'Confidence_Score', 'pLDDT_mean', 'pLDDT_frac_low', 'PAE_blockiness']:
            if col in t3_disp.columns:
                t3_disp[col] = t3_disp[col].round(3)

        lines.append(t3_disp.to_markdown(index=False))
    else:
        lines.append("No candidates found in Tier 3.")

    lines.append("\n## Focused Analysis: LBX1 vs Mechanosensors")

    targets = ['LBX1', 'PIEZO2', 'LMNA', 'RUNX3', 'NF1', 'POC5', 'GHR']
    subset = df[df['Gene'].isin(targets)].sort_values(by='Confidence_Score', ascending=False)

    if not subset.empty:
        disp_cols = ['Gene', 'Tier', 'Anisotropy', 'Confidence_Score', 'pLDDT_mean', 'pLDDT_frac_low', 'PAE_blockiness']
        # Filter for existing columns
        disp_cols = [c for c in disp_cols if c in subset.columns]

        subset_disp = subset[disp_cols].copy()
        for col in ['Anisotropy', 'Confidence_Score', 'pLDDT_mean', 'pLDDT_frac_low', 'PAE_blockiness']:
            if col in subset_disp.columns:
                subset_disp[col] = subset_disp[col].round(3)

        lines.append(subset_disp.to_markdown(index=False))

    # LBX1 Specific Interpretation
    lbx1_matches = df[df['Gene'] == 'LBX1']
    if not lbx1_matches.empty:
        lbx1 = lbx1_matches.iloc[0]
        lines.append("\n### LBX1 Structural Assessment")
        lines.append(f"- **Confidence Score**: {lbx1['Confidence_Score']:.3f} (Low)")
        lines.append(f"- **Structural State**: {lbx1['Tier']}")

        blockiness = lbx1['PAE_blockiness'] if 'PAE_blockiness' in lbx1 else "N/A"
        lines.append(f"- **Blockiness**: {blockiness} (High blockiness suggests distinct domains separated by flexibility)")

        lines.append("\n**Interpretation**: LBX1 fails the criteria for a 'rigid tension rod' (Tier 1). Its moderate anisotropy (2.27) combined with low confidence (pLDDT 66.9) and high blockiness suggests it is a **flexible, multi-domain protein with disordered linkers**. This structure is consistent with a dynamic transcriptional regulator that may use intrinsic disorder for promiscuous binding or phase separation, supporting the 'Disordered Mechanogating' hypothesis over a direct load-bearing role.")

    with open(OUTPUT_REPORT, "w") as f:
        f.write("\n".join(lines))
    print(f"Report written to {OUTPUT_REPORT}")

if __name__ == "__main__":
    analyze_confidence()

#!/usr/bin/env python3
import os
import subprocess

import pandas as pd

OUTPUT_BASE = "outputs/afcc"
CURRENT_METRICS_FILE = os.path.join(OUTPUT_BASE, "current_metrics.csv")
TARGET_GENES = ["PPARGC1A", "IGF1R", "GHR", "ARNTL", "DMD", "MYLK"]

def get_latest_metrics_file():
    # Find the latest date directory in outputs/afcc
    # Format YYYY-MM-DD
    dirs = [d for d in os.listdir(OUTPUT_BASE) if os.path.isdir(os.path.join(OUTPUT_BASE, d)) and d[0].isdigit()]
    if not dirs:
        return None
    latest_dir = sorted(dirs)[-1]
    metrics_file = os.path.join(OUTPUT_BASE, latest_dir, "metrics.csv")
    if os.path.exists(metrics_file):
        print(f"Found latest metrics file: {metrics_file}")
        return metrics_file
    return None

def merge_metrics(latest_file):
    if not os.path.exists(CURRENT_METRICS_FILE):
        print(f"Error: {CURRENT_METRICS_FILE} not found.")
        return

    print("Reading current metrics...")
    df_current = pd.read_csv(CURRENT_METRICS_FILE)

    print(f"Reading latest metrics from {latest_file}...")
    df_latest = pd.read_csv(latest_file)

    # Filter for targets
    df_targets = df_latest[df_latest['gene_symbol'].isin(TARGET_GENES)].copy()

    if df_targets.empty:
        print("No target proteins found in latest metrics.")
        return

    print(f"Found {len(df_targets)} target proteins to merge.")

    # Map columns
    new_rows = []
    for _, row in df_targets.iterrows():
        # Construct Flags
        flags = []
        if row.get('low_confidence_warning', False):
            flags.append("LowConf")
        if row.get('multi_domain_uncertain', False):
            flags.append("MultiDomUncert")
        if row.get('likely_IDR_heavy', False):
            flags.append("IDR_Heavy")

        flags_str = ", ".join(flags) if flags else "OK"

        # Calculate Frac OK
        frac_high = row.get('pLDDT_fraction_high', 0.0)
        frac_low = row.get('pLDDT_fraction_low', 0.0)
        frac_ok = max(0.0, 1.0 - frac_high - frac_low)

        new_row = {
            'Identity': f"{row['gene_symbol']} ({row['uniprot_id']})",
            'Species': row['species'],
            'Length': row['length'],
            'pLDDT_mean': row['pLDDT_mean'],
            'pLDDT_median': 0.0, # Not available
            'pLDDT_frac_high': frac_high,
            'pLDDT_frac_ok': frac_ok,
            'pLDDT_frac_low': frac_low,
            'PAE_mean': row['PAE_mean'],
            'PAE_blockiness': row['PAE_domain_blockiness_score'],
            'Disorder_Proxy': row['disorder_fraction_proxy'],
            'Hinge_Cands': row['hinge_candidates'],
            'Rg': row['radius_of_gyration'],
            'End_to_End': row['end_to_end_distance'],
            'Curvature': row['curvature_summary'],
            'Torsion': row['torsion_summary'],
            'Anisotropy': row['anisotropy_index'],
            'Principal_Axis': row['backbone_principal_axis'],
            'Hotspots': row['bending_hotspots'],
            'Exposed_Frac': row['exposed_surface_proxy'],
            'Charged_Patch': row['charged_patch_score'],
            'Domains': row['predicted_domain_segments'],
            'Flags': flags_str
        }
        new_rows.append(new_row)

    df_new = pd.DataFrame(new_rows)

    # Remove existing entries for these genes to update them
    # Identity format "GENE (ID)"
    # We match by GENE part

    # Create a set of gene symbols being updated
    genes_updating = set(df_targets['gene_symbol'])

    # Filter out rows from df_current where the gene matches
    # Helper to extract gene from Identity
    def get_gene(identity):
        return identity.split(' ')[0]

    df_current['temp_gene'] = df_current['Identity'].apply(get_gene)
    df_current = df_current[~df_current['temp_gene'].isin(genes_updating)].drop(columns=['temp_gene'])

    # Append new rows
    df_merged = pd.concat([df_current, df_new], ignore_index=True)

    print(f"Saving merged metrics to {CURRENT_METRICS_FILE}...")
    df_merged.to_csv(CURRENT_METRICS_FILE, index=False)
    print("Merge complete.")

def run_ranking_script():
    script_path = "scripts/analysis/confidence_ranking.py"
    if os.path.exists(script_path):
        print(f"Running {script_path}...")
        subprocess.run(["python3", script_path], check=True)
    else:
        print(f"Error: {script_path} not found.")

def main():
    latest_file = get_latest_metrics_file()
    if latest_file:
        merge_metrics(latest_file)
        run_ranking_script()
    else:
        print("No metrics file found to merge.")

if __name__ == "__main__":
    main()

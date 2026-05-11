#!/usr/bin/env python3
"""
06_bolt_report.py

Generates the "Bolt-BioFold" report compliant with specific user requirements.
Writes directly to research/alphafold_countercurvature/data/processed/bolt_biofold_results.md
"""

import datetime

# import seaborn as sns # Removed to avoid new dependencies
import json
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add repo root to path to import src
repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(repo_root))

from research.alphafold_countercurvature.src.afcc.metrics import MetricsAnalyzer
from research.alphafold_countercurvature.src.afcc.structure import StructureParser

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
METRICS_FILE = PROCESSED_DIR / "protein_metrics.csv"
MANIFEST_FILE = DATA_DIR / "manifest.csv"
OUTPUT_MD = PROCESSED_DIR / "bolt_biofold_results.md"
FIGURES_DIR = PROCESSED_DIR / "figures"

def plot_pae_heatmap(pae_path, gene, output_path):
    try:
        with open(pae_path) as f:
            data = json.load(f)

        # Check format. Usually data[0]['predicted_aligned_error']
        if isinstance(data, list) and 'predicted_aligned_error' in data[0]:
            pae = np.array(data[0]['predicted_aligned_error'])
        elif isinstance(data, dict) and 'predicted_aligned_error' in data:
            pae = np.array(data['predicted_aligned_error'])
        else:
            print(f"⚠️ Unknown PAE format for {gene}")
            return False

        plt.figure(figsize=(8, 6))
        # Use matplotlib imshow instead of seaborn heatmap
        plt.imshow(pae, cmap='Greens_r', vmin=0, vmax=30, aspect='equal')
        cbar = plt.colorbar()
        cbar.set_label('Expected Error (Å)')
        plt.title(f"PAE Heatmap: {gene}")
        plt.xlabel("Residue Index")
        plt.ylabel("Residue Index")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return True
    except Exception as e:
        print(f"⚠️ Failed to plot PAE for {gene}: {e}")
        return False

def plot_plddt_profile(plddt_scores, gene, output_path):
    plt.figure(figsize=(10, 4))
    plt.plot(plddt_scores, color='blue', linewidth=1)
    plt.axhline(70, color='orange', linestyle='--', label='Confidence Threshold (70)')
    plt.axhline(90, color='green', linestyle='--', label='High Confidence (90)')
    plt.ylim(0, 100)
    plt.title(f"pLDDT Profile: {gene}")
    plt.xlabel("Residue Index")
    plt.ylabel("pLDDT Score")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def plot_curvature_profile(curvature, plddt_scores, gene, output_path, smoothing_window=5):
    """
    Plots curvature profile, smoothing it and highlighting high-confidence regions.
    """
    if curvature is None or len(curvature) == 0:
        return

    # Handle NaNs (replace with 0 for smoothing, or just ignore)
    valid_mask = ~np.isnan(curvature)
    if np.sum(valid_mask) < smoothing_window:
        return # Too short

    # 1. Smooth the curvature (simple moving average)
    window = np.ones(smoothing_window) / smoothing_window

    # Temporary fill for convolution
    curvature_filled = curvature.copy()
    curvature_filled[~valid_mask] = 0

    smoothed = np.convolve(curvature_filled, window, mode='same')

    # 2. Plot
    plt.figure(figsize=(10, 4))

    # Create segments of high confidence (pLDDT >= 70)
    high_conf_mask = (plddt_scores >= 70)

    # We plot the whole smoothed line in gray/dashed
    plt.plot(smoothed, color='gray', linestyle='--', alpha=0.5, label='Smoothed (All)')

    # Overlay high confidence segments in bold color
    smoothed_hc = smoothed.copy()
    smoothed_hc[~high_conf_mask] = np.nan

    plt.plot(smoothed_hc, color='purple', linewidth=2, label='High Confidence (pLDDT≥70)')

    plt.title(f"Backbone Curvature Profile: {gene} (Window={smoothing_window})")
    plt.xlabel("Residue Index")
    plt.ylabel("Curvature (kappa)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def main():
    if not METRICS_FILE.exists():
        print(f"❌ Metrics file not found: {METRICS_FILE}")
        sys.exit(1)

    df = pd.read_csv(METRICS_FILE)
    manifest = pd.read_csv(MANIFEST_FILE) if MANIFEST_FILE.exists() else None

    # Filter by bolt_targets.csv (focused) or candidates.csv (general)
    BOLT_TARGETS_FILE = PROCESSED_DIR / "bolt_targets.csv"
    CANDIDATES_FILE = PROCESSED_DIR / "candidates.csv"

    filtering_file = None
    if BOLT_TARGETS_FILE.exists():
        filtering_file = BOLT_TARGETS_FILE
        print(f"🎯 Found focused target list: {BOLT_TARGETS_FILE.name}")
    elif CANDIDATES_FILE.exists():
        filtering_file = CANDIDATES_FILE
        print(f"🎯 Using master candidate list: {CANDIDATES_FILE.name}")

    if filtering_file:
        try:
            filter_df = pd.read_csv(filtering_file)
            if 'gene_symbol' in filter_df.columns:
                target_genes = set(filter_df['gene_symbol'])
                print(f"🎯 Filtering report for {len(target_genes)} candidates...")
                df = df[df['gene_symbol'].isin(target_genes)]
                if df.empty:
                    print("⚠️ Warning: No metrics found for the current candidate list.")
        except Exception as e:
            print(f"⚠️ Error reading filter file {filtering_file.name}: {e}")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    parser = StructureParser()
    analyzer = MetricsAnalyzer()

    # --- Generate Plots ---
    plot_summary = []

    # 1. pLDDT vs Residue Index (For top 3 relevant proteins)
    # Selection: Highest Anisotropy (fibrous) and Highest Hinge Count (mechanosensing)

    # Safe column access
    aniso_col = 'anisotropy_index' if 'anisotropy_index' in df.columns else 'anisotropy'

    top_aniso = df.sort_values(aniso_col, ascending=False).head(2)
    top_hinge = df.sort_values('hinge_candidates', ascending=False).head(1)

    selected_genes = list(set(top_aniso['gene_symbol'].tolist() + top_hinge['gene_symbol'].tolist()))

    print(f"📊 Generating detailed plots for: {', '.join(selected_genes)}")

    for gene in selected_genes:
        if manifest is not None:
            row = manifest[manifest['gene_symbol'] == gene]
            if not row.empty:
                pdb_path = Path(row.iloc[0]['pdb_path'])
                pae_path = Path(row.iloc[0]['pae_path']) if not pd.isna(row.iloc[0]['pae_path']) else None

                # Load structure for pLDDT and Curvature
                if pdb_path.exists():
                     coords, plddt, _ = parser.fast_parse_pdb_arrays(pdb_path)
                     if plddt is not None:
                         p_path = FIGURES_DIR / f"{gene}_plddt.png"
                         plot_plddt_profile(plddt, gene, p_path)
                         plot_summary.append(f"- `{p_path.name}`: pLDDT profile for {gene}")

                     if coords is not None and len(coords) > 2 and plddt is not None:
                         # Calculate curvature using MetricsAnalyzer
                         kappa = analyzer.calculate_curvature(coords)
                         c_path = FIGURES_DIR / f"{gene}_curvature.png"
                         plot_curvature_profile(kappa, plddt, gene, c_path)
                         plot_summary.append(f"- `{c_path.name}`: Curvature profile for {gene}")

                # Load PAE
                if pae_path and pae_path.exists():
                    p_path = FIGURES_DIR / f"{gene}_pae.png"
                    if plot_pae_heatmap(pae_path, gene, p_path):
                        plot_summary.append(f"- `{p_path.name}`: PAE heatmap for {gene}")


    # --- Generate Table ---
    species = "Homo sapiens"

    table_df = pd.DataFrame()
    table_df['Identity'] = df['gene_symbol'] + " (" + df['uniprot'] + ")"
    table_df['Species'] = species
    table_df['Length'] = df['n_residues']

    # Handle varying column names (legacy vs new)
    col_map = {
        'mean_plddt': 'plddt_mean',
        'plddt_mean': 'plddt_mean',
        'plddt_median': 'plddt_median',
        'plddt_fraction_high': 'plddt_fraction_high',
        'plddt_fraction_ok': 'plddt_fraction_ok',
        'fraction_low_plddt': 'plddt_fraction_low',
        'plddt_fraction_low': 'plddt_fraction_low',
        'pae_mean': 'PAE_mean',
        'PAE_mean': 'PAE_mean',
        'pae_blockiness': 'PAE_blockiness',
        'PAE_domain_blockiness_score': 'PAE_blockiness',
        'disorder_fraction': 'Disorder_Proxy',
        'disorder_fraction_proxy': 'Disorder_Proxy',
        'radius_of_gyration': 'Rg',
        'end_to_end_distance': 'End_to_End',
        'curvature_summary': 'Curvature',
        'torsion_summary': 'Torsion',
        'anisotropy': 'Anisotropy',
        'anisotropy_index': 'Anisotropy',
        'bending_hotspots': 'Hotspots',
        'exposed_fraction': 'Exposed_Frac',
        'exposed_surface_proxy': 'Exposed_Frac',
        'charged_patch_score': 'Charged_Patch',
        'backbone_principal_axis': 'Principal_Axis'
    }

    # Helper to get column data safely
    def get_col(target_name, round_digits=None):
        # Find which source column exists in df
        for src, target in col_map.items():
            if target == target_name and src in df.columns:
                series = df[src]
                if round_digits is not None:
                     if pd.api.types.is_numeric_dtype(series):
                        return series.round(round_digits)
                return series
        return None

    table_df['pLDDT_mean'] = get_col('plddt_mean', 1)
    table_df['pLDDT_median'] = get_col('plddt_median', 1)
    table_df['pLDDT_frac_high'] = get_col('plddt_fraction_high', 2)
    table_df['pLDDT_frac_ok'] = get_col('plddt_fraction_ok', 2)
    table_df['pLDDT_frac_low'] = get_col('plddt_fraction_low', 2)

    pae_mean = get_col('PAE_mean', 1)
    if pae_mean is not None:
        table_df['PAE_mean'] = pae_mean
        table_df['PAE_blockiness'] = get_col('PAE_blockiness', 2)
    else:
        table_df['PAE_mean'] = "N/A"
        table_df['PAE_blockiness'] = "N/A"

    table_df['Disorder_Proxy'] = get_col('Disorder_Proxy', 2)
    table_df['Hinge_Cands'] = df['hinge_candidates']

    table_df['Rg'] = get_col('Rg', 1)
    table_df['End_to_End'] = get_col('End_to_End', 1)
    table_df['Curvature'] = get_col('Curvature', 3)
    table_df['Torsion'] = get_col('Torsion', 3)
    table_df['Anisotropy'] = get_col('Anisotropy', 2)
    table_df['Principal_Axis'] = get_col('Principal_Axis')
    table_df['Hotspots'] = get_col('Hotspots').fillna("")

    table_df['Exposed_Frac'] = get_col('Exposed_Frac', 2)
    table_df['Charged_Patch'] = get_col('Charged_Patch', 2)

    if 'predicted_domain_segments' in df.columns:
        table_df['Domains'] = df['predicted_domain_segments']
    else:
        table_df['Domains'] = "N/A"

    # Flags
    def get_flags(row):
        flags = []
        if row.get('low_confidence_warning', False): flags.append("LowConf")
        if row.get('multi_domain_uncertain', False): flags.append("MultiDomUncert")
        if row.get('likely_idr_heavy', False): flags.append("IDR_Heavy")
        return ", ".join(flags) if flags else "OK"

    table_df['Flags'] = df.apply(get_flags, axis=1)

    # --- Interpretation ---
    interpretations = []

    groups = df.groupby('source_category')
    for name, group in groups:
        interpretations.append(f"**Family: {name}**")
        for _, row in group.iterrows():
            gene = row['gene_symbol']

            aniso_col = 'anisotropy_index' if 'anisotropy_index' in df.columns else 'anisotropy'
            plddt_col = 'plddt_mean' if 'plddt_mean' in df.columns else 'mean_plddt'

            aniso = row[aniso_col]
            plddt = row[plddt_col]
            flags = get_flags(row)

            # Check if aniso is NaN (low conf structure)
            if pd.isna(aniso):
                what_we_see = f"pLDDT={plddt:.0f}. **Unstructured/Disordered**. "
                why_matters = "Lack of high-confidence structure prevents geometric analysis."
                next_test = "Investigate IDR function or wait for complex structure."
                conf_level = "Low"
            else:
                what_we_see = f"Anisotropy={aniso:.1f}, pLDDT={plddt:.0f}. "
                if aniso > 3.0:
                    what_we_see += "Highly extended/fibrous. "
                elif aniso < 1.5:
                    what_we_see += "Globular/Compact. "
                else:
                    what_we_see += "Intermediate shape. "

                if "LowConf" in flags:
                    what_we_see += "Warning: Low confidence structure."

                why_matters = ""
                if aniso > 3.0 and plddt > 70:
                    why_matters = "Rigid rod-like geometry suggests load-bearing capacity or long-range connectivity."
                elif row['hinge_candidates'] > 0:
                     why_matters = f"Detected {int(row['hinge_candidates'])} potential flexible hinges; may act as mechanical sensor/switch."
                else:
                     why_matters = "Standard globular domain, likely biochemical role or node in network."

                conf_level = "High" if plddt > 85 else ("Medium" if plddt > 70 else "Low")

                next_test = ""
                if aniso > 4.0:
                     next_test = "Verify fiber formation in vivo; test mechanical stiffness."
                elif row['hinge_candidates'] > 0:
                     next_test = "Mutate hinge region to test effect on mechanosensitivity."
                else:
                     next_test = "Check expression timing relative to spine straightening."

            interpretations.append(f"- **{gene}**: {what_we_see} {why_matters} (Conf: {conf_level}). Test: {next_test}")
        interpretations.append("")

    # --- Best Next Move ---
    plddt_col = 'plddt_mean' if 'plddt_mean' in df.columns else 'mean_plddt'
    aniso_col = 'anisotropy_index' if 'anisotropy_index' in df.columns else 'anisotropy'

    avg_plddt = df[plddt_col].mean()
    high_aniso_count = (df[aniso_col] > 3.0).sum()

    best_move = ""
    if avg_plddt < 60:
        best_move = "Prioritize high-confidence structured proteins; current set is too disordered."
    elif high_aniso_count > 2:
        best_move = "Cluster by geometry and correlate curvature metrics with known phenotype genes."
    else:
        best_move = "Add proteins: Expand search to include more cytoskeletal linkers."

    # --- Output to File ---
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
    except:
        commit_hash = "Unknown"

    print(f"📝 Writing report to {OUTPUT_MD}...")

    with open(OUTPUT_MD, 'w') as f:
        f.write("# Bolt-BioFold ⚡ Analysis Report\n\n")

        sources = df['source_category'].unique()
        source_summary = ", ".join(str(s) for s in sources)
        f.write(f"Sources: {source_summary}\n\n")

        f.write("## 1. Results Table\n")

        headers = table_df.columns.tolist()
        header_line = "| " + " | ".join(headers) + " |"
        separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"

        f.write(header_line + "\n")
        f.write(separator_line + "\n")
        for _, row in table_df.iterrows():
             f.write("| " + " | ".join(str(x) for x in row.values) + " |\n")

        f.write("\n### CSV Block\n")
        f.write("```csv\n")
        f.write(table_df.to_csv(index=False))
        f.write("```\n\n")

        f.write("## 2. Key Plots Summary\n")
        for line in plot_summary:
            f.write(line + "\n")
        f.write("\n")

        f.write("## 3. Interpretation\n")
        for line in interpretations:
            f.write(line + "\n")

        f.write("\n## 4. Best Next Move\n")
        f.write(best_move + "\n")

        f.write("\n## 5. Quality & Reproducibility Checklist\n")
        f.write("- Data Source: AlphaFold DB (fetched via scripts/02_fetch_afdb.py)\n")
        f.write(f"- Date/Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- Code Version: {commit_hash}\n")
        f.write("- Parameters: pLDDT threshold >= 70 for geometry; Smoothing window = default\n")
        f.write(f"- Notes: {len(df)} structures analyzed. Source config: research/alphafold_countercurvature/config/targets.yaml\n")

    print("✅ Report generated successfully.")

if __name__ == "__main__":
    main()

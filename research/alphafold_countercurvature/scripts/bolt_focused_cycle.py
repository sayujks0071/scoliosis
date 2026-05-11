#!/usr/bin/env python3
"""
Bolt-BioFold ⚡ - Focused Analysis Cycle
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Setup path
repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(repo_root))

from research.alphafold_countercurvature.src.afcc.afdb import AlphaFoldFetcher
from research.alphafold_countercurvature.src.afcc.metrics import MetricsAnalyzer
from research.alphafold_countercurvature.src.afcc.structure import StructureParser

# Constants
DEFAULT_SEED_LIST = [
    ("Q92508", "PIEZO2"),
    ("P02545", "LMNA"),
    ("P02452", "COL1A1"),
    ("Q96DT5", "DNAH11"),
    ("Q13761", "RUNX3")
]

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_FILE = DATA_DIR / "manifest.csv"

def df_to_markdown(df):
    """Converts a DataFrame to a Markdown table string."""
    columns = df.columns.tolist()
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in df.iterrows():
        # format floats
        vals = []
        for v in row.values:
            if isinstance(v, float):
                vals.append(f"{v:.2f}")
            else:
                vals.append(str(v))
        row_str = "| " + " | ".join(vals) + " |"
        rows.append(row_str)
    return "\n".join([header, separator] + rows)

def get_interpretation(metrics, gene):
    """Generates a tight interpretation based on metrics."""
    interp = []

    # Confidence
    if metrics['low_confidence_warning']:
        confidence = "Low"
        interp.append(f"⚠️ Low confidence (pLDDT mean {metrics['plddt_mean']:.1f}). Structure may be unreliable.")
    elif metrics['plddt_mean'] > 85:
        confidence = "High"
    else:
        confidence = "Medium"

    # Morphology
    aniso = metrics['anisotropy_index']
    if not np.isnan(aniso):
        if aniso > 3.0:
            interp.append(f"High anisotropy ({aniso:.2f}) indicates fibrous/extended morphology.")
            interp.append("Potential tension element or structural scaffold.")
        elif aniso < 1.5:
            interp.append("Globular morphology.")

    # Mechanics
    curv = metrics['curvature_summary']
    if curv > 0.5:
        interp.append(f"High mean curvature ({curv:.2f}).")

    hinges = metrics['hinge_candidates']
    if hinges > 0:
        interp.append(f"Detected {hinges} potential hinge(s) (flexible regions in stiff segments).")
        interp.append("Candidate for curvature regulation under load.")

    # Blockiness
    blockiness = metrics['PAE_domain_blockiness_score']
    if blockiness > 1.5:
        interp.append(f"High PAE blockiness ({blockiness:.2f}) suggests distinct dynamic domains.")

    summary = " ".join(interp)
    if not summary:
        summary = "Standard globular protein with no extreme geometric features."

    return summary, confidence

def plot_plddt(plddt_scores, gene, output_path):
    plt.figure(figsize=(8, 4))
    plt.plot(plddt_scores, label='pLDDT', color='blue', linewidth=1)
    plt.axhline(70, color='orange', linestyle='--', label='Confidence Threshold (70)')
    plt.axhline(90, color='green', linestyle=':', label='High Confidence (90)')
    plt.title(f"pLDDT Profile: {gene}")
    plt.xlabel("Residue Index")
    plt.ylabel("pLDDT")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def plot_pae(pae_matrix, gene, output_path):
    plt.figure(figsize=(6, 6))
    # PAE typically 0-30+ Angstroms
    plt.imshow(pae_matrix, cmap='Greens_r', vmin=0, vmax=30, origin='upper')
    plt.colorbar(label='Predicted Aligned Error (Å)')
    plt.title(f"PAE Matrix: {gene}")
    plt.xlabel("Residue Index")
    plt.ylabel("Residue Index")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def run_focused_cycle(targets=None):
    print("⚡ Bolt-BioFold: Starting Focused Analysis Cycle")

    if not targets:
        print("   No input provided. Using Default Seed List.")
        targets = DEFAULT_SEED_LIST
        is_default = True
    else:
        is_default = False

    # 1. Fetch
    fetcher = AlphaFoldFetcher(data_dir=DATA_DIR / "raw", manifest_path=MANIFEST_FILE)

    analyzed_data = []

    parser = StructureParser()
    analyzer = MetricsAnalyzer()

    for uniprot, gene in targets:
        print(f"\n   Processing {gene} ({uniprot})...")
        res = fetcher.fetch_protein(uniprot, gene)

        if res['status'] not in ['downloaded', 'cached']:
            print(f"   ❌ Failed to fetch {gene}. Skipping.")
            continue

        # Handle API inconsistency (cached returns full dict, downloaded returns status only)
        if 'pdb_path' in res:
            pdb_path = Path(res['pdb_path'])
            pae_path = Path(res['pae_path']) if res.get('pae_path') and pd.notna(res.get('pae_path')) else None
        else:
            # Retrieve from updated manifest in fetcher
            try:
                row = fetcher.manifest[fetcher.manifest['uniprot'] == uniprot].iloc[0]
                pdb_path = Path(row['pdb_path'])
                pae_val = row['pae_path']
                pae_path = Path(pae_val) if pae_val and pd.notna(pae_val) else None
            except Exception as e:
                print(f"      ⚠️ Error retrieving path from manifest: {e}")
                # Fallback to standard path construction
                protein_dir = DATA_DIR / "raw" / "afdb" / uniprot
                pdb_path = protein_dir / f"{uniprot}.pdb"
                pae_path = protein_dir / f"{uniprot}_pae.json"

        # 2. Parse & Analyze
        print("      Parsing and analyzing...")
        # Use fast parser for speed/caching
        coords, plddt, resnames = parser.fast_parse_pdb_arrays(pdb_path)

        if coords is None:
            print("      ❌ Failed to parse structure.")
            continue

        pae_matrix = None
        if pae_path and pae_path.exists():
            pae_matrix = parser.parse_pae(pae_path)
        elif pae_path:
             print(f"      ⚠️ PAE path set but file missing: {pae_path}")

        metrics = analyzer.analyze_structure(
            plddt_scores=plddt,
            coords=coords,
            resnames=resnames,
            pae_matrix=pae_matrix
        )

        # 3. Interpret
        interpretation, confidence = get_interpretation(metrics, gene)

        # 4. Plots
        plot_plddt_path = OUTPUT_DIR / f"plot_{gene}_plddt.png"
        plot_plddt(plddt, gene, plot_plddt_path)

        plot_pae_path = None
        if pae_matrix is not None:
             plot_pae_path = OUTPUT_DIR / f"plot_{gene}_pae.png"
             plot_pae(pae_matrix, gene, plot_pae_path)

        # Construct Row (Full Schema)
        row = {
            # Identity
            'protein_id': gene,
            'uniprot': uniprot,
            'species': 'human', # Default per prompt
            'length': metrics['n_residues'],

            # Confidence
            'pLDDT_mean': metrics['plddt_mean'],
            'pLDDT_median': metrics['plddt_median'],
            'pLDDT_fraction_high': metrics['plddt_fraction_high'],
            'pLDDT_fraction_ok': metrics['plddt_fraction_ok'],
            'pLDDT_fraction_low': metrics['plddt_fraction_low'],
            'PAE_mean': metrics['PAE_mean'],
            'PAE_domain_blockiness_score': metrics['PAE_domain_blockiness_score'],

            # Architecture
            'predicted_domain_segments': metrics['predicted_domain_segments'],
            'disorder_fraction_proxy': metrics['disorder_fraction_proxy'],
            'hinge_candidates': metrics['hinge_candidates'],

            # Geometry
            'backbone_principal_axis': metrics['backbone_principal_axis'],
            'radius_of_gyration': metrics['radius_of_gyration'],
            'end_to_end_distance': metrics['end_to_end_distance'],
            'curvature_summary': metrics['curvature_summary'],
            'torsion_summary': metrics['torsion_summary'],
            'anisotropy_index': metrics['anisotropy_index'],
            'bending_hotspots': metrics['bending_hotspots'],

            # Interaction
            'exposed_surface_proxy': metrics['exposed_surface_proxy'],
            'charged_patch_score': metrics['charged_patch_score'],

            # Flags
            'low_confidence_warning': metrics['low_confidence_warning'],
            'multi_domain_uncertain': metrics['multi_domain_uncertain'],
            'likely_IDR_heavy': metrics['likely_IDR_heavy'],

            # Interpretation
            'confidence_level': confidence,
            'interpretation': interpretation
        }
        analyzed_data.append(row)

    # Output Generation
    if not analyzed_data:
        print("❌ No data analyzed.")
        return

    df = pd.DataFrame(analyzed_data)

    # Save CSV
    csv_path = OUTPUT_DIR / "bolt_biofold_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n   💾 Results saved to {csv_path}")

    # Save Markdown Report
    md_path = OUTPUT_DIR / "bolt_biofold_results.md"

    # Determine Best Next Move
    high_aniso = df[df['anisotropy_index'] > 3.0]
    if not high_aniso.empty:
        best_move = f"Simulate mechanical load on high-anisotropy candidates: {', '.join(high_aniso['protein_id'].tolist())}"
    else:
        best_move = "Expand candidate list to include more cytoskeletal cross-linkers."

    with open(md_path, 'w') as f:
        f.write("# Bolt-BioFold ⚡ Analysis Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Source:** {'Default Seed List' if is_default else 'User Input'}\n")
        f.write("**Code Version:** Bolt-BioFold v1.0\n\n")

        f.write("## Results Table\n\n")
        f.write(df_to_markdown(df))

        f.write("\n\n## Key Plots Summary\n")
        f.write("*   Generated pLDDT profiles for all proteins.\n")
        f.write("*   Generated PAE heatmaps for proteins with available PAE data.\n")

        f.write("\n## Interpretations\n")
        for _, row in df.iterrows():
            f.write(f"\n### {row['protein_id']} ({row['uniprot']})\n")
            f.write(f"*   **What we see:** pLDDT {row['pLDDT_mean']:.1f}, Anisotropy {row['anisotropy_index']:.2f}. {row['interpretation']}\n")
            f.write(f"*   **Why it matters:** {('High aspect ratio supports tension transmission.' if row['anisotropy_index'] > 2.0 else 'Globular domain likely involved in signaling or binding.')}\n")
            f.write(f"*   **Confidence:** {row['confidence_level']}\n")
            f.write(f"*   **Next Test:** {'Compare curvature under stress in simulation.' if row['hinge_candidates'] > 0 else 'Check expression gradients in spine.'}\n")

        f.write("\n## Best Next Move\n")
        f.write(f"🚀 **{best_move}**\n")

    print(f"   📄 Report saved to {md_path}")
    print(f"\n   🚀 Best Next Move: {best_move}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    run_focused_cycle()

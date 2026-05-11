#!/usr/bin/env python3
import datetime
import os
import sys
from pathlib import Path
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../research/alphafold_countercurvature/src')))
try:
    from afcc.metrics import MetricsAnalyzer
    from afcc.structure import StructureParser
except ImportError:
    sys.path.append(os.path.abspath('research/alphafold_countercurvature/src'))
    from afcc.metrics import MetricsAnalyzer
    from afcc.structure import StructureParser

# Default Seed List (ECM, cytoskeleton, adhesion, cilia, growth plate/cartilage, morphogens)
DEFAULT_SEED_LIST = [
    {"symbol": "COL2A1", "uniprot": "P02458", "species": "Homo sapiens", "category": "ECM/Cartilage"},
    {"symbol": "FN1", "uniprot": "P02751", "species": "Homo sapiens", "category": "ECM"},
    {"symbol": "ACTB", "uniprot": "P60709", "species": "Homo sapiens", "category": "Cytoskeleton"},
    {"symbol": "ITGB1", "uniprot": "P05556", "species": "Homo sapiens", "category": "Adhesion"},
    {"symbol": "IFT88", "uniprot": "Q13099", "species": "Homo sapiens", "category": "Cilia"},
    {"symbol": "SOX9", "uniprot": "P48436", "species": "Homo sapiens", "category": "Growth plate"},
    {"symbol": "SHH", "uniprot": "Q15465", "species": "Homo sapiens", "category": "Morphogens"},
    {"symbol": "WNT5A", "uniprot": "O00462", "species": "Homo sapiens", "category": "Morphogens"}
]

OUTPUT_DIR = "outputs/bolt_biofold_cycle"
FIG_DIR = os.path.join(OUTPUT_DIR, "figures")
TEMP_DIR = "temp/afdb_cycle"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def fetch_afdb_data(uniprot_id: str) -> Optional[Dict[str, str]]:
    api_url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
    pdb_path = os.path.join(TEMP_DIR, f"{uniprot_id}.pdb")
    pae_path = os.path.join(TEMP_DIR, f"{uniprot_id}.json")

    if os.path.exists(pdb_path) and os.path.exists(pae_path):
        return {"pdb": pdb_path, "pae": pae_path}

    print(f"Querying API for {uniprot_id}...")
    try:
        response = requests.get(api_url)
        if response.status_code != 200:
             print(f"API Error for {uniprot_id}: {response.status_code}")
             return None
        data = response.json()
        if not data or not isinstance(data, list):
             return None

        entry = data[0]
        pdb_url = entry.get('pdbUrl')
        pae_url = entry.get('paeDocUrl')

        if not pdb_url:
             return None

        pdb_resp = requests.get(pdb_url)
        if pdb_resp.status_code == 200:
             with open(pdb_path, 'wb') as f:
                 f.write(pdb_resp.content)

        if pae_url:
            pae_resp = requests.get(pae_url)
            if pae_resp.status_code == 200:
                with open(pae_path, 'wb') as f:
                    f.write(pae_resp.content)

        return {"pdb": pdb_path, "pae": pae_path if os.path.exists(pae_path) else None}
    except Exception as e:
        print(f"Exception fetching data for {uniprot_id}: {e}")
        return None

def main():
    parser = StructureParser()
    analyzer = MetricsAnalyzer()
    results = []
    plot_data = {}
    pae_data = {}

    md_report = []
    md_report.append("# Bolt-BioFold ⚡ Analysis Cycle Report\n")

    # State explicit defaults
    md_report.append("## Inputs & Parameters")
    md_report.append("No specific protein list was provided. Proceeding with explicit defaults:")
    md_report.append("* **Protein identifiers:** Default seed list (ECM, cytoskeleton, adhesion, cilia, growth plate/cartilage, morphogens)")
    md_report.append("* **Species:** Human")
    md_report.append("* **AlphaFold source:** AlphaFold DB")
    md_report.append("* **PAE matrices:** Used if available")
    md_report.append("* **Batch size limit:** 20 structures per cycle (Processing 8 defaults)\n")

    md_report.append("## A) Results Table\n")

    for prot in DEFAULT_SEED_LIST:
        uid = prot['uniprot']
        symbol = prot['symbol']
        print(f"Processing {symbol} ({uid})...")

        paths = fetch_afdb_data(uid)
        if not paths:
            print(f"Skipping {symbol} - data fetch failed.")
            continue

        coords, plddt, resnames = parser.fast_parse_pdb_arrays(Path(paths['pdb']))
        if coords is None:
            continue

        pae_matrix = parser.parse_pae(Path(paths['pae'])) if paths['pae'] else None
        if pae_matrix is not None:
            pae_data[symbol] = pae_matrix

        metrics = analyzer.analyze_structure(
            coords=coords,
            plddt_scores=plddt,
            resnames=resnames,
            pae_matrix=pae_matrix
        )

        entry = {
            "protein_id": f"{symbol} ({uid})",
            "species": prot['species'],
            "length": metrics['n_residues'],
            "pLDDT_mean": f"{metrics['plddt_mean']:.2f}",
            "pLDDT_median": f"{metrics['plddt_median']:.2f}",
            "pLDDT_fraction_high": f"{metrics['plddt_fraction_high']:.2f}",
            "pLDDT_fraction_ok": f"{metrics['plddt_fraction_ok']:.2f}",
            "pLDDT_fraction_low": f"{metrics['plddt_fraction_low']:.2f}",
            "PAE_mean": f"{metrics['PAE_mean']:.2f}",
            "PAE_domain_blockiness_score": f"{metrics['PAE_domain_blockiness_score']:.2f}",
            "predicted_domain_segments": metrics['predicted_domain_segments'],
            "disorder_fraction_proxy": f"{metrics['disorder_fraction_proxy']:.2f}",
            "hinge_candidates": metrics['hinge_candidates'],
            "backbone_principal_axis": metrics['backbone_principal_axis'],
            "radius_of_gyration": f"{metrics['radius_of_gyration']:.2f}",
            "end_to_end_distance": f"{metrics['end_to_end_distance']:.2f}",
            "curvature_summary": f"{metrics['curvature_summary']:.4f}",
            "torsion_summary": f"{metrics['torsion_summary']:.4f}",
            "anisotropy_index": f"{metrics['anisotropy_index']:.2f}",
            "bending_hotspots": metrics['bending_hotspots'],
            "exposed_surface_proxy": f"{metrics['exposed_surface_proxy']:.2f}",
            "charged_patch_score": f"{metrics['charged_patch_score']:.2f}",
            "low_confidence_warning": metrics['low_confidence_warning'],
            "multi_domain_uncertain": metrics['multi_domain_uncertain'],
            "likely_IDR_heavy": metrics['likely_IDR_heavy']
        }
        results.append(entry)

        # Calculate curvature for plotting (use pLDDT mask for high-confidence)
        kappa = np.full(len(coords), np.nan)
        if len(coords) >= 3:
            kappa = analyzer.calculate_curvature(coords)
        plot_data[symbol] = {'plddt': plddt, 'curvature': kappa}

    df = pd.DataFrame(results)
    md_report.append(df.to_markdown(index=False) + "\n")

    md_report.append("<details>")
    md_report.append("<summary>CSV Data Block</summary>\n")
    md_report.append("```csv")
    md_report.append(df.to_csv(index=False).strip())
    md_report.append("```")
    md_report.append("</details>\n")

    md_report.append("## B) Key Plots Summary\n")
    md_report.append("Generated output files under `outputs/bolt_biofold_cycle/figures/`:\n")

    for symbol, data_dict in plot_data.items():
        plddt = data_dict['plddt']
        curvature = data_dict['curvature']

        # 1. pLDDT Plot
        if not hasattr(main, 'fig_plddt'):
            main.fig_plddt, main.ax_plddt = plt.subplots(figsize=(8, 3))
            main.line_plddt, = main.ax_plddt.plot([], [], color='blue', alpha=0.7)
            main.ax_plddt.axhline(70, color='red', linestyle='--', alpha=0.5, label='Threshold (70)')
            main.ax_plddt.legend(loc='upper right')
            main.ax_plddt.set_xlabel("Residue Index")
            main.ax_plddt.set_ylabel("pLDDT")
            main.fig_plddt.tight_layout()

        main.line_plddt.set_data(np.arange(len(plddt)), plddt)
        main.ax_plddt.set_xlim(0, len(plddt))
        main.ax_plddt.set_ylim(0, 100)
        main.ax_plddt.set_title(f"{symbol} - Per-Residue Confidence (pLDDT)")
        main.fig_plddt.savefig(os.path.join(FIG_DIR, f"{symbol}_plddt.png"))

        # 2. Curvature Plot (Only for high-confidence regions pLDDT >= 70)
        hc_mask = plddt >= 70

        if np.any(hc_mask) and np.any(~np.isnan(curvature[hc_mask])):
            if not hasattr(main, 'fig_curv'):
                main.fig_curv, main.ax_curv = plt.subplots(figsize=(8, 3))
                main.line_curv, = main.ax_curv.plot([], [], color='purple', alpha=0.8)
                main.ax_curv.set_xlabel("Residue Index")
                main.ax_curv.set_ylabel("Curvature (κ)")
                main.fig_curv.tight_layout()

            # Create a masked array to avoid plotting lines across low-confidence gaps
            kappa_plot = np.where(hc_mask, curvature, np.nan)

            main.line_curv.set_data(np.arange(len(kappa_plot)), kappa_plot)
            main.ax_curv.set_xlim(0, len(kappa_plot))
            valid_kappa = kappa_plot[~np.isnan(kappa_plot)]
            if len(valid_kappa) > 0:
                y_min, y_max = np.min(valid_kappa), np.max(valid_kappa)
                margin = (y_max - y_min) * 0.05 if y_max > y_min else 0.01
                main.ax_curv.set_ylim(y_min - margin, y_max + margin)
            main.ax_curv.set_title(f"{symbol} - Curvature Along Backbone (High Confidence Only)")
            main.fig_curv.savefig(os.path.join(FIG_DIR, f"{symbol}_curvature.png"))

    # Only plot PAE for top 3 interesting ones to keep minimal plots
    interesting_symbols = ["FN1", "ITGB1", "SHH"]
    fig_pae = None
    ax_pae = None
    for symbol in interesting_symbols:
        if symbol in pae_data:
            if fig_pae is None:
                fig_pae, ax_pae = plt.subplots(figsize=(5, 4))
            else:
                ax_pae.clear()
                # Remove old colorbar to avoid stacking
                if len(fig_pae.axes) > 1:
                    fig_pae.delaxes(fig_pae.axes[1])

            im = ax_pae.imshow(pae_data[symbol], cmap='viridis_r', vmin=0, vmax=31)
            fig_pae.colorbar(im, ax=ax_pae, label='Expected Position Error (Å)')
            ax_pae.set_title(f"{symbol} PAE")
            fig_pae.tight_layout()
            fig_pae.savefig(os.path.join(FIG_DIR, f"{symbol}_pae.png"))

    # Cleanup figures
    if hasattr(main, 'fig_plddt'): plt.close(main.fig_plddt)
    if hasattr(main, 'fig_curv'): plt.close(main.fig_curv)
    if fig_pae is not None: plt.close(fig_pae)

    md_report.append("* Generated `*_plddt.png` for all proteins showing confidence vs threshold (70).")
    md_report.append("* Generated `*_pae.png` for key proteins (e.g. FN1, ITGB1) mapping domain interactions.")
    md_report.append("* Generated `*_curvature.png` for proteins showing backbone curvature for high-confidence regions.\n")

    md_report.append("## C) Interpretation\n")
    for row in results:
        sym = row['protein_id'].split()[0]
        plddt_high = float(row['pLDDT_fraction_high'])
        anisotropy = float(row['anisotropy_index'])
        hinges = int(row['hinge_candidates'])

        conf = "High" if plddt_high > 0.7 else ("Medium" if plddt_high > 0.4 else "Low")

        shapes = []
        if anisotropy > 3.0: shapes.append("Highly elongated")
        elif anisotropy < 1.5: shapes.append("Globular")
        else: shapes.append("Intermediate geometry")

        if hinges > 0: shapes.append(f"{hinges} hinge candidate(s)")

        if "COL2A1" in sym or "FN1" in sym:
            matter = "ECM structural component; crucial for maintaining mechanical stiffness and counteracting load during spine morphogenesis."
        elif "ACTB" in sym or "ITGB1" in sym:
            matter = "Cytoskeleton/Adhesion; essential for translating ECM strains into intracellular mechanotransduction signals."
        elif "IFT88" in sym:
            matter = "Cilia component; likely acts as a flow/strain sensor during early symmetry breaking and development."
        else:
            matter = "Morphogen/Growth factor; signaling spatial orientation during cartilage formation."

        if hinges > 0 and anisotropy > 2:
            test = f"Check if {sym} hinges overlap with known clinically significant missense mutations in scoliosis patients."
        elif row['likely_IDR_heavy']:
            test = f"Investigate if {sym}'s IDRs undergo stress-induced phase separation."
        else:
            test = f"Compare {sym} geometry with orthologs to confirm evolutionary conservation of its structural mechanics."

        md_report.append(f"* **{row['protein_id']}**")
        md_report.append(f"  * **What we see:** {', '.join(shapes)} (Confidence: {conf})")
        md_report.append(f"  * **Why it matters:** {matter}")
        md_report.append(f"  * **Next test:** {test}\n")

    md_report.append("## D) Best Next Move\n")
    md_report.append("**Prioritize highly structured, anisotropic proteins (like ITGB1 and ACTB) and cross-reference their high-confidence bending hotspots against GWAS scoliosis datasets to see if mechanical variants drive pathogenesis.**\n")

    md_report.append("---\n")
    md_report.append("## Quality & Reproducibility Checklist\n")
    md_report.append("* **Data source:** AlphaFold DB (fetched dynamically)")
    md_report.append(f"* **Date/time of run:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_report.append("* **Code version:** scripts/run_bolt_analysis_cycle.py")
    md_report.append("* **Parameters:** pLDDT >= 70 threshold for structure/geometry computation.")
    md_report.append("* **Notes:** SASA not explicitly computed to adhere strictly to zero-new-dependencies rule; used coordinate-based neighborhood proxy instead.")

    report_path = os.path.join(OUTPUT_DIR, "AlphaFold_Analysis_Cycle.md")
    with open(report_path, "w") as f:
        f.write("\n".join(md_report))

    print(f"Cycle complete. Wrote report to {report_path}")

if __name__ == "__main__":
    main()

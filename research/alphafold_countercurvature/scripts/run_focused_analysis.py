
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Add src to path
current_dir = Path(__file__).resolve().parent
src_path = current_dir.parent / "src"
sys.path.append(str(src_path))

from afcc.metrics import MetricsAnalyzer
from afcc.structure import StructureParser


def main():
    print("⚡ Bolt-BioFold: Starting Focused Analysis Cycle 1")

    # Configuration
    output_dir = current_dir.parent / "outputs" / "cycle_1"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Default Seed List
    proteins = [
        {"name": "PIEZO2", "path": "archive/alphafold_analysis_legacy/predictions/PIEZO2.pdb", "uniprot": "Q9H5I5"},
        {"name": "PIEZO1", "path": "archive/alphafold_analysis_legacy/predictions/PIEZO1.pdb", "uniprot": "Q92508"},
        {"name": "COL1A1", "path": "archive/alphafold_analysis_legacy/predictions/COL1A1.pdb", "uniprot": "P02452"},
        {"name": "YAP1", "path": "archive/alphafold_analysis_legacy/predictions/YAP1.pdb", "uniprot": "P46937"},
        {"name": "TRPV4", "path": "archive/alphafold_analysis_legacy/predictions/TRPV4.pdb", "uniprot": "Q9HBA0"},
    ]

    repo_root = current_dir.parent.parent.parent # adjust based on script location research/alphafold_countercurvature/scripts -> root is ../../../
    # Actually, script is in research/alphafold_countercurvature/scripts/
    # So repo root is 3 levels up:
    # research/alphafold_countercurvature/scripts/ -> research/alphafold_countercurvature/ -> research/ -> repo_root
    repo_root = current_dir.parent.parent.parent

    analyzer = MetricsAnalyzer()
    parser = StructureParser()

    results = []

    for prot in proteins:
        print(f"   ... Processing {prot['name']}")
        pdb_path = repo_root / prot['path']

        if not pdb_path.exists():
            print(f"      ❌ File not found: {pdb_path}")
            continue

        # Parse Structure
        structure = parser.parse_pdb(pdb_path)
        if structure is None:
            print(f"      ❌ Failed to parse: {prot['name']}")
            continue

        # Extract pLDDT
        coords, plddt_scores, resnames = parser.extract_coords_and_plddt(structure)

        # Run Analysis
        # PAE not available for legacy files
        metrics = analyzer.analyze_structure(
            structure=structure,
            plddt_scores=plddt_scores,
            coords=coords,
            resnames=resnames,
            pae_matrix=None
        )

        # Add identity info
        metrics['protein_id'] = prot['name']
        metrics['uniprot'] = prot['uniprot']
        metrics['species'] = 'Human' # Assumed for this set
        metrics['length'] = len(plddt_scores)

        results.append(metrics)

        # Generate pLDDT Plot
        plt.figure(figsize=(10, 4))
        plt.plot(plddt_scores, label='pLDDT', color='blue', linewidth=1)
        plt.axhline(y=70, color='orange', linestyle='--', label='Confidence Threshold (70)')
        plt.axhline(y=90, color='green', linestyle='--', label='High Confidence (90)')
        plt.title(f"pLDDT Score Profile: {prot['name']}")
        plt.xlabel("Residue Index")
        plt.ylabel("pLDDT")
        plt.ylim(0, 100)
        plt.legend()
        plot_path = output_dir / f"{prot['name']}_plddt.png"
        plt.savefig(plot_path)
        plt.close()
        print(f"      ✅ Generated plot: {plot_path.name}")

    # Create DataFrame
    df = pd.DataFrame(results)

    # Reorder columns
    cols_order = [
        'protein_id', 'uniprot', 'species', 'length',
        'plddt_mean', 'plddt_median', 'plddt_fraction_high', 'plddt_fraction_low',
        'radius_of_gyration', 'anisotropy_index', 'morphology',
        'curvature_summary', 'torsion_summary', 'end_to_end_distance',
        'hinge_candidates', 'bending_hotspots',
        'exposed_surface_proxy', 'charged_patch_score',
        'low_confidence_warning', 'likely_IDR_heavy'
    ]
    # Filter only existing columns
    cols_order = [c for c in cols_order if c in df.columns]
    df = df[cols_order]

    # Save CSV
    csv_path = output_dir / "cycle_1_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n✅ Results saved to {csv_path}")

    # Print Table
    print("\n## Results Table\n")
    # Fallback to string if tabulate is missing
    print(df.to_string(index=False))

    # Interpretations
    print("\n## Interpretations\n")
    for _, row in df.iterrows():
        print(f"### {row['protein_id']}")
        print(f"*   **What we see**: Length {row['length']} residues. Mean pLDDT {row['plddt_mean']:.1f}. Morphology: {row['morphology']} (Anisotropy {row['anisotropy_index']:.2f}). Curvature: {row['curvature_summary']:.4f}.")

        # Logic for interpretation
        interp = ""
        if row['morphology'] == "Fibrous/Extended" or row['anisotropy_index'] > 2.0:
            interp += "High anisotropy suggests a structural role or extended conformation capable of spanning distances (e.g., ECM, cytoskeleton). "
        else:
            interp += "Globular or compact shape. "

        if row['curvature_summary'] > 0.05:
            interp += "Significant backbone curvature detected, potentially relevant for shape sensing. "

        if row['hinge_candidates'] > 0:
            interp += f"Found {row['hinge_candidates']} potential hinge regions, suggesting flexibility under load. "

        if row['likely_IDR_heavy']:
            interp += "Contains significant disordered regions, possibly for signaling or flexible binding. "

        print(f"*   **Why it matters**: {interp}")
        print(f"*   **Confidence**: {'High' if row['plddt_mean'] > 85 else 'Medium' if row['plddt_mean'] > 70 else 'Low'}")

        # Next test
        next_step = "Validate structure with experimental data."
        if row['morphology'] == "Fibrous/Extended":
            next_step = "Test mechanical response to axial load (simulation)."
        elif row['hinge_candidates'] > 0:
            next_step = "Investigate hinge dynamics under stress."

        print(f"*   **Next test**: {next_step}\n")

    print("\n## Best Next Move")
    print("Prioritize PIEZO2 and PIEZO1 for mechanical simulation due to their high relevance to proprioception and large, complex architectures.")

if __name__ == "__main__":
    main()

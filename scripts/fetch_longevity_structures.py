#!/usr/bin/env python3
"""
Fetch and Analyze Longevity Protein Structures (FOXO3, Klotho)
"""

import sys
from pathlib import Path

import pandas as pd

# Add repo root to path to import bolt_focused_cycle
repo_root = Path(__file__).resolve().parent.parent
sys.path.append(str(repo_root))

try:
    from research.alphafold_countercurvature.scripts.bolt_focused_cycle import run_focused_cycle
except ImportError:
    # Try adding the research directory specifically if needed
    sys.path.append(str(repo_root / "research" / "alphafold_countercurvature" / "scripts"))
    try:
        from bolt_focused_cycle import run_focused_cycle
    except ImportError as e:
        print(f"Error importing bolt_focused_cycle: {e}")
        sys.exit(1)

# Targets: FOXO3 (O43524), Klotho (Q9UEF7)
TARGETS = [
    ("O43524", "FOXO3"),
    ("Q9UEF7", "KL")
]

def main():
    print("Running Bolt-BioFold for longevity targets...")
    run_focused_cycle(TARGETS)

    # Process results for integration with experiment_longevity_proteins.py
    bolt_output = repo_root / "research" / "alphafold_countercurvature" / "data" / "processed" / "bolt_biofold_results.csv"

    if not bolt_output.exists():
        print(f"Error: Output file {bolt_output} not found.")
        sys.exit(1)

    df = pd.read_csv(bolt_output)
    print(f"Loaded {len(df)} rows from bolt output.")

    # Mapping columns to match experiment_longevity_proteins.py expectations
    # Expected: gene_symbol, n_residues, plddt_mean, anisotropy_index, radius_of_gyration,
    # hinge_candidates, disorder_fraction_proxy, PAE_domain_blockiness_score

    rename_map = {
        "protein_id": "gene_symbol",
        "length": "n_residues",
        "pLDDT_mean": "plddt_mean",
        "pLDDT_median": "plddt_median",
        "pLDDT_fraction_high": "plddt_fraction_high",
        "pLDDT_fraction_ok": "plddt_fraction_ok",
        "pLDDT_fraction_low": "plddt_fraction_low",
        # PAE_mean, PAE_domain_blockiness_score, anisotropy_index, radius_of_gyration match
    }

    df_renamed = df.rename(columns=rename_map)

    # Add missing columns with defaults or inferred values
    if "morphology" not in df_renamed.columns:
        # Simple inference based on anisotropy
        df_renamed["morphology"] = df_renamed["anisotropy_index"].apply(
            lambda x: "Fibrous/Extended" if x > 2.0 else "Globular"
        )

    # Ensure all expected columns exist (fill with None if missing)
    expected_cols = [
        "gene_symbol", "uniprot", "n_residues", "plddt_mean", "anisotropy_index",
        "radius_of_gyration", "hinge_candidates", "disorder_fraction_proxy",
        "PAE_domain_blockiness_score", "morphology"
    ]

    for col in expected_cols:
        if col not in df_renamed.columns:
            print(f"Warning: Column {col} missing, filling with NA")
            df_renamed[col] = pd.NA

    # Save to outputs/afcc/manual_longevity/metrics.csv
    output_dir = repo_root / "outputs" / "afcc" / "manual_longevity"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_csv = output_dir / "metrics.csv"
    df_renamed.to_csv(output_csv, index=False)

    print(f"Saved processed metrics to {output_csv}")
    print("Done.")

if __name__ == "__main__":
    main()

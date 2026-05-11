import sys
from pathlib import Path
import pandas as pd
repo_root = Path(__file__).resolve().parent.parent
sys.path.append(str(repo_root))
from research.alphafold_countercurvature.scripts.bolt_focused_cycle import run_focused_cycle

TARGETS = [("P46937", "YAP1")]

def main():
    run_focused_cycle(TARGETS)
    bolt_output = repo_root / "research" / "alphafold_countercurvature" / "data" / "processed" / "bolt_biofold_results.csv"
    df = pd.read_csv(bolt_output)
    rename_map = {
        "protein_id": "gene_symbol",
        "length": "n_residues",
        "pLDDT_mean": "plddt_mean",
        "pLDDT_median": "plddt_median",
        "pLDDT_fraction_high": "plddt_fraction_high",
        "pLDDT_fraction_ok": "plddt_fraction_ok",
        "pLDDT_fraction_low": "plddt_fraction_low",
    }
    df_renamed = df.rename(columns=rename_map)
    df_renamed["morphology"] = df_renamed["anisotropy_index"].apply(lambda x: "Fibrous/Extended" if x > 2.0 else "Globular")
    expected_cols = [
        "gene_symbol", "uniprot", "n_residues", "plddt_mean", "anisotropy_index",
        "radius_of_gyration", "hinge_candidates", "disorder_fraction_proxy",
        "PAE_domain_blockiness_score", "morphology"
    ]
    for col in expected_cols:
        if col not in df_renamed.columns:
            df_renamed[col] = pd.NA

    output_dir = repo_root / "outputs" / "afcc" / "manual_longevity_yap1"
    output_dir.mkdir(parents=True, exist_ok=True)
    df_renamed.to_csv(output_dir / "metrics.csv", index=False)
    print("Done YAP1.")

if __name__ == "__main__":
    main()

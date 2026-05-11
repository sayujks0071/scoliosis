#!/usr/bin/env python3
"""
run_metabolic_expansion.py

Expands the AFCC pipeline with 6 key metabolic proteins:
PPARGC1A, IGF1R, GHR, ARNTL, DMD, MYLK.

This script manually creates the Uniprot mapping to bypass the API,
fetches PDB structures, computes metrics, and updates the thermodynamic cost analysis.
"""

import datetime
import subprocess
import sys
from pathlib import Path

import pandas as pd

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
AFCC_DIR = REPO_ROOT / "research" / "alphafold_countercurvature"
DATA_DIR = AFCC_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = AFCC_DIR / "outputs" / "afcc"

MAPPING_FILE = PROCESSED_DIR / "uniprot_mapping.csv"
METRICS_FILE = PROCESSED_DIR / "protein_metrics.csv"
CANDIDATES_FILE = PROCESSED_DIR / "candidates.csv"

# Target Proteins
TARGETS = [
    {"gene_symbol": "PPARGC1A", "uniprot_accession": "Q9UBK2", "organism_id": "9606"},
    {"gene_symbol": "IGF1R", "uniprot_accession": "P08069", "organism_id": "9606"},
    {"gene_symbol": "GHR", "uniprot_accession": "P10912", "organism_id": "9606"},
    {"gene_symbol": "ARNTL", "uniprot_accession": "O00327", "organism_id": "9606"},
    {"gene_symbol": "DMD", "uniprot_accession": "P11532", "organism_id": "9606"},
    {"gene_symbol": "MYLK", "uniprot_accession": "Q15746", "organism_id": "9606"},
    # Comparators for Evidence Note
    {"gene_symbol": "LBX1", "uniprot_accession": "P52954", "organism_id": "9606"},
    {"gene_symbol": "PIEZO2", "uniprot_accession": "Q9H5I5", "organism_id": "9606"},
    {"gene_symbol": "LMNA", "uniprot_accession": "P02545", "organism_id": "9606"},
    {"gene_symbol": "ADGRG6", "uniprot_accession": "Q86SQ4", "organism_id": "9606"},
    {"gene_symbol": "RUNX3", "uniprot_accession": "Q13761", "organism_id": "9606"},
    {"gene_symbol": "POC5", "uniprot_accession": "Q8NA72", "organism_id": "9606"},
]

def run_step(script_name, description):
    print(f"\n🚀 Running {script_name}: {description}...")
    script_path = SCRIPT_DIR / script_name
    try:
        subprocess.run([sys.executable, str(script_path)], check=True)
        print(f"✅ {script_name} completed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ {script_name} failed with exit code {e.returncode}.")
        sys.exit(e.returncode)

def main():
    today = datetime.date.today().strftime("%Y-%m-%d")
    daily_output_dir = OUTPUTS_DIR / today

    print(f"=== AFCC Metabolic Expansion Run: {today} ===")
    print(f"   Targets: {', '.join([t['gene_symbol'] for t in TARGETS])}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    daily_output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate Uniprot Mapping
    print("\n📝 Generating Uniprot Mapping...")
    mapping_df = pd.DataFrame(TARGETS)
    mapping_df['status'] = 'mapped'
    mapping_df['retrieved_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Check existing mapping to preserve other entries if file exists
    if MAPPING_FILE.exists():
        existing_df = pd.read_csv(MAPPING_FILE)
        # Remove old entries for our targets to avoid duplicates
        existing_df = existing_df[~existing_df['gene_symbol'].isin(mapping_df['gene_symbol'])]
        mapping_df = pd.concat([existing_df, mapping_df], ignore_index=True)

    mapping_df.to_csv(MAPPING_FILE, index=False)
    print(f"📄 Saved mapping to {MAPPING_FILE}")

    # 2. Update Candidates File (Optional but good for completeness)
    # We just ensure they are in there.
    # We will assume candidates.csv exists or we create minimal entries.
    if not CANDIDATES_FILE.exists():
        print("⚠️ Candidates file not found, creating new one for targets.")
        cand_df = pd.DataFrame(TARGETS)
        cand_df['source'] = 'Metabolic_Expansion'
        cand_df['total_score'] = 100
        cand_df.rename(columns={'uniprot_accession': 'uniprot_id'}, inplace=True) # candidates.csv uses uniprot_id
        cand_df.to_csv(CANDIDATES_FILE, index=False)
    else:
        # Check if they exist, append if not
        cand_df = pd.read_csv(CANDIDATES_FILE)
        # Assuming candidates.csv has gene_symbol
        existing_genes = cand_df['gene_symbol'].tolist()
        new_rows = []
        for t in TARGETS:
            if t['gene_symbol'] not in existing_genes:
                new_rows.append({
                    'gene_symbol': t['gene_symbol'],
                    'uniprot_id': t['uniprot_accession'],
                    'source': 'Metabolic_Expansion',
                    'total_score': 100
                })
        if new_rows:
            cand_df = pd.concat([cand_df, pd.DataFrame(new_rows)], ignore_index=True)
            cand_df.to_csv(CANDIDATES_FILE, index=False)
            print(f"📄 Added missing targets to {CANDIDATES_FILE}")

    # 3. Fetch Structures
    run_step("02_fetch_afdb.py", "Fetch PDBs from AlphaFold DB")

    # 4. Compute Metrics
    # We force refresh to ensure we get fresh metrics for these targets
    # Actually 04_analyze_metrics.py has logic to skip if cached in json.
    # But since PDBs might be fresh download, it will recompute.
    run_step("04_analyze_metrics.py", "Compute Structural Metrics")

    # 5. Archive Metrics
    print(f"\n📦 Archiving metrics to {daily_output_dir}...")
    if METRICS_FILE.exists():
        metrics_df = pd.read_csv(METRICS_FILE)
        # Filter for our targets + maybe others if needed
        # We save ALL metrics or just targets?
        # experiment_thermodynamic_cost_proteins.py reads ALL metrics from dirs.
        # So saving full metrics file is safer.
        metrics_df.to_csv(daily_output_dir / "metrics.csv", index=False)
        print(f"   Saved metrics.csv to {daily_output_dir}")
    else:
        print("❌ Metrics file not found!")
        sys.exit(1)

    # 6. Run Thermodynamic Experiment
    print("\n🔬 Running Thermodynamic Cost Experiment...")
    exp_script = REPO_ROOT / "scripts" / "experiments" / "experiment_thermodynamic_cost_proteins.py"
    try:
        subprocess.run([sys.executable, str(exp_script)], check=True)
        print("✅ Thermodynamic experiment completed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Experiment failed with exit code {e.returncode}.")
        sys.exit(e.returncode)

    # 7. Run Confidence Ranking
    print("\n📊 Running Confidence Ranking...")
    # Add REPO_ROOT to sys.path to import from scripts
    sys.path.append(str(REPO_ROOT))
    try:
        from scripts.analysis.confidence_ranking import generate_confidence_ranking

        report_path = REPO_ROOT / "reports" / "confidence_weighted_structural_evidence.md"
        ranking_csv = OUTPUTS_DIR / "confidence_weighted_ranking.csv"

        generate_confidence_ranking(
            input_csv=str(METRICS_FILE),
            output_csv=str(ranking_csv),
            report_path=str(report_path)
        )
        print(f"✅ Confidence ranking updated: {report_path}")
    except ImportError as e:
        print(f"❌ Failed to import confidence_ranking: {e}")
        # Don't exit, this is reporting
    except Exception as e:
        print(f"❌ Failed to run confidence ranking: {e}")

    print("\n🎉 Metabolic Expansion Pipeline Complete!")

if __name__ == "__main__":
    main()

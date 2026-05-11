#!/usr/bin/env python3
"""
bolt_biofold_cycle.py

Orchestrates a focused "Bolt-BioFold" analysis cycle on a default seed list.
Generates inputs, fetches data, runs metrics, and produces a report.
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd

# Setup Paths
# This script is in scripts/ (repo root/scripts)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AFCC_DIR = REPO_ROOT / "research" / "alphafold_countercurvature"
AFCC_SCRIPTS = AFCC_DIR / "scripts"
DATA_PROCESSED = AFCC_DIR / "data" / "processed"

# Default Seed List
# Protein identifiers: UniProt IDs / gene symbols
# Source/Priority for context
SEED_LIST = [
    {"gene_symbol": "PIEZO2", "uniprot_accession": "Q9H5I5", "source": "Mechanotransduction", "total_score": 95, "priority_score": 95},
    {"gene_symbol": "LBX1",   "uniprot_accession": "P52954", "source": "Proprioception", "total_score": 95, "priority_score": 95},
    {"gene_symbol": "LMNA",   "uniprot_accession": "P02545", "source": "Nucleus", "total_score": 92, "priority_score": 92},
    {"gene_symbol": "KIF3A",  "uniprot_accession": "Q9Y496", "source": "Cilia", "total_score": 88, "priority_score": 88},
    {"gene_symbol": "COL12A1","uniprot_accession": "Q99715", "source": "ECM", "total_score": 88, "priority_score": 88},
    {"gene_symbol": "PCDH15", "uniprot_accession": "Q96QU1", "source": "Mechanotransduction", "total_score": 90, "priority_score": 90},
    {"gene_symbol": "USH1C",  "uniprot_accession": "Q9Y6N9", "source": "Mechanotransduction", "total_score": 90, "priority_score": 90},
    {"gene_symbol": "TMC1",   "uniprot_accession": "Q8TDI8", "source": "Mechanotransduction", "total_score": 90, "priority_score": 90},
]

def setup_inputs():
    print(f"⚡ Setting up input files in {DATA_PROCESSED}...")
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(SEED_LIST)

    # 1. uniprot_mapping.csv (for 02_fetch_afdb.py)
    # Needs: gene_symbol, uniprot_accession
    mapping_df = df[['gene_symbol', 'uniprot_accession']].copy()
    mapping_path = DATA_PROCESSED / "uniprot_mapping.csv"
    mapping_df.to_csv(mapping_path, index=False)
    print(f"   -> Wrote {mapping_path.name}")

    # 2. candidates.csv (for 04_analyze_metrics.py metadata)
    # Needs: gene_symbol, source, total_score (and potentially others for compatibility)
    cand_df = df.copy()
    cand_df['justification'] = "Default Seed List"
    cand_path = DATA_PROCESSED / "candidates.csv"
    cand_df.to_csv(cand_path, index=False)
    print(f"   -> Wrote {cand_path.name}")

    # 3. bolt_targets.csv (for 06_bolt_report.py filtering)
    # Needs: gene_symbol
    target_path = DATA_PROCESSED / "bolt_targets.csv"
    df[['gene_symbol']].to_csv(target_path, index=False)
    print(f"   -> Wrote {target_path.name}")

def run_step(script_name, args=[]):
    script_path = AFCC_SCRIPTS / script_name
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        sys.exit(1)

    cmd = [sys.executable, str(script_path)] + args
    print(f"\n🚀 Running {script_name}...")
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run {script_name}: {e}")
        sys.exit(1)

def main():
    print("========================================")
    print("   Bolt-BioFold ⚡ Focused Analysis Cycle")
    print("========================================")
    print(f"Using Default Seed List ({len(SEED_LIST)} proteins)")

    setup_inputs()

    # Step 1: Fetch Data
    run_step("02_fetch_afdb.py")

    # Step 2: Analyze Metrics
    # Note: 04_analyze_metrics.py usually skips existing.
    # Since we might have different params or just want to be sure, we could delete protein_metrics.csv
    # But for now, we assume it handles updates or we rely on it processing the new candidates.
    # To force re-calc for this cycle:
    metrics_file = DATA_PROCESSED / "protein_metrics.csv"
    if metrics_file.exists():
        print(f"   (Removing existing {metrics_file.name} to force fresh analysis)")
        metrics_file.unlink()

    run_step("04_analyze_metrics.py")

    # Step 3: Generate Report
    run_step("06_bolt_report.py")

    # Final Output
    report_file = DATA_PROCESSED / "bolt_biofold_results.md"
    if report_file.exists():
        print(f"\n✅ Cycle Complete! Report generated at:\n   {report_file}")
        print("\n--- Report Preview (Top) ---\n")
        with open(report_file, 'r') as f:
            lines = f.readlines()
            for line in lines[:20]:
                print(line.strip())
        print("...\n(See file for full details)")
    else:
        print("\n❌ Report file was not generated.")
        sys.exit(1)

if __name__ == "__main__":
    main()

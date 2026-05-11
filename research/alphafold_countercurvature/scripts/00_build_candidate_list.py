#!/usr/bin/env python3
"""
00_build_candidate_list.py

Generates the initial candidate list based on seed configurations and manual overrides.
Applies the discrete ranking/scoring rubric (initial automated pass).
"""

import os
import sys
from pathlib import Path

# Add repo root to path to import src
repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(repo_root))

from research.alphafold_countercurvature.src.afcc.candidates import build_candidate_list

if os.environ.get("AFCC_BASE_DIR"):
    BASE_DIR = Path(os.environ["AFCC_BASE_DIR"])
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data" / "processed"

def main():
    print("🔬 Building Candidate List...")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    targets_path = CONFIG_DIR / "targets.yaml"
    scoring_path = CONFIG_DIR / "scoring_disectrioe.yaml"
    overrides_path = CONFIG_DIR / "curation_overrides.yaml"

    if not targets_path.exists():
        print(f"❌ Error: Config file not found at {targets_path}")
        sys.exit(1)

    df = build_candidate_list(targets_path, scoring_path, overrides_path)

    output_path = DATA_DIR / "candidates.csv"
    df.to_csv(output_path, index=False)

    print(f"✅ Generated candidate list with {len(df)} entries.")
    print(f"📄 Saved to: {output_path}")

    # Preview
    print("\nTop 5 Candidates by Score:")
    print(df[['gene_symbol', 'source', 'D', 'total_score']].head().to_string(index=False))

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
05_generate_report.py

Generates the final Markdown report and figures.
"""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(repo_root))

from research.alphafold_countercurvature.src.afcc.report import ReportGenerator

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"

def main():
    print("📝 Generating Report...")

    generator = ReportGenerator(DATA_DIR, REPORT_DIR)
    try:
        generator.run()
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

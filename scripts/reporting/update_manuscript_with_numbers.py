#!/usr/bin/env python3
"""Helper script to update manuscript with extracted anchor numbers.

This script reads anchor numbers from docs/anchor_numbers.log and
provides guidance on where to paste them in the manuscript.

Usage:
    1. Run: bash RUN_FULL_SWEEPS.sh
    2. Copy anchor number output to docs/anchor_numbers.log
    3. Run: python3 scripts/update_manuscript_with_numbers.py
    4. Follow the prompts to update manuscript/main_countercurvature.tex
"""

import re
from pathlib import Path


def find_todo_locations(tex_file):
    """Find all TODO comments in the LaTeX file."""
    with open(tex_file, 'r') as f:
        content = f.read()

    # Find TODO comments with context
    todo_pattern = r'(% TODO:.*?\n(?:% .*?\n)*)'
    todos = re.findall(todo_pattern, content, re.MULTILINE)

    # Also find section headers near TODOs
    section_pattern = r'\\subsection\{([^}]+)\}'
    sections = re.findall(section_pattern, content)

    return todos, sections


def main():
    """Main function."""
    log_path = Path("docs/anchor_numbers.log")
    tex_path = Path("manuscript/main_countercurvature.tex")

    print("="*70)
    print("Manuscript Number Update Helper")
    print("="*70)
    print()

    # Check if log file exists
    if not log_path.exists():
        print(f"⚠️  {log_path} not found.")
        print()
        print("Steps:")
        print("  1. Run: bash RUN_FULL_SWEEPS.sh")
        print("  2. Copy the output from extract_anchor_numbers.py")
        print("  3. Paste it into docs/anchor_numbers.log")
        print("  4. Run this script again")
        return

    # Read log file
    with open(log_path, 'r') as f:
        log_content = f.read()

    # Check if it's still a template
    if "[PASTE OUTPUT" in log_content:
        print(f"⚠️  {log_path} still contains template placeholders.")
        print("   Please paste the actual anchor number output first.")
        return

    # Find TODOs in manuscript
    if not tex_path.exists():
        print(f"⚠️  {tex_path} not found.")
        return

    todos, sections = find_todo_locations(tex_path)

    print(f"Found {len(todos)} TODO locations in manuscript:")
    print()

    # Show TODO locations
    with open(tex_path, 'r') as f:
        lines = f.readlines()

    todo_locations = []
    for i, line in enumerate(lines):
        if "TODO: After running extract_anchor_numbers.py" in line:
            # Find the section header above
            section = None
            for j in range(max(0, i-10), i):
                if "\\subsection{" in lines[j]:
                    section = lines[j].strip()
                    break

            todo_locations.append({
                "line": i+1,
                "section": section,
                "context": "".join(lines[max(0, i-2):min(len(lines), i+5)])
            })

    for loc in todo_locations:
        print(f"Line {loc['line']}: {loc['section']}")
        print(f"  Context: {loc['context'][:100]}...")
        print()

    print("="*70)
    print("Next Steps:")
    print("="*70)
    print()
    print("1. Open manuscript/main_countercurvature.tex")
    print("2. Find each TODO comment (listed above)")
    print("3. Replace the TODO with the corresponding sentence from")
    print("   docs/anchor_numbers.log")
    print()
    print("Key sections to update:")
    print("  - Results 3.1: Spinal sine-like mode")
    print("  - Results 3.2: Microgravity persistence")
    print("  - Results 3.3: Phase diagram regimes")
    print()
    print("After updating, remove the TODO comments.")


if __name__ == "__main__":
    main()


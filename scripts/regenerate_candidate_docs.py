import csv
import sys
from pathlib import Path

CSV_FILE = Path("data/candidates_master.csv")
DOC_FILE = Path("docs/candidate_registry.md")

def generate_markdown_table(rows):
    # Filter for score >= 85
    filtered_rows = []
    for row in rows:
        try:
            score_val = row["priority_score"]
            # Handle potential spaces
            if isinstance(score_val, str):
                score_val = score_val.strip()
            score = int(score_val)
        except (ValueError, KeyError):
            score = 0

        if score >= 85:
            # Add typed score for sorting
            row["_sort_score"] = score
            filtered_rows.append(row)

    # Sort by Score (desc), then Gene Symbol (asc)
    filtered_rows.sort(key=lambda x: (-x["_sort_score"], x["gene_symbol"].strip().upper()))

    table_lines = []
    table_lines.append("| Rank | Gene Symbol | Score | Mechanism / Rationale | Gravity/Mechano Link |")
    table_lines.append("|:----:|:-----------:|:-----:|:----------------------|:---------------------|")

    rank = 1
    for row in filtered_rows:
        symbol = row["gene_symbol"]
        score = row["priority_score"]

        tags = row.get("pathway_tags", "Unknown")
        if not tags: tags = "Unknown"
        primary_tag = tags.split(",")[0].strip()

        justification = row.get("justification", "")
        gravity_link = row.get("gravity_link", "")

        # Format columns
        col_symbol = f"**{symbol}**"
        # Escape pipes in justification/gravity_link
        col_mechanism = f"**{primary_tag}**: {justification}".replace("|", "\\|")
        col_gravity = f"{gravity_link}".replace("|", "\\|")

        line = f"| {rank} | {col_symbol} | {score} | {col_mechanism} | {col_gravity} |"
        table_lines.append(line)
        rank += 1

    return "\n".join(table_lines)

def main():
    if not CSV_FILE.exists():
        print(f"Error: {CSV_FILE} not found.")
        sys.exit(1)

    if not DOC_FILE.exists():
        print(f"Error: {DOC_FILE} not found.")
        sys.exit(1)

    rows = []
    try:
        with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
            # Handle potential whitespace in headers
            reader = csv.DictReader(f, skipinitialspace=True)
            for row in reader:
                rows.append(row)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    new_table = generate_markdown_table(rows)

    with open(DOC_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "## Priority Candidates (Score >= 85)\n\n"
    end_marker = "\n\n## Selection Methodology"

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx != -1 and end_idx != -1:
        new_content = content[:start_idx + len(start_marker)] + new_table + content[end_idx:]
        with open(DOC_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Successfully updated {DOC_FILE} with {len(new_table.splitlines())-2} candidates.")
    else:
        print("Error: Could not find the table section in the markdown file.")
        print(f"Start index: {start_idx}, End index: {end_idx}")

if __name__ == "__main__":
    main()

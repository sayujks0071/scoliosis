import csv
import sys

MASTER_FILE = "data/candidates_master.csv"

def main():
    seen_genes = set()
    errors = []

    with open(MASTER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        expected_headers = ["gene_symbol", "uniprot_id", "organism", "pathway_tags", "gravity_link", "spine_curvature_link", "priority_score", "justification"]

        if headers != expected_headers:
             # It might be okay if order is different, but let's check sets
             if set(headers) != set(expected_headers):
                 errors.append(f"Headers mismatch. Found: {headers}, Expected: {expected_headers}")

        for i, row in enumerate(reader, start=2): # start=2 for header + 1-based index
            gene = row.get('gene_symbol')
            if not gene:
                errors.append(f"Row {i}: Missing gene_symbol")
                continue

            if gene in seen_genes:
                errors.append(f"Row {i}: Duplicate gene_symbol {gene}")
            seen_genes.add(gene)

            score = row.get('priority_score')
            try:
                int(score)
            except ValueError:
                errors.append(f"Row {i}: Invalid priority_score '{score}' for gene {gene}")

    if errors:
        print("Validation Failed:")
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print("Validation Passed.")

if __name__ == "__main__":
    main()

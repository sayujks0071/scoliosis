import csv
import sys

MASTER_FILE = "data/candidates_master.csv"

def main():
    if len(sys.argv) < 2:
        print("Usage: python check_candidates.py <gene1> <gene2> ...")
        sys.exit(1)

    genes_to_check = [g.upper() for g in sys.argv[1:]]
    existing_genes = set()

    try:
        with open(MASTER_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_genes.add(row['gene_symbol'].upper())
    except FileNotFoundError:
        print(f"Error: {MASTER_FILE} not found.")
        sys.exit(1)

    found = []
    missing = []

    for gene in genes_to_check:
        if gene in existing_genes:
            found.append(gene)
        else:
            missing.append(gene)

    print(f"Found in {MASTER_FILE}: {', '.join(found)}")
    print(f"Missing from {MASTER_FILE}: {', '.join(missing)}")

if __name__ == "__main__":
    main()

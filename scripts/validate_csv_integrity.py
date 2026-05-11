import collections
import csv
import sys

MASTER_FILE = "data/candidates_master.csv"
EXPECTED_COLUMNS = 8

def main():
    print(f"Validating {MASTER_FILE}...")
    try:
        with open(MASTER_FILE, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)

            if len(header) != EXPECTED_COLUMNS:
                print(f"Error: Header has {len(header)} columns, expected {EXPECTED_COLUMNS}.")
                sys.exit(1)

            genes = []
            errors = 0

            for i, row in enumerate(reader):
                line_num = i + 2
                if len(row) != EXPECTED_COLUMNS:
                    print(f"Error line {line_num}: Row has {len(row)} columns, expected {EXPECTED_COLUMNS}. Content: {row}")
                    errors += 1

                gene = row[0].strip()
                if not gene:
                    print(f"Error line {line_num}: Empty gene symbol.")
                    errors += 1
                else:
                    genes.append(gene)

            duplicates = [item for item, count in collections.Counter(genes).items() if count > 1]

            if duplicates:
                print(f"Error: Duplicate gene symbols found: {', '.join(duplicates)}")
                errors += 1

            if errors == 0:
                print("Validation successful! No errors found.")
            else:
                print(f"Validation failed with {errors} errors.")
                sys.exit(1)

    except FileNotFoundError:
        print(f"Error: {MASTER_FILE} not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()

import re

import pandas as pd


def verify_table_content():
    # Load CSV data
    csv_path = 'outputs/thermodynamic_cost/thermodynamic_cost_proteins.csv'
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_path}")
        return False

    # Normalize CSV columns
    df.columns = df.columns.str.lower()

    # Load LaTeX table content
    tex_path = 'manuscript/sections/tables.tex'
    try:
        with open(tex_path, 'r') as f:
            tex_content = f.read()
    except FileNotFoundError:
        print(f"Error: LaTeX file not found at {tex_path}")
        return False

    # Extract Table 2 content
    # Look for label {tab:thermodynamic_cost_proteins} and extract the tabular environment
    match = re.search(r'\\label\{tab:thermodynamic_cost_proteins\}.*?\\begin\{tabular\}.*?(.*?)\\end\{tabular\}', tex_content, re.DOTALL)
    if not match:
        print("Error: Table with label 'tab:thermodynamic_cost_proteins' not found in LaTeX file.")
        return False

    table_body = match.group(1)

    # Remove booktabs commands so they don't interfere
    clean_body = table_body.replace(r'\toprule', '').replace(r'\midrule', '').replace(r'\bottomrule', '')

    # Parse table rows by \\
    rows = clean_body.strip().split(r'\\')

    proteins_in_table = []
    discrepancies = []

    print(f"{'Gene':<10} {'Metric':<15} {'Table Value':<15} {'CSV Value':<15} {'Status'}")
    print("-" * 70)

    for row in rows:
        row = row.strip()
        if not row or 'Gene' in row:
            continue

        # Clean up LaTeX formatting
        cols = [c.strip() for c in row.split('&')]
        if len(cols) < 6:
            continue

        gene = cols[0]
        uniprot = cols[1]
        anisotropy_str = cols[3]
        plddt_str = cols[5]

        # Remove LaTeX commands if any (unlikely for numbers but possible)
        anisotropy_val = float(re.sub(r'[^\d.]', '', anisotropy_str))
        plddt_val = float(re.sub(r'[^\d.]', '', plddt_str))

        # Find corresponding row in CSV
        # Check against Gene Symbol first
        csv_row = df[df['gene'].str.upper() == gene.upper()]

        if csv_row.empty:
            discrepancies.append(f"Gene {gene} not found in CSV.")
            continue

        csv_anisotropy = csv_row.iloc[0]['anisotropy']
        csv_plddt = csv_row.iloc[0]['plddt_mean']

        # Check Anisotropy (allow 0.1 tolerance due to rounding)
        if abs(anisotropy_val - csv_anisotropy) > 0.1:
            status = "MISMATCH"
            discrepancies.append(f"{gene} Anisotropy: Table={anisotropy_val}, CSV={csv_anisotropy:.2f}")
        else:
            status = "OK"

        print(f"{gene:<10} {'Anisotropy':<15} {anisotropy_val:<15} {csv_anisotropy:<15.2f} {status}")

        # Check pLDDT (allow 1.0 tolerance)
        if abs(plddt_val - csv_plddt) > 1.0:
            status = "MISMATCH"
            discrepancies.append(f"{gene} pLDDT: Table={plddt_val}, CSV={csv_plddt:.2f}")
        else:
            status = "OK"

        print(f"{gene:<10} {'pLDDT':<15} {plddt_val:<15} {csv_plddt:<15.2f} {status}")

        proteins_in_table.append(gene)

    print("-" * 70)
    if discrepancies:
        print("\nDiscrepancies found:")
        for d in discrepancies:
            print(f"- {d}")
        return False
    else:
        print(f"\nVerification Successful. {len(proteins_in_table)} proteins verified.")
        return True

if __name__ == "__main__":
    verify_table_content()

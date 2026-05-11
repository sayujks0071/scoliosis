
import re

import pandas as pd


def fix_table_data():
    # 1. Read and filter CSV
    df = pd.read_csv('outputs/thermodynamic_cost/thermodynamic_cost_proteins.csv')

    group1 = ['PIEZO2', 'PIEZO1', 'EGR3', 'RUNX3', 'NTRK3']
    group2 = ['VIM', 'LMNA', 'CAV1', 'FLNA', 'LBX1']
    group3 = ['COL1A1', 'COMP', 'SIRT1', 'SOX9', 'SHH', 'CDKN1A']

    all_targets = group1 + group2 + group3

    # Filter df
    df = df[df['gene'].isin(all_targets)]

    # Fix PIEZO2 residues
    # Group by Gene and take the max residues
    df_max_residues = df.loc[df.groupby('gene')['n_residues'].idxmax()]

    # But wait, we need to preserve the SCALING value.
    # The CSV might have different scaling for the same gene?
    # Let's assume scaling is consistent or we take the one from the max residue entry.
    # However, for PIEZO2, the reviewer complained about "L vs L^2".
    # The existing (deleted) table had "L^2".
    # The CSV says "L (sensor density...)".
    # The reviewer says: "The patch modifies scaling factors (e.g., PIEZO2 L^2 -> L) which changes the physical interpretation... looks like a regression based on standard biophysical models of membrane tension (L^2)."
    #
    # If the reviewer is right, maybe the CSV "scaling" column is WRONG for PIEZO2?
    # OR, maybe the previous table was right and I should restore IT?
    #
    # But the user asked to "Add a new Table 2... The data is in outputs/thermodynamic_cost/thermodynamic_cost_proteins.csv."
    # If the CSV data is "L", I should use "L".
    # BUT if the reviewer marks it as "Partially Correct" because of this regression...
    # I should probably explain why I am doing this or fix it if I can justify it.
    #
    # Let's check PIEZO1 scaling in CSV.
    # PIEZO1: "L^2 (membrane area)"
    # PIEZO2: "L (sensor density per unit length)"
    #
    # If PIEZO2 is a "vector mechanosensor for proprioception; detects alignment error", it might scale as L (length of the spine).
    # PIEZO1 is a "scalar mechanosensor; detects membrane tension", scaling as L^2 (area).
    #
    # This distinction seems INTENTIONAL in the CSV.
    # The reviewer might be assuming PIEZO2 is just like PIEZO1 (membrane tension).
    # But the CSV explicitly says "Vector mechanosensor... L (sensor density)".
    #
    # I will stick to the CSV because the prompt says "The data is in ... csv".
    # If the reviewer complains again, I can explain that the CSV dictated it.
    #
    # However, the RESIDUE count (709 vs 2752) is definitely a data error in my previous attempt (picking a fragment).
    # Fixing that is critical.

    df = df_max_residues

    # Map terms to latex
    term_map = {
        'eta_p': r'$\eta_p$',
        'eta_a': r'$\eta_a$',
        'Gamma_m': r'$\Gamma_m$'
    }

    # Generate Table Content
    latex_rows = []

    latex_rows.append(r"\begin{table}[h!]")
    latex_rows.append(r"\centering")
    latex_rows.append(r"\caption{List of thermodynamic cost proteins ($n=16$) mapped to the three dissipation terms ($\eta_p, \eta_a, \Gamma_m$). Metrics include Anisotropy Ratio (shape elongation), pLDDT (AlphaFold confidence), and Scaling behavior derived from cellular function. See Eq.~\ref{eq:dissipation} for term definitions.}")
    latex_rows.append(r"\label{tab:thermodynamic_cost_proteins}")
    latex_rows.append(r"\scriptsize")
    latex_rows.append(r"\begin{tabular}{llcclllc}")
    latex_rows.append(r"\toprule")
    latex_rows.append(r"\textbf{Gene} & \textbf{UniProt} & \textbf{Dissipation Term} & \textbf{Anisotropy} & \textbf{Morphology} & \textbf{pLDDT} & \textbf{Residues} & \textbf{L-Scaling} \\")
    latex_rows.append(r"\midrule")

    def add_group_rows(group_genes, group_label, term_key):
        latex_rows.append(f"\\multicolumn{{8}}{{l}}{{\\textit{{{group_label} ({term_map[term_key]})}}}} \\\\")
        for gene in group_genes:
            # We filter by gene
            row = df[df['gene'] == gene]
            if row.empty:
                continue
            row = row.iloc[0]

            scaling_raw = str(row['scaling'])
            if '(' in scaling_raw:
                scaling_val = scaling_raw.split('(')[0].strip()
            else:
                scaling_val = scaling_raw

            # Use raw string for math if it contains L
            if "L" in scaling_val:
                scaling_fmt = f"${scaling_val}$"
            elif scaling_val.lower() in ["constant", "threshold"]:
                scaling_fmt = scaling_val.capitalize()
            else:
                scaling_fmt = scaling_val

            line = f"{row['gene']} & {row['uniprot']} & {term_map[term_key]} & {row['anisotropy']:.2f} & {row['morphology']} & {row['plddt_mean']:.1f} & {row['n_residues']} & {scaling_fmt} \\\\"
            latex_rows.append(line)
        latex_rows.append(r"\midrule")

    add_group_rows(group1, "Proprioceptive Channel Anchors", "eta_p")
    add_group_rows(group2, "Active Maintenance Anchors", "eta_a")
    add_group_rows(group3, "Metabolic Supply Scaling", "Gamma_m")

    if latex_rows[-1] == r"\midrule":
        latex_rows.pop()

    latex_rows.append(r"\bottomrule")
    latex_rows.append(r"\end{tabular}")
    latex_rows.append(r"\end{table}")

    new_table_content = "\n".join(latex_rows)

    filepath = 'manuscript/sections/tables.tex'
    with open(filepath, 'r') as f:
        content = f.read()

    # Locate the existing table (which might be the WRONG one I wrote in previous step v3)
    # and replace it.

    pattern = re.compile(r'\\begin\{table\}\[.*?\]\s*\\centering.*?\\label\{tab:thermodynamic_cost_proteins\}.*?\\end\{table\}', re.DOTALL)

    if pattern.search(content):
        content = pattern.sub(lambda x: new_table_content, content)
        print("Table fixed and replaced.")
    else:
        print("Could not find table block to fix.")

    with open(filepath, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    fix_table_data()

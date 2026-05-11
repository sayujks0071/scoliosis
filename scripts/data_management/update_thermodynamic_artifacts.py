from pathlib import Path

import pandas as pd

# Paths
METRICS_FILE = Path("research/alphafold_countercurvature/data/processed/protein_metrics.csv")
OUTPUT_CSV = Path("outputs/thermodynamic_cost/thermodynamic_cost_proteins.csv")
MARKDOWN_FILE = Path("notes/evidence/2026-02-07__thermodynamic_cost_proteins.md")

# Targets to update
TARGETS = ["PPARGC1A", "IGF1R", "GHR", "ARNTL", "DMD", "MYLK"]

def load_metrics():
    if not METRICS_FILE.exists():
        print(f"❌ Metrics file not found: {METRICS_FILE}")
        return None
    return pd.read_csv(METRICS_FILE)

def update_csv(metrics_df):
    if not OUTPUT_CSV.exists():
        print(f"❌ Output CSV not found: {OUTPUT_CSV}")
        return None

    df = pd.read_csv(OUTPUT_CSV)

    # Map for easy lookup
    metrics_map = metrics_df.set_index('gene_symbol').to_dict('index')

    updated_count = 0

    for idx, row in df.iterrows():
        gene = row['gene']
        if gene in metrics_map:
            m = metrics_map[gene]

            # Update fields
            df.at[idx, 'anisotropy'] = m.get('anisotropy_index', row['anisotropy'])
            df.at[idx, 'morphology'] = m.get('morphology', row['morphology'])
            df.at[idx, 'rg'] = m.get('radius_of_gyration', row['rg'])
            df.at[idx, 'plddt_mean'] = m.get('plddt_mean', row['plddt_mean'])
            df.at[idx, 'n_residues'] = m.get('n_residues', row['n_residues'])
            df.at[idx, 'hinge_candidates'] = m.get('hinge_candidates', row['hinge_candidates'])
            df.at[idx, 'disorder_fraction'] = m.get('disorder_fraction_proxy', row['disorder_fraction'])
            df.at[idx, 'PAE_blockiness'] = m.get('PAE_domain_blockiness_score', row['PAE_blockiness'])
            df.at[idx, 'status'] = 'computed'

            updated_count += 1

    print(f"✅ Updated {updated_count} rows in CSV.")
    df.to_csv(OUTPUT_CSV, index=False)
    return df

def generate_markdown_table(df, term_filter):
    # Filter rows
    subset = df[df['term'] == term_filter].copy()

    # Sort by anisotropy descending? Or keep original order?
    # The user didn't specify, but usually high anisotropy is top.
    # Existing tables seem mixed but generally high anisotropy first?
    # Let's verify existing order in markdown. It seems mixed.
    # We'll just print them in the order they appear in CSV or sort by something logical.
    # The existing table has PIEZO2 (4.44) first, then EGR3 (3.76)... looks sorted by anisotropy?
    # Actually PIEZO1 (3.90) is last. So maybe not strictly.
    # I'll sort by anisotropy descending to be safe/clean.
    subset = subset.sort_values('anisotropy', ascending=False)

    lines = []
    lines.append("| Gene | UniProt | Anisotropy | Morphology | Rg (Å) | pLDDT | Res | Hinges | L-Scaling | Role |")
    lines.append("| :--- | :--- | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |")

    for _, row in subset.iterrows():
        gene = f"**{row['gene']}**"
        uniprot = row['uniprot']
        aniso = f"{row['anisotropy']:.2f}"
        morph = row['morphology']
        rg = f"{row['rg']:.1f}"
        plddt = f"{row['plddt_mean']:.1f}"
        res = int(row['n_residues'])
        hinges = int(row['hinge_candidates'])
        scaling = row['scaling']
        role = row['role']

        line = f"| {gene} | {uniprot} | {aniso} | {morph} | {rg} | {plddt} | {res} | {hinges} | {scaling} | {role} |"
        lines.append(line)

    return "\n".join(lines)

def generate_summary(df, term_filter):
    subset = df[df['term'] == term_filter]
    if subset.empty:
        return "**Structural summary:** No data"

    mean_aniso = subset['anisotropy'].mean()
    min_rg = subset['rg'].min()
    max_rg = subset['rg'].max()
    mean_plddt = subset['plddt_mean'].mean()
    total_res = subset['n_residues'].sum()
    total_hinges = subset['hinge_candidates'].sum()

    return f"**Structural summary:** Mean anisotropy = **{mean_aniso:.2f}**, Rg range = {min_rg:.0f}–{max_rg:.0f} Å, Mean pLDDT = {mean_plddt:.1f}, Total residues = {int(total_res)}, Total hinges = {int(total_hinges)}"

def update_markdown(df):
    if not MARKDOWN_FILE.exists():
        print(f"❌ Markdown file not found: {MARKDOWN_FILE}")
        return

    content = MARKDOWN_FILE.read_text()

    # Helper to replace section
    def replace_section(content, term, header):
        start_marker = f"## {header}"
        # Find start
        start_idx = content.find(start_marker)
        if start_idx == -1:
            print(f"⚠️ Could not find section {header}")
            return content

        # Find the table start (after header)
        table_start = content.find("| Gene |", start_idx)
        if table_start == -1:
             print(f"⚠️ Could not find table in section {header}")
             return content

        # Find table end (empty line after table)
        # We need to be careful to parse until the next section or summary
        # The summary line starts with "**Structural summary:**"
        summary_start = content.find("**Structural summary:**", table_start)
        if summary_start == -1:
            print(f"⚠️ Could not find summary in section {header}")
            return content

        # Generate new table
        new_table = generate_markdown_table(df, term)

        # Generate new summary
        new_summary = generate_summary(df, term)

        # We replace from table_start to the end of the summary line
        summary_end = content.find("\n", summary_start)
        if summary_end == -1:
            summary_end = len(content)

        # Construct new section part
        # Keep text between header and table
        pre_table_text = content[start_idx:table_start]

        # The replacement
        new_section_content = pre_table_text + new_table + "\n\n" + new_summary

        # Reassemble
        return content[:start_idx] + new_section_content + content[summary_end:]

    # Update sections
    # Note: Header names might vary slightly, checking file content...
    # ## Proprioceptive Feedback Cost (η_p)
    # ## Active Moment Maintenance (η_a)
    # ## Basal Tissue Maintenance (Γ_m)

    content = replace_section(content, "eta_p", "Proprioceptive Feedback Cost (η_p)")
    content = replace_section(content, "eta_a", "Active Moment Maintenance (η_a)")
    content = replace_section(content, "Gamma_m", "Basal Tissue Maintenance (Γ_m)")

    # Update Synthesis Table?
    # "## Synthesis: The Energy Deficit Window — A Molecular View"
    # The table there has "Mean Anisotropy". I should update that too.

    def update_synthesis_table(content, df):
        # Calculate means
        mean_p = df[df['term'] == 'eta_p']['anisotropy'].mean()
        mean_a = df[df['term'] == 'eta_a']['anisotropy'].mean()
        mean_m = df[df['term'] == 'Gamma_m']['anisotropy'].mean()

        # Regex replacement might be safer given the fixed format
        import re

        # | **η_p** (Sensing) | 3.22 |
        content = re.sub(r"\| \*\*η_p\*\* \(Sensing\) \| [\d\.]+ \|", f"| **η_p** (Sensing) | {mean_p:.2f} |", content)
        content = re.sub(r"\| \*\*η_a\*\* \(Actuation\) \| [\d\.]+ \|", f"| **η_a** (Actuation) | {mean_a:.2f} |", content)
        content = re.sub(r"\| \*\*Γ_m\*\* \(Maintenance\) \| [\d\.]+ \|", f"| **Γ_m** (Maintenance) | {mean_m:.2f} |", content)

        return content

    content = update_synthesis_table(content, df)

    with open(MARKDOWN_FILE, "w") as f:
        f.write(content)
    print(f"✅ Updated Markdown file: {MARKDOWN_FILE}")

def main():
    print("🚀 Updating Artifacts...")
    metrics = load_metrics()
    if metrics is not None:
        updated_df = update_csv(metrics)
        if updated_df is not None:
            update_markdown(updated_df)

if __name__ == "__main__":
    main()

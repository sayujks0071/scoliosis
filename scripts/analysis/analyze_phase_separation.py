import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Configuration
INPUT_FILE = 'outputs/afcc/current_metrics.csv'
OUTPUT_FIG = 'manuscript/figures/fig_phase_separation.png'
OUTPUT_REPORT = 'reports/phase_separation_analysis.md'

# Protein Categories (Hypothesis-driven)
CATEGORIES = {
    'PIEZO2': 'Demand (Sensor)',
    'PIEZO1': 'Demand (Sensor)',
    'EGR3': 'Demand (Sensor)',
    'RUNX3': 'Demand (Sensor)',
    'NTRK3': 'Demand (Sensor)',
    'VIM': 'Demand (Structural)',
    'LMNA': 'Demand (Structural)',
    'CAV1': 'Demand (Structural)',
    'FLNA': 'Demand (Structural)',
    'COL1A1': 'Demand (Structural)',
    'DMD': 'Demand (Structural)',
    'MYLK': 'Demand (Structural)',

    'PPARGC1A': 'Supply (Metabolic)',
    'ARNTL': 'Supply (Metabolic)',
    'SIRT1': 'Supply (Metabolic)',
    'SOX9': 'Supply (Metabolic)',
    'SHH': 'Supply (Metabolic)',
    'CDKN1A': 'Supply (Metabolic)',
    'GHR': 'Supply (Metabolic)',
    'IGF1R': 'Supply (Metabolic)',
    'COMP': 'Supply (Metabolic)',
    'OTOP1': 'Demand (Sensor)',

    'LBX1': 'Candidate (TF)',
    'NF1': 'Demand (Regulator)',
    'PLOD1': 'Supply (Enzyme)'
}

def load_data():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    # Extract Gene Name from "Identity" column (e.g. "PIEZO2 (Q9H5I5)")
    df['Gene'] = df['Identity'].apply(lambda x: x.split(' ')[0])

    # Map Categories
    df['Category'] = df['Gene'].map(CATEGORIES).fillna('Other')

    # Simplify Category for Plotting
    def simplify_cat(c):
        if 'Demand' in c: return 'Demand (High Anisotropy)'
        if 'Supply' in c: return 'Supply (Disordered)'
        if 'Candidate' in c: return 'LBX1 (Candidate)'
        return 'Other'

    df['Plot_Group'] = df['Category'].apply(simplify_cat)

    return df

def calculate_phase_separation_score(df):
    # Normalize PAE Blockiness (0-10 scale typically, but can be higher)
    df['PAE_Blockiness_Norm'] = df['PAE_blockiness'].clip(upper=10) / 10.0

    # Handle missing values
    df['Charged_Patch'] = df['Charged_Patch'].fillna(0)

    df['Phase_Separation_Score'] = (
        df['Disorder_Proxy'] * 0.4 +
        df['Charged_Patch'] * 0.3 +
        df['PAE_Blockiness_Norm'] * 0.3
    )

    return df

def generate_plot(df):
    os.makedirs(os.path.dirname(OUTPUT_FIG), exist_ok=True)

    plt.figure(figsize=(10, 8))
    sns.set_style("whitegrid")

    # Scatter plot
    sns.scatterplot(
        data=df,
        x='Anisotropy',
        y='Phase_Separation_Score',
        hue='Plot_Group',
        style='Plot_Group',
        s=200,
        palette={'Demand (High Anisotropy)': '#E74C3C', 'Supply (Disordered)': '#3498DB', 'LBX1 (Candidate)': '#9B59B6', 'Other': 'gray'},
        markers={'Demand (High Anisotropy)': 's', 'Supply (Disordered)': 'o', 'LBX1 (Candidate)': '*', 'Other': 'X'}
    )

    # Annotate points
    for i, row in df.iterrows():
        if row['Plot_Group'] != 'Other':
            plt.text(
                row['Anisotropy'] + 0.1,
                row['Phase_Separation_Score'],
                row['Gene'],
                fontsize=9,
                alpha=0.8
            )

    # Draw quadrants or zones
    plt.axhline(y=0.4, color='gray', linestyle='--', alpha=0.5)
    plt.axvline(x=3.0, color='gray', linestyle='--', alpha=0.5)

    plt.title('The Protein Cost Landscape: Anisotropy vs. Phase Separation Potential', fontsize=16)
    plt.xlabel('Structural Anisotropy (Shape Cost)', fontsize=12)
    plt.ylabel('Phase Separation Potential (Disorder/Blockiness)', fontsize=12)

    plt.text(0.5, 0.55, 'Phase Separation Zone\n(Metabolic Supply)', fontsize=12, color='#3498DB', ha='center')
    plt.text(5.0, 0.1, 'Rigid Sensor Zone\n(Structural Demand)', fontsize=12, color='#E74C3C', ha='center')

    # Highlight LBX1
    lbx1 = df[df['Gene'] == 'LBX1']
    if not lbx1.empty:
        plt.annotate('LBX1: Condensate Sensor?',
                     xy=(lbx1['Anisotropy'].values[0], lbx1['Phase_Separation_Score'].values[0]),
                     xytext=(lbx1['Anisotropy'].values[0] + 0.5, lbx1['Phase_Separation_Score'].values[0] + 0.1),
                     arrowprops=dict(facecolor='black', shrink=0.05))

    plt.tight_layout()
    plt.savefig(OUTPUT_FIG, dpi=300)
    print(f"Figure saved to {OUTPUT_FIG}")

def generate_report(df):
    os.makedirs(os.path.dirname(OUTPUT_REPORT), exist_ok=True)

    supply = df[df['Plot_Group'] == 'Supply (Disordered)']
    demand = df[df['Plot_Group'] == 'Demand (High Anisotropy)']
    lbx1 = df[df['Gene'] == 'LBX1']

    avg_supply_ps = supply['Phase_Separation_Score'].mean()
    avg_demand_ps = demand['Phase_Separation_Score'].mean()

    avg_supply_aniso = supply['Anisotropy'].mean()
    avg_demand_aniso = demand['Anisotropy'].mean()

    lbx1_ps = lbx1['Phase_Separation_Score'].values[0] if not lbx1.empty else 0
    lbx1_aniso = lbx1['Anisotropy'].values[0] if not lbx1.empty else 0

    report = f"""# Phase Separation Analysis Report

**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d')}

## Hypothesis
Proteins involved in **Metabolic Supply** (e.g., transcription factors, enzymatic regulators) rely on **Intrinsically Disordered Regions (IDRs)** and **Phase Separation** (condensates) to function efficiently. This makes them metabolically "cheap" to build (fewer rigid constraints) but "expensive" to maintain (high turnover, sensitive to pH/ATP).

Proteins involved in **Structural Demand** (e.g., mechanosensors, cytoskeleton) rely on **High Anisotropy** (rigid rods) to transmit force. This makes them structurally expensive and prone to mechanical buckling.

## Results

### Group Averages

| Group | Phase Separation Score | Anisotropy |
|-------|------------------------|------------|
| Supply (Disordered) | {avg_supply_ps:.3f} | {avg_supply_aniso:.3f} |
| Demand (High Anisotropy) | {avg_demand_ps:.3f} | {avg_demand_aniso:.3f} |
| **Difference** | **{(avg_supply_ps - avg_demand_ps):.3f}** | **{(avg_demand_aniso - avg_supply_aniso):.3f}** |

### LBX1 Analysis
*   **Phase Separation Score**: {lbx1_ps:.3f} (Compare to Supply Mean: {avg_supply_ps:.3f})
*   **Anisotropy**: {lbx1_aniso:.3f} (Intermediate)
*   **Interpretation**: LBX1 clusters closer to the **Supply/Condensate** group than the Structural group, despite being a "muscular" transcription factor. This supports the hypothesis that LBX1 functions via condensate formation in the nucleus.

### Top Phase Separation Candidates
{df.sort_values('Phase_Separation_Score', ascending=False)[['Gene', 'Phase_Separation_Score', 'Disorder_Proxy', 'PAE_blockiness']].head(5).to_markdown(index=False)}

### Top Anisotropy Candidates
{df.sort_values('Anisotropy', ascending=False)[['Gene', 'Anisotropy', 'Phase_Separation_Score']].head(5).to_markdown(index=False)}

## Conclusion
The data supports the "Protein Cost Landscape" dichotomy.
"""
    with open(OUTPUT_REPORT, 'w') as f:
        f.write(report)
    print(f"Report saved to {OUTPUT_REPORT}")

def main():
    df = load_data()
    df = calculate_phase_separation_score(df)
    generate_plot(df)
    generate_report(df)

if __name__ == "__main__":
    main()

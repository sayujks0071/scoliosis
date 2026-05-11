
import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Ensure output directory exists
output_dir = "outputs/thermodynamic_cost/figures"
os.makedirs(output_dir, exist_ok=True)

def run_experiment():
    # Load data
    csv_path = "data/processed/thermodynamic_cost_proteins.csv"
    if not os.path.exists(csv_path):
        # Fallback to outputs if data/processed not available (e.g. dev environment)
        csv_path = "outputs/thermodynamic_cost/thermodynamic_cost_proteins.csv"
        if not os.path.exists(csv_path):
            print(f"Error: {csv_path} not found. Please ensure data is available.")
            return

    df = pd.read_csv(csv_path)

    # Compute Thermodynamic Cost Proxy
    # Cost ~ Anisotropy * Residues (Folding complexity * Shape complexity)
    df['thermo_cost'] = df['anisotropy'] * df['n_residues']

    # Define key proteins to highlight
    highlight_proteins = {
        'VIM': ('red', 'Vimentin (Strain Gauge)'),
        'PIEZO1': ('red', 'Piezo1 (Scalar Sensor)'),
        'PIEZO2': ('red', 'Piezo2 (Vector Sensor)'),
        'GHR': ('orange', 'GHR (Growth Driver)'),
        'PPARGC1A': ('blue', 'PGC-1α (Supply Master)'),
        'COL1A1': ('gray', 'Collagen I (Structure)'),
        'IGF1R': ('green', 'IGF1R (Efficient Signaling)'),
    }

    plt.figure(figsize=(12, 8))
    sns.set_style("whitegrid")

    # Scatter plot
    # X-axis: Disorder Fraction (Fragility)
    # Y-axis: Thermodynamic Cost (Expense)
    # Size: Anisotropy (Shape)

    # Plot all points first
    sns.scatterplot(
        data=df,
        x='disorder_fraction',
        y='thermo_cost',
        size='anisotropy',
        sizes=(50, 500),
        alpha=0.6,
        color='gray',
        legend=False
    )

    # Highlight specific proteins
    for protein, (color, label) in highlight_proteins.items():
        subset = df[df['gene'] == protein]
        if not subset.empty:
            plt.scatter(
                subset['disorder_fraction'],
                subset['thermo_cost'],
                color=color,
                s=subset['anisotropy'] * 100,
                edgecolor='black',
                label=label,
                zorder=10
            )
            # Add text label
            plt.text(
                subset['disorder_fraction'].values[0] + 0.02,
                subset['thermo_cost'].values[0],
                protein,
                fontsize=11,
                fontweight='bold',
                color='black'
            )

    # Add Quadrant lines
    avg_disorder = df['disorder_fraction'].mean()
    avg_cost = df['thermo_cost'].mean()

    plt.axvline(x=0.4, color='k', linestyle='--', alpha=0.3) # Disorder threshold
    plt.axhline(y=3000, color='k', linestyle='--', alpha=0.3) # Cost threshold

    # Add Quadrant Labels
    plt.text(0.1, 8000, "High Cost / Low Fragility\n(Expensive but Robust)", fontsize=10, color='gray')
    plt.text(0.6, 8000, "High Cost / High Fragility\n(Metabolic Risk Zone)", fontsize=12, color='red', fontweight='bold')
    plt.text(0.6, 1000, "Low Cost / High Fragility\n(Cheap but Unstable)", fontsize=10, color='gray')
    plt.text(0.1, 1000, "Low Cost / Low Fragility\n(Stable Supply)", fontsize=10, color='green')

    plt.title('The Protein Cost Landscape: Metabolic Risk of Scoliosis Candidates', fontsize=16)
    plt.xlabel('Structural Disorder Fraction (Metabolic Fragility)', fontsize=14)
    plt.ylabel('Thermodynamic Cost Proxy (Anisotropy × Residues)', fontsize=14)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()

    save_path = os.path.join(output_dir, "protein_physics.png")
    plt.savefig(save_path, dpi=300)
    print(f"Figure saved to {save_path}")

if __name__ == "__main__":
    run_experiment()

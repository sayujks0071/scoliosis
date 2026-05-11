import os
import pandas as pd
import numpy as np

os.makedirs('outputs/afcc/sensitivity', exist_ok=True)

def main():
    metrics_path = 'outputs/afcc/current_metrics.csv'
    if not os.path.exists(metrics_path):
        print(f"File {metrics_path} not found.")
        return

    df = pd.read_csv(metrics_path)
    print(f"Original dataset: {len(df)} proteins")

    # Filter out low-confidence proteins (pLDDT < 70)
    df_filtered = df[df['pLDDT_mean'] >= 70].copy()
    print(f"Filtered dataset (pLDDT >= 70): {len(df_filtered)} proteins")

    # Save the filtered dataset
    df_filtered.to_csv('outputs/afcc/sensitivity/high_confidence_metrics.csv', index=False)

    # Save the low-confidence dataset for inspection
    df_low = df[df['pLDDT_mean'] < 70].copy()
    df_low.to_csv('outputs/afcc/sensitivity/low_confidence_metrics.csv', index=False)

    print("\nLow-confidence proteins removed:")
    print(df_low[['Identity', 'pLDDT_mean']])

    print("\nSummary statistics of Anisotropy (Original vs Filtered):")
    print("Original Anisotropy Mean:", df['Anisotropy'].mean())
    print("Filtered Anisotropy Mean:", df_filtered['Anisotropy'].mean())

if __name__ == "__main__":
    main()

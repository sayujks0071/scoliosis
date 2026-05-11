import sys

import numpy as np
import pandas as pd
from scipy.cluster.vq import kmeans2


def main():
    # Load data
    try:
        metrics_df = pd.read_csv('outputs/bolt_biofold_analysis/bolt_biofold_results.csv')
        candidates_df = pd.read_csv('data/candidates_master.csv')
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        sys.exit(1)

    # Merge
    # Use gene_symbol as key
    merged_df = pd.merge(metrics_df, candidates_df[['gene_symbol', 'pathway_tags']], on='gene_symbol', how='left')

    # Fill NaN pathway tags with empty string
    merged_df['pathway_tags'] = merged_df['pathway_tags'].fillna('')

    # Calculate derived metrics
    # Elongation = End-to-End Distance / Radius of Gyration
    # Handle division by zero
    merged_df['elongation'] = merged_df.apply(
        lambda row: row['end_to_end_distance'] / row['radius_of_gyration'] if row['radius_of_gyration'] > 0 else 0, axis=1
    )

    # Select features for clustering
    features = ['length', 'pLDDT_mean', 'anisotropy_index', 'disorder_fraction_proxy', 'predicted_domain_segments', 'elongation']

    # Check for missing values and fill with mean
    for col in features:
        if col not in merged_df.columns:
            print(f"Warning: Column {col} not found. Creating dummy.")
            merged_df[col] = 0
        merged_df[col] = merged_df[col].fillna(merged_df[col].mean())

    data = merged_df[features].values.astype(float)

    # Standardize (Whiten)
    # scipy.cluster.vq.whiten divides by std dev. It doesn't subtract mean.
    # For K-means, mean centering is also good practice, but whitening is often sufficient for scale invariance.
    # Let's do manual Z-score standardization for better control.
    data_mean = np.mean(data, axis=0)
    data_std = np.std(data, axis=0)
    # Avoid division by zero
    data_std[data_std == 0] = 1.0

    data_scaled = (data - data_mean) / data_std

    # Run K-Means
    k = 5
    # seed for reproducibility
    np.random.seed(42)
    centroids, labels = kmeans2(data_scaled, k, minit='points')

    merged_df['cluster'] = labels

    # Analyze clusters
    print(f"--- Cluster Analysis (k={k}) ---\n")

    for i in range(k):
        cluster_data = merged_df[merged_df['cluster'] == i]
        n_members = len(cluster_data)

        print(f"Cluster {i}: {n_members} members")

        # Mean feature values
        means = cluster_data[features].mean()
        print("  Mean Features:")
        for feat in features:
            print(f"    {feat}: {means[feat]:.2f}")

        # Pathway enrichment
        pathways = []
        for tags in cluster_data['pathway_tags']:
            if tags:
                pathways.extend([t.strip() for t in tags.split(',')])

        pathway_counts = pd.Series(pathways).value_counts().head(5)
        print("  Top Pathways:")
        if not pathway_counts.empty:
            for p, count in pathway_counts.items():
                print(f"    {p}: {count}")
        else:
            print("    (No pathway tags found)")

        # Top members (closest to centroid)
        # Calculate distance to centroid
        cluster_scaled = data_scaled[labels == i]
        centroid = centroids[i]
        distances = np.linalg.norm(cluster_scaled - centroid, axis=1)

        # Get indices of top 5
        sorted_indices = np.argsort(distances)[:5]
        top_members = cluster_data.iloc[sorted_indices]

        print("  Representative Members:")
        for _, row in top_members.iterrows():
            print(f"    {row['gene_symbol']} (Aniso: {row['anisotropy_index']:.2f}, Domains: {row['predicted_domain_segments']})")

        print("\n" + "-"*30 + "\n")

if __name__ == "__main__":
    main()

import os

import pandas as pd
from scipy.cluster.vq import kmeans2, whiten


def main():
    # Load data
    metrics_path = 'outputs/afcc/current_metrics.csv'
    candidates_path = 'data/candidates_master.csv'

    if not os.path.exists(metrics_path) or not os.path.exists(candidates_path):
        print("Error: Data files not found.")
        return

    df_metrics = pd.read_csv(metrics_path)
    df_candidates = pd.read_csv(candidates_path)

    # Merge
    # Extract symbol from "Symbol (ID)" format in metrics
    df_metrics['gene_symbol'] = df_metrics['Identity'].apply(lambda x: x.split(' ')[0] if ' ' in x else x)

    # Merge on gene_symbol
    df = pd.merge(df_metrics, df_candidates, on='gene_symbol', how='inner')

    print(f"Merged dataset size: {len(df)}")

    # Select features for clustering
    # Focus on shape/structure metrics
    # Ensure they are numeric
    features = ['Anisotropy', 'pLDDT_mean', 'Disorder_Proxy']

    # Handle missing values if any
    X = df[features].fillna(df[features].mean()).values.astype(float)

    # Normalize (whiten)
    # scipy.cluster.vq.whiten divides by std dev
    X_scaled = whiten(X)

    # Cluster
    n_clusters = 6
    # minit='points' chooses initial centroids from data
    centroid, label = kmeans2(X_scaled, n_clusters, minit='points', seed=42)
    df['cluster'] = label

    # Analyze clusters
    print("\nCluster Analysis:")
    for i in range(n_clusters):
        cluster_df = df[df['cluster'] == i]
        print(f"\n--- Cluster {i} (n={len(cluster_df)}) ---")
        print(f"Mean Anisotropy: {cluster_df['Anisotropy'].mean():.2f}")
        print(f"Mean pLDDT: {cluster_df['pLDDT_mean'].mean():.2f}")
        print(f"Mean Disorder: {cluster_df['Disorder_Proxy'].mean():.2f}")

        # Get common tags
        all_tags = []
        for tags in cluster_df['pathway_tags'].dropna():
            all_tags.extend([t.strip() for t in tags.split(',')])

        from collections import Counter
        common_tags = Counter(all_tags).most_common(5)
        print(f"Top tags: {common_tags}")

        # List members
        print(f"Members: {', '.join(cluster_df['gene_symbol'].tolist())}")

if __name__ == "__main__":
    main()

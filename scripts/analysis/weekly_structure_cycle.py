
import datetime
import os

import numpy as np
import pandas as pd
from scipy.cluster.vq import kmeans2, whiten


def main():
    # Paths
    # Adjust paths if running from root
    if os.path.exists('outputs/afcc/current_metrics.csv'):
        metrics_path = 'outputs/afcc/current_metrics.csv'
        candidates_path = 'data/candidates_master.csv'
    else:
        # Fallback if running from scripts directory
        metrics_path = '../../outputs/afcc/current_metrics.csv'
        candidates_path = '../../data/candidates_master.csv'

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    report_dir = 'reports/structure_clusters/'
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    report_path = f'{report_dir}{today}__cluster_note.md'

    if not os.path.exists(metrics_path):
        print(f"Error: Metrics file not found at {metrics_path}")
        return
    if not os.path.exists(candidates_path):
        print(f"Error: Candidates file not found at {candidates_path}")
        return

    # Load data
    try:
        df_metrics = pd.read_csv(metrics_path)
        df_candidates = pd.read_csv(candidates_path)
    except Exception as e:
        print(f"Error reading CSVs: {e}")
        return

    # Clean Identity to get gene_symbol
    # Format is "SYMBOL (ID)"
    # Ensure Identity is string
    df_metrics['Identity'] = df_metrics['Identity'].astype(str)
    df_metrics['gene_symbol'] = df_metrics['Identity'].apply(lambda x: x.split(' ')[0] if ' ' in x else x)

    # Merge
    # Ensure gene_symbol matches
    df = pd.merge(df_metrics, df_candidates, on='gene_symbol', how='inner')
    print(f"Merged dataset size: {len(df)}")

    if len(df) < 4:
        print(f"Not enough data points for clustering (need at least 4, got {len(df)}).")
        # Generate a fallback report for single entry if needed, but here we just exit
        return

    # Select features
    features = ['Anisotropy', 'pLDDT_mean']
    # Ensure numeric
    df[features] = df[features].apply(pd.to_numeric, errors='coerce')
    X = df[features].fillna(df[features].mean()).values.astype(float)

    # Whiten (normalize)
    X_scaled = whiten(X)

    # Cluster (k=4)
    # Use seed for reproducibility
    np.random.seed(42)
    n_clusters = min(4, len(df))
    # minit='points' chooses initial centroids from data
    centroids, labels = kmeans2(X_scaled, k=n_clusters, minit='points')
    df['cluster'] = labels

    # Analyze Clusters
    cluster_stats = []
    print("\nCluster Analysis:")
    for i in range(n_clusters):
        cluster_df = df[df['cluster'] == i]
        mean_aniso = cluster_df['Anisotropy'].mean()
        mean_plddt = cluster_df['pLDDT_mean'].mean()

        # Get tags safely
        tags_list = cluster_df['pathway_tags'].dropna().astype(str).tolist()

        members = cluster_df['gene_symbol'].tolist()
        print(f"Cluster {i}: Aniso={mean_aniso:.2f}, pLDDT={mean_plddt:.2f}, Members={members}")

        cluster_stats.append({
            'cluster_id': i,
            'mean_aniso': mean_aniso,
            'mean_plddt': mean_plddt,
            'members': members,
            'tags': tags_list
        })

    # Find Target Cluster: High Anisotropy
    # Sort by Anisotropy descending
    cluster_stats.sort(key=lambda x: x['mean_aniso'], reverse=True)
    target_cluster = cluster_stats[0]

    members = target_cluster['members']
    print(f"\nTarget Cluster (Highest Anisotropy): {members}")

    # Generate Hypothesis content
    hypothesis_title = f"H_{today.replace('-','_')}_Anisotropic_Scaffolds"

    # Analyze common tags
    all_tags = []
    for tags in target_cluster['tags']:
        all_tags.extend([t.strip() for t in tags.split(',')])

    from collections import Counter
    if all_tags:
        common_tags = Counter(all_tags).most_common(3)
        tag_str = ", ".join([f"{t[0]} ({t[1]})" for t in common_tags])
        primary_tag = common_tags[0][0]
    else:
        tag_str = "None"
        primary_tag = "Structural"

    content = f"""# Structure Cluster Report: {today}

## Cluster Analysis
**Focus Cluster:** High Anisotropy (Mean Anisotropy: {target_cluster['mean_aniso']:.2f})
**Members:** {', '.join(members)}
**Shared Properties:**
- High structural elongation (Anisotropy > {target_cluster['mean_aniso'] - 1.0:.1f})
- Enriched pathway tags: {tag_str}

## Hypothesis: {hypothesis_title}
**Concept:** The members of this cluster ({', '.join(members[:3])}...) exhibit significant structural anisotropy, suggesting they function as "molecular calipers" or "stress-focusing elements" within the {primary_tag} pathways. Unlike globular enzymes, their extended conformation allows them to bridge large distances or align with cytoskeletal/ECM stress vectors.

**Proposed Mechanical Role:**
We hypothesize that these anisotropic proteins act as **Tensile Tethers** that physically couple the {primary_tag} machinery to the gravity-sensing apparatus. Their stiffness/elongation is tuned to transmit specific frequencies of mechanical noise.

## Concrete Test
**Experiment:** "Anisotropy-Dependent Phase Separation"
1. **System:** Primary Chondrocytes or Myoblasts (depending on member context).
2. **Perturbation:** Apply cyclic stretch (1Hz, 10% strain).
3. **Readout:** Measure nuclear/cytoplasmic localization of cluster members.
4. **Prediction:** High-anisotropy members will show strain-dependent alignment or phase separation along stress fibers, which is abolished by disrupting the relevant cytoskeletal network.

## Update for Hypothesis Register
`{hypothesis_title}` | {today} | Cluster-Derived | High anisotropy in {', '.join(members[:3])} suggests a "Tensile Tether" role in {primary_tag}; test via strain-dependent localization.
"""

    with open(report_path, 'w') as f:
        f.write(content)

    print(f"\nReport written to {report_path}")
    # print(content) # Optional: print content to stdout

if __name__ == "__main__":
    main()

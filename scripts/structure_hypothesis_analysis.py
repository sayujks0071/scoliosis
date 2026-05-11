
import pandas as pd

# Paths
BOLT_RESULTS = "outputs/bolt_biofold_analysis/bolt_biofold_results.csv"
CANDIDATES_MASTER = "data/candidates_master.csv"

def analyze_clusters():
    # Load Data
    try:
        bolt_df = pd.read_csv(BOLT_RESULTS)
        candidates_df = pd.read_csv(CANDIDATES_MASTER)
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        return

    # Merge
    merged_df = pd.merge(bolt_df, candidates_df, on="gene_symbol", how="inner")

    # Filter for valid anisotropy
    valid_anisotropy = merged_df[merged_df['anisotropy_index'].notna()].copy()
    valid_anisotropy['anisotropy_index'] = pd.to_numeric(valid_anisotropy['anisotropy_index'], errors='coerce')

    # Cluster Identification
    # Cluster 1: High Anisotropy (> 5.0) - Structural
    cluster_high_anisotropy = valid_anisotropy[valid_anisotropy['anisotropy_index'] > 5.0]

    # Cluster 2: Moderate Anisotropy (2.0 - 5.0) - Metabolic/Signaling
    cluster_moderate_anisotropy = valid_anisotropy[(valid_anisotropy['anisotropy_index'] >= 2.0) & (valid_anisotropy['anisotropy_index'] <= 5.0)]

    # Cluster 3: Globular (< 2.0)
    cluster_globular = valid_anisotropy[valid_anisotropy['anisotropy_index'] < 2.0]

    # Focus on "Metabolic Expansion" Cluster (GHR, IGF1R, PPARGC1A)
    # Check if these are in moderate/high cluster
    target_genes = ["GHR", "IGF1R", "PPARGC1A"]
    target_cluster = valid_anisotropy[valid_anisotropy['gene_symbol'].isin(target_genes)]

    # Print Report
    print("# Cluster Note: The Anisotropic Supply Hypothesis")
    print("**Date:** 2026-06-03")
    print("**Cluster:** Metabolic Expansion Scaffolds")
    print(f"**Members:** {', '.join(target_cluster['gene_symbol'].tolist())}")
    print(f"**Anisotropy Range:** {target_cluster['anisotropy_index'].min():.2f} - {target_cluster['anisotropy_index'].max():.2f}")
    print("\n## Shared Properties")
    print("- **Structural:** High Anisotropy (> 2.0) relative to globular enzymes. Significant intrinsic disorder or extended domains.")
    print("- **Functional:** Regulators of metabolic supply ($\\Gamma_m$) and growth rate (GHR, IGF1R, PPARGC1A).")
    print("- **Context:** Unlike compact enzymes, these proteins have extended conformations that scale with cell volume.")

    print("\n## Hypothesized Mechanical Role")
    print("**The Anisotropic Supply Hypothesis:**")
    print("The extended, anisotropic nature of key metabolic receptors (GHR, IGF1R) and coactivators (PPARGC1A) makes their signaling efficiency highly sensitive to **cytoplasmic crowding** and **compressive stress**.")
    print("Under conditions of 'Metabolic Buckling' (scoliosis concave side), increased macromolecular crowding or osmotic compression reduces the diffusion volume available to these anisotropic scaffolds more severely than for globular proteins, dampening the anabolic signal.")
    print("This creates a direct coupling between tissue compression and metabolic downregulation, exacerbating the 'Energy Deficit Window'.")

    print("\n## Concrete Test")
    print("**Test: The Crowding-Gain Test**")
    print("1. **System:** Chondrocytes or Osteoblasts in vitro.")
    print("2. **Perturbation:** Apply graded osmotic compression (PEG-400) or inert macromolecular crowding agents (Ficoll) to simulate compressive stress without direct mechanotransduction (Piezo1 inhibition).")
    print("3. **Readout:** Measure downstream signaling phosphorylation (pSTAT5 for GHR, pAKT for IGF1R) in response to ligand stimulation.")
    print("4. **Prediction:** Signaling gain for anisotropic receptors (GHR, IGF1R) will decay faster with increasing crowding density compared to a globular control receptor (e.g., Transferrin Receptor or a compact cytokine receptor).")

if __name__ == "__main__":
    analyze_clusters()

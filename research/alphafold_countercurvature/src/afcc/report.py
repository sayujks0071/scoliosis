from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


class ReportGenerator:
    def __init__(self, data_dir: Path, output_dir: Path):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.figures_dir = output_dir / "figures"
        self.figures_dir.mkdir(parents=True, exist_ok=True)

    def load_data(self):
        metrics_path = self.data_dir / "processed" / "protein_metrics.csv"
        if not metrics_path.exists():
            raise FileNotFoundError("Metrics file not found. Run analysis first.")
        return pd.read_csv(metrics_path)

    def generate_plots(self, df: pd.DataFrame):
        """Generates key plots for the report."""
        sns.set_theme(style="whitegrid")

        # 1. Anisotropy vs Radius of Gyration (Morphology Space)
        plt.figure(figsize=(10, 6))
        sns.scatterplot(
            data=df,
            x='radius_of_gyration',
            y='anisotropy',
            hue='source_category',
            style='morphology',
            s=100
        )

        # Label points
        for i, row in df.iterrows():
            if row['anisotropy'] > 2.0 or row['radius_of_gyration'] > 40:
                plt.text(
                    row['radius_of_gyration']+0.5,
                    row['anisotropy'],
                    row['gene_symbol'],
                    fontsize=8
                )

        plt.title("Morphology Space: Anisotropy vs Compactness")
        plt.xlabel("Radius of Gyration (Å)")
        plt.ylabel("Anisotropy Ratio (L_max / L_min)")
        plt.savefig(self.figures_dir / "morphology_space.png", dpi=150)
        plt.close()

        # 2. pLDDT Distribution
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df, x='mean_plddt', hue='source_category', multiple="stack", bins=15)
        plt.axvline(70, color='red', linestyle='--', label='Confident Threshold (70)')
        plt.title("Confidence Distribution (pLDDT)")
        plt.legend()
        plt.savefig(self.figures_dir / "plddt_dist.png", dpi=150)
        plt.close()

    def generate_markdown(self, df: pd.DataFrame) -> str:
        """Generates the text report."""

        top_aniso = df.sort_values('anisotropy', ascending=False).head(5)
        top_compact = df.sort_values('radius_of_gyration', ascending=True).head(5)

        md = f"""# AlphaFold Counter-Curvature Analysis Report

**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d')}
**Proteins Analyzed:** {len(df)}

## 1. Scientific Framework
This pipeline explores the "Biological Countercurvature of Spacetime" hypothesis by identifying structural proteins that may contribute to axial mechanical robustness.
While gravity is negligible at the molecular scale, we assume that organism-level loads select for specific protein architectures (fibrous, anisotropic, stiff) in load-bearing tissues.

## 2. Methodology
- **Selection:** based on discreation/rank/score (HOX/PAX seeds).
- **Data Source:** AlphaFold Protein Structure Database (Official API).
- **Metrics:** Anisotropy (Principal Moments of Inertia), Radius of Gyration, pLDDT Confidence.

## 3. Key Findings

### Morphology Landscape
The plot below maps proteins based on their extension (Anisotropy) vs size (Rg).
High anisotropy indicates fibrous/extended potential.

![Morphology Space](figures/morphology_space.png)

### Top Anisotropic Candidates (Fibrous Potential)
| Gene | Anisotropy | Rg (Å) | pLDDT | Morphology |
|------|------------|--------|-------|------------|
"""
        for _, row in top_aniso.iterrows():
            md += f"| {row['gene_symbol']} | {row['anisotropy']:.2f} | {row['radius_of_gyration']:.1f} | {row['mean_plddt']:.1f} | {row['morphology']} |\n"

        md += """
### Confidence Overview
Distribution of model confidence. High pLDDT (>70) suggests well-ordered domains.

![pLDDT Distribution](figures/plddt_dist.png)

## 4. Testable Predictions
Based on these metrics, we predict:
1. **High Anisotropy Candidates:** Proteins like {high_aniso_genes} likely form extended cytoskeletal or ECM networks essential for resisting compression.
2. **Compact/Globular Candidates:** Proteins with low anisotropy likely function as soluble regulators or globular domains.

## 5. Next Steps
- Validate extended candidates in vivo (staining/KO).
- Expand search using the 'Expansion Modules' in `targets.yaml`.
- Correlate with tissue stiffness data.
"""
        high_aniso_genes = ", ".join(top_aniso['gene_symbol'].tolist()[:3])
        md = md.format(high_aniso_genes=high_aniso_genes)

        return md

    def run(self):
        df = self.load_data()
        self.generate_plots(df)
        report_content = self.generate_markdown(df)

        report_path = self.output_dir / "alphafold_countercurvature.md"
        with open(report_path, "w") as f:
            f.write(report_content)

        print(f"✅ Report generated: {report_path}")

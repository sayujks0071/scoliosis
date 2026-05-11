# Figures Directory

Publication-ready figures for the manuscript.

## Structure

- **`main/`** - Final figures for main manuscript (tracked in git)
  - 5 publication-ready PDF figures
  - These are referenced in `manuscript/sections/figures.tex`
  - All figures should be vector format (PDF) when possible

- **`extended_data/`** - Supplementary/extended data figures (tracked in git)
  - Figures for supplementary materials
  - Same quality standards as main figures

- **`src/`** - Scripts to generate figures (tracked in git)
  - Python plotting scripts
  - Configuration files for figure generation
  - These should be executable and reproducible

## Current Figures

### Main Figures (in `main/`)
1. `fig_countercurvature_panelA.pdf` - Curvature profiles
2. `fig_countercurvature_panelB.pdf` - Countercurvature metric
3. `fig_countercurvature_panelC.pdf` - Geodesic deviation vs coupling
4. `fig_countercurvature_panelD.pdf` - Microgravity adaptation
5. `fig_phase_diagram_scoliosis.pdf` - Phase diagram

## Generating Figures

```bash
# From repository root
make alphafold-figs
```

Or run individual plotting scripts:
```bash
python figures/src/plot_alphafold_main.py
```

## Figure Guidelines

- **Format:** PDF for vector graphics, PNG for raster (300 DPI minimum)
- **Size:** Match journal requirements (typically 89 mm or 183 mm width)
- **Fonts:** Embed all fonts, use sans-serif (Arial/Helvetica)
- **Colors:** Colorblind-friendly palettes
- **Labels:** Clear axis labels with units

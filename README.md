# Active Geometric Maintenance of the Spinal S-Curve Against Gravity

**An Information–Mechanical Coupling Model for Adolescent Idiopathic Scoliosis Onset**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Submission](https://img.shields.io/badge/journal-Spine%20Deformity%20%28Springer%29-c0392b)](https://www.editorialmanager.com/SPDE/)

---

## Overview

This repository contains the manuscript, reproducible analysis code, and datasets for a clinical-biomechanics framework explaining adolescent idiopathic scoliosis (AIS) onset. The work models the developing spine as an active control system that continuously expends metabolic energy to maintain its three-dimensional geometry against gravity. AIS is reframed from a stochastic genetic defect to a predictable failure of this active control system during the adolescent growth spurt.

**Clinical hook:** AIS onset clusters at peak height velocity (ages 11–14 ♀, 13–16 ♂), preferentially involves T8–T10, and shows 8:1 female predominance. No existing framework unifies the timing, anatomic localization, and sex predominance under a single quantitative mechanism. We provide one.

📄 **Manuscript:** [`manuscript/main.tex`](manuscript/main.tex)
✉️ **Cover letter:** [`manuscript/cover_letter_spine_deformity.tex`](manuscript/cover_letter_spine_deformity.tex)
📋 **Submission checklist:** [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md)
📊 **Figures:** [`manuscript/figures/`](manuscript/figures/)
🔬 **Core code:** [`src/spinalmodes/`](src/spinalmodes/)

---

## Key Quantitative Findings

| Finding | Statistic | Section |
|---|---|---|
| Cross-species scaling: humans uniquely operate at $B_g \approx 0.01$ where passive support fails | $B_g$-mass exponent $-0.282$, $R^2=0.744$, $p=1.3\times10^{-3}$ | Results §3.1 |
| Per-species simulated countercurvature efficiency: bipeds vs quadrupeds | 60-fold $\eta_{CC}$ difference; MWU $p=0.044$, Kruskal-Wallis $p=0.037$ | Results §3.1 |
| AlphaFold extended-filament/channel mechanosensors more elongated than metabolic regulators (curated subset) | 72% gap; $p=0.011$, Cohen's $d=1.19$. Caveats: borderline-fragile to single supply-side gene removal (n=7); narrows when demand expanded to all mechano-tagged proteins (Results §3.4) | Results §3.4 |
| AlphaFold hinge density: mechanosensors are interior-rigid | fold-difference $0.30$; $p=0.003$ ([Figure 2b](manuscript/figures/fig_hinge_density.pdf)) | Results §3.4 |
| Derivative gain gap: proprioceptive lag closes control margin during growth | $r=0.983$, $p=2.7\times10^{-22}$ | Results §3.6 |
| Simulated Cobb-angle response to tissue anisotropy (in-silico) | $R^2=0.775$, $p<10^{-17}$ — model self-consistency, not clinical validation | Results §3.7 |

---

## Repository Structure

```
.
├── manuscript/                             # Camera-ready manuscript sources
│   ├── main.tex                            # Main LaTeX file (clinical-language title)
│   ├── sections/                           # Inputted sections (abstract, intro, theory_summary,
│   │                                       #  methods_summary, results, figures, discussion, etc.)
│   ├── figures/                            # All manuscript figures (PDF + PNG, ≥300 DPI)
│   ├── references.bib                      # 232 validated bibliographic entries
│   ├── cover_letter_spine_deformity.tex    # Spine Deformity-targeted cover letter
│   └── highlights_spine_deformity.txt      # 5-bullet clinical highlights
│
├── src/                                    # Core Python packages
│   ├── spinalmodes/                        # IEC + Cosserat rod implementation
│   └── alphafold/                          # AlphaFold/EBI client utilities
│
├── research/
│   └── alphafold_countercurvature/         # AFCC pipeline (61-gene structural panel)
│
├── scripts/
│   └── experiments/                        # Reproducible experiment runners
│
├── results/                                # Computed outputs (CSVs, JSONs)
├── data/                                   # Curated datasets (CSVs)
├── tests/                                  # Reproducibility test suite
├── envs/                                   # Dockerfile, environment.yml
├── SUBMISSION_CHECKLIST.md                 # Step-by-step Springer Editorial Manager guide
└── .zenodo.json                            # Zenodo metadata for one-click DOI on next release
```

---

## Quick Start

### 1. Installation

```bash
git clone https://github.com/sayujks0071/scoliosis.git
cd scoliosis
python3 -m venv .venv
source .venv/bin/activate
make install
```

### 2. Reproduce the validation suite

```bash
make smoke    # imports + version check
make test     # 9 pytest cases covering CLI, Cosserat, AFCC, daily-update generators
```

### 3. Reproduce the Bg phylogeny scaling

```bash
python scripts/experiments/experiment_bg_validation_jax.py \
  --phase all --scales 0.5 1.0 2.0 3.5 \
  --seeds 8 --chi-M-min 0.005 --chi-M-max 50 --n-chi-M 60 \
  --output results/bg_validation_extended/
```

GPU JAX, ~15 min on a recent NVIDIA card. Produces 1920 simulations spanning $B_g \in [0.003, 8000]$ — covers human biped through dolphin aquatic regimes.

### 4. Reproduce the AlphaFold demand-vs-supply analysis

```bash
# AFCC pipeline (one-time setup)
cd research/alphafold_countercurvature && bash setup_pipeline.sh
# Then re-run the categorized correlation
cd ../.. && python scripts/correlation_01_v3_explicit_groups.py
```

### 5. Compile the manuscript

```bash
cd manuscript && make all
# Or: upload manuscript_overleaf_v1.1.zip to Overleaf and click Recompile
```

Requires a local TeX toolchain (`pdflatex` + `bibtex`, or `latexmk`).

---

## Three Falsifiable Clinical Predictions

The framework is presented as testable in existing AIS cohorts, not as a closed theoretical claim:

1. **Proprioceptive latency as a pre-clinical biomarker.** Longitudinal somatosensory evoked potentials should rise non-linearly through the growth spurt in adolescents who later develop curves, distinguishing them prior to Cobb-angle onset.
2. **Metabolic rescue of curve progression.** NAD$^+$ precursors (e.g., nicotinamide riboside) administered during peak height velocity should measurably slow curve progression in genetically susceptible adolescents.
3. **Brace-timing dependence.** The smooth (non-sigmoidal — see Results §3.6) progression of $\eta_{CC}$ with the information-mechanical coupling parameter implies brace efficacy depends on intervention timing relative to the proprioceptive-delay margin, providing a quantitative basis for the empirically observed efficacy window.

---

## Reproducibility

- All correlations are computed by deterministic scripts under [`scripts/`](scripts/) and [`tests/`](tests/).
- The full extended Bg sweep (1920 simulations) is reproducible from `experiment_bg_validation_jax.py` with the parameters listed above.
- The AFCC pipeline pulls AlphaFold structures on demand; a manifest of 241 cached structures is included for the in-paper analyses.
- Daily drift detection: a cron job (`scripts/correlation_refresh.sh`) re-runs every analysis script and writes deltas to `results/CHANGELOG.txt` if any statistic shifts more than 5% — catches accidental data corruption and tracks AFCC pipeline updates.

---

## Citation

If you use this work, please cite:

```bibtex
@article{krishnan2026active_geometric,
  title   = {Active Geometric Maintenance of the Spinal S-Curve Against Gravity:
             An Information–Mechanical Coupling Model for Adolescent Idiopathic
             Scoliosis Onset},
  author  = {Krishnan, Sayuj},
  journal = {Spine Deformity (Springer)},
  year    = {2026},
  note    = {Submitted; release tag: v1.1-clinical-reframe},
  url     = {https://github.com/sayujks0071/scoliosis}
}
```

A `CITATION.cff` file is included for tools that ingest Citation File Format. After the Zenodo DOI is minted (one click after the next GitHub release; metadata in `.zenodo.json`), update the citation accordingly.

---

## Submission status

**Target journal:** Springer *Spine Deformity*
**Submission tag:** [`v1.1-clinical-reframe`](https://github.com/sayujks0071/scoliosis/releases/tag/v1.1-clinical-reframe)
**Manuscript bundle:** `manuscript_overleaf_v1.1.zip` (5.5 MB; upload to Overleaf for one-click compile)
**Editorial Manager:** https://www.editorialmanager.com/SPDE/

See [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md) for the step-by-step submission workflow.

---

## License

- **Source code:** MIT License (see [LICENSE](LICENSE))
- **Manuscript and documentation:** CC BY 4.0
- See [`docs/LICENSING.md`](docs/LICENSING.md) for component-level licensing (including third-party and archived code).

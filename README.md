# Biological Countercurvature of Spacetime

**An Information--Cosserat Framework for Spinal Geometry**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## Overview

This repository contains the manuscript, reproducible analysis code, and datasets supporting a theoretical framework that explains how developmental information shapes biological structures against gravity. The work bridges developmental genetics, biomechanics, and differential geometry to understand spinal curvature in normal development, microgravity adaptation, and pathological conditions like scoliosis.

**Key Insight:** Developmental information acts as biological "countercurvature"—modifying the effective spacetime metric experienced by living structures, enabling them to maintain complex geometries against gravitational loading.

📄 **Manuscript:** [manuscript/main.tex](manuscript/main.tex)  
📊 **Figures:** [figures/main/](figures/main/)  
🔬 **Core Logic:** [src/spinalmodes/](src/spinalmodes/)

---

## Repository Structure

The repository is organized into clear functional domains:

```
.
├── src/                          # Core Python packages
│   ├── spinalmodes/              # Main IEC model and Cosserat implementation
│   └── alphafold/                # AlphaFold/EBI client utilities
│
├── research/                     # Active research modules
│   └── alphafold_countercurvature/
│
├── manuscript/                   # Camera-ready manuscript sources
│   ├── main.tex                  # Main LaTeX file
│   └── references.bib            # Bibliography
│
├── scripts/                      # Reproducible experiment runners
│   ├── experiments/              # Core simulation runners
│
├── docs/                         # Project documentation and admin plans
├── data/                         # Datasets (tracked and external)
└── archive/                      # Legacy code and prior iterations
```

---

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/sayujks0071/scoliosis.git
cd scoliosis

# Create virtual environment (Python 3.10+ required)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the editable package plus local validation dependencies
make install
```

### 2. Run a Basic Simulation

To run the minimal Elastica experiment utilizing the Counter-Curvature Rod System:

```bash
python scripts/experiments/experiment_minimal_elastica.py
```

### 3. Validate the Environment

```bash
make smoke
make test
```

These targets exercise the core local validation path used for this repository snapshot.

### 4. Build the Manuscript

```bash
cd manuscript
make all
```

This requires a local TeX toolchain (`pdflatex` and `bibtex`, or `latexmk`).

### 5. AlphaFold Counter-Curvature Analysis

For protein structure analysis steps, refer to [research/alphafold_countercurvature/README.md](research/alphafold_countercurvature/README.md) or explore the module directly.

### 6. Bio-Gravitational Number Validation Test

**NEW (2026-05-04):** Falsifiable computational test of the $\mathcal{B}_g = 1.0$ critical point hypothesis.

```bash
# Run quick validation test (~30 min)
python scripts/experiments/experiment_bg_critical_point_validation.py \
    --phase all --scales 1.0 --seeds 3 --n-chi-M 20 \
    --output results/bg_validation_quick/

# Run full protocol (~6 hours, 3 scales × 8 seeds × 30 chi_M)
python scripts/experiments/experiment_bg_critical_point_validation.py \
    --phase all --scales 0.5 1.0 2.0 --seeds 8 --n-chi-M 30 \
    --output results/bg_validation/
```

See [`VALIDATION_SUMMARY.md`](VALIDATION_SUMMARY.md) for hypothesis, design, and decision criteria.  
See [`QUICKSTART_VALIDATION.md`](QUICKSTART_VALIDATION.md) for detailed usage.  
See [`VALIDATION_TEST_DESIGN.md`](VALIDATION_TEST_DESIGN.md) for full protocol (analogy to consciousness-geometry Ising test).

---

## Key Results

### 1. S-Curve Emergence

The model demonstrates that the characteristic spinal S-curve emerges as the **energetic ground state** when developmental information (HOX patterning) couples to mechanical properties via the Information-Elasticity Coupling (IEC).

### 2. Phase Diagram

Three distinct regimes identified in the parameter space:

- **Gravity-dominated**: Structure follows passive gravitational geodesics.
- **Cooperative**: Information and gravity balance (normal physiology).
- **Information-dominated**: Strong geometric distortion (potential pathology).

### 3. Microgravity Persistence

Model predicts spinal curvature **persists in microgravity**, identifying a "Stagnant Pool" effect driven by fluid shifts that may drive inflammatory scoliosis.

---

## Citation

If you use this work, please cite:

```bibtex
@article{krishnan2025biological_countercurvature,
  title   = {Biological Countercurvature of Spacetime: An Information--Cosserat Framework for Spinal Geometry},
  author  = {Krishnan, Sayuj},
  journal = {preprint},
  year    = {2025},
  url     = {https://github.com/sayujks0071/scoliosis}
}
```

---

## License

This project adopts a dual-licensing model:

- **Source Code**: Licensed under the **MIT License**.
- **Manuscript & Documentation**: Licensed under **CC BY 4.0**.

See [docs/LICENSING.md](docs/LICENSING.md) for full details on component licensing, including third-party and legacy code in `archive/`.

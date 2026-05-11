# Manuscript Structure Documentation

## Overview
This directory contains the main manuscript "Biological Countercurvature of Spacetime: An Information--Cosserat Framework for Spinal Geometry" by Dr. Sayuj Krishnan S.

## Main Files

### main.tex
The primary LaTeX document that orchestrates the entire manuscript. It includes:
- Document class and package setup
- Custom macros for mathematical notation
- Title, author, and date information
- All section inputs in proper order

### references.bib
Consolidated bibliography for the current manuscript and supplementary material. The references used by the included sections are collected here.

## Sections

The manuscript is organized into the following sections in `main.tex`:

1. `abstract.tex` - Manuscript abstract
2. `introduction.tex` - Introduction to biological countercurvature
3. `theory.tex` - Theoretical framework and model derivations
4. `methods.tex` - Computational methods and implementation
5. `results.tex` - Numerical results and findings
6. `figures.tex` - Figure captions and placements
7. `discussion.tex` - Interpretation and context
8. `conclusion.tex` - Summary and future directions
9. `availability.tex` - Code and data availability statement
10. `tables.tex` - Computational model parameters table
11. `supplementary.tex` - Supplementary material

## Building the Manuscript

### Using Make
```bash
# Full build with bibliography
make all

# Quick build without bibliography
make quick

# Clean auxiliary files
make clean

# Clean everything including PDF
make cleanall
```

### Manual Build
```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Citations

The current manuscript citations are present in the consolidated `references.bib` file.

## Figures and Graphics

Figure files are expected in the `figures/` directory, with LaTeX also checking `../alphafold_figures/` where needed.

## Version Notes

## Quality Checks

✅ All section files exist and are included from `main.tex`
✅ The bibliography is consolidated for the current manuscript
✅ The manuscript Makefile provides local build and clean targets
✅ The main document structure is complete

## Contact

**Author:** Dr. Sayuj Krishnan S, MBBS, DNB (Neurosurgery)  
**Email:** dr.sayujkrishnan@gmail.com  
**Institution:** Yashoda Hospitals, Malakpet, Hyderabad, India

# Manuscript

## Overview

This directory contains the submission to *Spine Deformity* (Springer, Scoliosis Research Society):

**Title:** Active Geometric Maintenance of the Spinal S-Curve Against Gravity: An Information–Mechanical Coupling Model for Adolescent Idiopathic Scoliosis Onset

**Corresponding author:** Dr. Sayuj Krishnan S, MBBS, DNB (Neurosurgery), Yashoda Hospitals Malakpet, Hyderabad, India.

## Build

The single source of truth is `main.tex`. The Overleaf-ready bundle is `manuscript_overleaf_v1.4.zip` at the repository root (or in `~/life/` on the author's workstation).

```bash
cd manuscript
make all          # local pdflatex + bibtex (requires a TeX installation)
# Or upload manuscript_overleaf_v1.4.zip to Overleaf.
```

## Files

| File | Role |
|---|---|
| `main.tex` | Main document; `\input`s the 12 section files in `sections/` |
| `sections/abstract.tex` | Structured abstract (Background / Methods / Results / Conclusions) |
| `sections/introduction.tex` | Clinical motivation (AIS epidemiology) |
| `sections/theory_summary.tex` | Information–mechanical coupling overview |
| `sections/methods_summary.tex` | Cross-species allometry, AlphaFold pipeline, delay-differential model |
| `sections/results.tex` | All quantitative findings (model-internal) |
| `sections/figures.tex` | Figure inclusion + captions |
| `sections/discussion.tex` | Clinical interpretation + limits |
| `sections/conclusion.tex` | Summary |
| `sections/availability.tex` | Code and data availability statement |
| `sections/statements.tex` | Ethics / Consent / Competing Interests / Funding / Author Contributions |
| `sections/tables.tex` | All in-text tables |
| `sections/supplementary.tex` | Supplementary methods, tables, and sensitivity analyses |
| `cover_letter_spine_deformity.tex` | Cover letter for *Spine Deformity* submission |
| `highlights_spine_deformity.txt` | 5-bullet clinical highlights for the submission form |
| `references.bib` | Bibliographic database (53 entries cited in the manuscript; additional entries retained for future revisions) |
| `figures/` | All manuscript figures (PDF + PNG, ≥300 DPI) |
| `_archive/` | Earlier drafts and superseded files (not part of the current submission; preserved for revision history) |

## Sections actually included in the compiled PDF

`main.tex` inputs exactly: `abstract`, `introduction`, `theory_summary`, `methods_summary`, `results`, `figures`, `discussion`, `conclusion`, `availability`, `statements`, `tables`, `supplementary`. Files in `_archive/` are not compiled into the submission PDF.

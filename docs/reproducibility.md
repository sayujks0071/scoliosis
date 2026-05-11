# Reproducibility Guide

This repository is organized around a small set of reproducible entry points:
the `spinalmodes` package in `src/`, the experiment scripts in `scripts/experiments/`,
the manuscript sources in `manuscript/`, and a lightweight root `Makefile` for local checks.

## Requirements

- Python 3.10 or newer.
- A virtual environment is strongly recommended.
- `pytest` and `pytest-cov` for test execution.
- `build` if you want to create a wheel locally.
- TeX tooling such as `pdflatex` and `bibtex` if you want to compile the manuscript.

## Recommended Local Setup

```bash
git clone https://github.com/sayujks0071/life.git
cd life
python3 -m venv .venv
source .venv/bin/activate
make install
```

Equivalent explicit commands are:

```bash
python -m pip install -e .
python -m pip install -r requirements.txt
```

The root `Makefile` wraps the same workflow:

```bash
make install
make smoke
make test
make build
```

## What Each Command Does

- `make install` installs the package in editable mode and then installs the dependency set from `requirements.txt`.
- `make smoke` checks that the package imports and the CLI version entry point works.
- `make test` runs the core pytest subset that is currently reliable in this repo snapshot.
- `make build` creates a wheel in `dist/`.

## Current Validation Scope

The core validation path is the Python test subset exercised by `make test` and the
smoke checks in `tests/test_cli.py` and `tests/test_smoke.py`. These are the fastest
checks to run after a fresh install.

The broader `pytest` suite includes slower or more environment-sensitive experiment
paths. Once `make install` has completed successfully, you can run the full suite with:

```bash
python -m pytest -q
```

## Core Experiments

The minimal end-to-end rod experiment lives in
`scripts/experiments/experiment_minimal_elastica.py`.

```bash
python scripts/experiments/experiment_minimal_elastica.py
```

For AlphaFold and candidate-processing workflows, use the scripts in
`scripts/data_management/` and `research/alphafold_countercurvature/scripts/`.

## Manuscript Build

If a TeX toolchain is available, the manuscript can be compiled from `manuscript/`
with the standard LaTeX sequence:

```bash
cd manuscript
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Troubleshooting

- If a module import fails, confirm the virtual environment is active and the repo
  root is on the Python path.
- If manuscript compilation fails, check that TeX binaries are installed locally.

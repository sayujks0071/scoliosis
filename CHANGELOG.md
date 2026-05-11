# Changelog

## [0.4.0] - 2026-02-10
### Added
- "Versioning" strategy documented in `docs/CONTRIBUTING.md`.
- `archive/` directory for legacy code (`biology_research`, `life`, `life-1`, `ragflow`).
- `research/` directory for exploratory code.
- `src/` directory for core library code.

### Changed
- Refactored repository structure to separate core library (`src/`) from research (`research/`) and legacy (`archive/`).
- Updated `pyproject.toml` and `src/spinalmodes/__init__.py` to version 0.4.0.
- Consolidated root-level scripts into `scripts/`.

## [0.3.0] - 2025-11-19
### Added
- New `spinalmodes` package layout with `model/{core,solvers}` + legacy shim.
- Deterministic analysis pipeline (01–05) with provenance emitters.
- CLI entrypoints: `spinalmodes-validate`, `spinalmodes-figures`, `spinalmodes-paper`.
- Tests: BC, convergence, units, IEC phase/amplitude; optional cosserat-bridge skip.
- CI: pytest + smoke figure job; tagged release build; pip cache.
- Manuscript inserts: validation, IEC-1/2, longevity methods/results.
- Packaging: sdist includes manuscript, figures, tables; arXiv bundle script.

### Changed
- Makefile targets: env/test/figures/paper/all + build/dist/arxiv.

### Fixed
- Headless plotting (Agg) in CI; guarded `lifelines` import with install hint.


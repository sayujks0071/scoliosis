# Environments

This directory contains historical environment snapshots and configurations.

## Active Configuration

The active dependency configuration for this project is managed via **Poetry** in the root `pyproject.toml`.

To install dependencies:
```bash
poetry install
```

Or using the generated root `requirements.txt` (mirrored from `pyproject.toml`):
```bash
pip install -r requirements.txt
```

## Historical Snapshots

- `requirements_snapshot_v0.2.0.txt`: Snapshot of dependencies for version 0.2.0 (BVP solver upgrade, 2025-11-04).
- `environment.yml`: Conda environment file (may be outdated).
- `Dockerfile`: Container configuration.

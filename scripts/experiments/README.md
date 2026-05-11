# Experiments

This directory contains simulation experiments and parameter sweeps.

## Standard Interface

New experiments should use the `StandardExperimentParser` from `experiment_utils.py` to ensure a consistent CLI.

### Usage

```python
from experiment_utils import StandardExperimentParser, setup_experiment

def main():
    parser = StandardExperimentParser(description="Experiment Description")
    # Add custom arguments if needed
    parser.add_argument("--my-arg", type=int, default=10)

    args = parser.parse_args()
    out_dir = setup_experiment(args)

    # Run experiment...
    # Use args.quick to reduce sweep size for testing
```

### Standard Arguments

All scripts inheriting from `StandardExperimentParser` support:

- `--out-dir`: Directory to save results (default: `outputs/sim/{YYYY-MM-DD}`).
- `--quick`: Run a reduced set of parameters for testing.
- `--debug`: Enable verbose debug logging.

## Directory Structure

- `experiment_utils.py`: Shared utilities for experiments.
- `experiment_*.py`: General experiments (often reproducible or long-lived).
- `weekly_sim_*.py`: Specific simulations tied to weekly research goals.
- `run_*.py`: Legacy scripts (consider refactoring or using as wrappers).

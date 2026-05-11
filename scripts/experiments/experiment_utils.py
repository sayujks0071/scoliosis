"""
Standard utilities for experiment scripts.

This module provides a standardized interface for running experiments, ensuring consistent
argument parsing, logging, and output directory management.
"""

import argparse
import logging
from datetime import date
from pathlib import Path
from typing import Optional


def get_default_output_dir() -> Path:
    """Return the default output directory based on today's date."""
    today = date.today().strftime("%Y-%m-%d")
    return Path(f"outputs/sim/{today}")

class StandardExperimentParser(argparse.ArgumentParser):
    """
    Standard argument parser for experiment scripts.

    Adds common arguments:
    - --out-dir: Output directory (default: outputs/sim/{YYYY-MM-DD})
    - --quick: Run a quick smoke test
    - --debug: Enable debug logging
    """
    def __init__(self, description: str, default_out_dir: Optional[str] = None):
        super().__init__(description=description)

        if default_out_dir is None:
            default_out_dir = str(get_default_output_dir())

        self.add_argument(
            "--out-dir",
            type=str,
            default=default_out_dir,
            help=f"Output directory for results (default: {default_out_dir})"
        )
        self.add_argument(
            "--quick",
            action="store_true",
            help="Run a quick smoke test with reduced parameters."
        )
        self.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging."
        )

def setup_experiment(args: argparse.Namespace) -> Path:
    """
    Set up the experiment environment.

    - Configures logging based on args.debug.
    - Creates the output directory if it doesn't exist.
    - Returns the Path to the output directory.
    """
    # Configure logging
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )

    # Create output directory
    out_path = Path(args.out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    logging.info("Experiment setup complete.")
    logging.info(f"Output directory: {out_path}")
    if args.quick:
        logging.warning("Running in QUICK mode (reduced parameters).")

    return out_path

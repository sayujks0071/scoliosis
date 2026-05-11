"""Deterministic seeding utilities."""

import os
import random

import numpy as np


def set_seed(seed: int = 1337) -> None:
    """Seed numpy, random, and hash seed for reproducibility."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    random.seed(seed)


"""Provenance tracking helpers for deterministic runs."""

from __future__ import annotations

import json
import platform
import subprocess
import time
from pathlib import Path


def git_sha() -> str:
    """Return git SHA if available."""
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def write_provenance(path: str | Path, seed: int, inputs: dict) -> None:
    """Write a small provenance JSON alongside generated artifacts."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "git_sha": git_sha(),
        "seed": seed,
        "inputs": inputs,
        "system": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
    }
    Path(path).write_text(json.dumps(payload, indent=2))


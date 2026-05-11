import sys
from pathlib import Path

import pytest

# Add repo root to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Add scripts directory to sys.path
scripts_dir = root_dir / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.append(str(scripts_dir))

# Add research/alphafold_countercurvature/src to sys.path
afcc_src_dir = root_dir / "research" / "alphafold_countercurvature" / "src"
if str(afcc_src_dir) not in sys.path:
    sys.path.append(str(afcc_src_dir))


def _cuda_available() -> bool:
    try:
        import torch
    except ImportError:
        return False
    return torch.cuda.is_available()


def pytest_collection_modifyitems(config, items):
    if _cuda_available():
        return
    skip_gpu = pytest.mark.skip(reason="CUDA not available in this environment")
    for item in items:
        if "gpu" in item.keywords:
            item.add_marker(skip_gpu)

# Contributing to the Repository

Welcome! This document defines the standards and workflows for contributing to this research repository. Our goal is to maintain **publication-grade code quality**, ensuring reproducibility, readability, and long-term viability.

## Repository Structure

Understanding the layout is crucial for placing your code correctly:

*   **`src/`**: **Core Library.** Contains polished, tested, and reusable packages. This code is held to the highest standard.
*   **`research/`**: **Exploratory Space.** Contains active research scripts, one-off experiments, and hypothesis testing code. While flexible, code here should still be readable and roughly typed.
*   **`tests/`**: **Test Suite.** Mirrors the structure of `src/`. Core functionality should have accompanying tests.
*   **`docs/`**: **Documentation.** Project plans, reproducibility notes, and API references.
*   **`scripts/`**: **Utilities.** Helper scripts for maintenance, data processing, or running simulations.
*   **`data/`**: **Inputs.** Raw and processed data files. Large generated files should not be committed unless they are a canonical input dataset.
*   **`archive/`**: **Legacy.** Deprecated code and old experiments. Do not modify files here.

## Development Workflow

1.  **Branching**:
    *   Use descriptive branch names: `feat/new-solver`, `fix/typo-in-docs`, `refactor/cleanup-imports`.
2.  **Atomic Commits**:
    *   Make small, focused commits.
    *   Format: `type: Description` (e.g., `feat: Add IEC coupling module`, `fix: Correct boundary condition`).
3.  **Pull Requests**:
    *   Describe the **Goal**, **Changes**, and **Verification** in your PR description.

## Coding Standards

We enforce strict standards to ensure uniformity.

### 1. Formatting
We use **Black** for code formatting.
*   Line length: 100 characters.
*   Double quotes for strings.
*   Run: `black .`

### 2. Linting
We use **Ruff** for linting.
*   Fix common errors automatically: `ruff check --fix .`
*   Ensure imports are sorted and unused variables are removed.

### 3. Typing
We use **MyPy** for static type checking.
*   **Strict Typing**: Aim for type hints on public function arguments and return values.
*   Use `typing.Optional`, `typing.List`, `typing.Dict`, etc., or standard collection types (Python 3.10+).
*   Use `numpy.typing.NDArray` for arrays.

**Example:**
```python
from typing import Optional, Tuple
import numpy as np
from numpy.typing import NDArray

def calculate_curvature(
    coords: NDArray[np.float64],
    smooth: bool = True
) -> Tuple[NDArray[np.float64], Optional[float]]:
    """Calculates curvature from coordinates."""
    ...
```

### 4. Docstrings
We use the **Google Style** for docstrings. Every public module, class, and function must be documented.

**Structure:**
*   **Summary**: A one-line summary.
*   **Details**: (Optional) Extended description.
*   **Args**: List of arguments with types and descriptions.
*   **Returns**: Description of the return value.
*   **Raises**: (Optional) List of exceptions raised.

**Example:**
```python
def solve_system(a: float, b: float) -> float:
    """
    Solves the linear system for the given parameters.

    Args:
        a: The coefficient of the linear term.
        b: The constant offset.

    Returns:
        The solution x such that ax + b = 0.

    Raises:
        ValueError: If a is zero.
    """
    if a == 0:
        raise ValueError("Coefficient 'a' cannot be zero.")
    return -b / a
```

## Testing

We use **pytest**.
*   **Unit Tests**: Place in `tests/`.
*   **Naming**: Files must start with `test_`. Functions must start with `test_`.
*   **Coverage**: Aim for high coverage on `src/` modules and keep core checks fast.
*   **Run**: `make test` for the repository's core validation subset, or `pytest -q` when you want the full test suite.

## Versioning

We follow **Semantic Versioning (SemVer)** (e.g., `MAJOR.MINOR.PATCH`).
*   **MAJOR**: Incompatible API changes.
*   **MINOR**: Backwards-compatible functionality additions.
*   **PATCH**: Backwards-compatible bug fixes.

The single source of truth for the version number is **`pyproject.toml`**. Keep `src/spinalmodes/__init__.py` in sync when releasing.

## Environment

*   Manage dependencies via `requirements.txt` and `pyproject.toml`.
*   Always use a virtual environment (`.venv`, `env`, or `conda`).

---
*Thank you for helping us build a robust scientific tool.*

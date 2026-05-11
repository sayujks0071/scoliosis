"""CLI entry points and convenience wrappers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    import typer  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    # Allow importing this module in minimal environments (e.g. some CI sandboxes)
    # where CLI dependencies aren't installed. Unit tests only require that the
    # module imports and exposes helper functions (e.g. cmd_figures).
    typer = None

if typer is not None:
    from spinalmodes.iec_cli import app as iec_app

    app = typer.Typer(help="Spinal modes: Counter-curvature and IEC model")
    # Register subcommands
    app.add_typer(iec_app, name="iec")
else:
    app = None  # type: ignore


def _run(pyfile: str) -> int:
    """Execute a Python script and return its exit code."""
    path = Path(pyfile)
    if not path.exists():
        print(f"Expected script not found: {path}", file=sys.stderr)
        return 1
    return subprocess.call([sys.executable, str(path)])


def cmd_validate() -> int:
    """Run solver validation script."""
    return _run("scripts/validation/validate_solver_figures.py")


def cmd_figures() -> int:
    """Regenerate all figures and tables."""
    for f in [
        "scripts/validation/validate_solver_figures.py",
        "scripts/analysis/01_data_audit.py",
        "scripts/analysis/03_iec_phase_amp.py",
        "scripts/analysis/04_countercurvature.py",
        "scripts/analysis/05_longevity_demo.py",
    ]:
        rc = _run(f)
        if rc != 0:
            return rc
    return 0


def cmd_paper() -> int:
    """Create the manuscript submission bundle."""
    bundle_script = Path("scripts/reporting/arxiv_bundle.sh")
    if not bundle_script.exists():
        print(f"Expected bundle script not found: {bundle_script}", file=sys.stderr)
        return 1
    return subprocess.call(["bash", str(bundle_script)])


if typer is not None:

    @app.command()
    def version():
        """Show version information."""
        from spinalmodes import __version__

        typer.echo(f"spinalmodes version {__version__}")


if __name__ == "__main__":
    if typer is None or app is None:
        raise SystemExit(
            "CLI dependencies not installed. Install 'typer' (and extras) to use the CLI."
        )
    app()

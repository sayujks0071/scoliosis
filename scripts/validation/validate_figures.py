#!/usr/bin/env python3
"""
Figure validation tool.

Checks:
- PNG DPI ≥ 300
- Width 1800-3600 px
- No alpha channel
- Sidecar JSON present
- CSV headers present with >50 rows for maps
"""

import json
import sys
from pathlib import Path

import pandas as pd
from PIL import Image


def validate_png(png_path: Path) -> list:
    """Validate PNG file requirements."""
    errors = []

    if not png_path.exists():
        return [f"File not found: {png_path}"]

    try:
        img = Image.open(png_path)

        # Check DPI
        dpi = img.info.get("dpi", (72, 72))
        if isinstance(dpi, tuple):
            dpi_val = dpi[0]
        else:
            dpi_val = dpi

        if dpi_val < 300:
            errors.append(f"{png_path.name}: DPI {dpi_val} < 300")

        # Check width
        width = img.width
        if width < 1800 or width > 3600:
            errors.append(
                f"{png_path.name}: Width {width}px not in range [1800, 3600]"
            )

        # Check alpha channel
        if img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        ):
            errors.append(f"{png_path.name}: Has alpha channel (not allowed)")

    except Exception as e:
        errors.append(f"{png_path.name}: Error reading image: {e}")

    return errors


def validate_sidecar_json(png_path: Path) -> list:
    """Validate sidecar JSON file."""
    errors = []
    json_path = png_path.with_suffix(".json")

    if not json_path.exists():
        errors.append(f"{png_path.name}: Missing sidecar JSON: {json_path.name}")
        return errors

    try:
        with open(json_path) as f:
            metadata = json.load(f)

        # Check required fields
        required_fields = ["figure_type", "parameters", "code_version"]
        for field in required_fields:
            if field not in metadata:
                errors.append(
                    f"{json_path.name}: Missing required field '{field}'"
                )

    except json.JSONDecodeError as e:
        errors.append(f"{json_path.name}: Invalid JSON: {e}")
    except Exception as e:
        errors.append(f"{json_path.name}: Error reading JSON: {e}")

    return errors


def validate_csv(csv_path: Path, min_rows: int = 50) -> list:
    """Validate CSV file for map data."""
    errors = []

    if not csv_path.exists():
        return []  # CSV not required for all figures

    try:
        df = pd.read_csv(csv_path)

        # Check headers present
        if df.shape[1] == 0:
            errors.append(f"{csv_path.name}: No columns/headers found")

        # Check minimum rows for maps
        if "map" in csv_path.stem.lower() and df.shape[0] < min_rows:
            errors.append(
                f"{csv_path.name}: Only {df.shape[0]} rows (expected >{min_rows})"
            )

    except Exception as e:
        errors.append(f"{csv_path.name}: Error reading CSV: {e}")

    return errors


def main():
    """Run validation on all figures."""
    project_root = Path(__file__).parent.parent.parent
    figs_dir = project_root / "outputs" / "figs"
    csv_dir = project_root / "outputs" / "csv"

    if not figs_dir.exists():
        print(f"❌ Figures directory not found: {figs_dir}")
        return 1

    # Find all PNG files
    png_files = list(figs_dir.glob("*.png"))

    if not png_files:
        print(f"⚠️  No PNG files found in {figs_dir}")
        return 0

    print(f"Validating {len(png_files)} figure(s)...\n")

    all_errors = []

    for png_path in sorted(png_files):
        print(f"Checking {png_path.name}...")

        # Validate PNG
        png_errors = validate_png(png_path)
        all_errors.extend(png_errors)

        # Validate sidecar JSON
        json_errors = validate_sidecar_json(png_path)
        all_errors.extend(json_errors)

        # Validate associated CSV if exists
        csv_path = csv_dir / png_path.with_suffix(".csv").name
        if csv_path.exists():
            csv_errors = validate_csv(csv_path)
            all_errors.extend(csv_errors)

    print()

    if all_errors:
        print("❌ Validation FAILED:\n")
        for error in all_errors:
            print(f"  • {error}")
        return 1
    else:
        print("✅ All figures passed validation!")
        return 0


if __name__ == "__main__":
    sys.exit(main())


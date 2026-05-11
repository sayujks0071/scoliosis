"""Inventory current repository files into tables/data_catalog.csv."""

import csv
from pathlib import Path

from spinalmodes.utils.provenance import write_provenance


def main() -> None:
    tables = Path("tables")
    tables.mkdir(exist_ok=True, parents=True)
    with (tables / "data_catalog.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["path", "bytes"])
        for p in Path(".").rglob("*"):
            if not p.is_file():
                continue
            if p.parts[0].startswith("."):
                continue
            if "__pycache__" in p.parts or "venv" in p.parts:
                continue
            writer.writerow([str(p), p.stat().st_size])
    write_provenance("tables/data_catalog.provenance.json", seed=1337, inputs={})


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Run Phase 2 longitudinal AIS progression validation.

Default mode uses a deterministic synthetic demo cohort so the full pipeline can
be tested without private clinical data. Pass --input to analyze a real
longitudinal CSV that follows the Phase 2 schema.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from spinalmodes.longitudinal import (
    generate_demo_cohort,
    build_progression_table,
    evaluate_progression_models,
    summarize_longitudinal_run,
    validate_longitudinal_schema,
)


DEMO_CSV = PROJECT_DIR / "data" / "demo" / "phase2_synthetic_longitudinal.csv"
RESULTS_DIR = PROJECT_DIR / "results" / "longitudinal"

PROGRESSION_CSV = RESULTS_DIR / "phase2_progression_table.csv"
METRICS_CSV = RESULTS_DIR / "phase2_model_metrics.csv"
SUMMARY_JSON = RESULTS_DIR / "phase2_longitudinal_summary.json"
REPORT_MD = RESULTS_DIR / "phase2_longitudinal_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DEMO_CSV,
        help="Longitudinal visit CSV. Defaults to the deterministic synthetic demo cohort.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RESULTS_DIR,
        help="Directory for progression table, metrics, summary, and report.",
    )
    parser.add_argument(
        "--generate-demo",
        action="store_true",
        help="Regenerate the deterministic demo CSV before running validation.",
    )
    parser.add_argument("--demo-patients", type=int, default=160)
    parser.add_argument("--seed", type=int, default=202602)
    parser.add_argument(
        "--dataset-kind",
        choices=["synthetic_demo", "real_or_mixed"],
        default="synthetic_demo",
        help="Label written to summary outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.generate_demo or input_path == DEMO_CSV and not input_path.exists():
        demo = generate_demo_cohort(n_patients=args.demo_patients, seed=args.seed)
        DEMO_CSV.parent.mkdir(parents=True, exist_ok=True)
        demo.to_csv(DEMO_CSV, index=False)

    if not input_path.exists():
        raise FileNotFoundError(f"input CSV not found: {input_path}")

    visits = pd.read_csv(input_path)
    visits = validate_longitudinal_schema(visits)
    progressions = build_progression_table(visits)
    metrics = evaluate_progression_models(progressions)
    summary = summarize_longitudinal_run(visits, progressions, metrics, args.dataset_kind)

    progression_csv = output_dir / PROGRESSION_CSV.name
    metrics_csv = output_dir / METRICS_CSV.name
    summary_json = output_dir / SUMMARY_JSON.name
    report_md = output_dir / REPORT_MD.name

    progressions.to_csv(progression_csv, index=False)
    metrics.to_csv(metrics_csv, index=False)
    summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report_md.write_text(write_report(summary, metrics, progression_csv, metrics_csv), encoding="utf-8")

    print(f"Wrote {progression_csv}")
    print(f"Wrote {metrics_csv}")
    print(f"Wrote {summary_json}")
    print(f"Wrote {report_md}")
    return 0


def write_report(
    summary: dict[str, Any],
    metrics: pd.DataFrame,
    progression_csv: Path,
    metrics_csv: Path,
) -> str:
    binary = metrics[metrics["task"] == "binary"].copy()
    regression = metrics[metrics["task"] == "regression"].copy()

    lines = [
        "# Phase 2 Longitudinal Progression Validation",
        "",
        "## Dataset",
        "",
        f"- Dataset kind: `{summary['dataset_kind']}`",
        f"- Source datasets: {', '.join(summary['source_datasets'])}",
        f"- Visits: {summary['n_visits']}",
        f"- Baseline-to-final trajectories: {summary['n_trajectories']}",
        f"- Median follow-up: {summary['followup_years_median']:.2f} years",
        f"- Median baseline Cobb angle: {summary['baseline_cobb_median']:.2f} degrees",
        f"- Median Cobb change: {summary['delta_cobb_median']:.2f} degrees",
        "",
        "## Progression Counts",
        "",
        _dict_table(summary["progression_counts"], key_label="Endpoint", value_label="Count"),
        "",
        "## Binary Model Comparison",
        "",
        _metrics_table(binary, ["target", "model", "n", "positives", "auroc", "average_precision", "brier_score"]),
        "",
        "## Annualized Cobb Change Model Comparison",
        "",
        _metrics_table(regression, ["model", "n", "r2", "mae", "rmse"]),
        "",
        "## Outputs",
        "",
        f"- Progression table: `{progression_csv}`",
        f"- Model metrics: `{metrics_csv}`",
        "",
        "## Interpretation Guardrails",
        "",
        "- Binary endpoints are modeled only when both classes have at least two trajectories; rare threshold crossings are counted but not benchmarked.",
    ]
    lines.extend(f"- {item}" for item in summary["limitations"])
    lines.append("")
    return "\n".join(lines)


def _dict_table(values: dict[str, Any], key_label: str, value_label: str) -> str:
    lines = [f"| {key_label} | {value_label} |", "|---|---:|"]
    for key, value in values.items():
        lines.append(f"| `{key}` | {value} |")
    return "\n".join(lines)


def _metrics_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "No evaluable models for this endpoint."
    available = [column for column in columns if column in frame.columns]
    display = frame[available].copy()
    for column in display.columns:
        if pd.api.types.is_float_dtype(display[column]):
            display[column] = display[column].map(lambda value: "" if pd.isna(value) else f"{value:.3f}")

    lines = ["| " + " | ".join(available) + " |", "|" + "|".join("---" for _ in available) + "|"]
    for _, row in display.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in available) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())

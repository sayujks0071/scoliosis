#!/usr/bin/env python3
"""
Extract open-data spine geometry features from the curated SpineWeb/AASCE XMLs.

The current validation target is intentionally narrow:
  - parse free T1-L5 landmark annotations;
  - compute Cobb-like and centerline geometry endpoints;
  - separate 2D projection proxies from claims that require 3D/EOS data.

This script does not use image pixels and does not infer progression risk.
"""

from __future__ import annotations

import csv
import json
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_DIR / "data" / "open" / "spineweb_curated"
RESULTS_DIR = PROJECT_DIR / "results" / "open_data"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

VERTEBRA_ORDER = [f"T{i}" for i in range(1, 13)] + [f"L{i}" for i in range(1, 6)]
VERTEBRA_RANK = {name: i for i, name in enumerate(VERTEBRA_ORDER)}


@dataclass(frozen=True)
class VertebraLandmark:
    vertebra_id: str
    points: np.ndarray  # shape (4, 2), expected order: TL, TR, BR, BL


def _clean_header(value: str | None) -> str:
    return (value or "").replace("\ufeff", "").strip()


def read_corrections(path: Path, split: str) -> dict[str, dict[str, str]]:
    """Read the semicolon-delimited correction CSV into a filename-keyed map."""
    if not path.exists():
        return {}

    rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=";")
        header = [_clean_header(h) for h in next(reader)]
        indices = {name: i for i, name in enumerate(header) if name}

        for raw in reader:
            if not raw:
                continue
            file_idx = indices.get("File name")
            if file_idx is None or file_idx >= len(raw):
                continue
            file_name = raw[file_idx].strip()
            if not file_name:
                continue

            def get(name: str) -> str:
                idx = indices.get(name)
                if idx is None or idx >= len(raw):
                    return ""
                return raw[idx].strip()

            key = normalize_case_key(file_name)
            rows[key] = {
                "split": split,
                "file_name": file_name,
                "correction_state": get("Correction state"),
                "annotation_quality": get("Annotation"),
                "comment": get("Comment"),
                "suitable_for_training": get("Suitable for training"),
                "not_suitable_for_training": get("Not suitable for training"),
            }
    return rows


def normalize_case_key(file_name: str) -> str:
    path = Path(file_name.strip())
    stem = path.stem if path.suffix else file_name.strip()
    return " ".join(stem.lower().split())


def parse_xml(path: Path) -> tuple[str, list[VertebraLandmark]]:
    root = ET.parse(path).getroot()
    exam = root.find(".//exam")
    input_file = exam.attrib.get("inputFile", path.with_suffix(".jpg").name) if exam is not None else path.with_suffix(".jpg").name

    landmarks: list[VertebraLandmark] = []
    for ann in root.findall(".//annotation"):
        vertebra_id = ann.attrib.get("id", "").strip()
        pos = ann.findtext("pos", default="").strip()
        if vertebra_id not in VERTEBRA_RANK or not pos:
            continue
        values = [float(v) for v in pos.split()]
        if len(values) != 8:
            continue
        points = np.asarray(values, dtype=float).reshape(4, 2)
        landmarks.append(VertebraLandmark(vertebra_id=vertebra_id, points=points))

    landmarks.sort(key=lambda item: VERTEBRA_RANK[item.vertebra_id])
    return input_file, landmarks


def canonical_line_angle_deg(p1: np.ndarray, p2: np.ndarray) -> float:
    """Directionless line angle in degrees, canonicalized to [-90, 90)."""
    dx, dy = (p2 - p1).astype(float)
    angle = math.degrees(math.atan2(dy, dx))
    while angle >= 90.0:
        angle -= 180.0
    while angle < -90.0:
        angle += 180.0
    return float(angle)


def acute_angle_difference_deg(a: float, b: float) -> float:
    diff = abs(a - b) % 180.0
    if diff > 90.0:
        diff = 180.0 - diff
    return float(diff)


def endplate_angles(landmarks: Iterable[VertebraLandmark]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for landmark in landmarks:
        p = landmark.points
        rows.append(
            {
                "vertebra_id": landmark.vertebra_id,
                "plate": "superior",
                "angle_deg": canonical_line_angle_deg(p[0], p[1]),
            }
        )
        rows.append(
            {
                "vertebra_id": landmark.vertebra_id,
                "plate": "inferior",
                "angle_deg": canonical_line_angle_deg(p[3], p[2]),
            }
        )
    return rows


def cobb_endplate_envelope(landmarks: list[VertebraLandmark]) -> tuple[float, str, str]:
    """Maximum acute angle between any two vertebral endplate lines."""
    plates = endplate_angles(landmarks)
    best = (0.0, "", "")
    for i, first in enumerate(plates):
        for second in plates[i + 1 :]:
            diff = acute_angle_difference_deg(float(first["angle_deg"]), float(second["angle_deg"]))
            if diff > best[0]:
                first_name = f"{first['vertebra_id']}:{first['plate']}"
                second_name = f"{second['vertebra_id']}:{second['plate']}"
                best = (diff, first_name, second_name)
    return best


def centers_from_landmarks(landmarks: list[VertebraLandmark]) -> tuple[list[str], np.ndarray]:
    ids = [item.vertebra_id for item in landmarks]
    centers = np.vstack([item.points.mean(axis=0) for item in landmarks])
    order = np.argsort(centers[:, 1])
    return [ids[i] for i in order], centers[order]


def centerline_boundary_angle_deg(centers: np.ndarray, frac: float = 0.2) -> float:
    """Angle between cranial and caudal centerline tangents in the AP projection."""
    n = len(centers)
    if n < 6:
        return 0.0
    k = max(3, int(round(frac * n)))
    k = min(k, n // 2)

    def fit_angle(segment: np.ndarray) -> float:
        y = segment[:, 1]
        x = segment[:, 0]
        slope, _ = np.polyfit(y, x, deg=1)
        return math.degrees(math.atan(slope))

    cranial = fit_angle(centers[:k])
    caudal = fit_angle(centers[-k:])
    return acute_angle_difference_deg(cranial, caudal)


def centerline_features(centers: np.ndarray) -> dict[str, float]:
    x = centers[:, 0]
    y = centers[:, 1]
    vertical_span = float(np.ptp(y))
    lateral_span = float(np.ptp(x))
    if vertical_span <= 0.0:
        return {
            "vertical_span_px": 0.0,
            "lateral_span_px": lateral_span,
            "lateral_span_norm": 0.0,
            "max_chord_deviation_norm": 0.0,
            "arc_length_norm": 0.0,
            "tortuosity": 0.0,
            "projected_rotation_total_deg": 0.0,
            "projected_rotation_net_deg": 0.0,
            "projected_curvature_energy": 0.0,
            "centerline_inflections": 0.0,
            "centerline_cobb_like_deg": 0.0,
        }

    chord_x = np.interp(y, [y[0], y[-1]], [x[0], x[-1]])
    chord_deviation = x - chord_x
    diffs = np.diff(centers, axis=0)
    segment_lengths = np.linalg.norm(diffs, axis=1)
    arc_length = float(segment_lengths.sum())
    chord_length = float(np.linalg.norm(centers[-1] - centers[0]))

    segment_angles = np.unwrap(np.arctan2(diffs[:, 0], diffs[:, 1]))
    turns = np.diff(segment_angles)
    nonzero_turns = turns[np.abs(turns) > 1e-6]
    inflections = 0
    if len(nonzero_turns) > 1:
        inflections = int(np.sum(np.sign(nonzero_turns[1:]) != np.sign(nonzero_turns[:-1])))

    return {
        "vertical_span_px": vertical_span,
        "lateral_span_px": lateral_span,
        "lateral_span_norm": lateral_span / vertical_span,
        "max_chord_deviation_norm": float(np.max(np.abs(chord_deviation)) / vertical_span),
        "arc_length_norm": arc_length / vertical_span,
        "tortuosity": arc_length / chord_length if chord_length > 0.0 else 0.0,
        "projected_rotation_total_deg": float(np.degrees(np.sum(np.abs(turns)))) if len(turns) else 0.0,
        "projected_rotation_net_deg": float(np.degrees(np.sum(turns))) if len(turns) else 0.0,
        "projected_curvature_energy": float(np.sum(turns**2)) if len(turns) else 0.0,
        "centerline_inflections": float(inflections),
        "centerline_cobb_like_deg": centerline_boundary_angle_deg(centers),
    }


def extract_case(path: Path, split: str, corrections: dict[str, dict[str, str]]) -> dict[str, object]:
    input_file, landmarks = parse_xml(path)
    case_key = normalize_case_key(input_file)
    correction = corrections.get(case_key, {})
    vertebra_ids, centers = centers_from_landmarks(landmarks)
    cobb_deg, cobb_plate_a, cobb_plate_b = cobb_endplate_envelope(landmarks)
    features = centerline_features(centers)

    usable = correction.get("suitable_for_training", "")
    excluded = correction.get("not_suitable_for_training", "")
    is_usable = usable == "1" and excluded != "1"

    row: dict[str, object] = {
        "split": split,
        "xml_file": path.name,
        "input_file": input_file,
        "case_key": case_key,
        "n_vertebrae": len(landmarks),
        "vertebra_ids": ",".join(vertebra_ids),
        "is_complete_t1_l5": len(landmarks) == len(VERTEBRA_ORDER),
        "correction_state": correction.get("correction_state", ""),
        "annotation_quality": correction.get("annotation_quality", ""),
        "suitable_for_training": usable,
        "not_suitable_for_training": excluded,
        "is_usable": is_usable,
        "cobb_endplate_envelope_deg": cobb_deg,
        "cobb_plate_a": cobb_plate_a,
        "cobb_plate_b": cobb_plate_b,
        "open_geometry_scoliosis_proxy_10deg": cobb_deg >= 10.0,
        "open_geometry_scoliosis_proxy_20deg": cobb_deg >= 20.0,
        "open_geometry_scoliosis_proxy_40deg": cobb_deg >= 40.0,
    }
    row.update(features)
    return row


def summarize(df: pd.DataFrame) -> dict[str, object]:
    usable = df[df["is_usable"]].copy()
    complete = usable[usable["is_complete_t1_l5"]].copy()

    def quantiles(series: pd.Series) -> dict[str, float]:
        qs = series.quantile([0.05, 0.25, 0.5, 0.75, 0.95])
        return {str(k): float(v) for k, v in qs.items()}

    summary: dict[str, object] = {
        "dataset": "SpineWeb/AASCE 2019 curated landmark annotations",
        "source": "https://zenodo.org/records/4413665",
        "n_cases_total": int(len(df)),
        "n_train": int((df["split"] == "train").sum()),
        "n_test": int((df["split"] == "test").sum()),
        "n_usable": int(df["is_usable"].sum()),
        "n_complete_t1_l5": int(df["is_complete_t1_l5"].sum()),
        "n_usable_complete_t1_l5": int(len(complete)),
        "annotation_quality_counts": df["annotation_quality"].fillna("").value_counts().to_dict(),
        "correction_state_counts": df["correction_state"].fillna("").value_counts().to_dict(),
        "usable_proxy_counts": {
            "cobb_ge_10": int((usable["cobb_endplate_envelope_deg"] >= 10.0).sum()),
            "cobb_ge_20": int((usable["cobb_endplate_envelope_deg"] >= 20.0).sum()),
            "cobb_ge_40": int((usable["cobb_endplate_envelope_deg"] >= 40.0).sum()),
        },
    }
    for column in [
        "cobb_endplate_envelope_deg",
        "centerline_cobb_like_deg",
        "lateral_span_norm",
        "max_chord_deviation_norm",
        "tortuosity",
        "projected_rotation_total_deg",
        "projected_curvature_energy",
    ]:
        summary[f"{column}_usable_quantiles"] = quantiles(usable[column])
    return summary


def write_plots(df: pd.DataFrame, out_path: Path) -> None:
    usable = df[df["is_usable"]].copy()
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))

    axes[0, 0].hist(usable["cobb_endplate_envelope_deg"], bins=30, color="#4C78A8", edgecolor="white")
    axes[0, 0].axvline(10, color="#E45756", linestyle="--", linewidth=1)
    axes[0, 0].set_title("Endplate Cobb-like envelope")
    axes[0, 0].set_xlabel("Degrees")
    axes[0, 0].set_ylabel("Usable cases")

    axes[0, 1].scatter(
        usable["cobb_endplate_envelope_deg"],
        usable["max_chord_deviation_norm"],
        s=14,
        alpha=0.7,
        color="#54A24B",
    )
    axes[0, 1].set_title("Cobb-like angle vs centerline deviation")
    axes[0, 1].set_xlabel("Endplate envelope, degrees")
    axes[0, 1].set_ylabel("Max chord deviation / vertical span")

    axes[1, 0].scatter(
        usable["cobb_endplate_envelope_deg"],
        usable["projected_rotation_total_deg"],
        s=14,
        alpha=0.7,
        color="#F58518",
    )
    axes[1, 0].set_title("Projected rotation proxy")
    axes[1, 0].set_xlabel("Endplate envelope, degrees")
    axes[1, 0].set_ylabel("Total centerline turn, degrees")

    grouped = usable.groupby("annotation_quality")["cobb_endplate_envelope_deg"]
    labels = [str(label) or "unlabeled" for label in grouped.groups]
    values = [grouped.get_group(label).to_numpy() for label in grouped.groups]
    try:
        axes[1, 1].boxplot(values, tick_labels=labels, showfliers=False)
    except TypeError:
        axes[1, 1].boxplot(values, labels=labels, showfliers=False)
    axes[1, 1].set_title("Cobb-like angle by annotation quality")
    axes[1, 1].set_ylabel("Degrees")
    axes[1, 1].tick_params(axis="x", rotation=20)

    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main() -> None:
    corrections: dict[str, dict[str, str]] = {}
    corrections.update(read_corrections(DATA_DIR / "correction_train.csv", "train"))
    corrections.update(read_corrections(DATA_DIR / "correction_test.csv", "test"))

    rows = []
    for split in ["train", "test"]:
        annotation_dir = DATA_DIR / f"annotations_{split}"
        for xml_path in sorted(annotation_dir.glob("*.xml")):
            rows.append(extract_case(xml_path, split, corrections))

    if not rows:
        raise RuntimeError(f"No XML annotations found under {DATA_DIR}")

    df = pd.DataFrame(rows)
    csv_path = RESULTS_DIR / "spineweb_landmark_features.csv"
    json_path = RESULTS_DIR / "spineweb_landmark_features_summary.json"
    png_path = RESULTS_DIR / "spineweb_landmark_features.png"

    df.to_csv(csv_path, index=False)
    summary = summarize(df)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_plots(df, png_path)

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {png_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

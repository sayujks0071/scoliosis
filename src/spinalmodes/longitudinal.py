"""Longitudinal scoliosis progression utilities.

This module turns patient visit tables into baseline-to-final progression
trajectories and benchmarks simple progression predictors. It is intentionally
small and inspectable: Phase 2 needs a reproducible validation frame before it
needs complex modeling.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import rankdata


REQUIRED_COLUMNS: tuple[str, ...] = (
    "patient_id",
    "visit_date",
    "age_years",
    "sex",
    "cobb_angle_deg",
    "curve_region",
    "risser_stage",
    "brace_status",
    "source_dataset",
)

GEOMETRY_COLUMNS: tuple[str, ...] = (
    "tortuosity",
    "lateral_span_norm",
    "max_chord_deviation_norm",
    "projected_rotation_total_deg",
    "projected_curvature_energy",
    "cobb_endplate_envelope_deg",
)


@dataclass(frozen=True)
class ModelSpec:
    """A named predictor set for Phase 2 benchmarking."""

    name: str
    predictors: tuple[str, ...]


def generate_demo_cohort(n_patients: int = 160, seed: int = 202602) -> pd.DataFrame:
    """Create a deterministic synthetic longitudinal AIS-like cohort.

    The demo cohort is only for pipeline verification. It deliberately encodes a
    geometry/maturity progression signal so tests can verify model wiring; it is
    not scientific evidence.
    """

    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    start = pd.Timestamp("2020-01-01")

    for idx in range(n_patients):
        patient_id = f"SYN{idx + 1:04d}"
        sex = str(rng.choice(["F", "M"], p=[0.74, 0.26]))
        curve_region = str(rng.choice(["thoracic", "thoracolumbar", "lumbar"], p=[0.62, 0.26, 0.12]))
        baseline_age = float(np.clip(rng.normal(12.6 if sex == "F" else 13.7, 1.25), 9.0, 16.8))

        maturity_center = baseline_age - (12.2 if sex == "F" else 13.3)
        risser_float = 1.6 + 0.9 * maturity_center + rng.normal(0.0, 0.9)
        risser = int(np.clip(round(risser_float), 0, 5))

        baseline_cobb = float(np.clip(rng.normal(18.0 + 2.0 * (sex == "F") - 1.2 * risser, 6.2), 6.0, 38.0))
        brace_status = "braced" if baseline_cobb >= 24.0 and rng.random() < 0.38 else "none"

        geometry_latent = rng.normal(0.0, 0.9) + 0.08 * (baseline_cobb - 18.0)
        immaturity = max(0.0, (3.0 - float(risser)) / 3.0)
        risk_score = (
            0.10 * (baseline_cobb - 18.0)
            + 0.70 * geometry_latent
            + 0.55 * immaturity
            + 0.22 * (sex == "F")
            - 0.42 * (brace_status == "braced")
            + rng.normal(0.0, 0.55)
        )

        followup_years = float(rng.uniform(0.9, 2.25))
        annual_delta = -0.8 + 8.8 * float(expit(risk_score)) + rng.normal(0.0, 1.7)
        delta_cobb = float(np.clip(annual_delta * followup_years, -3.5, 27.0))
        final_cobb = float(np.clip(baseline_cobb + delta_cobb, 0.0, 78.0))

        baseline_date = start + pd.Timedelta(days=int(rng.integers(0, 730)))
        final_date = baseline_date + pd.Timedelta(days=int(round(followup_years * 365.25)))

        for visit_idx, (visit_date, age, cobb, risser_value) in enumerate(
            [
                (baseline_date, baseline_age, baseline_cobb, risser),
                (final_date, baseline_age + followup_years, final_cobb, min(5, risser + int(followup_years >= 1.2))),
            ]
        ):
            visit_growth = max(0.0, (3.0 - float(risser_value)) / 3.0)
            noise = rng.normal(0.0, 0.015, size=5)
            rows.append(
                {
                    "patient_id": patient_id,
                    "visit_date": visit_date.date().isoformat(),
                    "age_years": round(float(age), 3),
                    "sex": sex,
                    "cobb_angle_deg": round(float(cobb), 3),
                    "curve_region": curve_region,
                    "risser_stage": int(risser_value),
                    "brace_status": brace_status,
                    "source_dataset": "synthetic_phase2_demo",
                    "tortuosity": round(1.0 + 0.0037 * cobb + 0.018 * geometry_latent + noise[0], 6),
                    "lateral_span_norm": round(0.030 + 0.0046 * cobb + 0.018 * geometry_latent + noise[1], 6),
                    "max_chord_deviation_norm": round(0.018 + 0.0038 * cobb + 0.016 * geometry_latent + noise[2], 6),
                    "projected_rotation_total_deg": round(12.0 + 1.7 * cobb + 5.0 * geometry_latent + noise[3] * 100.0, 6),
                    "projected_curvature_energy": round(0.025 + 0.0022 * cobb + 0.010 * geometry_latent + noise[4], 6),
                    "cobb_endplate_envelope_deg": round(float(cobb + rng.normal(0.0, 1.2)), 6),
                    "visit_index": visit_idx,
                }
            )

    columns = list(REQUIRED_COLUMNS) + list(GEOMETRY_COLUMNS) + ["visit_index"]
    return pd.DataFrame(rows, columns=columns)


def validate_longitudinal_schema(visits: pd.DataFrame, require_followup: bool = True) -> pd.DataFrame:
    """Validate and coerce a longitudinal visit table.

    Returns a sorted copy with parsed dates and numeric clinical columns.
    Raises ValueError with a concrete reason when a table cannot support
    progression labeling.
    """

    missing = [column for column in REQUIRED_COLUMNS if column not in visits.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

    frame = visits.copy()
    frame["patient_id"] = frame["patient_id"].astype(str).str.strip()
    frame["curve_region"] = frame["curve_region"].astype(str).str.strip()
    frame["sex"] = frame["sex"].astype(str).str.strip()
    frame["brace_status"] = frame["brace_status"].astype(str).str.strip()
    frame["source_dataset"] = frame["source_dataset"].astype(str).str.strip()

    for column in ["patient_id", "curve_region", "sex", "brace_status", "source_dataset"]:
        if (frame[column] == "").any():
            raise ValueError(f"{column} contains empty values")

    frame["visit_date"] = pd.to_datetime(frame["visit_date"], errors="coerce")
    if frame["visit_date"].isna().any():
        raise ValueError("visit_date contains invalid dates")

    for column in ["age_years", "cobb_angle_deg", "risser_stage"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if not np.isfinite(frame[column].to_numpy(dtype=float)).all():
            raise ValueError(f"{column} contains non-finite values")

    if not frame["age_years"].between(5.0, 25.0).all():
        raise ValueError("age_years must be between 5 and 25 for the AIS validation frame")
    if not frame["cobb_angle_deg"].between(0.0, 130.0).all():
        raise ValueError("cobb_angle_deg must be between 0 and 130")
    if not frame["risser_stage"].between(0.0, 5.0).all():
        raise ValueError("risser_stage must be between 0 and 5")

    duplicate_mask = frame.duplicated(["patient_id", "curve_region", "visit_date"], keep=False)
    if duplicate_mask.any():
        first = frame.loc[duplicate_mask, ["patient_id", "curve_region", "visit_date"]].iloc[0]
        raise ValueError(
            "duplicate same-day visit for "
            f"{first['patient_id']} / {first['curve_region']} / {first['visit_date'].date().isoformat()}"
        )

    frame = frame.sort_values(["patient_id", "curve_region", "visit_date"]).reset_index(drop=True)
    if require_followup:
        visit_counts = frame.groupby(["patient_id", "curve_region"], dropna=False).size()
        singletons = visit_counts[visit_counts < 2]
        if len(singletons):
            first_patient, first_region = singletons.index[0]
            raise ValueError(f"single-visit trajectory: {first_patient} / {first_region}")

    return frame


def build_progression_table(visits: pd.DataFrame) -> pd.DataFrame:
    """Collapse visits into one baseline-to-final trajectory per patient curve."""

    frame = validate_longitudinal_schema(visits, require_followup=True)
    rows: list[dict[str, Any]] = []

    for (patient_id, curve_region), group in frame.groupby(["patient_id", "curve_region"], sort=True):
        baseline = group.iloc[0]
        final = group.iloc[-1]
        followup_days = int((final["visit_date"] - baseline["visit_date"]).days)
        if followup_days <= 0:
            raise ValueError(f"non-positive follow-up interval: {patient_id} / {curve_region}")

        followup_years = followup_days / 365.25
        delta_cobb = float(final["cobb_angle_deg"] - baseline["cobb_angle_deg"])
        annualized = delta_cobb / followup_years
        sex_value = str(baseline["sex"]).upper()
        brace_value = str(baseline["brace_status"]).strip().lower()

        row: dict[str, Any] = {
            "patient_id": patient_id,
            "curve_region": curve_region,
            "source_dataset": baseline["source_dataset"],
            "baseline_visit_date": baseline["visit_date"].date().isoformat(),
            "final_visit_date": final["visit_date"].date().isoformat(),
            "followup_years": float(followup_years),
            "n_visits": int(len(group)),
            "baseline_age_years": float(baseline["age_years"]),
            "final_age_years": float(final["age_years"]),
            "sex": baseline["sex"],
            "sex_female": 1.0 if sex_value.startswith("F") else 0.0,
            "baseline_risser_stage": float(baseline["risser_stage"]),
            "final_risser_stage": float(final["risser_stage"]),
            "baseline_brace_status": baseline["brace_status"],
            "baseline_braced": 1.0 if brace_value in {"braced", "brace", "yes", "active"} else 0.0,
            "baseline_cobb_angle_deg": float(baseline["cobb_angle_deg"]),
            "final_cobb_angle_deg": float(final["cobb_angle_deg"]),
            "delta_cobb_deg": delta_cobb,
            "annualized_cobb_change_deg": float(annualized),
            "progressed_5deg": bool(delta_cobb >= 5.0),
            "progressed_6deg": bool(delta_cobb > 6.0),
            "crossed_40deg": bool(float(baseline["cobb_angle_deg"]) < 40.0 <= float(final["cobb_angle_deg"])),
            "crossed_50deg": bool(float(baseline["cobb_angle_deg"]) < 50.0 <= float(final["cobb_angle_deg"])),
        }

        for column in GEOMETRY_COLUMNS:
            if column in group.columns:
                row[f"baseline_{column}"] = float(pd.to_numeric(baseline[column], errors="coerce"))

        rows.append(row)

    return pd.DataFrame(rows)


def model_specs_for_table(progressions: pd.DataFrame) -> list[ModelSpec]:
    """Return predictor sets available for a progression table."""

    specs = [
        ModelSpec("cobb_only", ("baseline_cobb_angle_deg",)),
        ModelSpec("maturity_only", ("baseline_age_years", "baseline_risser_stage", "sex_female")),
    ]
    geometry_predictors = tuple(
        f"baseline_{column}" for column in GEOMETRY_COLUMNS if f"baseline_{column}" in progressions.columns
    )
    if geometry_predictors:
        specs.append(ModelSpec("geometry_only", geometry_predictors))
        specs.append(
            ModelSpec(
                "combined_theory",
                (
                    "baseline_cobb_angle_deg",
                    "baseline_age_years",
                    "baseline_risser_stage",
                    "sex_female",
                    *geometry_predictors,
                ),
            )
        )
    return specs


def evaluate_progression_models(progressions: pd.DataFrame) -> pd.DataFrame:
    """Evaluate binary and continuous progression endpoints for all model specs."""

    specs = model_specs_for_table(progressions)
    rows: list[dict[str, Any]] = []
    for target in ["progressed_5deg", "progressed_6deg", "crossed_40deg", "crossed_50deg"]:
        if target in progressions.columns:
            counts = progressions[target].astype(int).value_counts()
            if len(counts) == 2 and int(counts.min()) >= 2:
                for spec in specs:
                    rows.append(_binary_metrics(progressions, target, spec))

    for spec in specs:
        rows.append(_regression_metrics(progressions, "annualized_cobb_change_deg", spec))

    return pd.DataFrame(rows)


def summarize_longitudinal_run(
    visits: pd.DataFrame,
    progressions: pd.DataFrame,
    metrics: pd.DataFrame,
    dataset_kind: str,
) -> dict[str, Any]:
    """Build a JSON-serializable summary for report outputs."""

    binary = metrics[metrics["task"] == "binary"].copy()
    best_binary: list[dict[str, Any]] = []
    if len(binary):
        for target, group in binary.groupby("target"):
            ordered = group.sort_values("auroc", ascending=False, na_position="last")
            best_binary.append(_clean_dict(ordered.iloc[0].to_dict()))

    regression = metrics[metrics["task"] == "regression"].copy()
    best_regression: dict[str, Any] | None = None
    if len(regression):
        best_regression = _clean_dict(regression.sort_values("mae").iloc[0].to_dict())

    return {
        "phase": "phase2_longitudinal_progression",
        "dataset_kind": dataset_kind,
        "source_datasets": sorted(str(value) for value in visits["source_dataset"].unique()),
        "n_visits": int(len(visits)),
        "n_trajectories": int(len(progressions)),
        "n_patients": int(progressions["patient_id"].nunique()),
        "followup_years_median": float(progressions["followup_years"].median()),
        "baseline_cobb_median": float(progressions["baseline_cobb_angle_deg"].median()),
        "delta_cobb_median": float(progressions["delta_cobb_deg"].median()),
        "progression_counts": {
            "progressed_5deg": int(progressions["progressed_5deg"].sum()),
            "progressed_6deg": int(progressions["progressed_6deg"].sum()),
            "crossed_40deg": int(progressions["crossed_40deg"].sum()),
            "crossed_50deg": int(progressions["crossed_50deg"].sum()),
        },
        "best_binary_models": best_binary,
        "best_regression_model": best_regression,
        "limitations": [
            "Synthetic demo data verifies software wiring only and is not evidence for the biological theory.",
            "Real patient-level longitudinal validation requires dated visits with growth or maturity covariates.",
            "Ingested radiograph-only resources need identity-preserving visit linkage before progression testing.",
        ],
    }


def _binary_metrics(progressions: pd.DataFrame, target: str, spec: ModelSpec) -> dict[str, Any]:
    frame = _finite_model_frame(progressions, [target, *spec.predictors])
    y = frame[target].astype(int).to_numpy()
    x = frame[list(spec.predictors)].to_numpy(dtype=float)
    predictions, evaluation = _cross_validated_logistic_predictions(x, y)
    return {
        "task": "binary",
        "target": target,
        "model": spec.name,
        "predictors": ",".join(spec.predictors),
        "n": int(len(frame)),
        "positives": int(y.sum()),
        "prevalence": float(np.mean(y)),
        "evaluation": evaluation,
        "auroc": _auroc(y, predictions),
        "average_precision": _average_precision(y, predictions),
        "brier_score": float(np.mean((predictions - y) ** 2)),
        "calibration": _calibration_table(y, predictions),
    }


def _regression_metrics(progressions: pd.DataFrame, target: str, spec: ModelSpec) -> dict[str, Any]:
    frame = _finite_model_frame(progressions, [target, *spec.predictors])
    y = frame[target].to_numpy(dtype=float)
    x = frame[list(spec.predictors)].to_numpy(dtype=float)
    predictions, evaluation = _cross_validated_ridge_predictions(x, y)
    residual = y - predictions
    ss_total = float(np.sum((y - np.mean(y)) ** 2))
    ss_residual = float(np.sum(residual**2))
    r2 = float(1.0 - ss_residual / ss_total) if ss_total > 0.0 else float("nan")
    return {
        "task": "regression",
        "target": target,
        "model": spec.name,
        "predictors": ",".join(spec.predictors),
        "n": int(len(frame)),
        "evaluation": evaluation,
        "r2": r2,
        "mae": float(np.mean(np.abs(residual))),
        "rmse": float(np.sqrt(np.mean(residual**2))),
    }


def _finite_model_frame(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    out = frame.copy()
    for column in columns:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    mask = np.isfinite(out[list(columns)].to_numpy(dtype=float)).all(axis=1)
    return out.loc[mask].copy()


def _cross_validated_logistic_predictions(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, str]:
    folds = _stratified_folds(y)
    if len(folds) < 2:
        x_train, x_eval = _standardize(x, x)
        beta = _fit_logistic_ridge(x_train, y)
        return expit(_add_intercept(x_eval) @ beta), "in_sample_fallback"

    predictions = np.zeros(len(y), dtype=float)
    for fold in folds:
        train = np.setdiff1d(np.arange(len(y)), fold)
        if len(np.unique(y[train])) < 2:
            predictions[fold] = float(np.mean(y[train]))
            continue
        x_train, x_test = _standardize(x[train], x[fold])
        beta = _fit_logistic_ridge(x_train, y[train])
        predictions[fold] = expit(_add_intercept(x_test) @ beta)
    return predictions, f"stratified_{len(folds)}fold_cv"


def _cross_validated_ridge_predictions(x: np.ndarray, y: np.ndarray, l2: float = 1.0) -> tuple[np.ndarray, str]:
    if len(y) < 6:
        x_train, x_eval = _standardize(x, x)
        beta = _fit_ridge(x_train, y, l2=l2)
        return _add_intercept(x_eval) @ beta, "in_sample_fallback"

    n_splits = min(5, len(y))
    predictions = np.zeros(len(y), dtype=float)
    for fold in np.array_split(np.arange(len(y)), n_splits):
        train = np.setdiff1d(np.arange(len(y)), fold)
        x_train, x_test = _standardize(x[train], x[fold])
        beta = _fit_ridge(x_train, y[train], l2=l2)
        predictions[fold] = _add_intercept(x_test) @ beta
    return predictions, f"{n_splits}fold_cv"


def _fit_logistic_ridge(x: np.ndarray, y: np.ndarray, l2: float = 1.0) -> np.ndarray:
    x_design = _add_intercept(x)

    def objective(beta: np.ndarray) -> float:
        logits = x_design @ beta
        loss = float(np.sum(np.logaddexp(0.0, logits) - y * logits))
        penalty = 0.5 * l2 * float(np.sum(beta[1:] ** 2))
        return loss + penalty

    result = minimize(objective, np.zeros(x_design.shape[1]), method="BFGS")
    if not result.success:
        return np.zeros(x_design.shape[1])
    return result.x


def _fit_ridge(x: np.ndarray, y: np.ndarray, l2: float = 1.0) -> np.ndarray:
    x_design = _add_intercept(x)
    penalty = np.eye(x_design.shape[1]) * l2
    penalty[0, 0] = 0.0
    return np.linalg.solve(x_design.T @ x_design + penalty, x_design.T @ y)


def _standardize(train: np.ndarray, test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    center = np.nanmean(train, axis=0)
    scale = np.nanstd(train, axis=0)
    scale = np.where(scale > 1e-12, scale, 1.0)
    return (train - center) / scale, (test - center) / scale


def _add_intercept(x: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(x)), x])


def _stratified_folds(y: np.ndarray, max_splits: int = 5) -> list[np.ndarray]:
    classes, counts = np.unique(y, return_counts=True)
    if len(classes) < 2 or int(np.min(counts)) < 2:
        return []
    n_splits = min(max_splits, int(np.min(counts)))
    folds: list[list[int]] = [[] for _ in range(n_splits)]
    for value in classes:
        indices = np.flatnonzero(y == value)
        for pos, index in enumerate(indices):
            folds[pos % n_splits].append(int(index))
    return [np.asarray(sorted(fold), dtype=int) for fold in folds if fold]


def _auroc(y_true: np.ndarray, scores: np.ndarray) -> float:
    positives = int(np.sum(y_true == 1))
    negatives = int(np.sum(y_true == 0))
    if positives == 0 or negatives == 0:
        return float("nan")
    ranks = rankdata(scores)
    rank_sum_pos = float(np.sum(ranks[y_true == 1]))
    return float((rank_sum_pos - positives * (positives + 1) / 2.0) / (positives * negatives))


def _average_precision(y_true: np.ndarray, scores: np.ndarray) -> float:
    positives = int(np.sum(y_true == 1))
    if positives == 0:
        return float("nan")
    order = np.argsort(-scores)
    y_sorted = y_true[order]
    hit_count = 0
    precision_sum = 0.0
    for rank, value in enumerate(y_sorted, start=1):
        if value == 1:
            hit_count += 1
            precision_sum += hit_count / rank
    return float(precision_sum / positives)


def _calibration_table(y_true: np.ndarray, scores: np.ndarray, n_bins: int = 5) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    for idx in range(n_bins):
        left = edges[idx]
        right = edges[idx + 1]
        if idx == n_bins - 1:
            mask = (scores >= left) & (scores <= right)
        else:
            mask = (scores >= left) & (scores < right)
        if not np.any(mask):
            continue
        rows.append(
            {
                "bin": f"{left:.1f}-{right:.1f}",
                "n": int(mask.sum()),
                "mean_prediction": float(np.mean(scores[mask])),
                "observed_rate": float(np.mean(y_true[mask])),
            }
        )
    return rows


def _clean_dict(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, (np.integer, np.floating)):
            value = value.item()
        if isinstance(value, float) and not math.isfinite(value):
            value = None
        out[key] = value
    return out

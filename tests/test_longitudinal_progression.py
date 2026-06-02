"""Tests for Phase 2 longitudinal progression validation."""

import numpy as np
import pandas as pd
import pytest

from spinalmodes.longitudinal import (
    build_progression_table,
    evaluate_progression_models,
    generate_demo_cohort,
    validate_longitudinal_schema,
)


def _valid_visits() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "patient_id": "P001",
                "visit_date": "2020-01-01",
                "age_years": 12.0,
                "sex": "F",
                "cobb_angle_deg": 12.0,
                "curve_region": "thoracic",
                "risser_stage": 0,
                "brace_status": "none",
                "source_dataset": "fixture",
                "tortuosity": 1.05,
                "lateral_span_norm": 0.12,
                "max_chord_deviation_norm": 0.08,
                "projected_rotation_total_deg": 35.0,
                "projected_curvature_energy": 0.12,
                "cobb_endplate_envelope_deg": 13.0,
            },
            {
                "patient_id": "P001",
                "visit_date": "2021-01-01",
                "age_years": 13.0,
                "sex": "F",
                "cobb_angle_deg": 18.0,
                "curve_region": "thoracic",
                "risser_stage": 1,
                "brace_status": "none",
                "source_dataset": "fixture",
                "tortuosity": 1.08,
                "lateral_span_norm": 0.15,
                "max_chord_deviation_norm": 0.10,
                "projected_rotation_total_deg": 44.0,
                "projected_curvature_energy": 0.18,
                "cobb_endplate_envelope_deg": 18.5,
            },
            {
                "patient_id": "P002",
                "visit_date": "2020-06-01",
                "age_years": 13.5,
                "sex": "M",
                "cobb_angle_deg": 39.0,
                "curve_region": "lumbar",
                "risser_stage": 2,
                "brace_status": "braced",
                "source_dataset": "fixture",
                "tortuosity": 1.16,
                "lateral_span_norm": 0.23,
                "max_chord_deviation_norm": 0.18,
                "projected_rotation_total_deg": 72.0,
                "projected_curvature_energy": 0.26,
                "cobb_endplate_envelope_deg": 40.0,
            },
            {
                "patient_id": "P002",
                "visit_date": "2022-06-01",
                "age_years": 15.5,
                "sex": "M",
                "cobb_angle_deg": 41.0,
                "curve_region": "lumbar",
                "risser_stage": 4,
                "brace_status": "braced",
                "source_dataset": "fixture",
                "tortuosity": 1.17,
                "lateral_span_norm": 0.24,
                "max_chord_deviation_norm": 0.19,
                "projected_rotation_total_deg": 75.0,
                "projected_curvature_energy": 0.28,
                "cobb_endplate_envelope_deg": 41.5,
            },
        ]
    )


def test_schema_validation_accepts_valid_fixture():
    validated = validate_longitudinal_schema(_valid_visits())
    assert len(validated) == 4
    assert str(validated["visit_date"].dtype).startswith("datetime64")


def test_schema_validation_requires_core_columns():
    visits = _valid_visits().drop(columns=["risser_stage"])
    with pytest.raises(ValueError, match="missing required columns"):
        validate_longitudinal_schema(visits)


@pytest.mark.parametrize(
    ("column", "value", "match"),
    [
        ("visit_date", "not-a-date", "invalid dates"),
        ("cobb_angle_deg", 140.0, "cobb_angle_deg"),
        ("age_years", 30.0, "age_years"),
        ("risser_stage", 8, "risser_stage"),
    ],
)
def test_schema_validation_rejects_invalid_values(column, value, match):
    visits = _valid_visits()
    visits.loc[0, column] = value
    with pytest.raises(ValueError, match=match):
        validate_longitudinal_schema(visits)


def test_schema_validation_rejects_duplicate_same_day_visits():
    visits = _valid_visits()
    duplicate = visits.iloc[[0]].copy()
    visits = pd.concat([visits, duplicate], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate same-day visit"):
        validate_longitudinal_schema(visits)


def test_schema_validation_rejects_single_visit_trajectories():
    visits = _valid_visits().iloc[:1].copy()
    with pytest.raises(ValueError, match="single-visit trajectory"):
        validate_longitudinal_schema(visits)


def test_progression_labels_match_threshold_definitions():
    progressions = build_progression_table(_valid_visits()).sort_values("patient_id")
    p1 = progressions.iloc[0]
    p2 = progressions.iloc[1]

    assert p1["delta_cobb_deg"] == pytest.approx(6.0)
    assert bool(p1["progressed_5deg"]) is True
    assert bool(p1["progressed_6deg"]) is False

    assert p2["delta_cobb_deg"] == pytest.approx(2.0)
    assert bool(p2["crossed_40deg"]) is True
    assert bool(p2["progressed_5deg"]) is False


def test_demo_generation_is_deterministic():
    first = generate_demo_cohort(n_patients=12, seed=123)
    second = generate_demo_cohort(n_patients=12, seed=123)
    third = generate_demo_cohort(n_patients=12, seed=124)

    assert first.equals(second)
    assert not first.equals(third)
    assert first["source_dataset"].eq("synthetic_phase2_demo").all()


def test_model_evaluation_smoke_on_demo_cohort():
    visits = generate_demo_cohort(n_patients=60, seed=321)
    progressions = build_progression_table(visits)
    metrics = evaluate_progression_models(progressions)

    assert {"cobb_only", "maturity_only", "geometry_only", "combined_theory"}.issubset(
        set(metrics["model"])
    )
    binary = metrics[(metrics["task"] == "binary") & (metrics["target"] == "progressed_5deg")]
    assert not binary.empty
    assert np.isfinite(binary["auroc"]).all()
    assert (binary["n"] == len(progressions)).all()

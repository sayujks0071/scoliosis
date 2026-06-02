# Phase 2 Longitudinal Progression Protocol

## Objective

Phase 2 tests whether baseline AP landmark geometry and maturity variables improve prediction of adolescent idiopathic scoliosis progression beyond a Cobb-only baseline. This is the operational bridge from the open SpineWeb landmark geometry validation to a time-dependent progression claim.

## Required Visit Schema

Each row is one dated patient visit for one curve region. The required columns are:

| Column | Meaning |
|---|---|
| `patient_id` | Stable de-identified patient key. |
| `visit_date` | ISO-like date parseable by pandas. |
| `age_years` | Age at visit, expected AIS validation range 5 to 25. |
| `sex` | Sex label from source dataset. |
| `cobb_angle_deg` | Cobb angle in degrees, expected range 0 to 130. |
| `curve_region` | Curve region such as thoracic, thoracolumbar, or lumbar. |
| `risser_stage` | Skeletal maturity stage, expected range 0 to 5. |
| `brace_status` | Baseline treatment exposure label when known. |
| `source_dataset` | Dataset/provenance label. |

Optional baseline geometry columns are compatible with the open SpineWeb extraction layer: `tortuosity`, `lateral_span_norm`, `max_chord_deviation_norm`, `projected_rotation_total_deg`, `projected_curvature_energy`, and `cobb_endplate_envelope_deg`.

## Progression Endpoints

The validation script collapses each patient/curve trajectory to first visit versus final visit and computes:

| Endpoint | Definition |
|---|---|
| `delta_cobb_deg` | Final Cobb minus baseline Cobb. |
| `followup_years` | Final date minus baseline date, divided by 365.25. |
| `annualized_cobb_change_deg` | `delta_cobb_deg / followup_years`. |
| `progressed_5deg` | `delta_cobb_deg >= 5`. |
| `progressed_6deg` | `delta_cobb_deg > 6`. |
| `crossed_40deg` | Baseline below 40 degrees and final at or above 40 degrees. |
| `crossed_50deg` | Baseline below 50 degrees and final at or above 50 degrees. |

## Model Comparisons

Phase 2 uses inspectable baselines before complex simulation:

| Model | Predictors |
|---|---|
| `cobb_only` | Baseline Cobb angle. |
| `maturity_only` | Baseline age, Risser stage, and sex-female indicator. |
| `geometry_only` | Available baseline geometry fields. |
| `combined_theory` | Cobb, maturity, and geometry fields together. |

Binary endpoints use ridge-regularized logistic regression with deterministic stratified cross-validation when class counts allow it. Continuous annualized Cobb change uses ridge regression with deterministic folds. Metrics are written as AUROC, average precision, Brier score, R2, MAE, and RMSE.

## Interpretation Guardrails

- The committed demo cohort is synthetic and only verifies the software pipeline.
- The open SpineWeb/AASCE data validate geometry extraction but do not include longitudinal progression, growth stage, or treatment exposure.
- A real-data Phase 2 claim requires identity-preserving longitudinal visits with dated Cobb measurements and maturity covariates.
- Radiograph-only datasets need de-identification-safe patient linkage before they can test progression.

# Phase 2 Longitudinal Progression Validation

## Dataset

- Dataset kind: `synthetic_demo`
- Source datasets: synthetic_phase2_demo
- Visits: 320
- Baseline-to-final trajectories: 160
- Median follow-up: 1.53 years
- Median baseline Cobb angle: 16.53 degrees
- Median Cobb change: 6.04 degrees

## Progression Counts

| Endpoint | Count |
|---|---:|
| `progressed_5deg` | 91 |
| `progressed_6deg` | 80 |
| `crossed_40deg` | 5 |
| `crossed_50deg` | 1 |

## Binary Model Comparison

| target | model | n | positives | auroc | average_precision | brier_score |
|---|---|---|---|---|---|---|
| progressed_5deg | cobb_only | 160 | 91.000 | 0.744 | 0.781 | 0.203 |
| progressed_5deg | maturity_only | 160 | 91.000 | 0.660 | 0.715 | 0.233 |
| progressed_5deg | geometry_only | 160 | 91.000 | 0.790 | 0.825 | 0.185 |
| progressed_5deg | combined_theory | 160 | 91.000 | 0.775 | 0.817 | 0.193 |
| progressed_6deg | cobb_only | 160 | 80.000 | 0.739 | 0.739 | 0.207 |
| progressed_6deg | maturity_only | 160 | 80.000 | 0.617 | 0.623 | 0.242 |
| progressed_6deg | geometry_only | 160 | 80.000 | 0.787 | 0.795 | 0.189 |
| progressed_6deg | combined_theory | 160 | 80.000 | 0.767 | 0.777 | 0.198 |
| crossed_40deg | cobb_only | 160 | 5.000 | 0.970 | 0.606 | 0.021 |
| crossed_40deg | maturity_only | 160 | 5.000 | 0.734 | 0.100 | 0.030 |
| crossed_40deg | geometry_only | 160 | 5.000 | 0.985 | 0.715 | 0.017 |
| crossed_40deg | combined_theory | 160 | 5.000 | 0.995 | 0.885 | 0.013 |

## Annualized Cobb Change Model Comparison

| model | n | r2 | mae | rmse |
|---|---|---|---|---|
| cobb_only | 160 | 0.300 | 1.867 | 2.343 |
| maturity_only | 160 | 0.066 | 2.261 | 2.706 |
| geometry_only | 160 | 0.425 | 1.707 | 2.124 |
| combined_theory | 160 | 0.444 | 1.667 | 2.087 |

## Outputs

- Progression table: `/home/sayuj/jupyterlab/scoliosis/results/longitudinal/phase2_progression_table.csv`
- Model metrics: `/home/sayuj/jupyterlab/scoliosis/results/longitudinal/phase2_model_metrics.csv`

## Interpretation Guardrails

- Binary endpoints are modeled only when both classes have at least two trajectories; rare threshold crossings are counted but not benchmarked.
- Synthetic demo data verifies software wiring only and is not evidence for the biological theory.
- Real patient-level longitudinal validation requires dated visits with growth or maturity covariates.
- Ingested radiograph-only resources need identity-preserving visit linkage before progression testing.

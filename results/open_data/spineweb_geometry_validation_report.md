# SpineWeb Open Landmark Geometry Validation

## Dataset

This analysis uses the free SpineWeb/AASCE 2019 curated landmark annotations from Zenodo.
The package contains T1-L5 quadrilateral landmarks for AP spine radiographs and correction-quality flags.

- Total cases: 609
- Train/test cases: 481 / 128
- Usable cases by correction flags: 534
- Usable complete T1-L5 cases: 534

## Derived Endpoints

The primary endpoint is `cobb_endplate_envelope_deg`, defined as the maximum acute angle between any two annotated vertebral endplate lines.
Secondary endpoints quantify centerline shape in the AP projection: normalized lateral deviation, lateral span, tortuosity, total projected turn, projected curvature energy, and a centerline boundary-angle proxy.

## Main Results

- Median derived Cobb-like envelope in usable cases: 40.82 degrees.
- Interquartile range: 29.18 to 53.88 degrees.
- Usable cases with Cobb-like envelope >=10/20/40 degrees: 529 / 478 / 275.

Strongest rank correlations with the primary endpoint:

- `tortuosity`: Spearman rho=0.964, 95% CI [0.957, 0.969], p=1.85e-307, n=534
- `lateral_span_norm`: Spearman rho=0.908, 95% CI [0.892, 0.922], p=1.77e-203, n=534
- `max_chord_deviation_norm`: Spearman rho=0.901, 95% CI [0.884, 0.916], p=1.52e-195, n=534
- `projected_rotation_total_deg`: Spearman rho=0.896, 95% CI [0.878, 0.912], p=8.31e-190, n=534

## Quality Sensitivity

Good annotations had median Cobb-like envelope 41.65 degrees (n=363); non-good usable annotations had median 37.87 degrees (n=171).
Mann-Whitney U p-value for good vs non-good usable cases: 0.0101.

## Interpretation

This validates that the open landmark pipeline produces coherent geometric endpoints: derived endplate angle, lateral deviation, tortuosity, and projected curvature move together in the expected direction.
It does not validate the full AIS progression mechanism because this open package lacks growth stage, treatment exposure, serial Cobb measurements, and progression labels.

## Output Files

- Feature table: `/home/sayuj/jupyterlab/scoliosis/results/open_data/spineweb_landmark_features.csv`
- Validation summary: `/home/sayuj/jupyterlab/scoliosis/results/open_data/spineweb_geometry_validation_summary.json`
- Manual-review outliers: `/home/sayuj/jupyterlab/scoliosis/results/open_data/spineweb_geometry_validation_outliers.csv`
- Figure panels: `/home/sayuj/jupyterlab/scoliosis/results/open_data/spineweb_geometry_validation_panels.png`

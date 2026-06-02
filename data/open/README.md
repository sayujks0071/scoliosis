# Open Spine Data

This directory tracks free/open datasets that can support the next validation
stage of the scoliosis project.

## SpineWeb / AASCE 2019 Landmark Annotations

- Source: https://aasce19.github.io/
- Curated annotations: https://zenodo.org/records/4413665
- Local files:
  - `spineweb_curated/annotations_train.zip`
  - `spineweb_curated/annotations_test.zip`
  - `spineweb_curated/correction_train.csv`
  - `spineweb_curated/correction_test.csv`
  - `spineweb_curated/annotations_train/*.xml`
  - `spineweb_curated/annotations_test/*.xml`
- Contents: AP spine radiograph landmark annotations, T1-L5. Each vertebra is
  represented by four corner points.
- Immediate use: open landmark-only geometry validation. This supports
  Cobb-like endplate envelopes, centerline deviation, planar curvature, and
  projected rotation proxies without needing image pixels.
- Limitation: this is not a longitudinal AIS progression registry. It does not
  directly provide growth velocity, Risser/Sanders staging, bracing exposure, or
  12-month progression outcomes.

## Other Free Sources To Track

- Scoliosis1K: https://zhouzi180.github.io/Scoliosis1K/
- VerSe vertebral segmentation challenge: https://github.com/anjany/verse
- Mendeley scoliosis angle/vertebra datasets:
  - https://data.mendeley.com/datasets/ssfmrw2fg9/2
  - https://data.mendeley.com/datasets/4kby36n3ng/2
- ISICO brace sensor dataset: https://zenodo.org/records/8305775
- MSK EOS database: https://mskdatabase.com/

The highest-value next external dataset is still a retrospective clinical
cohort with serial Cobb angle, growth stage, treatment exposure, and progression
labels. The open landmark datasets can validate geometric endpoints, but not the
full derivative-gain/progression hypothesis by themselves.

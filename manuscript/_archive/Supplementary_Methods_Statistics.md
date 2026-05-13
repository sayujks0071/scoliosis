# Comprehensive Statistical Summary

| Finding | Metric / Effect Size | Statistical Test | p-value | Significance / Strength |
| --- | --- | --- | --- | --- |
| Cross-Species Allometric Scaling | Exponent = -0.282 | Log-log regression | 1.31×10⁻³ | STRONG. 95% CI: [-0.347, -0.117], metabolic prediction (-0.25) within interval. |
| Anisotropy Rescue Effect | R² = 0.775 | Linear regression | < 10⁻¹⁷ | STRONG. High anisotropy delays instability. |
| Energy Deficit vs Cobb Angle | r = 0.983 | Pearson correlation | 2.74×10⁻²² | STRONG. Deficit magnitude predicts curve severity. |
| Circadian Disruption | 2.52-fold increase | Mann-Whitney U | 2.6×10⁻⁴ | MODERATE. Dependent on elevated high-coupling. |
| Clinical Cohort Validation | r = 0.899 | Pearson correlation | 3.79×10⁻² | MODERATE. L_crit = 0.35m correlates to onset window (11-14 yrs). |

## Sensitivity Analysis

Filtering out low-confidence AlphaFold structures (pLDDT < 70) retains 8 high-confidence proteins while dropping 7, including LBX1, RUNX3, EGR3, MYLK, PPARGC1A, GHR, ARNTL.
- Original Anisotropy Mean: 2.74
- Filtered Anisotropy Mean: 2.62

The conclusions remain robust and consistent with initial findings despite excluding these low-confidence IDRs.

## Bayesian Model Comparison

Comparing the IEC Framework (Allometric Scaling) against a simple beam model (Constant Gravity Scaling):
- Allometric Model BIC: -22.13
- Constant Model BIC: -10.79
- Delta BIC: 11.34
- Approximate Bayes Factor (Allometric over Constant): 290.0

The evidence strongly supports the allometric model over the constant beam model (BF > 100).

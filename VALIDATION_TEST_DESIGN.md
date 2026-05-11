# Falsifiable Validation Test: Bio-Gravitational Number Hypothesis

**Date:** 2026-05-04  
**Principal Investigator:** Dr Sayuj Krishnan  
**Status:** Design phase — ready for implementation

---

## Analogy to Consciousness-Geometry Ising Test

**Consciousness-geometry experiment:**
- **Hypothesis:** Integrated information (Φ) correlates with emergent geometric curvature (|∂κ/∂h|) in an Ising lattice
- **Operationalization:** 2D classical Ising → pairwise MI → Ollivier-Ricci curvature on MI-graph
- **Result:** NULL (ρ = -0.15, p = 0.53). Correlation drifted toward zero as seeds increased → noise signature
- **Falsification:** The specific Ising proxy does not support the hypothesis

**Spine research test:**
- **Hypothesis:** Bio-Gravitational Number $\mathcal{B}_g = \frac{EI}{MgL^2}$ predicts a critical transition from gravity-dominated (sagging) to information-dominated (S-curve maintenance) at $\mathcal{B}_g \approx 1.0$
- **Operationalization:** PyElastica rod simulations sweeping $\chi_M$ (active muscle tone) → compute $\mathcal{B}_g$ → measure counter-curvature efficiency
- **Prediction:** Sharp phase transition in tip deflection / S-curve emergence at $\mathcal{B}_g \approx 1.0$
- **Null signature:** If counter-curvature efficiency scales continuously (no sharp transition), or if transition point drifts with random seeds → no critical $\mathcal{B}_g$ exists

---

## Core Hypothesis (Testable Claim)

From manuscript §2.3 and `research_schedule_gravity_optimization.md`:

> **Stability Criterion:** $\mathcal{B}_g > 1$ is required for stable counter-curvature against gravity. If $\mathcal{B}_g < 1$, gravity dominates (buckling).

**Specific prediction:** There exists a **critical Bio-Gravitational Number** $\mathcal{B}_g^* \approx 1.0$ where the system transitions from passive gravitational geodesic (sagging rod) to active counter-curved geometry (S-shape). This transition should be:
1. **Sharp** (bifurcation-like, not gradual)
2. **Robust** to parameter noise (consistent across random seeds)
3. **Universal** (same $\mathcal{B}_g^*$ across different rod lengths L, radii r, provided $\mathcal{B}_g$ is held constant)

**Falsification conditions:**
- Transition is gradual/smooth (power-law scaling, no critical point)
- Critical point drifts significantly with seeds (like consciousness-geometry: -0.30 → -0.15 as seeds increased)
- $\mathcal{B}_g^*$ shifts by >50% when changing L or r while nominally holding $\mathcal{B}_g$ constant (dimensionless number fails to collapse data)

---

## Operationalization

### Observable: Counter-Curvature Efficiency $\eta_{CC}$

Define:
$$
\eta_{CC} = 1 - \frac{|z_{tip}|}{|z_{tip}^{passive}|}
$$

where:
- $z_{tip}$ = vertical tip deflection with active IEC coupling ($\chi_M > 0$)
- $z_{tip}^{passive}$ = tip deflection under pure gravity ($\chi_M = 0$, all IEC couplings off)

**Interpretation:**
- $\eta_{CC} = 0$ → No counter-curvature effect (gravity-dominated)
- $\eta_{CC} \to 1$ → Full counter-curvature (information-dominated, tip maintains height)

### Parameter Sweep Design

**Primary sweep variable:** $\chi_M$ (active muscle tone coupling)

**Fixed parameters (baseline):**
- Length $L = 0.5$ m (approximate human spine scale)
- Radius $r = 0.01$ m
- Density $\rho = 1000$ kg/m³
- Young's modulus $E_0 = 1 \times 10^6$ Pa (soft tissue range)
- Gravity $g = 9.81$ m/s²
- Information field: $I(s) = \sin^2(2\pi s/L)$ → $\langle |\nabla I| \rangle \approx 3.14$ (analytical)
- Boundary condition: Fixed base (clamped), free tip
- Simulation time: $t_{final} = 2.0$ s (equilibration)
- Time step: $dt = 10^{-5}$ s

**Computed Bio-Gravitational Number:**
$$
\mathcal{B}_g = \frac{\chi_M \langle |\nabla I| \rangle}{\rho A g L^2}
$$

where $A = \pi r^2$

**Sweep range:** $\chi_M \in [0, 50]$ (logarithmic spacing, 30 points)

**Random seeds:** 8 seeds per $\chi_M$ value → 240 total simulations

**Output metrics per simulation:**
1. $z_{tip}$ — vertical tip deflection (m)
2. $\eta_{CC}$ — counter-curvature efficiency
3. $S_{lat}$ — lateral scoliosis index (from `compute_scoliosis_metrics`)
4. $\theta_{Cobb}$ — Cobb angle (degrees)
5. $E_{bend}$ — bending energy $\int \kappa^2 \, ds$
6. $\mathcal{B}_g$ — computed Bio-Gravitational Number

---

## Statistical Analysis Plan

### Phase 1: Critical Point Identification

**Method:** Fit piecewise sigmoid to $\eta_{CC}(\mathcal{B}_g)$:

$$
\eta_{CC}(\mathcal{B}_g) = \frac{1}{1 + e^{-k(\mathcal{B}_g - \mathcal{B}_g^*)}}
$$

where:
- $\mathcal{B}_g^*$ = critical Bio-Gravitational Number
- $k$ = sharpness parameter (analogous to inverse correlation length)

**Null hypothesis:** $k \leq 1$ (gradual transition, no critical point)

**Alternative:** $k > 5$ (sharp bifurcation)

**Test statistic:** Bootstrap 95% CI on $k$ from 8-seed ensemble at each $\chi_M$

**Decision rule:** If CI$[k]$ does not exclude 1.0, reject sharp-transition claim.

### Phase 2: Robustness Across Seeds

**Method:** Compute seed-to-seed variance in $\mathcal{B}_g^*$ estimate:

$$
\sigma_{\mathcal{B}_g^*} = \text{std}(\mathcal{B}_g^*[seed_1], \ldots, \mathcal{B}_g^*[seed_8])
$$

**Null hypothesis:** $\sigma_{\mathcal{B}_g^*} / \mathcal{B}_g^* > 0.3$ (drift like consciousness-geometry)

**Alternative:** $\sigma_{\mathcal{B}_g^*} / \mathcal{B}_g^* < 0.1$ (robust critical point)

**Test:** If relative std > 30%, the "critical point" is a noise artifact.

### Phase 3: Universality Test

**Method:** Repeat sweep at 3 different scales:
1. $L = 0.25$ m, $r = 0.005$ m (mouse-scale)
2. $L = 0.5$ m, $r = 0.01$ m (human-scale, baseline)
3. $L = 1.0$ m, $r = 0.02$ m (large animal / giraffe)

For each scale, adjust $\chi_M$ range to cover same $\mathcal{B}_g \in [0.1, 10]$.

**Null hypothesis:** $\mathcal{B}_g^*$ shifts by >50% across scales (dimensionless number fails to collapse data)

**Alternative:** $\mathcal{B}_g^* = 1.0 \pm 0.2$ across all scales (universal critical point)

**Test:** ANOVA on $\mathcal{B}_g^*$ estimates from 3 scales. If $p < 0.05$, universality fails.

---

## Expected Outcomes

### Scenario A: Hypothesis Supported

**Pattern:**
- Sigmoid fit with $k > 5$, $\mathcal{B}_g^* = 1.0 \pm 0.15$
- $\sigma_{\mathcal{B}_g^*} / \mathcal{B}_g^* < 0.1$ (robust across seeds)
- ANOVA $p > 0.05$ (universal across scales)
- Below $\mathcal{B}_g^*$: $\eta_{CC} < 0.2$, large $z_{tip}$ (sagging)
- Above $\mathcal{B}_g^*$: $\eta_{CC} > 0.8$, S-curve emerges

**Interpretation:** $\mathcal{B}_g = 1$ is a genuine phase boundary. Spinal stability requires active maintenance scaling as $L^4$ (since $\mathcal{B}_g \propto \chi_M / L^2$ and maintaining $\mathcal{B}_g = 1$ across L requires $\chi_M \propto L^2$, but biomechanical cost scales $\propto L^4$). This supports the "Allometric Trap" narrative in manuscript.

### Scenario B: Smooth Transition (Gradual Scaling)

**Pattern:**
- Sigmoid fit with $k < 2$, or better fit by power law $\eta_{CC} \propto \mathcal{B}_g^\alpha$
- No identifiable critical point
- $\eta_{CC}$ increases continuously from 0 to 1 over broad $\mathcal{B}_g$ range

**Interpretation:** No sharp phase transition exists. Counter-curvature efficiency scales smoothly with active effort. $\mathcal{B}_g = 1$ is not a critical threshold — it's a convenient normalization. Falsifies the "critical Bio-Gravitational Number" claim. Manuscript narrative must shift to "scaling law" without invoking critical phenomena.

### Scenario C: Noise-Dominated (Like Consciousness-Geometry)

**Pattern:**
- Fitted $\mathcal{B}_g^*$ drifts from 0.7 → 1.2 → 1.5 as seeds increase 3 → 5 → 8
- $\sigma_{\mathcal{B}_g^*} / \mathcal{B}_g^* > 0.4$
- Universality test shows $\mathcal{B}_g^*$ at mouse-scale = 0.5, human-scale = 1.2, giraffe-scale = 2.0 (inconsistent)

**Interpretation:** The "critical point" is a noise artifact. PyElastica simulations are too sensitive to initial conditions / numerical stochness at the tested parameter regime. The Bio-Gravitational Number framework is not robustly falsifiable via this computational operationalization. Requires either:
1. Different observable (e.g., frequency of S-curve emergence in stochastic ensemble)
2. Different simulator (e.g., coarse-grained analytical model)
3. Empirical animal data (direct measurement of $\chi_M$, $L$, and S-curve prevalence)

### Scenario D: Non-Universal (Scale-Dependent)

**Pattern:**
- Sharp transition exists ($k > 5$), robust to seeds
- BUT: $\mathcal{B}_g^*$ varies with scale: mouse = 0.6, human = 1.0, giraffe = 1.5

**Interpretation:** The dimensionless number $\mathcal{B}_g$ is mis-specified. Missing a scale-dependent factor (e.g., metabolic rate scaling, $\propto L^{-1/4}$ per West et al.). Manuscript claim of "universal scaling law" fails. Suggests additional biological constraints not captured in pure mechanics.

---

## Implementation Checklist

### Code Modifications

Starting from existing `src/spinalmodes/experiments/bio_gravitational_experiment.py`:

1. **Extend $\chi_M$ sweep:**
   - Current: `[0.0, 2.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0]` (8 points)
   - New: Logarithmic `np.logspace(-1, np.log10(50), 30)` → 30 points covering $\mathcal{B}_g \in [0.01, 10]$

2. **Add seed loop:**
   - Wrap simulation in `for seed in range(8):`
   - Set `np.random.seed(seed)` before each `CounterCurvatureRodSystem` initialization
   - Log `seed` in output CSV

3. **Compute $\eta_{CC}$:**
   - Run **baseline simulation** once with $\chi_M = 0$ (all IEC off) → store $z_{tip}^{passive}$
   - For each $\chi_M > 0$: $\eta_{CC} = 1 - |z_{tip}| / |z_{tip}^{passive}|$

4. **Add scale sweep:**
   - Create function `run_scale_sweep(scale_factor)` where:
     - $L \to L \times scale_factor$
     - $r \to r \times scale_factor$
     - Re-normalize $\chi_M$ range to cover same $\mathcal{B}_g$ domain
   - Run for `scale_factor ∈ [0.5, 1.0, 2.0]`

5. **Output CSV schema:**
   ```
   seed, scale, chi_M, Bg, z_tip, z_tip_passive, eta_CC, S_lat, cobb_angle, bending_energy, runtime_sec
   ```

### Analysis Script

New file: `scripts/analysis/validate_bg_critical_point.py`

**Functions:**
1. `fit_sigmoid(Bg_array, eta_CC_array)` → returns `(Bg_star, k, r_squared)`
2. `bootstrap_critical_point(data, n_boot=1000)` → returns CI on $\mathcal{B}_g^*$
3. `test_universality(data_mouse, data_human, data_giraffe)` → ANOVA on $\mathcal{B}_g^*$
4. `plot_phase_diagram(data)` → $\eta_{CC}$ vs $\mathcal{B}_g$ with error bars, sigmoid fit overlay

**Output:**
- `results/validation_phase1_sigmoid_fit.png` — Phase diagram with fit
- `results/validation_phase2_seed_stability.csv` — $\mathcal{B}_g^*$ per seed
- `results/validation_phase3_universality_test.csv` — ANOVA table
- `results/validation_summary.md` — Decision: SUPPORTED / REJECTED / INCONCLUSIVE

---

## Compute Budget

**Per simulation:**
- 50 elements, 2.0 s final time, dt = 1e-5 → 200k time steps
- Estimated runtime: ~30 sec on GB10 (based on existing benchmarks)

**Total simulations:**
- Phase 1+2: 30 $\chi_M$ × 8 seeds × 1 scale = 240 sims → ~2 hours
- Phase 3: 30 $\chi_M$ × 8 seeds × 2 additional scales = 480 sims → ~4 hours
- **Grand total: ~6 hours on GB10**

**Parallelization:** Embarrassingly parallel over ($\chi_M$, seed) tuples. Can run 8 parallel workers → wall-clock ~45 min for full suite.

---

## Decision Criteria (Falsification Protocol)

**PASS (Hypothesis Supported):**
- All 3 phases meet thresholds:
  1. $k > 5$ (sharp transition)
  2. $\sigma_{\mathcal{B}_g^*} / \mathcal{B}_g^* < 0.1$ (robust)
  3. ANOVA $p > 0.05$ (universal)
- $\mathcal{B}_g^* \in [0.85, 1.15]$ (matches theoretical prediction)

**CONDITIONAL PASS (Partial Support):**
- 2 out of 3 phases pass
- Example: Sharp + robust, but non-universal → suggests missing biological factor

**FAIL (Hypothesis Rejected):**
- Phase 1 fails ($k < 2$) → no critical point exists
- Phase 2 fails ($\sigma > 0.3$) → noise artifact (like consciousness-geometry)

**INCONCLUSIVE (Requires Redesign):**
- Simulations fail to equilibrate (numerical instability)
- $\mathcal{B}_g^*$ outside plausible biological range ([0.1, 10])
- Universality test suggests $\mathcal{B}_g$ formulation is incorrect (need to add metabolic scaling term)

---

## Next Steps (Implementation Timeline)

**Week 1 (May 5-11):**
1. Modify `bio_gravitational_experiment.py` per checklist above
2. Run baseline simulation ($\chi_M = 0$) to establish $z_{tip}^{passive}$
3. Test single-scale sweep (human baseline, 8 seeds) → validate CSV output format

**Week 2 (May 12-18):**
1. Run full Phase 1+2 (240 sims, ~2 hrs)
2. Implement `validate_bg_critical_point.py` analysis script
3. Generate Phase 1+2 plots and summary statistics

**Week 3 (May 19-25):**
1. Run Phase 3 (universality test, 480 additional sims, ~4 hrs)
2. Complete ANOVA analysis
3. Generate `VALIDATION_SUMMARY.md` with decision

**Week 4 (May 26-Jun 1):**
1. If PASS → update manuscript §Results with validation confirmation
2. If FAIL → write "Falsification Note" for supplementary materials
3. If INCONCLUSIVE → design follow-up experiment (e.g., analytical toy model)

---

## Relationship to Consciousness-Geometry Experiment

| Aspect | Consciousness-Geometry | Spine Bio-Gravitational |
|--------|------------------------|-------------------------|
| **Hypothesis** | Φ (integrated info) ↔ emergent curvature | $\mathcal{B}_g$ critical point at 1.0 |
| **System** | 2D Ising lattice (equilibrium stat mech) | 1D elastic rod (non-equilibrium mechanics) |
| **Observable** | Spearman ρ(Φ, \|∂κ/∂h\|) | Sigmoid sharpness $k$ of $\eta_{CC}(\mathcal{B}_g)$ |
| **Falsification** | ρ → 0 as seeds increase | $k < 2$ or $\sigma_{\mathcal{B}_g^*} > 0.3$ |
| **Result (prior)** | NULL (ρ = -0.15, p = 0.53) | TBD |
| **Compute cost** | ~66 min (1120 points, CPU) | ~6 hrs (720 points, CPU + PyElastica) |

**Key difference:** Spine test has 3 phases (sharpness + robustness + universality), not just correlation. This guards against false positives from noise.

---

## Open Questions (Deferred to Implementation)

1. **Quasi-static assumption:** Does 2.0 s equilibration time suffice for $\chi_M \to 50$ (high active moment)? May need adaptive $t_{final}$.

2. **Information field choice:** Current $I(s) = \sin^2(2\pi s/L)$ is arbitrary. Should test 2-3 profiles (Gaussian bump, linear gradient, step function) to ensure $\mathcal{B}_g^*$ is profile-independent.

3. **Boundary condition sensitivity:** Fixed-base vs pinned-base vs free-standing. Does $\mathcal{B}_g^*$ shift? (Likely not if dimensionless number is correct, but worth checking.)

4. **Definition of "passive":** Is $\chi_M = 0$ the right baseline, or should we also turn off other IEC channels ($\chi_\kappa$, $\chi_E$)?

5. **Non-equilibrium effects:** If simulations show persistent oscillations (not damped), $\eta_{CC}$ becomes time-dependent. Need to define observable over trajectory, not just endpoint.

---

## Success Metrics (Meta-Level)

**Primary:** Produce a clear PASS / FAIL / INCONCLUSIVE decision within 4 weeks.

**Secondary (regardless of outcome):**
- Reusable analysis pipeline for future validation tests (other observables, other hypotheses)
- If NULL: Honest "Falsification Note" demonstrates scientific rigor (like consciousness-geometry)
- If PASS: Strong computational evidence for critical $\mathcal{B}_g$ → grounds for proposing animal experiments

**Comparison to consciousness-geometry:**
- That test took ~66 min compute, 2 weeks calendar time (including result interpretation)
- This test: ~6 hrs compute, 4 weeks calendar time (more complex analysis, 3-phase protocol)
- Both share principle: **pre-registered falsification conditions, no post-hoc rationalization**

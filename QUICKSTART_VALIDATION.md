# Quick Start: Bio-Gravitational Number Validation Test

**Goal:** Test whether $\mathcal{B}_g = 1.0$ is a critical phase boundary for spinal stability.

**Analogy:** Like the consciousness-geometry Ising test (NULL result: ρ = -0.15, p = 0.53), this test is designed for falsification, not validation.

---

## Prerequisites

```bash
cd /home/sayuj/life
source .venv/bin/activate

# Verify PyElastica is installed
python -c "import pyelastica; print('PyElastica OK')"
```

If PyElastica missing:
```bash
pip install pyelastica
```

---

## Run Validation Test

### Option A: Full Protocol (Phases 1+2+3, ~6 hours on GB10)

```bash
python scripts/experiments/experiment_bg_critical_point_validation.py \
    --phase all \
    --scales 0.5 1.0 2.0 \
    --seeds 8 \
    --chi-M-min 0.1 \
    --chi-M-max 50.0 \
    --n-chi-M 30 \
    --output results/bg_validation/
```

**Output:** `results/bg_validation/bg_validation_results.csv`

Total simulations: 720 (3 scales × 8 seeds × 30 chi_M)  
Estimated time: ~6 hours (30s/sim average)

---

### Option B: Quick Test (Human scale only, 3 seeds, ~45 min)

```bash
python scripts/experiments/experiment_bg_critical_point_validation.py \
    --phase all \
    --scales 1.0 \
    --seeds 3 \
    --chi-M-min 0.1 \
    --chi-M-max 50.0 \
    --n-chi-M 20 \
    --output results/bg_validation_quick/
```

Total simulations: 60 (1 scale × 3 seeds × 20 chi_M)  
Estimated time: ~30 minutes

---

### Option C: Baseline Only (Compute z_tip_passive reference)

```bash
python scripts/experiments/experiment_bg_critical_point_validation.py \
    --phase baseline \
    --scales 0.5 1.0 2.0 \
    --seeds 8 \
    --output results/bg_validation/
```

Total simulations: 24 (3 scales × 8 seeds, chi_M = 0)  
Estimated time: ~12 minutes

---

## Expected Output

CSV columns:
```
seed, scale, chi_M, Bg, z_tip, z_tip_passive, eta_CC, S_lat, cobb_angle, 
bending_energy, shear_energy, gravitational_energy, runtime_sec, peak_memory_mb
```

**Key observable:** `eta_CC` = Counter-Curvature Efficiency = 1 - |z_tip| / |z_tip_passive|

**Hypothesis:** `eta_CC(Bg)` should show **sharp sigmoid transition** at `Bg ≈ 1.0` if critical point exists.

---

## Analysis (Next Step)

Create analysis script at `scripts/analysis/validate_bg_critical_point.py`:

```python
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import f_oneway
import matplotlib.pyplot as plt

def sigmoid(Bg, Bg_star, k):
    """Sigmoid fit: eta_CC = 1 / (1 + exp(-k * (Bg - Bg_star)))"""
    return 1.0 / (1.0 + np.exp(-k * (Bg - Bg_star)))

def fit_critical_point(csv_file):
    df = pd.read_csv(csv_file)
    
    # Phase 1: Fit sigmoid for each scale
    scales = df['scale'].unique()
    results = {}
    
    for scale in scales:
        data = df[df['scale'] == scale]
        
        # Aggregate over seeds at each Bg
        grouped = data.groupby('Bg')['eta_CC'].agg(['mean', 'std']).reset_index()
        Bg_array = grouped['Bg'].values
        eta_CC_mean = grouped['mean'].values
        
        # Fit sigmoid
        try:
            popt, pcov = curve_fit(sigmoid, Bg_array, eta_CC_mean, p0=[1.0, 5.0])
            Bg_star, k = popt
            results[scale] = {'Bg_star': Bg_star, 'k': k}
            
            print(f"Scale {scale}: Bg* = {Bg_star:.3f}, k = {k:.3f}")
        except Exception as e:
            print(f"Scale {scale}: Fit failed ({e})")
    
    # Phase 2: Test robustness (seed-to-seed variance)
    for scale in scales:
        data = df[df['scale'] == scale]
        
        # Fit Bg_star per seed
        seed_Bg_stars = []
        for seed in data['seed'].unique():
            seed_data = data[data['seed'] == seed]
            grouped = seed_data.groupby('Bg')['eta_CC'].mean()
            # (Simplified: just find Bg where eta_CC crosses 0.5)
            crossing = grouped[grouped > 0.5].index
            if len(crossing) > 0:
                seed_Bg_stars.append(crossing[0])
        
        if len(seed_Bg_stars) > 1:
            mean_Bg_star = np.mean(seed_Bg_stars)
            std_Bg_star = np.std(seed_Bg_stars)
            rel_std = std_Bg_star / mean_Bg_star if mean_Bg_star > 0 else 0
            print(f"Scale {scale}: Robustness σ(Bg*)/Bg* = {rel_std:.3f}")
    
    # Phase 3: Universality (ANOVA on Bg_star across scales)
    Bg_star_values = [results[s]['Bg_star'] for s in scales if s in results]
    if len(Bg_star_values) >= 2:
        # Simple range check (proper ANOVA requires replicates)
        Bg_range = max(Bg_star_values) - min(Bg_star_values)
        print(f"\nUniversality: Bg* range = {Bg_range:.3f}")
        if Bg_range < 0.3:
            print("PASS: Bg* is universal across scales")
        else:
            print("FAIL: Bg* varies significantly across scales")

# Usage
fit_critical_point('results/bg_validation/bg_validation_results.csv')
```

Run:
```bash
python scripts/analysis/validate_bg_critical_point.py --input results/bg_validation/bg_validation_results.csv
```

---

## Decision Criteria

**PASS (Hypothesis Supported):**
- Sigmoid sharpness `k > 5` (sharp transition)
- Seed robustness `σ(Bg*)/Bg* < 0.1` (not noise artifact)
- Universality `Bg* range < 0.3` across scales
- `Bg* ∈ [0.85, 1.15]` (matches theoretical prediction)

**FAIL (Hypothesis Rejected):**
- `k < 2` (gradual transition, no critical point)
- `σ(Bg*)/Bg* > 0.3` (noise artifact like consciousness-geometry)
- `Bg*` varies by >50% across scales (dimensionless number mis-specified)

**INCONCLUSIVE:**
- Simulations fail to equilibrate
- `Bg*` outside biological range [0.1, 10]
- Requires redesign (analytical model, different observable)

---

## Comparison to Consciousness-Geometry Test

| Metric | Consciousness-Geometry | Spine Validation |
|--------|------------------------|------------------|
| **System** | 2D Ising lattice | 1D elastic rod (PyElastica) |
| **Hypothesis** | Φ ↔ emergent curvature | Bg = 1 critical point |
| **Observable** | Spearman ρ(Φ, \|∂κ/∂h\|) | Sigmoid sharpness k |
| **Result (prior)** | NULL (ρ → 0 as seeds ↑) | TBD |
| **Compute** | ~66 min (1120 points) | ~6 hrs (720 points) |
| **Falsification** | ρ → 0 noise signature | k < 2 or σ(Bg*) > 0.3 |

---

## Troubleshooting

### PyElastica not converging
- Increase `final_time` from 2.0s to 5.0s (add `--final-time 5.0` arg)
- Check for NaN in output CSV → numerical instability

### Memory issues on GB10
- Reduce `n_elements` from 50 to 30 (coarser mesh)
- Run scales sequentially instead of all at once

### Baseline z_tip_passive ≈ 0
- Rod may not be deflecting under gravity
- Check `base_direction` initialization (should be horizontal)
- Verify gravity acts in -Z direction

---

## Timeline

**Week 1 (May 5-11):**
- Run quick test (Option B, 45 min)
- Implement basic analysis script
- Validate CSV output format, check for NaNs

**Week 2 (May 12-18):**
- Run full protocol (Option A, 6 hrs)
- Complete Phase 1+2 analysis (sigmoid fit + robustness)
- Generate phase diagram plot: eta_CC vs Bg with error bars

**Week 3 (May 19-25):**
- Finalize Phase 3 analysis (universality test)
- Write `VALIDATION_SUMMARY.md` with decision

**Week 4 (May 26-Jun 1):**
- If PASS → update manuscript §Results
- If FAIL → write "Falsification Note" for supplementary
- If INCONCLUSIVE → design follow-up (analytical model)

---

## References

- Design doc: `/home/sayuj/life/VALIDATION_TEST_DESIGN.md`
- Experiment script: `/home/sayuj/life/scripts/experiments/experiment_bg_critical_point_validation.py`
- Existing Bg experiment: `/home/sayuj/life/src/spinalmodes/experiments/bio_gravitational_experiment.py`
- Consciousness-geometry (NULL result): `/home/sayuj/consciousness-geometry/results/highseed/`

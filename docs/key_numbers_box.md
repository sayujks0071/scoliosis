# Key Numbers Box: Summary of Anchor Values

## For Manuscript (After Running Full Sweeps)

Once you've run `scripts/extract_anchor_numbers.py`, fill in this box with actual values and add it to your manuscript (e.g., as a "Key Results" box or in the Results section).

---

## Template (Fill in after extraction)

### Key Quantitative Results

**Microgravity persistence:**
- At g = 9.81: D̂_geo = [X.XXX], passive energy = [X.XXe-X]
- At g = 0.01: D̂_geo = [X.XXX], passive energy = [X.XXe-X]
- Passive energy collapse: [XX]% reduction
- D̂_geo persistence: [X.XX]× (ratio)

**Phase diagram regimes:**
- **Gravity-dominated** (χ_κ = [X.XXX], g = [X.XX]): D̂_geo ≈ [0.0X], S_lat < 0.01, Cobb < 3°
- **Cooperative** (χ_κ = [X.XXX], g = [X.XX]): D̂_geo ≈ [0.XX], intermediate S_lat
- **Information-dominated/scoliotic** (χ_κ = [X.XXX], g = [X.XX]): D̂_geo > 0.3, S_lat ≳ 0.05, Cobb > 10°

**Spine S-curve sine-mode:**
- Sign changes in κ_I(s): [1]
- Max/RMS ratio: [X.XX]
- D̂_geo (info-driven): [X.XXX]

**Scoliosis amplification:**
- Gravity-dominated: S_lat_asym / S_lat_sym ≈ [X.XX]×
- Information-dominated: S_lat_asym / S_lat_sym ≈ [X.XX]×
- Amplification factor: [X-X]× increase

---

## LaTeX Version (For Manuscript)

```latex
\begin{tcolorbox}[colback=gray!5!white, colframe=black!60, title=Key Quantitative Results]

\textbf{Microgravity persistence:} As $g$ decreases from 9.81 to 0.01, passive curvature energy falls by [XX]\% while $\Dgeohat$ changes by only [X]\%, demonstrating information-driven structure maintenance independent of gravitational strength.

\textbf{Phase diagram regimes:} Three distinct countercurvature regimes emerge: (1) \emph{Gravity-dominated} ($\Dgeohat < 0.1$): $\chiK = [X.XXX]$, $g = [X.XX]$, $S_{\mathrm{lat}} < 0.01$, Cobb-like $< 3°$; (2) \emph{Cooperative} ($0.1 < \Dgeohat < 0.3$): intermediate regime; (3) \emph{Information-dominated/scoliotic} ($\Dgeohat > 0.3$): $\chiK = [X.XXX]$, $g = [X.XX]$, $S_{\mathrm{lat}} \gtrsim 0.05$, Cobb-like $> 10°$.

\textbf{Spine S-curve:} The information-selected curvature $\kappaInfo(s)$ exhibits a single sign change and max-to-RMS ratio of $\approx [X.XX]$, consistent with a sine-like counter-curvature mode against gravity ($\Dgeohat \approx [X.XXX]$).

\textbf{Scoliosis amplification:} In the information-dominated regime, a 5\% asymmetry ($\varepsilon_{\mathrm{asym}} = 0.05$) produces $S_{\mathrm{lat}} \approx [X.XX]$ and Cobb-like angles $> [XX]°$, representing a [X-X]× amplification relative to the gravity-dominated regime.

\end{tcolorbox}
```

---

## Usage

1. **Run full sweeps** (see `docs/full_sweeps_extraction_guide.md`)
2. **Run extraction script**: `python3 scripts/extract_anchor_numbers.py`
3. **Fill in template** with actual values
4. **Add to manuscript** (Results section or as standalone box)

---

## Status

⏳ **Waiting for full sweeps** - Run experiments first, then extract numbers

